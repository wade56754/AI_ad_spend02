"""
E2E 测试账户种子脚本

创建用于 Playwright E2E 测试的测试用户账户。
基于 __tests__/fixtures/test-accounts.ts 中定义的账户配置。

用法:
    python scripts/seed_test_accounts.py

注意:
    - 需要数据库连接 (DATABASE_URL 环境变量或 .env 文件)
    - 如果账户已存在，会跳过创建
    - 密码使用 bcrypt 哈希
"""

import os
import sys
from pathlib import Path
from uuid import uuid4

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(project_root / ".env")
load_dotenv(project_root / "backend" / ".env")

# 测试账户配置
# 映射关系: 测试角色 -> 数据库角色
# - ceo -> admin (老板使用 admin 角色)
# - finance -> finance
# - supervisor -> data_operator
# - pitcher -> media_buyer
# - project_owner -> project_owner
# - account_manager -> account_manager
# - admin -> admin

TEST_ACCOUNTS = [
    {
        "email": "ceo@test.local",
        "username": "test_ceo",
        "password": "test123",
        "role": "admin",  # CEO 使用 admin 角色
        "display_name": "测试老板",
    },
    {
        "email": "finance@test.local",
        "username": "test_finance",
        "password": "test123",
        "role": "finance",
        "display_name": "测试财务",
    },
    {
        "email": "supervisor@test.local",
        "username": "test_supervisor",
        "password": "test123",
        "role": "data_operator",  # supervisor -> data_operator
        "display_name": "测试主管",
    },
    {
        "email": "pitcher@test.local",
        "username": "test_pitcher",
        "password": "test123",
        "role": "media_buyer",  # pitcher -> media_buyer
        "display_name": "测试投手",
    },
    {
        "email": "owner@test.local",
        "username": "test_owner",
        "password": "test123",
        "role": "project_owner",
        "display_name": "测试项目负责人",
    },
    {
        "email": "am@test.local",
        "username": "test_am",
        "password": "test123",
        "role": "account_manager",
        "display_name": "测试户管",
    },
    {
        "email": "admin@test.local",
        "username": "test_admin",
        "password": "test123",
        "role": "admin",
        "display_name": "测试管理员",
    },
]


def hash_password(password: str) -> str:
    """使用 bcrypt 哈希密码"""
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def get_database_url() -> str:
    """获取数据库连接 URL"""
    # 优先使用环境变量
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url

    # 尝试从配置中读取
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    if supabase_url and supabase_key:
        # 从 Supabase URL 构建 PostgreSQL 连接字符串
        # Supabase URL 格式: https://xxx.supabase.co
        project_id = supabase_url.replace("https://", "").replace(".supabase.co", "")
        db_password = os.getenv("SUPABASE_DB_PASSWORD", "")
        if db_password:
            return f"postgresql://postgres.{project_id}:{db_password}@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

    raise ValueError(
        "无法获取数据库连接信息。请设置 DATABASE_URL 环境变量，"
        "或者设置 SUPABASE_URL 和 SUPABASE_DB_PASSWORD。"
    )


def create_test_accounts():
    """创建测试账户"""
    print("=" * 60)
    print("E2E 测试账户种子脚本")
    print("=" * 60)

    # 获取数据库连接
    try:
        db_url = get_database_url()
        print(f"\n数据库: {db_url[:50]}...")
    except ValueError as e:
        print(f"\n错误: {e}")
        sys.exit(1)

    # 创建数据库引擎
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    print(f"\n准备创建 {len(TEST_ACCOUNTS)} 个测试账户:\n")

    created_count = 0
    skipped_count = 0
    error_count = 0

    for account in TEST_ACCOUNTS:
        email = account["email"]
        username = account["username"]
        role = account["role"]

        try:
            # 检查账户是否已存在
            result = session.execute(
                text("SELECT id FROM users WHERE email = :email OR username = :username"),
                {"email": email, "username": username}
            )
            existing = result.fetchone()

            if existing:
                print(f"  [跳过] {email} - 账户已存在")
                skipped_count += 1
                continue

            # 创建新用户
            user_id = str(uuid4())
            password_hash = hash_password(account["password"])

            session.execute(
                text("""
                    INSERT INTO users (id, email, username, password_hash, role, is_active, created_at, updated_at)
                    VALUES (:id, :email, :username, :password_hash, :role, true, NOW(), NOW())
                """),
                {
                    "id": user_id,
                    "email": email,
                    "username": username,
                    "password_hash": password_hash,
                    "role": role,
                }
            )

            print(f"  [创建] {email} (角色: {role})")
            created_count += 1

        except Exception as e:
            print(f"  [错误] {email} - {e}")
            error_count += 1

    # 提交事务
    try:
        session.commit()
        print(f"\n事务已提交。")
    except Exception as e:
        session.rollback()
        print(f"\n事务回滚: {e}")
        error_count += len(TEST_ACCOUNTS)
        created_count = 0
    finally:
        session.close()

    # 打印摘要
    print("\n" + "=" * 60)
    print("摘要:")
    print(f"  创建: {created_count}")
    print(f"  跳过: {skipped_count}")
    print(f"  错误: {error_count}")
    print("=" * 60)

    # 打印登录信息
    if created_count > 0 or skipped_count > 0:
        print("\n测试账户登录信息:")
        print("-" * 40)
        for account in TEST_ACCOUNTS:
            print(f"  邮箱: {account['email']}")
            print(f"  密码: {account['password']}")
            print(f"  角色: {account['role']}")
            print()

    return created_count, skipped_count, error_count


if __name__ == "__main__":
    create_test_accounts()
