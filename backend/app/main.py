"""
PCB缺陷检测系统 - 主应用入口

FastAPI 应用入口，负责应用初始化、路由注册、中间件配置等。
采用路径管理模块和日志管理模块确保系统的可移植性和可维护性。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.detection import router as detection_router
from app.api.auth import router as auth_router
from app.api.history import router as history_router
from app.services.detection_service import detection_service
from app.services.model_manager import model_manager
from app.config import settings
from app.utils.paths import Paths
from app.utils.logging import configure_logging, get_logger, set_request_id, clear_request_id
from app.database import init_db
import uuid

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    启动时初始化目录结构、配置日志、扫描模型、加载默认模型。
    关闭时清理资源。
    """
    logger.info("=" * 50)
    logger.info(f"{settings.app_name} 启动中...")
    logger.info("=" * 50)

    configure_logging(
        log_level=settings.log_level,
        log_dir=settings.logs_dir,
        max_file_size=settings.log_max_file_size * 1024 * 1024,
        backup_count=settings.log_backup_count,
        enable_json=settings.log_enable_json,
    )

    logger.info(f"日志级别: {settings.log_level}")
    logger.info(f"项目根目录: {Paths.root()}")

    Paths.init_all_dirs()

    logger.info("初始化数据库...")
    try:
        init_db()
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.warning(f"数据库初始化失败: {e}")
        logger.warning("请确保 PostgreSQL 服务已启动并配置正确")

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
        logger.info(f"请将模型文件(.pt, .pth, .onnx)放入 {Paths.models()} 目录")

    logger.info("=" * 50)
    logger.info("系统启动完成")
    logger.info("=" * 50)

    yield

    logger.info("系统正在关闭...")


app = FastAPI(
    title=settings.app_name,
    description="""
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


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """
    请求ID中间件

    为每个请求分配唯一的请求ID，便于日志追踪和问题定位。
    """
    request_id = str(uuid.uuid4())
    set_request_id(request_id)

    try:
        response = await call_next(request)
    finally:
        clear_request_id()

    response.headers["X-Request-ID"] = request_id
    return response


app.mount("/static", StaticFiles(directory=str(Paths.static())), name="static")

# 注册路由（API路由已经包含 /api 前缀，不需要再添加）
app.include_router(detection_router)
app.include_router(auth_router)
app.include_router(history_router)


@app.get("/")
async def root():
    """
    根路径

    返回系统基本信息和可用模型列表。
    """
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
    """
    健康检查端点

    用于监控系统运行状态。
    """
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
        log_level="warning"
    )
