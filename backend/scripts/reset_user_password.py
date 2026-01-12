"""
重置用户密码脚本

用于修复密码验证问题或重置用户密码

用法:
    python backend/scripts/reset_user_password.py --email ceo@example.com --password newpassword123
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from backend.core.db import get_db
from backend.models import User
from backend.services.local_auth_service import LocalAuthService


def reset_user_password(
    email_or_username: str,
    new_password: str,
    db: Session = None,
) -> bool:
    """
    重置用户密码

    Args:
        email_or_username: 邮箱或用户名
        new_password: 新密码
        db: 数据库会话

    Returns:
        是否成功
    """
    if db is None:
        db = next(get_db())

    try:
        # 查找用户（支持邮箱或用户名）
        from sqlalchemy import or_
        user = (
            db.query(User)
            .filter(or_(User.email == email_or_username, User.username == email_or_username))
            .first()
        )

        if not user:
            print(f"❌ 用户 '{email_or_username}' 不存在")
            return False

        # 使用 LocalAuthService 的密码哈希方法（与登录验证一致）
        password_hash = LocalAuthService.hash_password(new_password)

        # 更新密码
        user.password_hash = password_hash
        db.commit()
        db.refresh(user)

        print(f"✅ 密码重置成功！")
        print(f"   用户: {user.username} ({user.email})")
        print(f"   角色: {user.role}")
        print(f"   新密码: {new_password}")

        return True

    except Exception as e:
        db.rollback()
        print(f"❌ 重置密码失败: {str(e)}")
        return False
    finally:
        db.close()


def verify_password(
    email_or_username: str,
    password: str,
    db: Session = None,
) -> bool:
    """
    验证用户密码是否正确

    Args:
        email_or_username: 邮箱或用户名
        password: 密码
        db: 数据库会话

    Returns:
        密码是否正确
    """
    if db is None:
        db = next(get_db())

    try:
        # 查找用户
        from sqlalchemy import or_
        user = (
            db.query(User)
            .filter(or_(User.email == email_or_username, User.username == email_or_username))
            .first()
        )

        if not user:
            print(f"❌ 用户 '{email_or_username}' 不存在")
            return False

        if not user.password_hash:
            print(f"⚠️  用户 '{email_or_username}' 没有设置密码")
            return False

        # 验证密码
        is_valid = LocalAuthService.verify_password(password, user.password_hash)

        if is_valid:
            print(f"✅ 密码验证成功！")
            print(f"   用户: {user.username} ({user.email})")
            print(f"   角色: {user.role}")
        else:
            print(f"❌ 密码验证失败！")
            print(f"   用户: {user.username} ({user.email})")
            print(f"   提示: 密码不匹配，请使用 --reset 参数重置密码")

        return is_valid

    except Exception as e:
        print(f"❌ 验证密码失败: {str(e)}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="重置或验证用户密码")
    parser.add_argument("--email", "--username", dest="identifier", required=True, help="邮箱或用户名")
    parser.add_argument("--password", required=True, help="新密码（重置）或当前密码（验证）")
    parser.add_argument("--reset", action="store_true", help="重置密码（默认是验证）")
    parser.add_argument("--verify", action="store_true", help="验证密码（默认）")

    args = parser.parse_args()

    if args.reset:
        print("=" * 50)
        print("重置用户密码")
        print("=" * 50)
        print(f"用户: {args.identifier}")
        print("=" * 50)

        success = reset_user_password(args.identifier, args.password)

        if success:
            print("\n✅ 密码已重置，可以使用新密码登录:")
            print(f"   邮箱/用户名: {args.identifier}")
            print(f"   新密码: {args.password}")
        else:
            print("\n❌ 密码重置失败")
            sys.exit(1)
    else:
        print("=" * 50)
        print("验证用户密码")
        print("=" * 50)
        print(f"用户: {args.identifier}")
        print("=" * 50)

        is_valid = verify_password(args.identifier, args.password)

        if not is_valid:
            print("\n💡 提示: 如果密码错误，可以使用以下命令重置:")
            print(f"   python backend/scripts/reset_user_password.py --email {args.identifier} --password YourNewPassword --reset")
            sys.exit(1)

