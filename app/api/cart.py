from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis_client import get_redis
from app.schemas.cart import AddToCart,UpdateCart
from app.services import auth_service, cart_service

router = APIRouter()


@router.post("/")
async def add_to_cart(
        data: AddToCart,
        current_user=Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis)

):
    return await cart_service.add_to_cart(
        current_user, data.variant_id, data.quantity, db, redis
    )


@router.get("/")
async def get_cart(
        current_user=Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis)
):
    return await cart_service.get_cart(current_user, db, redis)


@router.delete("/{variant_id}")
async def remove_from_cart(
        variant_id: str,
        current_user=Depends(auth_service.get_current_user),
        redis: Redis = Depends(get_redis)

):
    return await cart_service.remove_from_cart(current_user,variant_id,redis)


@router.put("/{variant_id}")
async def update_cart(
    variant_id: str,
    data: UpdateCart,
    current_user = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    return await cart_service.update_cart_item(
        current_user, variant_id,
        data.quantity, db, redis
    )

@router.delete("/")
async def clear_cart(
    current_user = Depends(auth_service.get_current_user),
    redis: Redis = Depends(get_redis)
):
    return await cart_service.clear_cart(current_user, redis)



