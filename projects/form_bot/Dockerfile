# FormBot Dockerfile
# Multi-stage build для оптимизации размера образа

FROM python:3.11-slim as builder

WORKDIR /app

# Устанавливаем зависимости для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Финальный образ
FROM python:3.11-slim

WORKDIR /app

# Создаём непривилегированного пользователя
RUN groupadd -r botuser && useradd -r -g botuser botuser

# Копируем зависимости из builder
COPY --from=builder /root/.local /home/botuser/.local

# Обновляем PATH
ENV PATH=/home/botuser/.local/bin:$PATH

# Копируем исходный код
COPY --chown=botuser:botuser . .

# Создаём директории для данных и логов
RUN mkdir -p /app/data /app/logs && \
    chown -R botuser:botuser /app/data /app/logs

# Переключаемся на непривилегированного пользователя
USER botuser

# Метаданные
LABEL maintainer="FormBot"
LABEL description="Telegram bot for collecting client applications"
LABEL version="1.0.0"

# Запуск бота
CMD ["python", "main.py"]
