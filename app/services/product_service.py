import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from redis.asyncio import Redis
from app.models.product import Category, Product, ProductVariant
from app.schemas.product import CategoryCreate, ProductCreate, VariantCreate, ProductUpdate


async def create_category(data: CategoryCreate,db:AsyncSession):
    result = await db.execute(select(Category).where(Category.slug==data.slug)
                              )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Category slug already exists")

    category = Category(
        name=data.name,
        slug=data.slug,
        parent_id=data.parent_id,
        gender=data.gender
    )

    db.add(category)
    await db.commit()
    await db.refresh(category)

    return category

########################################product##################################################


async def create_product(data:ProductCreate,db:AsyncSession,redis:Redis):
    #check slug exists

    result = await db.execute(select(Product).where(Product.slug == data.slug))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,detail="Product slug already exists"

        )

    #check category exists
    cat = await db.execute(select(Category).where(Category.id == data.category_id))

    if not cat.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    product = Product(
        name=data.name,
        slug=data.slug,
        brand=data.brand,
        description=data.description,
        category_id=data.category_id,
        gender=data.gender,
        season=data.season

    )

    db.add(product)
    await db.commit()

    await db.refresh(product)


    await redis.delete("products:listing")


    return product




async def get_products(db: AsyncSession, redis: Redis):
    # check cache first
    cached = await redis.get("products:listing")
    if cached:
        return json.loads(cached)

    # fetch from DB
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.variants))
        .where(Product.is_active == True)
    )
    products = result.scalars().all()

    # serialize
    data = [
        {
            "id"         : p.id,
            "name"       : p.name,
            "slug"       : p.slug,
            "brand"      : p.brand,
            "gender"     : p.gender,
            "season"     : p.season,
            "variants"   : [
                {
                    "id"         : v.id,
                    "sku"        : v.sku,
                    "color"      : v.color,
                    "size"       : v.size,
                    "price"      : v.price,
                    "stock_count": v.stock_count,
                    "is_active"  : v.is_active
                }
                for v in p.variants
            ]
        }
        for p in products
    ]

    # store in cache 5 min
    await redis.set("products:listing", json.dumps(data), ex=300)

    return data


# ---------------------------GET SINGLE PRODUCT-------------------------------------------------------

async def get_product(
        product_id: str,db:AsyncSession,redis: Redis
):
    cached = await redis.get(f"product:{product_id}")

    if cached:
        return json.loads(cached)

    #fetch from db
    result = await  db.execute(select(Product)
                               .options(selectinload(Product.variants))
                               .where(Product.id == product_id))

    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Product Not Found")

    data = {
        "id": product.id,
        "name": product.name,
        "slug": product.slug,
        "brand": product.brand,
        "description": product.description,
        "gender": product.gender,
        "season": product.season,
        "is_active": product.is_active,
        "variants": [
            {
                "id": v.id,
                "sku": v.sku,
                "color": v.color,
                "size": v.size,
                "price": v.price,
                "stock_count": v.stock_count,
                "is_active": v.is_active
            }
            for v in product.variants
        ]
    }

    await redis.set(f"product:{product_id}",json.dumps(data),ex=600)
    return data



#-------------------------------------------add Variant-------------------------------------------------------------

async def add_variant(product_id: str,
                      data: VariantCreate,
                      db:AsyncSession,
                      redis: Redis
                      ):
    result = await db.execute(select(Product).where(Product.id == product_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,detail="Product not found"

        )

    sku_check = await db.execute(
        select(ProductVariant).where(ProductVariant.sku == data.sku)
    )

    if sku_check.scalar_one_or_none():
        HTTPException(status_code=status.HTTP_409_CONFLICT,detail="SKU already exists")

    variant = ProductVariant(
        product_id=product_id,
        sku=data.sku,
        color=data.color,
        size=data.size,
        price=data.price,
        stock_count=data.stock_count
    )



    db.add(variant)
    await db.commit()
    await db.refresh(variant)

    #clear cache
    await redis.delete(f"product:{product_id}")
    await redis.delete("product:listing")

    return  variant






async def update_product(product_id: str,data: ProductUpdate,db:AsyncSession,redis:Redis):
    result = await  db.execute(select(Product).where(Product.id == product_id))

    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    if data.name is not None: product.name = data.name
    if data.brand is not None: product.brand = data.brand
    if data.description is not None: product.description = data.description
    if data.gender is not None: product.gender = data.gender
    if data.season is not None: product.season = data.season
    if data.is_active is not None: product.is_active = data.is_active

    await db.commit()
    await db.refresh(product)

    await redis.delete(f"product:{product_id
    }")
    await redis.delete(f"product:listing")
    return product




async def delete_product(
        product_id: str,
        db: AsyncSession,
        redis: Redis
):

    result =  await db.execute(select(Product).where(Product.id == product_id))

    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    await db.delete(product)
    await db.commit()


    await redis.delete(f"product:{product_id}")
    await redis.delete(f"product:listing")

    return {"message": "Product deleted successfully"}

















