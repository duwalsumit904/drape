
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from fastapi import HTTPException,status

from app.core.database import get_db
from app.models.user import User, Customer, Employee, UserType, EmployeeRole
from app.schemas.user import CustomerRegister, EmployeeCreate
from passlib.context import CryptContext
import uuid
from jose import jwt,JWTError
from datetime import datetime,timedelta
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_access_token(data:dict) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    data.update({"exp": expire})
    return jwt.encode(data,settings.SECRET_KEY,algorithm=settings.ALGORITHM)

def create_refresh_token(data:dict) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    data.update({"exp":expire})
    return jwt.encode(data,settings.SECRET_KEY,algorithm=settings.ALGORITHM)



pwd_context = CryptContext(schemes=["bcrypt"],deprecated="auto")
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str ,hashed: str) -> bool:
    return pwd_context.verify(plain,hashed)

async def register_customer(data: CustomerRegister,db:AsyncSession):

    #check email
    result = await db.execute(select(User).where(User.email == data.email))
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    #user creation

    user =  User(email=data.email,
                 hashed_password  = hash_password(data.password),
                 user_type = UserType.customer
                 )
    db.add(user)
    await db.flush()



    #create customer
    customer = Customer(user_id=user.id,
                        full_name=data.full_name,
                        phone=data.phone
                        )
    db.add(customer)
    await db.commit()
    await db.refresh(user)

    return user


async def login_user(email: str, password: str, db: AsyncSession):
    # find user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Email or Password"

        )

    # verify password
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid Email or Password"
        )

    #create_token
    token_data = {
        "user_id":user.id,
        "user_type":user.user_type.value,
        "email":user.email
    }


    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return access_token,refresh_token


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate":'Bearer'}
    )

    try:
        payload = jwt.decode(token,settings.SECRET_KEY,algorithms=[settings.ALGORITHM]
                             )
        user_id: str = payload.get("user_id")
        if not user_id:
            raise credentials_exception

    except JWTError:
        raise credentials_exception


    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise credentials_exception
    return user


