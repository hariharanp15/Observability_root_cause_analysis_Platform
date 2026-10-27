from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
class SpanEvent(BaseModel):
    event_id: str; trace_id: str; span_id: str; parent_span_id: str|None=None; service_name: str; operation_name: str; start_time: datetime; end_time: datetime; status: Literal['OK','ERROR']='OK'; error_message: str|None=None
class LogEvent(BaseModel):
    event_id: str; service_name: str; message: str; severity: Literal['INFO','WARNING','ERROR','CRITICAL']='INFO'; timestamp: datetime; trace_id: str|None=None; span_id: str|None=None
class MetricEvent(BaseModel):
    event_id: str; service_name: str; metric_name: str; metric_value: float; recorded_at: datetime
class Batch(BaseModel):
    traces: list[SpanEvent]=[]; logs: list[LogEvent]=[]; metrics: list[MetricEvent]=[]
