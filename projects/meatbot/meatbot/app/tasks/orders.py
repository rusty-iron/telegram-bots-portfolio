"""
Задачи для обработки заказов
"""

from __future__ import annotations

import structlog
from celery import Task

from ..celery_app import celery_app

logger = structlog.get_logger()


class OrderTask(Task):
    """Базовый класс для задач обработки заказов"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Обработка ошибок выполнения задач"""
        logger.error(
            "order_task_failed",
            task_id=task_id,
            task_name=self.name,
            error=str(exc),
            args=args,
            kwargs=kwargs,
        )


@celery_app.task(
    bind=True,
    base=OrderTask,
    name="meatbot.app.tasks.orders.process_order",
    queue="high",
    max_retries=3,
    default_retry_delay=60,
)
def process_order(self, order_id: int) -> dict[str, str]:
    """Обработка заказа"""
    logger.info("processing_order", order_id=order_id, task_id=self.request.id)

    try:
        # Здесь будет логика обработки заказа
        # Пока что просто логируем

        logger.info(
            "order_processed_successfully",
            order_id=order_id,
            task_id=self.request.id,
        )

        return {
            "status": "success",
            "message": f"Order {order_id} processed successfully",
            "order_id": order_id,
        }

    except Exception as exc:
        logger.error(
            "order_processing_failed",
            order_id=order_id,
            error=str(exc),
            task_id=self.request.id,
        )

        # Retry логика
        if self.request.retries < self.max_retries:
            logger.info(
                "retrying_order_processing",
                order_id=order_id,
                retry_count=self.request.retries + 1,
                max_retries=self.max_retries,
            )
            raise self.retry(countdown=60 * (2**self.request.retries))

        return {
            "status": "failed",
            "message": f"Order {order_id} processing failed after {
                self.max_retries} retries",
            "order_id": order_id,
            "error": str(exc),
        }


@celery_app.task(
    bind=True,
    base=OrderTask,
    name="meatbot.app.tasks.orders.update_order_status",
    queue="high",
    max_retries=2,
    default_retry_delay=30,
)
def update_order_status(self, order_id: int,
                        new_status: str) -> dict[str, str]:
    """Обновление статуса заказа"""
    logger.info(
        "updating_order_status",
        order_id=order_id,
        new_status=new_status,
        task_id=self.request.id,
    )

    try:
        # Здесь будет логика обновления статуса в БД
        # Пока что просто логируем

        logger.info(
            "order_status_updated",
            order_id=order_id,
            new_status=new_status,
            task_id=self.request.id,
        )

        return {
            "status": "success",
            "message": f"Order {order_id} status updated to {new_status}",
            "order_id": order_id,
            "new_status": new_status,
        }

    except Exception as exc:
        logger.error(
            "order_status_update_failed",
            order_id=order_id,
            new_status=new_status,
            error=str(exc),
            task_id=self.request.id,
        )

        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30)

        return {
            "status": "failed",
            "message": f"Failed to update order {order_id} status",
            "order_id": order_id,
            "error": str(exc),
        }


@celery_app.task(
    bind=True,
    base=OrderTask,
    name="meatbot.app.tasks.orders.cancel_order",
    queue="high",
    max_retries=1,
    default_retry_delay=60,
)
def cancel_order(self, order_id: int, reason: str = "") -> dict[str, str]:
    """Отмена заказа"""
    logger.info(
        "cancelling_order",
        order_id=order_id,
        reason=reason,
        task_id=self.request.id,
    )

    try:
        # Здесь будет логика отмены заказа
        # Пока что просто логируем

        logger.info(
            "order_cancelled",
            order_id=order_id,
            reason=reason,
            task_id=self.request.id,
        )

        return {
            "status": "success",
            "message": f"Order {order_id} cancelled",
            "order_id": order_id,
            "reason": reason,
        }

    except Exception as exc:
        logger.error(
            "order_cancellation_failed",
            order_id=order_id,
            reason=reason,
            error=str(exc),
            task_id=self.request.id,
        )

        return {
            "status": "failed",
            "message": f"Failed to cancel order {order_id}",
            "order_id": order_id,
            "error": str(exc),
        }
