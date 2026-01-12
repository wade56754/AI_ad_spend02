"""
创建或重置 CEO 账号脚本（智能版）

自动检测：
- 如果用户不存在，则创建
- 如果用户存在，则重置密码

用法:
    python backend/scripts/create_or_reset_ceo.py
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from backend.core.db import get_db
from backend.models import User
from backend.services.local_auth_service import LocalAuthService
from backend.core.config import get_settings

settings = get_settings()


def check_table_exists(db: Session, table_name: str = "users") -> bool:
    """检查表是否存在"""
    try:
        inspector = inspect(db.bind)
        tables = inspector.get_table_names()
        return table_name in tables
    except Exception:
        return False


def create_or_reset_ceo_user(
    username: str = "ceo",
    email: str = "ceo@example.com",
    password: str = "ceo123456",
    full_name: str = "老板",
    role: str = "admin",
) -> bool:
    """创建或重置 CEO 用户"""
    db = next(get_db())

    try:
        # 检查表是否存在
        if not check_table_exists(db, "users"):
            print("❌ 数据库表 'users' 不存在")
            print("\n💡 解决方案:")
            print("   1. 运行数据库迁移:")
            print("      cd backend")
            print("      python -m alembic upgrade head")
            print("\n   2. 或者使用 SQL 脚本直接创建:")
            print("      查看 backend/scripts/create_ceo_user.sql")
            print("\n   3. 如果使用 Supabase，可以在 Supabase Dashboard 中手动创建用户")
            return False

        # 查找用户（支持邮箱或用户名）
        from sqlalchemy import or_
        user = (
            db.query(User)
            .filter(or_(User.email == email, User.username == username))
            .first()
        )

        # 使用 LocalAuthService 的密码哈希方法（与登录验证一致）
        password_hash = LocalAuthService.hash_password(password)

        if user:
            # 用户存在，重置密码
            print(f"📝 用户已存在: {user.username} ({user.email})")
            print(f"   当前角色: {user.role}")
            print(f"   正在重置密码...")

            user.password_hash = password_hash
            # 如果角色不对，也更新角色
            if user.role != role:
                print(f"   更新角色: {user.role} → {role}")
                user.role = role
            if user.full_name != full_name:
                user.full_name = full_name

            db.commit()
            db.refresh(user)

            print(f"✅ 密码重置成功！")
            print(f"   用户名: {user.username}")
            print(f"   邮箱: {user.email}")
            print(f"   新密码: {password}")
            print(f"   角色: {user.role}")

        else:
            # 用户不存在，创建新用户
            print(f"📝 用户不存在，正在创建...")

            from uuid import uuid4
            new_user = User(
                id=uuid4(),
                username=username,
                email=email,
                password_hash=password_hash,
                role=role,
                full_name=full_name,
                is_active=True,
            )

            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            print(f"✅ 老板账号创建成功！")
            print(f"   用户名: {new_user.username}")
            print(f"   邮箱: {new_user.email}")
            print(f"   密码: {password}")
            print(f"   角色: {new_user.role}")
            print(f"   用户ID: {new_user.id}")

        return True

    except Exception as e:
        db.rollback()
        print(f"❌ 操作失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="创建或重置 CEO 账号（智能版）")
    parser.add_argument("--username", default="ceo", help="用户名 (默认: ceo)")
    parser.add_argument("--email", default="ceo@example.com", help="邮箱 (默认: ceo@example.com)")
    parser.add_argument("--password", default="ceo123456", help="密码 (默认: ceo123456)")
    parser.add_argument("--full-name", default="老板", help="真实姓名 (默认: 老板)")
    parser.add_argument("--role", default="admin", choices=["admin", "ceo"], help="角色 (默认: admin)")

    args = parser.parse_args()

    print("=" * 50)
    print("创建或重置 CEO 账号（智能版）")
    print("=" * 50)
    print(f"用户名: {args.username}")
    print(f"邮箱: {args.email}")
    print(f"角色: {args.role}")
    print("=" * 50)

    success = create_or_reset_ceo_user(
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

