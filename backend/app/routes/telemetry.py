from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import db
from ..schemas import SpanEvent,LogEvent,MetricEvent,Batch
from ..services.processor import trace,log,metric,check_alerts
from ..config import BROKER_ENABLED
from ..broker import publish
router=APIRouter(prefix='/api/v1/telemetry',tags=['Telemetry ingestion'])
async def dispatch(kind, event, session):
    if BROKER_ENABLED:
        try: await publish(kind, event.model_dump(mode='json'))
        except Exception as exc: raise HTTPException(503, 'Telemetry broker temporarily unavailable') from exc
    else:
        {'traces': trace, 'logs': log, 'metrics': metric}[kind](session, event)
        if kind == 'traces': check_alerts(session)
@router.post('/traces')
async def ingest_trace(e:SpanEvent,s:Session=Depends(db)): await dispatch('traces',e,s); return {'data':{'event_id':e.event_id},'message':'accepted'}
@router.post('/logs')
async def ingest_log(e:LogEvent,s:Session=Depends(db)): await dispatch('logs',e,s); return {'data':{'event_id':e.event_id},'message':'accepted'}
@router.post('/metrics')
async def ingest_metric(e:MetricEvent,s:Session=Depends(db)): await dispatch('metrics',e,s); return {'data':{'event_id':e.event_id},'message':'accepted'}
@router.post('/batch')
async def ingest_batch(b:Batch,s:Session=Depends(db)):
    for x in b.traces: await dispatch('traces',x,s)
    for x in b.logs: await dispatch('logs',x,s)
    for x in b.metrics: await dispatch('metrics',x,s)
    return {'data':{'traces':len(b.traces),'logs':len(b.logs),'metrics':len(b.metrics)},'message':'accepted'}
