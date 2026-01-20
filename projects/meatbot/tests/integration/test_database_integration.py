"""
Интеграционные тесты для работы с базой данных
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from meatbot.app.database.base import Base
from meatbot.app.database.models.category import Category
from meatbot.app.database.models.product import Product
from meatbot.app.database.models.user import User
from meatbot.app.services.database_service import DatabaseService


class TestDatabaseIntegration:
    """Интеграционные тесты для базы данных"""

    @pytest.fixture(scope="class")
    def test_engine(self):
        """Создает тестовый engine для базы данных"""
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        return engine

    @pytest.fixture(scope="class")
    def test_session(self, test_engine):
        """Создает тестовую сессию"""
        Session = sessionmaker(bind=test_engine)
        session = Session()
        yield session
        session.close()

    @pytest.fixture
    def database_service(self, test_session):
        """Создает экземпляр DatabaseService"""
        return DatabaseService()

    def test_user_creation_and_retrieval(self, test_session, database_service):
        """Тест создания и получения пользователя"""
        # Создаем пользователя
        user = User(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User",
        )

        test_session.add(user)
        test_session.commit()

        # Получаем пользователя
        query = "SELECT * FROM users WHERE telegram_id = :telegram_id"
        result = database_service.fetch_one(query, {"telegram_id": 123456789})

        assert result is not None
        assert result["telegram_id"] == 123456789
        assert result["username"] == "testuser"
        assert result["first_name"] == "Test"

    def test_category_creation_and_retrieval(
        self, test_session, database_service
    ):
        """Тест создания и получения категории"""
        # Создаем категорию
        category = Category(
            name="Test Category",
            description="Test Description",
            is_active=True,
        )

        test_session.add(category)
        test_session.commit()

        # Получаем категорию
        query = "SELECT * FROM categories WHERE name = :name"
        result = database_service.fetch_one(query, {"name": "Test Category"})

        assert result is not None
        assert result["name"] == "Test Category"
        assert result["description"] == "Test Description"
        assert result["is_active"]

    def test_product_creation_and_retrieval(
        self, test_session, database_service
    ):
        """Тест создания и получения товара"""
        # Создаем категорию
        category = Category(
            name="Test Category",
            description="Test Description",
            is_active=True,
        )
        test_session.add(category)
        test_session.commit()

        # Создаем товар
        product = Product(
            name="Test Product",
            description="Test Product Description",
            price=99.99,
            category_id=category.id,
            is_active=True,
        )

        test_session.add(product)
        test_session.commit()

        # Получаем товар
        query = "SELECT * FROM products WHERE name = :name"
        result = database_service.fetch_one(query, {"name": "Test Product"})

        assert result is not None
        assert result["name"] == "Test Product"
        assert result["price"] == 99.99
        assert result["category_id"] == category.id

    def test_complex_query_with_joins(self, test_session, database_service):
        """Тест сложного запроса с JOIN"""
        # Создаем категорию
        category = Category(
            name="Test Category",
            description="Test Description",
            is_active=True,
        )
        test_session.add(category)
        test_session.commit()

        # Создаем товары
        product1 = Product(
            name="Product 1",
            description="Description 1",
            price=10.99,
            category_id=category.id,
            is_active=True,
        )
        product2 = Product(
            name="Product 2",
            description="Description 2",
            price=20.99,
            category_id=category.id,
            is_active=True,
        )

        test_session.add_all([product1, product2])
        test_session.commit()

        # Выполняем сложный запрос
        query = """
            SELECT p.name, p.price, c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE c.name = :category_name
            ORDER BY p.price
        """

        results = database_service.fetch_all(
            query, {"category_name": "Test Category"}
        )

        assert len(results) == 2
        assert results[0]["name"] == "Product 1"
        assert results[0]["price"] == 10.99
        assert results[1]["name"] == "Product 2"
        assert results[1]["price"] == 20.99

    def test_transaction_rollback(self, test_session, database_service):
        """Тест отката транзакции"""
        # Начинаем транзакцию
        test_session.begin()

        try:
            # Создаем пользователя
            user = User(
                telegram_id=999999999,
                username="rollback_user",
                first_name="Rollback",
                last_name="Test",
            )

            test_session.add(user)
            test_session.commit()

            # Проверяем, что пользователь создан
            query = "SELECT * FROM users WHERE telegram_id = :telegram_id"
            result = database_service.fetch_one(
                query, {"telegram_id": 999999999}
            )
            assert result is not None

            # Откатываем транзакцию
            test_session.rollback()

            # Проверяем, что пользователь удален
            result = database_service.fetch_one(
                query, {"telegram_id": 999999999}
            )
            assert result is None

        except Exception:
            test_session.rollback()
            raise

    def test_bulk_operations(self, test_session, database_service):
        """Тест массовых операций"""
        # Создаем несколько пользователей
        users = [
            User(
                telegram_id=1001,
                username="user1",
                first_name="User",
                last_name="One",
            ),
            User(
                telegram_id=1002,
                username="user2",
                first_name="User",
                last_name="Two",
            ),
            User(
                telegram_id=1003,
                username="user3",
                first_name="User",
                last_name="Three",
            ),
        ]

        test_session.add_all(users)
        test_session.commit()

        # Получаем всех пользователей
        query = "SELECT * FROM users WHERE telegram_id >= :min_id ORDER BY telegram_id"
        results = database_service.fetch_all(query, {"min_id": 1001})

        assert len(results) == 3
        assert results[0]["telegram_id"] == 1001
        assert results[1]["telegram_id"] == 1002
        assert results[2]["telegram_id"] == 1003

    def test_database_constraints(self, test_session, database_service):
        """Тест ограничений базы данных"""
        # Пытаемся создать пользователя с дублирующимся telegram_id
        user1 = User(
            telegram_id=2001,
            username="user1",
            first_name="User",
            last_name="One",
        )

        user2 = User(
            telegram_id=2001,
            username="user2",
            first_name="User",
            last_name="Two",
        )  # Дублирующийся ID

        test_session.add(user1)
        test_session.commit()

        # Вторая попытка должна вызвать ошибку
        with pytest.raises(Exception):
            test_session.add(user2)
            test_session.commit()

    def test_database_performance(self, test_session, database_service):
        """Тест производительности базы данных"""
        import time

        # Создаем много записей
        start_time = time.time()

        for i in range(100):
            user = User(
                telegram_id=3000 + i,
                username=f"perf_user_{i}",
                first_name="Performance",
                last_name="Test",
            )
            test_session.add(user)

        test_session.commit()
        creation_time = time.time() - start_time

        # Тестируем время выполнения запроса
        start_time = time.time()
        query = "SELECT * FROM users WHERE telegram_id >= :min_id"
        results = database_service.fetch_all(query, {"min_id": 3000})
        query_time = time.time() - start_time

        assert len(results) == 100
        assert creation_time < 1.0  # Создание должно быть быстрым
        assert query_time < 0.1  # Запрос должен быть быстрым
