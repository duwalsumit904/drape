from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException,status
from app.models.user import User,Customer,UserType

async def get_customer_profile(current_user: User, db:AsyncSession):
    if current_user.user_type != UserType.customer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a Customer account"
        )


    result = await  db.execute(select(Customer).where(Customer.user_id == current_user.id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,detail="Customer profile not found"

        )


    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "user_type": current_user.user_type,
        "full_name": customer.full_name,
        "phone": customer.phone,
        "customer_type": customer.customer_type,
        "loyalty_points": customer.loyalty_points,
        "created_at": customer.created_at,

    }


async def update_customer_profile(current_user: User,data,db: AsyncSession):
    if current_user.user_type != UserType.customer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not a customer account")

    result = await db.execute(select(Customer).where(Customer.user_id == current_user.id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="customer profile not found")

    if data.full_name is not None:
        customer.full_name = data.full_name

    if data.phone is not None:
        customer.phone = data.phone


    await db.commit()
    await db.refresh(customer)

    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "full_name": customer.full_name,
        "phone": customer.phone,
        "customer_type": customer.customer_type,
        "loyalty_points": customer.loyalty_points,
    }
