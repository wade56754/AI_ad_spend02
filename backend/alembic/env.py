"""
Alembic Environment Configuration
用于运行数据库迁移

使用方法:
    alembic upgrade head      # 运行所有迁移
    alembic downgrade -1      # 回滚一个版本
    alembic current           # 查看当前版本
    alembic history           # 查看迁移历史
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入模型以便 autogenerate 使用
from backend.models import Base
from backend.core.config import get_settings

# Alembic Config 对象
config = context.config

# 设置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 模型元数据，用于 autogenerate
target_metadata = Base.metadata


def get_url():
    """获取数据库连接 URL"""
    try:
        settings = get_settings()
        return settings.database_url
    except Exception as e:
        # 如果配置加载失败，尝试从环境变量获取
        url = os.getenv("DATABASE_URL")
        if url:
            return url
        raise RuntimeError(f"无法获取数据库 URL: {e}")


def run_migrations_offline() -> None:
    """
    在 'offline' 模式下运行迁移

    这会配置 context 仅使用 URL，而不是 Engine。
    通过跳过 Engine 创建，我们甚至不需要 DBAPI 可用。

    在这种模式下调用 context.execute() 会将给定的字符串
    输出到脚本输出。
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    在 'online' 模式下运行迁移

    在这种场景中，我们需要创建一个 Engine
    并将连接与 context 关联。
    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
