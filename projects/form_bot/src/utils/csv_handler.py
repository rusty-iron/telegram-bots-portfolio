"""
Модуль для работы с CSV-файлом заявок.

Обеспечивает сохранение и экспорт данных заявок.
Поддерживает новый формат с полями status и updated_at.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.config import settings

logger = logging.getLogger(__name__)

# Заголовки CSV-файла (новый формат с поддержкой статусов)
CSV_HEADERS = ["timestamp", "user_id", "name", "phone", "email", "message", "status", "updated_at"]

# Статус по умолчанию для новых заявок
DEFAULT_STATUS = "Новая"


class CSVHandler:
    """Обработчик CSV-файла с заявками."""

    def __init__(self, file_path: Optional[Path] = None) -> None:
        """
        Инициализирует обработчик CSV.

        Args:
            file_path: Путь к CSV-файлу. По умолчанию из настроек.
        """
        self.file_path = file_path or settings.csv_file
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Создаёт CSV-файл с заголовками, если он не существует."""
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(CSV_HEADERS)
            logger.info(f"Создан CSV-файл: {self.file_path}")

    def save_application(
        self,
        user_id: int,
        name: str,
        phone: str,
        email: str,
        message: str = "",
    ) -> bool:
        """
        Сохраняет заявку в CSV-файл.

        Args:
            user_id: Telegram ID пользователя.
            name: Имя пользователя.
            phone: Номер телефона.
            email: Email адрес.
            message: Текст сообщения (опционально).

        Returns:
            bool: True если сохранение успешно, False при ошибке.
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with open(self.file_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp,
                    user_id,
                    name,
                    phone,
                    email,
                    message,
                    DEFAULT_STATUS,  # Статус по умолчанию
                    timestamp,       # updated_at = timestamp при создании
                ])

            logger.info(f"Заявка сохранена: user_id={user_id}, name={name}")
            return True

        except Exception as e:
            logger.error(f"Ошибка сохранения заявки: {e}")
            return False

    def get_csv_content(self) -> Optional[bytes]:
        """
        Возвращает содержимое CSV-файла в байтах с UTF-8 BOM.

        BOM (Byte Order Mark) необходим для корректного отображения
        кириллицы в Excel и других программах.

        Returns:
            Optional[bytes]: Содержимое файла с BOM или None при ошибке.
        """
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Добавляем UTF-8 BOM для корректного отображения в Excel
            return b'\xef\xbb\xbf' + content.encode("utf-8")
        except Exception as e:
            logger.error(f"Ошибка чтения CSV: {e}")
            return None

    def get_applications_count(self) -> int:
        """
        Возвращает количество сохранённых заявок.

        Returns:
            int: Количество заявок (без учёта заголовка).
        """
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return sum(1 for _ in f) - 1  # Минус заголовок
        except Exception as e:
            logger.error(f"Ошибка подсчёта заявок: {e}")
            return 0

    def get_file_path(self) -> Path:
        """
        Возвращает путь к CSV-файлу.

        Returns:
            Path: Путь к файлу.
        """
        return self.file_path


# Глобальный экземпляр обработчика
csv_handler = CSVHandler()
