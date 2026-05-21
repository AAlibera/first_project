from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid

from app.config import settings

DATABASE_URL = (
    f"postgresql+psycopg2://{settings.database.username}:{settings.database.password}"
    f"@{settings.database.host}:{settings.database.port}/{settings.database.database}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(50))
    role = Column(String(20), default="user")
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    detection_records = relationship("DetectionRecord", back_populates="user")
    ai_qa_records = relationship("AIQARecord", back_populates="user")

class DetectionRecord(Base):
    __tablename__ = "detection_records"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    type = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")
    model_name = Column(String(50), nullable=False)
    model_version = Column(String(20), default="1.0.0")
    total_objects = Column(Integer, default=0)
    detection_time = Column(Float)
    original_image_key = Column(String(500))
    result_image_key = Column(String(500))
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    user = relationship("User", back_populates="detection_records")
    results = relationship("DetectionResult", back_populates="record")

class DetectionResult(Base):
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
    
    record = relationship("DetectionRecord", back_populates="results")

class TargetCategory(Base):
    __tablename__ = "target_categories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    chinese_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    icon_url = Column(String(500))
    color = Column(String(20), default="#10b981")
    enabled = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class AIQARecord(Base):
    __tablename__ = "ai_qa_records"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    model_name = Column(String(50))
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="ai_qa_records")

class ModelVersion(Base):
    __tablename__ = "model_versions"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False)
    version = Column(String(20), nullable=False)
    description = Column(Text)
    model_key = Column(String(500))
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database tables created successfully!")