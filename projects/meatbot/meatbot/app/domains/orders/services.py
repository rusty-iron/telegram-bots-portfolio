"""
Сервисы домена заказов
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog

from ...interfaces import ICacheService, IDatabaseService

logger = structlog.get_logger()


class OrdersDomainService:
    """Сервис домена заказов"""

    def __init__(
        self, cache_service: ICacheService, database_service: IDatabaseService
    ):
        self.cache = cache_service
        self.database = database_service

    def create_order(
        self, user_id: int, order_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Создать заказ"""
        try:
            # Начинаем транзакцию
            session = self.database.get_connection()

            # Создаем заказ
            order_query = """
                INSERT INTO orders (user_id, total_amount, status, notes, created_at)
                VALUES (%(user_id)s, %(total_amount)s, %(status)s, %(notes)s, %(created_at)s)
                RETURNING id
            """

            order_params = {
                "user_id": user_id,
                "total_amount": order_data.get("total_amount", 0.0),
                "status": order_data.get("status", "pending"),
                "notes": order_data.get("notes", ""),
                "created_at": datetime.utcnow(),
            }

            result = self.database.execute_query(order_query, order_params)
            order_id = result[0][0] if result else None

            if not order_id:
                raise Exception("Failed to create order")

            # Создаем элементы заказа
            items = order_data.get("items", [])
            for item in items:
                item_query = """
                    INSERT INTO order_items (order_id, product_id, quantity, price, notes)
                    VALUES (%(order_id)s, %(product_id)s, %(quantity)s, %(price)s, %(notes)s)
                """

                item_params = {
                    "order_id": order_id,
                    "product_id": item.get("product_id"),
                    "quantity": item.get("quantity", 1),
                    "price": item.get("price", 0.0),
                    "notes": item.get("notes", ""),
                }

                self.database.execute_query(item_query, item_params)

            # Коммитим транзакцию
            session.commit()

            # Очищаем кэш пользователя
            self._invalidate_user_cache(user_id)

            logger.info("order_created", order_id=order_id, user_id=user_id)

            return self.get_order(order_id)

        except Exception as e:
            logger.error("create_order_failed", user_id=user_id, error=str(e))
            return None

    def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Получить заказ по ID"""
        cache_key = f"orders:order:{order_id}"

        if self.cache.exists(cache_key):
            return self.cache.get(cache_key)

        # Получаем заказ
        order_query = """
            SELECT o.id, o.user_id, o.total_amount, o.status, o.notes, o.created_at, o.updated_at,
                   u.first_name, u.last_name, u.phone
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
            WHERE o.id = %s
        """

        try:
            result = self.database.execute_query(
                order_query, {"order_id": order_id}
            )

            if not result:
                return None

            row = result[0]
            order = {
                "id": row[0],
                "user_id": row[1],
                "total_amount": float(row[2]) if row[2] else 0.0,
                "status": row[3],
                "notes": row[4],
                "created_at": row[5].isoformat() if row[5] else None,
                "updated_at": row[6].isoformat() if row[6] else None,
                "user_name": f"{row[7] or ''} {row[8] or ''}".strip(),
                "user_phone": row[9],
            }

            # Получаем элементы заказа
            items_query = """
                SELECT oi.id, oi.product_id, oi.quantity, oi.price, oi.notes,
                       p.name as product_name
                FROM order_items oi
                LEFT JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = %s
                ORDER BY oi.id
            """

            items_result = self.database.execute_query(
                items_query, {"order_id": order_id}
            )
            items = []

            for item_row in items_result:
                items.append(
                    {
                        "id": item_row[0],
                        "product_id": item_row[1],
                        "quantity": item_row[2],
                        "price": float(item_row[3]) if item_row[3] else 0.0,
                        "notes": item_row[4],
                        "product_name": item_row[5],
                    }
                )

            order["items"] = items

            # Сохраняем в кэш
            self.cache.set(cache_key, order, ttl=1800)  # 30 минут

            return order

        except Exception as e:
            logger.error("get_order_failed", order_id=order_id, error=str(e))
            return None

    def get_user_orders(
        self, user_id: int, limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Получить заказы пользователя"""
        cache_key = f"orders:user:{user_id}:{limit}:{offset}"

        if self.cache.exists(cache_key):
            return self.cache.get(cache_key)

        # Получаем заказы
        query = """
            SELECT o.id, o.user_id, o.total_amount, o.status, o.notes, o.created_at, o.updated_at
            FROM orders o
            WHERE o.user_id = %s
            ORDER BY o.created_at DESC
            LIMIT %s OFFSET %s
        """

        try:
            result = self.database.execute_query(
                query, {"user_id": user_id, "limit": limit, "offset": offset}
            )
            orders = []

            for row in result:
                orders.append(
                    {
                        "id": row[0],
                        "user_id": row[1],
                        "total_amount": float(row[2]) if row[2] else 0.0,
                        "status": row[3],
                        "notes": row[4],
                        "created_at": row[5].isoformat() if row[5] else None,
                        "updated_at": row[6].isoformat() if row[6] else None,
                    }
                )

            # Сохраняем в кэш
            self.cache.set(cache_key, orders, ttl=900)  # 15 минут

            return orders

        except Exception as e:
            logger.error(
                "get_user_orders_failed", user_id=user_id, error=str(e)
            )
            return []

    def update_order_status(self, order_id: int, status: str) -> bool:
        """Обновить статус заказа"""
        try:
            query = """
                UPDATE orders
                SET status = %s, updated_at = %s
                WHERE id = %s
            """

            params = {
                "status": status,
                "updated_at": datetime.utcnow(),
                "order_id": order_id,
            }

            self.database.execute_query(query, params)

            # Очищаем кэш
            self._invalidate_order_cache(order_id)

            logger.info(
                "order_status_updated", order_id=order_id, status=status
            )
            return True

        except Exception as e:
            logger.error(
                "update_order_status_failed",
                order_id=order_id,
                status=status,
                error=str(e),
            )
            return False

    def get_orders_by_status(
        self, status: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Получить заказы по статусу"""
        cache_key = f"orders:status:{status}:{limit}:{offset}"

        if self.cache.exists(cache_key):
            return self.cache.get(cache_key)

        # Получаем заказы
        query = """
            SELECT o.id, o.user_id, o.total_amount, o.status, o.notes, o.created_at, o.updated_at,
                   u.first_name, u.last_name, u.phone
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
            WHERE o.status = %s
            ORDER BY o.created_at DESC
            LIMIT %s OFFSET %s
        """

        try:
            result = self.database.execute_query(
                query, {"status": status, "limit": limit, "offset": offset}
            )
            orders = []

            for row in result:
                orders.append(
                    {
                        "id": row[0],
                        "user_id": row[1],
                        "total_amount": float(row[2]) if row[2] else 0.0,
                        "status": row[3],
                        "notes": row[4],
                        "created_at": row[5].isoformat() if row[5] else None,
                        "updated_at": row[6].isoformat() if row[6] else None,
                        "user_name": f"{row[7] or ''} {row[8] or ''}".strip(),
                        "user_phone": row[9],
                    }
                )

            # Сохраняем в кэш
            self.cache.set(cache_key, orders, ttl=600)  # 10 минут

            return orders

        except Exception as e:
            logger.error(
                "get_orders_by_status_failed", status=status, error=str(e)
            )
            return []

    def get_order_statistics(self) -> Dict[str, Any]:
        """Получить статистику заказов"""
        cache_key = "orders:statistics"

        if self.cache.exists(cache_key):
            return self.cache.get(cache_key)

        try:
            # Общая статистика
            total_query = "SELECT COUNT(*) FROM orders"
            total_result = self.database.execute_query(total_query)
            total_orders = total_result[0][0] if total_result else 0

            # Статистика по статусам
            status_query = """
                SELECT status, COUNT(*) as count
                FROM orders
                GROUP BY status
            """
            status_result = self.database.execute_query(status_query)
            status_stats = {row[0]: row[1] for row in status_result}

            # Статистика по дням (последние 7 дней)
            daily_query = """
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM orders
                WHERE created_at >= NOW() - INTERVAL '7 days'
                GROUP BY DATE(created_at)
                ORDER BY date
            """
            daily_result = self.database.execute_query(daily_query)
            daily_stats = {row[0].isoformat(): row[1] for row in daily_result}

            # Общая сумма заказов
            total_amount_query = "SELECT SUM(total_amount) FROM orders WHERE status != 'cancelled'"
            total_amount_result = self.database.execute_query(
                total_amount_query
            )
            total_amount = (
                float(total_amount_result[0][0])
                if total_amount_result and total_amount_result[0][0]
                else 0.0
            )

            statistics = {
                "total_orders": total_orders,
                "status_breakdown": status_stats,
                "daily_breakdown": daily_stats,
                "total_amount": total_amount,
                "generated_at": datetime.utcnow().isoformat(),
            }

            # Сохраняем в кэш
            self.cache.set(cache_key, statistics, ttl=1800)  # 30 минут

            return statistics

        except Exception as e:
            logger.error("get_order_statistics_failed", error=str(e))
            return {}

    def _invalidate_order_cache(self, order_id: int) -> None:
        """Очистить кэш заказа"""
        cache_key = f"orders:order:{order_id}"
        self.cache.delete(cache_key)

        # Очищаем статистику
        self.cache.delete("orders:statistics")

    def _invalidate_user_cache(self, user_id: int) -> None:
        """Очистить кэш пользователя"""
        # Очищаем все ключи пользователя
        patterns = [
            f"orders:user:{user_id}:*",
            "orders:statistics",
        ]

        for pattern in patterns:
            # В реальной реализации здесь был бы поиск по паттерну
            logger.info("user_cache_invalidated", pattern=pattern)
