from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.product import ProductVariant
from app.models.user import User

CART_TTL = 60 * 60 * 24


async def add_to_cart(
        current_user: User,
        variant_id: str,
        quantity: int,
        db: AsyncSession,
        redis: Redis

):
    # check stock

    result = await db.execute(select(ProductVariant).where(ProductVariant.id == variant_id))

    variant = result.scalar_one_or_none()
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product variant not found"
        )

    if not variant.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product variant not available"
        )

    if variant.stock_count < quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {variant.stock_count} items in stock"
        )
    if quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be at least 1"
        )



    cart_key = f"cart:{current_user.id}"

    cart_size = await redis.hlen(cart_key)
    if cart_size >=50:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="cart limit reached. Magit aximum 50 items allowed"
        )

    # get existing  quantity

    existing = await redis.hget(cart_key, variant_id)
    new_qty = (int(existing) if existing else 0) + quantity

    if new_qty > variant.stock_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {variant.stock_count} items available"
        )

    # add to cart
    await redis.hset(cart_key, variant_id, new_qty)
    await redis.expire(cart_key, CART_TTL)

    return {"message": "Added to cart", "quantity": new_qty}


async def get_cart(
    current_user: User,
    db: AsyncSession,
    redis: Redis
):
    cart_key = f"cart:{current_user.id}"
    cart = await redis.hgetall(cart_key)

    if not cart:
        return {"items": [], "total": 0}

    # ONE query for all variants ✅
    variant_ids = list(cart.keys())
    result = await db.execute(
        select(ProductVariant)
        .options(selectinload(ProductVariant.product))
        .where(ProductVariant.id.in_(variant_ids))
    )
    variants = {v.id: v for v in result.scalars().all()}

    items = []
    total = 0

    for variant_id, quantity in cart.items():
        variant = variants.get(variant_id)
        if variant:
            subtotal = variant.price * int(quantity)
            total += subtotal
            items.append({
                "variant_id"  : variant_id,
                "product_name": variant.product.name,  # ← from relationship
                "sku"         : variant.sku,
                "color"       : variant.color,
                "size"        : variant.size,
                "price"       : variant.price,
                "quantity"    : int(quantity),
                "subtotal"    : subtotal,
                "in_stock"    : variant.stock_count >= int(quantity)
            })

    return {"items": items, "total": total}


async def remove_from_cart(
        current_user: User,
        variant_id: str,
        redis: Redis
):
    cart_key = f"cart:{current_user.id}"
    deleted = await redis.hdel(cart_key, variant_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not in cart"
        )

    return {"message": "Item removed from cart"}


async def update_cart_item(
        current_user: User,
        variant_id: str,
        quantity: int,
        db: AsyncSession,
        redis: Redis
):
    #check stock
    result = await db.execute(
        select(ProductVariant).where(
            ProductVariant.id == variant_id
        )
    )
    variant = result.scalar_one_or_none()

    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variant not found"
        )

    if quantity > variant.stock_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {variant.stock_count} items available")

    if quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity cannot be negative"
        )
    cart_key = f"cart:{current_user.id}"

    if quantity == 0:
        await redis.hdel(cart_key,variant_id)
        return {"message":"Item removed from cart"}

    await redis.hset(cart_key,variant_id,quantity)
    await redis.expire(cart_key,CART_TTL)

    return {"message": "Cart updated", "quantity": quantity}




async def clear_cart(current_user: User, redis: Redis):
    await redis.delete(f"cart:{current_user.id}")
    return {"message": "Cart cleared"}