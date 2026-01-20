"""
Сервис для работы с настройками платежей
"""

from typing import Optional

import structlog

from ..database import PaymentSettings, get_db

logger = structlog.get_logger()


class PaymentSettingsService:
    """Сервис для работы с настройками платежей"""

    def get_active_settings(self):
        """
        Получает активные настройки платежа

        Returns:
            dict | None: Активные настройки в виде словаря или None
        """
        try:
            with get_db() as db:
                settings = (
                    db.query(PaymentSettings)
                    .filter(PaymentSettings.is_active.is_(True))
                    .first()
                )

                if not settings:
                    logger.warning("no_active_payment_settings")
                    return None

                # Копируем данные в словарь внутри сессии
                settings_dict = {
                    "id": settings.id,
                    "bank_name": settings.bank_name,
                    "card_number": settings.card_number,
                    "recipient_name": settings.recipient_name,
                    "additional_info": settings.additional_info,
                    "is_active": settings.is_active,
                }

                return settings_dict

        except Exception as e:
            logger.error("get_active_settings_failed", error=str(e))
            return None

    def get_settings_by_id(
        self, settings_id: int
    ) -> Optional[PaymentSettings]:
        """
        Получает настройки по ID

        Args:
            settings_id: ID настроек

        Returns:
            Optional[PaymentSettings]: Настройки или None
        """
        try:
            with get_db() as db:
                settings = (
                    db.query(PaymentSettings)
                    .filter(PaymentSettings.id == settings_id)
                    .first()
                )
                return settings

        except Exception as e:
            logger.error(
                "get_settings_by_id_failed",
                settings_id=settings_id,
                error=str(e),
            )
            return None

    def update_settings(
        self,
        settings_id: int,
        bank_name: Optional[str] = None,
        card_number: Optional[str] = None,
        recipient_name: Optional[str] = None,
        additional_info: Optional[str] = None,
    ) -> bool:
        """
        Обновляет настройки платежа

        Args:
            settings_id: ID настроек
            bank_name: Название банка
            card_number: Номер карты
            recipient_name: Имя получателя
            additional_info: Дополнительная информация

        Returns:
            bool: True если обновление успешно, False иначе
        """
        try:
            with get_db() as db:
                settings = (
                    db.query(PaymentSettings)
                    .filter(PaymentSettings.id == settings_id)
                    .first()
                )

                if not settings:
                    logger.error(
                        "update_settings_not_found", settings_id=settings_id
                    )
                    return False

                # Обновляем только переданные поля
                if bank_name is not None:
                    settings.bank_name = bank_name
                if card_number is not None:
                    settings.card_number = card_number
                if recipient_name is not None:
                    settings.recipient_name = recipient_name
                if additional_info is not None:
                    settings.additional_info = additional_info

                db.commit()

                logger.info(
                    "settings_updated_successfully", settings_id=settings_id
                )
                return True

        except Exception as e:
            logger.error(
                "update_settings_failed",
                settings_id=settings_id,
                error=str(e),
            )
            return False

    def get_payment_message(self, total_amount: float) -> str:
        """
        Формирует сообщение с реквизитами для перевода

        Args:
            total_amount: Сумма к оплате

        Returns:
            str: Отформатированное сообщение
        """
        settings = self.get_active_settings()

        if not settings:
            # Возвращаем сообщение по умолчанию
            return (
                "💳 **Реквизиты для перевода:**\n\n"
                "⚠️ Реквизиты не настроены. Обратитесь к администратору.\n\n"
                f"💰 **Сумма к переводу:** {total_amount:.2f}₽"
            )

        message = (
            "💳 **Реквизиты для перевода:**\n\n"
            f"🏦 **Банк:** {settings['bank_name']}\n"
            f"💳 **Номер карты:** {settings['card_number']}\n"
            f"👤 **Получатель:** {settings['recipient_name']}\n\n"
            f"💰 **Сумма к переводу:** {total_amount:.2f}₽\n\n"
            f"{settings['additional_info']}"
        )

        return message
