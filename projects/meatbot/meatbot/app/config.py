from typing import Union

from pydantic import AnyUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str = ""
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@db:5432/meatbot"
    )
    redis_url: Union[AnyUrl, str] = "redis://redis:6379/0"
    env: str = "development"
    web_app_host: str = "0.0.0.0"
    web_app_port: int = 8000
    log_level: str = "info"
    run_migrations_on_start: bool = False

    # Celery configuration
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"
    celery_task_serializer: str = "json"
    celery_result_serializer: str = "json"
    celery_accept_content: list[str] = ["json"]
    celery_timezone: str = "UTC"
    celery_enable_utc: bool = True
    celery_task_track_started: bool = True
    celery_task_time_limit: int = 30 * 60  # 30 minutes
    celery_task_soft_time_limit: int = 25 * 60  # 25 minutes
    celery_worker_prefetch_multiplier: int = 1
    celery_task_acks_late: bool = True
    celery_worker_disable_rate_limits: bool = False

    # Cache configuration
    cache_default_ttl: int = 3600  # 1 hour
    cache_catalog_ttl: int = 1800  # 30 minutes
    cache_products_ttl: int = 900  # 15 minutes
    cache_sessions_ttl: int = 86400  # 24 hours
    cache_enabled: bool = True

    # Image optimization settings
    image_optimization_enabled: bool = True
    image_max_size: int = 5 * 1024 * 1024  # 5MB
    image_quality: int = 85
    image_format: str = "WEBP"

    # Security settings
    security_enabled: bool = True
    api_key: str = ""
    admin_key: str = ""
    encryption_key: str = ""
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    file_scan_enabled: bool = True
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: list[str] = ["jpg", "jpeg", "png", "webp"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",  # Ignore extra fields in .env file
    }


settings = Settings()
