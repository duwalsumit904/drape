from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.redis_client import get_redis
from app.schemas.user import ChangePassword, UpdateCustomerProfile
from app.services import auth_service, profile_service
from app.services import opt_service

router = APIRouter()

@router.get("/")

async def get_profile(
        current_user = Depends(auth_service.get_current_user),
        db:AsyncSession = Depends(get_db)
):
    return await profile_service.get_customer_profile(current_user,db)

@router.post("/request-otp")
async def request_opt(
        current_user = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis)
):
    return await opt_service.request_otp(
        current_user,db,redis
    )

@router.post("/change-password")
async def change_password(
        data: ChangePassword,
        current_user = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis)

):
    return await opt_service.change_password(
        current_user,
        data.otp,
        data.new_password,
        data.confirm_password,
        db,
        redis
    )
@router.patch("/update")
async def update_profile(
        data: UpdateCustomerProfile,
        current_user = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db)

):
    return await profile_service.update_customer_profile(
        current_user,
        data,
        db
    )

