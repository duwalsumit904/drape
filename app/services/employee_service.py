from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload

from app.models.user import User, Employee, UserType
from app.schemas.user import EmployeeCreate, EmployeeResponse
from app.services.auth_service import hash_password
from workers.email_task import send_welcome_email


async def create_employee(
        data: EmployeeCreate,
        db: AsyncSession
):
    result = await db.execute(
        select(User).where(User.email == data.email)

    )

    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # create user

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        user_type=UserType.employee
    )

    db.add(user)
    await db.flush()

    # create employee

    employee = Employee(
        user_id=user.id,
        full_name=data.full_name,
        role=data.role,
        department=data.department
    )

    db.add(employee)
    await db.commit()
    await db.refresh(user)
    # send welcome mail
    send_welcome_email.delay(email=data.email, full_name=data.full_name)
    return {
        "message":"Employee created successfully",
        "user_id": user.id,
        "email": user.email,
        "full_name": employee.full_name,
        "role": employee.role,
        "department": employee.department

    }


async def get_employees(db:AsyncSession):
    result = await db.execute(select(Employee).options(selectinload(Employee.user)))

    employee = result.scalars().all()

    data= [
        EmployeeResponse(
            id=emp.id,
            user_id=emp.user_id,
            full_name=emp.full_name,
            email=emp.user.email,
            phone=emp.phone,
            role=emp.role,
            department=emp.department,
        )
        for emp in employee
    ]

    print(data)  # Check what's actually being returned
    return data