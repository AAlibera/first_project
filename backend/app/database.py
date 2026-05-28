"""
PCB缺陷检测系统 - 数据库连接管理

提供数据库会话管理和连接配置。
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

# 构建数据库连接 URL
DATABASE_URL = (
    f"postgresql+psycopg2://{settings.database.username}:{settings.database.password}"
    f"@{settings.database.host}:{settings.database.port}/{settings.database.database}"
)

# 创建数据库引擎
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类（所有模型的父类）
Base = declarative_base()


def get_db():
    """
    数据库会话依赖注入函数
    
    用于 FastAPI 路由中获取数据库会话，使用完毕后自动关闭。
    
    Yields:
        Session: SQLAlchemy 数据库会话
    
    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库，创建所有表
    
    应该在应用启动时调用一次。
    """
    from app.models.database import (
        User,
        DetectionRecord,
        DetectionResult
    )
    Base.metadata.create_all(bind=engine)
