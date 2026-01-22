"""
Модуль конфигурации приложения.

Использует Pydantic Settings для загрузки и валидации
переменных окружения из файла .env.
"""

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram Bot
    bot_token: str
    admin_id: int

    # Logging
    log_level: str = "INFO"

    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = base_dir / "data"
    logs_dir: Path = base_dir / "logs"
    csv_file: Path = data_dir / "applications.csv"
    log_file: Path = logs_dir / "bot.log"

    # Anti-flood settings
    throttle_rate: float = 0.5

    @field_validator("bot_token")
    @classmethod
    def validate_bot_token(cls, v: str) -> str:
        """Проверяет формат токена бота."""
        if not v or ":" not in v:
            raise ValueError("Некорректный формат BOT_TOKEN")
        return v

    @field_validator("admin_id")
    @classmethod
    def validate_admin_id(cls, v: int) -> int:
        """Проверяет корректность ADMIN_ID."""
        if v <= 0:
            raise ValueError("ADMIN_ID должен быть положительным числом")
        return v

    def ensure_directories(self) -> None:
        """Создаёт необходимые директории, если они не существуют."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    """
    Фабрика для получения настроек.

    Returns:
        Settings: Объект с настройками приложения.
    """
    return Settings()


settings = get_settings()
