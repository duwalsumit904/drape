import enum
import uuid
from datetime import datetime
from sqlalchemy import String,Boolean,DateTime,ForeignKey,Enum
from sqlalchemy.orm import Mapped,mapped_column,relationship

from app.core.database import Base

#enums

class  UserType(str,enum.Enum):
    customer = "customer"
    employee = "employee"

class CustomerType(str, enum.Enum):
    normal = "normal"
    premium = "premium"
    business = "business"

class EmployeeRole(str,enum.Enum):
    admin = "admin"
    manager = "manager"
    support ="support"
    view_only = "view_only"



#user table - authentication only

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String,primary_key=True,default=lambda: str(uuid.uuid4()))
    email : Mapped[str] = mapped_column(String,unique=True,nullable=False)
    hashed_password: Mapped[str] = mapped_column(String,nullable=False)
    user_type: Mapped[UserType] = mapped_column(Enum(UserType),nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean,default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    #relationships

    customer: Mapped["Customer"] = relationship("Customer",back_populates="user",uselist=False)
    employee: Mapped["Employee"] = relationship("Employee" ,back_populates="user",uselist=False)


#customer table

class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=True)
    customer_type: Mapped[CustomerType] = mapped_column(Enum(CustomerType), default=CustomerType.normal)
    loyalty_points: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    #relationship
    user: Mapped["User"] = relationship("User",back_populates="customer")


#Employee table

class Employee(Base):
    __tablename__ = "employees"

    id         : Mapped[str]          = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id    : Mapped[str]          = mapped_column(String, ForeignKey("users.id"), nullable=False)
    full_name  : Mapped[str]          = mapped_column(String, nullable=False)
    phone      : Mapped[str]          = mapped_column(String, nullable=True)
    role       : Mapped[EmployeeRole] = mapped_column(Enum(EmployeeRole), default=EmployeeRole.support)
    department : Mapped[str]          = mapped_column(String, nullable=True)
    created_at : Mapped[datetime]     = mapped_column(DateTime, default=datetime.utcnow)

    # relationship
    user: Mapped["User"] = relationship("User", back_populates="employee")