"""
Конфигурация FAQ бота.
Загружает настройки из переменных окружения.
"""

import os
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Config:
    """Конфигурация приложения."""

    bot_token: str
    admin_id: int
    support_username: str
    base_dir: Path
    data_dir: Path
    faq_file: Path
    db_file: Path

    @classmethod
    def from_env(cls) -> "Config":
        """Создает конфигурацию из переменных окружения."""
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            raise ValueError("BOT_TOKEN не установлен")

        admin_id_str = os.getenv("ADMIN_ID")
        if not admin_id_str:
            raise ValueError("ADMIN_ID не установлен")

        try:
            admin_id = int(admin_id_str)
        except ValueError:
            raise ValueError("ADMIN_ID должен быть числом")

        support_username = os.getenv("SUPPORT_USERNAME", "support")

        base_dir = Path(__file__).parent
        data_dir = base_dir / "data"
        data_dir.mkdir(exist_ok=True)

        return cls(
            bot_token=bot_token,
            admin_id=admin_id,
            support_username=support_username,
            base_dir=base_dir,
            data_dir=data_dir,
            faq_file=data_dir / "faq.json",
            db_file=data_dir / "stats.db",
        )


def get_config() -> Config:
    """Получает конфигурацию приложения."""
    return Config.from_env()
