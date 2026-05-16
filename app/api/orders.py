"""
Author: Sumit
Created: 5/12/2026
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from app.core.database import get_db
from app.core.redis_client import get_redis
from app.services import auth_service, order_service

router = APIRouter()


@router.post("/",status_code=201)
async def place_order(
        current_user = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis)

):
    return await order_service.place_order(
        current_user,db,redis
    )


@router.get("/")
async def get_orders(
        current_user = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db)

):
    return await order_service.get_orders(current_user,db)



@router.get("/{order_id}")
async  def get_order(
        order_id:str,
        db: AsyncSession  = Depends(get_db),
        current_user = Depends(auth_service.get_current_user)
):

    return await order_service.get_order(order_id,current_user, db)










