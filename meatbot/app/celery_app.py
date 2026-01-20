"""
Celery приложение для MeatBot
"""

from __future__ import annotations

from celery import Celery

from .config import settings


def create_celery_app() -> Celery:
    """Создание и настройка Celery приложения"""

    celery_app = Celery(
        "meatbot",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
        include=[
            "meatbot.app.tasks.orders",
            "meatbot.app.tasks.notifications",
            "meatbot.app.tasks.webhooks",
        ],
    )

    # Конфигурация Celery
    celery_app.conf.update(
        task_serializer=settings.celery_task_serializer,
        result_serializer=settings.celery_result_serializer,
        accept_content=settings.celery_accept_content,
        timezone=settings.celery_timezone,
        enable_utc=settings.celery_enable_utc,
        task_track_started=settings.celery_task_track_started,
        task_time_limit=settings.celery_task_time_limit,
        task_soft_time_limit=settings.celery_task_soft_time_limit,
        worker_prefetch_multiplier=settings.celery_worker_prefetch_multiplier,
        task_acks_late=settings.celery_task_acks_late,
        worker_disable_rate_limits=settings.celery_worker_disable_rate_limits,
    )

    # Настройка маршрутизации задач по приоритетам
    celery_app.conf.task_routes = {
        "meatbot.app.tasks.webhooks.*": {"queue": "critical"},
        "meatbot.app.tasks.orders.*": {"queue": "high"},
        "meatbot.app.tasks.notifications.*": {"queue": "normal"},
    }

    return celery_app


# Создаем глобальный экземпляр Celery
celery_app = create_celery_app()
