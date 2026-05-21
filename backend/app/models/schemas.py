from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DetectionBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_id: int
    class_name: str
    chinese_name: Optional[str] = None

class DetectionResult(BaseModel):
    detection_id: str
    image_url: str
    result_image_url: str
    boxes: List[DetectionBox]
    total_objects: int
    detection_time: float
    model_name: str
    created_at: datetime

class SingleDetectionResponse(BaseModel):
    success: bool
    message: str
    data: Optional[DetectionResult] = None

class HistoryItem(BaseModel):
    id: str
    image_url: str
    result_image_url: str
    total_objects: int
    created_at: datetime
    model_name: str
    filename: str = ""
    status: str = "completed"
    type: str = "single"
    time: str = ""
    count: int = 1
    detected_targets: list = []

class HistoryResponse(BaseModel):
    success: bool
    message: str
    data: List[HistoryItem]
    total: int

class TargetItem(BaseModel):
    id: int
    name: str
    chinese_name: str
    description: Optional[str] = None

class TargetListResponse(BaseModel):
    success: bool
    message: str
    data: List[TargetItem]

class ModelMetadata(BaseModel):
    name: str
    version: str
    created_at: datetime
    description: Optional[str] = None
    metrics: Optional[dict] = None
    config: Optional[dict] = None

class ModelItem(BaseModel):
    object_name: str
    metadata: Optional[ModelMetadata] = None
    public_url: str

class ModelListResponse(BaseModel):
    success: bool
    message: str
    data: List[ModelItem]
    latest: Optional[ModelItem] = None

class CurrentModelResponse(BaseModel):
    success: bool
    message: str
    data: ModelItem

class ReloadModelRequest(BaseModel):
    object_name: Optional[str] = None

class ReloadModelResponse(BaseModel):
    success: bool
    message: str
    data: Optional[ModelItem] = None

class UserRegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    nickname: Optional[str] = None

class UserLoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None