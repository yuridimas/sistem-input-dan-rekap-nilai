"""Hubungkan CLI Alembic dengan konfigurasi dan metadata model.

Mode offline menghasilkan SQL; mode online menerapkan revisi melalui
koneksi async.
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.config import get_settings
from app.models import Base
import app.models.class_  # noqa: F401
import app.models.course  # noqa: F401
import app.models.enrollment  # noqa: F401
import app.models.student  # noqa: F401
import app.models.user  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Susun SQL migration tanpa koneksi database.

    Error revisi diteruskan ke CLI.

    Menjalankan context offline.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Terapkan revisi pada koneksi sinkron Alembic.

    Perubahan schema sesuai revisi dalam transaksi; exception
    diteruskan.

    Args:
        connection: Koneksi sinkron yang dipinjam dari engine async
            Alembic.
    """
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Buka koneksi tanpa pool lalu jembatani operasi Alembic sinkron.

    Menerapkan schema; engine di-dispose setelah jalur sukses.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Sediakan event loop untuk entrypoint migration CLI sinkron.

    Menjalankan migration DB; error koneksi/revisi diteruskan.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()