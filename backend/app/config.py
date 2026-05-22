"""
PCB缺陷检测系统 - 配置管理
"""

from pydantic import BaseModel
from typing import List, Optional
import os
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")


class Settings(BaseModel):
    """应用配置"""
    app_name: str = os.getenv("APP_NAME", "PCB缺陷检测系统")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    debug: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    # 目录配置
    static_dir: str = "static"
    upload_dir: str = "static/uploads"
    result_dir: str = "static/results"
    models_dir: str = "models"

    # CORS配置
    cors_origins: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

    # YOLO模型配置
    yolo_model_path: str = os.getenv("YOLO_MODEL_PATH", "models/yolo11n.pt")
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
    iou_threshold: float = float(os.getenv("IOU_THRESHOLD", "0.45"))

    # 支持的图片格式
    supported_image_formats: List[str] = [".jpg", ".jpeg", ".png", ".bmp", ".gif"]

    # 支持的模型格式
    supported_model_formats: List[str] = [".pt", ".pth", ".onnx", ".h5"]

    # 最大文件大小（MB）
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "50"))


settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings
