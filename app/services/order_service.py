import json

from celery.bin.result import result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from redis.asyncio import Redis
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import ProductVariant
from app.models.user import User
# from app.messaging.rabbitmq import publish_order_placed
# ─── Lua Script ─────────────────────────────────────────
stock_deduct_lua = """
local quantity = tonumber(ARGV[1])
local stock_key = KEYS[1]

local current_stock = tonumber(redis.call("GET", stock_key))

if not current_stock then
    return {err="stock key not found"}
end

if current_stock < quantity then
    return {err="insufficient stock: " .. current_stock .. " available"}
end

redis.call("DECRBY", stock_key, quantity)
return "ok"
"""

async def place_order(current_user: User, db: AsyncSession, redis: Redis):

    # STEP 1 — Get cart
    cart_key = f"cart:{current_user.id}"
    cart     = await redis.hgetall(cart_key)

    if not cart:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty"
        )

    # STEP 2 — Fetch all variants
    variant_ids = list(cart.keys())
    result      = await db.execute(
        select(ProductVariant).where(
            ProductVariant.id.in_(variant_ids)
        )
    )
    variants = {v.id: v for v in result.scalars().all()}

    # STEP 3 — Validate variants
    for vid in variant_ids:
        if vid not in variants:
            raise HTTPException(400, "Variant not found")
        if not variants[vid].is_active:
            raise HTTPException(400, "Variant not available")

    # STEP 4 — Load stock into Redis
    for vid, variant in variants.items():
        stock_key = f"stock:{vid}"
        existing  = await redis.get(stock_key)
        if not existing:
            await redis.set(stock_key, variant.stock_count)

    # STEP 5 — Lua atomic stock check + deduct
    for vid, qty_str in cart.items():
        stock_key = f"stock:{vid}"
        try:
            await redis.eval(    # ← await added ✅
                stock_deduct_lua,
                1,
                stock_key,
                str(int(qty_str))
            )
        except Exception as e:
            raise HTTPException(400, str(e))

    # STEP 6 — Calculate total
    total = sum(
        variants[vid].price * int(qty)
        for vid, qty in cart.items()
    )

    # STEP 7 — Create Order
    order = Order(
        user_id=current_user.id,
        status =OrderStatus.pending,
        total  =total
    )
    db.add(order)
    await db.flush()    # get order.id

    # STEP 8 — Create OrderItems
    for vid, qty_str in cart.items():
        item = OrderItem(
            order_id              =order.id,
            variant_id            =vid,
            quantity              =int(qty_str),
            unit_price_at_purchase=variants[vid].price
        )
        db.add(item)

    # STEP 9 — Atomic PostgreSQL stock update ✅
    from sqlalchemy import update as sql_update
    for vid, qty_str in cart.items():
        await db.execute(
            sql_update(ProductVariant)
            .where(ProductVariant.id == vid)
            .values(
                stock_count=ProductVariant.stock_count - int(qty_str)
            )
        )

    # ONE commit — all or nothing ✅
    await db.commit()
    await db.refresh(order)

    # STEP 10 — Clear cart
    await redis.delete(cart_key)

    # STEP 11 — Clear cache
    for vid in variant_ids:
        product_id = variants[vid].product_id
        await redis.delete(f"product:{product_id}")
    await redis.delete("products:listing")

    #publish order (Rabbitmq)
    # await publish_order_placed({
    #     "event": "order.placed",
    #     "order_id": str(order.id),
    #     "user_id": str(current_user.id),
    #     "user_email": current_user.email,
    #     "total": float(order.total),
    #     "item_count": len(cart),
    #     "items":[
    #         {
    #             "variant_id":vid,
    #             "quantity": int(qty),
    #             "unit_price": float(variants[vid].price),
    #         }
    #         for vid,qty in cart.items()
    #     ],
    #
    # })

    return {
        "order_id"  : order.id,
        "status"    : order.status,
        "total"     : order.total,
        "item_count": len(cart)
    }

#get single order

async def get_order(
        order_id: str,
        current_user: User,
        db :AsyncSession
):
    result  = await db.execute(select(Order).options(selectinload(Order.items))
                             .where(Order.id == order_id,
                                    Order.user_id == current_user.id
                                    )
                             )

    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,detail="Order not found"
        )

    return {
        "order_id": order.id,
        "status": order.status,
        "total": order.total,
        "created_at": order.created_at,
        "items": [
            {
                "variant_id": item.variant_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price_at_purchase,
                "subtotal": item.quantity *
                            item.unit_price_at_purchase
            }

            for item in order.items

            ]

    }




#-----get orders----------------------------------------------

async def get_orders(current_user: User,db:AsyncSession):

    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())

    )

    orders = result.scalars().all()

    return [
        {
            "order_id": o.id,
            "status": o.status,
            "total": o.total,
            "created_at": o.created_at,
            "items": [
                {
                    "variant_id": item.variant_id,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price_at_purchase,
                    "subtotal": item.quantity *
                                item.unit_price_at_purchase
                }
                for item in o.items
            ]
        }
        for o in orders
    ]


































