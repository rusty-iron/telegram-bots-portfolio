import asyncio
import sys
import traceback
from typing import Any, Type, cast

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web

from .config import settings
from .container import container, register_instance, register_singleton
from .handlers import (
    admin_router,
    cart_router,
    catalog_router,
    commands_router,
    orders_router,
    start_router,
)
from .interfaces import IConfigService, IDatabaseService
from .middlewares.admin import AdminMiddleware
from .middlewares.auth import setup_security_middleware
from .middlewares.error_handler import ErrorHandlerMiddleware
from .middlewares.rate_limit import RateLimitMiddleware
from .services.async_service import (
    AsyncCacheService,
    AsyncDatabaseService,
    AsyncService,
)
from .services.cache_service import CacheService
from .services.catalog_service import CatalogService
from .services.config_service import ConfigService
from .services.database_service import DatabaseService
from .services.health_service import HealthService
from .services.image_service import ImageOptimizationService
from .services.metrics_service import init_metrics_service
from .services.sync_service import (
    SyncCacheService,
    SyncDatabaseService,
    SyncFileService,
    SyncService,
)
from .utils.cache import create_redis_client
from .utils.encryption import init_security_services
from .utils.file_validation import init_file_validation_services

logger = structlog.get_logger()


def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def setup_di_container() -> None:
    """Настройка DI контейнера"""
    logger.info("Настройка DI контейнера...")

    # Регистрируем сервисы
    register_singleton(cast(Type[Any], IConfigService), ConfigService)
    register_singleton(cast(Type[Any], IDatabaseService), DatabaseService)

    # Регистрируем экземпляры сервисов
    config_service = ConfigService()
    database_service = DatabaseService()

    register_instance(cast(Type[Any], IConfigService), config_service)
    register_instance(cast(Type[Any], IDatabaseService), database_service)

    # Инициализируем сервис метрик
    init_metrics_service(config_service)
    logger.info("Metrics service initialized")

    # Инициализируем сервисы безопасности
    # SECURITY FIX (P2-ENC-03): Pass encryption_key from settings to ensure data persistence
    init_security_services(secret_key=settings.encryption_key)
    init_file_validation_services()
    logger.info("Security services initialized")

    # Инициализируем async/sync сервисы
    async_service = AsyncService(config_service, database_service)
    sync_service = SyncService(config_service, database_service)

    # Регистрируем экземпляры сервисов
    register_instance(AsyncService, async_service)
    register_instance(SyncService, sync_service)

    logger.info("Async/Sync services initialized")
    logger.info("DI контейнер настроен")


def create_app() -> web.Application:
    app = web.Application()

    redis_client = create_redis_client(str(settings.redis_url))

    # Инициализируем DI контейнер
    setup_di_container()

    # Инициализируем сервисы
    cache_service = CacheService(redis_client)
    catalog_service = CatalogService(cache_service)
    image_service = ImageOptimizationService()

    # Получаем async/sync сервисы из DI контейнера
    async_service = container.get(AsyncService)
    sync_service = container.get(SyncService)

    # Создаем специализированные сервисы
    async_db_service = AsyncDatabaseService(
        container.get(IDatabaseService)
    )  # type: ignore[type-abstract]
    sync_db_service = SyncDatabaseService(
        container.get(IDatabaseService)
    )  # type: ignore[type-abstract]
    async_cache_service = AsyncCacheService(cache_service)
    sync_cache_service = SyncCacheService(cache_service)
    sync_file_service = SyncFileService(
        container.get(IConfigService)
    )  # type: ignore[type-abstract]

    # Сохраняем сервисы в контексте приложения
    app["cache_service"] = cache_service
    app["catalog_service"] = catalog_service
    app["image_service"] = image_service
    app["async_service"] = async_service
    app["sync_service"] = sync_service
    app["async_db_service"] = async_db_service
    app["sync_db_service"] = sync_db_service
    app["async_cache_service"] = async_cache_service
    app["sync_cache_service"] = sync_cache_service
    app["sync_file_service"] = sync_file_service

    async def live_handler(_: web.Request) -> web.Response:
        return web.json_response({"status": "live"})

    async def ready_handler(_: web.Request) -> web.Response:
        """Health check endpoint"""
        try:
            # Получаем сервисы из DI контейнера
            # type: ignore[type-abstract]
            config_service = container.get(cast(Type[Any], IConfigService))
            database_service = container.get(
                IDatabaseService
            )  # type: ignore[type-abstract]
            cache_service = app.get("cache_service")

            # Создаем health service
            health_service = HealthService(
                config_service, database_service, cache_service
            )

            # Выполняем быструю проверку
            result = await health_service.run_quick_check()

            if result["status"] == "healthy":
                return web.json_response(result)
            else:
                return web.json_response(result, status=503)
        except Exception as e:
            logger.error("health_check_failed", error=str(e))
            return web.json_response(
                {"status": "error", "error": str(e)}, status=500
            )

    async def metrics_handler(_: web.Request) -> web.Response:
        """Metrics endpoint"""
        try:
            from .services.metrics_service import get_metrics_service

            metrics_service = get_metrics_service()

            if not metrics_service:
                return web.json_response(
                    {"error": "Metrics service not available"}, status=503
                )

            summary = metrics_service.get_summary()
            return web.json_response(summary)
        except Exception as e:
            logger.error("metrics_endpoint_failed", error=str(e))
            return web.json_response({"error": str(e)}, status=500)

    app.add_routes(
        [
            web.get("/health/live", live_handler),
            web.get("/health/ready", ready_handler),
            web.get("/metrics", metrics_handler),
        ]
    )

    # Настраиваем middleware безопасности
    api_key = settings.api_key if settings.api_key else settings.bot_token[:32]
    admin_key = settings.admin_key if settings.admin_key else api_key
    setup_security_middleware(app, api_key, admin_key)

    return app


