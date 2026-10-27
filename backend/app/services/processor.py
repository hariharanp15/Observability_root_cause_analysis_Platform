from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import Trace, Span, ProcessedLog, Metric, Diagnostic, Alert
from ..schemas import SpanEvent, LogEvent, MetricEvent
from ..config import SLOW_SPAN_MS, ALERT_ERROR_RATE

def trace(s: Session, e: SpanEvent):
    if s.query(Span).filter_by(trace_id=e.trace_id, span_id=e.span_id).first(): return False
    ms=(e.end_time-e.start_time).total_seconds()*1000
    s.add(Span(trace_id=e.trace_id,span_id=e.span_id,parent_span_id=e.parent_span_id,service_name=e.service_name,operation_name=e.operation_name,start_time=e.start_time,end_time=e.end_time,duration_ms=ms,status=e.status,error_message=e.error_message))
    t=s.get(Trace,e.trace_id)
    if not t: s.add(Trace(trace_id=e.trace_id,root_service=e.service_name,start_time=e.start_time,end_time=e.end_time,duration_ms=ms,status=e.status))
    else:
        t.start_time=min(t.start_time,e.start_time); t.end_time=max(t.end_time or e.end_time,e.end_time); t.duration_ms=(t.end_time-t.start_time).total_seconds()*1000
        if e.status=='ERROR': t.status='ERROR'
    s.commit(); return True
def log(s,e):
    if s.get(ProcessedLog,e.event_id): return False
    s.add(ProcessedLog(**e.model_dump())); s.commit(); return True
def metric(s,e):
    if s.get(Metric,e.event_id): return False
    s.add(Metric(**e.model_dump())); s.commit(); return True
def analyze(s, trace_id):
    spans=s.query(Span).filter_by(trace_id=trace_id).order_by(Span.start_time).all()
    if not spans: return None
    failed=next((x for x in spans if x.status=='ERROR'),None); slow=max(spans,key=lambda x:x.duration_ms)
    target=failed or (slow if slow.duration_ms>=SLOW_SPAN_MS else None)
    if not target: return None
    evidence=f"span={target.span_id}; duration_ms={target.duration_ms:.0f}; status={target.status}; trace_id={trace_id}"
    text=(f"Confirmed failing span in {target.service_name}: {target.error_message or target.operation_name}" if failed else f"Potential latency bottleneck in {target.service_name}: {target.duration_ms:.0f}ms")
    r=Diagnostic(trace_id=trace_id,affected_service=target.service_name,severity='HIGH' if failed else 'MEDIUM',diagnosis=text,evidence=evidence,confidence_level='CONFIRMED' if failed else 'POTENTIAL'); s.add(r); s.commit(); return r
def check_alerts(s):
    for service,total,errors in s.query(Span.service_name,func.count(),func.sum(Span.status=='ERROR')).group_by(Span.service_name):
        rate=(errors or 0)/total
        if rate>=ALERT_ERROR_RATE:
            a=s.query(Alert).filter_by(service_name=service,alert_type='ERROR_RATE',status='ACTIVE').first()
            if a: a.last_seen_at=datetime.utcnow(); a.occurrence_count+=1; a.measured_value=rate
            else: s.add(Alert(service_name=service,alert_type='ERROR_RATE',measured_value=rate,threshold_value=ALERT_ERROR_RATE))
    s.commit()
