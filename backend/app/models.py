from datetime import datetime
from sqlalchemy import String, Float, DateTime, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Trace(Base):
    __tablename__ = "traces"; trace_id: Mapped[str] = mapped_column(String(64), primary_key=True); root_service: Mapped[str] = mapped_column(String(80)); start_time: Mapped[datetime] = mapped_column(DateTime); end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True); duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True); status: Mapped[str] = mapped_column(String(20), default="INCOMPLETE")
class Span(Base):
    __tablename__ = "trace_spans"; __table_args__=(UniqueConstraint("trace_id","span_id"),)
    id: Mapped[int] = mapped_column(primary_key=True); trace_id: Mapped[str] = mapped_column(String(64), index=True); span_id: Mapped[str] = mapped_column(String(64)); parent_span_id: Mapped[str | None] = mapped_column(String(64), nullable=True); service_name: Mapped[str] = mapped_column(String(80), index=True); operation_name: Mapped[str] = mapped_column(String(120)); start_time: Mapped[datetime] = mapped_column(DateTime); end_time: Mapped[datetime] = mapped_column(DateTime); duration_ms: Mapped[float] = mapped_column(Float); status: Mapped[str] = mapped_column(String(20)); error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
class ProcessedLog(Base):
    __tablename__="processed_logs"; event_id: Mapped[str] = mapped_column(String(64), primary_key=True); trace_id: Mapped[str | None]=mapped_column(String(64),index=True,nullable=True); span_id: Mapped[str | None]=mapped_column(String(64),nullable=True); service_name: Mapped[str]=mapped_column(String(80),index=True); severity: Mapped[str]=mapped_column(String(12)); message: Mapped[str]=mapped_column(Text); timestamp: Mapped[datetime]=mapped_column(DateTime,index=True)
class Metric(Base):
    __tablename__="metric_samples"; event_id: Mapped[str]=mapped_column(String(64),primary_key=True); service_name: Mapped[str]=mapped_column(String(80),index=True); metric_name: Mapped[str]=mapped_column(String(80)); metric_value: Mapped[float]=mapped_column(Float); recorded_at: Mapped[datetime]=mapped_column(DateTime)
class Diagnostic(Base):
    __tablename__="diagnostic_reports"; id: Mapped[int]=mapped_column(primary_key=True); trace_id: Mapped[str]=mapped_column(String(64),index=True); affected_service: Mapped[str]=mapped_column(String(80)); severity: Mapped[str]=mapped_column(String(20)); diagnosis: Mapped[str]=mapped_column(Text); evidence: Mapped[str]=mapped_column(Text); confidence_level: Mapped[str]=mapped_column(String(20)); created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class Alert(Base):
    __tablename__="alerts"; id: Mapped[int]=mapped_column(primary_key=True); service_name: Mapped[str]=mapped_column(String(80)); alert_type: Mapped[str]=mapped_column(String(80)); measured_value: Mapped[float]=mapped_column(Float); threshold_value: Mapped[float]=mapped_column(Float); status: Mapped[str]=mapped_column(String(20),default="ACTIVE"); first_seen_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); last_seen_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); occurrence_count: Mapped[int]=mapped_column(Integer,default=1)
