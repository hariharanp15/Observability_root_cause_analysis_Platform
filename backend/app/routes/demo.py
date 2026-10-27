"""Backend-generated sample traffic for local demonstrations and end-to-end tests."""
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import db
from ..schemas import SpanEvent, LogEvent, MetricEvent
from ..services.processor import trace, log, metric, check_alerts, analyze

router = APIRouter(prefix='/api/v1/demo', tags=['Sample instrumented application'])

@router.post('/orders')
def create_order(scenario: str = 'normal', s: Session = Depends(db)):
    """Generate an Order → Payment → Notification trace from backend service logic."""
    allowed = {'normal', 'slow_payment', 'payment_failure', 'notification_timeout', 'invalid_downstream', 'intermittent_unavailable'}
    if scenario not in allowed: raise HTTPException(422, f"scenario must be one of {sorted(allowed)}")
    tid, now = uuid4().hex, datetime.utcnow()
    definitions = [('gateway', 'POST /orders', 30, 'OK', None), ('order-service', 'create_order', 90, 'OK', None), ('payment-service', 'charge', 120, 'OK', None), ('notification-service', 'send_receipt', 60, 'OK', None)]
    if scenario == 'slow_payment': definitions[2] = ('payment-service', 'charge', 1800, 'OK', None)
    if scenario in {'payment_failure', 'invalid_downstream', 'intermittent_unavailable'}: definitions[2] = ('payment-service', 'charge', 140, 'ERROR', 'payment provider unavailable' if scenario != 'invalid_downstream' else 'invalid provider response')
    if scenario == 'notification_timeout': definitions[3] = ('notification-service', 'send_receipt', 1200, 'ERROR', 'downstream timeout')
    parent = None
    for index, (service, operation, duration, status, error) in enumerate(definitions):
        span_id = f'{tid[:8]}-{index}'
        start = now + timedelta(milliseconds=index * 10)
        trace(s, SpanEvent(event_id=f'{tid}-span-{index}', trace_id=tid, span_id=span_id, parent_span_id=parent, service_name=service, operation_name=operation, start_time=start, end_time=start + timedelta(milliseconds=duration), status=status, error_message=error))
        metric(s, MetricEvent(event_id=f'{tid}-metric-{index}', service_name=service, metric_name='request_latency_ms', metric_value=duration, recorded_at=start))
        if status == 'ERROR': log(s, LogEvent(event_id=f'{tid}-log-{index}', service_name=service, severity='ERROR', message=error or 'failed request', timestamp=start, trace_id=tid, span_id=span_id))
        parent = span_id
    check_alerts(s)
    report = analyze(s, tid)
    return {'data': {'trace_id': tid, 'scenario': scenario, 'diagnostic_report_id': report.id if report else None}, 'message': 'sample distributed request generated'}
