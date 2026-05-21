from fastapi import APIRouter, HTTPException

from app.services.detection_service import detection_service
from app.services.minio_service import minio_service
from app.models.schemas import (
    ModelListResponse, ModelItem, CurrentModelResponse,
    ReloadModelRequest, ReloadModelResponse, ModelMetadata
)
from app.config import settings

router = APIRouter(prefix="/model", tags=["model"])

@router.get("/list", response_model=ModelListResponse)
async def get_model_list():
    try:
        models_with_meta = minio_service.list_models_with_metadata()

        model_items = []
        for model in models_with_meta:
            metadata = None
            if model.get("metadata"):
                meta_data = model["metadata"]
                metadata = ModelMetadata(
                    name=meta_data.get("name", "unknown"),
                    version=meta_data.get("version", "unknown"),
                    created_at=meta_data.get("created_at"),
                    description=meta_data.get("description"),
                    metrics=meta_data.get("metrics"),
                    config=meta_data.get("config")
                )

            model_items.append(ModelItem(
                object_name=model["object_name"],
                metadata=metadata,
                public_url=model["public_url"]
            ))

        latest_model = None
        if model_items:
            latest_object_name = minio_service.get_latest_model()
            if latest_object_name:
                for item in model_items:
                    if item.object_name == latest_object_name:
                        latest_model = item
                        break

        return ModelListResponse(
            success=True,
            message="获取成功",
            data=model_items,
            latest=latest_model
        )

    except Exception as e:
        raise HTTPException(status_code=500, message="获取模型列表失败", detail=str(e))

@router.get("/current", response_model=CurrentModelResponse)
async def get_current_model():
    try:
        current_info = detection_service.current_model_info

        metadata = None
        if current_info.get("metadata"):
            meta_data = current_info["metadata"]
            metadata = ModelMetadata(
                name=meta_data.get("name", "unknown"),
                version=meta_data.get("version", "unknown"),
                created_at=meta_data.get("created_at"),
                description=meta_data.get("description"),
                metrics=meta_data.get("metrics"),
                config=meta_data.get("config")
            )

        object_name = current_info.get("object_name", "unknown")
        public_url = ""
        if object_name and object_name != "unknown":
            public_url = minio_service.get_public_url(settings.minio.models_bucket, object_name)

        model_item = ModelItem(
            object_name=object_name,
            metadata=metadata,
            public_url=public_url
        )

        return CurrentModelResponse(
            success=True,
            message="获取成功",
            data=model_item
        )

    except Exception as e:
        raise HTTPException(status_code=500, message="获取当前模型信息失败", detail=str(e))

@router.post("/reload", response_model=ReloadModelResponse)
async def reload_model(request: ReloadModelRequest = None):
    try:
        success = detection_service.reload_model(
            model_object_name=request.object_name if request else None
        )

        if not success:
            raise HTTPException(status_code=500, message="模型重新加载失败")

        current_info = detection_service.current_model_info

        metadata = None
        if current_info.get("metadata"):
            meta_data = current_info["metadata"]
            metadata = ModelMetadata(
                name=meta_data.get("name", "unknown"),
                version=meta_data.get("version", "unknown"),
                created_at=meta_data.get("created_at"),
                description=meta_data.get("description"),
                metrics=meta_data.get("metrics"),
                config=meta_data.get("config")
            )

        object_name = current_info.get("object_name", "unknown")
        public_url = ""
        if object_name and object_name != "unknown":
            public_url = minio_service.get_public_url(settings.minio.models_bucket, object_name)

        model_item = ModelItem(
            object_name=object_name,
            metadata=metadata,
            public_url=public_url
        )

        return ReloadModelResponse(
            success=True,
            message="模型重新加载成功",
            data=model_item
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, message="模型重新加载失败", detail=str(e))