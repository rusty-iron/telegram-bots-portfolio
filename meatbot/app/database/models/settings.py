"""
Модели настроек системы
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class PaymentSettings(Base):
    """Модель настроек платежей"""

    __tablename__ = "payment_settings"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="ID настроек"
    )

    # Реквизиты для перевода
    bank_name: Mapped[str] = mapped_column(
        String(255),
        default="Сбербанк",
        nullable=False,
        comment="Название банка",
    )

    # SECURITY WARNING: Store only masked card number or last 4 digits
    # ⚠️ NEVER store full card numbers in plain text for PCI DSS compliance!
    # Recommended format: "**** **** **** 1234" or "СберБанк ...1234"
    card_number: Mapped[str] = mapped_column(
        String(50),
        default="**** **** **** 1234",
        nullable=False,
        comment="Номер карты (только маскированный)",
    )

    recipient_name: Mapped[str] = mapped_column(
        String(255),
        default="ИП Иванов И.И.",
        nullable=False,
        comment="Имя получателя",
    )

    # Дополнительная информация
    additional_info: Mapped[str] = mapped_column(
        Text,
        default="После перевода отправьте скриншот или фото чека для подтверждения оплаты.",
        nullable=False,
        comment="Дополнительная информация",
    )

    # Активность настроек
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Активны ли настройки",
    )

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Дата создания",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Дата обновления",
    )

    def __repr__(self) -> str:
        return f"<PaymentSettings(id={self.id}, bank={self.bank_name})>"
