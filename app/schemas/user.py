from pydantic import BaseModel, EmailStr
from enum import Enum

class CustomerType(str, Enum):
    normal   = "normal"
    premium  = "premium"
    business = "business"

class EmployeeRole(str, Enum):
    admin     = "admin"
    manager   = "manager"
    support   = "support"
    view_only = "view_only"

# Customer Registration
class CustomerRegister(BaseModel):
    email    : EmailStr
    password : str
    full_name: str
    phone    : str | None = None

# Employee Creation (admin only)
class EmployeeCreate(BaseModel):
    email     : EmailStr
    password  : str
    full_name : str
    role      : EmployeeRole
    department: str | None = None

# Login
class LoginRequest(BaseModel):
    email   : EmailStr
    password: str

# Token Response
class TokenResponse(BaseModel):
    access_token : str
    refresh_token: str
    token_type   : str = "bearer"