import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Path, Response
from fastapi.responses import StreamingResponse

from app.services.detection_service import detection_service
from app.services.minio_service import minio_service
from app.utils.file_utils import save_upload_file, ensure_directories
from app.config import settings
from app.models.schemas import (
    SingleDetectionResponse, HistoryResponse, TargetListResponse,
    TargetItem, HistoryItem, DetectionResult, DetectionBox
)
from app.models.database import DetectionRecord

router = APIRouter(prefix="/detection", tags=["detection"])
ensure_directories()

@router.post("/single", response_model=SingleDetectionResponse)
async def detect_single_image(
    file: UploadFile = File(...),
    model_name: str = Form("rsod-yolo11n"),
    user_id: str = Form(None)
):
    try:
        os.makedirs(settings.upload_dir, exist_ok=True)
        filename = await save_upload_file(file, settings.upload_dir)
        image_path = os.path.join(settings.upload_dir, filename)

        result = detection_service.detect_single_image(image_path, user_id, model_name, minio_service)

        try:
            os.remove(image_path)
        except:
            pass

        return SingleDetectionResponse(
            success=True,
            message="检测成功",
            data=result
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail="模型文件未找到")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")

@router.get("/history", response_model=HistoryResponse)
async def get_detection_history(
    page: int = 1,
    page_size: int = 10,
    user_id: str = None
):
    try:
        records = detection_service.get_detection_history(user_id=user_id, limit=page_size * page)

        start = (page - 1) * page_size
        end = start + page_size

        history_items = []
        for record in records[start:end]:
            original_filename = os.path.basename(record.original_image_key) if record.original_image_key else ""
            result_filename = os.path.basename(record.result_image_key) if record.result_image_key else ""

            image_url = f"http://localhost:8000/api/detection/files/rsod-original/{original_filename}" if original_filename else ""
            result_url = f"http://localhost:8000/api/detection/files/rsod-results/{result_filename}" if result_filename else ""

            history_items.append(HistoryItem(
                id=str(record.id),
                image_url=image_url,
                result_image_url=result_url,
                total_objects=record.total_objects or 0,
                created_at=record.created_at,
                model_name=record.model_name or "rsod-yolo11n",
                filename=original_filename or "detection.jpg",
                status=record.status or "completed",
                type=record.type or "single",
                time=record.created_at.strftime("%Y-%m-%d %H:%M") if record.created_at else "",
                count=1,
                detected_targets=[]
            ))

        return HistoryResponse(
            success=True,
            message="获取成功",
            data=history_items,
            total=len(records)
        )

    except Exception as e:
        raise HTTPException(status_code=500, message="获取历史记录失败", detail=str(e))

@router.get("/{detection_id}", response_model=SingleDetectionResponse)
async def get_detection_by_id(detection_id: str = Path(..., description="检测记录 ID")):
    try:
        record = detection_service.get_detection_by_id(detection_id)

        if not record:
            raise HTTPException(status_code=404, message="检测记录不存在")

        original_filename = os.path.basename(record.original_image_key) if record.original_image_key else ""
        result_filename = os.path.basename(record.result_image_key) if record.result_image_key else ""

        image_url = f"http://localhost:8000/api/detection/files/rsod-original/{original_filename}" if original_filename else ""
        result_url = f"http://localhost:8000/api/detection/files/rsod-results/{result_filename}" if result_filename else ""

        boxes = []
        if hasattr(record, 'results') and record.results:
            for result in record.results:
                boxes.append(DetectionBox(
                    x1=result.x1, y1=result.y1, x2=result.x2, y2=result.y2,
                    confidence=result.confidence,
                    class_id=result.class_id,
                    class_name=result.class_name,
                    chinese_name=result.chinese_name
                ))

        detection_result = DetectionResult(
            detection_id=str(record.id),
            image_url=image_url,
            result_image_url=result_url,
            boxes=boxes,
            total_objects=record.total_objects or 0,
            detection_time=record.detection_time or 0,
            model_name=record.model_name or "rsod-yolo11n",
            created_at=record.created_at
        )

        return SingleDetectionResponse(
            success=True,
            message="获取成功",
            data=detection_result
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, message="获取检测记录失败", detail=str(e))

@router.delete("/{detection_id}")
async def delete_detection(detection_id: str = Path(..., description="检测记录 ID")):
    try:
        success = detection_service.delete_detection(detection_id)

        if not success:
            raise HTTPException(status_code=404, message="检测记录不存在")

        return {"success": True, "message": "删除成功"}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, message="删除检测记录失败", detail=str(e))

@router.get("/targets/list", response_model=TargetListResponse)
async def get_target_list():
    targets = [
        TargetItem(id=0, name="aircraft", chinese_name="飞机", description="固定翼飞机、直升机等"),
        TargetItem(id=1, name="oiltank", chinese_name="油罐", description="储油罐、化工罐等"),
        TargetItem(id=2, name="overpass", chinese_name="立交桥", description="各类立交桥"),
        TargetItem(id=3, name="playground", chinese_name="操场", description="运动场、操场等"),
    ]

    return TargetListResponse(
        success=True,
        message="获取成功",
        data=targets
    )

@router.get("/files/{bucket}/{filename}", response_class=Response)
def get_file(bucket: str, filename: str):
    try:
        response = minio_service.client.get_object(bucket, filename)

        content_type = "image/jpeg"
        if filename.endswith(".png"):
            content_type = "image/png"
        elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
            content_type = "image/jpeg"

        data = response.read()
        response.close()
        response.release_conn()

        return Response(
            content=data,
            media_type=content_type,
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "Content-Length": str(len(data))
            }
        )

    except Exception as e:
        raise HTTPException(status_code=404, message="文件未找到", detail=f"{type(e).__name__}: {str(e)}")