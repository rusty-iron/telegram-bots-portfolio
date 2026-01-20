from __future__ import annotations

import os

from sqlalchemy import engine_from_config, pool

from alembic import context

# Импортируем модели для создания метаданных
from meatbot.app.database import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Skip Alembic logging configuration to avoid missing 'formatters' errors

# Override sqlalchemy.url from environment variables
database_url = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@db:5432/meatbot"
)
config.set_main_option("sqlalchemy.url", database_url)

# Устанавливаем метаданные из наших моделей
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
