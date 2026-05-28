"""
PCB缺陷检测系统 - 数据模型和Schema定义
定义API请求和响应的数据结构
"""

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime


# ============ 基础响应模型 ============

class SuccessResponse(BaseModel):
    """通用成功响应"""
    success: bool = True
    message: str = "操作成功"


class ErrorResponse(BaseModel):
    """通用错误响应"""
    success: bool = False
    message: str = "操作失败"
    detail: Optional[str] = None


# ============ 检测相关模型 ============

class DetectionBoxData(BaseModel):
    """检测框数据"""
    x1: float = Field(..., description="左上角X坐标")
    y1: float = Field(..., description="左上角Y坐标")
    x2: float = Field(..., description="右下角X坐标")
    y2: float = Field(..., description="右下角Y坐标")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    class_id: int = Field(..., description="类别ID")
    class_name: str = Field(..., description="类别名称")
    chinese_name: str = Field(..., description="中文名称")
    color: Optional[str] = Field(None, description="显示颜色")


class DetectionResultData(BaseModel):
    """检测结果数据"""
    detection_id: str = Field(..., description="检测ID")
    image_url: str = Field(..., description="原图URL")
    result_image_url: str = Field(..., description="结果图URL")
    boxes: List[DetectionBoxData] = Field(default_factory=list, description="检测框列表")
    total_objects: int = Field(0, ge=0, description="检测目标总数")
    detection_time: float = Field(..., ge=0, description="检测耗时(秒)")
    model_name: str = Field(..., description="使用的模型名称")
    created_at: str = Field(..., description="创建时间")


class DetectionResponse(BaseModel):
    """单图检测响应"""
    success: bool = True
    message: str = "检测成功"
    data: Optional[DetectionResultData] = None


class TargetItem(BaseModel):
    """目标类型项"""
    id: int = Field(..., description="目标ID")
    name: str = Field(..., description="目标名称")
    chinese_name: str = Field(..., description="中文名称")
    description: Optional[str] = Field(None, description="目标描述")
    color: Optional[str] = Field(None, description="显示颜色")


class TargetListResponse(BaseModel):
    """目标类型列表响应"""
    success: bool = True
    message: str = "获取成功"
    data: List[TargetItem] = Field(default_factory=list)


class DetectionStatsData(BaseModel):
    """检测统计数据"""
    total_detections: int = Field(0, description="总检测次数")
    total_objects: int = Field(0, description="检测到的总目标数")
    total_time: float = Field(0.0, description="总耗时(秒)")
    avg_detection_time: float = Field(0.0, description="平均检测耗时(秒)")
    last_detection_time: Optional[str] = Field(None, description="最后检测时间")


class DetectionStatsResponse(BaseModel):
    """检测统计响应"""
    success: bool = True
    message: str = "获取成功"
    data: DetectionStatsData


# ============ 模型相关模型 ============

class ModelItem(BaseModel):
    """模型项"""
    name: str = Field(..., description="模型名称")
    version: str = Field("1.0.0", description="模型版本")
    status: str = Field("unloaded", description="模型状态")
    path: Optional[str] = Field(None, description="模型路径")
    description: Optional[str] = Field(None, description="模型描述")
    class_names: Optional[List[str]] = Field(None, description="类别名称列表")
    created_at: Optional[str] = Field(None, description="创建时间")
    last_used: Optional[str] = Field(None, description="最后使用时间")


class ModelListResponse(BaseModel):
    """模型列表响应"""
    success: bool = True
    message: str = "获取成功"
    data: List[ModelItem] = Field(default_factory=list)


class CurrentModelResponse(BaseModel):
    """当前模型响应"""
    success: bool = True
    message: str = "获取成功"
    data: Optional[ModelItem] = None


# ============ 系统相关模型 ============

class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str = Field("healthy", description="服务状态")
    model_loaded: bool = Field(False, description="模型是否已加载")
    current_model: Optional[str] = Field(None, description="当前模型名称")
    service: str = Field("detection", description="服务名称")


# ============ 批量检测相关模型 ============

class BatchDetectionItem(BaseModel):
    """批量检测单项结果"""
    filename: str = Field(..., description="文件名")
    success: bool = Field(..., description="是否成功")
    result: Optional[DetectionResultData] = Field(None, description="检测结果")
    error: Optional[str] = Field(None, description="错误信息")


class BatchDetectionData(BaseModel):
    """批量检测数据"""
    total: int = Field(0, description="总数")
    success: int = Field(0, description="成功数")
    failed: int = Field(0, description="失败数")
    items: List[BatchDetectionItem] = Field(default_factory=list, description="结果列表")


class BatchDetectionResponse(BaseModel):
    """批量检测响应"""
    success: bool = True
    message: str = "批量检测完成"
    data: Optional[BatchDetectionData] = None


# ============ 视频检测相关模型 ============

class VideoDetectionData(BaseModel):
    """视频检测数据"""
    detection_id: str = Field(..., description="检测ID")
    video_url: str = Field(..., description="视频URL")
    total_frames: int = Field(0, description="总帧数")
    processed_frames: int = Field(0, description="已处理帧数")
    status: str = Field("processing", description="状态")
    created_at: str = Field(..., description="创建时间")


class VideoDetectionResponse(BaseModel):
    """视频检测响应"""
    success: bool = True
    message: str = "视频检测启动成功"
    data: Optional[VideoDetectionData] = None


# ============ 用户认证相关模型 ============

class UserBase(BaseModel):
    """用户基础信息"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")


class UserCreate(UserBase):
    """用户注册请求"""
    password: str = Field(..., min_length=6, max_length=128, description="密码")


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class UserResponse(UserBase):
    """用户响应信息"""
    id: str = Field(..., description="用户ID")
    nickname: Optional[str] = Field(None, description="昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    role: str = Field("user", description="角色")
    is_active: bool = Field(True, description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class UserUpdate(BaseModel):
    """用户信息更新请求"""
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    password: Optional[str] = Field(None, min_length=6, max_length=128, description="新密码")


class Token(BaseModel):
    """JWT令牌响应"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间(秒)")


class TokenData(BaseModel):
    """JWT令牌数据"""
    user_id: Optional[str] = None
    username: Optional[str] = None


class AuthResponse(BaseModel):
    """认证响应"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Token] = None


class UserAuthResponse(BaseModel):
    """用户信息响应"""
    success: bool = True
    message: str = "获取成功"
    data: Optional[UserResponse] = None


# ============ 历史记录相关模型 ============

class DetectionRecordItem(BaseModel):
    """检测历史记录项"""
    id: str = Field(..., description="记录ID")
    type: str = Field(..., description="检测类型")
    status: str = Field(..., description="检测状态")
    model_name: str = Field(..., description="模型名称")
    total_objects: int = Field(0, description="检测目标数")
    detection_time: Optional[float] = Field(None, description="检测耗时")
    original_image_url: Optional[str] = Field(None, description="原始图片URL")
    result_image_url: Optional[str] = Field(None, description="结果图片URL")
    created_at: datetime = Field(..., description="创建时间")
    boxes: Optional[List[DetectionBoxData]] = Field(None, description="检测框列表")


class DetectionHistoryResponse(BaseModel):
    """检测历史列表响应"""
    success: bool = True
    message: str = "获取成功"
    data: List[DetectionRecordItem] = Field(default_factory=list)
    total: int = Field(0, description="总记录数")
    page: int = Field(1, description="当前页")
    page_size: int = Field(20, description="每页数量")


class DetectionRecordDetailResponse(BaseModel):
    """检测记录详情响应"""
    success: bool = True
    message: str = "获取成功"
    data: Optional[DetectionRecordItem] = None
