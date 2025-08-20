from datetime import timedelta
from minio import Minio
from minio.error import S3Error
import uuid
import os
from fastapi import UploadFile, HTTPException
from typing import Optional
import aiofiles
from app.core.config import settings

class FileStorage:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE  # Используем настройку из конфига
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Создает bucket если он не существует"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"Bucket '{self.bucket_name}' created successfully")
            else:
                print(f"Bucket '{self.bucket_name}' already exists")
        except Exception as e:
            print(f"Error creating bucket '{self.bucket_name}': {e}")
            raise

    async def upload_image(self, file: UploadFile, product_id: uuid.UUID) -> Optional[str]:
        try:
            file_extension = os.path.splitext(file.filename)[1].lower()
            valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            
            if file_extension not in valid_extensions:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file extension. Only .jpg, .jpeg, .png, .webp are allowed"
                )

            object_name = f"products/{product_id}{file_extension}"
            
            # Сохраняем временный файл
            temp_file = f"/tmp/{uuid.uuid4()}{file_extension}"
            async with aiofiles.open(temp_file, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)

            # Загружаем в MinIO
            self.client.fput_object(
                self.bucket_name,
                object_name,
                temp_file,
                content_type=file.content_type
            )
            
            # Удаляем временный файл
            os.remove(temp_file)
            
            return object_name
        except S3Error as e:
            print(f"Error uploading image: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload image")
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    def get_image_url(self, object_name: str) -> Optional[str]:
        if not object_name:
            return None
        
        # В development используем публичный URL
        if settings.ENVIRONMENT == "development":
            return f"{settings.MINIO_PUBLIC_URL}/{self.bucket_name}/{object_name}"
        
        # В production используем presigned URL
        try:
            return self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=timedelta(hours=1))
        except S3Error:
            return None

file_storage = FileStorage()