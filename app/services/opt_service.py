import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from redis.asyncio import Redis
from app.models.user import User, Customer
from app.services.auth_service import hash_password
from workers.email_task import send_otp_email


def generate_otp() -> str:
    return str(random.randint(100000, 999999))

async def request_otp(
        current_user:User,
        db:AsyncSession,
        redis: Redis
):
    result = await  db.execute(select(Customer).where(Customer.user_id==current_user.id))
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="customer not found")

    existing = await redis.get(f"otp:{current_user.id}")
    if existing:
        ttl = await redis.ttl(f"otp:{current_user.id}")
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,detail=f"OTP already send. Try again in {ttl} seconds")

    #generate OTP

    otp = generate_otp()

    #store in redis 5 min

    await redis.set(f"otp:{current_user.id}",
                        otp,
                    ex=300
                    )


    #send OTP via celery
    send_otp_email.delay(email=current_user.email,otp=otp,full_name=customer.full_name)


    return {"message": "OTP sent to your mail"}



async def change_password(
        current_user: User,
        otp: str,
        new_password: str,
        confirm_password: str,
        db: AsyncSession,
        redis: Redis,
):

    #check the password
    if new_password != confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Passwords do not match")

    #get password form redis
    stored_otp = await redis.get(f"otp:{current_user.id}")
    if not stored_otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="OTP expired or not requested")

    #verify OTP
    if  stored_otp != otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Invalid OTP")

    await redis.delete(f"otp:{current_user.id}")

    #update password

    current_user.hashed_password = hash_password(new_password)
    db.add(current_user)
    await db.commit()

    return {"message":"Password changed successfully"}



