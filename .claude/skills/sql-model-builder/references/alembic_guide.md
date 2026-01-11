# Alembic Migration Guide

Complete guide for database schema migrations using Alembic with SQLAlchemy 2.x.

## Installation and Setup

```bash
# Install Alembic
pip install alembic

# Initialize Alembic in your project
alembic init alembic

# This creates:
# alembic/
#   ├── env.py           # Migration environment configuration
#   ├── script.py.mako   # Migration template
#   └── versions/        # Migration files
# alembic.ini            # Alembic configuration
```

## Configuration

### alembic.ini

```ini
[alembic]
# Path to migration scripts
script_location = alembic

# Database URL (can use environment variable)
sqlalchemy.url = postgresql://user:password@localhost:5432/dbname

# Or use driver name from env
# sqlalchemy.url = driver://user:pass@localhost/dbname

# Timezone
timezone = UTC

# File naming pattern
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

### env.py (Sync Configuration)

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os

# Import your Base metadata
from app.database.base import Base
from app.models import *  # Import all models

# Alembic Config object
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata
target_metadata = Base.metadata

# Get database URL from environment
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generate SQL scripts)."""
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


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connect to database)."""
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


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### env.py (Async Configuration)

```python
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import os

from app.database.base import Base
from app.models import *

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """Run migrations asynchronously."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## Creating Migrations

### Auto-Generate Migrations

```bash
# Create a new migration (auto-detect changes)
alembic revision --autogenerate -m "add users table"

# This compares your models to the database and generates migration code
```

### Manual Migration

```bash
# Create an empty migration
alembic revision -m "add custom index"
```

### Migration File Structure

```python
"""add users table

Revision ID: abc123
Revises: xyz789
Create Date: 2024-01-10 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = 'abc123'
down_revision = 'xyz789'  # Previous migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply migration (forward)."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_email', 'users', ['email'])


def downgrade() -> None:
    """Revert migration (backward)."""
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
```

## Common Migration Operations

### Create Table

```python
def upgrade():
    op.create_table(
        'posts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text()),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
    )
```

### Add Column

```python
def upgrade():
    op.add_column('users', sa.Column('is_active', sa.Boolean(), default=True))

    # Add column with default value for existing rows
    op.add_column(
        'users',
        sa.Column('login_count', sa.Integer(), server_default='0', nullable=False)
    )
```

### Modify Column

```python
def upgrade():
    # Change column type
    op.alter_column('users', 'age', type_=sa.SmallInteger())

    # Rename column
    op.alter_column('users', 'name', new_column_name='username')

    # Make column nullable
    op.alter_column('users', 'email', nullable=True)

    # Change column default
    op.alter_column('users', 'is_active', server_default='true')
```

### Drop Column

```python
def upgrade():
    op.drop_column('users', 'old_field')

def downgrade():
    op.add_column('users', sa.Column('old_field', sa.String(50)))
```

### Add Index

```python
def upgrade():
    # Simple index
    op.create_index('ix_users_email', 'users', ['email'])

    # Unique index
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

    # Composite index
    op.create_index('ix_users_email_username', 'users', ['email', 'username'])

    # Partial index (PostgreSQL)
    op.create_index(
        'ix_users_active_email',
        'users',
        ['email'],
        postgresql_where=sa.text('is_active = true')
    )
```

### Add Foreign Key

```python
def upgrade():
    op.create_foreign_key(
        'fk_posts_user_id',  # Constraint name
        'posts',             # Source table
        'users',             # Target table
        ['user_id'],         # Source column
        ['id'],              # Target column
        ondelete='CASCADE'   # On delete action
    )
```

### Data Migrations

```python
from sqlalchemy import table, column, Integer, String

def upgrade():
    # Create table reference
    users = table(
        'users',
        column('id', Integer),
        column('username', String),
        column('email', String),
    )

    # Insert data
    op.bulk_insert(
        users,
        [
            {'username': 'admin', 'email': 'admin@example.com'},
            {'username': 'user', 'email': 'user@example.com'},
        ]
    )

    # Update data
    op.execute(
        users.update()
        .where(users.c.username == 'admin')
        .values({'email': 'admin@newdomain.com'})
    )

    # Delete data
    op.execute(
        users.delete().where(users.c.username == 'spam')
    )
