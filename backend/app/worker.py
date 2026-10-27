"""Dedicated RabbitMQ consumer entry point for trace, log, and metric processors."""
import asyncio, json, os
import aio_pika
from .broker import RABBIT_URL
from .database import SessionLocal, initialize_database
from .schemas import SpanEvent, LogEvent, MetricEvent
from .services.processor import trace, log, metric, check_alerts

KIND = os.getenv("WORKER_KIND", "traces")
HANDLERS = {"traces": (SpanEvent, trace), "logs": (LogEvent, log), "metrics": (MetricEvent, metric)}

async def main():
    initialize_database()
    schema, handler = HANDLERS[KIND]
    connection = await aio_pika.connect_robust(RABBIT_URL)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=20)
    exchange = await channel.declare_exchange("telemetry", aio_pika.ExchangeType.TOPIC, durable=True)
    dead = await channel.declare_exchange("telemetry.dlx", aio_pika.ExchangeType.TOPIC, durable=True)
    queue = await channel.declare_queue(f"telemetry.{KIND}", durable=True, arguments={"x-dead-letter-exchange": "telemetry.dlx"})
    await queue.bind(exchange, routing_key=KIND)
    async def consume(message):
        async with message.process(requeue=False):
            session = SessionLocal()
            try:
                handler(session, schema.model_validate(json.loads(message.body)))
                if KIND == "traces": check_alerts(session)
            finally: session.close()
    await queue.consume(consume)
    await asyncio.Future()
if __name__ == '__main__': asyncio.run(main())
