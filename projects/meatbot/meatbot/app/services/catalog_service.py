"""
Сервис каталога товаров с кэшированием
"""

from typing import Any, Dict, List, Optional

import structlog

from ..database import Category, Product, get_db
from .cache_service import CacheService, CatalogCacheService

logger = structlog.get_logger()


class CatalogService:
    """Сервис для работы с каталогом товаров"""

    def __init__(self, cache_service: CacheService):
        self.catalog_cache = CatalogCacheService(cache_service)

    def get_categories(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Получить все категории"""
        if use_cache:
            cached_categories = self.catalog_cache.get_categories()
            if cached_categories is not None:
                logger.debug("categories_cache_hit")
                return cached_categories

        logger.debug("categories_cache_miss")

        with get_db() as db:
            categories = (
                db.query(Category)
                .order_by(Category.sort_order, Category.name)
                .all()
            )

            categories_data = []
            for category in categories:
                categories_data.append(
                    {
                        "id": category.id,
                        "name": category.name,
                        "description": category.description,
                        "image_url": category.image_url,
                        "sort_order": category.sort_order,
                        "is_active": category.is_active,
                        "created_at": category.created_at.isoformat()
                        if category.created_at
                        else None,
                        "updated_at": category.updated_at.isoformat()
                        if category.updated_at
                        else None,
                    }
                )

            # Сохраняем в кэш
            self.catalog_cache.set_categories(categories_data)

            return categories_data

    def get_active_categories(
        self, use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Получить активные категории"""
        if use_cache:
            cached_categories = self.catalog_cache.get_active_categories()
            if cached_categories is not None:
                logger.debug("active_categories_cache_hit")
                return cached_categories

        logger.debug("active_categories_cache_miss")

        with get_db() as db:
            categories = (
                db.query(Category)
                .filter(Category.is_active.is_(True))
                .order_by(Category.sort_order, Category.name)
                .all()
            )

            categories_data = []
            for category in categories:
                categories_data.append(
                    {
                        "id": category.id,
                        "name": category.name,
                        "description": category.description,
                        "image_url": category.image_url,
                        "sort_order": category.sort_order,
                        "is_active": category.is_active,
                        "created_at": category.created_at.isoformat()
                        if category.created_at
                        else None,
                        "updated_at": category.updated_at.isoformat()
                        if category.updated_at
                        else None,
                    }
                )

            # Сохраняем в кэш
            self.catalog_cache.set_active_categories(categories_data)

            return categories_data

    def get_category_products(
        self, category_id: int, use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Получить товары категории"""
        if use_cache:
            cached_products = self.catalog_cache.get_category_products(
                category_id
            )
            if cached_products is not None:
                logger.debug(
                    "category_products_cache_hit", category_id=category_id
                )
                return cached_products

        logger.debug("category_products_cache_miss", category_id=category_id)

        with get_db() as db:
            products = (
                db.query(Product)
                .filter(
                    Product.category_id == category_id,
                    Product.is_active.is_(True),
                    Product.is_available.is_(True),
                )
                .order_by(Product.sort_order, Product.name)
                .all()
            )

            products_data = []
            for product in products:
                products_data.append(
                    {
                        "id": product.id,
                        "name": product.name,
                        "description": product.description,
                        "short_description": product.short_description,
                        "price": float(product.price),
                        "unit": product.unit,
                        "image_url": product.image_url,
                        "images": product.images,
                        "category_id": product.category_id,
                        "sort_order": product.sort_order,
                        "is_active": product.is_active,
                        "is_available": product.is_available,
                        "version": product.version,
                        "created_at": product.created_at.isoformat()
                        if product.created_at
                        else None,
                        "updated_at": product.updated_at.isoformat()
                        if product.updated_at
                        else None,
                    }
                )

            # Сохраняем в кэш
            self.catalog_cache.set_category_products(
                category_id, products_data
            )

            return products_data

    def get_product(
        self, product_id: int, use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Получить товар по ID"""
        if use_cache:
            cached_product = self.catalog_cache.get_product(product_id)
            if cached_product is not None:
                logger.debug("product_cache_hit", product_id=product_id)
                return cached_product

        logger.debug("product_cache_miss", product_id=product_id)

        with get_db() as db:
            product = (
                db.query(Product).filter(Product.id == product_id).first()
            )

            if not product:
                return None

            product_data = {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "short_description": product.short_description,
                "price": float(product.price),
                "unit": product.unit,
                "image_url": product.image_url,
                "images": product.images,
                "category_id": product.category_id,
                "sort_order": product.sort_order,
                "is_active": product.is_active,
                "is_available": product.is_available,
                "version": product.version,
                "created_at": product.created_at.isoformat()
                if product.created_at
                else None,
                "updated_at": product.updated_at.isoformat()
                if product.updated_at
                else None,
            }

            # Сохраняем в кэш
            self.catalog_cache.set_product(product_id, product_data)

            return product_data

    def get_active_products(
        self, use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Получить все активные товары"""
        if use_cache:
            cached_products = self.catalog_cache.get_active_products()
            if cached_products is not None:
                logger.debug("active_products_cache_hit")
                return cached_products

        logger.debug("active_products_cache_miss")

        with get_db() as db:
            products = (
                db.query(Product)
                .filter(
                    Product.is_active.is_(True), Product.is_available.is_(True)
                )
                .order_by(
                    Product.category_id, Product.sort_order, Product.name
                )
                .all()
            )

            products_data = []
            for product in products:
                products_data.append(
                    {
                        "id": product.id,
                        "name": product.name,
                        "description": product.description,
                        "short_description": product.short_description,
                        "price": float(product.price),
                        "unit": product.unit,
                        "image_url": product.image_url,
                        "images": product.images,
                        "category_id": product.category_id,
                        "sort_order": product.sort_order,
                        "is_active": product.is_active,
                        "is_available": product.is_available,
                        "version": product.version,
                        "created_at": product.created_at.isoformat()
                        if product.created_at
                        else None,
                        "updated_at": product.updated_at.isoformat()
                        if product.updated_at
                        else None,
                    }
                )

            # Сохраняем в кэш
            self.catalog_cache.set_active_products(products_data)

            return products_data

    def search_products(
        self, query: str, use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Поиск товаров по названию"""
        # Для поиска не используем кэш, так как результаты могут быть разными
        logger.debug("product_search", query=query)

        with get_db() as db:
            products = (
                db.query(Product)
                .filter(
                    Product.is_active.is_(True),
                    Product.is_available.is_(True),
                    Product.name.ilike(f"%{query}%"),
                )
                .order_by(Product.name)
                .limit(50)  # Ограничиваем результаты
                .all()
            )

            products_data = []
            for product in products:
                products_data.append(
                    {
                        "id": product.id,
                        "name": product.name,
                        "description": product.description,
                        "short_description": product.short_description,
                        "price": float(product.price),
                        "unit": product.unit,
                        "image_url": product.image_url,
                        "images": product.images,
                        "category_id": product.category_id,
                        "sort_order": product.sort_order,
                        "is_active": product.is_active,
                        "is_available": product.is_available,
                        "version": product.version,
                        "created_at": product.created_at.isoformat()
                        if product.created_at
                        else None,
                        "updated_at": product.updated_at.isoformat()
                        if product.updated_at
                        else None,
                    }
                )

            return products_data

    def invalidate_category_cache(self, category_id: int) -> None:
        """Инвалидировать кэш категории"""
        self.catalog_cache.invalidate_category(category_id)
        logger.info("category_cache_invalidated", category_id=category_id)

    def invalidate_product_cache(
        self, product_id: int, category_id: Optional[int] = None
    ) -> None:
        """Инвалидировать кэш товара"""
        self.catalog_cache.invalidate_product(product_id, category_id)
        logger.info(
            "product_cache_invalidated",
            product_id=product_id,
            category_id=category_id,
        )

    def invalidate_all_catalog_cache(self) -> None:
        """Инвалидировать весь кэш каталога"""
        self.catalog_cache.invalidate_all_catalog()
        logger.info("all_catalog_cache_invalidated")
