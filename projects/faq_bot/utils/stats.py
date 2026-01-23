"""
Модуль для работы со статистикой бота.
"""

import aiosqlite
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class StatsManager:
    """Менеджер статистики с асинхронным SQLite."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None

    async def init(self) -> None:
        """Инициализация базы данных."""
        self._connection = await aiosqlite.connect(self.db_path)
        await self._create_tables()
        logger.info("База данных статистики инициализирована")

    async def close(self) -> None:
        """Закрытие соединения с базой данных."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("Соединение с базой данных закрыто")

    async def _create_tables(self) -> None:
        """Создание таблиц базы данных."""
        await self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS faq_views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT NOT NULL,
                question TEXT NOT NULL,
                viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS search_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                query TEXT NOT NULL,
                results_count INTEGER DEFAULT 0,
                searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS support_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_faq_views_question ON faq_views(question);
            CREATE INDEX IF NOT EXISTS idx_search_queries_query ON search_queries(query);
            CREATE INDEX IF NOT EXISTS idx_faq_views_viewed_at ON faq_views(viewed_at);
            """
        )
        await self._connection.commit()

    async def track_user(
        self, user_id: int, username: Optional[str], first_name: Optional[str]
    ) -> None:
        """Отслеживание пользователя."""
        await self._connection.execute(
            """
            INSERT INTO users (user_id, username, first_name, last_seen)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_seen = excluded.last_seen
            """,
            (user_id, username, first_name, datetime.now()),
        )
        await self._connection.commit()

    async def track_faq_view(
        self, user_id: int, category: str, question: str
    ) -> None:
        """Отслеживание просмотра FAQ."""
        await self._connection.execute(
            """
            INSERT INTO faq_views (user_id, category, question, viewed_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, category, question, datetime.now()),
        )
        await self._connection.commit()

    async def track_search(
        self, user_id: int, query: str, results_count: int
    ) -> None:
        """Отслеживание поискового запроса."""
        await self._connection.execute(
            """
            INSERT INTO search_queries (user_id, query, results_count, searched_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, query, results_count, datetime.now()),
        )
        await self._connection.commit()

    async def track_support_request(
        self, user_id: int, username: Optional[str]
    ) -> None:
        """Отслеживание запроса в поддержку."""
        await self._connection.execute(
            """
            INSERT INTO support_requests (user_id, username, requested_at)
            VALUES (?, ?, ?)
            """,
            (user_id, username, datetime.now()),
        )
        await self._connection.commit()

    async def get_total_users(self) -> int:
        """Получение общего числа пользователей."""
        async with self._connection.execute(
            "SELECT COUNT(*) FROM users"
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_total_faq_views(self) -> int:
        """Получение общего числа просмотров FAQ."""
        async with self._connection.execute(
            "SELECT COUNT(*) FROM faq_views"
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_total_searches(self) -> int:
        """Получение общего числа поисковых запросов."""
        async with self._connection.execute(
            "SELECT COUNT(*) FROM search_queries"
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_total_support_requests(self) -> int:
        """Получение общего числа обращений в поддержку."""
        async with self._connection.execute(
            "SELECT COUNT(*) FROM support_requests"
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_top_questions(self, limit: int = 10) -> list[tuple[str, int]]:
        """Получение топ вопросов по просмотрам."""
        async with self._connection.execute(
            """
            SELECT question, COUNT(*) as count
            FROM faq_views
            GROUP BY question
            ORDER BY count DESC
            LIMIT ?
            """,
            (limit,),
        ) as cursor:
            return await cursor.fetchall()

    async def get_top_searches(self, limit: int = 10) -> list[tuple[str, int]]:
        """Получение топ поисковых запросов."""
        async with self._connection.execute(
            """
            SELECT query, COUNT(*) as count
            FROM search_queries
            GROUP BY query
            ORDER BY count DESC
            LIMIT ?
            """,
            (limit,),
        ) as cursor:
            return await cursor.fetchall()

    async def get_failed_searches(self, limit: int = 10) -> list[tuple[str, int]]:
        """Получение топ неудачных поисковых запросов."""
        async with self._connection.execute(
            """
            SELECT query, COUNT(*) as count
            FROM search_queries
            WHERE results_count = 0
            GROUP BY query
            ORDER BY count DESC
            LIMIT ?
            """,
            (limit,),
        ) as cursor:
            return await cursor.fetchall()

    async def get_users_today(self) -> int:
        """Получение числа активных пользователей за сегодня."""
        async with self._connection.execute(
            """
            SELECT COUNT(DISTINCT user_id)
            FROM users
            WHERE date(last_seen) = date('now')
            """
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0
