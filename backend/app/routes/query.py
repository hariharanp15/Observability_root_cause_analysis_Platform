from datetime import datetime
from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import db
from ..models import Trace, Span, ProcessedLog, Metric, Diagnostic, Alert
from ..services.processor import analyze
router=APIRouter(prefix='/api/v1',tags=['Observability queries'])
def out(x): return {c.name:getattr(x,c.name) for c in x.__table__.columns}
def paged(q,page,size):
 total=q.count();return {'data':[out(x) for x in q.offset((page-1)*size).limit(size)],'pagination':{'page':page,'size':size,'total':total,'pages':ceil(total/size) if total else 0}}
@router.get('/overview')
def overview(s:Session=Depends(db)):
 traces=s.query(Trace).all(); spans=s.query(Span).all(); ds=sorted(x.duration_ms for x in spans);total=len(traces)
 return {'data':{'total_requests':total,'error_rate':sum(x.status=='ERROR' for x in traces)/total if total else 0,'average_latency_ms':sum(ds)/len(ds) if ds else 0,'p95_latency_ms':ds[max(0,ceil(len(ds)*.95)-1)] if ds else 0,'services_reporting_errors':len({x.service_name for x in spans if x.status=='ERROR'}),'active_alerts':s.query(Alert).filter_by(status='ACTIVE').count()}}
@router.get('/traces')
def traces(trace_id:str|None=None,status:str|None=None,page:int=Query(1,ge=1),size:int=Query(50,ge=1,le=200),s:Session=Depends(db)):
 q=s.query(Trace)
 if trace_id:q=q.filter(Trace.trace_id.contains(trace_id))
 if status:q=q.filter(Trace.status==status.upper())
 return paged(q.order_by(Trace.start_time.desc()),page,size)
@router.get('/traces/{trace_id}')
def trace_detail(trace_id:str,s:Session=Depends(db)):
 x=s.get(Trace,trace_id)
 if not x:raise HTTPException(404,'Trace not found')
 d=out(x);sp=s.query(Span).filter_by(trace_id=trace_id).all();d['missing_parent_span_ids']=sorted({x.parent_span_id for x in sp if x.parent_span_id and not any(y.span_id==x.parent_span_id for y in sp)});return {'data':d}
@router.get('/traces/{trace_id}/spans')
def spans(trace_id:str,s:Session=Depends(db)):
 if not s.get(Trace,trace_id):raise HTTPException(404,'Trace not found')
 return {'data':[out(x) for x in s.query(Span).filter_by(trace_id=trace_id).order_by(Span.start_time)]}
@router.get('/traces/{trace_id}/logs')
def trace_logs(trace_id:str,s:Session=Depends(db)):return {'data':[out(x) for x in s.query(ProcessedLog).filter_by(trace_id=trace_id).order_by(ProcessedLog.timestamp)]}
@router.get('/logs')
def logs(service:str|None=None,severity:str|None=None,trace_id:str|None=None,start_time:datetime|None=None,end_time:datetime|None=None,page:int=Query(1,ge=1),size:int=Query(100,ge=1,le=200),s:Session=Depends(db)):
 if start_time and end_time and start_time>end_time:raise HTTPException(422,'start_time must be before end_time')
 q=s.query(ProcessedLog)
 if service:q=q.filter_by(service_name=service)
 if severity:q=q.filter_by(severity=severity.upper())
 if trace_id:q=q.filter_by(trace_id=trace_id)
 if start_time:q=q.filter(ProcessedLog.timestamp>=start_time)
 if end_time:q=q.filter(ProcessedLog.timestamp<=end_time)
 return paged(q.order_by(ProcessedLog.timestamp.desc()),page,size)
@router.get('/logs/{log_id}')
def log_detail(log_id:str,s:Session=Depends(db)):
 x=s.get(ProcessedLog,log_id)
 if not x:raise HTTPException(404,'Log not found')
 return {'data':out(x)}
