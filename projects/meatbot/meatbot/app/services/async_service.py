"""
Сервис для асинхронных операций MeatBot
"""

import asyncio
from typing import Any, Awaitable, Callable, Dict, List, Optional

import structlog

from ..interfaces import IConfigService, IDatabaseService

logger = structlog.get_logger()


class AsyncService:
    """Сервис для управления асинхронными операциями"""

    def __init__(
        self,
        config_service: IConfigService,
        database_service: IDatabaseService,
    ):
        self.config = config_service
        self.database = database_service
        self._tasks: Dict[str, asyncio.Task] = {}
        self._semaphores: Dict[str, asyncio.Semaphore] = {}

    async def execute_with_retry(
        self,
        func: Callable[..., Awaitable[Any]],
        max_retries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        *args,
        **kwargs,
    ) -> Any:
        """Выполнить функцию с повторными попытками"""
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = delay * (backoff**attempt)
                    logger.warning(
                        "async_retry_attempt",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        wait_time=wait_time,
                        error=str(e),
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        "async_retry_failed",
                        function=func.__name__,
                        max_retries=max_retries,
                        error=str(e),
                    )

        raise last_exception

    async def execute_with_timeout(
        self,
        func: Callable[..., Awaitable[Any]],
        timeout: float = 30.0,
        *args,
        **kwargs,
    ) -> Any:
        """Выполнить функцию с таймаутом"""
        try:
            return await asyncio.wait_for(
                func(*args, **kwargs), timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.error(
                "async_timeout", function=func.__name__, timeout=timeout
            )
            raise

    async def execute_with_semaphore(
        self,
        semaphore_name: str,
        func: Callable[..., Awaitable[Any]],
        max_concurrent: int = 5,
        *args,
        **kwargs,
    ) -> Any:
        """Выполнить функцию с ограничением количества одновременных операций"""
        if semaphore_name not in self._semaphores:
            self._semaphores[semaphore_name] = asyncio.Semaphore(
                max_concurrent
            )

        semaphore = self._semaphores[semaphore_name]

        async with semaphore:
            return await func(*args, **kwargs)

    async def execute_parallel(
        self,
        tasks: List[Callable[..., Awaitable[Any]]],
        max_concurrent: Optional[int] = None,
        return_exceptions: bool = False,
    ) -> List[Any]:
        """Выполнить задачи параллельно"""
        if max_concurrent:
            semaphore = asyncio.Semaphore(max_concurrent)

            async def limited_task(task):
                async with semaphore:
                    return await task()

            tasks = [limited_task(task) for task in tasks]

        return await asyncio.gather(
            *tasks, return_exceptions=return_exceptions
        )

    async def execute_batch(
        self,
        items: List[Any],
        batch_size: int = 10,
        func: Callable[[List[Any]], Awaitable[Any]] = None,
    ) -> List[Any]:
        """Выполнить операции пакетами"""
        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]

            if func:
                result = await func(batch)
                results.append(result)
            else:
                # Обработка по умолчанию
                results.extend(batch)

        return results

    def create_task(self, name: str, coro: Awaitable[Any]) -> asyncio.Task:
        """Создать именованную задачу"""
        if name in self._tasks and not self._tasks[name].done():
            logger.warning("task_already_exists", name=name)
            self._tasks[name].cancel()

        task = asyncio.create_task(coro)
        self._tasks[name] = task

        logger.info("task_created", name=name)
        return task

    def get_task(self, name: str) -> Optional[asyncio.Task]:
        """Получить задачу по имени"""
        return self._tasks.get(name)

    def cancel_task(self, name: str) -> bool:
        """Отменить задачу"""
        if name in self._tasks:
            self._tasks[name].cancel()
            logger.info("task_cancelled", name=name)
            return True
        return False

    def get_active_tasks(self) -> Dict[str, str]:
        """Получить список активных задач"""
        active_tasks = {}
        for name, task in self._tasks.items():
            if not task.done():
                active_tasks[name] = "running"
            else:
                active_tasks[name] = (
                    "completed" if task.exception() is None else "failed"
                )
        return active_tasks

    async def wait_for_tasks(self, timeout: Optional[float] = None) -> None:
        """Дождаться завершения всех задач"""
        if not self._tasks:
            return

        tasks = [task for task in self._tasks.values() if not task.done()]
        if tasks:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True), timeout=timeout
            )

    async def cleanup_completed_tasks(self) -> None:
        """Очистить завершенные задачи"""
        completed_tasks = []
        for name, task in self._tasks.items():
            if task.done():
                completed_tasks.append(name)

        for name in completed_tasks:
            del self._tasks[name]

        if completed_tasks:
            logger.info("tasks_cleaned_up", count=len(completed_tasks))


class AsyncDatabaseService:
    """Асинхронный сервис для работы с базой данных"""

    def __init__(self, database_service: IDatabaseService):
        self.database = database_service
        self._connection_pool = None

    async def execute_async_query(
        self, query: str, params: Optional[Dict] = None
    ) -> Any:
        """Выполнить асинхронный запрос"""
        # В реальной реализации здесь был бы асинхронный драйвер
        # Пока используем синхронный с asyncio.to_thread
        return await asyncio.to_thread(
            self.database.execute_query, query, params
        )

    async def execute_batch_queries(
        self, queries: List[Dict[str, Any]]
    ) -> List[Any]:
        """Выполнить пакет запросов"""
        tasks = []
        for query_data in queries:
            task = self.execute_async_query(
                query_data["query"], query_data.get("params")
            )
            tasks.append(task)

        return await asyncio.gather(*tasks, return_exceptions=True)

    async def is_connected_async(self) -> bool:
        """Асинхронная проверка соединения"""
        return await asyncio.to_thread(self.database.is_connected)


class AsyncCacheService:
    """Асинхронный сервис для работы с кэшем"""

    def __init__(self, cache_service):
        self.cache = cache_service

    async def get_async(self, key: str) -> Optional[Any]:
        """Асинхронное получение из кэша"""
        return await asyncio.to_thread(self.cache.get, key)

    async def set_async(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> bool:
        """Асинхронное сохранение в кэш"""
        return await asyncio.to_thread(self.cache.set, key, value, ttl)

    async def delete_async(self, key: str) -> bool:
        """Асинхронное удаление из кэша"""
        return await asyncio.to_thread(self.cache.delete, key)

    async def exists_async(self, key: str) -> bool:
        """Асинхронная проверка существования ключа"""
        return await asyncio.to_thread(self.cache.exists, key)

    async def get_multiple_async(self, keys: List[str]) -> Dict[str, Any]:
        """Асинхронное получение нескольких ключей"""
        tasks = [self.get_async(key) for key in keys]
        values = await asyncio.gather(*tasks, return_exceptions=True)

        result = {}
        for key, value in zip(keys, values):
            if not isinstance(value, Exception):
                result[key] = value

        return result

    async def set_multiple_async(
        self, items: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """Асинхронное сохранение нескольких ключей"""
        tasks = [
            self.set_async(key, value, ttl) for key, value in items.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return all(
            not isinstance(result, Exception) and result for result in results
        )
