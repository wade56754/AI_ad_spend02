#!/usr/bin/env python3
"""
迁移现有用户到Supabase Auth
Version: 1.0
Author: Claude协作开发
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import click
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from supabase import create_client

from core.config import get_settings
from models.user import User
from core.supabase_client import supabase_client


settings = get_settings()


@click.command()
@click.option('--dry-run', is_flag=True, default=False, help='试运行模式，不实际执行迁移')
@click.option('--batch-size', default=10, help='每批处理的用户数量')
def migrate(dry_run, batch_size):
    """迁移现有用户到Supabase Auth"""

    print("=" * 60)
    print("开始迁移用户到Supabase Auth")
    print("=" * 60)

    if dry_run:
        print("\n⚠️  试运行模式 - 不会实际执行迁移")

    # 1. 连接数据库
    print("\n1. 连接数据库...")
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 2. 获取Supabase管理员客户端
        print("2. 连接Supabase...")
        admin_client = supabase_client.get_admin_client()

        # 3. 获取现有用户
        print("\n3. 获取现有用户列表...")
        users = db.query(User).all()
        total_users = len(users)
        print(f"   找到 {total_users} 个用户")

        if total_users == 0:
            print("   没有需要迁移的用户")
            return

        # 4. 备份数据
        if not dry_run:
            print("\n4. 备份现有数据...")
            backup_data = []
            for user in users:
                backup_data.append({
                    'id': user.id,
                    'email': user.email,
                    'nickname': user.nickname,
                    'role': user.role,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                })

            import json
            with open(f'user_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
                json.dump(backup_data, f, indent=2)
            print("   ✓ 数据已备份")

        # 5. 开始迁移
        print(f"\n5. 开始迁移用户（批次大小: {batch_size}）...")

        success_count = 0
        error_count = 0

        for i in range(0, total_users, batch_size):
            batch = users[i:i + batch_size]
            print(f"\n   处理批次 {i//batch_size + 1}/{(total_users + batch_size - 1)//batch_size}")

            for user in batch:
                try:
                    # 检查用户是否已存在
                    existing_users = admin_client.auth.admin.list_users()
                    if any(u.email == user.email for u in existing_users.users):
                        print(f"   ⚠️  用户 {user.email} 已存在，跳过")
                        continue

                    if dry_run:
                        print(f"   [DRY RUN] 将迁移用户: {user.email} (角色: {user.role})")
                        success_count += 1
                        continue

                    # 在Supabase中创建用户
                    user_data = {
                        "email": user.email,
                        "password": "TempPassword123!",  # 临时密码，用户需要重置
                        "email_confirm": True,  # 直接确认邮箱
                        "user_metadata": {
                            "username": user.email.split("@")[0],
                            "full_name": user.nickname,
                            "role": user.role,
                            "migrated": True,
                            "migration_date": datetime.now().isoformat(),
                            "original_id": str(user.id)
                        }
                    }

                    # 创建用户
                    response = admin_client.auth.admin.create_user(user_data)

                    if response.user:
                        # 用户创建成功，等待触发器创建profile
                        print(f"   ✓ 成功迁移用户: {user.email}")
                        success_count += 1

                        # 稍微延迟，避免触发器冲突
                        await asyncio.sleep(0.1)
                    else:
                        print(f"   ❌ 迁移失败: {user.email} - 未返回用户数据")
                        error_count += 1

                except Exception as e:
                    print(f"   ❌ 迁移失败: {user.email} - {str(e)}")
                    error_count += 1

            # 批次之间稍作延迟
            if not dry_run:
                await asyncio.sleep(1)

        # 6. 输出结果
        print("\n" + "=" * 60)
        print("迁移完成！")
        print("=" * 60)
        print(f"总用户数: {total_users}")
        print(f"成功迁移: {success_count}")
        print(f"失败数量: {error_count}")

        if not dry_run:
            print("\n📝 后续步骤:")
            print("1. 通知所有用户使用邮箱登录，密码为: TempPassword123!")
            print("2. 提醒用户立即修改密码")
            print("3. 检查所有用户profile是否正确创建")
            print("4. 验证角色权限是否正确设置")

    finally:
        db.close()


@click.command()
def check_migration():
    """检查迁移状态"""
    print("\n检查迁移状态...")

    # 连接数据库
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 获取Supabase用户
        admin_client = supabase_client.get_admin_client()
        supabase_users = admin_client.auth.admin.list_users()

        # 获取旧表用户
        old_users = db.query(User).all()

        # 获取新表profiles
        try:
            from models.user_profile import UserProfile
            profiles = db.query(UserProfile).all()
        except:
            profiles = []

        print(f"\nSupabase Auth用户数: {len(supabase_users.users)}")
        print(f"旧表用户数: {len(old_users)}")
        print(f"Profile记录数: {len(profiles)}")

        # 检查未迁移的用户
        migrated_emails = {u.email for u in supabase_users.users}
        unmigrated = [u for u in old_users if u.email not in migrated_emails]

        if unmigrated:
            print(f"\n⚠️  未迁移用户数: {len(unmigrated)}")
            for user in unmigrated[:5]:  # 只显示前5个
                print(f"   - {user.email}")
            if len(unmigrated) > 5:
                print(f"   ... 还有 {len(unmigrated) - 5} 个")
        else:
            print("\n✅ 所有用户都已迁移")

        # 检查profile缺失
        profile_ids = {p.id for p in profiles}
        missing_profiles = []
        for supabase_user in supabase_users.users:
            if supabase_user.id not in profile_ids:
                missing_profiles.append(supabase_user.email)

        if missing_profiles:
            print(f"\n⚠️  缺少Profile的用户数: {len(missing_profiles)}")
            for email in missing_profiles[:5]:
                print(f"   - {email}")
        else:
            print("\n✅ 所有用户都有Profile记录")

    finally:
        db.close()


@click.command()
@click.option('--user-id', help='特定用户的ID')
@click.option('--email', help='特定用户的邮箱')
def create_profile(user_id, email):
    """为Supabase用户创建Profile"""
    if not user_id and not email:
        print("错误: 必须提供 user-id 或 email")
        return

    print(f"\n为用户创建Profile...")

    # 获取Supabase用户
    admin_client = supabase_client.get_admin_client()

    if email:
        # 通过邮箱查找用户
        users = admin_client.auth.admin.list_users()
        target_user = next((u for u in users.users if u.email == email), None)
    else:
        # 通过ID查找用户
        try:
            response = admin_client.auth.admin.get_user(user_id)
            target_user = response.user
        except:
            target_user = None

    if not target_user:
        print(f"错误: 找不到用户")
        return

    print(f"找到用户: {target_user.email}")

    # 创建Profile
    try:
        profile_data = {
            "id": target_user.id,
            "username": target_user.user_metadata.get("username"),
            "full_name": target_user.user_metadata.get("full_name"),
            "role": target_user.user_metadata.get("role", "media_buyer"),
            "is_active": True,
            "created_at": target_user.created_at,
            "updated_at": datetime.now().isoformat()
        }

        response = admin_client.table("user_profiles").insert(profile_data).execute()

        if response.data:
            print(f"✅ Profile创建成功")
        else:
            print(f"❌ Profile创建失败")

    except Exception as e:
        print(f"❌ 创建Profile失败: {str(e)}")


@click.group()
def cli():
    """用户迁移工具"""
    pass


# 添加命令
cli.add_command(migrate)
cli.add_command(check_migration)
cli.add_command(create_profile)


if __name__ == "__main__":
    cli()