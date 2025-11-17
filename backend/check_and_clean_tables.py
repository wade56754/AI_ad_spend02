"""
检查并清理 Supabase 中的现有表
在迁移前运行此脚本
"""

import psycopg2

DATABASE_URL = "postgresql://postgres:BTsBIezNsDQF0UFp@db.jzmcoivxhiyidizncyaq.supabase.co:5432/postgres"

def check_existing_tables():
    """检查现有表"""
    print("\n" + "="*60)
    print("检查现有表结构")
    print("="*60 + "\n")

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # 检查 user_profiles 表
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'user_profiles'
        );
    """)

    user_profiles_exists = cursor.fetchone()[0]

    if user_profiles_exists:
        print("[FOUND] user_profiles 表已存在")

        # 查看表结构
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'user_profiles'
            ORDER BY ordinal_position;
        """)

        columns = cursor.fetchall()
        print("\n当前表结构:")
        for col_name, col_type in columns:
            print(f"  - {col_name}: {col_type}")

        # 检查记录数
        cursor.execute("SELECT COUNT(*) FROM user_profiles;")
        count = cursor.fetchone()[0]
        print(f"\n记录数: {count}")

        print("\n需要删除现有表以执行迁移")
        print("[ACTION] 准备删除现有表...")

        # 删除表
        try:
            cursor.execute("DROP TABLE IF EXISTS user_profiles CASCADE;")
            conn.commit()
            print("[OK] user_profiles 表已删除")
        except Exception as e:
            print(f"[FAIL] 删除失败: {str(e)}")

    else:
        print("[OK] user_profiles 表不存在，可以直接迁移")

    # 检查其他表
    for table in ['user_login_history', 'user_sessions']:
        cursor.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = '{table}'
            );
        """)

        if cursor.fetchone()[0]:
            print(f"[FOUND] {table} 表已存在，准备删除...")
            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            conn.commit()
            print(f"[OK] {table} 表已删除")

    cursor.close()
    conn.close()

    print("\n" + "="*60)
    print("[OK] 清理完成，可以执行迁移")
    print("="*60)


if __name__ == "__main__":
    try:
        check_existing_tables()
    except Exception as e:
        print(f"[FAIL] 错误: {str(e)}")
        import traceback
        traceback.print_exc()
