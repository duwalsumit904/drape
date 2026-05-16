import asyncio
from app.core.database import AsyncSessionLocal
from app.models.user import User, Employee, UserType, EmployeeRole
from app.services.auth_service import hash_password


async def create_admin():
    async with AsyncSessionLocal() as db:
        user = User(
            email="sduwal1414@gmail.com",
            hashed_password=hash_password("admin123"),
            user_type=UserType.employee
        )

        db.add(user)
        await db.flush()

        #create Employee
        employee = Employee(
            user_id=user.id,
            full_name="Super Admin",
            role=EmployeeRole.admin,
            department="Management"
        )

        db.add(employee)
        await db.commit()
        print(f"admin created:{ user.email }")

asyncio.run(create_admin())