# Этап сборки зависимостей
FROM python:3.10-slim as builder

WORKDIR /app

# Установка системных зависимостей для всех платформ
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    xclip \
    xdg-utils && \
    rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --user -r requirements.txt

# Финальный образ
FROM python:3.10-slim

WORKDIR /app
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Установка кросс-платформенных зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    xclip \
    xdg-utils \
    libgl1 \
    libx11-6 && \
    rm -rf /var/lib/apt/lists/*

# Копируем зависимости и код
COPY --from=builder /root/.local /root/.local
COPY . .

# Создаем необходимые директории с правильными правами
RUN mkdir -p \
    uploads \
    youtube_downloads \
    logs \
    instance && \
    chmod -R 755 /app && \
    chown -R nobody:nogroup /app

# Настройки окружения
ENV FLASK_ENV=production
ENV UPLOAD_FOLDER=/app/uploads
ENV YT_DOWNLOAD_FOLDER=/app/youtube_downloads
ENV LOG_FOLDER=/app/logs
ENV DISPLAY=host.docker.internal:0

# Прокидываем порт
EXPOSE 8080

# Команда запуска с поддержкой X11
CMD ["sh", "-c", "chmod 777 /tmp/.X11-unix && gunicorn --bind 0.0.0.0:8080 --worker-class eventlet -w 1 run:app"]