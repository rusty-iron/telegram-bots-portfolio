"""
Интерфейсы для сервисов MeatBot
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ICacheService(ABC):
    """Интерфейс сервиса кэширования"""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Сохранить значение в кэш"""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Удалить значение из кэша"""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Проверить существование ключа"""
        pass


class ICatalogService(ABC):
    """Интерфейс сервиса каталога"""

    @abstractmethod
    def get_categories(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Получить все категории"""
        pass

    @abstractmethod
    def get_active_categories(
        self, use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Получить активные категории"""
        pass

    @abstractmethod
    def get_category_products(
        self, category_id: int, use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Получить товары категории"""
        pass

    @abstractmethod
    def get_product(
        self, product_id: int, use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Получить товар по ID"""
        pass

    @abstractmethod
    def search_products(
        self, query: str, use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Поиск товаров"""
        pass


class IImageService(ABC):
    """Интерфейс сервиса изображений"""

    @abstractmethod
    def optimize_image(
        self,
        image_data: bytes,
        output_format: str = "WEBP",
        max_size: Optional[tuple] = None,
        quality: Optional[int] = None,
    ) -> bytes:
        """Оптимизировать изображение"""
        pass

    @abstractmethod
    def save_optimized_image(
        self, image_data: bytes, filename: str, image_type: str = "product"
    ) -> str:
        """Сохранить оптимизированное изображение"""
        pass

    @abstractmethod
    def validate_image(self, image_data: bytes) -> bool:
        """Проверить валидность изображения"""
        pass


class IUserService(ABC):
    """Интерфейс сервиса пользователей"""

    @abstractmethod
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить пользователя по ID"""
        pass

    @abstractmethod
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создать пользователя"""
        pass

    @abstractmethod
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """Обновить пользователя"""
        pass

    @abstractmethod
    def is_admin(self, user_id: int) -> bool:
        """Проверить, является ли пользователь администратором"""
        pass


class ICartService(ABC):
    """Интерфейс сервиса корзины"""

    @abstractmethod
    def get_cart(self, user_id: int) -> Dict[str, Any]:
        """Получить корзину пользователя"""
        pass

    @abstractmethod
    def add_to_cart(
        self,
        user_id: int,
        product_id: int,
        quantity: int,
        notes: Optional[str] = None,
    ) -> bool:
        """Добавить товар в корзину"""
        pass

    @abstractmethod
    def update_cart_item(
        self,
        user_id: int,
        item_id: int,
        quantity: int,
        notes: Optional[str] = None,
    ) -> bool:
        """Обновить товар в корзине"""
        pass

    @abstractmethod
    def remove_from_cart(self, user_id: int, item_id: int) -> bool:
        """Удалить товар из корзины"""
        pass

    @abstractmethod
    def clear_cart(self, user_id: int) -> bool:
        """Очистить корзину"""
        pass


class IOrderService(ABC):
    """Интерфейс сервиса заказов"""

    @abstractmethod
    def create_order(
        self, user_id: int, order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Создать заказ"""
        pass

    @abstractmethod
    def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Получить заказ по ID"""
        pass

    @abstractmethod
    def get_user_orders(
        self, user_id: int, limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Получить заказы пользователя"""
        pass

    @abstractmethod
    def update_order_status(self, order_id: int, status: str) -> bool:
        """Обновить статус заказа"""
        pass


class IAdminService(ABC):
    """Интерфейс сервиса администратора"""

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику"""
        pass

    @abstractmethod
    def get_users(
        self, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Получить список пользователей"""
        pass

    @abstractmethod
    def get_orders(
        self, limit: int = 50, offset: int = 0, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Получить список заказов"""
        pass

    @abstractmethod
    def create_category(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создать категорию"""
        pass

    @abstractmethod
    def update_category(
        self, category_id: int, category_data: Dict[str, Any]
    ) -> bool:
        """Обновить категорию"""
        pass

    @abstractmethod
    def delete_category(self, category_id: int) -> bool:
        """Удалить категорию"""
        pass

    @abstractmethod
    def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создать товар"""
        pass

    @abstractmethod
    def update_product(
        self, product_id: int, product_data: Dict[str, Any]
    ) -> bool:
        """Обновить товар"""
        pass

    @abstractmethod
    def delete_product(self, product_id: int) -> bool:
        """Удалить товар"""
        pass


class ILogger(ABC):
    """Интерфейс логгера"""

    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Логировать информационное сообщение"""
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Логировать предупреждение"""
        pass

    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """Логировать ошибку"""
        pass

    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Логировать отладочное сообщение"""
        pass


class IDatabaseService(ABC):
    """Интерфейс сервиса базы данных"""

    @abstractmethod
    def get_connection(self):
        """Получить соединение с базой данных"""
        pass

    @abstractmethod
    def execute_query(self, query: str, params: Optional[Dict] = None) -> Any:
        """Выполнить запрос"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Проверить соединение с базой данных"""
        pass


class IConfigService(ABC):
    """Интерфейс сервиса конфигурации"""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Получить значение конфигурации"""
        pass

    @abstractmethod
    def get_database_url(self) -> str:
        """Получить URL базы данных"""
        pass

    @abstractmethod
    def get_redis_url(self) -> str:
        """Получить URL Redis"""
        pass

    @abstractmethod
    def get_bot_token(self) -> str:
        """Получить токен бота"""
        pass

    @abstractmethod
    def is_development(self) -> bool:
        """Проверить, является ли окружение разработкой"""
        pass