```

### Execute Raw SQL

```python
def upgrade():
    # PostgreSQL specific
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Create trigger
    op.execute("""
        CREATE TRIGGER update_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column()
    """)

    # Multiple statements
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
```

### Batch Operations (SQLite)

```python
def upgrade():
    # SQLite doesn't support most ALTER TABLE operations
    # Use batch mode to recreate table
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('age', sa.Integer()))
        batch_op.alter_column('name', new_column_name='username')
        batch_op.create_index('ix_users_username', ['username'])
```

## Running Migrations

```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade to specific revision
alembic upgrade abc123

# Upgrade by relative steps
alembic upgrade +2  # Upgrade 2 versions

# Downgrade to specific revision
alembic downgrade xyz789

# Downgrade by relative steps
alembic downgrade -1  # Downgrade 1 version

# Downgrade to base (empty database)
alembic downgrade base

# Show current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic history --indicate-current

# Generate SQL instead of running migration
alembic upgrade head --sql

# Stamp database with specific revision (without running migration)
alembic stamp head
```

## Branching and Merging

```bash
# Create branch
alembic revision -m "feature branch" --head=abc123 --branch-label=feature

# Merge branches
alembic merge -m "merge branches" head1 head2

# Show heads
alembic heads

# Show branches
alembic branches
```

## Best Practices

### 1. Always Review Auto-Generated Migrations

```python
# Alembic may not detect all changes correctly
# Always review and test auto-generated migrations before applying
```

### 2. Test Migrations

```bash
# Test upgrade
alembic upgrade head

# Test downgrade
alembic downgrade -1

# Test full cycle
alembic upgrade head && alembic downgrade base && alembic upgrade head
```

### 3. Separate Schema and Data Migrations

```python
# migration_001_add_column.py - Schema migration
def upgrade():
    op.add_column('users', sa.Column('status', sa.String(20)))

# migration_002_set_default_status.py - Data migration
def upgrade():
    from sqlalchemy import table, column
    users = table('users', column('status', String))
    op.execute(users.update().values({'status': 'active'}))
```

### 4. Use Transactions

```python
def upgrade():
    with op.get_context().autocommit_block():
        # Operations here run in a transaction
        op.create_table('users', ...)
        op.create_index('ix_users_email', 'users', ['email'])
```

### 5. Document Complex Migrations

```python
"""
Add user roles and permissions system

This migration:
1. Creates roles table
2. Creates permissions table
3. Creates user_roles junction table
4. Migrates existing admin flags to roles

Dependencies: Users table must exist
Impact: May take several minutes on large databases
"""
```

### 6. Handle Existing Data

```python
def upgrade():
    # Add column as nullable first
    op.add_column('users', sa.Column('role_id', sa.Integer(), nullable=True))

    # Set default value for existing rows
    op.execute("UPDATE users SET role_id = 1")

    # Now make it non-nullable
    op.alter_column('users', 'role_id', nullable=False)

    # Add foreign key
    op.create_foreign_key('fk_users_role_id', 'users', 'roles', ['role_id'], ['id'])
```

### 7. Zero-Downtime Migrations

```python
# Step 1: Add new column (nullable)
def upgrade():
    op.add_column('users', sa.Column('email_new', sa.String(255), nullable=True))

# Step 2: Backfill data (separate deployment)
def upgrade():
    op.execute("UPDATE users SET email_new = email WHERE email_new IS NULL")

# Step 3: Make non-nullable and drop old column (separate deployment)
def upgrade():
    op.alter_column('users', 'email_new', nullable=False)
    op.drop_column('users', 'email')
    op.alter_column('users', 'email_new', new_column_name='email')
```

## Troubleshooting

### Reset Migration History

```bash
# Drop all tables
alembic downgrade base

# Or stamp current state without running migrations
alembic stamp head
```

### Fix Failed Migration

```bash
# Manually fix database
# Then stamp the revision
alembic stamp abc123
```

### Resolve Conflicts

```bash
# If multiple heads exist
alembic merge -m "merge heads" head1 head2
alembic upgrade head
```

## Integration with FastAPI

```python
# main.py
from alembic.config import Config
from alembic import command
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run migrations on startup
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    yield

    # Cleanup on shutdown
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
```

## Migration Checklist

- [ ] Review auto-generated migrations
- [ ] Test upgrade and downgrade locally
- [ ] Add data migrations separately from schema migrations
- [ ] Document complex migrations
- [ ] Handle existing data when adding non-nullable columns
- [ ] Use transactions for atomic changes
- [ ] Test on a database copy before production
- [ ] Plan zero-downtime migrations for production
- [ ] Backup database before running migrations
- [ ] Monitor migration execution time on large tables
