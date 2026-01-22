"""
Расширенный модуль для работы с CSV-файлом заявок.

Обеспечивает полный CRUD для заявок: чтение, фильтрация,
обновление статусов, удаление, пагинация.
"""

import csv
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from src.config import settings

logger = logging.getLogger(__name__)


class LeadStatus(str, Enum):
    """Статусы заявок."""

    NEW = "Новая"
    IN_PROGRESS = "В работе"
    COMPLETED = "Завершена"

    @classmethod
    def get_emoji(cls, status: str) -> str:
        """Возвращает эмодзи для статуса."""
        emoji_map = {
            cls.NEW: "🆕",
            cls.IN_PROGRESS: "⏳",
            cls.COMPLETED: "✅",
        }
        return emoji_map.get(status, "❓")


# Новые заголовки CSV с поддержкой статусов
CSV_HEADERS_V2 = [
    "timestamp", "user_id", "name", "phone",
    "email", "message", "status", "updated_at"
]

# Старые заголовки (для миграции)
CSV_HEADERS_V1 = ["timestamp", "user_id", "name", "phone", "email", "message"]


@dataclass
class Lead:
    """Модель заявки."""

    row_index: int  # Индекс строки в файле (для обновления/удаления)
    timestamp: str
    user_id: int
    name: str
    phone: str
    email: str
    message: str
    status: str
    updated_at: str

    @property
    def lead_id(self) -> int:
        """ID заявки (равен row_index + 1 для человекочитаемости)."""
        return self.row_index + 1

    @property
    def short_name(self) -> str:
        """Сокращённое имя (Имя Ф.)."""
        parts = self.name.split()
        if len(parts) >= 2:
            return f"{parts[0]} {parts[1][0]}."
        return self.name

    @property
    def short_phone(self) -> str:
        """Сокращённый телефон (+7999...)."""
        if len(self.phone) > 7:
            return f"{self.phone[:7]}..."
        return self.phone

    @property
    def short_email(self) -> str:
        """Сокращённый email (user@...)."""
        if "@" in self.email:
            local, domain = self.email.split("@", 1)
            if len(local) > 6:
                return f"{local[:6]}...@{domain[:5]}..."
            return f"{local}@..."
        return self.email

    @property
    def formatted_date(self) -> str:
        """Форматированная дата (DD.MM HH:MM)."""
        try:
            dt = datetime.strptime(self.timestamp, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d.%m %H:%M")
        except ValueError:
            return self.timestamp

    @property
    def formatted_full_date(self) -> str:
        """Полная форматированная дата (DD.MM.YYYY HH:MM)."""
        try:
            dt = datetime.strptime(self.timestamp, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d.%m.%Y %H:%M")
        except ValueError:
            return self.timestamp

    @property
    def formatted_updated_at(self) -> str:
        """Форматированная дата обновления."""
        if not self.updated_at or self.updated_at == "—":
            return self.formatted_full_date
        try:
            dt = datetime.strptime(self.updated_at, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d.%m.%Y %H:%M")
        except ValueError:
            return self.updated_at

    @property
    def status_emoji(self) -> str:
        """Эмодзи статуса."""
        return LeadStatus.get_emoji(self.status)


class CSVManager:
    """Менеджер для работы с CSV-файлом заявок."""

    def __init__(self, file_path: Optional[Path] = None) -> None:
        """
        Инициализирует менеджер CSV.

        Args:
            file_path: Путь к CSV-файлу. По умолчанию из настроек.
        """
        self.file_path = file_path or settings.csv_file
        self._ensure_file_exists()
        self._migrate_if_needed()

    def _ensure_file_exists(self) -> None:
        """Создаёт CSV-файл с заголовками, если он не существует."""
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(CSV_HEADERS_V2)
            logger.info(f"Создан CSV-файл: {self.file_path}")

    def _migrate_if_needed(self) -> None:
        """Проверяет и мигрирует старый формат CSV в новый."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                headers = next(reader, None)

                if headers is None:
                    return

                # Если уже новый формат - ничего не делаем
                if "status" in headers and "updated_at" in headers:
                    return

                # Читаем все данные
                rows = list(reader)

            # Мигрируем данные
            logger.info("Миграция CSV в новый формат со статусами...")

            with open(self.file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(CSV_HEADERS_V2)

                for row in rows:
                    if len(row) >= 6:
                        # Добавляем status="Новая" и updated_at
                        new_row = row[:6] + [LeadStatus.NEW.value, row[0]]
                        writer.writerow(new_row)

            logger.info(f"Миграция завершена. Обновлено {len(rows)} записей")

        except Exception as e:
            logger.error(f"Ошибка миграции CSV: {e}")

    def get_all_leads(self) -> list[Lead]:
        """
        Возвращает все заявки.

        Returns:
            list[Lead]: Список всех заявок от новых к старым.
        """
        leads = []

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for idx, row in enumerate(reader):
                    lead = self._row_to_lead(idx, row)
                    if lead:
                        leads.append(lead)

            # Сортируем от новых к старым
            leads.sort(key=lambda x: x.timestamp, reverse=True)

        except Exception as e:
            logger.error(f"Ошибка чтения заявок: {e}")

        return leads

    def get_leads_by_status(self, status: str) -> list[Lead]:
        """
        Возвращает заявки с определённым статусом.

        Args:
            status: Статус для фильтрации.

        Returns:
            list[Lead]: Список заявок с указанным статусом.
        """
        all_leads = self.get_all_leads()
        return [lead for lead in all_leads if lead.status == status]

    def get_lead_by_id(self, lead_id: int) -> Optional[Lead]:
        """
        Возвращает заявку по ID.

        Args:
            lead_id: ID заявки (row_index + 1).

        Returns:
            Optional[Lead]: Заявка или None если не найдена.
        """
        all_leads = self.get_all_leads()
        for lead in all_leads:
            if lead.lead_id == lead_id:
                return lead
        return None

    def get_stats(self) -> dict[str, int]:
        """
        Возвращает статистику по заявкам.

        Returns:
            dict: Словарь со статистикой {all, new, in_progress, completed}.
        """
        all_leads = self.get_all_leads()

        stats = {
            "all": len(all_leads),
            "new": sum(1 for l in all_leads if l.status == LeadStatus.NEW.value),
            "in_progress": sum(1 for l in all_leads if l.status == LeadStatus.IN_PROGRESS.value),
            "completed": sum(1 for l in all_leads if l.status == LeadStatus.COMPLETED.value),
        }

        return stats

    def update_lead_status(self, lead_id: int, new_status: str) -> bool:
        """
        Обновляет статус заявки.

        Args:
            lead_id: ID заявки.
            new_status: Новый статус.

        Returns:
            bool: True если обновление успешно.
        """
        try:
            # Читаем все данные
            with open(self.file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                headers = next(reader)
                rows = list(reader)

            # Находим и обновляем нужную строку
            # lead_id = row_index + 1, но row_index относится к отсортированным данным
            # Нам нужно найти строку по оригинальному row_index
            lead = self.get_lead_by_id(lead_id)
            if not lead:
                logger.error(f"Заявка #{lead_id} не найдена")
                return False

            # Ищем строку с соответствующими данными
            found = False
            for i, row in enumerate(rows):
                if len(row) >= 6:
                    if (row[0] == lead.timestamp and
                        row[1] == str(lead.user_id) and
                        row[2] == lead.name):
                        # Обновляем статус и updated_at
                        if len(row) >= 8:
                            row[6] = new_status
                            row[7] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            row.extend([
                                new_status,
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ])
                        found = True
                        break

            if not found:
                logger.error(f"Не удалось найти строку для заявки #{lead_id}")
                return False

            # Записываем обратно
            with open(self.file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(CSV_HEADERS_V2)
                writer.writerows(rows)

            logger.info(f"Статус заявки #{lead_id} изменён на '{new_status}'")
            return True

        except Exception as e:
            logger.error(f"Ошибка обновления статуса: {e}")
            return False

    def delete_lead(self, lead_id: int) -> bool:
        """
        Удаляет заявку.

        Args:
            lead_id: ID заявки.

        Returns:
            bool: True если удаление успешно.
        """
        try:
            lead = self.get_lead_by_id(lead_id)
            if not lead:
                logger.error(f"Заявка #{lead_id} не найдена для удаления")
                return False

            # Читаем все данные
            with open(self.file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                headers = next(reader)
                rows = list(reader)

            # Находим и удаляем строку
            new_rows = []
            deleted = False

            for row in rows:
                if len(row) >= 6:
                    if (row[0] == lead.timestamp and
                        row[1] == str(lead.user_id) and
                        row[2] == lead.name and not deleted):
                        deleted = True
                        continue
                new_rows.append(row)

            if not deleted:
                logger.error(f"Строка заявки #{lead_id} не найдена")
                return False

            # Записываем обратно
            with open(self.file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(CSV_HEADERS_V2)
                writer.writerows(new_rows)

            logger.info(f"Заявка #{lead_id} удалена")
            return True

        except Exception as e:
            logger.error(f"Ошибка удаления заявки: {e}")
            return False

    def _row_to_lead(self, idx: int, row: dict) -> Optional[Lead]:
        """
        Преобразует строку CSV в объект Lead.

        Args:
            idx: Индекс строки.
            row: Словарь с данными строки.

        Returns:
            Optional[Lead]: Объект Lead или None при ошибке.
        """
        try:
            # Обрабатываем старый формат (без status/updated_at)
            status = row.get("status", LeadStatus.NEW.value)
            if not status:
                status = LeadStatus.NEW.value

            updated_at = row.get("updated_at", row.get("timestamp", ""))
            if not updated_at:
                updated_at = row.get("timestamp", "")

            return Lead(
                row_index=idx,
                timestamp=row.get("timestamp", ""),
                user_id=int(row.get("user_id", 0)),
                name=row.get("name", ""),
                phone=row.get("phone", ""),
                email=row.get("email", ""),
                message=row.get("message", ""),
                status=status,
                updated_at=updated_at,
            )
        except (ValueError, KeyError) as e:
            logger.error(f"Ошибка парсинга строки {idx}: {e}")
            return None

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

    def get_file_path(self) -> Path:
        """
        Возвращает путь к CSV-файлу.

        Returns:
            Path: Путь к файлу.
        """
        return self.file_path


# Глобальный экземпляр менеджера
csv_manager = CSVManager()
