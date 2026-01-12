"""
创建老板权限账号脚本

用法:
    # 方法1: 从项目根目录运行
    python backend/scripts/create_ceo_user.py
    
    # 方法2: 从 backend 目录运行
    cd backend
    python scripts/create_ceo_user.py
    
    # 自定义参数
    python backend/scripts/create_ceo_user.py --username boss --email boss@example.com --password YourPassword123

功能:
    - 创建具有 admin 或 ceo 角色的用户账号
    - 自动检查用户名和邮箱是否已存在
    - 使用 bcrypt 加密密码

默认账号信息:
    - 用户名: ceo
    - 邮箱: ceo@example.com
    - 密码: ceo123456
    - 角色: admin

注意:
    - 运行前请确保数据库已初始化（运行 alembic upgrade head）
    - 确保已安装所有依赖（pip install -r requirements.txt）
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


def create_ceo_user(
    username: str = "ceo",
    email: str = "ceo@example.com",
    password: str = "ceo123456",
    full_name: str = "老板",
    role: str = "admin",
    db: Session = None,
) -> User:
    """
    创建老板权限账号

    Args:
        username: 用户名
        email: 邮箱
        password: 密码
        full_name: 真实姓名
        role: 角色 (admin 或 ceo)
        db: 数据库会话

    Returns:
        创建的用户对象
    """
    if db is None:
        db = next(get_db())

    try:
        # 检查用户名是否已存在
        existing_username = db.query(User).filter(User.username == username).first()
        if existing_username:
            print(f"❌ 用户名 '{username}' 已存在")
            return None

        # 检查邮箱是否已存在
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            print(f"❌ 邮箱 '{email}' 已存在")
            return None

        # 验证角色
        valid_roles = ["admin", "ceo"]
        if role not in valid_roles:
            print(f"❌ 无效的角色 '{role}'，必须是: {valid_roles}")
            return None

        # 使用 LocalAuthService 的密码哈希方法
        password_hash = LocalAuthService.hash_password(password)

        # 创建用户（确保使用正确的字段名）
        from uuid import uuid4
        new_user = User(
            id=uuid4(),
            username=username,
            email=email,
            password_hash=password_hash,  # 注意：User 模型使用 password_hash 字段
            role=role,
            full_name=full_name,
            is_active=True,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        print(f"✅ 老板账号创建成功！")
        print(f"   用户名: {username}")
        print(f"   邮箱: {email}")
        print(f"   密码: {password}")
        print(f"   角色: {role}")
        print(f"   用户ID: {new_user.id}")

        return new_user

    except Exception as e:
        db.rollback()
        print(f"❌ 创建用户失败: {str(e)}")
        return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="创建老板权限账号")
    parser.add_argument("--username", default="ceo", help="用户名 (默认: ceo)")
    parser.add_argument("--email", default="ceo@example.com", help="邮箱 (默认: ceo@example.com)")
    parser.add_argument("--password", default="ceo123456", help="密码 (默认: ceo123456)")
    parser.add_argument("--full-name", default="老板", help="真实姓名 (默认: 老板)")
    parser.add_argument("--role", default="admin", choices=["admin", "ceo"], help="角色 (默认: admin)")

    args = parser.parse_args()

    print("=" * 50)
    print("创建老板权限账号")
    print("=" * 50)
    print(f"用户名: {args.username}")
    print(f"邮箱: {args.email}")
    print(f"角色: {args.role}")
    print("=" * 50)

    user = create_ceo_user(
        username=args.username,
        email=args.email,
        password=args.password,
        full_name=args.full_name,
        role=args.role,
    )

    if user:
        print("\n✅ 账号创建成功，可以使用以下信息登录:")
        print(f"   邮箱/用户名: {args.email} 或 {args.username}")
        print(f"   密码: {args.password}")
    else:
        print("\n❌ 账号创建失败")
        sys.exit(1)

