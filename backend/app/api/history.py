"""
PCB缺陷检测系统 - 检测历史记录 API

提供检测历史记录的保存和查询功能。
"""

from typing import List, Optional
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.database import User, DetectionRecord, DetectionResult
from app.schemas import (
    DetectionHistoryResponse, DetectionRecordDetailResponse,
    DetectionRecordItem, DetectionBoxData, SuccessResponse
)
from app.api.auth import get_current_active_user
from app.config import settings

router = APIRouter(prefix="/api/history", tags=["历史记录"])


# ============ 工具函数 ============

def get_image_url(image_path: Optional[str]) -> Optional[str]:
    """获取图片的访问 URL"""
    if not image_path:
        return None
    try:
        path = Path(image_path)
        filename = path.name
        if str(settings.upload_dir) in image_path:
            return f"/api/static/uploads/{filename}"
        elif str(settings.result_dir) in image_path:
            return f"/api/static/results/{filename}"
        return None
    except:
        return None


def record_to_item(record: DetectionRecord, include_boxes: bool = False) -> DetectionRecordItem:
    """将检测记录转换为响应项"""
    boxes = None
    if include_boxes and record.results:
        boxes = [
            DetectionBoxData(
                x1=result.x1,
                y1=result.y1,
                x2=result.x2,
                y2=result.y2,
                confidence=result.confidence,
                class_id=result.class_id,
                class_name=result.class_name,
                chinese_name=result.chinese_name or result.class_name,
                color=None
            )
            for result in record.results
        ]
    
    return DetectionRecordItem(
        id=record.id,
        type=record.type,
        status=record.status,
        model_name=record.model_name,
        total_objects=record.total_objects,
        detection_time=record.detection_time,
        original_image_url=get_image_url(record.original_image_path),
        result_image_url=get_image_url(record.result_image_path),
        created_at=record.created_at,
        boxes=boxes
    )


# ============ API 路由 ============

@router.get("/", response_model=DetectionHistoryResponse)
async def get_detection_history(
    page: int = 1,
    page_size: int = 20,
    type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取检测历史记录列表
    
    支持分页和按类型过滤。
    """
    query = db.query(DetectionRecord).filter(DetectionRecord.user_id == current_user.id)
    
    if type:
        query = query.filter(DetectionRecord.type == type)
    
    total = query.count()
    
    records = query.order_by(desc(DetectionRecord.created_at)) \
        .offset((page - 1) * page_size) \
        .limit(page_size) \
        .all()
    
    items = [record_to_item(record) for record in records]
    
    return DetectionHistoryResponse(
        success=True,
        message="获取成功",
        data=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{record_id}", response_model=DetectionRecordDetailResponse)
async def get_detection_record_detail(
    record_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取检测记录详情
    
    包括检测框信息。
    """
    record = db.query(DetectionRecord) \
        .filter(DetectionRecord.id == record_id) \
        .filter(DetectionRecord.user_id == current_user.id) \
        .first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="检测记录不存在"
        )
    
    # 预加载检测结果
    db.refresh(record)
    
    return DetectionRecordDetailResponse(
        success=True,
        message="获取成功",
        data=record_to_item(record, include_boxes=True)
    )


@router.delete("/{record_id}", response_model=SuccessResponse)
async def delete_detection_record(
    record_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    删除检测记录
    """
    record = db.query(DetectionRecord) \
        .filter(DetectionRecord.id == record_id) \
        .filter(DetectionRecord.user_id == current_user.id) \
        .first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="检测记录不存在"
        )
    
    db.delete(record)
    db.commit()
    
    return SuccessResponse(
        success=True,
        message="删除成功"
    )


@router.delete("/", response_model=SuccessResponse)
async def delete_all_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    清空所有检测历史
    """
    db.query(DetectionRecord) \
        .filter(DetectionRecord.user_id == current_user.id) \
        .delete(synchronize_session=False)
    
    db.commit()
    
    return SuccessResponse(
        success=True,
        message="清空成功"
    )


# ============ 内部使用的保存记录函数 ============

def save_detection_record(
    db: Session,
    user_id: Optional[str],
    type: str,
    model_name: str,
    total_objects: int,
    detection_time: float,
    original_image_path: Optional[str],
    result_image_path: Optional[str],
    boxes: List[dict],
    status: str = "completed"
) -> DetectionRecord:
    """
    保存检测记录
    
    Args:
        db: 数据库会话
        user_id: 用户 ID
        type: 检测类型
        model_name: 模型名称
        total_objects: 检测目标数
        detection_time: 检测耗时
        original_image_path: 原始图片路径
        result_image_path: 结果图片路径
        boxes: 检测框列表
        status: 检测状态
    
    Returns:
        保存的检测记录
    """
    record = DetectionRecord(
        user_id=user_id,
        type=type,
        status=status,
        model_name=model_name,
        total_objects=total_objects,
        detection_time=detection_time,
        original_image_path=original_image_path,
        result_image_path=result_image_path,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    db.add(record)
    db.flush()  # 获取 ID
    
    # 保存检测框
    for box in boxes:
        result = DetectionResult(
            record_id=record.id,
            x1=box.get("x1", 0),
            y1=box.get("y1", 0),
            x2=box.get("x2", 0),
            y2=box.get("y2", 0),
            confidence=box.get("confidence", 0),
            class_id=box.get("class_id", 0),
            class_name=box.get("class_name", ""),
            chinese_name=box.get("chinese_name")
        )
        db.add(result)
    
    db.commit()
    db.refresh(record)
    
    return record
