"""
PCB缺陷检测系统 - 主应用入口
"""

import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.detection import router as detection_router
from app.services.detection_service import detection_service
from app.services.model_manager import model_manager
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info(f"{settings.app_name} 启动中...")
    logger.info("=" * 50)

    static_dir = Path(settings.static_dir)
    static_dir.mkdir(exist_ok=True)

    uploads_dir = Path(settings.upload_dir)
    uploads_dir.mkdir(exist_ok=True)

    results_dir = Path(settings.result_dir)
    results_dir.mkdir(exist_ok=True)

    models_dir = Path(settings.models_dir)
    models_dir.mkdir(exist_ok=True)

    logger.info("扫描可用模型...")
    available_models = model_manager.scan_models()
    logger.info(f"发现 {len(available_models)} 个可用模型")

    if available_models:
        first_model = available_models[0]
        logger.info(f"自动加载模型: {first_model.name}")
        success = model_manager.set_current_model(first_model.name)
        if success:
            detection_service.load_model(first_model.path)
            logger.info(f"模型加载完成: {first_model.name}")
        else:
            logger.warning("模型自动加载失败")
    else:
        logger.warning("未发现任何模型文件，检测功能将以模拟模式运行")
        logger.info("请将模型文件(.pt, .pth, .onnx)放入 models 目录")

    logger.info("=" * 50)
    logger.info("系统启动完成")
    logger.info("=" * 50)

    yield

    logger.info("系统正在关闭...")


app = FastAPI(
    title=settings.app_name,
    description=f"""
    基于深度学习的PCB（印制电路板）缺陷检测系统API

    ## 功能特性

    - **单图检测**: 上传PCB图像进行缺陷检测
    - **模型管理**: 管理多个AI检测模型
    - **实时统计**: 查看检测统计数据

    ## 支持的缺陷类型

    1. 划痕 (scratch)
    2. 裂纹 (crack)
    3. 孔洞 (hole)
    4. 变形 (deformation)
    5. 缺失 (missing)
    6. 焊点异常 (solder)
    """,
    version=settings.app_version,
    lifespan=lifespan,
    debug=settings.debug
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

app.include_router(detection_router, prefix="/api")


@app.get("/")
async def root():
    current_model = model_manager.get_current_model()
    return {
        "message": f"欢迎使用 {settings.app_name} API",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "model_loaded": detection_service.is_model_loaded(),
        "current_model": current_model.name if current_model else None,
        "available_models": [m.name for m in model_manager.list_models()]
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "pcb-detection-api",
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 60)
    print(f"  {settings.app_name}")
    print("=" * 60)
    print(f"  API文档: http://localhost:{settings.port}/docs")
    print(f"  健康检查: http://localhost:{settings.port}/health")
    print("=" * 60 + "\n")

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
