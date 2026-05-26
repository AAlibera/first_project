"""
PCB缺陷检测系统 - 配置管理

采用 Pydantic 进行配置验证，结合路径管理模块实现可移植的配置系统。
"""

from pydantic import BaseModel, Field
from typing import List, Optional
import os
from pathlib import Path
from dotenv import load_dotenv

from app.utils.paths import Paths


class Settings(BaseModel):
    """
    应用配置类
    
    使用 Pydantic 进行配置验证和类型转换。
    所有路径相关的配置都通过 Paths 模块获取，确保可移植性。
    
    Attributes:
        app_name: 应用名称
        app_version: 应用版本
        debug: 是否开启调试模式
        host: 服务监听地址
        port: 服务监听端口
        cors_origins: CORS 允许的源
        confidence_threshold: 检测置信度阈值
        iou_threshold: IOU 阈值
        supported_image_formats: 支持的图片格式
        supported_model_formats: 支持的模型格式
        max_file_size: 最大文件大小（MB）
    """
    
    model_config = {"protected_namespaces": ()}
    
    app_name: str = Field(
        default_factory=lambda: os.getenv("APP_NAME", "PCB缺陷检测系统"),
        description="应用名称"
    )
    app_version: str = Field(
        default_factory=lambda: os.getenv("APP_VERSION", "1.0.0"),
        description="应用版本"
    )
    debug: bool = Field(
        default_factory=lambda: os.getenv("DEBUG", "true").lower() in ("true", "1", "yes"),
        description="是否开启调试模式"
    )
    host: str = Field(
        default_factory=lambda: os.getenv("HOST", "0.0.0.0"),
        description="服务监听地址"
    )
    port: int = Field(
        default_factory=lambda: int(os.getenv("PORT", "8000")),
        description="服务监听端口"
    )
    
    cors_origins: List[str] = Field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
        description="CORS 允许的源"
    )
    
    yolo_model_path: str = Field(
        default_factory=lambda: os.getenv("YOLO_MODEL_PATH", "models/yolo11n.pt"),
        description="YOLO 模型默认路径"
    )
    confidence_threshold: float = Field(
        default_factory=lambda: float(os.getenv("CONFIDENCE_THRESHOLD", "0.5")),
        ge=0.0,
        le=1.0,
        description="检测置信度阈值"
    )
    iou_threshold: float = Field(
        default_factory=lambda: float(os.getenv("IOU_THRESHOLD", "0.45")),
        ge=0.0,
        le=1.0,
        description="IOU 阈值"
    )
    
    supported_image_formats: List[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".bmp", ".gif"],
        description="支持的图片格式"
    )
    supported_model_formats: List[str] = Field(
        default=[".pt", ".pth", ".onnx", ".h5"],
        description="支持的模型格式"
    )
    max_file_size: int = Field(
        default_factory=lambda: int(os.getenv("MAX_FILE_SIZE", "50")),
        ge=1,
        description="最大文件大小（MB）"
    )
    
    log_level: str = Field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper(),
        description="日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_max_file_size: int = Field(
        default_factory=lambda: int(os.getenv("LOG_MAX_FILE_SIZE", "10")),
        ge=1,
        description="单个日志文件最大大小（MB）"
    )
    log_backup_count: int = Field(
        default_factory=lambda: int(os.getenv("LOG_BACKUP_COUNT", "10")),
        ge=1,
        description="保留的日志文件数量"
    )
    log_enable_json: bool = Field(
        default_factory=lambda: os.getenv("LOG_ENABLE_JSON", "false").lower() in ("true", "1", "yes"),
        description="是否启用JSON格式日志"
    )
    
    @property
    def static_dir(self) -> Path:
        """获取静态文件目录"""
        return Paths.static()
    
    @property
    def upload_dir(self) -> Path:
        """获取上传文件目录"""
        return Paths.uploads()
    
    @property
    def result_dir(self) -> Path:
        """获取检测结果目录"""
        return Paths.results()
    
    @property
    def models_dir(self) -> Path:
        """获取模型文件目录"""
        return Paths.models()
    
    @property
    def logs_dir(self) -> Path:
        """获取日志文件目录"""
        return Paths.logs()


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    获取配置实例（单例模式）
    
    使用懒加载，首次调用时才初始化配置。
    同时加载 .env 文件和初始化目录结构。
    
    Returns:
        Settings: 配置实例
    """
    global _settings
    
    if _settings is None:
        env_path = Paths.backend() / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        
        _settings = Settings()
        
        Paths.init_all_dirs()
    
    return _settings


settings = get_settings()
