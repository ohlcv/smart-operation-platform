import asyncio
import os
from collections.abc import Iterable, MutableMapping
from logging.config import fileConfig
from typing import Literal

from alembic import context
from alembic.migration import MigrationContext
from alembic.operations.ops import MigrationScript
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from config.database import SYNC_SQLALCHEMY_DATABASE_URL, Base
from utils.import_util import ImportUtil

# 判断versions目录是否存在，如果不存在则创建
alembic_versions_path = 'alembic/versions'
if not os.path.exists(alembic_versions_path):
    os.makedirs(alembic_versions_path)


# 自动查找所有模型
found_models = ImportUtil.find_models(Base)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
alembic_config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata
# 使用同步驱动 URL（pymysql），alembic upgrade 不能直接用 asyncmy
alembic_config.set_main_option('sqlalchemy.url', SYNC_SQLALCHEMY_DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = alembic_config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    def include_name(
        name: str | None,
        type_: Literal['schema', 'table', 'column', 'index', 'unique_constraint', 'foreign_key_constraint'],
        parent_names: MutableMapping[Literal['schema_name', 'table_name', 'schema_qualified_table_name'], str | None],
    ) -> bool:
        if type_ == 'table':
            return name in target_metadata.tables
        return True

    def process_revision_directives(
        context: MigrationContext,
        revision: str | Iterable[str | None] | Iterable[str],
        directives: list[MigrationScript],
    ) -> None:
        script = directives[0]

        # 检查所有操作集是否为空
        all_empty = all(ops.is_empty() for ops in script.upgrade_ops_list)

        if all_empty:
            # 如果没有实际变更，不生成迁移文件
            directives[:] = []
            print('❎️ 未检测到模型变更，不生成迁移文件')
        else:
            print('✅️ 检测到模型变更，生成迁移文件')

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        transaction_per_migration=True,
        include_name=include_name,
        process_revision_directives=process_revision_directives,
        render_as_batch=False,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using a synchronous engine.

    使用同步驱动（pymysql / psycopg2）以确保 alembic upgrade / autogenerate
    在所有 ORM 场景下稳定工作。async 驱动不支持 alembic 的完整事务模型。
    """
    from sqlalchemy import create_engine

    connectable = create_engine(
        alembic_config.get_main_option('sqlalchemy.url'),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
