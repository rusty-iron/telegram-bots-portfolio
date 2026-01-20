"""
Сервис кэширования для MeatBot
"""

import json
from typing import Any, Dict, List, Optional

import structlog
from redis import Redis

from ..interfaces import ICacheService

logger = structlog.get_logger()


class CacheService(ICacheService):
    """Сервис для работы с кэшем Redis"""

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.default_ttl = 3600  # 1 час по умолчанию

    def _serialize(self, data: Any) -> bytes:
        """Сериализация данных для хранения в Redis

        SECURITY FIX (P2-CACHE-01): Use JSON instead of pickle to prevent RCE
        Pickle deserialization can execute arbitrary code if Redis is compromised
        """
        try:
            return json.dumps(data, default=str).encode("utf-8")
        except Exception as e:
            logger.error("cache_serialization_error", error=str(e), data_type=type(data).__name__)
            raise

    def _deserialize(self, data: bytes) -> Any:
        """Десериализация данных из Redis

        SECURITY FIX (P2-CACHE-01): Use JSON instead of pickle to prevent RCE
        Only JSON deserialization is safe for untrusted data sources
        """
        try:
            return json.loads(data.decode("utf-8"))
        except Exception as e:
            logger.error("cache_deserialization_error", error=str(e))
            raise

    def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        try:
            data = self.redis.get(key)
            if data is None:
                return None
            return self._deserialize(data)
        except Exception as e:
            logger.error("cache_get_error", key=key, error=str(e))
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Сохранить значение в кэш"""
        try:
            serialized_data = self._serialize(value)
            ttl = ttl or self.default_ttl
            result = self.redis.setex(key, ttl, serialized_data)
            return bool(result)
        except Exception as e:
            logger.error("cache_set_error", key=key, error=str(e))
            return False

    def delete(self, key: str) -> bool:
        """Удалить значение из кэша"""
        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error("cache_delete_error", key=key, error=str(e))
            return False

    def delete_pattern(self, pattern: str) -> int:
        """Удалить все ключи по паттерну"""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                result = self.redis.delete(*keys)
                return int(result) if result else 0
            return 0
        except Exception as e:
            logger.error(
                "cache_delete_pattern_error", pattern=pattern, error=str(e)
            )
            return 0

    def exists(self, key: str) -> bool:
        """Проверить существование ключа"""
        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            logger.error("cache_exists_error", key=key, error=str(e))
            return False

    def get_ttl(self, key: str) -> int:
        """Получить TTL ключа"""
        try:
            result = self.redis.ttl(key)
            return int(result) if result is not None else -1
        except Exception as e:
            logger.error("cache_ttl_error", key=key, error=str(e))
            return -1


class CatalogCacheService:
    """Специализированный сервис кэширования каталога"""

    def __init__(self, cache_service: CacheService):
        self.cache = cache_service

        # Ключи кэша
        self.CATEGORIES_KEY = "catalog:categories"
        self.CATEGORY_PRODUCTS_KEY = "catalog:category:{category_id}:products"
        self.PRODUCT_KEY = "catalog:product:{product_id}"
        self.ACTIVE_CATEGORIES_KEY = "catalog:categories:active"
        self.ACTIVE_PRODUCTS_KEY = "catalog:products:active"

        # TTL для разных типов данных
        self.CATEGORIES_TTL = 1800  # 30 минут
        self.PRODUCTS_TTL = 900  # 15 минут
        self.ACTIVE_TTL = 600  # 10 минут

    def get_categories(self) -> Optional[List[Dict[str, Any]]]:
        """Получить все категории из кэша"""
        return self.cache.get(self.CATEGORIES_KEY)

    def set_categories(self, categories: List[Dict[str, Any]]) -> bool:
        """Сохранить категории в кэш"""
        return self.cache.set(
            self.CATEGORIES_KEY, categories, self.CATEGORIES_TTL
        )

    def get_active_categories(self) -> Optional[List[Dict[str, Any]]]:
        """Получить активные категории из кэша"""
        return self.cache.get(self.ACTIVE_CATEGORIES_KEY)

    def set_active_categories(self, categories: List[Dict[str, Any]]) -> bool:
        """Сохранить активные категории в кэш"""
        return self.cache.set(
            self.ACTIVE_CATEGORIES_KEY, categories, self.ACTIVE_TTL
        )

    def get_category_products(
        self, category_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """Получить товары категории из кэша"""
        key = self.CATEGORY_PRODUCTS_KEY.format(category_id=category_id)
        return self.cache.get(key)

    def set_category_products(
        self, category_id: int, products: List[Dict[str, Any]]
    ) -> bool:
        """Сохранить товары категории в кэш"""
        key = self.CATEGORY_PRODUCTS_KEY.format(category_id=category_id)
        return self.cache.set(key, products, self.PRODUCTS_TTL)

    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Получить товар из кэша"""
        key = self.PRODUCT_KEY.format(product_id=product_id)
        return self.cache.get(key)

    def set_product(self, product_id: int, product: Dict[str, Any]) -> bool:
        """Сохранить товар в кэш"""
        key = self.PRODUCT_KEY.format(product_id=product_id)
        return self.cache.set(key, product, self.PRODUCTS_TTL)

    def get_active_products(self) -> Optional[List[Dict[str, Any]]]:
        """Получить все активные товары из кэша"""
        return self.cache.get(self.ACTIVE_PRODUCTS_KEY)

    def set_active_products(self, products: List[Dict[str, Any]]) -> bool:
        """Сохранить все активные товары в кэш"""
        return self.cache.set(
            self.ACTIVE_PRODUCTS_KEY, products, self.ACTIVE_TTL
        )

    def invalidate_category(self, category_id: int) -> None:
        """Инвалидировать кэш категории"""
        # Удаляем категорию из списка категорий
        self.cache.delete(self.CATEGORIES_KEY)
        self.cache.delete(self.ACTIVE_CATEGORIES_KEY)

        # Удаляем товары категории
        key = self.CATEGORY_PRODUCTS_KEY.format(category_id=category_id)
        self.cache.delete(key)

        # Удаляем общий кэш активных товаров
        self.cache.delete(self.ACTIVE_PRODUCTS_KEY)

        logger.info(
            "cache_invalidated", type="category", category_id=category_id
        )

    def invalidate_product(
        self, product_id: int, category_id: Optional[int] = None
    ) -> None:
        """Инвалидировать кэш товара"""
        # Удаляем товар
        key = self.PRODUCT_KEY.format(product_id=product_id)
        self.cache.delete(key)

        # Удаляем товары категории если указана
        if category_id:
            key = self.CATEGORY_PRODUCTS_KEY.format(category_id=category_id)
            self.cache.delete(key)

        # Удаляем общий кэш активных товаров
        self.cache.delete(self.ACTIVE_PRODUCTS_KEY)

        logger.info(
            "cache_invalidated",
            type="product",
            product_id=product_id,
            category_id=category_id,
        )

    def invalidate_all_catalog(self) -> None:
        """Инвалидировать весь кэш каталога"""
        self.cache.delete_pattern("catalog:*")
        logger.info("cache_invalidated", type="all_catalog")


