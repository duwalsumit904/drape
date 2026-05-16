from pydantic import BaseModel, EmailStr, Field, field_validator
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
    password : str = Field(min_length=8,max_length=50,description="Password must be at least 8 character long ")
    full_name: str = Field(min_length=4 , max_length=100)
    phone    : str | None = Field(default=None,max_length=15)

    @field_validator("full_name")
    @classmethod
    def full_name_must_not_be_empty(cls,v):
        if not v.strip():
            raise ValueError("Full name cannot be empty")

        return v.strip()


    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, v):
        if len(v) < 8:
            raise ValueError(
                "Password must be at least 8 characters"
            )
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        return v

    @field_validator("phone")
    @classmethod
    def phone_format(cls, v):
        if v is None:
            return v
        if not v.replace("+", "").replace("-", "").isdigit():
            raise ValueError("Invalid phone number format")
        return v

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


class CustomerProfileResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    phone: str | None
    customer_type: CustomerType
    loyalty_points: int


class RequestOTP(BaseModel):
    pass

class ChangePassword(BaseModel):
    otp: str
    new_password: str
    confirm_password: str

class UpdateCustomerProfile(BaseModel):
    full_name: str | None = None
    phone: str | None = None

    model_config = {"from_attributes":True}

class UpdateEmployee(BaseModel):
    full_name: str | None = None
    phone: str | None = None

    model_config = {"from_attributes": True}

class EmployeeUserResponse(BaseModel):
    id: str
    email: str
    model_config = {"from_attributes": True}

class EmployeeResponse(BaseModel):
    id: str
    user_id: str
    full_name: str
    email: str
    phone: str | None
    role: EmployeeRole
    department: str | None
    # created_at: datetime

    model_config = {"from_attributes": True}




