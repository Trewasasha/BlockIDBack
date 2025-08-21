FROM python:3.10-slim

ENV PYTHONPATH="/app"

WORKDIR /app

# Установка системных зависимостей включая curl для mc
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка mc клиента MinIO
RUN curl https://dl.min.io/client/mc/release/linux-amd64/mc \
    -o /usr/bin/mc && \
    chmod +x /usr/bin/mc

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем entrypoint скрипт
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Копируем остальные файлы
COPY . .

# Команда для запуска
ENTRYPOINT ["/entrypoint.sh"]