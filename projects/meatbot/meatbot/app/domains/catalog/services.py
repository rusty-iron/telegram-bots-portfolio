"""
Сервисы домена каталога
"""

from typing import Any, Dict, List, Optional

import structlog

from ...interfaces import ICacheService, IDatabaseService

logger = structlog.get_logger()


class CatalogDomainService:
    """Сервис домена каталога"""

    def __init__(
        self, cache_service: ICacheService, database_service: IDatabaseService
    ):
        self.cache = cache_service
        self.database = database_service

    def get_categories(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Получить все категории"""
        cache_key = "catalog:categories:all"

        if use_cache and self.cache.exists(cache_key):
            return self.cache.get(cache_key)

        # Получаем из базы данных
        query = """
            SELECT id, name, description, is_active, created_at, updated_at
            FROM categories
            ORDER BY name
        """

        try:
            result = self.database.execute_query(query)
            categories = []

            for row in result:
                categories.append(
                    {
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "is_active": row[3],
                        "created_at": row[4].isoformat() if row[4] else None,
                        "updated_at": row[5].isoformat() if row[5] else None,
                    }
                )

            # Сохраняем в кэш
            if use_cache:
                self.cache.set(cache_key, categories, ttl=1800)  # 30 минут

            return categories

        except Exception as e:
            logger.error("get_categories_failed", error=str(e))
            return []

    def get_active_categories(
        self, use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Получить активные категории"""
        cache_key = "catalog:categories:active"

        if use_cache and self.cache.exists(cache_key):
            return self.cache.get(cache_key)

        # Получаем из базы данных
        query = """
            SELECT id, name, description, created_at, updated_at
            FROM categories
            WHERE is_active = true
            ORDER BY name
        """

        try:
            result = self.database.execute_query(query)
            categories = []

            for row in result:
                categories.append(
                    {
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "created_at": row[4].isoformat() if row[4] else None,
                        "updated_at": row[5].isoformat() if row[5] else None,
                    }
                )

            # Сохраняем в кэш
            if use_cache:
                self.cache.set(cache_key, categories, ttl=1800)  # 30 минут

            return categories

        except Exception as e:
            logger.error("get_active_categories_failed", error=str(e))
            return []

    def get_category_products(
        self, category_id: int, use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Получить товары категории"""
        cache_key = f"catalog:products:category:{category_id}"

        if use_cache and self.cache.exists(cache_key):
            return self.cache.get(cache_key)

        # Получаем из базы данных
        query = """
            SELECT p.id, p.name, p.description, p.price, p.is_active, p.created_at, p.updated_at
            FROM products p
            WHERE p.category_id = %s
            ORDER BY p.name
        """

        try:
            result = self.database.execute_query(
                query, {"category_id": category_id}
            )
            products = []

            for row in result:
                products.append(
                    {
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "price": float(row[3]) if row[3] else 0.0,
                        "is_active": row[4],
                        "created_at": row[5].isoformat() if row[5] else None,
                        "updated_at": row[6].isoformat() if row[6] else None,
                    }
                )

            # Сохраняем в кэш
            if use_cache:
                self.cache.set(cache_key, products, ttl=900)  # 15 минут

            return products

        except Exception as e:
            logger.error(
                "get_category_products_failed",
                category_id=category_id,
                error=str(e),
            )
            return []

    def get_product(
        self, product_id: int, use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Получить товар по ID"""
        cache_key = f"catalog:product:{product_id}"

        if use_cache and self.cache.exists(cache_key):
            return self.cache.get(cache_key)

        # Получаем из базы данных
        query = """
            SELECT p.id, p.name, p.description, p.price, p.is_active, p.created_at, p.updated_at,
                   c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = %s
        """

        try:
            result = self.database.execute_query(
                query, {"product_id": product_id}
            )

            if result:
                row = result[0]
                product = {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "price": float(row[3]) if row[3] else 0.0,
                    "is_active": row[4],
                    "created_at": row[5].isoformat() if row[5] else None,
                    "updated_at": row[6].isoformat() if row[6] else None,
                    "category_name": row[7],
                }

                # Сохраняем в кэш
                if use_cache:
                    self.cache.set(cache_key, product, ttl=900)  # 15 минут

                return product

            return None

        except Exception as e:
            logger.error(
                "get_product_failed", product_id=product_id, error=str(e)
            )
            return None

    def search_products(
        self, query: str, use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Поиск товаров"""
        cache_key = f"catalog:search:{query.lower()}"

        if use_cache and self.cache.exists(cache_key):
            return self.cache.get(cache_key)

        # Получаем из базы данных
        search_query = """
            SELECT p.id, p.name, p.description, p.price, p.is_active, p.created_at, p.updated_at,
                   c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.name ILIKE %s OR p.description ILIKE %s
            ORDER BY p.name
        """

        search_pattern = f"%{query}%"

        try:
            result = self.database.execute_query(
                search_query,
                {"pattern1": search_pattern, "pattern2": search_pattern},
            )
            products = []

            for row in result:
                products.append(
                    {
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "price": float(row[3]) if row[3] else 0.0,
                        "is_active": row[4],
                        "created_at": row[5].isoformat() if row[5] else None,
                        "updated_at": row[6].isoformat() if row[6] else None,
                        "category_name": row[7],
                    }
                )

            # Сохраняем в кэш
            if use_cache:
                self.cache.set(cache_key, products, ttl=300)  # 5 минут

            return products

        except Exception as e:
            logger.error("search_products_failed", query=query, error=str(e))
            return []

    def invalidate_cache(self, cache_type: str = "all") -> None:
        """Очистить кэш"""
        if cache_type == "all":
            # Очищаем все ключи каталога
            patterns = [
                "catalog:categories:*",
                "catalog:products:*",
                "catalog:search:*",
            ]

            for pattern in patterns:
                # В реальной реализации здесь был бы поиск по паттерну
                logger.info("cache_invalidated", pattern=pattern)
        else:
            logger.info("cache_invalidated", cache_type=cache_type)
