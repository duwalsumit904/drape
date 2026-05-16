from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from redis.asyncio import ConnectionPool,Redis
from app.core.config import settings
from app.api import auth,profile,admin,products,cart,orders,payment
from app.messaging.rabbitmq import get_rabbit_connection,close_rabbit_connection
# ← add payments


redis_pool: ConnectionPool = None
@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_pool
    redis_pool= ConnectionPool.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        max_connections=20,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True

    )

    print("redis connected")

#-------------------------RABBITMQ------------------------
    await get_rabbit_connection()
    print("RABBITMQ connected")

#__________________________END OF RABBITMQ_________________
    yield
    await redis_pool.disconnect()
    print("redis pool closed")

    await close_rabbit_connection()

    print("RABBITMQ closed")



app = FastAPI(
    title="DRAPE API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router,     prefix="/auth",     tags=["auth"])
app.include_router(profile.router,  prefix="/profile",  tags=["profile"])
app.include_router(admin.router,    prefix="/admin",    tags=["admin"])
app.include_router(products.router, prefix="/admin",    tags=["products"])
app.include_router(cart.router,     prefix="/cart",     tags=["cart"])
app.include_router(orders.router,   prefix="/orders",   tags=["orders"])

app.include_router(payment.router, prefix="/payments", tags=["payments"])
async def health():
    return {"status": "ok"}