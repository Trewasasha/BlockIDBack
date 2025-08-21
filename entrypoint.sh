#!/bin/sh
set -e

echo "Ожидание запуска MinIO..."
until curl -s http://minio:9000/minio/health/live > /dev/null; do 
  echo "MinIO еще не запущен, ждем..."
  sleep 2
done

echo "MinIO запущен, настраиваем..."
mc alias set myminio http://minio:9000 minioadmin minioadmin

echo "Создаем bucket если не существует..."
mc mb myminio/kitchen-blocks || true

echo "Устанавливаем публичные права доступа..."
mc policy set public myminio/kitchen-blocks

echo "Проверяем настройки MinIO..."
mc ls myminio

echo "Запуск миграций базы данных..."
alembic upgrade head

echo "Запуск приложения..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000