class UserSessionCacheService:
    """Сервис кэширования пользовательских сессий"""

    def __init__(self, cache_service: CacheService):
        self.cache = cache_service

        # Ключи кэша
        self.USER_SESSION_KEY = "user:session:{user_id}"
        self.USER_CART_KEY = "user:cart:{user_id}"
        self.USER_STATE_KEY = "user:state:{user_id}"

        # TTL
        self.SESSION_TTL = 86400  # 24 часа
        self.CART_TTL = 3600  # 1 час
        self.STATE_TTL = 1800  # 30 минут

    def get_user_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить сессию пользователя"""
        key = self.USER_SESSION_KEY.format(user_id=user_id)
        return self.cache.get(key)

    def set_user_session(
        self, user_id: int, session_data: Dict[str, Any]
    ) -> bool:
        """Сохранить сессию пользователя"""
        key = self.USER_SESSION_KEY.format(user_id=user_id)
        return self.cache.set(key, session_data, self.SESSION_TTL)

    def get_user_cart(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить корзину пользователя"""
        key = self.USER_CART_KEY.format(user_id=user_id)
        return self.cache.get(key)

    def set_user_cart(self, user_id: int, cart_data: Dict[str, Any]) -> bool:
        """Сохранить корзину пользователя"""
        key = self.USER_CART_KEY.format(user_id=user_id)
        return self.cache.set(key, cart_data, self.CART_TTL)

    def get_user_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить состояние пользователя (FSM)"""
        key = self.USER_STATE_KEY.format(user_id=user_id)
        return self.cache.get(key)

    def set_user_state(self, user_id: int, state_data: Dict[str, Any]) -> bool:
        """Сохранить состояние пользователя (FSM)"""
        key = self.USER_STATE_KEY.format(user_id=user_id)
        return self.cache.set(key, state_data, self.STATE_TTL)

    def clear_user_data(self, user_id: int) -> None:
        """Очистить все данные пользователя"""
        patterns = [
            self.USER_SESSION_KEY.format(user_id=user_id),
            self.USER_CART_KEY.format(user_id=user_id),
            self.USER_STATE_KEY.format(user_id=user_id),
        ]

        for pattern in patterns:
            self.cache.delete(pattern)

        logger.info("user_cache_cleared", user_id=user_id)
