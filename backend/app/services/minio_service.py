import os
import json
import uuid
from datetime import datetime
from minio import Minio
from minio.error import S3Error

from app.config import settings

class MinIOService:
    def __init__(self):
        self.client = Minio(
            f"{settings.minio.host}:{settings.minio.port}",
            access_key=settings.minio.access_key,
            secret_key=settings.minio.secret_key,
            secure=settings.minio.secure
        )
        self._ensure_buckets()

    def _ensure_buckets(self):
        buckets = [
            settings.minio.original_bucket,
            settings.minio.results_bucket,
            settings.minio.models_bucket
        ]
        for bucket in buckets:
            if not self.client.bucket_exists(bucket):
                try:
                    self.client.make_bucket(bucket)
                except Exception as e:
                    pass

    def upload_image_bytes(self, image_bytes, filename):
        object_name = f"{uuid.uuid4().hex}_{filename}"
        try:
            from io import BytesIO
            data = BytesIO(image_bytes)
            self.client.put_object(
                settings.minio.original_bucket,
                object_name,
                data,
                len(image_bytes),
                content_type="image/jpeg"
            )
            return object_name
        except Exception as e:
            return f"original_{uuid.uuid4().hex}.jpg"

    def upload_result_image(self, image_bytes, ext):
        object_name = f"result_{uuid.uuid4().hex}.{ext}"
        try:
            from io import BytesIO
            data = BytesIO(image_bytes)
            self.client.put_object(
                settings.minio.results_bucket,
                object_name,
                data,
                len(image_bytes),
                content_type=f"image/{ext}"
            )
            return object_name
        except Exception as e:
            return f"result_{uuid.uuid4().hex}.{ext}"

    def get_public_url(self, bucket, object_name):
        try:
            return self.client.get_presigned_url(
                "GET",
                bucket,
                object_name,
                expires=3600
            )
        except Exception as e:
            return f"http://localhost:8000/api/detection/files/{bucket}/{object_name}"

    def download_model_file(self, object_name, destination_path):
        try:
            response = self.client.get_object(
                settings.minio.models_bucket,
                object_name
            )
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            with open(destination_path, "wb") as f:
                f.write(response.read())
            response.close()
            return True
        except Exception as e:
            return False

    def get_latest_model(self):
        try:
            objects = self.client.list_objects(settings.minio.models_bucket)
            model_files = [obj.object_name for obj in objects if obj.object_name.endswith(".pt")]
            if not model_files:
                return None
            return sorted(model_files)[-1]
        except Exception as e:
            return None

    def get_model_metadata(self, object_name):
        try:
            stat = self.client.stat_object(settings.minio.models_bucket, object_name)
            metadata = stat.metadata
            return {
                "name": metadata.get("x-amz-meta-name", object_name),
                "version": metadata.get("x-amz-meta-version", "1.0.0"),
                "created_at": stat.last_modified.isoformat() if stat.last_modified else datetime.now().isoformat(),
                "description": metadata.get("x-amz-meta-description", ""),
                "metrics": json.loads(metadata.get("x-amz-meta-metrics", "{}")),
                "config": json.loads(metadata.get("x-amz-meta-config", "{}"))
            }
        except Exception as e:
            return None

    def list_models_with_metadata(self):
        result = []
        try:
            objects = self.client.list_objects(settings.minio.models_bucket)
            for obj in objects:
                if obj.object_name.endswith(".pt"):
                    metadata = self.get_model_metadata(obj.object_name)
                    result.append({
                        "object_name": obj.object_name,
                        "metadata": metadata,
                        "public_url": self.get_public_url(settings.minio.models_bucket, obj.object_name)
                    })
            return sorted(result, key=lambda x: x.get("metadata", {}).get("created_at", ""), reverse=True)
        except Exception as e:
            return result

minio_service = MinIOService()