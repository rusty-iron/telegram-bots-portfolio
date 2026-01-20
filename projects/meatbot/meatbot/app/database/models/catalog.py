"""
Модели каталога товаров
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Category(Base):
    """Модель категории товаров"""

    __tablename__ = "categories"

    # Основные поля
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="ID категории"
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Название категории")
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Описание категории"
    )
    image_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="URL изображения категории"
    )

    # Порядок отображения
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Порядок сортировки категории",
    )

    # Статусные поля
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Активна ли категория"
    )

    # Связи с другими моделями
    products = relationship(
        "Product",
        back_populates="category",
        cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Category(id={
            self.id}, name={
            self.name}, active={
            self.is_active})>"


class Product(Base):
    """Модель товара"""

    __tablename__ = "products"

    # Основные поля
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="ID товара"
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Название товара")
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Описание товара"
    )
    short_description: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Краткое описание товара"
    )

    # Цена и единицы измерения
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment="Цена товара")
    unit: Mapped[str] = mapped_column(
        String(50),
        default="шт",
        nullable=False,
        comment="Единица измерения (кг, шт, упак)",
    )

    # Изображения
    image_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="URL основного изображения товара"
    )
    images: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="JSON массив дополнительных изображений"
    )

    # Связь с категорией
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID категории товара",
    )

    # Порядок отображения
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Порядок сортировки товара в категории",
    )

    # Статусные поля
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Активен ли товар"
    )
    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Доступен ли товар для заказа",
    )

    # Версионирование для optimistic locking
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Версия записи для optimistic locking",
    )

    # Связи с другими моделями
    category = relationship("Category", back_populates="products")
    cart_items = relationship(
        "CartItem",
        back_populates="product",
        cascade="all, delete-orphan")
    order_items = relationship(
        "OrderItem",
        back_populates="product",
        cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Product(id={
            self.id}, name={
            self.name}, price={
            self.price}, active={
                self.is_active})>"

    @property
    def formatted_price(self) -> str:
        """Форматированная цена для отображения"""
        return f"{self.price:.2f} ₽"

    @property
    def display_name(self) -> str:
        """Отображаемое название товара с единицей измерения"""
        return f"{self.name} ({self.unit})"
