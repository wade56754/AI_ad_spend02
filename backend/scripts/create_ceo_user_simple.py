"""
创建老板权限账号脚本（简化版）

直接使用 SQL 插入，适用于数据库已初始化的情况

用法:
    python backend/scripts/create_ceo_user_simple.py

默认账号:
    - 用户名: ceo
    - 邮箱: ceo@example.com  
    - 密码: ceo123456
    - 角色: admin
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.core.config import get_settings

settings = get_settings()


def create_ceo_user_simple(
    username: str = "ceo",
    email: str = "ceo@example.com",
    password: str = "ceo123456",
    full_name: str = "老板",
    role: str = "admin",
):
    """使用 SQL 直接创建用户"""
    try:
        # 创建数据库连接
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        # 检查用户名是否已存在
        result = db.execute(
            text("SELECT id FROM users WHERE username = :username"), {"username": username}
        )
        if result.fetchone():
            print(f"❌ 用户名 '{username}' 已存在")
            db.close()
            return False

        # 检查邮箱是否已存在
        result = db.execute(
            text("SELECT id FROM users WHERE email = :email"), {"email": email}
        )
        if result.fetchone():
            print(f"❌ 邮箱 '{email}' 已存在")
            db.close()
            return False

        # 哈希密码
        password_bytes = password.encode("utf-8")[:72]
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_bytes, salt).decode("utf-8")

        # 插入用户（使用正确的字段名和 UUID）
        from uuid import uuid4
        user_id = uuid4()
        
        # 根据数据库类型选择不同的 SQL 语法
        import re
        db_url = str(settings.database_url)
        is_sqlite = 'sqlite' in db_url.lower()
        
        if is_sqlite:
            # SQLite 使用 CURRENT_TIMESTAMP
            sql = text("""
                INSERT INTO users (id, username, email, password_hash, full_name, role, is_active, created_at, updated_at)
                VALUES (:id, :username, :email, :password_hash, :full_name, :role, :is_active, datetime('now'), datetime('now'))
            """)
        else:
            # PostgreSQL 使用 CURRENT_TIMESTAMP
            sql = text("""
                INSERT INTO users (id, username, email, password_hash, full_name, role, is_active, created_at, updated_at)
                VALUES (:id, :username, :email, :password_hash, :full_name, :role, :is_active, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """)
        
        db.execute(
            sql,
            {
                "id": str(user_id),
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "full_name": full_name,
                "role": role,
                "is_active": True,
            },
        )
        db.commit()

        print(f"✅ 老板账号创建成功！")
        print(f"   用户名: {username}")
        print(f"   邮箱: {email}")
        print(f"   密码: {password}")
        print(f"   角色: {role}")

        db.close()
        return True

    except Exception as e:
        print(f"❌ 创建用户失败: {str(e)}")
        if "no such table" in str(e).lower():
            print("\n💡 提示: 数据库表尚未创建，请先运行:")
            print("   python -m alembic upgrade head")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="创建老板权限账号（简化版）")
    parser.add_argument("--username", default="ceo", help="用户名 (默认: ceo)")
    parser.add_argument("--email", default="ceo@example.com", help="邮箱 (默认: ceo@example.com)")
    parser.add_argument("--password", default="ceo123456", help="密码 (默认: ceo123456)")
    parser.add_argument("--full-name", default="老板", help="真实姓名 (默认: 老板)")
    parser.add_argument("--role", default="admin", choices=["admin", "ceo"], help="角色 (默认: admin)")

    args = parser.parse_args()

    print("=" * 50)
    print("创建老板权限账号（简化版）")
    print("=" * 50)
    print(f"用户名: {args.username}")
    print(f"邮箱: {args.email}")
    print(f"角色: {args.role}")
    print("=" * 50)

    success = create_ceo_user_simple(
        username=args.username,
        email=args.email,
        password=args.password,
        full_name=args.full_name,
        role=args.role,
    )

    if success:
        print("\n✅ 账号创建成功，可以使用以下信息登录:")
        print(f"   邮箱/用户名: {args.email} 或 {args.username}")
        print(f"   密码: {args.password}")
    else:
        print("\n❌ 账号创建失败")
        sys.exit(1)

