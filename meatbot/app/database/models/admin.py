"""
Модели для административной системы
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AdminRole(str, Enum):
    """Роли администраторов"""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MODERATOR = "moderator"


class AdminUser(Base):
    """Модель администратора"""

    __tablename__ = "admin_users"

    # Основные поля
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="ID администратора",
    )
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        unique=True,
        comment="Telegram ID администратора",
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Telegram username администратора"
    )
    first_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Имя администратора"
    )
    last_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Фамилия администратора"
    )

    # Роль и права доступа
    role: Mapped[AdminRole] = mapped_column(
        String(50),
        default=AdminRole.MODERATOR,
        nullable=False,
        comment="Роль администратора",
    )

    # Статусные поля
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Активен ли администратор",
    )

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Дата создания",
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Последний вход"
    )

    def __repr__(self) -> str:
        return f"<AdminUser(id={
            self.id}, telegram_id={
            self.telegram_id}, role={
            self.role})>"

    @property
    def full_name(self) -> str:
        """Полное имя администратора"""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts) or self.username or f"Admin {self.telegram_id}"

    def has_permission(self, permission: str) -> bool:
        """Проверка прав доступа"""
        if not self.is_active:
            return False

        permissions = {
            AdminRole.SUPER_ADMIN: [
                "manage_catalog",
                "manage_orders",
                "manage_users",
                "manage_admins",
                "view_statistics",
                "manage_promotions",
            ],
            AdminRole.ADMIN: [
                "manage_catalog",
                "manage_orders",
                "view_statistics",
                "manage_promotions",
            ],
            AdminRole.MODERATOR: ["manage_catalog", "view_statistics"],
        }

        return permission in permissions.get(self.role, [])
