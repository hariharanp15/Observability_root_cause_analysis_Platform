"""Read-only evidence exports for trace investigations."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import db
from ..models import Diagnostic, ProcessedLog, Span, Trace

router = APIRouter(prefix='/api/v1/reports', tags=['Reports'])

def row(value): return {c.name: getattr(value, c.name) for c in value.__table__.columns}

@router.get('/traces/{trace_id}/evidence')
def trace_evidence(trace_id: str, s: Session = Depends(db)):
    trace = s.get(Trace, trace_id)
    if not trace: raise HTTPException(404, 'Trace not found')
    return {'data': {'trace': row(trace), 'spans': [row(x) for x in s.query(Span).filter_by(trace_id=trace_id).order_by(Span.start_time)], 'logs': [row(x) for x in s.query(ProcessedLog).filter_by(trace_id=trace_id).order_by(ProcessedLog.timestamp)], 'diagnostics': [row(x) for x in s.query(Diagnostic).filter_by(trace_id=trace_id).order_by(Diagnostic.created_at.desc())]}}
