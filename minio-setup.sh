#!/bin/sh
set -e

echo "Ожидание запуска MinIO..."
while ! curl -s http://minio:9000/minio/health/live > /dev/null; do
  sleep 1
done

echo "MinIO запущен, настраиваем..."

# Настройка клиента mc
mc alias set myminio http://minio:9000 minioadmin minioadmin

# Ожидаем полной инициализации MinIO
sleep 3

# Создаем bucket если не существует
if ! mc ls myminio/kitchen-blocks > /dev/null 2>&1; then
  echo "Создаем bucket: kitchen-blocks"
  mc mb myminio/kitchen-blocks
fi

# Устанавливаем публичную политику доступа для bucket
echo "Устанавливаем публичную политику доступа..."
mc policy set public myminio/kitchen-blocks

echo "Настройка MinIO завершена!"