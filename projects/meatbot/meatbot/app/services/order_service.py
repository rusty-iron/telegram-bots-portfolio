"""
Сервис для работы с заказами
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional

import structlog

from ..database import (
    CartItem,
    Order,
    OrderItem,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    User,
    get_db,
)
from ..utils.order_number import generate_order_number

logger = structlog.get_logger()


class OrderService:
    """Сервис для работы с заказами"""

    def create_order_from_cart(
        self,
        user_id: int,
        delivery_data: Dict[str, Any],
        payment_method: str,
        payment_status: str = "pending",
    ) -> Optional[Dict[str, Any]]:
        """
        Создает заказ из корзины пользователя

        Args:
            user_id: ID пользователя
            delivery_data: Данные доставки (phone, address, notes)
            payment_method: Способ оплаты (cash/transfer)
            payment_status: Статус оплаты (pending/paid)

        Returns:
            Dict[str, Any]: Данные созданного заказа или None при ошибке
        """
        try:
            with get_db() as db:
                # Получаем пользователя
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    logger.error(
                        "create_order_user_not_found", user_id=user_id
                    )
                    return None

                # Получаем товары из корзины
                cart_items = (
                    db.query(CartItem)
                    .filter(CartItem.user_id == user.id)
                    .all()
                )

                if not cart_items:
                    logger.warning("create_order_empty_cart", user_id=user_id)
                    return None

                # Проверяем доступность товаров
                for cart_item in cart_items:
                    product = cart_item.product
                    if not product.is_available:
                        logger.warning(
                            "create_order_product_unavailable",
                            user_id=user_id,
                            product_id=product.id,
                            product_name=product.name,
                        )
                        return None

                # Генерируем номер заказа
                order_number = generate_order_number()

                # Рассчитываем суммы
                subtotal = sum(
                    item.price_at_add * item.quantity for item in cart_items
                )
                delivery_cost = Decimal("0")  # Пока бесплатная доставка
                total_amount = subtotal + delivery_cost

                # Создаем заказ
                order = Order(
                    user_id=user.id,
                    order_number=order_number,
                    status=OrderStatus.PENDING,
                    payment_status=PaymentStatus(payment_status),
                    payment_method=PaymentMethod(payment_method),
                    subtotal=subtotal,
                    delivery_cost=delivery_cost,
                    total_amount=total_amount,
                    delivery_address=delivery_data["address"],
                    delivery_phone=delivery_data["phone"],
                    delivery_notes=delivery_data.get("notes", ""),
                )

                db.add(order)
                db.flush()  # Получаем ID заказа

                # Создаем элементы заказа
                for cart_item in cart_items:
                    product = cart_item.product

                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        product_name=product.name,
                        product_unit=product.unit,
                        product_price=cart_item.price_at_add,
                        quantity=cart_item.quantity,
                        total_price=cart_item.price_at_add
                        * cart_item.quantity,
                    )
                    db.add(order_item)

                # Очищаем корзину
                for cart_item in cart_items:
                    db.delete(cart_item)

                # Сохраняем изменения
                db.commit()
                db.refresh(order)

                # Создаем копию данных заказа для возврата
                order_data = {
                    "id": order.id,
                    "order_number": order.order_number,
                    "total_amount": order.total_amount,
                    "status": order.status.value,
                    "payment_status": order.payment_status.value,
                    "payment_method": order.payment_method.value,
                    "delivery_address": order.delivery_address,
                    "delivery_phone": order.delivery_phone,
                    "delivery_notes": order.delivery_notes,
                }

                logger.info(
                    "order_created_successfully",
                    user_id=user_id,
                    order_id=order.id,
                    order_number=order_number,
                    total_amount=float(total_amount),
                    items_count=len(cart_items),
                )

                return order_data

        except Exception as e:
            logger.error(
                "create_order_failed",
                user_id=user_id,
                error=str(e),
                delivery_data=delivery_data,
                payment_method=payment_method,
            )
            return None

    def get_user_order(
        self, user_id: int, order_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Получает заказ пользователя по ID

        Args:
            user_id: ID пользователя
            order_id: ID заказа

        Returns:
            Dict[str, Any]: Данные заказа в виде словаря или None
        """
        try:
            with get_db() as db:
                from sqlalchemy.orm import joinedload

                order = (
                    db.query(Order)
                    .options(joinedload(Order.order_items))
                    .filter(
                        Order.id == order_id,
                        Order.user_id == user_id,
                    )
                    .first()
                )

                if not order:
                    return None

                # Преобразуем в словарь
                order_dict = {
                    "id": order.id,
                    "order_number": order.order_number,
                    "status": order.status,
                    "payment_status": order.payment_status,
                    "payment_method": order.payment_method,
                    "total_amount": order.total_amount,
                    "subtotal": order.subtotal,
                    "delivery_cost": order.delivery_cost,
                    "delivery_address": order.delivery_address,
                    "delivery_phone": order.delivery_phone,
                    "delivery_notes": order.delivery_notes,
                    "items": [
                        {
                            "product_name": item.product_name,
                            "product_unit": item.product_unit,
                            "product_price": item.product_price,
                            "quantity": item.quantity,
                            "total_price": item.total_price,
                        }
                        for item in order.order_items
                    ],
                }

                return order_dict
        except Exception as e:
            logger.error(
                "get_user_order_failed",
                user_id=user_id,
                order_id=order_id,
                error=str(e),
            )
            return None

    def get_user_orders(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0,
        active_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Получает список заказов пользователя

        Args:
            user_id: ID пользователя
            limit: Максимальное количество заказов
            offset: Смещение для пагинации
            active_only: Если True, возвращает только активные заказы (не delivered и не cancelled)

        Returns:
            List[Dict[str, Any]]: Список заказов в виде словарей
        """
        try:
            with get_db() as db:
                from sqlalchemy.orm import joinedload

                query = (
                    db.query(Order)
                    .options(joinedload(Order.order_items))
                    .filter(Order.user_id == user_id)
                )

                # Фильтр для активных заказов (исключаем delivered и cancelled)
                if active_only:
                    query = query.filter(
                        Order.status.notin_(
                            [OrderStatus.DELIVERED, OrderStatus.CANCELLED]
                        )
                    )

                orders = (
                    query.order_by(Order.id.desc())
                    .offset(offset)
                    .limit(limit)
                    .all()
                )

                # Преобразуем ORM объекты в словари
                orders_data = []
                for order in orders:
                    order_dict = {
                        "id": order.id,
                        "order_number": order.order_number,
                        "status": order.status,
                        "payment_status": order.payment_status,
                        "payment_method": order.payment_method,
                        "total_amount": order.total_amount,
                        "subtotal": order.subtotal,
                        "delivery_cost": order.delivery_cost,
                        "delivery_address": order.delivery_address,
                        "delivery_phone": order.delivery_phone,
                        "delivery_notes": order.delivery_notes,
                        "items": [
                            {
                                "product_name": item.product_name,
                                "product_unit": item.product_unit,
                                "product_price": item.product_price,
                                "quantity": item.quantity,
                                "total_price": item.total_price,
                            }
                            for item in order.order_items
                        ],
                    }
                    orders_data.append(order_dict)

                logger.info(
                    "get_user_orders_success",
                    user_id=user_id,
                    orders_count=len(orders_data),
                    order_ids=[o["id"] for o in orders_data],
                )

                return orders_data
        except Exception as e:
            logger.error(
                "get_user_orders_failed",
                user_id=user_id,
                limit=limit,
                offset=offset,
                error=str(e),
            )
            return []

    def get_user_orders_history(
        self, user_id: int, limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Получает историю заказов пользователя (только delivered и cancelled)

        Args:
            user_id: ID пользователя
            limit: Максимальное количество заказов
            offset: Смещение для пагинации

        Returns:
            List[Dict[str, Any]]: Список заказов в виде словарей
        """
        try:
            with get_db() as db:
                from sqlalchemy.orm import joinedload

                orders = (
                    db.query(Order)
                    .options(joinedload(Order.order_items))
                    .filter(Order.user_id == user_id)
                    .filter(
                        Order.status.in_(
                            [OrderStatus.DELIVERED, OrderStatus.CANCELLED]
                        )
                    )
                    .order_by(Order.id.desc())
                    .offset(offset)
                    .limit(limit)
                    .all()
                )

                # Преобразуем ORM объекты в словари
                orders_data = []
                for order in orders:
                    order_dict = {
                        "id": order.id,
                        "order_number": order.order_number,
                        "status": order.status,
                        "payment_status": order.payment_status,
                        "payment_method": order.payment_method,
                        "total_amount": order.total_amount,
                        "subtotal": order.subtotal,
                        "delivery_cost": order.delivery_cost,
                        "delivery_address": order.delivery_address,
                        "delivery_phone": order.delivery_phone,
                        "delivery_notes": order.delivery_notes,
                        "items": [
                            {
                                "product_name": item.product_name,
                                "product_unit": item.product_unit,
                                "product_price": item.product_price,
                                "quantity": item.quantity,
                                "total_price": item.total_price,
                            }
                            for item in order.order_items
                        ],
                    }
                    orders_data.append(order_dict)

                logger.info(
                    "get_user_orders_history_success",
                    user_id=user_id,
                    orders_count=len(orders_data),
                )

                return orders_data
        except Exception as e:
            logger.error(
                "get_user_orders_history_failed",
                user_id=user_id,
                limit=limit,
                offset=offset,
                error=str(e),
            )
            return []

    def cancel_order(self, user_id: int, order_id: int) -> bool:
        """
        Отменяет заказ пользователя

        Args:
            user_id: ID пользователя
            order_id: ID заказа

        Returns:
            bool: True если заказ отменен, False иначе
        """
        try:
            with get_db() as db:
                order = (
                    db.query(Order)
                    .filter(
                        Order.id == order_id,
                        Order.user_id == user_id,
                    )
                    .first()
                )

                if not order:
                    logger.warning(
                        "cancel_order_not_found",
                        user_id=user_id,
                        order_id=order_id,
                    )
                    return False

                # Проверяем, можно ли отменить заказ
                if order.status in [
                    OrderStatus.DELIVERED,
                    OrderStatus.CANCELLED,
                ]:
                    logger.warning(
                        "cancel_order_invalid_status",
                        user_id=user_id,
                        order_id=order_id,
                        current_status=order.status.value,
                    )
                    return False

                # Отменяем заказ
                order.status = OrderStatus.CANCELLED
                order.payment_status = PaymentStatus.REFUNDED

                db.commit()

                logger.info(
                    "order_cancelled",
                    user_id=user_id,
                    order_id=order_id,
                    order_number=order.order_number,
                )

                return True

        except Exception as e:
            logger.error(
                "cancel_order_failed",
                user_id=user_id,
                order_id=order_id,
                error=str(e),
            )
            return False

    def get_orders_by_status(
        self, status: OrderStatus, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Получает заказы по статусу (для администраторов)

        Args:
            status: Статус заказа
            limit: Максимальное количество заказов
            offset: Смещение для пагинации

        Returns:
            List[Dict[str, Any]]: Список заказов в виде словарей
        """
        try:
            with get_db() as db:
                from sqlalchemy.orm import joinedload

                orders = (
                    db.query(Order)
                    .options(
                        joinedload(Order.order_items), joinedload(Order.user)
                    )
                    .filter(Order.status == status)
                    .order_by(Order.id.desc())
                    .offset(offset)
                    .limit(limit)
                    .all()
                )

                # Преобразуем ORM объекты в словари
                orders_data = []
                for order in orders:
                    order_dict = {
                        "id": order.id,
                        "order_number": order.order_number,
                        "status": order.status,
                        "payment_status": order.payment_status,
                        "payment_method": order.payment_method,
                        "total_amount": order.total_amount,
                        "subtotal": order.subtotal,
                        "delivery_cost": order.delivery_cost,
                        "delivery_address": order.delivery_address,
                        "delivery_phone": order.delivery_phone,
                        "delivery_notes": order.delivery_notes,
                        "user": {
                            "id": order.user.id,
                            "first_name": order.user.first_name,
                            "last_name": order.user.last_name,
                        },
                        "items": [
                            {
                                "product_name": item.product_name,
                                "product_unit": item.product_unit,
                                "product_price": item.product_price,
                                "quantity": item.quantity,
                                "total_price": item.total_price,
                            }
                            for item in order.order_items
                        ],
                    }
                    orders_data.append(order_dict)

                return orders_data
        except Exception as e:
            logger.error(
                "get_orders_by_status_failed",
                status=status.value,
                limit=limit,
                offset=offset,
                error=str(e),
            )
            return []

    def update_order_status(
        self, order_id: int, new_status: OrderStatus
    ) -> bool:
        """
        Обновляет статус заказа (для администраторов)

        Args:
            order_id: ID заказа
            new_status: Новый статус

        Returns:
            bool: True если статус обновлен, False иначе
        """
        try:
            with get_db() as db:
                order = db.query(Order).filter(Order.id == order_id).first()

                if not order:
                    logger.warning(
                        "update_order_status_not_found", order_id=order_id
                    )
                    return False

                old_status = order.status
                order.status = new_status

                # Обновляем статус оплаты при доставке
                if new_status == OrderStatus.DELIVERED:
                    order.payment_status = PaymentStatus.PAID

                db.commit()

                logger.info(
                    "order_status_updated",
                    order_id=order_id,
                    order_number=order.order_number,
                    old_status=old_status.value,
                    new_status=new_status.value,
                )

                return True

        except Exception as e:
            logger.error(
                "update_order_status_failed",
                order_id=order_id,
                new_status=new_status.value,
                error=str(e),
            )
            return False

    def get_order_statistics(self) -> Dict[str, Any]:
        """
        Получает статистику заказов

        Returns:
            Dict[str, Any]: Статистика заказов
        """
        try:
            with get_db() as db:
                # Общее количество заказов
                total_orders = db.query(Order).count()

                # Заказы по статусам
                status_counts = {}
                for status in OrderStatus:
                    count = (
                        db.query(Order).filter(Order.status == status).count()
                    )
                    status_counts[status.value] = count

                # Общая сумма заказов
                total_amount_result = (
                    db.query(Order.total_amount)
                    .filter(Order.status != OrderStatus.CANCELLED)
                    .all()
                )
                total_amount = sum(
                    float(amount[0]) for amount in total_amount_result
                )

                # Средний чек
                avg_order_value = (
                    total_amount / total_orders if total_orders > 0 else 0
                )

                statistics = {
                    "total_orders": total_orders,
                    "status_breakdown": status_counts,
                    "total_amount": total_amount,
                    "average_order_value": avg_order_value,
                }

                return statistics

        except Exception as e:
            logger.error("get_order_statistics_failed", error=str(e))
            return {}
