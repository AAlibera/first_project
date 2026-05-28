"""
PCB缺陷检测系统 - 用户认证 API

提供用户注册、登录、JWT 认证、用户信息管理等功能。
符合生产环境规范，包含完善的错误处理和日志记录。
"""

from datetime import datetime, timedelta
from typing import Optional
import hashlib
import hmac
import base64

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.database import get_db
from app.models.database import User
from app.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    TokenData,
    AuthResponse,
    UserAuthResponse,
    UserUpdate
)
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# 使用固定的密钥用于密码哈希（生产环境应该放在环境变量中）
SECRET_KEY = settings.jwt.secret_key if hasattr(settings, 'jwt') else "your-secret-key-change-in-production"

# OAuth2 认证方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)

router = APIRouter(prefix="/api/auth", tags=["认证"])


# ============ 工具函数 ============

def get_password_hash(password: str) -> str:
    """
    生成密码哈希
    
    使用 HMAC-SHA256 算法，没有长度限制
    """
    # 将密码转换为字节
    password_bytes = password.encode('utf-8')
    secret_bytes = SECRET_KEY.encode('utf-8') if isinstance(SECRET_KEY, str) else SECRET_KEY
    
    # 使用 HMAC-SHA256 哈希
    hash_obj = hmac.new(secret_bytes, password_bytes, hashlib.sha256)
    # 转换为 base64 字符串，便于存储
    return base64.b64encode(hash_obj.digest()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    对比输入的密码和存储的哈希值
    """
    # 重新计算输入密码的哈希
    computed_hash = get_password_hash(plain_password)
    # 使用安全的比较方法，防止时序攻击
    return hmac.compare_digest(computed_hash, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT 访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=settings.jwt.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt.secret_key,
        algorithm=settings.jwt.algorithm
    )
    return encoded_jwt


def get_user(db: Session, username: str) -> Optional[User]:
    """根据用户名或邮箱获取用户"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = db.query(User).filter(User.email == username).first()
    return user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """认证用户"""
    user = get_user(db, username)
    if not user:
        logger.warning(f"登录失败: 用户不存在 - {username}")
        return None
    if not verify_password(password, user.password_hash):
        logger.warning(f"登录失败: 密码错误 - {username}")
        return None
    if not user.is_active:
        logger.warning(f"登录失败: 用户已禁用 - {username}")
        return None
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """获取当前认证用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(
            token,
            settings.jwt.secret_key,
            algorithms=[settings.jwt.algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前激活用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    return current_user


def user_to_response(user: User) -> UserResponse:
    """将用户模型转换为响应模型"""
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


# ============ API 路由 ============

@router.post("/register", response_model=AuthResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    用户注册

    创建新用户账号，自动登录并返回 JWT 令牌。
    """
    logger.info(f"注册请求 - 用户名: {user_data.username}, 邮箱: {user_data.email}")

    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        logger.warning(f"注册失败: 用户名已存在 - {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 检查邮箱是否已存在
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        logger.warning(f"注册失败: 邮箱已被注册 - {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )

    # 创建新用户
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        nickname=user_data.username  # 默认昵称同用户名
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"用户注册成功: {new_user.username} (ID: {new_user.id})")

    # 生成访问令牌
    access_token_expires = timedelta(minutes=settings.jwt.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": new_user.username, "user_id": new_user.id},
        expires_delta=access_token_expires
    )

    return AuthResponse(
        success=True,
        message="注册成功",
        data=Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds())
        )
    )


@router.post("/login", response_model=AuthResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    用户登录 (OAuth2 格式)

    使用用户名/邮箱和密码登录，获取 JWT 令牌。
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"用户登录成功: {user.username}")

    # 生成访问令牌
    access_token_expires = timedelta(minutes=settings.jwt.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )

    return AuthResponse(
        success=True,
        message="登录成功",
        data=Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds())
        )
    )


@router.post("/login-json", response_model=AuthResponse)
async def login_json(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录 (JSON 格式)

    使用用户名/邮箱和密码登录，获取 JWT 令牌。
    """
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"用户登录成功: {user.username}")

    # 生成访问令牌
    access_token_expires = timedelta(minutes=settings.jwt.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )

    return AuthResponse(
        success=True,
        message="登录成功",
        data=Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds())
        )
    )


@router.get("/me", response_model=UserAuthResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前用户信息

    返回当前登录用户的详细信息。
    """
    return UserAuthResponse(
        success=True,
        message="获取成功",
        data=user_to_response(current_user)
    )


@router.put("/me", response_model=UserAuthResponse)
async def update_current_user_info(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    更新当前用户信息

    修改用户的昵称、头像或密码。
    """
    if user_update.nickname is not None:
        current_user.nickname = user_update.nickname
    if user_update.avatar_url is not None:
        current_user.avatar_url = user_update.avatar_url
    if user_update.password is not None:
        current_user.password_hash = get_password_hash(user_update.password)

    current_user.updated_at = datetime.now()
    db.commit()
    db.refresh(current_user)

    logger.info(f"用户信息更新成功: {current_user.username}")

    return UserAuthResponse(
        success=True,
        message="更新成功",
        data=user_to_response(current_user)
    )
