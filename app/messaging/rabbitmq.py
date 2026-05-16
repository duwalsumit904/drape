"""
Author: Sumit
Created: 5/13/2026
"""

import json
import aio_pika
from aio_pika import DeliveryMode,ExchangeType,Message
from app.core.config import settings



EXCHANGE_NAME = "orders"
EMAIL_QUEUE = "email.queue"
WH_QUEUE = "warehouse.queue"



#---------------connection pool--------------------------------------

_connection: aio_pika.abc.AbstractRobustConnection | None = None

async def get_rabbit_connection() -> aio_pika.abc.AbstractRobustConnection:
    global _connection
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    return _connection

async def close_rabbit_connection() -> None:
    global _connection
    if _connection and not _connection.is_closed:
        await _connection.close()


async def declare_topology(channel:aio_pika.abc.AbstractChannel) -> aio_pika.abc.AbstractExchange:
    exchange = await channel.declare_exchange(
        EXCHANGE_NAME,
        ExchangeType.TOPIC,
        durable=True
    )

    for queue_name,routing_key in [
        (EMAIL_QUEUE,"order.placed"),
        (WH_QUEUE,"order.placed"),
    ]:
        queue = await channel.declare_queue(queue_name,durable=True)
        await queue.bind(exchange,routing_key=routing_key)

    return exchange



#----------------------------publisher----------------------------------------

async def publish_order_placed(payload:dict) -> None:
    conn = await get_rabbit_connection()
    channel = await conn.channel()

    try:
        exchange = await declare_topology(channel)
        await exchange.publish(
            Message(
                body = json.dumps(payload).encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json"


            ),
            routing_key="order.placed"

        )

    finally:
        await  channel.close()
