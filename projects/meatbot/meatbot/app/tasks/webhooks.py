"""
Задачи для обработки webhook'ов
"""

from __future__ import annotations

import structlog
from celery import Task

from ..celery_app import celery_app

logger = structlog.get_logger()


class WebhookTask(Task):
    """Базовый класс для задач обработки webhook'ов"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Обработка ошибок webhook'ов"""
        logger.error(
            "webhook_task_failed",
            task_id=task_id,
            task_name=self.name,
            error=str(exc),
            args=args,
            kwargs=kwargs,
        )


@celery_app.task(
    bind=True,
    base=WebhookTask,
    name="meatbot.app.tasks.webhooks.process_payment_webhook",
    queue="critical",
    max_retries=5,
    default_retry_delay=10,
)
def process_payment_webhook(self, webhook_data: dict) -> dict[str, str]:
    """Обработка webhook'а от платежной системы"""
    logger.info(
        "processing_payment_webhook",
        webhook_id=webhook_data.get("id"),
        event_type=webhook_data.get("event"),
        task_id=self.request.id,
    )

    try:
        # Здесь будет логика обработки webhook'а от YooKassa
        # Проверка подписи, валидация данных, обновление статуса заказа
        # Пока что просто логируем

        webhook_id = webhook_data.get("id")
        event_type = webhook_data.get("event")

        logger.info(
            "payment_webhook_processed",
            webhook_id=webhook_id,
            event_type=event_type,
            task_id=self.request.id,
        )

        return {
            "status": "success",
            "message": f"Payment webhook {webhook_id} processed successfully",
            "webhook_id": webhook_id,
            "event_type": event_type,
        }

    except Exception as exc:
        logger.error(
            "payment_webhook_failed",
            webhook_data=webhook_data,
            error=str(exc),
            task_id=self.request.id,
        )

        # Retry с exponential backoff для критичных webhook'ов
        if self.request.retries < self.max_retries:
            delay = 10 * (2**self.request.retries)  # 10s, 20s, 40s, 80s, 160s
            logger.info(
                "retrying_payment_webhook",
                webhook_id=webhook_data.get("id"),
                retry_count=self.request.retries + 1,
                delay=delay,
            )
            raise self.retry(countdown=delay)

        return {
            "status": "failed",
            "message": f"Payment webhook processing failed after {
                self.max_retries} retries",
            "webhook_id": webhook_data.get("id"),
            "error": str(exc),
        }


@celery_app.task(
    bind=True,
    base=WebhookTask,
    name="meatbot.app.tasks.webhooks.process_telegram_webhook",
    queue="critical",
    max_retries=3,
    default_retry_delay=5,
)
def process_telegram_webhook(self, webhook_data: dict) -> dict[str, str]:
    """Обработка webhook'а от Telegram"""
    logger.info(
        "processing_telegram_webhook",
        update_id=webhook_data.get("update_id"),
        task_id=self.request.id,
    )

    try:
        # Здесь будет логика обработки webhook'а от Telegram
        # Пока что просто логируем

        update_id = webhook_data.get("update_id")

        logger.info(
            "telegram_webhook_processed",
            update_id=update_id,
            task_id=self.request.id,
        )

        return {
            "status": "success",
            "message": f"Telegram webhook {update_id} processed successfully",
            "update_id": update_id,
        }

    except Exception as exc:
        logger.error(
            "telegram_webhook_failed",
            webhook_data=webhook_data,
            error=str(exc),
            task_id=self.request.id,
        )

        if self.request.retries < self.max_retries:
            raise self.retry(countdown=5 * (2**self.request.retries))

        return {
            "status": "failed",
            "message": "Telegram webhook processing failed",
            "update_id": webhook_data.get("update_id"),
            "error": str(exc),
        }


@celery_app.task(
    bind=True,
    base=WebhookTask,
    name="meatbot.app.tasks.webhooks.validate_webhook_signature",
    queue="critical",
    max_retries=1,
    default_retry_delay=30,
)
def validate_webhook_signature(
        self, signature: str, payload: str, secret: str) -> dict[str, str]:
    """Валидация подписи webhook'а"""
    logger.info(
        "validating_webhook_signature",
        signature_length=len(signature),
        payload_length=len(payload),
        task_id=self.request.id,
    )

    try:
        # Здесь будет логика валидации HMAC подписи
        # Пока что просто логируем

        logger.info(
            "webhook_signature_validated",
            signature_length=len(signature),
            task_id=self.request.id,
        )

        return {
            "status": "success",
            "message": "Webhook signature validated successfully",
            "is_valid": True,
        }

    except Exception as exc:
        logger.error(
            "webhook_signature_validation_failed",
            error=str(exc),
            task_id=self.request.id,
        )

        return {
            "status": "failed",
            "message": "Webhook signature validation failed",
            "is_valid": False,
            "error": str(exc),
        }
