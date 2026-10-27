import os, time
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
class Base(DeclarativeBase): pass
def initialize_database(retries: int | None = None):
    """Wait for Compose DNS/MySQL readiness before services create their tables."""
    attempts = retries or int(os.getenv('DATABASE_CONNECT_RETRIES', '30'))
    last_error = None
    for _ in range(attempts):
        try:
            Base.metadata.create_all(engine)
            return
        except OperationalError as exc:
            last_error = exc
            time.sleep(2)
    raise last_error or RuntimeError('Database initialization failed')
def db():
    s = SessionLocal()
    try: yield s
    finally: s.close()
