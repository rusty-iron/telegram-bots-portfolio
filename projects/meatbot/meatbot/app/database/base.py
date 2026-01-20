"""
Базовая конфигурация для SQLAlchemy моделей
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовая модель для всех таблиц"""

    # Автоматические поля для всех моделей
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Дата создания записи",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Дата последнего обновления записи",
    )

    def to_dict(self) -> dict[str, Any]:
        """Преобразование модели в словарь для JSON сериализации"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def __repr__(self) -> str:
        """Строковое представление модели для отладки"""
        return f"<{self.__class__.__name__}(id={getattr(self, 'id', 'N/A')})>"
