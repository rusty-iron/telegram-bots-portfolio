from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine, create_engine


def create_sync_engine(database_url: str) -> Engine:
    """Создает оптимизированный engine для базы данных с connection pooling"""
    return create_engine(
        database_url,
        # Connection pooling settings
        pool_size=10,  # Количество соединений в пуле
        max_overflow=20,  # Дополнительные соединения при превышении pool_size
        pool_pre_ping=True,  # Проверка соединений перед использованием
        pool_recycle=3600,  # Пересоздание соединений каждый час
        pool_timeout=30,  # Таймаут ожидания соединения
        # Performance settings
        future=True,  # Использовать SQLAlchemy 2.0 API
        echo=False,  # Отключить логирование SQL (включить для отладки)
        # Connection settings
        connect_args={
            "connect_timeout": 10,  # Таймаут подключения
            "application_name": "meatbot",  # Имя приложения в PostgreSQL
        },
    )


def check_db_connection(engine: Engine) -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
