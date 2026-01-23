"""
Модуль поиска по FAQ.
"""

from dataclasses import dataclass
from typing import Optional
import re
import logging

from utils.faq_loader import FAQData

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Результат поиска."""

    category: str
    question: str
    answer: str
    score: float


class FAQSearch:
    """Поиск по FAQ с ранжированием результатов."""

    MIN_QUERY_LENGTH = 2
    MAX_RESULTS = 5

    def __init__(self, faq_data: FAQData):
        self.faq_data = faq_data

    def update_data(self, faq_data: FAQData) -> None:
        """Обновление данных FAQ для поиска."""
        self.faq_data = faq_data

    def search(self, query: str, max_results: Optional[int] = None) -> list[SearchResult]:
        """
        Поиск по FAQ.

        Args:
            query: Поисковый запрос
            max_results: Максимальное количество результатов

        Returns:
            Список результатов поиска, отсортированных по релевантности
        """
        if not query or len(query.strip()) < self.MIN_QUERY_LENGTH:
            return []

        max_results = max_results or self.MAX_RESULTS
        query = query.strip().lower()
        query_words = set(self._tokenize(query))

        if not query_words:
            return []

        results: list[SearchResult] = []

        for category, questions in self.faq_data.items():
            for question, answer in questions.items():
                score = self._calculate_score(query, query_words, question, answer)

                if score > 0:
                    results.append(
                        SearchResult(
                            category=category,
                            question=question,
                            answer=answer,
                            score=score,
                        )
                    )

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:max_results]

    def _tokenize(self, text: str) -> list[str]:
        """Токенизация текста."""
        text = text.lower()
        words = re.findall(r"\b\w+\b", text, re.UNICODE)
        return [w for w in words if len(w) >= 2]

    def _calculate_score(
        self, query: str, query_words: set[str], question: str, answer: str
    ) -> float:
        """Расчет релевантности результата."""
        score = 0.0
        question_lower = question.lower()
        answer_lower = answer.lower()

        if query in question_lower:
            score += 10.0

        if query in answer_lower:
            score += 3.0

        question_words = set(self._tokenize(question))
        answer_words = set(self._tokenize(answer))

        question_matches = len(query_words & question_words)
        if question_matches:
            score += question_matches * 2.0

        answer_matches = len(query_words & answer_words)
        if answer_matches:
            score += answer_matches * 0.5

        if question_words:
            coverage = question_matches / len(question_words)
            score += coverage * 3.0

        return score

    def get_suggestions(self, partial_query: str) -> list[str]:
        """Получение подсказок для автодополнения."""
        if len(partial_query) < 2:
            return []

        partial_lower = partial_query.lower()
        suggestions = set()

        for category, questions in self.faq_data.items():
            for question in questions.keys():
                if partial_lower in question.lower():
                    suggestions.add(question)

        return list(suggestions)[:5]
