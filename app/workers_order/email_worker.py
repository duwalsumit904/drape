"""
Author: Sumit
Created: 5/13/2026
"""

import asyncio,json
import logging
import aio_pika
from app.core.config import settings
from app.messaging.rabbitmq import EMAIL_QUEUE, declare_topology, get_rabbit_connection
from workers.email_order import send_order_confirmation


logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s %(levelname)-8s %(message)s"
)
logger = logging.getLogger(__name__)


async def handle_email(message:aio_pika.IncomingMessage) -> None:
    async with message.process(requeue=False):
        payload = json.loads(message.body)
        send_order_confirmation(
            to = payload["user_email"],
            order_id= payload["order_id"],
            total= payload["total"],
            item_count=payload["item_count"]
        )


async def main() -> None:
    conn = await get_rabbit_connection()
    channel = await conn.channel()
    await channel.set_qos(prefetch_count=10)

    await declare_topology(channel)
    queue = await channel.declare_queue(EMAIL_QUEUE,durable=True)

    await queue.consume(handle_email)

    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        logger.info("Shutting down email worker...")
    finally:
        await conn.close()
        logger.info("Connection closed")
if __name__ == "__main__":
    asyncio.run(main())




