import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./observability.db")
RABBIT_URL = os.getenv("RABBIT_URL", "amqp://guest:guest@localhost:5672/")
BROKER_ENABLED = os.getenv("BROKER_ENABLED", "false").lower() == "true"
SERVICE_NAME = os.getenv("SERVICE_NAME", "observability-query")
SLOW_SPAN_MS = int(os.getenv("SLOW_SPAN_MS", "800"))
ALERT_ERROR_RATE = float(os.getenv("ALERT_ERROR_RATE", "0.10"))
