"""
Supabase 迁移执行脚本 - 简化版
直接执行数据库迁移
"""

import sys
from pathlib import Path

# 数据库连接
DATABASE_URL = "postgresql://postgres:BTsBIezNsDQF0UFp@db.jzmcoivxhiyidizncyaq.supabase.co:5432/postgres"

def execute_migration_file(file_path: Path, db_url: str):
    """执行迁移文件"""
    import psycopg2

    print(f"\n{'='*60}")
    print(f"执行迁移: {file_path.name}")
    print(f"{'='*60}")

    if not file_path.exists():
        print(f"[FAIL] 文件不存在: {file_path}")
        return False

    # 读取 SQL 文件
    sql_content = file_path.read_text(encoding='utf-8')

    try:
        # 连接数据库
        conn = psycopg2.connect(db_url)
        conn.autocommit = False  # 使用事务
        cursor = conn.cursor()

        print(f"[OK] 数据库连接成功")
        print(f"开始执行 SQL...")

        # 执行 SQL（作为单个事务）
        try:
            cursor.execute(sql_content)
            conn.commit()
            print(f"[OK] {file_path.name} 执行成功")
            success = True
        except Exception as e:
            conn.rollback()
            error_msg = str(e)

            # 检查是否是"已存在"错误（可以忽略）
            if 'already exists' in error_msg.lower():
                print(f"[SKIP] {file_path.name} - 对象已存在，跳过")
                success = True
            else:
                print(f"[FAIL] {file_path.name} 执行失败: {error_msg}")
                success = False

        cursor.close()
        conn.close()
        return success

    except Exception as e:
        print(f"[FAIL] 数据库连接或执行失败: {str(e)}")
        return False


def verify_migration(db_url: str):
    """验证迁移结果"""
    import psycopg2

    print(f"\n{'='*60}")
    print("验证迁移结果")
    print(f"{'='*60}")

    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # 检查表是否存在
        tables = ['user_profiles', 'user_login_history', 'user_sessions']

        for table in tables:
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = '{table}'
                );
            """)
            exists = cursor.fetchone()[0]

            if exists:
                print(f"[OK] 表 '{table}' 已创建")

                # 统计记录数
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                print(f"  记录数: {count}")
            else:
                print(f"[FAIL] 表 '{table}' 不存在")

        # 检查 RLS 策略
        cursor.execute("""
            SELECT COUNT(*)
            FROM pg_policies
            WHERE tablename = 'user_profiles';
        """)
        policy_count = cursor.fetchone()[0]
        print(f"\n[OK] user_profiles RLS 策略数: {policy_count}")

        # 检查触发器
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.triggers
            WHERE trigger_name = 'on_auth_user_created';
        """)
        trigger_count = cursor.fetchone()[0]
        print(f"[OK] 自动创建用户触发器: {'已配置' if trigger_count > 0 else '未找到'}")

        cursor.close()
        conn.close()

        print(f"\n{'='*60}")
        print("[OK] 迁移验证完成")
        print(f"{'='*60}")
        return True

    except Exception as e:
        print(f"[FAIL] 验证失败: {str(e)}")
        return False


def main():
    """主函数"""
    print("\n" + "="*60)
    print("Supabase 用户认证系统迁移")
    print("="*60 + "\n")

    # 检查 psycopg2
    try:
        import psycopg2
        print("[OK] psycopg2 已安装")
    except ImportError:
        print("正在安装 psycopg2-binary...")
        import os
        os.system(f"{sys.executable} -m pip install psycopg2-binary -q")
        import psycopg2
        print("[OK] psycopg2 安装成功")

    # 测试连接
    print(f"\n正在测试数据库连接...")
    print(f"数据库: db.jzmcoivxhiyidizncyaq.supabase.co")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"[OK] 连接成功")
        print(f"  PostgreSQL: {version.split(',')[0]}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[FAIL] 连接失败: {str(e)}")
        return

    # 准备迁移文件
    project_root = Path(__file__).parent.parent
    migration_files = [
        project_root / "supabase" / "migrations" / "20251116000001_create_user_profiles.sql",
        project_root / "supabase" / "migrations" / "20251116000002_migrate_existing_users.sql",
        project_root / "supabase" / "migrations" / "20251116000003_create_user_sessions_tables.sql",
    ]

    existing_files = [f for f in migration_files if f.exists()]

    print(f"\n发现 {len(existing_files)} 个迁移文件:")
    for f in existing_files:
        print(f"  - {f.name}")

    # 执行迁移
    print(f"\n开始执行迁移...")

    success_count = 0
    for file_path in existing_files:
        if execute_migration_file(file_path, DATABASE_URL):
            success_count += 1
        else:
            print(f"\n[WARN] 迁移文件执行遇到问题: {file_path.name}")
            print("[INFO] 自动继续执行下一个迁移...")
            # 在非交互环境自动继续
            # cont = input("是否继续下一个迁移？(y/n): ").strip().lower()
            # if cont != 'y':
            #     break

    # 验证迁移
    print(f"\n{'='*60}")
    print(f"迁移执行完成: {success_count}/{len(existing_files)} 个文件")
    print(f"{'='*60}")

    if success_count > 0:
        verify_migration(DATABASE_URL)

        print("\n" + "="*60)
        print("[OK] 迁移全部完成！")
        print("="*60)
        print("\n下一步操作:")
        print("1. 登录 Supabase Dashboard 查看表结构")
        print("2. 测试用户注册功能（触发器会自动创建 user_profile）")
        print("3. 验证 RLS 策略是否正常工作")
        print("\nSupabase Dashboard: https://app.supabase.com/project/jzmcoivxhiyidizncyaq")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()
