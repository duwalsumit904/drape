import stripe
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException
from redis.asyncio import Redis
from app.core.config import settings
from app.models.order import Order, OrderStatus, OrderItem
from app.models.product import ProductVariant
from app.messaging.rabbitmq import publish_order_placed

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)


async def create_payment_intent(
    order_id: str,
    db      : AsyncSession,
    user_id : str,
) -> dict:

    result = await db.execute(
        select(Order).where(
            Order.id      == order_id,
            Order.user_id == user_id
        )
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(404, "Order not found")
    if order.status != OrderStatus.pending:
        raise HTTPException(400, f"Order is already {order.status}")

    intent = stripe.PaymentIntent.create(
        amount   = int(order.total * 100),
        currency = "inr",
        payment_method_types=["card"],

        metadata = {
            "order_id": str(order_id),
            "user_id" : str(user_id),       # ✅ fixed
        }
    )

    logger.info(f"PaymentIntent created → {intent.id} for order {order_id}")

    return {
        "client_secret"    : intent.client_secret,
        "payment_intent_id": intent.id,
        "amount"           : order.total,
        "currency"         : "inr",
    }


async def confirm_payment(
    order_id          : str,
    payment_intent_id : str,
    db                : AsyncSession,
    redis             : Redis,
    current_user      : any,
) -> dict:

    result = await db.execute(
        select(Order).where(
            Order.id      == order_id,
            Order.user_id == current_user.id
        )
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(404, "Order not found")
    if order.status != OrderStatus.pending:
        raise HTTPException(400, f"Order already {order.status}")

    try:

        # intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        #confirm should not be done form backend right now its for api testing
        intent = stripe.PaymentIntent.confirm(
            payment_intent_id,
            payment_method="pm_card_visa"
        )
    except stripe.error.StripeError as e:

        raise HTTPException(400, f"Stripe error: {e.user_message}")

    if intent.status == "succeeded":                        # ✅ colon fixed
        await db.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(status=OrderStatus.confirmed)
        )
        await db.commit()

        items_result = await db.execute(
            select(OrderItem).where(OrderItem.order_id == order_id)
        )
        items = items_result.scalars().all()

        await publish_order_placed({
            "order_id"  : str(order.id),
            "user_email": current_user.email,
            "total"     : float(order.total),
            "item_count": len(items),
        })

        logger.info(f"Payment confirmed → order {order_id}")

        return {
            "status"  : "confirmed",
            "order_id": order_id,
            "message" : "Payment successful. Confirmation email sent."
        }

    elif intent.status in ["requires_payment_method", "canceled"]:
        await _cancel_order(order_id, db, redis)
        return {
            "status"  : "cancelled",
            "order_id": order_id,
            "message" : "Payment failed. Order cancelled. Stock restored."
        }

    else:
        return {
            "status"  : intent.status,
            "order_id": order_id,
            "message" : "Payment still processing."
        }


async def _cancel_order(
    order_id: str,
    db      : AsyncSession,
    redis   : Redis,
) -> None:

    await db.execute(
        update(Order)
        .where(Order.id == order_id)
        .values(status=OrderStatus.cancelled)
    )

    items_result = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order_id)
    )
    items = items_result.scalars().all()

    for item in items:
        await db.execute(
            update(ProductVariant)
            .where(ProductVariant.id == item.variant_id)
            .values(stock_count=ProductVariant.stock_count + item.quantity)
        )

        stock_key = f"stock:{item.variant_id}"
        exists = await redis.exists(stock_key)
        if exists:
            await redis.incrby(stock_key, item.quantity)

    await db.commit()
    logger.info(f"Order {order_id} cancelled. Stock restored.")