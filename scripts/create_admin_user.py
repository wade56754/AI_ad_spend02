"""
创建 Admin 测试账号

用法:
    cd D:/project/AI_ad_spend02
    python scripts/create_admin_user.py
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uuid import uuid4
import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def hash_password(password: str) -> str:
    """使用 bcrypt 加密密码"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# 从 .env 文件加载环境变量
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# 数据库连接
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("错误: 未找到 DATABASE_URL 环境变量")
    print("请确保项目根目录存在 .env 文件并包含 DATABASE_URL")
    sys.exit(1)

def create_admin_user():
    """创建 admin 测试账号"""

    # 用户信息
    admin_user = {
        "id": str(uuid4()),
        "username": "admin",
        "email": "admin@test.com",
        "password": "admin123",  # 测试密码
        "role": "admin",
        "is_active": True,
    }

    # 加密密码
    password_hash = hash_password(admin_user["password"])

    print(f"创建 Admin 测试账号...")
    print(f"  用户名: {admin_user['username']}")
    print(f"  邮箱: {admin_user['email']}")
    print(f"  密码: {admin_user['password']}")
    print(f"  角色: {admin_user['role']}")
    print()

    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()

        # 检查用户是否已存在
        result = session.execute(
            text("SELECT id, username, role FROM users WHERE username = :username OR email = :email"),
            {"username": admin_user["username"], "email": admin_user["email"]}
        )
        existing = result.fetchone()

        if existing:
            print(f"[!] 用户已存在:")
            print(f"    ID: {existing[0]}")
            print(f"    用户名: {existing[1]}")
            print(f"    角色: {existing[2]}")

            # 更新为 admin 角色
            session.execute(
                text("UPDATE users SET role = 'admin', password_hash = :password_hash WHERE username = :username"),
                {"username": admin_user["username"], "password_hash": password_hash}
            )
            session.commit()
            print(f"[OK] 已更新用户角色为 admin，密码已重置为: {admin_user['password']}")
        else:
            # 创建新用户
            session.execute(
                text("""
                    INSERT INTO users (id, username, email, password_hash, role, is_active, created_at, updated_at)
                    VALUES (:id, :username, :email, :password_hash, :role, :is_active, NOW(), NOW())
                """),
                {
                    "id": admin_user["id"],
                    "username": admin_user["username"],
                    "email": admin_user["email"],
                    "password_hash": password_hash,
                    "role": admin_user["role"],
                    "is_active": admin_user["is_active"],
                }
            )
            session.commit()
            print(f"[OK] Admin 用户创建成功!")

        session.close()

        print()
        print("=" * 50)
        print("登录信息:")
        print(f"  URL: http://localhost:3000/login")
        print(f"  用户名: {admin_user['username']}")
        print(f"  密码: {admin_user['password']}")
        print("=" * 50)

    except Exception as e:
        print(f"[ERROR] {e}")
        raise

if __name__ == "__main__":
    create_admin_user()
