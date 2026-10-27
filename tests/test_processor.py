from datetime import datetime,timedelta
from uuid import uuid4
from backend.app.database import Base,engine,SessionLocal
from backend.app.schemas import SpanEvent
from backend.app.services.processor import trace,analyze
def test_duplicate_and_failure_diagnosis():
 Base.metadata.create_all(engine); s=SessionLocal(); now=datetime.utcnow(); tid=uuid4().hex; e=SpanEvent(event_id=uuid4().hex,trace_id=tid,span_id='s1',service_name='payment',operation_name='charge',start_time=now,end_time=now+timedelta(seconds=2),status='ERROR',error_message='timeout'); assert trace(s,e); assert not trace(s,e); assert analyze(s,tid).affected_service=='payment'; s.close()
