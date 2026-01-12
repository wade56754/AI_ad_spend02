"""
快速创建 CEO 账号（不依赖数据库迁移）

直接使用 SQL 创建用户，适用于数据库表已存在但用户不存在的情况

用法:
    python backend/scripts/quick_create_ceo.py
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


def quick_create_ceo(
    username: str = "ceo",
    email: str = "ceo@example.com",
    password: str = "ceo123456",
    full_name: str = "老板",
    role: str = "admin",
):
    """
    快速创建 CEO 用户（使用原始 SQL）
    
    ⚠️ 安全警告：
    - 默认密码仅用于开发/测试环境
    - 生产环境必须通过 --password 参数提供强密码
    - 创建后请立即修改密码
    """
    try:
        # 创建数据库连接
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        # 检查表是否存在
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'"))
        if not result.fetchone():
            print("❌ 数据库表 'users' 不存在")
            print("\n💡 请先运行数据库迁移:")
            print("   cd backend")
            print("   python -m alembic upgrade head")
            db.close()
            return False

        # 检查用户是否已存在
        result = db.execute(
            text("SELECT id, username, email, role FROM users WHERE email = :email OR username = :username"),
            {"email": email, "username": username}
        )
        existing = result.fetchone()

        if existing:
            print(f"📝 用户已存在: {existing[1]} ({existing[2]})")
            print(f"   当前角色: {existing[3]}")
            print(f"   正在重置密码...")

            # 哈希新密码
            password_bytes = password.encode("utf-8")[:72]
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password_bytes, salt).decode("utf-8")

            # 更新密码和角色
            db.execute(
                text("""
                    UPDATE users 
                    SET password_hash = :password_hash, 
                        role = :role,
                        full_name = :full_name,
                        updated_at = datetime('now')
                    WHERE id = :id
                """),
                {
                    "id": str(existing[0]),
                    "password_hash": password_hash,
                    "role": role,
                    "full_name": full_name,
                }
            )
            db.commit()

            print(f"✅ 密码重置成功！")
            print(f"   用户名: {existing[1]}")
            print(f"   邮箱: {existing[2]}")
            print(f"   新密码: {password}")
            print(f"   角色: {role}")

        else:
            # 创建新用户
            print(f"📝 用户不存在，正在创建...")

            # 哈希密码
            password_bytes = password.encode("utf-8")[:72]
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password_bytes, salt).decode("utf-8")

            # 生成 UUID（SQLite 兼容方式）
            from uuid import uuid4
            user_id = str(uuid4())

            # 插入用户
            db.execute(
                text("""
                    INSERT INTO users (
                        id, username, email, password_hash, full_name, role, is_active, created_at, updated_at
                    )
                    VALUES (
                        :id, :username, :email, :password_hash, :full_name, :role, :is_active, 
                        datetime('now'), datetime('now')
                    )
                """),
                {
                    "id": user_id,
                    "username": username,
                    "email": email,
                    "password_hash": password_hash,
                    "full_name": full_name,
                    "role": role,
                    "is_active": 1,  # SQLite 使用 1/0 表示布尔值
                }
            )
            db.commit()

            print(f"✅ 老板账号创建成功！")
            print(f"   用户名: {username}")
            print(f"   邮箱: {email}")
            print(f"   密码: {password}")
            print(f"   角色: {role}")
            print(f"   用户ID: {user_id}")

        db.close()
        return True

    except Exception as e:
        print(f"❌ 操作失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if "no such table" in str(e).lower():
            print("\n💡 提示: 数据库表尚未创建，请先运行:")
            print("   python -m alembic upgrade head")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="快速创建或重置 CEO 账号")
    parser.add_argument("--username", default="ceo", help="用户名 (默认: ceo)")
    parser.add_argument("--email", default="ceo@example.com", help="邮箱 (默认: ceo@example.com)")
    parser.add_argument(
        "--password", 
        default="ceo123456", 
        help="密码 (默认: ceo123456) ⚠️ 生产环境必须使用强密码"
    )
    parser.add_argument("--full-name", default="老板", help="真实姓名 (默认: 老板)")
    parser.add_argument("--role", default="admin", choices=["admin", "ceo"], help="角色 (默认: admin)")

    args = parser.parse_args()

    print("=" * 50)
    print("快速创建或重置 CEO 账号")
    print("=" * 50)
    print(f"用户名: {args.username}")
    print(f"邮箱: {args.email}")
    print(f"角色: {args.role}")
    print("=" * 50)

    success = quick_create_ceo(
        username=args.username,
        email=args.email,
        password=args.password,
        full_name=args.full_name,
        role=args.role,
    )

    if success:
        print("\n✅ 操作成功，可以使用以下信息登录:")
        print(f"   邮箱/用户名: {args.email} 或 {args.username}")
        print(f"   密码: {args.password}")
    else:
        print("\n❌ 操作失败")
        sys.exit(1)

