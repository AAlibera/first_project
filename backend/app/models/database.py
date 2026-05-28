"""
PCB缺陷检测系统 - 数据库 ORM 模型

定义数据库表结构，使用 SQLAlchemy ORM 进行映射。
"""

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, 
    Text, Boolean, ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class User(Base):
    """
    用户表模型
    
    存储系统用户信息，包括认证信息和个人资料。
    
    Attributes:
        id: 用户唯一标识 (UUID)
        username: 用户名 (唯一)
        email: 邮箱 (唯一)
        password_hash: 密码哈希值
        nickname: 昵称
        avatar_url: 头像 URL
        role: 用户角色 (user/admin)
        is_active: 是否激活
        created_at: 创建时间
        updated_at: 更新时间
        detection_records: 关联的检测记录
    """
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(50))
    avatar_url = Column(String(500))
    role = Column(String(20), default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系: 一个用户可以有多个检测记录
    detection_records = relationship("DetectionRecord", back_populates="user", cascade="all, delete-orphan")


class DetectionRecord(Base):
    """
    检测记录表模型
    
    存储用户的检测历史记录。
    
    Attributes:
        id: 记录唯一标识 (UUID)
        user_id: 所属用户 ID
        type: 检测类型 (single/batch/folder/video/camera)
        status: 检测状态 (pending/processing/completed/failed)
        model_name: 使用的模型名称
        total_objects: 检测到的目标总数
        detection_time: 检测耗时 (秒)
        original_image_path: 原始图片路径
        result_image_path: 结果图片路径
        error_message: 错误信息
        created_at: 创建时间
        updated_at: 更新时间
        user: 所属用户
        results: 检测结果
    """
    __tablename__ = "detection_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    type = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")
    model_name = Column(String(50), nullable=False)
    total_objects = Column(Integer, default=0)
    detection_time = Column(Float)
    original_image_path = Column(String(500))
    result_image_path = Column(String(500))
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系: 属于某个用户
    user = relationship("User", back_populates="detection_records")
    # 关系: 包含多个检测结果
    results = relationship("DetectionResult", back_populates="record", cascade="all, delete-orphan")


class DetectionResult(Base):
    """
    检测结果表模型
    
    存储单个检测任务的详细检测结果。
    
    Attributes:
        id: 结果唯一标识 (UUID)
        record_id: 所属记录 ID
        x1: 检测框左上角 X 坐标
        y1: 检测框左上角 Y 坐标
        x2: 检测框右下角 X 坐标
        y2: 检测框右下角 Y 坐标
        confidence: 置信度 (0-1)
        class_id: 类别 ID
        class_name: 英文类别名
        chinese_name: 中文类别名
        record: 所属记录
    """
    __tablename__ = "detection_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    record_id = Column(String(36), ForeignKey("detection_records.id", ondelete="CASCADE"), nullable=False)
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    class_id = Column(Integer, nullable=False)
    class_name = Column(String(50), nullable=False)
    chinese_name = Column(String(50))

    # 关系: 属于某条检测记录
    record = relationship("DetectionRecord", back_populates="results")
