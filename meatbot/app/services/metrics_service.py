"""
Сервис метрик для MeatBot
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import structlog

from ..interfaces import IConfigService

logger = structlog.get_logger()


class MetricsService:
    """Сервис для сбора и анализа метрик"""

    def __init__(self, config_service: IConfigService):
        self.config = config_service
        self._metrics: Dict[str, Any] = {}
        self._start_time = datetime.utcnow()

    def increment_counter(
        self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Увеличить счетчик"""
        key = self._build_key(name, tags)
        if key not in self._metrics:
            self._metrics[key] = {"type": "counter", "value": 0}
        self._metrics[key]["value"] += value

        logger.info("metric_counter", name=name, value=value, tags=tags)

    def set_gauge(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Установить значение gauge"""
        key = self._build_key(name, tags)
        self._metrics[key] = {"type": "gauge", "value": value}

        logger.info("metric_gauge", name=name, value=value, tags=tags)

    def record_timing(
        self, name: str, duration: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Записать время выполнения"""
        key = self._build_key(name, tags)
        if key not in self._metrics:
            self._metrics[key] = {"type": "timing", "values": []}
        self._metrics[key]["values"].append(duration)

        # Оставляем только последние 100 значений
        if len(self._metrics[key]["values"]) > 100:
            self._metrics[key]["values"] = self._metrics[key]["values"][-100:]

        logger.info("metric_timing", name=name, duration=duration, tags=tags)

    def get_metric(
        self, name: str, tags: Optional[Dict[str, str]] = None
    ) -> Optional[Any]:
        """Получить метрику"""
        key = self._build_key(name, tags)
        return self._metrics.get(key)

    def get_all_metrics(self) -> Dict[str, Any]:
        """Получить все метрики"""
        return self._metrics.copy()

    def get_summary(self) -> Dict[str, Any]:
        """Получить сводку метрик"""
        uptime = (datetime.utcnow() - self._start_time).total_seconds()

        summary = {
            "uptime_seconds": uptime,
            "uptime_human": str(timedelta(seconds=int(uptime))),
            "total_metrics": len(self._metrics),
            "start_time": self._start_time.isoformat(),
        }

        # Анализируем метрики
        counters = {}
        gauges = {}
        timings = {}

        for key, metric in self._metrics.items():
            if metric["type"] == "counter":
                counters[key] = metric["value"]
            elif metric["type"] == "gauge":
                gauges[key] = metric["value"]
            elif metric["type"] == "timing":
                values = metric["values"]
                if values:
                    timings[key] = {
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "p95": sorted(values)[int(len(values) * 0.95)]
                        if len(values) > 1
                        else values[0],
                    }

        summary["counters"] = counters
        summary["gauges"] = gauges
        summary["timings"] = timings

        return summary

    def _build_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """Построить ключ для метрики"""
        if not tags:
            return name

        tag_parts = [f"{k}={v}" for k, v in sorted(tags.items())]
        return f"{name}[{','.join(tag_parts)}]"

    def reset(self) -> None:
        """Сбросить все метрики"""
        self._metrics.clear()
        self._start_time = datetime.utcnow()
        logger.info("metrics_reset")


class TimingContext:
    """Контекстный менеджер для измерения времени"""

    def __init__(
        self,
        metrics_service: MetricsService,
        name: str,
        tags: Optional[Dict[str, str]] = None,
    ):
        self.metrics_service = metrics_service
        self.name = name
        self.tags = tags
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.metrics_service.record_timing(self.name, duration, self.tags)


# Глобальный экземпляр метрик
_metrics_service: Optional[MetricsService] = None


def get_metrics_service() -> Optional[MetricsService]:
    """Получить глобальный сервис метрик"""
    return _metrics_service


def init_metrics_service(config_service: IConfigService) -> MetricsService:
    """Инициализировать глобальный сервис метрик"""
    global _metrics_service
    _metrics_service = MetricsService(config_service)
    return _metrics_service


def timing(name: str, tags: Optional[Dict[str, str]] = None):
    """Декоратор для измерения времени выполнения функции"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            metrics_service = get_metrics_service()
            if metrics_service:
                with TimingContext(metrics_service, name, tags):
                    return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        return wrapper

    return decorator


def counter(name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
    """Декоратор для подсчета вызовов функции"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            metrics_service = get_metrics_service()
            if metrics_service:
                metrics_service.increment_counter(name, value, tags)
            return func(*args, **kwargs)

        return wrapper

    return decorator
