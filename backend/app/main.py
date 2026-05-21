from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.detection import router as detection_router
from app.api.model import router as model_router
from app.api.user import router as user_router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="遥感图像目标检测平台 API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(detection_router, prefix="/api")
app.include_router(model_router, prefix="/api")
app.include_router(user_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": f"欢迎使用 {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.app_name}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )