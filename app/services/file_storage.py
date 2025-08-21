from datetime import timedelta
from minio import Minio
from minio.error import S3Error
import uuid
import os
from fastapi import UploadFile, HTTPException
from typing import Optional
import aiofiles
from app.core.config import settings
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class FileStorage:
    def __init__(self):
        try:
            self.client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            self.bucket_name = settings.MINIO_BUCKET_NAME
            self.public_url = settings.MINIO_PUBLIC_URL
            self.executor = ThreadPoolExecutor(max_workers=4)
            self._ensure_bucket_exists()
            logger.info(f"FileStorage initialized successfully for bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize FileStorage: {e}")
            raise

    async def _run_in_thread(self, func, *args, **kwargs):
    # """Запускает синхронную функцию в thread pool"""
        loop = asyncio.get_event_loop()
        if args or kwargs:
        # Если есть аргументы, создаем partial функцию
            from functools import partial
            func_with_args = partial(func, *args, **kwargs)
            return await loop.run_in_executor(self.executor, func_with_args)
        else:
            return await loop.run_in_executor(self.executor, func)

    def _ensure_bucket_exists(self):
        """Создает bucket если он не существует"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Bucket '{self.bucket_name}' created successfully")
                
                # Устанавливаем политику для публичного доступа в development
                if settings.ENVIRONMENT == "development":
                    policy = {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"AWS": "*"},
                                "Action": ["s3:GetObject"],
                                "Resource": [f"arn:aws:s3:::{self.bucket_name}/*"]
                            }
                        ]
                    }
                    self.client.set_bucket_policy(self.bucket_name, policy)
                    logger.info(f"Public read policy set for bucket: {self.bucket_name}")
                    
            else:
                logger.info(f"Bucket '{self.bucket_name}' already exists")
                
        except S3Error as e:
            logger.error(f"S3Error creating bucket '{self.bucket_name}': {e}")
            raise HTTPException(status_code=500, detail="Failed to create storage bucket")
        except Exception as e:
            logger.error(f"Unexpected error creating bucket '{self.bucket_name}': {e}")
            raise HTTPException(status_code=500, detail="Failed to initialize storage")

    async def upload_image(self, file: UploadFile, product_id: uuid.UUID) -> Optional[str]:

        try:
            await file.seek(0)
        
        # Валидация расширения файла
            file_extension = os.path.splitext(file.filename)[1].lower() if file.filename else '.jpg'
            valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        
            if file_extension not in valid_extensions:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file extension. Only .jpg, .jpeg, .png, .webp, .gif are allowed"
                )

            object_name = f"products/{product_id}{file_extension}"
        
            # Создаем временный файл (более надежный способ для больших файлов)
            temp_file = f"/tmp/{uuid.uuid4()}{file_extension}"
        
            try:
                # Сохраняем содержимое во временный файл
                async with aiofiles.open(temp_file, 'wb') as out_file:
                    content = await file.read()
                    await out_file.write(content)

                # Загружаем в MinIO используя fput_object (для файлов)
                await self._run_in_thread(
                    self.client.fput_object,
                    self.bucket_name,
                    object_name,
                    temp_file,
                    file.content_type or "image/jpeg"
                )
            
                logger.info(f"Image uploaded successfully: {object_name}")
                return object_name
            
            finally:
                # Всегда удаляем временный файл
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                
        except S3Error as e:
            logger.error(f"MinIO error uploading image for product {product_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload image to storage")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error uploading image for product {product_id}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error during image upload")

    async def delete_image(self, object_name: str) -> bool:
        """Удаляет изображение из MinIO"""
        if not object_name:
            return True
            
        try:
            await self._run_in_thread(
                self.client.remove_object,
                self.bucket_name,
                object_name
            )
            logger.info(f"Image deleted successfully: {object_name}")
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                logger.warning(f"Image already deleted: {object_name}")
                return True
            logger.warning(f"MinIO error deleting image {object_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting image {object_name}: {e}")
            return False

    def get_image_url(self, object_name: str) -> Optional[str]:
        """Возвращает URL для доступа к изображению"""
        if not object_name:
            return None
        
        try:
            if settings.ENVIRONMENT == "development":
                # Прямой URL для development
                return f"{self.public_url}/{self.bucket_name}/{object_name}"
            else:
                # Presigned URL для production
                return self.client.presigned_get_object(
                    self.bucket_name,
                    object_name,
                    expires=timedelta(hours=24)
                )
        except S3Error as e:
            logger.error(f"MinIO error generating URL for {object_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating URL for {object_name}: {e}")
            return None

    async def image_exists(self, object_name: str) -> bool:
        """Проверяет существует ли изображение в хранилище"""
        if not object_name:
            return False
            
        try:
            await self._run_in_thread(
                self.client.stat_object,
                self.bucket_name,
                object_name
            )
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            logger.warning(f"MinIO error checking image existence {object_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking image existence {object_name}: {e}")
            return False

    async def check_connection(self) -> bool:
        """Проверяет соединение с MinIO"""
        try:
            await self._run_in_thread(self.client.list_buckets)
            logger.info("MinIO connection check successful")
            return True
        except S3Error as e:
            logger.error(f"MinIO connection check failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during MinIO connection check: {e}")
            return False

# Глобальный экземпляр FileStorage
file_storage = FileStorage()