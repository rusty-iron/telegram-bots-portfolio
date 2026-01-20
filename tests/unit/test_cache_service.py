"""
Unit тесты для CacheService
"""

from unittest.mock import Mock

import pytest

from meatbot.app.services.cache_service import (
    CacheService,
    CatalogCacheService,
    UserSessionCacheService,
)


class TestCacheService:
    """Тесты для CacheService"""

    @pytest.fixture
    def mock_redis(self):
        """Мок Redis клиента"""
        mock = Mock()
        mock.get.return_value = None
        mock.set.return_value = True
        mock.delete.return_value = True
        mock.exists.return_value = False
        return mock

    @pytest.fixture
    def cache_service(self, mock_redis):
        """Экземпляр CacheService"""
        return CacheService(mock_redis)

    def test_get_existing_key(self, cache_service, mock_redis):
        """Тест получения существующего ключа"""
        # Arrange
        mock_redis.get.return_value = b'{"test": "value"}'

        # Act
        result = cache_service.get("test_key")

        # Assert
        assert result == {"test": "value"}
        mock_redis.get.assert_called_once_with("test_key")

    def test_get_nonexistent_key(self, cache_service, mock_redis):
        """Тест получения несуществующего ключа"""
        # Arrange
        mock_redis.get.return_value = None

        # Act
        result = cache_service.get("nonexistent_key")

        # Assert
        assert result is None
        mock_redis.get.assert_called_once_with("nonexistent_key")

    def test_set_value(self, cache_service, mock_redis):
        """Тест сохранения значения"""
        # Arrange
        test_data = {"test": "value"}
        mock_redis.set.return_value = True

        # Act
        result = cache_service.set("test_key", test_data, ttl=3600)

        # Assert
        assert result is True
        mock_redis.set.assert_called_once()

    def test_set_value_with_default_ttl(self, cache_service, mock_redis):
        """Тест сохранения значения с TTL по умолчанию"""
        # Arrange
        test_data = {"test": "value"}
        mock_redis.set.return_value = True

        # Act
        result = cache_service.set("test_key", test_data)

        # Assert
        assert result is True
        mock_redis.set.assert_called_once()

    def test_delete_key(self, cache_service, mock_redis):
        """Тест удаления ключа"""
        # Arrange
        mock_redis.delete.return_value = True

        # Act
        result = cache_service.delete("test_key")

        # Assert
        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")

    def test_exists_key(self, cache_service, mock_redis):
        """Тест проверки существования ключа"""
        # Arrange
        mock_redis.exists.return_value = True

        # Act
        result = cache_service.exists("test_key")

        # Assert
        assert result is True
        mock_redis.exists.assert_called_once_with("test_key")

    def test_redis_connection_error(self, cache_service, mock_redis):
        """Тест обработки ошибки подключения к Redis"""
        # Arrange
        mock_redis.get.side_effect = Exception("Connection error")

        # Act & Assert
        with pytest.raises(Exception):
            cache_service.get("test_key")


