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

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

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
    ErrorResponse
)
from app.utils.paths import Paths
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/detection", tags=["检测"])


@router.post("/single", response_model=DetectionResponse)
async def detect_single_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    model_name: Optional[str] = Form(None),
    conf_threshold: Optional[float] = Form(0.5),
    iou_threshold: Optional[float] = Form(0.45)
):
    """
    单图检测接口

    上传PCB图像，返回检测结果

    - **file**: PCB图像文件
    - **model_name**: 模型名称（可选，默认使用当前模型）
    - **conf_threshold**: 置信度阈值（默认0.5）
    - **iou_threshold**: IOU阈值（默认0.45）
    """
    try:
        Paths.ensure_dir(Paths.uploads())
        
        file_path = Paths.uploads() / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        logger.info(f"接收到图像: {file.filename}, 大小: {len(content)} bytes")

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
            image_url=f"/api/detection/files/{result.image_path}",
            result_image_url=f"/api/detection/files/{result.result_image_path}",
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

        return DetectionResponse(
            success=True,
            message="检测成功",
            data=result_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检测失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"检测失败: {str(e)}"
        )


@router.get("/targets/list", response_model=TargetListResponse)
async def get_target_list():
    """
    获取支持的检测目标类型列表

    返回系统支持的所有PCB缺陷类型
    """
    targets = [
        TargetItem(id=0, name="scratch", chinese_name="划痕", description="PCB板表面划痕", color="#f87171"),
        TargetItem(id=1, name="crack", chinese_name="裂纹", description="PCB板表面裂纹", color="#fb923c"),
        TargetItem(id=2, name="hole", chinese_name="孔洞", description="PCB板表面孔洞缺陷", color="#facc15"),
        TargetItem(id=3, name="deformation", chinese_name="变形", description="PCB板变形缺陷", color="#34d399"),
        TargetItem(id=4, name="missing", chinese_name="缺失", description="元器件缺失", color="#38bdf8"),
        TargetItem(id=5, name="solder", chinese_name="焊点异常", description="焊接点质量问题", color="#a78bfa"),
    ]

    return TargetListResponse(
        success=True,
        message="获取成功",
        data=targets
    )


@router.get("/stats", response_model=DetectionStatsResponse)
async def get_detection_stats():
    """
    获取检测统计信息

    返回系统的检测统计数据
    """
    stats = detection_service.get_stats()

    return DetectionStatsResponse(
        success=True,
        message="获取成功",
        data=stats
    )


@router.post("/stats/reset", response_model=SuccessResponse)
async def reset_detection_stats():
    """
    重置检测统计信息
    """
    detection_service.reset_stats()

    return SuccessResponse(
        success=True,
        message="统计信息已重置"
    )


@router.get("/models/list", response_model=ModelListResponse)
async def get_model_list():
    """
    获取模型列表

    返回所有可用的检测模型
    """
    models = model_manager.scan_models()

    model_items = [
        ModelItem(
            name=model.name,
            version=model.version,
            status=model.status.value,
            path=model.path,
            description=model.description,
            class_names=model.class_names,
            created_at=model.created_at,
            last_used=model.last_used
        )
        for model in models
    ]

    return ModelListResponse(
        success=True,
        message="获取成功",
        data=model_items
    )


@router.get("/models/current", response_model=CurrentModelResponse)
async def get_current_model():
    """
    获取当前使用的模型

    返回当前正在使用的检测模型信息
    """
    model = model_manager.get_current_model()

    if not model:
        raise HTTPException(
            status_code=404,
            detail="未设置当前模型"
        )

    return CurrentModelResponse(
        success=True,
        message="获取成功",
        data=ModelItem(
            name=model.name,
            version=model.version,
            status=model.status.value,
            path=model.path,
            description=model.description,
            class_names=model.class_names,
            created_at=model.created_at,
            last_used=model.last_used
        )
    )


@router.post("/models/switch", response_model=CurrentModelResponse)
async def switch_model(model_name: str = Form(...)):
    """
    切换检测模型

    - **model_name**: 要切换的模型名称
    """
    model_info = model_manager.get_model(model_name)
    if not model_info:
        raise HTTPException(
            status_code=404,
            detail=f"模型不存在: {model_name}"
        )

    success = model_manager.set_current_model(model_name)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="模型切换失败"
        )

    load_success = detection_service.load_model(model_info.path)
    if not load_success:
        raise HTTPException(
            status_code=500,
            detail=f"模型加载失败: {model_name}"
        )

    model = model_manager.get_model(model_name)

    return CurrentModelResponse(
        success=True,
        message="模型切换成功",
        data=ModelItem(
            name=model.name,
            version=model.version,
            status=model.status.value,
            path=model.path,
            description=model.description,
            class_names=model.class_names,
            created_at=model.created_at,
            last_used=model.last_used
        )
    )


@router.get("/files/{file_path:path}", response_class=FileResponse)
async def get_detection_file(file_path: str):
    """
    获取检测结果文件

    - **file_path**: 文件路径（相对于项目根目录）
    """
    file_full_path = Paths.root() / file_path

    if not file_full_path.exists():
        logger.error(f"文件不存在: {file_full_path}")
        raise HTTPException(
            status_code=404,
            detail="文件不存在"
        )

    suffix = file_full_path.suffix.lower()
    media_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp'
    }

    return FileResponse(
        path=str(file_full_path),
        media_type=media_types.get(suffix, 'application/octet-stream'),
        filename=file_full_path.name
    )


