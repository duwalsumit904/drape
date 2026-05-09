from fastapi import FastAPI
from app.api import auth
from fastapi import APIRouter
app = FastAPI(
    title="Drape API",
    version="1.0.0"
)

router = APIRouter()
#routers
app.include_router(auth.router,prefix="/auth",tags=["auth"])

@app.get("/health")
async def health():
    return {"status": "ok"}

@router.get("/tests")
async def test():
    return {"message": "auth working"}