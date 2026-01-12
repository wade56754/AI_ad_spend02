"""临时脚本：检查用户角色"""
import sys
import os
# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy.orm import Session
from core.db import get_db
from models import User

def check_user_roles():
    db: Session = next(get_db())
    
    # 查找所有用户
    users = db.query(User).all()
    
    print("=" * 60)
    print("数据库中的用户角色信息：")
    print("=" * 60)
    for user in users:
        print(f"ID: {user.id}")
        print(f"Email: {user.email}")
        print(f"Username: {user.username}")
        print(f"Role: {user.role} (type: {type(user.role)})")
        print(f"Is Active: {user.is_active}")
        print("-" * 60)
    
    # 检查是否有 admin 或 ceo 角色
    admin_users = db.query(User).filter(User.role.in_(["admin", "ceo"])).all()
    print(f"\n具有 admin 或 ceo 角色的用户数量: {len(admin_users)}")
    for user in admin_users:
        print(f"  - {user.email} ({user.username}): {user.role}")

if __name__ == "__main__":
    check_user_roles()

