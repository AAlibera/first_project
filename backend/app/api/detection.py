"""
PCB缺陷检测系统 - 检测API路由

提供图像检测相关的API接口。
采用统一日志模块和路径管理模块。
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
import base64
import io
import uuid
import os
import asyncio

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.services.detection_service import detection_service
from app.services.model_manager import model_manager
from app.schemas import (
    DetectionResponse,
    DetectionResultData,
    DetectionBoxData,
    TargetListResponse,
    TargetItem,
    ModelListResponse,
    ModelItem,
    CurrentModelResponse,
    DetectionStatsResponse,
    SuccessResponse,
    ErrorResponse,
    BatchDetectionResponse,
    BatchDetectionData,
    BatchDetectionItem,
    VideoDetectionResponse,
    VideoDetectionData
)
from app.utils.paths import Paths
from app.utils.logging import get_logger
from app.database import get_db
from app.api.auth import get_current_user
from app.api.history import save_detection_record
from app.models.database import User
from app.config import settings

from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# 创建一个可选的认证依赖
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_optional_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    可选地获取当前用户（用于不需要强制登录的接口）
    """
    if not token:
        return None
    try:
        from jose import jwt
        from app.config import settings
        payload = jwt.decode(
            token,
            settings.jwt.secret_key,
            algorithms=[settings.jwt.algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            return None
        from app.api.auth import get_user
        user = get_user(db, username=username)
        return user
    except Exception:
        return None


# 为不同的缺陷类别分配颜色
def get_color_for_class(class_id: int) -> str:
    colors = [
        "#ef4444",  # 划痕 - 红色
        "#f59e0b",  # 裂纹 - 橙色
        "#8b5cf6",  # 孔洞 - 紫色
        "#ec4899",  # 变形 - 粉色
        "#3b82f6",  # 缺失 - 蓝色
        "#10b981",  # 焊点 - 绿色
        "#fbbf24",  # 其他1 - 黄色
        "#6366f1",  # 其他2 - 靛蓝
        "#14b8a6",  # 其他3 - 青色
        "#f97316",  # 其他4 - 亮橙
    ]
    return colors[class_id % len(colors)]


def cleanup_file(file_path: Path):
    """后台清理临时文件"""
    try:
        if file_path.exists():
            file_path.unlink()
    except Exception:
        pass


logger = get_logger(__name__)

router = APIRouter(prefix="/api/detection", tags=["检测"])


@router.post("/single", response_model=DetectionResponse)
async def detect_single_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    model_name: Optional[str] = Form(None),
    conf_threshold: Optional[float] = Form(0.5),
    iou_threshold: Optional[float] = Form(0.45),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """单图检测接口"""
    try:
        Paths.ensure_dir(Paths.uploads())
        
        file_path = Paths.uploads() / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        if model_name:
            model_info = model_manager.get_model(model_name)
            if not model_info:
                raise HTTPException(
                    status_code=404,
                    detail=f"模型不存在: {model_name}"
                )
            current_model = model_manager.get_current_model()
            if not current_model or current_model.name != model_name:
                success = model_manager.set_current_model(model_name)
                if success:
                    model_info = model_manager.get_model(model_name)
                    if model_info:
                        detection_service.load_model(model_info.path)

        result = detection_service.detect_image(
            str(file_path),
            conf_threshold=conf_threshold,
            iou_threshold=iou_threshold
        )

        background_tasks.add_task(cleanup_file, file_path)

        result_data = DetectionResultData(
            detection_id=result.detection_id,
            image_url=f"/api/detection/files/{Path(result.image_path).name}",
            result_image_url=f"/api/detection/files/{Path(result.result_image_path).name}",
            boxes=[
                DetectionBoxData(
                    x1=box.x1,
                    y1=box.y1,
                    x2=box.x2,
                    y2=box.y2,
                    confidence=box.confidence,
                    class_id=box.class_id,
                    class_name=box.class_name,
                    chinese_name=box.chinese_name,
                    color=get_color_for_class(box.class_id)
                )
                for box in result.boxes
            ],
            total_objects=result.total_objects,
            detection_time=result.detection_time,
            model_name=result.model_name,
            created_at=result.created_at
        )

        if current_user:
            save_detection_record(
                db=db,
                user_id=current_user.id,
                type="single",
                model_name=result.model_name,
                total_objects=result.total_objects,
                detection_time=result.detection_time,
                original_image_path=result.image_path,
                result_image_path=result.result_image_path,
                boxes=[
                    {
                        "x1": b.x1,
                        "y1": b.y1,
                        "x2": b.x2,
                        "y2": b.y2,
                        "confidence": b.confidence,
                        "class_id": b.class_id,
                        "class_name": b.class_name,
                        "chinese_name": b.chinese_name
                    }
                    for b in result.boxes
                ]
            )

        return DetectionResponse(
            success=True,
            message="检测成功",
            data=result_data
        )

    except Exception as e:
        logger.error(f"单图检测失败: {e}")
        return DetectionResponse(
            success=False,
            message=f"检测失败: {str(e)}"
        )


@router.get("/models/list", response_model=ModelListResponse)
async def get_model_list():
    """获取可用模型列表"""
    try:
        models = model_manager.list_models()
        model_items = []
        for model in models:
            model_items.append(ModelItem(
                name=model.name,
                version=model.version,
                status=model.status,
                path=str(model.path) if model.path else None,
                description=model.description,
                class_names=model.class_names,
                created_at=model.created_at,
                last_used=model.last_used
            ))
        
        current_model = model_manager.get_current_model()
        for item in model_items:
            if item.name == current_model.name:
                item.status = "loaded"
        
        return ModelListResponse(
            success=True,
            message="获取成功",
            data=model_items
        )
    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        return ModelListResponse(
            success=False,
            message=f"获取失败: {str(e)}",
            data=[]
        )


@router.get("/models/current", response_model=CurrentModelResponse)
async def get_current_model():
    """获取当前使用的模型"""
    try:
        current_model = model_manager.get_current_model()
        if current_model:
            return CurrentModelResponse(
                success=True,
                message="获取成功",
                data=ModelItem(
                    name=current_model.name,
                    version=current_model.version,
                    status=current_model.status,
                    path=str(current_model.path) if current_model.path else None,
                    description=current_model.description,
                    class_names=current_model.class_names,
                    created_at=current_model.created_at,
                    last_used=current_model.last_used
                )
            )
        else:
            return CurrentModelResponse(
                success=True,
                message="未选择模型",
                data=None
            )
    except Exception as e:
        logger.error(f"获取当前模型失败: {e}")
        return CurrentModelResponse(
            success=False,
            message=f"获取失败: {str(e)}",
            data=None
        )


@router.post("/models/switch", response_model=CurrentModelResponse)
async def switch_model(model_name: str = Form(...)):
    """切换当前使用的模型"""
    try:
        model_info = model_manager.get_model(model_name)
        if not model_info:
            return CurrentModelResponse(
                success=False,
                message=f"模型不存在: {model_name}",
                data=None
            )
        
        success = model_manager.set_current_model(model_name)
        if success:
            detection_service.load_model(model_info.path)
            return CurrentModelResponse(
                success=True,
                message=f"模型切换成功: {model_name}",
                data=ModelItem(
                    name=model_info.name,
                    version=model_info.version,
                    status="loaded",
                    path=str(model_info.path),
                    description=model_info.description,
                    class_names=model_info.class_names,
                    created_at=model_info.created_at,
                    last_used=model_info.last_used
                )
            )
        else:
            return CurrentModelResponse(
                success=False,
                message="模型切换失败",
                data=None
            )
    except Exception as e:
        logger.error(f"切换模型失败: {e}")
        return CurrentModelResponse(
            success=False,
            message=f"切换失败: {str(e)}",
            data=None
        )


@router.get("/targets/list", response_model=TargetListResponse)
async def get_target_list():
    """获取可检测目标列表"""
    targets = [
        TargetItem(id=0, name="scratch", chinese_name="划痕", description="PCB表面划痕"),
        TargetItem(id=1, name="crack", chinese_name="裂纹", description="PCB裂纹缺陷"),
        TargetItem(id=2, name="hole", chinese_name="孔洞", description="PCB孔洞缺陷"),
        TargetItem(id=3, name="deformation", chinese_name="变形", description="PCB变形"),
        TargetItem(id=4, name="missing", chinese_name="缺失", description="元件缺失"),
        TargetItem(id=5, name="solder", chinese_name="焊点异常", description="焊点缺陷"),
    ]
    
    return TargetListResponse(
        success=True,
        message="获取成功",
        data=targets
    )


@router.get("/files/{filename}", response_class=FileResponse)
async def get_detection_file(filename: str):
    """获取检测相关文件"""
    try:
        file_path = Paths.static() / "results" / filename
        if file_path.exists():
            return FileResponse(file_path)
        
        file_path = Paths.static() / "uploads" / filename
        if file_path.exists():
            return FileResponse(file_path)
        
        raise HTTPException(status_code=404, detail="文件不存在")
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/stats", response_model=DetectionStatsResponse)
async def get_detection_stats():
    """获取检测统计数据"""
    try:
        stats = detection_service.get_stats()
        return DetectionStatsResponse(
            success=True,
            message="获取成功",
            data=stats
        )
    except Exception as e:
        logger.error(f"获取统计数据失败: {e}")
        return DetectionStatsResponse(
            success=False,
            message=f"获取失败: {str(e)}",
            data=detection_service.get_default_stats()
        )


@router.post("/stats/reset", response_model=SuccessResponse)
async def reset_detection_stats():
    """重置检测统计数据"""
    try:
        detection_service.reset_stats()
        return SuccessResponse(success=True, message="重置成功")
    except Exception as e:
        logger.error(f"重置统计数据失败: {e}")
        return SuccessResponse(success=False, message=f"重置失败: {str(e)}")


@router.post("/batch", response_model=BatchDetectionResponse)
async def detect_batch(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    model_name: Optional[str] = Form(None),
    conf_threshold: Optional[float] = Form(0.5),
    iou_threshold: Optional[float] = Form(0.45),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """批量检测接口"""
    try:
        Paths.ensure_dir(Paths.uploads())
        
        items: List[BatchDetectionItem] = []
        success_count = 0
        failed_count = 0
        
        # 保存所有上传的文件
        file_paths = []
        for file in files:
            file_path = Paths.uploads() / file.filename
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            file_paths.append((file.filename, file_path))
        
        # 切换模型（如果指定）
        if model_name:
            model_info = model_manager.get_model(model_name)
            if not model_info:
                return BatchDetectionResponse(
                    success=False,
                    message=f"模型不存在: {model_name}",
                    data=BatchDetectionData(
                        total=len(files),
                        success=0,
                        failed=len(files),
                        items=[
                            BatchDetectionItem(
                                filename=f.filename,
                                success=False,
                                error=f"模型不存在: {model_name}"
                            ) for f in files
                        ]
                    )
                )
            current_model = model_manager.get_current_model()
            if not current_model or current_model.name != model_name:
                success_switch = model_manager.set_current_model(model_name)
                if success_switch:
                    detection_service.load_model(model_info.path)
        
        # 逐个检测
        for filename, file_path in file_paths:
            try:
                result = detection_service.detect_image(
                    str(file_path),
                    conf_threshold=conf_threshold,
                    iou_threshold=iou_threshold
                )
                
                result_data = DetectionResultData(
                    detection_id=result.detection_id,
                    image_url=f"/api/detection/files/{Path(result.image_path).name}",
                    result_image_url=f"/api/detection/files/{Path(result.result_image_path).name}",
                    boxes=[
                        DetectionBoxData(
                            x1=box.x1,
                            y1=box.y1,
                            x2=box.x2,
                            y2=box.y2,
                            confidence=box.confidence,
                            class_id=box.class_id,
                            class_name=box.class_name,
                            chinese_name=box.chinese_name,
                            color=get_color_for_class(box.class_id)
                        )
                        for box in result.boxes
                    ],
                    total_objects=result.total_objects,
                    detection_time=result.detection_time,
                    model_name=result.model_name,
                    created_at=result.created_at
                )
                
                items.append(BatchDetectionItem(
                    filename=filename,
                    success=True,
                    result=result_data
                ))
                success_count += 1
                
                # 保存历史记录
                if current_user:
                    save_detection_record(
                        db=db,
                        user_id=current_user.id,
                        type="batch",
                        model_name=result.model_name,
                        total_objects=result.total_objects,
                        detection_time=result.detection_time,
                        original_image_path=result.image_path,
                        result_image_path=result.result_image_path,
                        boxes=[{
                            "x1": b.x1, "y1": b.y1, "x2": b.x2, "y2": b.y2,
                            "confidence": b.confidence, "class_id": b.class_id,
                            "class_name": b.class_name, "chinese_name": b.chinese_name
                        } for b in result.boxes]
                    )
                    
            except Exception as e:
                logger.error(f"检测文件 {filename} 失败: {e}")
                items.append(BatchDetectionItem(
                    filename=filename,
                    success=False,
                    error=str(e)
                ))
                failed_count += 1
            
            # 清理临时文件
            background_tasks.add_task(cleanup_file, file_path)
        
        return BatchDetectionResponse(
            success=True,
            message=f"批量检测完成: 成功 {success_count}, 失败 {failed_count}",
            data=BatchDetectionData(
                total=len(items),
                success=success_count,
                failed=failed_count,
                items=items
            )
        )
    
    except Exception as e:
        logger.error(f"批量检测失败: {e}")
        return BatchDetectionResponse(
            success=False,
            message=f"批量检测失败: {str(e)}"
        )


@router.post("/realtime", response_model=DetectionResponse)
async def detect_realtime(
    background_tasks: BackgroundTasks,
    image_base64: str = Form(...),
    model_name: Optional[str] = Form(None),
    conf_threshold: Optional[float] = Form(0.5),
    iou_threshold: Optional[float] = Form(0.45),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """实时检测接口（摄像头用）"""
    try:
        Paths.ensure_dir(Paths.uploads())
        
        # 解码base64图片
        import base64
        import io
        from PIL import Image
        
        # 移除data:image/jpeg;base64,前缀
        if image_base64.startswith('data:image'):
            image_base64 = image_base64.split(',')[1]
        
        image_data = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_data))
        
        # 保存临时文件
        import uuid
        temp_filename = f"realtime_{uuid.uuid4().hex}.jpg"
        temp_path = Paths.uploads() / temp_filename
        image.save(temp_path)
        
        # 切换模型（如果指定）
        if model_name:
            model_info = model_manager.get_model(model_name)
            if not model_info:
                raise HTTPException(
                    status_code=404,
                    detail=f"模型不存在: {model_name}"
                )
            current_model = model_manager.get_current_model()
            if not current_model or current_model.name != model_name:
                success_switch = model_manager.set_current_model(model_name)
                if success_switch:
                    detection_service.load_model(model_info.path)
        
        # 检测图片
        result = detection_service.detect_image(
            str(temp_path),
            conf_threshold=conf_threshold,
            iou_threshold=iou_threshold
        )
        
        # 清理临时文件
        background_tasks.add_task(cleanup_file, temp_path)
        
        result_data = DetectionResultData(
            detection_id=result.detection_id,
            image_url=f"/api/detection/files/{Path(result.image_path).name}",
            result_image_url=f"/api/detection/files/{Path(result.result_image_path).name}",
            boxes=[
                DetectionBoxData(
                    x1=box.x1,
                    y1=box.y1,
                    x2=box.x2,
                    y2=box.y2,
                    confidence=box.confidence,
                    class_id=box.class_id,
                    class_name=box.class_name,
                    chinese_name=box.chinese_name,
                    color=get_color_for_class(box.class_id)
                )
                for box in result.boxes
            ],
            total_objects=result.total_objects,
            detection_time=result.detection_time,
            model_name=result.model_name,
            created_at=result.created_at
        )
        
        # 保存历史记录
        if current_user:
            save_detection_record(
                db=db,
                user_id=current_user.id,
                type="realtime",
                model_name=result.model_name,
                total_objects=result.total_objects,
                detection_time=result.detection_time,
                original_image_path=result.image_path,
                result_image_path=result.result_image_path,
                boxes=[{
                    "x1": b.x1, "y1": b.y1, "x2": b.x2, "y2": b.y2,
                    "confidence": b.confidence, "class_id": b.class_id,
                    "class_name": b.class_name, "chinese_name": b.chinese_name
                } for b in result.boxes]
            )
        
        return DetectionResponse(
            success=True,
            message="检测成功",
            data=result_data
        )
    
    except Exception as e:
        logger.error(f"实时检测失败: {e}")
        return DetectionResponse(
            success=False,
            message=f"检测失败: {str(e)}"
        )


@router.post("/video", response_model=VideoDetectionResponse)
async def detect_video(
    file: UploadFile = File(...),
    model_name: Optional[str] = Form(None),
    conf_threshold: Optional[float] = Form(0.5),
    iou_threshold: Optional[float] = Form(0.45),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """视频检测接口"""
    from datetime import datetime
    import uuid
    
    try:
        Paths.ensure_dir(Paths.uploads())
        Paths.ensure_dir(Paths.static() / "uploads")
        
        # 保存视频文件
        video_id = str(uuid.uuid4())
        video_filename = f"{video_id}_{file.filename}"
        video_path = Paths.uploads() / video_filename
        
        with open(video_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 复制到static目录供前端访问
        import shutil
        static_video_path = Paths.static() / "uploads" / video_filename
        shutil.copy(str(video_path), str(static_video_path))
        
        # 切换模型（如果指定）
        if model_name:
            model_info = model_manager.get_model(model_name)
            if not model_info:
                return VideoDetectionResponse(
                    success=False,
                    message=f"模型不存在: {model_name}"
                )
            current_model = model_manager.get_current_model()
            if not current_model or current_model.name != model_name:
                success_switch = model_manager.set_current_model(model_name)
                if success_switch:
                    detection_service.load_model(model_info.path)
        
        # 返回视频检测任务（模拟处理）
        # 真实环境这里应该启动异步任务
        video_data = VideoDetectionData(
            detection_id=video_id,
            video_url=f"/api/detection/files/{video_filename}",
            total_frames=100,  # 模拟
            processed_frames=0,
            status="processing",
            created_at=datetime.now().isoformat()
        )
        
        return VideoDetectionResponse(
            success=True,
            message="视频检测已启动",
            data=video_data
        )
    
    except Exception as e:
        logger.error(f"视频检测失败: {e}")
        return VideoDetectionResponse(
            success=False,
            message=f"视频检测失败: {str(e)}"
        )
