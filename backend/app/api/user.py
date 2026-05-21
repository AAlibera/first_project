from fastapi import APIRouter, HTTPException
from passlib.context import CryptContext

from app.models.schemas import UserRegisterRequest, UserLoginRequest, UserResponse
from app.models.database import User, get_db

router = APIRouter(prefix="/user", tags=["user"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

@router.post("/register", response_model=UserResponse)
async def register_user(request: UserRegisterRequest):
    try:
        db = next(get_db())
        
        if db.query(User).filter(User.username == request.username).first():
            raise HTTPException(status_code=400, detail="用户名已存在")
        
        if db.query(User).filter(User.email == request.email).first():
            raise HTTPException(status_code=400, detail="邮箱已被注册")
        
        hashed_password = get_password_hash(request.password)
        
        user = User(
            username=request.username,
            email=request.email,
            password_hash=hashed_password,
            nickname=request.nickname or request.username
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return UserResponse(
            success=True,
            message="注册成功",
            data={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "nickname": user.nickname,
                "role": user.role
            }
        )
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")

@router.post("/login", response_model=UserResponse)
async def login_user(request: UserLoginRequest):
    try:
        db = next(get_db())
        
        user = db.query(User).filter(User.username == request.username).first()
        
        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        if not user.is_active:
            raise HTTPException(status_code=400, detail="用户已被禁用")
        
        return UserResponse(
            success=True,
            message="登录成功",
            data={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "nickname": user.nickname,
                "role": user.role,
                "avatar_url": user.avatar_url
            }
        )
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")