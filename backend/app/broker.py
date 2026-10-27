"""RabbitMQ transport with explicit at-least-once delivery semantics."""
import json
try:
    import aio_pika
except ModuleNotFoundError:  # Native SQLite mode does not require broker packages.
    aio_pika = None
from .config import RABBIT_URL

async def publish(event_type: str, payload: dict) -> None:
    if aio_pika is None: raise RuntimeError('aio-pika is required when BROKER_ENABLED=true')
    connection = await aio_pika.connect_robust(RABBIT_URL, timeout=3)
    try:
        channel = await connection.channel(publisher_confirms=True)
        exchange = await channel.declare_exchange("telemetry", aio_pika.ExchangeType.TOPIC, durable=True)
        await exchange.publish(aio_pika.Message(json.dumps(payload, default=str).encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT, content_type="application/json"), routing_key=event_type)
    finally:
        await connection.close()
