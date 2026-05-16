from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.user import EmployeeCreate, EmployeeResponse
from app.services import auth_service, employee_service


router = APIRouter()
@router.post("/employees",status_code=201)
async def create_employee(
        data: EmployeeCreate,
        db: AsyncSession = Depends(get_db),
        current_user = Depends(auth_service.require_admin)

):
    return await employee_service.create_employee(data,db)

@router.get("/employees",response_model=list[EmployeeResponse])
async def get_employees(
        db: AsyncSession = Depends(get_db),
        current_user = Depends(auth_service.require_admin)
):
         return await employee_service.get_employees(db)

