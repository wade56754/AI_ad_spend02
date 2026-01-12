#!/usr/bin/env python3
"""
AI广告代投系统 - 测试数据库初始化脚本

用途: 创建 SQLite 数据库表并添加测试用户数据
执行方式: python backend/scripts/init_test_db.py

测试用户对应 __tests__/fixtures/test-accounts.ts 中的定义
"""

import os
import sys
from pathlib import Path
from uuid import uuid4

# 动态添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量，避免配置加载问题
os.environ.setdefault("ENV_NAME", "development")
os.environ.setdefault("DATABASE_URL", "sqlite:///./ai_ad_spend_dev.db")

# 生成测试用安全密钥
import secrets
os.environ.setdefault("JWT_SECRET", secrets.token_urlsafe(64))
os.environ.setdefault("ENCRYPTION_KEY", secrets.token_urlsafe(32))
os.environ.setdefault("SUPABASE_URL", "https://placeholder.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "placeholder_anon_key_for_testing")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "placeholder_service_key_for_testing")

# ============================================================
# SQLite 兼容性补丁 - 必须在导入模型之前执行
# ============================================================
# PostgreSQL 特有的 JSONB 类型在 SQLite 上不支持
# 这里替换为通用的 JSON 类型
from sqlalchemy import JSON as StandardJSON
import sqlalchemy.dialects.postgresql as pg_module
pg_module.JSONB = StandardJSON
print("[PATCH] 已将 PostgreSQL JSONB 替换为 JSON (SQLite 兼容)")


def create_tables():
    """创建数据库表 - 使用 SQLAlchemy ORM 创建所有表"""
    print("=" * 60)
    print("开始初始化测试数据库")
    print("=" * 60)

    try:
        from sqlalchemy import create_engine, text, JSON
        from sqlalchemy.pool import StaticPool
        from sqlalchemy.types import TypeDecorator

        database_url = os.environ.get("DATABASE_URL", "sqlite:///./ai_ad_spend_dev.db")

        # 检测是否为 SQLite
        is_sqlite = database_url.startswith("sqlite")

        # SQLite 特殊配置
        engine_kwargs = {
            "echo": False,
            "isolation_level": "SERIALIZABLE",
            "poolclass": StaticPool,
            "connect_args": {
                "check_same_thread": False,
                "timeout": 30
            }
        }

        engine = create_engine(database_url, **engine_kwargs)

        # 导入所有模型以确保它们被注册到 Base.metadata
        # 注意: JSONB 类型补丁已在文件开头应用
        from backend.models import Base

        # 使用 SQLAlchemy ORM 创建所有表
        # 这会创建所有模型定义的表，包括:
        # - users, teams (核心)
        # - projects, channels (业务)
        # - ad_accounts, daily_reports (账户/报告)
        # - ledger_entries, topup_requests (财务)
        # 等等
        print("[INFO] 使用 SQLAlchemy ORM 创建所有表...")
        Base.metadata.create_all(bind=engine)

        # 验证关键表是否创建成功
        with engine.connect() as conn:
            # 检查核心表
            tables_to_check = [
                "users", "teams", "projects", "channels",
                "ad_accounts", "daily_reports", "ledger_entries",
                "topup_requests"
            ]
            for table_name in tables_to_check:
                try:
                    result = conn.execute(text(f"SELECT 1 FROM {table_name} LIMIT 1"))
                    print(f"  [OK] 表 {table_name} 已创建")
                except Exception as e:
                    # 表存在但可能为空，这是正常的
                    if "no such table" in str(e).lower():
                        print(f"  [WARN] 表 {table_name} 创建失败")
                    else:
                        print(f"  [OK] 表 {table_name} 已创建")

        print(f"\n[OK] 数据库表创建成功 ({database_url})")
        return True

    except Exception as e:
        print(f"[FAIL] 数据库表创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_session():
    """获取数据库会话"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    database_url = os.environ.get("DATABASE_URL", "sqlite:///./ai_ad_spend_dev.db")

    engine_kwargs = {
        "echo": False,
        "isolation_level": "SERIALIZABLE",
        "poolclass": StaticPool,
        "connect_args": {
            "check_same_thread": False,
            "timeout": 30
        }
    }

    engine = create_engine(database_url, **engine_kwargs)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def create_test_users():
    """创建测试用户

    对应 __tests__/fixtures/test-accounts.ts 中的定义:
    - ceo: ceo@test.local / test123
    - finance: finance@test.local / test123
    - supervisor: supervisor@test.local / test123 (废弃，映射到 project_owner)
    - pitcher: pitcher@test.local / test123
    - project_owner: project_owner@test.local / test123
    - account_manager: account_manager@test.local / test123
    - admin: admin@test.local / test123
    """
    print("\n" + "=" * 60)
    print("创建测试用户")
    print("=" * 60)

    import bcrypt
    from sqlalchemy import create_engine, text
    from sqlalchemy.pool import StaticPool

    def hash_password(password: str) -> str:
        """使用 bcrypt 直接哈希密码"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # 测试用户列表 - 对应 test-accounts.ts
    test_users = [
        {
            "id": str(uuid4()),
            "username": "ceo",
            "email": "ceo@test.local",
            "password": "test123",
            "role": "ceo",
            "full_name": "测试老板",
        },
        {
            "id": str(uuid4()),
            "username": "finance",
            "email": "finance@test.local",
            "password": "test123",
            "role": "finance",
            "full_name": "测试财务",
        },
        {
            "id": str(uuid4()),
            "username": "supervisor",
            "email": "supervisor@test.local",
            "password": "test123",
            "role": "project_owner",  # supervisor 已废弃，映射到 project_owner
            "full_name": "测试主管",
        },
        {
            "id": str(uuid4()),
            "username": "pitcher",
            "email": "pitcher@test.local",
            "password": "test123",
            "role": "pitcher",
            "full_name": "测试投手",
        },
        {
            "id": str(uuid4()),
            "username": "project_owner",
            "email": "project_owner@test.local",
            "password": "test123",
            "role": "project_owner",
            "full_name": "测试项目负责人",
        },
        {
            "id": str(uuid4()),
            "username": "account_manager",
            "email": "account_manager@test.local",
            "password": "test123",
            "role": "account_manager",
            "full_name": "测试户管",
        },
        {
            "id": str(uuid4()),
            "username": "admin",
            "email": "admin@test.local",
            "password": "test123",
            "role": "admin",
            "full_name": "测试管理员",
        },
    ]

    database_url = os.environ.get("DATABASE_URL", "sqlite:///./ai_ad_spend_dev.db")
    engine_kwargs = {
        "echo": False,
        "isolation_level": "SERIALIZABLE",
        "poolclass": StaticPool,
        "connect_args": {
            "check_same_thread": False,
            "timeout": 30
        }
    }
    engine = create_engine(database_url, **engine_kwargs)

    try:
        with engine.connect() as conn:
            for user_data in test_users:
                # 检查用户是否已存在
                result = conn.execute(
                    text("SELECT id FROM users WHERE email = :email"),
                    {"email": user_data["email"]}
                )
                existing = result.fetchone()

                if existing:
                    print(f"[SKIP] 用户已存在: {user_data['email']}")
                    continue

                # 创建新用户
                password_hash = hash_password(user_data["password"])

                conn.execute(
                    text("""
                        INSERT INTO users (id, username, email, password_hash, role, full_name, is_active)
                        VALUES (:id, :username, :email, :password_hash, :role, :full_name, 1)
                    """),
                    {
                        "id": user_data["id"],
                        "username": user_data["username"],
                        "email": user_data["email"],
                        "password_hash": password_hash,
                        "role": user_data["role"],
                        "full_name": user_data["full_name"],
                    }
                )
                print(f"[OK] 创建用户: {user_data['email']} (角色: {user_data['role']})")

            conn.commit()
            print("\n[OK] 测试用户创建完成")

    except Exception as e:
        print(f"\n[FAIL] 创建用户失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def verify_users():
    """验证用户创建成功"""
    print("\n" + "=" * 60)
    print("验证测试用户")
    print("=" * 60)

    from sqlalchemy import create_engine, text
    from sqlalchemy.pool import StaticPool

    database_url = os.environ.get("DATABASE_URL", "sqlite:///./ai_ad_spend_dev.db")
    engine_kwargs = {
        "echo": False,
        "isolation_level": "SERIALIZABLE",
        "poolclass": StaticPool,
        "connect_args": {
            "check_same_thread": False,
            "timeout": 30
        }
    }
    engine = create_engine(database_url, **engine_kwargs)

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT email, role, is_active FROM users"))
            users = result.fetchall()
            print(f"数据库中共有 {len(users)} 个用户:")
            for user in users:
                print(f"  - {user[0]} (角色: {user[1]}, 激活: {user[2]})")
    except Exception as e:
        print(f"[FAIL] 验证失败: {e}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("AI广告代投系统 - 测试数据库初始化")
    print("=" * 60)

    # 1. 创建表
    if not create_tables():
        print("\n[FAIL] 初始化失败")
        sys.exit(1)

    # 2. 创建测试用户
    if not create_test_users():
        print("\n[FAIL] 初始化失败")
        sys.exit(1)

    # 3. 验证
    verify_users()

    print("\n" + "=" * 60)
    print("[SUCCESS] 测试数据库初始化完成!")
    print("=" * 60)
    print("\n现在可以启动后端并运行 Playwright 测试了")


if __name__ == "__main__":
    main()
