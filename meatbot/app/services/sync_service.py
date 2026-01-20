"""
Сервис для синхронных операций MeatBot
"""

import time
from typing import Any, Callable, Dict, List, Optional

import structlog

from ..interfaces import IConfigService, IDatabaseService

logger = structlog.get_logger()


class SyncService:
    """Сервис для управления синхронными операциями"""

    def __init__(
        self,
        config_service: IConfigService,
        database_service: IDatabaseService,
    ):
        self.config = config_service
        self.database = database_service
        self._locks: Dict[str, Any] = {}

    def execute_with_retry(
        self,
        func: Callable[..., Any],
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
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = delay * (backoff**attempt)
                    logger.warning(
                        "sync_retry_attempt",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        wait_time=wait_time,
                        error=str(e),
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        "sync_retry_failed",
                        function=func.__name__,
                        max_retries=max_retries,
                        error=str(e),
                    )

        raise last_exception

    def execute_with_timeout(
        self, func: Callable[..., Any], timeout: float = 30.0, *args, **kwargs
    ) -> Any:
        """Выполнить функцию с таймаутом"""
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError(
                f"Function {
                    func.__name__} timed out after {timeout} seconds")

        # Устанавливаем обработчик таймаута
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(timeout))

        try:
            result = func(*args, **kwargs)
            return result
        except TimeoutError:
            logger.error(
                "sync_timeout",
                function=func.__name__,
                timeout=timeout)
            raise
        finally:
            # Восстанавливаем старый обработчик
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    def execute_batch(
        self,
        items: List[Any],
        batch_size: int = 10,
        func: Callable[[List[Any]], Any] = None,
    ) -> List[Any]:
        """Выполнить операции пакетами"""
        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i: i + batch_size]

            if func:
                result = func(batch)
                results.append(result)
            else:
                # Обработка по умолчанию
                results.extend(batch)

        return results

    def execute_sequential(
            self, functions: List[Callable[..., Any]], *args, **kwargs) -> List[Any]:
        """Выполнить функции последовательно"""
        results = []

        for func in functions:
            try:
                result = func(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(
                    "sequential_execution_failed",
                    function=func.__name__,
                    error=str(e),
                )
                results.append(None)

        return results


class SyncDatabaseService:
    """Синхронный сервис для работы с базой данных"""

    def __init__(self, database_service: IDatabaseService):
        self.database = database_service
        self._connection_pool = None

    def execute_query(self, query: str, params: Optional[Dict] = None) -> Any:
        """Выполнить синхронный запрос"""
        return self.database.execute_query(query, params)

    def execute_batch_queries(
            self, queries: List[Dict[str, Any]]) -> List[Any]:
        """Выполнить пакет запросов"""
        results = []
        for query_data in queries:
            try:
                result = self.execute_query(
                    query_data["query"], query_data.get("params"))
                results.append(result)
            except Exception as e:
                logger.error(
                    "batch_query_failed",
                    query=query_data["query"],
                    error=str(e),
                )
                results.append(None)

        return results

    def execute_transaction(self, operations: List[Callable[[], Any]]) -> bool:
        """Выполнить операции в транзакции"""
        try:
            # Начинаем транзакцию
            session = self.database.get_connection()

            for operation in operations:
                operation()

            # Коммитим транзакцию
            session.commit()
            return True

        except Exception as e:
            # Откатываем транзакцию
            session.rollback()
            logger.error("transaction_failed", error=str(e))
            return False

    def is_connected(self) -> bool:
        """Проверить соединение"""
        return self.database.is_connected()


class SyncCacheService:
    """Синхронный сервис для работы с кэшем"""

    def __init__(self, cache_service):
        self.cache = cache_service

    def get(self, key: str) -> Optional[Any]:
        """Получить из кэша"""
        return self.cache.get(key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Сохранить в кэш"""
        return self.cache.set(key, value, ttl)

    def delete(self, key: str) -> bool:
        """Удалить из кэша"""
        return self.cache.delete(key)

    def exists(self, key: str) -> bool:
        """Проверить существование ключа"""
        return self.cache.exists(key)

    def get_multiple(self, keys: List[str]) -> Dict[str, Any]:
        """Получить несколько ключей"""
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result

    def set_multiple(self, items: Dict[str, Any],
                     ttl: Optional[int] = None) -> bool:
        """Сохранить несколько ключей"""
        success = True
        for key, value in items.items():
            if not self.set(key, value, ttl):
                success = False
        return success

    def clear_pattern(self, pattern: str) -> int:
        """Очистить ключи по паттерну"""
        # В реальной реализации здесь был бы поиск по паттерну
        # Пока возвращаем 0
        logger.info("clear_pattern", pattern=pattern)
        return 0


class SyncFileService:
    """Синхронный сервис для работы с файлами"""

    def __init__(self, config_service: IConfigService):
        self.config = config_service
        self._file_locks: Dict[str, Any] = {}

    def read_file(self, filepath: str) -> Optional[str]:
        """Прочитать файл"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error("file_read_failed", filepath=filepath, error=str(e))
            return None

    def write_file(self, filepath: str, content: str) -> bool:
        """Записать файл"""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error("file_write_failed", filepath=filepath, error=str(e))
            return False

    def file_exists(self, filepath: str) -> bool:
        """Проверить существование файла"""
        import os

        return os.path.exists(filepath)

    def get_file_size(self, filepath: str) -> Optional[int]:
        """Получить размер файла"""
        import os

        try:
            return os.path.getsize(filepath)
        except Exception as e:
            logger.error("file_size_failed", filepath=filepath, error=str(e))
            return None

    def list_files(self, directory: str, pattern: str = "*") -> List[str]:
        """Получить список файлов"""
        import glob
        import os

        try:
            search_pattern = os.path.join(directory, pattern)
            return glob.glob(search_pattern)
        except Exception as e:
            logger.error(
                "list_files_failed",
                directory=directory,
                error=str(e))
            return []
