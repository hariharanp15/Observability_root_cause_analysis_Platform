"""Platform-level operational API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..config import SERVICE_NAME, BROKER_ENABLED
from ..database import db
from ..models import Alert, Diagnostic, Metric, ProcessedLog, Span, Trace

router = APIRouter(prefix='/api/v1/system', tags=['System'])

@router.get('/status')
def status(s: Session = Depends(db)):
    return {'data': {'service': SERVICE_NAME, 'status': 'healthy', 'storage': 'connected', 'broker_enabled': BROKER_ENABLED}}

@router.get('/statistics')
def statistics(s: Session = Depends(db)):
    return {'data': {'traces': s.query(Trace).count(), 'spans': s.query(Span).count(), 'logs': s.query(ProcessedLog).count(), 'metric_samples': s.query(Metric).count(), 'diagnostics': s.query(Diagnostic).count(), 'active_alerts': s.query(Alert).filter_by(status='ACTIVE').count()}}

@router.get('/capabilities')
def capabilities():
    return {'data': {'telemetry': ['traces', 'logs', 'metrics', 'batch'], 'queries': ['overview', 'traces', 'logs', 'metrics', 'dependencies', 'diagnostics', 'alerts'], 'delivery_guarantee': 'at-least-once with idempotent event persistence', 'broker_mode': 'rabbitmq' if BROKER_ENABLED else 'direct-local'}}