@router.get("/health")
async def health_check():
    """
    健康检查接口

    返回系统健康状态
    """
    model_loaded = detection_service.is_model_loaded()
    current_model = model_manager.get_current_model()

    return {
        "status": "healthy",
        "model_loaded": model_loaded,
        "current_model": current_model.name if current_model else None,
        "service": "detection"
    }


def get_color_for_class(class_id: int) -> str:
    """获取类别对应的颜色"""
    colors = {
        0: "#f87171",
        1: "#fb923c",
        2: "#facc15",
        3: "#34d399",
        4: "#38bdf8",
        5: "#a78bfa",
    }
    return colors.get(class_id, "#10b981")


def cleanup_file(file_path: Path):
    """清理上传的文件"""
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"已清理临时文件: {file_path}")
    except Exception as e:
        logger.error(f"清理文件失败: {str(e)}")


@router.post("/realtime")
async def detect_realtime_image(
    image_base64: str = Form(...),
    conf_threshold: Optional[float] = Form(0.5),
    iou_threshold: Optional[float] = Form(0.45)
):
    """
    实时图像检测接口

    接收base64编码的图像，返回检测结果

    - **image_base64**: base64编码的图像数据
    - **conf_threshold**: 置信度阈值（默认0.5）
    - **iou_threshold**: IOU阈值（默认0.45）
    """
    try:
        image_data = base64.b64decode(image_base64)
        image_bytes = io.BytesIO(image_data)

        temp_file_path = Paths.temp() / f"realtime_{str(uuid.uuid4())[:8]}.jpg"
        with open(temp_file_path, "wb") as f:
            f.write(image_bytes.getvalue())

        logger.debug(f"接收到实时检测图像，大小: {len(image_data)} bytes")

        result = detection_service.detect_image(
            str(temp_file_path),
            conf_threshold=conf_threshold,
            iou_threshold=iou_threshold
        )

        cleanup_file(temp_file_path)

        boxes_data = []
        for box in result.boxes:
            boxes_data.append({
                "x1": box.x1,
                "y1": box.y1,
                "x2": box.x2,
                "y2": box.y2,
                "confidence": box.confidence,
                "class_id": box.class_id,
                "class_name": box.class_name,
                "chinese_name": box.chinese_name,
                "color": get_color_for_class(box.class_id)
            })

        return {
            "success": True,
            "message": "检测成功",
            "data": {
                "total_objects": result.total_objects,
                "detection_time": result.detection_time,
                "model_name": result.model_name,
                "boxes": boxes_data
            }
        }

    except Exception as e:
        logger.error(f"实时检测失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"实时检测失败: {str(e)}"
        )


@router.post("/batch")
async def detect_batch(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    model_name: Optional[str] = Form(None),
    conf_threshold: Optional[float] = Form(0.5),
    iou_threshold: Optional[float] = Form(0.45)
):
    """
    批量图像检测接口

    上传多张PCB图像，返回批量检测结果

    - **files**: PCB图像文件列表（最多50张）
    - **model_name**: 模型名称（可选，默认使用当前模型）
    - **conf_threshold**: 置信度阈值（默认0.5）
    - **iou_threshold**: IOU阈值（默认0.45）
    """
    try:
        if len(files) > 50:
            raise HTTPException(
                status_code=400,
                detail="最多支持50张图像同时检测"
            )

        Paths.ensure_dir(Paths.uploads())

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
                    detection_service.load_model(model_info.path)

        results = []
        for idx, file in enumerate(files):
            file_path = Paths.uploads() / f"batch_{idx}_{file.filename}"
            
            try:
                content = await file.read()
                with open(file_path, "wb") as buffer:
                    buffer.write(content)

                logger.info(f"处理图像 {idx + 1}/{len(files)}: {file.filename}")

                result = detection_service.detect_image(
                    str(file_path),
                    conf_threshold=conf_threshold,
                    iou_threshold=iou_threshold
                )

                background_tasks.add_task(cleanup_file, file_path)

                result_data = {
                    "detection_id": result.detection_id,
                    "image_url": f"/api/detection/files/{result.image_path}",
                    "result_image_url": f"/api/detection/files/{result.result_image_path}",
                    "boxes": [
                        {
                            "x1": box.x1,
                            "y1": box.y1,
                            "x2": box.x2,
                            "y2": box.y2,
                            "confidence": box.confidence,
                            "class_id": box.class_id,
                            "class_name": box.class_name,
                            "chinese_name": box.chinese_name,
                            "color": get_color_for_class(box.class_id)
                        }
                        for box in result.boxes
                    ],
                    "total_objects": result.total_objects,
                    "detection_time": result.detection_time,
                    "model_name": result.model_name,
                    "created_at": result.created_at
                }

                results.append({
                    "filename": file.filename,
                    "success": True,
                    "result": result_data,
                    "error": None
                })

            except Exception as e:
                logger.error(f"处理图像失败 {file.filename}: {str(e)}")
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "result": None,
                    "error": str(e)
                })

        success_count = sum(1 for r in results if r["success"])
        failed_count = len(results) - success_count

        return {
            "success": True,
            "message": f"批量检测完成：成功 {success_count} 张，失败 {failed_count} 张",
            "data": {
                "total": len(results),
                "success": success_count,
                "failed": failed_count,
                "items": results
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量检测失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"批量检测失败: {str(e)}"
        )
