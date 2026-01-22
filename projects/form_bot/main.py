"""
FormBot — Telegram бот для сбора заявок.

Точка входа приложения.
"""

import asyncio
import logging
import signal
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from src.config import settings
from src.handlers import setup_routers
from src.middlewares import ThrottlingMiddleware


def setup_logging() -> None:
    """Настраивает систему логирования с ротацией файлов."""
    settings.ensure_directories()

    # Формат логов
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Настройка корневого логгера
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())

    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.log_level.upper())
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(console_handler)

    # Файловый обработчик с ротацией
    file_handler = RotatingFileHandler(
        filename=settings.log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(settings.log_level.upper())
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(file_handler)

    # Уменьшаем уровень логирования для внешних библиотек
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


async def on_startup(bot: Bot) -> None:
    """
    Действия при запуске бота.

    Args:
        bot: Экземпляр бота.
    """
    logger = logging.getLogger(__name__)

    # Получаем информацию о боте
    bot_info = await bot.get_me()
    logger.info(f"Бот запущен: @{bot_info.username} ({bot_info.full_name})")
    logger.info(f"ID администратора: {settings.admin_id}")

    # Уведомляем администратора
    try:
        await bot.send_message(
            chat_id=settings.admin_id,
            text="🟢 <b>Бот запущен и готов к работе!</b>",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.warning(f"Не удалось отправить уведомление админу о запуске: {e}")


async def on_shutdown(bot: Bot) -> None:
    """
    Действия при остановке бота.

    Args:
        bot: Экземпляр бота.
    """
    logger = logging.getLogger(__name__)
    logger.info("Остановка бота...")

    # Уведомляем администратора
    try:
        await bot.send_message(
            chat_id=settings.admin_id,
            text="🔴 <b>Бот остановлен.</b>",
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass

    logger.info("Бот остановлен")


async def main() -> None:
    """Главная функция запуска бота."""
    # Настраиваем логирование
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 50)
    logger.info("Инициализация FormBot")
    logger.info("=" * 50)

    # Создаём бота и диспетчер
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрируем middleware
    dp.message.middleware(ThrottlingMiddleware())

    # Подключаем роутеры
    router = setup_routers()
    dp.include_router(router)

    # Регистрируем события запуска/остановки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Запускаем polling
    try:
        logger.info("Запуск polling...")
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )
    finally:
        await bot.session.close()


def handle_signal(signum: int, frame: Optional[object]) -> None:
    """
    Обработчик сигналов для graceful shutdown.

    Args:
        signum: Номер сигнала.
        frame: Текущий стек-фрейм.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Получен сигнал {signum}, завершение работы...")
    sys.exit(0)


if __name__ == "__main__":
    # Регистрируем обработчики сигналов для graceful shutdown
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен пользователем")
