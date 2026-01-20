"""
Сервис конфигурации для MeatBot
"""

from typing import Any

from ..config import settings
from ..interfaces import IConfigService


class ConfigService(IConfigService):
    """Сервис для работы с конфигурацией"""

    def get(self, key: str, default: Any = None) -> Any:
        """Получить значение конфигурации"""
        return getattr(settings, key, default)

    def get_database_url(self) -> str:
        """Получить URL базы данных"""
        return settings.database_url

    def get_redis_url(self) -> str:
        """Получить URL Redis"""
        return str(settings.redis_url)

    def get_bot_token(self) -> str:
        """Получить токен бота"""
        return settings.bot_token

    def is_development(self) -> bool:
        """Проверить, является ли окружение разработкой"""
        return settings.env == "development"

    def get_cache_ttl(self, cache_type: str) -> int:
        """Получить TTL для типа кэша"""
        ttl_map = {
            "default": settings.cache_default_ttl,
            "catalog": settings.cache_catalog_ttl,
            "products": settings.cache_products_ttl,
            "sessions": settings.cache_sessions_ttl,
        }
        return ttl_map.get(cache_type, settings.cache_default_ttl)

    def is_cache_enabled(self) -> bool:
        """Проверить, включен ли кэш"""
        return settings.cache_enabled

    def get_image_settings(self) -> dict:
        """Получить настройки изображений"""
        return {
            "optimization_enabled": settings.image_optimization_enabled,
            "max_size": settings.image_max_size,
            "quality": settings.image_quality,
            "format": settings.image_format,
        }

    def get_celery_settings(self) -> dict:
        """Получить настройки Celery"""
        return {
            "broker_url": settings.celery_broker_url,
            "result_backend": settings.celery_result_backend,
            "task_serializer": settings.celery_task_serializer,
            "result_serializer": settings.celery_result_serializer,
            "accept_content": settings.celery_accept_content,
            "timezone": settings.celery_timezone,
            "enable_utc": settings.celery_enable_utc,
            "task_track_started": settings.celery_task_track_started,
            "task_time_limit": settings.celery_task_time_limit,
            "task_soft_time_limit": settings.celery_task_soft_time_limit,
            "worker_prefetch_multiplier": settings.celery_worker_prefetch_multiplier,
            "task_acks_late": settings.celery_task_acks_late,
            "worker_disable_rate_limits": settings.celery_worker_disable_rate_limits,
        }
