from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.user import CustomerRegister, TokenResponse
from app.services import auth_service
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

router = APIRouter()

@router.post("/register",status_code=status.HTTP_201_CREATED)
async def register_customer(
        data:CustomerRegister,
        db: AsyncSession= Depends(get_db)
):

    user = await auth_service.register_customer(data,db)
    return {
        "message": "registration successful",
        "user_id": user.id,
        "email":user.email
    }

@router.post("/login")
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)

):
    access_token,refresh_token = await auth_service.login_user(form_data.username,form_data.password,db)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }



@router.get("/me")
async def get_me(current_user = Depends(auth_service.get_current_user)):
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "user_type": current_user.user_type
    }
