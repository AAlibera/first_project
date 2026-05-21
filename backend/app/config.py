from pydantic import BaseModel
from typing import List
import os
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

class DatabaseConfig(BaseModel):
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    username: str = os.getenv("DB_USERNAME", "rsod_user")
    password: str = os.getenv("DB_PASSWORD", "rsod_password")
    database: str = os.getenv("DB_DATABASE", "rsod_platform")

class MinIOConfig(BaseModel):
    host: str = os.getenv("MINIO_HOST", "localhost")
    port: int = int(os.getenv("MINIO_PORT", "9000"))
    access_key: str = os.getenv("MINIO_ACCESS_KEY", "admin")
    secret_key: str = os.getenv("MINIO_SECRET_KEY", "minio_password")
    secure: bool = os.getenv("MINIO_SECURE", "false").lower() in ("true", "1", "yes")
    original_bucket: str = "rsod-original"
    results_bucket: str = "rsod-results"
    models_bucket: str = "rsod-models"

class RedisConfig(BaseModel):
    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    password: str = os.getenv("REDIS_PASSWORD", "redis_password")

class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "RSOD Detection Platform")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    debug: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    static_dir: str = "static"
    upload_dir: str = "static/uploads"
    result_dir: str = "static/results"
    
    database: DatabaseConfig = DatabaseConfig()
    minio: MinIOConfig = MinIOConfig()
    redis: RedisConfig = RedisConfig()
    
    cors_origins: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    
    yolo_model_path: str = os.getenv("YOLO_MODEL_PATH", "models/yolo11n.pt")
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
    iou_threshold: float = float(os.getenv("IOU_THRESHOLD", "0.45"))

settings = Settings()