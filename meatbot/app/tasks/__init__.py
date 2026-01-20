"""
Модуль задач Celery для MeatBot
"""

from .notifications import (
    send_admin_notification,
    send_bulk_notification,
    send_order_notification,
)
from .orders import cancel_order, process_order, update_order_status
from .webhooks import (
    process_payment_webhook,
    process_telegram_webhook,
    validate_webhook_signature,
)

__all__ = [
    # Order tasks
    "process_order",
    "update_order_status",
    "cancel_order",
    # Notification tasks
    "send_order_notification",
    "send_admin_notification",
    "send_bulk_notification",
    # Webhook tasks
    "process_payment_webhook",
    "process_telegram_webhook",
    "validate_webhook_signature",
]
