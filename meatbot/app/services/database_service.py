"""
Сервис базы данных для MeatBot
"""

from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..interfaces import IDatabaseService


class DatabaseService(IDatabaseService):
    """Сервис для работы с базой данных"""

    def __init__(self):
        self._session: Optional[Session] = None

    def get_connection(self) -> Session:
        """Получить соединение с базой данных"""
        if self._session is None or not self._session.is_active:
            with get_db() as session:
                self._session = session
        return self._session

    def execute_query(self, query: str, params: Optional[Dict] = None) -> Any:
        """Выполнить запрос"""
        session = self.get_connection()
        try:
            result = session.execute(text(query), params or {})
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            raise e

    def is_connected(self) -> bool:
        """Проверить соединение с базой данных"""
        try:
            session = self.get_connection()
            session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def close(self) -> None:
        """Закрыть соединение"""
        if self._session:
            self._session.close()
            self._session = None

    def __enter__(self):
        """Контекстный менеджер - вход"""
        return self.get_connection()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - выход"""
        if exc_type:
            self.get_connection().rollback()
        else:
            self.get_connection().commit()
        self.close()
