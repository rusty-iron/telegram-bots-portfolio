"""
Контейнер внедрения зависимостей для MeatBot
"""

import inspect
from typing import Any, Callable, Dict, Type, TypeVar

T = TypeVar("T")


class DIContainer:
    """Простой контейнер внедрения зависимостей"""

    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._singletons: Dict[Type, Any] = {}

    def register_singleton(
        self, interface: Type[T], implementation: Type[T]
    ) -> None:
        """Регистрирует singleton сервис"""
        self._services[interface] = implementation
        self._singletons[interface] = None

    def register_transient(
        self, interface: Type[T], implementation: Type[T]
    ) -> None:
        """Регистрирует transient сервис"""
        self._services[interface] = implementation

    def register_factory(
        self, interface: Type[T], factory: Callable[[], T]
    ) -> None:
        """Регистрирует фабрику для создания сервиса"""
        self._factories[interface] = factory

    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Регистрирует готовый экземпляр"""
        self._services[interface] = instance
        self._singletons[interface] = instance

    def get(self, interface: Type[T]) -> T:
        """Получает экземпляр сервиса"""
        # Проверяем готовые экземпляры
        if (
            interface in self._singletons
            and self._singletons[interface] is not None
        ):
            return self._singletons[interface]

        # Проверяем фабрики
        if interface in self._factories:
            instance = self._factories[interface]()
            if interface in self._singletons:
                self._singletons[interface] = instance
            return instance

        # Проверяем зарегистрированные классы
        if interface in self._services:
            implementation = self._services[interface]

            # Если это уже экземпляр
            if not inspect.isclass(implementation):
                if interface in self._singletons:
                    self._singletons[interface] = implementation
                return implementation

            # Создаем новый экземпляр
            instance = self._create_instance(implementation)

            # Сохраняем как singleton если нужно
            if interface in self._singletons:
                self._singletons[interface] = instance

            return instance

        raise ValueError(f"Service {interface} not registered")

    def _create_instance(self, implementation: Type[T]) -> T:
        """Создает экземпляр с автоматическим внедрением зависимостей"""
        try:
            # Получаем сигнатуру конструктора
            signature = inspect.signature(implementation.__init__)
            kwargs = {}

            # Заполняем параметры
            for param_name, param in signature.parameters.items():
                if param_name == "self":
                    continue

                # Пытаемся получить зависимость из контейнера
                if param.annotation != inspect.Parameter.empty:
                    try:
                        kwargs[param_name] = self.get(param.annotation)
                    except ValueError:
                        # Если зависимость не найдена, используем значение по
                        # умолчанию
                        if param.default != inspect.Parameter.empty:
                            kwargs[param_name] = param.default
                        else:
                            raise ValueError(
                                f"Cannot resolve dependency {param_name} for {implementation}"
                            )

            return implementation(**kwargs)
        except Exception as e:
            raise ValueError(
                f"Failed to create instance of {implementation}: {e}"
            )

    def is_registered(self, interface: Type[T]) -> bool:
        """Проверяет, зарегистрирован ли сервис"""
        return interface in self._services or interface in self._factories

    def clear(self) -> None:
        """Очищает контейнер"""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()


# Глобальный контейнер
container = DIContainer()


def inject(interface: Type[T]) -> T:
    """Декоратор для внедрения зависимостей"""
    return container.get(interface)


def register_singleton(interface: Type[T], implementation: Type[T]) -> None:
    """Удобная функция для регистрации singleton"""
    container.register_singleton(interface, implementation)


def register_transient(interface: Type[T], implementation: Type[T]) -> None:
    """Удобная функция для регистрации transient"""
    container.register_transient(interface, implementation)


def register_factory(interface: Type[T], factory: Callable[[], T]) -> None:
    """Удобная функция для регистрации фабрики"""
    container.register_factory(interface, factory)


def register_instance(interface: Type[T], instance: T) -> None:
    """Удобная функция для регистрации экземпляра"""
    container.register_instance(interface, instance)


def get_service(interface: Type[T]) -> T:
    """Удобная функция для получения сервиса"""
    return container.get(interface)
