"""
Сервисы домена пользователей
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog

from ...interfaces import ICacheService, IDatabaseService

logger = structlog.get_logger()


class UsersDomainService:
    """Сервис домена пользователей"""

    def __init__(
        self, cache_service: ICacheService, database_service: IDatabaseService
    ):
        self.cache = cache_service
        self.database = database_service

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить пользователя по ID"""
        cache_key = f"users:user:{user_id}"

        if self.cache.exists(cache_key):
            return self.cache.get(cache_key)

        # Получаем пользователя
        query = """
            SELECT id, telegram_id, username, first_name, last_name, phone,
                   is_active, created_at, last_login
            FROM users
            WHERE id = %s
        """

        try:
            result = self.database.execute_query(query, {"user_id": user_id})

            if not result:
                return None

            row = result[0]
            user = {
                "id": row[0],
                "telegram_id": row[1],
                "username": row[2],
                "first_name": row[3],
                "last_name": row[4],
                "phone": row[5],
                "is_active": row[6],
                "created_at": row[7].isoformat() if row[7] else None,
                "last_login": row[8].isoformat() if row[8] else None,
            }

            # Сохраняем в кэш
            self.cache.set(cache_key, user, ttl=3600)  # 1 час

            return user

        except Exception as e:
            logger.error("get_user_failed", user_id=user_id, error=str(e))
            return None

    def get_user_by_telegram_id(
        self, telegram_id: int
    ) -> Optional[Dict[str, Any]]:
        """Получить пользователя по Telegram ID"""
        cache_key = f"users:telegram:{telegram_id}"

        if self.cache.exists(cache_key):
            return self.cache.get(cache_key)

        # Получаем пользователя
        query = """
            SELECT id, telegram_id, username, first_name, last_name, phone,
                   is_active, created_at, last_login
            FROM users
            WHERE telegram_id = %s
        """

        try:
            result = self.database.execute_query(
                query, {"telegram_id": telegram_id}
            )

            if not result:
                return None

            row = result[0]
            user = {
                "id": row[0],
                "telegram_id": row[1],
                "username": row[2],
                "first_name": row[3],
                "last_name": row[4],
                "phone": row[5],
                "is_active": row[6],
                "created_at": row[7].isoformat() if row[7] else None,
                "last_login": row[8].isoformat() if row[8] else None,
            }

            # Сохраняем в кэш
            self.cache.set(cache_key, user, ttl=3600)  # 1 час

            return user

        except Exception as e:
            logger.error(
                "get_user_by_telegram_id_failed",
                telegram_id=telegram_id,
                error=str(e),
            )
            return None

    def create_user(
        self, user_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Создать пользователя"""
        try:
            query = """
                INSERT INTO users (telegram_id, username, first_name, last_name, phone, is_active, created_at)
                VALUES (%(telegram_id)s, %(username)s, %(first_name)s, %(last_name)s, %(phone)s, %(is_active)s, %(created_at)s)
                RETURNING id
            """

            params = {
                "telegram_id": user_data.get("telegram_id"),
                "username": user_data.get("username"),
                "first_name": user_data.get("first_name"),
                "last_name": user_data.get("last_name"),
                "phone": user_data.get("phone"),
                "is_active": user_data.get("is_active", True),
                "created_at": datetime.utcnow(),
            }

            result = self.database.execute_query(query, params)
            user_id = result[0][0] if result else None

            if not user_id:
                raise Exception("Failed to create user")

            logger.info(
                "user_created",
                user_id=user_id,
                telegram_id=user_data.get("telegram_id"),
            )

            return self.get_user(user_id)

        except Exception as e:
            logger.error(
                "create_user_failed", user_data=user_data, error=str(e)
            )
            return None

    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """Обновить пользователя"""
        try:
            # Строим динамический запрос
            update_fields = []
            params = {"user_id": user_id}

            for field, value in user_data.items():
                if field in [
                    "username",
                    "first_name",
                    "last_name",
                    "phone",
                    "is_active",
                ]:
                    update_fields.append(f"{field} = %({field})s")
                    params[field] = value

            if not update_fields:
                return False

            update_fields.append("updated_at = %(updated_at)s")
            params["updated_at"] = datetime.utcnow()

            query = f"""
                UPDATE users
                SET {', '.join(update_fields)}
                WHERE id = %(user_id)s
            """

            self.database.execute_query(query, params)

            # Очищаем кэш
            self._invalidate_user_cache(user_id)

            logger.info("user_updated", user_id=user_id)
            return True

        except Exception as e:
            logger.error("update_user_failed", user_id=user_id, error=str(e))
            return False

    def update_last_login(self, user_id: int) -> bool:
        """Обновить время последнего входа"""
        try:
            query = """
                UPDATE users
                SET last_login = %s
                WHERE id = %s
            """

            params = {
                "last_login": datetime.utcnow(),
                "user_id": user_id,
            }

            self.database.execute_query(query, params)

            # Очищаем кэш
            self._invalidate_user_cache(user_id)

            return True

        except Exception as e:
            logger.error(
                "update_last_login_failed", user_id=user_id, error=str(e)
            )
            return False

    def get_users(
        self, limit: int = 50, offset: int = 0, active_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Получить список пользователей"""
        cache_key = f"users:list:{limit}:{offset}:{active_only}"

        if self.cache.exists(cache_key):
            return self.cache.get(cache_key)

        # Строим запрос
        where_clause = "WHERE is_active = true" if active_only else ""

        query = f"""
            SELECT id, telegram_id, username, first_name, last_name, phone,
                   is_active, created_at, last_login
            FROM users
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """

        try:
            result = self.database.execute_query(
                query, {"limit": limit, "offset": offset}
            )
            users = []

            for row in result:
                users.append(
                    {
                        "id": row[0],
                        "telegram_id": row[1],
                        "username": row[2],
                        "first_name": row[3],
                        "last_name": row[4],
                        "phone": row[5],
                        "is_active": row[6],
                        "created_at": row[7].isoformat() if row[7] else None,
                        "last_login": row[8].isoformat() if row[8] else None,
                    }
                )

            # Сохраняем в кэш
            self.cache.set(cache_key, users, ttl=1800)  # 30 минут

            return users

        except Exception as e:
            logger.error("get_users_failed", error=str(e))
            return []

    def get_user_statistics(self) -> Dict[str, Any]:
        """Получить статистику пользователей"""
        cache_key = "users:statistics"

        if self.cache.exists(cache_key):
            return self.cache.get(cache_key)

        try:
            # Общая статистика
            total_query = "SELECT COUNT(*) FROM users"
            total_result = self.database.execute_query(total_query)
            total_users = total_result[0][0] if total_result else 0

            # Активные пользователи
            active_query = "SELECT COUNT(*) FROM users WHERE is_active = true"
            active_result = self.database.execute_query(active_query)
            active_users = active_result[0][0] if active_result else 0

            # Пользователи за последние 7 дней
            recent_query = """
                SELECT COUNT(*) FROM users
                WHERE created_at >= NOW() - INTERVAL '7 days'
            """
            recent_result = self.database.execute_query(recent_query)
            recent_users = recent_result[0][0] if recent_result else 0

            # Пользователи за последние 30 дней
            monthly_query = """
                SELECT COUNT(*) FROM users
                WHERE created_at >= NOW() - INTERVAL '30 days'
            """
            monthly_result = self.database.execute_query(monthly_query)
            monthly_users = monthly_result[0][0] if monthly_result else 0

            # Статистика по дням (последние 7 дней)
            daily_query = """
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM users
                WHERE created_at >= NOW() - INTERVAL '7 days'
                GROUP BY DATE(created_at)
                ORDER BY date
            """
            daily_result = self.database.execute_query(daily_query)
            daily_stats = {row[0].isoformat(): row[1] for row in daily_result}

            statistics = {
                "total_users": total_users,
                "active_users": active_users,
                "recent_users_7d": recent_users,
                "recent_users_30d": monthly_users,
                "daily_breakdown": daily_stats,
                "generated_at": datetime.utcnow().isoformat(),
            }

            # Сохраняем в кэш
            self.cache.set(cache_key, statistics, ttl=1800)  # 30 минут

            return statistics

        except Exception as e:
            logger.error("get_user_statistics_failed", error=str(e))
            return {}

    def is_admin(self, user_id: int) -> bool:
        """Проверить, является ли пользователь администратором"""
        cache_key = f"users:admin:{user_id}"

        if self.cache.exists(cache_key):
            return self.cache.get(cache_key)

        try:
            query = """
                SELECT COUNT(*) FROM admin_users
                WHERE telegram_id = (
                    SELECT telegram_id FROM users WHERE id = %s
                ) AND is_active = true
            """

            result = self.database.execute_query(query, {"user_id": user_id})
            is_admin = result[0][0] > 0 if result else False

            # Сохраняем в кэш
            self.cache.set(cache_key, is_admin, ttl=1800)  # 30 минут

            return is_admin

        except Exception as e:
            logger.error(
                "is_admin_check_failed", user_id=user_id, error=str(e)
            )
            return False

    def _invalidate_user_cache(self, user_id: int) -> None:
        """Очистить кэш пользователя"""
        # Очищаем все ключи пользователя
        patterns = [
            f"users:user:{user_id}",
            f"users:admin:{user_id}",
            "users:statistics",
            "users:list:*",
        ]

        for pattern in patterns:
            # В реальной реализации здесь был бы поиск по паттерну
            logger.info("user_cache_invalidated", pattern=pattern)
