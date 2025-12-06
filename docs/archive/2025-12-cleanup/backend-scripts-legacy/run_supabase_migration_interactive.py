"""
Supabase 数据库迁移脚本（交互式版本）
支持从 .env 文件、环境变量或交互输入获取配置
"""

import os
import sys
from pathlib import Path
from typing import Optional
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_env_file():
    """从 .env 文件加载环境变量"""
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        logger.info(f"从 {env_file} 加载配置...")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
                    if key.strip() in ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']:
                        logger.info(f"✓ 加载 {key.strip()}")


def get_supabase_config():
    """获取 Supabase 配置"""
    # 1. 尝试从环境变量读取
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

    # 2. 如果没有，尝试从 .env 文件读取
    if not supabase_url or not supabase_key:
        load_env_file()
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

    # 3. 如果还是没有，交互式输入
    if not supabase_url or not supabase_key:
        logger.info("\n" + "="*60)
        logger.info("请输入 Supabase 连接信息")
        logger.info("(可在 https://app.supabase.com → Settings → API 找到)")
        logger.info("="*60 + "\n")

        if not supabase_url:
            supabase_url = input("SUPABASE_URL (例如 https://xxxxx.supabase.co): ").strip()

        if not supabase_key:
            supabase_key = input("SUPABASE_SERVICE_ROLE_KEY: ").strip()

        # 询问是否保存到 .env
        save_to_env = input("\n是否保存到 .env 文件？(y/n): ").strip().lower()
        if save_to_env == 'y':
            env_file = Path(__file__).parent / '.env'
            with open(env_file, 'a', encoding='utf-8') as f:
                f.write(f"\n# Supabase 配置 (由迁移脚本添加)\n")
                f.write(f"SUPABASE_URL={supabase_url}\n")
                f.write(f"SUPABASE_SERVICE_ROLE_KEY={supabase_key}\n")
            logger.info(f"✓ 配置已保存到 {env_file}")

    return supabase_url, supabase_key


def execute_sql_via_psycopg2(sql: str, db_url: str) -> bool:
    """使用 psycopg2 执行 SQL"""
    try:
        import psycopg2

        conn = psycopg2.connect(db_url)
        conn.autocommit = True  # 自动提交
        cursor = conn.cursor()

        # 分割并执行多条语句
        statements = [s.strip() for s in sql.split(';') if s.strip()]

        for i, stmt in enumerate(statements, 1):
            try:
                logger.debug(f"执行语句 {i}/{len(statements)}...")
                cursor.execute(stmt)
            except Exception as e:
                # 某些错误可以忽略（如表已存在）
                if 'already exists' in str(e).lower():
                    logger.warning(f"语句 {i} 跳过（对象已存在）")
                else:
                    logger.error(f"语句 {i} 执行失败: {str(e)}")
                    raise

        cursor.close()
        conn.close()
        return True

    except ImportError:
        logger.error("未安装 psycopg2")
        logger.info("正在安装 psycopg2-binary...")
        os.system(f"{sys.executable} -m pip install psycopg2-binary")
        return execute_sql_via_psycopg2(sql, db_url)  # 重试

    except Exception as e:
        logger.error(f"SQL 执行失败: {str(e)}")
        return False


