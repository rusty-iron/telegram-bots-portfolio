"""
Сервис мониторинга безопасности
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import structlog

logger = structlog.get_logger()


class SecurityEvent:
    """Событие безопасности"""

    def __init__(
        self,
        event_type: str,
        user_id: int,
        description: str,
        severity: str = "info",
        metadata: Optional[Dict] = None,
    ) -> None:
        self.event_type = event_type
        self.user_id = user_id
        self.description = description
        self.severity = severity  # info, warning, critical
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        return {
            "event_type": self.event_type,
            "user_id": self.user_id,
            "description": self.description,
            "severity": self.severity,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class SecurityMonitor:
    """
    Мониторинг безопасности и подозрительной активности

    Отслеживает:
    - Попытки injection атак
    - Множественные неудачные попытки
    - Подозрительные паттерны ввода
    - Rate limiting нарушения
    """

    def __init__(self) -> None:
        # История событий: {user_id: [SecurityEvent, ...]}
        self._events: Dict[int, List[SecurityEvent]] = defaultdict(list)

        # Счетчики по типам событий
        self._event_counters: Dict[str, int] = defaultdict(int)

        # Заблокированные пользователи
        self._blocked_users: Dict[int, datetime] = {}

        # Настройки
        self.max_events_per_user: int = 100  # Максимум событий на пользователя
        self.event_retention_hours: int = 24  # Сколько часов хранить события
        self.critical_threshold: int = 5  # Критических событий для блокировки

    def log_event(
        self,
        event_type: str,
        user_id: int,
        description: str,
        severity: str = "info",
        metadata: Optional[Dict] = None,
    ) -> None:
        """Логирует событие безопасности"""
        event = SecurityEvent(
            event_type=event_type,
            user_id=user_id,
            description=description,
            severity=severity,
            metadata=metadata,
        )

        # Добавляем в историю
        self._events[user_id].append(event)
        self._event_counters[event_type] += 1

        # Ограничиваем количество событий на пользователя
        if len(self._events[user_id]) > self.max_events_per_user:
            self._events[user_id] = self._events[user_id][
                -self.max_events_per_user :
            ]

        # Логируем
        log_func = logger.info
        if severity == "warning":
            log_func = logger.warning
        elif severity == "critical":
            log_func = logger.error

        log_func(
            f"security_event_{event_type}",
            user_id=user_id,
            severity=severity,
            description=description,
            metadata=metadata,
        )

        # Проверяем на критические события
        if severity == "critical":
            self._check_for_blocking(user_id)

    def log_injection_attempt(
        self,
        user_id: int,
        input_text: str,
        detected_pattern: str,
        field_name: str,
    ) -> None:
        """Логирует попытку injection атаки"""
        self.log_event(
            event_type="injection_attempt",
            user_id=user_id,
            description=f"Detected {detected_pattern} in {field_name}",
            severity="critical",
            metadata={
                "input_text": input_text[:200],  # Ограничиваем длину
                "detected_pattern": detected_pattern,
                "field_name": field_name,
            },
        )

    def log_xss_attempt(
        self,
        user_id: int,
        input_text: str,
        field_name: str,
    ) -> None:
        """Логирует попытку XSS атаки"""
        self.log_event(
            event_type="xss_attempt",
            user_id=user_id,
            description=f"XSS pattern detected in {field_name}",
            severity="critical",
            metadata={
                "input_text": input_text[:200],
                "field_name": field_name,
            },
        )

    def log_validation_error(
        self,
        user_id: int,
        field_name: str,
        error_message: str,
        input_value: str,
    ) -> None:
        """Логирует ошибку валидации"""
        self.log_event(
            event_type="validation_error",
            user_id=user_id,
            description=f"Validation failed for {field_name}: {error_message}",
            severity="warning",
            metadata={
                "field_name": field_name,
                "error_message": error_message,
                "input_value": input_value[:100],
            },
        )

    def log_rate_limit_violation(
        self,
        user_id: int,
        request_count: int,
        limit: int,
    ) -> None:
        """Логирует нарушение rate limit"""
        self.log_event(
            event_type="rate_limit_violation",
            user_id=user_id,
            description=f"Rate limit exceeded: {request_count}/{limit}",
            severity="warning",
            metadata={
                "request_count": request_count,
                "limit": limit,
            },
        )

    def log_suspicious_activity(
        self,
        user_id: int,
        activity_type: str,
        description: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Логирует подозрительную активность"""
        self.log_event(
            event_type=f"suspicious_{activity_type}",
            user_id=user_id,
            description=description,
            severity="warning",
            metadata=metadata,
        )

    def _check_for_blocking(self, user_id: int) -> None:
        """Проверяет, нужно ли заблокировать пользователя"""
        # Считаем критические события за последний час
        cutoff_time = datetime.now() - timedelta(hours=1)
        recent_critical = [
            event
            for event in self._events[user_id]
            if event.severity == "critical" and event.timestamp > cutoff_time
        ]

        if len(recent_critical) >= self.critical_threshold:
            self._block_user(user_id, hours=24)

    def _block_user(self, user_id: int, hours: int = 24) -> None:
        """Блокирует пользователя"""
        block_until = datetime.now() + timedelta(hours=hours)
        self._blocked_users[user_id] = block_until

        logger.error(
            "user_blocked_for_security",
            user_id=user_id,
            block_until=block_until.isoformat(),
            hours=hours,
        )

    def is_user_blocked(self, user_id: int) -> bool:
        """Проверяет, заблокирован ли пользователь"""
        if user_id not in self._blocked_users:
            return False

        block_until = self._blocked_users[user_id]
        if datetime.now() > block_until:
            # Блокировка истекла
            del self._blocked_users[user_id]
            return False

        return True

    def unblock_user(self, user_id: int) -> None:
        """Разблокирует пользователя"""
        if user_id in self._blocked_users:
            del self._blocked_users[user_id]
            logger.info("user_unblocked", user_id=user_id)

    def get_user_events(
        self,
        user_id: int,
        hours: Optional[int] = None,
        severity: Optional[str] = None,
    ) -> List[SecurityEvent]:
        """Получает события пользователя"""
        events = self._events.get(user_id, [])

        if hours:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            events = [e for e in events if e.timestamp > cutoff_time]

        if severity:
            events = [e for e in events if e.severity == severity]

        return events

    def get_statistics(self) -> Dict:
        """Возвращает статистику безопасности"""
        total_events = sum(len(events) for events in self._events.values())

        # Считаем по уровням severity
        severity_counts = {"info": 0, "warning": 0, "critical": 0}
        for events in self._events.values():
            for event in events:
                severity_counts[event.severity] += 1

        # Топ пользователей по событиям
        top_users = sorted(
            [
                (user_id, len(events))
                for user_id, events in self._events.items()
            ],
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        return {
            "total_events": total_events,
            "total_users": len(self._events),
            "blocked_users": len(self._blocked_users),
            "severity_counts": severity_counts,
            "event_type_counts": dict(self._event_counters),
            "top_users_by_events": top_users,
        }

    def cleanup_old_events(self) -> None:
        """Очищает старые события"""
        cutoff_time = datetime.now() - timedelta(
            hours=self.event_retention_hours
        )

        for user_id in list(self._events.keys()):
            self._events[user_id] = [
                event
                for event in self._events[user_id]
                if event.timestamp > cutoff_time
            ]

            # Удаляем пользователя, если нет событий
            if not self._events[user_id]:
                del self._events[user_id]

        logger.info("security_events_cleaned_up")


# Глобальный экземпляр монитора
security_monitor = SecurityMonitor()
