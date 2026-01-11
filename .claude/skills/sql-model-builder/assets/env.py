"""
Alembic Migration Environment Template

This template supports both sync and async database engines.
Uncomment the appropriate section based on your setup.
"""

import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import os

# Import your Base and models here
# Example:
# from app.database.base import Base
# from app.models import *  # Import all model modules

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate support
# Replace with your Base.metadata
target_metadata = None  # Replace: target_metadata = Base.metadata

# Override database URL from environment variable
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)


# ============================================================================
# OFFLINE MODE (Generate SQL scripts without database connection)
# ============================================================================

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine.
    Calls to context.execute() here emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ============================================================================
# SYNCHRONOUS MODE (For sync SQLAlchemy engines)
# ============================================================================

def run_migrations_sync() -> None:
    """Run migrations in 'online' mode with synchronous engine."""
    from sqlalchemy import engine_from_config

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


# ============================================================================
# ASYNCHRONOUS MODE (For async SQLAlchemy engines)
# ============================================================================

def do_run_migrations(connection: Connection) -> None:
    """Execute migrations within a connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations asynchronously."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_async() -> None:
    """Run migrations in 'online' mode with async engine."""
    asyncio.run(run_async_migrations())


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if context.is_offline_mode():
    # Generate SQL scripts without database connection
    run_migrations_offline()
else:
    # Choose sync or async mode based on your database setup
    # Uncomment the appropriate line:

    # For synchronous engines (sync drivers):
    # run_migrations_sync()

    # For asynchronous engines (async drivers like asyncpg, aiomysql):
    run_migrations_async()
