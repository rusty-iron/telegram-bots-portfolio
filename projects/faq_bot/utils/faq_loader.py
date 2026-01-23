"""
Модуль для загрузки и управления FAQ данными.
"""

import json
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

FAQData = dict[str, dict[str, str]]


class FAQLoader:
    """Загрузчик FAQ данных из JSON файла."""

    def __init__(self, faq_path: Path):
        self.faq_path = faq_path
        self._data: FAQData = {}

    def load(self) -> FAQData:
        """Загрузка FAQ из файла."""
        if not self.faq_path.exists():
            logger.warning(f"Файл FAQ не найден: {self.faq_path}")
            self._data = {}
            return self._data

        try:
            with open(self.faq_path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
            logger.info(f"FAQ загружен: {len(self._data)} категорий")
            return self._data
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга FAQ JSON: {e}")
            self._data = {}
            return self._data
        except Exception as e:
            logger.error(f"Ошибка загрузки FAQ: {e}")
            self._data = {}
            return self._data

    def save(self, data: FAQData) -> bool:
        """Сохранение FAQ в файл."""
        try:
            with open(self.faq_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._data = data
            logger.info(f"FAQ сохранен: {len(data)} категорий")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения FAQ: {e}")
            return False

    @property
    def data(self) -> FAQData:
        """Получение текущих данных FAQ."""
        return self._data

    def get_categories(self) -> list[str]:
        """Получение списка категорий."""
        return list(self._data.keys())

    def get_questions(self, category: str) -> dict[str, str]:
        """Получение вопросов категории."""
        return self._data.get(category, {})

    def get_answer(self, category: str, question: str) -> Optional[str]:
        """Получение ответа на вопрос."""
        return self._data.get(category, {}).get(question)

    def validate_json(self, data: dict) -> tuple[bool, Optional[str]]:
        """Валидация структуры FAQ JSON."""
        if not isinstance(data, dict):
            return False, "FAQ должен быть объектом"

        if not data:
            return False, "FAQ пустой"

        for category, questions in data.items():
            if not isinstance(category, str):
                return False, f"Название категории должно быть строкой"

            if not isinstance(questions, dict):
                return False, f"Категория '{category}' должна содержать объект с вопросами"

            if not questions:
                return False, f"Категория '{category}' пуста"

            for question, answer in questions.items():
                if not isinstance(question, str):
                    return False, f"Вопрос в категории '{category}' должен быть строкой"

                if not isinstance(answer, str):
                    return False, f"Ответ на '{question}' должен быть строкой"

                if not answer.strip():
                    return False, f"Ответ на '{question}' пустой"

        return True, None

    def reload(self) -> FAQData:
        """Перезагрузка FAQ из файла."""
        return self.load()

    def export_json(self) -> str:
        """Экспорт FAQ в JSON строку."""
        return json.dumps(self._data, ensure_ascii=False, indent=2)
