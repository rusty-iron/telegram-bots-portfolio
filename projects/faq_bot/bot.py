"""
FAQ Bot - Telegram бот с базой знаний.

Точка входа приложения.
"""

import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import get_config
from handlers import get_all_routers
from utils.stats import StatsManager
from utils.faq_loader import FAQLoader
from utils.search import FAQSearch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Главная функция запуска бота."""
    logger.info("Запуск FAQ Bot...")

    try:
        config = get_config()
    except ValueError as e:
        logger.error(f"Ошибка конфигурации: {e}")
        sys.exit(1)

    stats = StatsManager(config.db_file)
    await stats.init()

    faq_loader = FAQLoader(config.faq_file)
    faq_loader.load()

    faq_search = FAQSearch(faq_loader.data)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp["admin_id"] = config.admin_id
    dp["support_username"] = config.support_username
    dp["stats"] = stats
    dp["faq_loader"] = faq_loader
    dp["faq_search"] = faq_search

    for router in get_all_routers():
        dp.include_router(router)

    dp.shutdown.register(shutdown_handler(stats))

    logger.info("Бот запущен")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await stats.close()
        await bot.session.close()
        logger.info("Бот остановлен")


def shutdown_handler(stats: StatsManager):
    """Создает обработчик завершения работы."""
    async def handler(*args, **kwargs):
        logger.info("Завершение работы...")
        await stats.close()
    return handler


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
        sys.exit(1)
