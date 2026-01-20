"""
Сервис health checks для MeatBot
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog

from ..interfaces import ICacheService, IConfigService, IDatabaseService

logger = structlog.get_logger()


class HealthCheck:
    """Базовый класс для health check"""

    def __init__(self, name: str, critical: bool = True):
        self.name = name
        self.critical = critical
        self.last_check: Optional[datetime] = None
        self.last_status: Optional[bool] = None
        self.last_error: Optional[str] = None

    async def check(self) -> Dict[str, Any]:
        """Выполнить проверку"""
        try:
            start_time = datetime.utcnow()
            result = await self._perform_check()
            duration = (datetime.utcnow() - start_time).total_seconds()

            self.last_check = datetime.utcnow()
            self.last_status = result.get("status") == "healthy"
            self.last_error = None

            return {
                "name": self.name,
                "status": result.get("status", "unknown"),
                "duration_ms": round(duration * 1000, 2),
                "critical": self.critical,
                "details": result.get("details", {}),
                "timestamp": self.last_check.isoformat(),
            }
        except Exception as e:
            self.last_check = datetime.utcnow()
            self.last_status = False
            self.last_error = str(e)

            logger.error("health_check_failed", name=self.name, error=str(e))

            return {
                "name": self.name,
                "status": "unhealthy",
                "duration_ms": 0,
                "critical": self.critical,
                "error": str(e),
                "timestamp": self.last_check.isoformat(),
            }

    async def _perform_check(self) -> Dict[str, Any]:
        """Выполнить конкретную проверку (должен быть переопределен)"""
        raise NotImplementedError


class DatabaseHealthCheck(HealthCheck):
    """Health check для базы данных"""

    def __init__(self, database_service: IDatabaseService):
        super().__init__("database", critical=True)
        self.database_service = database_service

    async def _perform_check(self) -> Dict[str, Any]:
        """Проверить подключение к базе данных"""
        try:
            # Проверяем соединение
            is_connected = self.database_service.is_connected()

            if not is_connected:
                return {
                    "status": "unhealthy",
                    "details": {"error": "Database connection failed"},
                }

            # Выполняем простой запрос
            self.database_service.execute_query("SELECT 1 as test")

            return {
                "status": "healthy",
                "details": {"connection": "active", "query_test": "passed"},
            }
        except Exception as e:
            return {"status": "unhealthy", "details": {"error": str(e)}}


class RedisHealthCheck(HealthCheck):
    """Health check для Redis"""

    def __init__(self, cache_service: Optional[ICacheService]):
        super().__init__("redis", critical=False)  # Redis не критичен
        self.cache_service = cache_service

    async def _perform_check(self) -> Dict[str, Any]:
        """Проверить подключение к Redis"""
        if not self.cache_service:
            return {
                "status": "disabled",
                "details": {"reason": "Cache service not available"},
            }

        try:
            # Проверяем соединение
            test_key = "health_check_test"
            test_value = "test_value"

            # Тест записи
            set_result = self.cache_service.set(test_key, test_value, ttl=10)
            if not set_result:
                return {
                    "status": "unhealthy",
                    "details": {"error": "Failed to set test key"},
                }

            # Тест чтения
            get_result = self.cache_service.get(test_key)
            if get_result != test_value:
                return {
                    "status": "unhealthy",
                    "details": {"error": "Failed to get test key"},
                }

            # Тест удаления
            delete_result = self.cache_service.delete(test_key)
            if not delete_result:
                return {
                    "status": "unhealthy",
                    "details": {"error": "Failed to delete test key"},
                }

            return {
                "status": "healthy",
                "details": {
                    "connection": "active",
                    "read_write_test": "passed",
                },
            }
        except Exception as e:
            return {"status": "unhealthy", "details": {"error": str(e)}}


class ConfigHealthCheck(HealthCheck):
    """Health check для конфигурации"""

    def __init__(self, config_service: IConfigService):
        super().__init__("config", critical=True)
        self.config_service = config_service

    async def _perform_check(self) -> Dict[str, Any]:
        """Проверить конфигурацию"""
        try:
            # Проверяем обязательные настройки
            bot_token = self.config_service.get_bot_token()
            database_url = self.config_service.get_database_url()

            issues = []

            if not bot_token:
                issues.append("BOT_TOKEN is empty")

            if not database_url:
                issues.append("DATABASE_URL is empty")

            if issues:
                return {"status": "unhealthy", "details": {"issues": issues}}

            return {
                "status": "healthy",
                "details": {
                    "bot_token": "configured",
                    "database_url": "configured",
                    "environment": self.config_service.get("env", "unknown"),
                },
            }
        except Exception as e:
            return {"status": "unhealthy", "details": {"error": str(e)}}


class HealthService:
    """Сервис для управления health checks"""

    def __init__(
        self,
        config_service: IConfigService,
        database_service: IDatabaseService,
        cache_service: Optional[ICacheService] = None,
    ):
        self.config_service = config_service
        self.database_service = database_service
        self.cache_service = cache_service
        self.checks: List[HealthCheck] = []
        self._setup_checks()

    def _setup_checks(self) -> None:
        """Настроить health checks"""
        self.checks = [
            ConfigHealthCheck(self.config_service),
            DatabaseHealthCheck(self.database_service),
            RedisHealthCheck(self.cache_service),
        ]

    async def run_all_checks(self) -> Dict[str, Any]:
        """Выполнить все health checks"""
        logger.info("Running health checks...")

        results = []
        overall_status = "healthy"
        critical_failed = False

        # Выполняем все проверки параллельно
        tasks = [check.check() for check in self.checks]
        check_results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(check_results):
            if isinstance(result, Exception):
                # Обрабатываем исключения
                check = self.checks[i]
                result = {
                    "name": check.name,
                    "status": "unhealthy",
                    "duration_ms": 0,
                    "critical": check.critical,
                    "error": str(result),
                    "timestamp": datetime.utcnow().isoformat(),
                }

            results.append(result)

            # Определяем общий статус
            if (
                isinstance(result, dict)
                and result.get("status") == "unhealthy"
            ):
                if result.get("critical"):
                    critical_failed = True
                    overall_status = "unhealthy"
                elif overall_status == "healthy":
                    overall_status = "degraded"

        response = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": results,
            "summary": {
                "total": len(results),
                "healthy": len(
                    [r for r in results if r["status"] == "healthy"]
                ),
                "unhealthy": len(
                    [r for r in results if r["status"] == "unhealthy"]
                ),
                "disabled": len(
                    [r for r in results if r["status"] == "disabled"]
                ),
                "critical_failed": critical_failed,
            },
        }

        logger.info(
            "Health checks completed",
            status=overall_status,
            summary=response["summary"],
        )
        return response

    async def run_quick_check(self) -> Dict[str, Any]:
        """Выполнить быструю проверку (только критические компоненты)"""
        critical_checks = [check for check in self.checks if check.critical]

        if not critical_checks:
            return {
                "status": "healthy",
                "message": "No critical checks configured",
            }

        # Выполняем только критические проверки
        tasks = [check.check() for check in critical_checks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_healthy = True
        for result in results:
            if isinstance(result, Exception) or (
                isinstance(result, dict) and result.get("status") != "healthy"
            ):
                all_healthy = False
                break

        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "critical_checks_passed": all_healthy,
        }

    def get_check_status(self, name: str) -> Optional[Dict[str, Any]]:
        """Получить статус конкретной проверки"""
        for check in self.checks:
            if check.name == name:
                return {
                    "name": check.name,
                    "last_check": check.last_check.isoformat()
                    if check.last_check
                    else None,
                    "last_status": check.last_status,
                    "last_error": check.last_error,
                    "critical": check.critical,
                }
        return None
