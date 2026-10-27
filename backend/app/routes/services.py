"""Observed service inventory and service-focused performance endpoints."""
from math import ceil
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import db
from ..models import Span
from .query import dependency_rows

router = APIRouter(prefix='/api/v1/services', tags=['Observed services'])

def service_values(s: Session, name: str):
    values = [x for x in s.query(Span).filter_by(service_name=name).all()]
    if not values: raise HTTPException(404, 'Observed service not found')
    durations = sorted(x.duration_ms for x in values)
    return values, durations

@router.get('')
def list_services(s: Session = Depends(db)):
    result = []
    for name, in s.query(Span.service_name).distinct():
        spans, values = service_values(s, name)
        result.append({'service_name': name, 'requests': len(spans), 'errors': sum(x.status == 'ERROR' for x in spans), 'error_rate': sum(x.status == 'ERROR' for x in spans) / len(spans), 'average_latency_ms': sum(values) / len(values), 'p95_latency_ms': values[max(0, ceil(len(values) * .95) - 1)]})
    return {'data': result}

@router.get('/{service_name}')
def service_summary(service_name: str, s: Session = Depends(db)):
    spans, values = service_values(s, service_name)
    return {'data': {'service_name': service_name, 'span_count': len(spans), 'failed_spans': sum(x.status == 'ERROR' for x in spans), 'average_latency_ms': sum(values) / len(values), 'p95_latency_ms': values[max(0, ceil(len(values) * .95) - 1)], 'recent_spans': [{'trace_id': x.trace_id, 'span_id': x.span_id, 'operation_name': x.operation_name, 'status': x.status, 'duration_ms': x.duration_ms} for x in sorted(spans, key=lambda x: x.start_time, reverse=True)[:20]]}}

@router.get('/{service_name}/dependencies')
def dependencies(service_name: str, s: Session = Depends(db)):
    service_values(s, service_name)
    return {'data': [x for x in dependency_rows(s) if x['source'] == service_name or x['target'] == service_name]}
