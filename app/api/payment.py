"""
Author: Sumit
Created: 5/13/2026
"""


from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from app.core.database import get_db
from app.core.redis_client import get_redis
from app.models.user import User
from app.services.payment_service import create_payment_intent, confirm_payment
from app.services import auth_service, order_service

router = APIRouter()

@router.post("/create-intent/{order_id}")
async def create_intent(
        order_id: str,
        db: AsyncSession = Depends(get_db),
        current_user :User =Depends(auth_service.get_current_user)
):
    return await create_payment_intent(
        order_id = order_id,
        db = db,
        user_id= str(current_user.id)
    )

@router.post("/confirm/{order_id}")
async def confirm(
        order_id: str,
        payment_intent_id: str,
        db: AsyncSession = Depends(get_db),
        redis: Redis =Depends(get_redis),
        current_user: User = Depends(auth_service.get_current_user)
):
    return await confirm_payment(order_id = order_id,payment_intent_id=payment_intent_id,
                                 db=db,redis=redis,
                                 current_user=current_user)