def validate_secrets() -> None:
    """Validate that all required secrets are set"""
    errors = []

    # Validate BOT_TOKEN
    if not settings.bot_token or settings.bot_token.strip() == "":
        errors.append("BOT_TOKEN must be set and not empty")

    # Validate API keys (for HTTP middleware)
    if not settings.api_key or settings.api_key.strip() == "":
        errors.append("API_KEY must be set and not empty")

    if not settings.admin_key or settings.admin_key.strip() == "":
        errors.append("ADMIN_KEY must be set and not empty")

    # Validate ENCRYPTION_KEY
    if not settings.encryption_key or settings.encryption_key.strip() == "":
        errors.append("ENCRYPTION_KEY must be set and not empty")

    # Validate Redis password (check for :password@ pattern)
    redis_url_str = str(settings.redis_url)
    if "://:@" in redis_url_str or "redis://redis:" in redis_url_str:
        errors.append("REDIS_URL must contain password (format: redis://:password@host:port/db)")

    # Validate database URL doesn't use default credentials in production
    if settings.env == "production":
        if "postgres:postgres" in settings.database_url:
            errors.append("DATABASE_URL uses default credentials in production environment")

    if errors:
        logger.error("secrets_validation_failed", errors=errors)
        print("\n" + "=" * 80)
        print("SECURITY ERROR: Missing or invalid secrets!")
        print("=" * 80)
        for error in errors:
            print(f"  - {error}")
        print("=" * 80)
        print("\nPlease check your .env file and set all required secrets.")
        print("See .env.example for instructions on how to generate secure keys.\n")
        sys.exit(1)

    logger.info("secrets_validation_passed")


async def run_bot() -> None:
    configure_logging()
    logger.info("starting_meatbot", env=settings.env)

    # Validate secrets before starting
    validate_secrets()

    bot_token = settings.bot_token.strip()
    bot = None
    dp = None
    if bot_token:
        bot = Bot(
            token=bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        dp = Dispatcher()

        # Добавляем middleware для rate limiting (первым - защита от DoS)
        rate_limiter = RateLimitMiddleware(
            rate_limit=30,  # 30 запросов за минуту для обычных пользователей
            time_window=60,  # Временное окно 60 секунд
            admin_rate_limit=100,  # 100 запросов за минуту для админов
        )
        dp.message.middleware(rate_limiter)
        dp.callback_query.middleware(rate_limiter)

        logger.info(
            "rate_limiting_enabled",
            user_limit=30,
            admin_limit=100,
            time_window=60,
        )

        # Добавляем middleware для обработки ошибок
        dp.message.middleware(ErrorHandlerMiddleware())
        dp.callback_query.middleware(ErrorHandlerMiddleware())

        # Добавляем middleware для проверки прав администратора
        dp.message.middleware(AdminMiddleware())
        dp.callback_query.middleware(AdminMiddleware())

        # Подключаем роутеры
        dp.include_router(start_router)
        dp.include_router(commands_router)
        dp.include_router(catalog_router)
        dp.include_router(cart_router)
        dp.include_router(orders_router)
        dp.include_router(admin_router)
    else:
        logger.warning(
            "bot_token_missing", msg="BOT_TOKEN is empty; polling disabled"
        )

    # Optionally run migrations on start
    if settings.run_migrations_on_start:
        import subprocess

        try:
            subprocess.check_call(
                ["alembic", "-c", "/app/alembic.ini", "upgrade", "head"],
                cwd="/app",
            )
            logger.info("alembic_upgrade_success")
        except Exception as exc:
            logger.error("alembic_upgrade_failed", error=str(exc))

    # Start web health server in background
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
        runner, host=settings.web_app_host, port=settings.web_app_port
    )
    await site.start()
    logger.info(
        "health_server_started",
        host=settings.web_app_host,
        port=settings.web_app_port,
    )

    try:
        if bot_token and bot and dp:
            logger.info("bot_polling_started")
            await dp.start_polling(bot)
        else:
            # Keep process alive for health endpoints
            while True:
                await asyncio.sleep(3600)
    except Exception as exc:
        logger.error(
            "bot_critical_error",
            error=str(exc),
            exc_info=traceback.format_exc(),
            error_type=type(exc).__name__,
        )
        sys.exit(1)
    finally:
        logger.info("bot_shutdown")
        if bot:
            await bot.session.close()
        await runner.cleanup()


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