class TestCatalogCacheService:
    """Тесты для CatalogCacheService"""

    @pytest.fixture
    def mock_redis(self):
        """Мок Redis клиента"""
        mock = Mock()
        mock.get.return_value = None
        mock.set.return_value = True
        mock.delete.return_value = True
        mock.exists.return_value = False
        return mock

    @pytest.fixture
    def catalog_cache_service(self, mock_redis):
        """Экземпляр CatalogCacheService"""
        return CatalogCacheService(mock_redis)

    def test_get_categories_cache_hit(self, catalog_cache_service, mock_redis):
        """Тест получения категорий из кэша"""
        # Arrange
        cached_categories = [{"id": 1, "name": "Test Category"}]
        mock_redis.get.return_value = b'[{"id": 1, "name": "Test Category"}]'

        # Act
        result = catalog_cache_service.get_categories()

        # Assert
        assert result == cached_categories
        mock_redis.get.assert_called_once_with("catalog:categories:all")

    def test_get_categories_cache_miss(
        self, catalog_cache_service, mock_redis
    ):
        """Тест получения категорий при промахе кэша"""
        # Arrange
        mock_redis.get.return_value = None

        # Act
        result = catalog_cache_service.get_categories()

        # Assert
        assert result is None
        mock_redis.get.assert_called_once_with("catalog:categories:all")

    def test_set_categories(self, catalog_cache_service, mock_redis):
        """Тест сохранения категорий в кэш"""
        # Arrange
        categories = [{"id": 1, "name": "Test Category"}]
        mock_redis.set.return_value = True

        # Act
        result = catalog_cache_service.set_categories(categories)

        # Assert
        assert result is True
        mock_redis.set.assert_called_once()

    def test_get_products_cache_hit(self, catalog_cache_service, mock_redis):
        """Тест получения товаров из кэша"""
        # Arrange
        cached_products = [{"id": 1, "name": "Test Product"}]
        mock_redis.get.return_value = b'[{"id": 1, "name": "Test Product"}]'

        # Act
        result = catalog_cache_service.get_products(1)

        # Assert
        assert result == cached_products
        mock_redis.get.assert_called_once_with("catalog:products:category:1")

    def test_invalidate_categories(self, catalog_cache_service, mock_redis):
        """Тест инвалидации кэша категорий"""
        # Arrange
        mock_redis.delete.return_value = True

        # Act
        result = catalog_cache_service.invalidate_categories()

        # Assert
        assert result is True
        mock_redis.delete.assert_called_once_with("catalog:categories:all")


class TestUserSessionCacheService:
    """Тесты для UserSessionCacheService"""

    @pytest.fixture
    def mock_redis(self):
        """Мок Redis клиента"""
        mock = Mock()
        mock.get.return_value = None
        mock.set.return_value = True
        mock.delete.return_value = True
        mock.exists.return_value = False
        return mock

    @pytest.fixture
    def user_session_cache_service(self, mock_redis):
        """Экземпляр UserSessionCacheService"""
        return UserSessionCacheService(mock_redis)

    def test_get_user_session(self, user_session_cache_service, mock_redis):
        """Тест получения пользовательской сессии"""
        # Arrange
        session_data = {"user_id": 123, "state": "active"}
        mock_redis.get.return_value = b'{"user_id": 123, "state": "active"}'

        # Act
        result = user_session_cache_service.get_user_session(123)

        # Assert
        assert result == session_data
        mock_redis.get.assert_called_once_with("user:session:123")

    def test_set_user_session(self, user_session_cache_service, mock_redis):
        """Тест сохранения пользовательской сессии"""
        # Arrange
        session_data = {"user_id": 123, "state": "active"}
        mock_redis.set.return_value = True

        # Act
        result = user_session_cache_service.set_user_session(123, session_data)

        # Assert
        assert result is True
        mock_redis.set.assert_called_once()

    def test_delete_user_session(self, user_session_cache_service, mock_redis):
        """Тест удаления пользовательской сессии"""
        # Arrange
        mock_redis.delete.return_value = True

        # Act
        result = user_session_cache_service.delete_user_session(123)

        # Assert
        assert result is True
        mock_redis.delete.assert_called_once_with("user:session:123")

    def test_get_user_cart(self, user_session_cache_service, mock_redis):
        """Тест получения корзины пользователя"""
        # Arrange
        cart_data = {"items": [{"product_id": 1, "quantity": 2}]}
        mock_redis.get.return_value = (
            b'{"items": [{"product_id": 1, "quantity": 2}]}'
        )

        # Act
        result = user_session_cache_service.get_user_cart(123)

        # Assert
        assert result == cart_data
        mock_redis.get.assert_called_once_with("user:cart:123")

    def test_set_user_cart(self, user_session_cache_service, mock_redis):
        """Тест сохранения корзины пользователя"""
        # Arrange
        cart_data = {"items": [{"product_id": 1, "quantity": 2}]}
        mock_redis.set.return_value = True

        # Act
        result = user_session_cache_service.set_user_cart(123, cart_data)

        # Assert
        assert result is True
        mock_redis.set.assert_called_once()
