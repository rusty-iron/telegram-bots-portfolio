"""
Задачи для отправки уведомлений
"""

from __future__ import annotations

import structlog
from celery import Task

from ..celery_app import celery_app

logger = structlog.get_logger()


class NotificationTask(Task):
    """Базовый класс для задач уведомлений"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Обработка ошибок отправки уведомлений"""
        logger.error(
            "notification_task_failed",
            task_id=task_id,
            task_name=self.name,
            error=str(exc),
            args=args,
            kwargs=kwargs,
        )


@celery_app.task(
    bind=True,
    base=NotificationTask,
    name="meatbot.app.tasks.notifications.send_order_notification",
    queue="normal",
    max_retries=3,
    default_retry_delay=30,
)
def send_order_notification(
        self, user_id: int, order_id: int, message: str) -> dict[str, str]:
    """Отправка уведомления о заказе пользователю"""
    logger.info(
        "sending_order_notification",
        user_id=user_id,
        order_id=order_id,
        task_id=self.request.id,
    )

    try:
        # Здесь будет логика отправки уведомления через Telegram Bot API
        # Пока что просто логируем

        logger.info(
            "order_notification_sent",
            user_id=user_id,
            order_id=order_id,
            message=message,
            task_id=self.request.id,
        )

        return {
            "status": "success",
            "message": f"Notification sent to user {user_id} about order {order_id}",
            "user_id": user_id,
            "order_id": order_id,
        }

    except Exception as exc:
        logger.error(
            "order_notification_failed",
            user_id=user_id,
            order_id=order_id,
            error=str(exc),
            task_id=self.request.id,
        )

        if self.request.retries < self.max_retries:
            logger.info(
                "retrying_notification",
                user_id=user_id,
                order_id=order_id,
                retry_count=self.request.retries + 1,
            )
            raise self.retry(countdown=30 * (2**self.request.retries))

        return {
            "status": "failed",
            "message": f"Failed to send notification to user {user_id}",
            "user_id": user_id,
            "order_id": order_id,
            "error": str(exc),
        }


@celery_app.task(
    bind=True,
    base=NotificationTask,
    name="meatbot.app.tasks.notifications.send_admin_notification",
    queue="normal",
    max_retries=2,
    default_retry_delay=60,
)
def send_admin_notification(
    self, admin_id: int, message: str, order_id: int = None
) -> dict[str, str]:
    """Отправка уведомления администратору"""
    logger.info(
        "sending_admin_notification",
        admin_id=admin_id,
        order_id=order_id,
        task_id=self.request.id,
    )

    try:
        # Здесь будет логика отправки уведомления администратору
        # Пока что просто логируем

        logger.info(
            "admin_notification_sent",
            admin_id=admin_id,
            order_id=order_id,
            message=message,
            task_id=self.request.id,
        )

        return {
            "status": "success",
            "message": f"Admin notification sent to {admin_id}",
            "admin_id": admin_id,
            "order_id": order_id,
        }

    except Exception as exc:
        logger.error(
            "admin_notification_failed",
            admin_id=admin_id,
            order_id=order_id,
            error=str(exc),
            task_id=self.request.id,
        )

        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60)

        return {
            "status": "failed",
            "message": f"Failed to send admin notification to {admin_id}",
            "admin_id": admin_id,
            "error": str(exc),
        }


@celery_app.task(
    bind=True,
    base=NotificationTask,
    name="meatbot.app.tasks.notifications.send_bulk_notification",
    queue="normal",
    max_retries=1,
    default_retry_delay=120,
)
def send_bulk_notification(
        self, user_ids: list[int], message: str) -> dict[str, str]:
    """Массовая отправка уведомлений"""
    logger.info(
        "sending_bulk_notification",
        user_count=len(user_ids),
        task_id=self.request.id,
    )

    try:
        # Здесь будет логика массовой отправки уведомлений
        # С соблюдением rate limits Telegram API (30 сообщений/сек)
        # Пока что просто логируем

        logger.info(
            "bulk_notification_sent",
            user_count=len(user_ids),
            message=message,
            task_id=self.request.id,
        )

        return {
            "status": "success",
            "message": f"Bulk notification sent to {len(user_ids)} users",
            "user_count": len(user_ids),
        }

    except Exception as exc:
        logger.error(
            "bulk_notification_failed",
            user_count=len(user_ids),
            error=str(exc),
            task_id=self.request.id,
        )

        return {
            "status": "failed",
            "message": f"Failed to send bulk notification to {len(user_ids)} users",
            "user_count": len(user_ids),
            "error": str(exc),
        }
