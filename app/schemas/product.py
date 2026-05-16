from pydantic import BaseModel
from app.models.product import Gender, Season

class CategoryCreate(BaseModel):
    name     : str
    slug     : str
    parent_id: str | None = None
    gender   : Gender | None = None

class ProductCreate(BaseModel):
    name       : str
    slug       : str
    brand      : str
    description: str | None = None
    category_id: str
    gender     : Gender
    season     : Season = Season.all

class VariantCreate(BaseModel):
    sku        : str
    color      : str
    size       : str
    price      : float
    stock_count: int = 0
    image_url  : str | None = None

class ProductUpdate(BaseModel):
    name: str | None = None
    brand: str | None = None
    description: str | None = None
    gender: Gender | None = None
    season: Season | None = None
    is_active: bool | None = None