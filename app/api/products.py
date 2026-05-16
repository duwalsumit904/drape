from fastapi import APIRouter, Depends
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from app.core.database import get_db
from app.core.redis_client import get_redis
from app.schemas.product import CategoryCreate, ProductCreate, VariantCreate, ProductUpdate
from app.services import auth_service, product_service


router = APIRouter()


@router.post("/categories",status_code=201)
async def create_category(
        data: CategoryCreate,
        db: AsyncSession = Depends(get_db),
        current_user = Depends(auth_service.require_admin)

):
    return await product_service.create_category(data,db)

#---------------------------------Products--------------------------------------

@router.post("/products",status_code=201)
async def create_product(
        data: ProductCreate,
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis),
        current_user = Depends(auth_service.require_admin)

):
    return await product_service.create_product(data,db,redis)

@router.get("/products")
async def get_products(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)

):
    return await product_service.get_products(db,redis)


@router.get("/products/{product_id}")
async def get_product(
        product_id: str,
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis)
):
    return await product_service.get_product(product_id,db,redis)




@router.post("/products/{product_id}/{variants}",status_code=201)
async def add_variant(
        product_id: str,
        data: VariantCreate,
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis),
        current_user = Depends(auth_service.require_admin)


):
    return await product_service.add_variant(product_id,data,db,redis)



@router.put("/products/{product_id}")
async def update_product(
        product_id: str,
        data: ProductUpdate,
        db:AsyncSession = Depends(get_db),
        redis:Redis = Depends(get_redis),
        current_user = Depends(auth_service.require_admin)
):
    return await product_service.update_product(product_id,data,db,redis)

@router.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user = Depends(auth_service.require_admin)
):
    return await product_service.delete_product(
        product_id, db, redis
    )