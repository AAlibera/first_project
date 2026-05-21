import os
import time
import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from app.config import settings
from app.models.schemas import DetectionBox, DetectionResult
from app.models.database import DetectionRecord, DetectionResult as DBDetectionResult
from app.services.minio_service import minio_service

logger = logging.getLogger(__name__)

try:
    from ultralytics import YOLO
    from PIL import Image
    import cv2
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("YOLO not available, detection will be simulated")

class DetectionService:
    def __init__(self):
        self.model = None
        self.current_model_info = {
            "version": None,
            "object_name": None,
            "loaded_at": None,
            "metadata": None
        }
        self.local_model_info_path = Path(settings.yolo_model_path).parent / "model_info.json"
        self.class_names = {}
        if YOLO_AVAILABLE:
            self._load_model_smart()
        self._init_class_names()

    def _save_local_model_info(self, model_info: dict):
        try:
            info_path = Path(self.local_model_info_path)
            info_path.parent.mkdir(parents=True, exist_ok=True)
            with open(info_path, "w", encoding="utf-8") as f:
                json.dump(model_info, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"保存本地模型信息失败: {str(e)}")

    def _load_local_model_info(self) -> Optional[dict]:
        try:
            info_path = Path(self.local_model_info_path)
            if not info_path.exists():
                return None
            with open(info_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"加载本地模型信息失败: {str(e)}")
            return None

    def _load_model_smart(self):
        local_info = self._load_local_model_info()
        latest_model = minio_service.get_latest_model()
        need_download = False
        model_object_name = None

        if not os.path.exists(settings.yolo_model_path):
            logger.info("本地模型不存在")
            need_download = True
        elif not local_info:
            logger.info("本地模型存在但没有版本信息")
            need_download = True
        else:
            if latest_model and local_info.get("object_name") != latest_model:
                logger.info(f"发现新版本模型: {latest_model}")
                need_download = True
            else:
                logger.info("本地模型已是最新版本")

        if need_download and latest_model:
            logger.info(f"从 MinIO 下载最新模型")
            success = minio_service.download_model_file(latest_model, settings.yolo_model_path)
            if not success:
                if os.path.exists(settings.yolo_model_path):
                    logger.warning("模型下载失败，使用本地已有模型")
                    model_object_name = local_info.get("object_name") if local_info else None
                else:
                    raise FileNotFoundError(f"模型下载失败且本地不存在")
            else:
                model_object_name = latest_model
        elif not latest_model:
            if not os.path.exists(settings.yolo_model_path):
                raise FileNotFoundError(f"模型文件未找到")
            model_object_name = local_info.get("object_name") if local_info else None

        if YOLO_AVAILABLE and os.path.exists(settings.yolo_model_path):
            self.model = YOLO(settings.yolo_model_path)
            model_metadata = minio_service.get_model_metadata(model_object_name) if model_object_name else None
            self.current_model_info = {
                "version": model_metadata.get("version", "unknown") if model_metadata else "unknown",
                "object_name": model_object_name,
                "loaded_at": datetime.now().isoformat(),
                "metadata": model_metadata
            }
            self._save_local_model_info(self.current_model_info)
            logger.info(f"模型加载成功: {settings.yolo_model_path}")

    def reload_model(self, model_object_name: Optional[str] = None) -> bool:
        try:
            if model_object_name:
                logger.info(f"加载指定模型: {model_object_name}")
                success = minio_service.download_model_file(model_object_name, settings.yolo_model_path)
                if not success:
                    return False
            else:
                logger.info("重新加载最新模型")
            
            self.model = None
            self._load_model_smart()
            return True
        except Exception as e:
            logger.error(f"重新加载模型失败: {str(e)}")
            return False

    def _init_class_names(self):
        self.class_names = {
            0: "aircraft",
            1: "oiltank",
            2: "overpass",
            3: "playground",
        }

    def get_class_chinese_name(self, class_name: str) -> str:
        chinese_names = {
            "aircraft": "飞机",
            "oiltank": "油罐",
            "overpass": "立交桥",
            "playground": "操场"
        }
        return chinese_names.get(class_name, class_name)

    def detect_single_image(self, image_path: str, user_id: Optional[str] = None, model_name: str = "rsod-yolo11n", minio_svc = None) -> DetectionResult:
        start_time = time.time()
        detection_id = str(uuid.uuid4())
        boxes = []
        db_results = []

        if YOLO_AVAILABLE and self.model:
            results = self.model.predict(
                source=image_path,
                conf=settings.confidence_threshold,
                iou=settings.iou_threshold,
                save=False
            )

            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = self.class_names.get(class_id, f"class_{class_id}")
                    chinese_name = self.get_class_chinese_name(class_name)

                    boxes.append(DetectionBox(
                        x1=x1, y1=y1, x2=x2, y2=y2,
                        confidence=confidence,
                        class_id=class_id,
                        class_name=class_name,
                        chinese_name=chinese_name
                    ))

                    db_results.append(DBDetectionResult(
                        x1=x1, y1=y1, x2=x2, y2=y2,
                        confidence=confidence,
                        class_id=class_id,
                        class_name=class_name,
                        chinese_name=chinese_name
                    ))

            annotated_image = results[0].plot()
            annotated_image_bgr = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)
            _, image_bytes = cv2.imencode('.jpg', annotated_image_bgr)
            image_bytes = image_bytes.tobytes()
        else:
            boxes = [
                DetectionBox(x1=100, y1=50, x2=200, y2=150, confidence=0.95, class_id=0, class_name="aircraft", chinese_name="飞机"),
                DetectionBox(x1=300, y1=200, x2=400, y2=300, confidence=0.88, class_id=0, class_name="aircraft", chinese_name="飞机")
            ]
            db_results = [
                DBDetectionResult(x1=100, y1=50, x2=200, y2=150, confidence=0.95, class_id=0, class_name="aircraft", chinese_name="飞机"),
                DBDetectionResult(x1=300, y1=200, x2=400, y2=300, confidence=0.88, class_id=0, class_name="aircraft", chinese_name="飞机")
            ]
            import numpy as np
            image_bytes = np.zeros((400, 400, 3), dtype=np.uint8).tobytes()

        minio = minio_svc if minio_svc is not None else minio_service
        result_object_name = minio.upload_result_image(image_bytes, "jpg")
        detection_time = time.time() - start_time
        image_filename = os.path.basename(image_path)

        try:
            with open(image_path, 'rb') as f:
                original_image_bytes = f.read()
            original_object_name = minio.upload_image_bytes(original_image_bytes, image_filename)
        except:
            original_object_name = f"original_{uuid.uuid4().hex}.jpg"

        original_image_key = f"uploads/{original_object_name}"
        result_image_key = f"results/{result_object_name}"

        self._save_to_database(
            user_id=user_id,
            detection_id=detection_id,
            model_name=model_name,
            total_objects=len(boxes),
            detection_time=detection_time,
            original_image_key=original_image_key,
            result_image_key=result_image_key,
            results=db_results
        )

        original_image_url = f"http://localhost:8000/api/detection/files/rsod-original/{original_object_name}"
        result_image_url = f"http://localhost:8000/api/detection/files/rsod-results/{result_object_name}"

        return DetectionResult(
            detection_id=detection_id,
            image_url=original_image_url,
            result_image_url=result_image_url,
            boxes=boxes,
            total_objects=len(boxes),
            detection_time=round(detection_time, 3),
            model_name=model_name,
            created_at=datetime.now()
        )

    def _save_to_database(self, user_id, detection_id, model_name, total_objects, detection_time, original_image_key, result_image_key, results):
        try:
            from app.models.database import get_db
            db = next(get_db())

            record = DetectionRecord(
                id=detection_id,
                user_id=user_id,
                type="single",
                status="completed",
                model_name=model_name,
                model_version="1.0.0",
                total_objects=total_objects,
                detection_time=detection_time,
                original_image_key=original_image_key,
                result_image_key=result_image_key
            )
            db.add(record)

            for result in results:
                result.record_id = detection_id
                db.add(result)

            db.commit()
            db.refresh(record)
            logger.info(f"检测记录已保存到数据库: {detection_id}")
            return record
        except Exception as e:
            logger.error(f"保存检测记录到数据库失败: {str(e)}")
            try:
                db.rollback()
            except:
                pass
            return None

    def get_detection_history(self, user_id: str = None, limit: int = 10) -> List[DetectionRecord]:
        try:
            from app.models.database import get_db
            db = next(get_db())

            query = db.query(DetectionRecord).order_by(DetectionRecord.created_at.desc())
            if user_id:
                query = query.filter(DetectionRecord.user_id == user_id)

            records = query.limit(limit).all()
            logger.info(f"获取检测历史记录: {len(records)} 条")
            return records
        except Exception as e:
            logger.error(f"获取检测历史记录失败: {str(e)}")
            return []

    def get_detection_by_id(self, detection_id: str) -> Optional[DetectionRecord]:
        try:
            from app.models.database import get_db
            db = next(get_db())

            record = db.query(DetectionRecord).filter(DetectionRecord.id == detection_id).first()
            return record
        except Exception as e:
            logger.error(f"获取检测记录失败: {str(e)}")
            return None

    def delete_detection(self, detection_id: str) -> bool:
        try:
            from app.models.database import get_db
            db = next(get_db())

            record = db.query(DetectionRecord).filter(DetectionRecord.id == detection_id).first()
            if record:
                db.query(DBDetectionResult).filter(DBDetectionResult.record_id == detection_id).delete()
                db.delete(record)
                db.commit()
                logger.info(f"检测记录已删除: {detection_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"删除检测记录失败: {str(e)}")
            try:
                db.rollback()
            except:
                pass
            return False

detection_service = DetectionService()