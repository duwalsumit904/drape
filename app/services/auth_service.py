
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
from redis.asyncio import Redis
from workers.email_task import send_welcome_email

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


    #send welcome mail
    send_welcome_email.delay(email=data.email,full_name=data.full_name)

    return user


async def login_user(email: str, password: str, db: AsyncSession,redis:Redis):
    # find user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Email or Password"

        )
    # add after user not found check
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact support."
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

    await redis.set(f"session:{refresh_token}",
                    user.id,
                    ex=60*60*24*7
                    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_type": user.user_type.value,  # ← convenience ✅
        "user_id": user.id  # ← convenience ✅
    }


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


async def logout_user(refresh_token:str, redis:Redis):
    #delete session from redis

    deleted = await redis.delete(f"session:{refresh_token}")
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or already logged out"
        )

    return {"message":"logged out successfully"}



async def refresh_access_token(refresh_token: str, redis: Redis,db:AsyncSession):
    user_id = await redis.get(f"session:{refresh_token}")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session Expired, Please login again"
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="User not found")


    # create new access token

    token_data = {
        "user_id": user.id,
        "user_type": user.user_type.value,
        "email": user.email
    }

    new_access_token = create_access_token(token_data)
    return {"access_token":new_access_token,"token_type": "bearer"}




async def require_admin(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)

):
    if current_user.user_type != UserType.employee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Employees Only")

    #fetch employee record
    result = await  db.execute(select(Employee).where(Employee.user_id == current_user.id))

    employee = result.scalar_one_or_none()

    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="Employee record not found")

    if employee.role != EmployeeRole.admin:
        raise HTTPException(

            status_code=status.HTTP_403_FORBIDDEN , detail="Admin access required"
        )



    return current_user