@router.get('/metrics/services')
def metric_services(s:Session=Depends(db)):return {'data':[x[0] for x in s.query(Metric.service_name).distinct()]}
@router.get('/metrics/summary')
def metric_summary(service:str|None=None,s:Session=Depends(db)):
 q=s.query(Metric)
 if service:q=q.filter_by(service_name=service)
 grouped={}
 for x in q.all():grouped.setdefault(x.service_name,[]).append(x.metric_value)
 return {'data':[{'service':n,'average':sum(v)/len(v),'minimum':min(v),'maximum':max(v),'samples':len(v)} for n,v in grouped.items()]}
@router.get('/metrics/timeseries')
def metrics(service:str|None=None,metric_name:str|None=None,s:Session=Depends(db)):
 q=s.query(Metric)
 if service:q=q.filter_by(service_name=service)
 if metric_name:q=q.filter_by(metric_name=metric_name)
 return {'data':[out(x) for x in q.order_by(Metric.recorded_at).limit(500)]}
@router.get('/metrics/latency')
def latency(service:str|None=None,s:Session=Depends(db)):
 q=s.query(Span)
 if service:q=q.filter_by(service_name=service)
 g={}
 for x in q.all():g.setdefault(x.service_name,[]).append(x.duration_ms)
 return {'data':[{'service':n,'average_ms':sum(v)/len(v),'p95_ms':sorted(v)[max(0,ceil(len(v)*.95)-1)],'samples':len(v)} for n,v in g.items()],'percentile_method':'nearest-rank p95 over retained raw span durations'}
def dependency_rows(s):
 rows=s.query(Span).all();idx={(x.trace_id,x.span_id):x for x in rows};edges={}
 for x in rows:
  p=idx.get((x.trace_id,x.parent_span_id))
  if p and p.service_name!=x.service_name:edges.setdefault((p.service_name,x.service_name),[]).append(x)
 return [{'source':k[0],'target':k[1],'requests':len(v),'error_rate':sum(x.status=='ERROR' for x in v)/len(v),'average_latency_ms':sum(x.duration_ms for x in v)/len(v)} for k,v in edges.items()]
@router.get('/dependencies')
def dependencies(s:Session=Depends(db)):return {'data':dependency_rows(s)}
@router.get('/dependencies/{service_name}')
def service_dependencies(service_name:str,s:Session=Depends(db)):return {'data':[x for x in dependency_rows(s) if x['source']==service_name or x['target']==service_name],'service':service_name}
@router.get('/diagnostics')
def diagnostics(trace_id:str|None=None,s:Session=Depends(db)):
 q=s.query(Diagnostic)
 if trace_id:q=q.filter_by(trace_id=trace_id)
 return {'data':[out(x) for x in q.order_by(Diagnostic.created_at.desc())]}
@router.get('/diagnostics/{report_id}')
def diagnostic_detail(report_id:int,s:Session=Depends(db)):
 x=s.get(Diagnostic,report_id)
 if not x:raise HTTPException(404,'Diagnostic report not found')
 return {'data':out(x)}
@router.post('/diagnostics/analyze/{trace_id}')
def diagnostic(trace_id:str,s:Session=Depends(db)):
 r=analyze(s,trace_id)
 if not r:raise HTTPException(422,'Insufficient telemetry for a diagnosis')
 return {'data':out(r)}
@router.get('/alerts')
def alerts(status:str|None=None,s:Session=Depends(db)):
 q=s.query(Alert)
 if status:q=q.filter_by(status=status.upper())
 return {'data':[out(x) for x in q.order_by(Alert.last_seen_at.desc())]}
@router.get('/alerts/{alert_id}')
def alert_detail(alert_id:int,s:Session=Depends(db)):
 x=s.get(Alert,alert_id)
 if not x:raise HTTPException(404,'Alert not found')
 return {'data':out(x)}
@router.patch('/alerts/{alert_id}')
def update_alert(alert_id:int,status:str='ACKNOWLEDGED',s:Session=Depends(db)):
 if status.upper() not in {'ACTIVE','ACKNOWLEDGED','RESOLVED'}:raise HTTPException(422,'Invalid alert status')
 x=s.get(Alert,alert_id)
 if not x:raise HTTPException(404,'Alert not found')
 x.status=status.upper();s.commit();return {'data':out(x)}