def execute_migration_file(file_path: Path, db_url: str) -> bool:
    """执行迁移文件"""
    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"执行迁移: {file_path.name}")
        logger.info(f"{'='*60}")

        if not file_path.exists():
            logger.error(f"文件不存在: {file_path}")
            return False

        # 读取 SQL 文件
        sql_content = file_path.read_text(encoding='utf-8')

        # 执行 SQL
        logger.info("开始执行 SQL...")
        if execute_sql_via_psycopg2(sql_content, db_url):
            logger.info(f"✓ {file_path.name} 执行成功")
            return True
        else:
            logger.error(f"✗ {file_path.name} 执行失败")
            return False

    except Exception as e:
        logger.error(f"执行迁移文件失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def build_database_url(supabase_url: str, supabase_key: str) -> str:
    """
    构建 PostgreSQL 连接字符串

    Supabase URL 格式: https://xxxxx.supabase.co
    PostgreSQL 连接: postgresql://postgres:[password]@db.xxxxx.supabase.co:5432/postgres
    """
    from urllib.parse import urlparse

    parsed = urlparse(supabase_url)
    project_ref = parsed.hostname.split('.')[0]

    # Supabase 的 service role key 就是数据库密码
    # 但实际上 Supabase 使用的是 JWT，需要特殊处理

    logger.info("\n请选择连接方式:")
    logger.info("1. 使用 Supabase PostgreSQL 直连（需要数据库密码）")
    logger.info("2. 使用自定义 DATABASE_URL")

    choice = input("\n请选择 (1/2): ").strip()

    if choice == '2':
        db_url = input("请输入完整的 DATABASE_URL (postgresql://...): ").strip()
        return db_url
    else:
        # 使用 Supabase 直连
        logger.info(f"\nSupabase 项目 ID: {project_ref}")
        logger.info(f"数据库主机: db.{project_ref}.supabase.co")

        db_password = input("\n请输入数据库密码 (在 Supabase → Settings → Database): ").strip()

        db_url = f"postgresql://postgres.{project_ref}:{db_password}@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

        # 询问是否正确
        logger.info(f"\n数据库连接URL: {db_url}")
        confirm = input("是否正确？(y/n): ").strip().lower()

        if confirm != 'y':
            return build_database_url(supabase_url, supabase_key)

        return db_url


def verify_connection(db_url: str) -> bool:
    """验证数据库连接"""
    try:
        import psycopg2

        logger.info("\n正在测试数据库连接...")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        logger.info(f"✓ 数据库连接成功")
        logger.info(f"  PostgreSQL 版本: {version[:50]}...")
        cursor.close()
        conn.close()
        return True

    except Exception as e:
        logger.error(f"✗ 数据库连接失败: {str(e)}")
        return False


def main():
    """主函数"""
    try:
        print("\n" + "="*60)
        print("Supabase 用户认证系统迁移工具")
        print("="*60 + "\n")

        # 1. 获取 Supabase 配置
        supabase_url, supabase_key = get_supabase_config()

        if not supabase_url or not supabase_key:
            logger.error("无法获取 Supabase 配置，退出")
            sys.exit(1)

        logger.info(f"\n✓ Supabase URL: {supabase_url}")
        logger.info(f"✓ Service Role Key: {supabase_key[:20]}...")

        # 2. 构建数据库连接
        db_url = build_database_url(supabase_url, supabase_key)

        # 3. 验证连接
        if not verify_connection(db_url):
            logger.error("数据库连接失败，请检查配置")
            sys.exit(1)

        # 4. 准备迁移文件
        project_root = Path(__file__).parent.parent
        migration_files = [
            project_root / "supabase" / "migrations" / "20251116000001_create_user_profiles.sql",
            project_root / "supabase" / "migrations" / "20251116000002_migrate_existing_users.sql",
            project_root / "supabase" / "migrations" / "20251116000003_create_user_sessions_tables.sql",
        ]

        existing_files = [f for f in migration_files if f.exists()]

        logger.info(f"\n发现 {len(existing_files)} 个迁移文件:")
        for f in existing_files:
            logger.info(f"  - {f.name}")

        # 5. 确认执行
        print("\n" + "="*60)
        confirm = input("确认执行迁移？(y/n): ").strip().lower()
        if confirm != 'y':
            logger.info("取消迁移")
            sys.exit(0)

        # 6. 执行迁移
        success_count = 0
        for file_path in existing_files:
            if execute_migration_file(file_path, db_url):
                success_count += 1
            else:
                logger.error(f"迁移失败: {file_path.name}")
                retry = input("\n是否继续下一个迁移？(y/n): ").strip().lower()
                if retry != 'y':
                    break

        # 7. 总结
        print("\n" + "="*60)
        print(f"迁移完成: {success_count}/{len(existing_files)} 个文件成功")
        print("="*60)

        if success_count == len(existing_files):
            logger.info("\n✓ 所有迁移执行成功！")
            logger.info("\n下一步:")
            logger.info("1. 登录 Supabase Dashboard 验证表结构")
            logger.info("2. 测试用户注册和登录功能")
            logger.info("3. 检查 RLS 策略是否生效")

    except KeyboardInterrupt:
        logger.info("\n\n用户中断操作")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
