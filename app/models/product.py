import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum, Integer, Float, ARRAY, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import enum

class Gender(str, enum.Enum):
    men     = "men"
    women   = "women"
    unisex  = "unisex"

class Season(str, enum.Enum):
    summer = "summer"
    winter = "winter"
    spring = "spring"
    autumn = "autumn"
    all    = "all"

# Category
class Category(Base):
    __tablename__ = "categories"

    id       : Mapped[str]           = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name     : Mapped[str]           = mapped_column(String, nullable=False)
    slug     : Mapped[str]           = mapped_column(String, unique=True, nullable=False)
    parent_id: Mapped[str | None]    = mapped_column(String, ForeignKey("categories.id"), nullable=True)
    gender   : Mapped[Gender | None] = mapped_column(Enum(Gender), nullable=True)

    # relationships
    products : Mapped[list["Product"]]  = relationship("Product", back_populates="category")
    parent   : Mapped["Category | None"]= relationship("Category", remote_side="Category.id")

# Product
class Product(Base):
    __tablename__ = "products"

    id         : Mapped[str]          = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name       : Mapped[str]          = mapped_column(String, nullable=False)
    slug       : Mapped[str]          = mapped_column(String, unique=True, nullable=False)
    brand      : Mapped[str]          = mapped_column(String, nullable=False)
    description: Mapped[str | None]   = mapped_column(Text, nullable=True)
    category_id: Mapped[str]          = mapped_column(String, ForeignKey("categories.id"), nullable=False)
    gender     : Mapped[Gender]       = mapped_column(Enum(Gender), nullable=False)
    season     : Mapped[Season]       = mapped_column(Enum(Season), default=Season.all)
    is_active  : Mapped[bool]         = mapped_column(Boolean, default=True)
    created_at : Mapped[datetime]     = mapped_column(DateTime, default=datetime.utcnow)
    updated_at : Mapped[datetime]     = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    category : Mapped["Category"]            = relationship("Category", back_populates="products")
    variants : Mapped[list["ProductVariant"]]= relationship("ProductVariant", back_populates="product")

# ProductVariant
class ProductVariant(Base):
    __tablename__ = "product_variants"

    id         : Mapped[str]      = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id : Mapped[str]      = mapped_column(String, ForeignKey("products.id"), nullable=False)
    sku        : Mapped[str]      = mapped_column(String, unique=True, nullable=False)
    color      : Mapped[str]      = mapped_column(String, nullable=False)
    size       : Mapped[str]      = mapped_column(String, nullable=False)
    price      : Mapped[float]    = mapped_column(Float, nullable=False)
    stock_count: Mapped[int]      = mapped_column(Integer, default=0)
    is_active  : Mapped[bool]     = mapped_column(Boolean, default=True)
    created_at : Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # relationships
    product: Mapped["Product"]           = relationship("Product", back_populates="variants")
    images : Mapped[list["ProductImage"]]= relationship("ProductImage", back_populates="variant")

# ProductImage
class ProductImage(Base):
    __tablename__ = "product_images"

    id        : Mapped[str]      = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    variant_id: Mapped[str]      = mapped_column(String, ForeignKey("product_variants.id"), nullable=False)
    url       : Mapped[str]      = mapped_column(String, nullable=False)
    position  : Mapped[int]      = mapped_column(Integer, default=0)
    is_primary: Mapped[bool]     = mapped_column(Boolean, default=False)

    # relationship
    variant: Mapped["ProductVariant"] = relationship("ProductVariant", back_populates="images")