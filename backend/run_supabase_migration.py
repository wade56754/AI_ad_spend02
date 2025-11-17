"""
Supabase 数据库迁移脚本
执行 user_profiles 相关表的迁移
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
from typing import Optional
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SupabaseMigrator:
    """Supabase 迁移工具"""

    def __init__(self):
        """初始化 Supabase 客户端"""
        self.supabase_url = os.environ.get('SUPABASE_URL')
        self.supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "缺少 Supabase 连接信息！\n"
                "请确保已设置以下环境变量：\n"
                "- SUPABASE_URL\n"
                "- SUPABASE_SERVICE_ROLE_KEY"
            )

        logger.info(f"正在连接到 Supabase: {self.supabase_url}")
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        logger.info("✓ Supabase 客户端初始化成功")

    def execute_sql(self, sql: str, description: str = "") -> bool:
        """
        执行 SQL 语句

        Args:
            sql: SQL 语句
            description: 操作描述

        Returns:
            是否执行成功
        """
        try:
            if description:
                logger.info(f"正在执行: {description}")

            # 使用 Supabase 的 RPC 或直接 SQL 执行
            # 注意：Supabase Python SDK 主要用于 REST API，执行原始 SQL 需要使用 postgrest
            result = self.client.postgrest.rpc('exec', {'query': sql}).execute()

            logger.info(f"✓ {description} - 执行成功")
            return True

        except Exception as e:
            logger.error(f"✗ {description} - 执行失败: {str(e)}")
            return False

    def execute_sql_file(self, file_path: Path) -> bool:
        """
        执行 SQL 文件

        Args:
            file_path: SQL 文件路径

        Returns:
            是否执行成功
        """
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"执行文件: {file_path.name}")
            logger.info(f"{'='*60}")

            if not file_path.exists():
                logger.error(f"文件不存在: {file_path}")
                return False

            # 读取 SQL 文件
            sql_content = file_path.read_text(encoding='utf-8')

            # 分割成独立的 SQL 语句
            # 注意：这是简单的分割，可能需要更复杂的解析器处理函数定义等
            statements = self._split_sql_statements(sql_content)

            logger.info(f"发现 {len(statements)} 条 SQL 语句")

            # 逐条执行
            success_count = 0
            for i, statement in enumerate(statements, 1):
                if statement.strip():
                    logger.info(f"\n[{i}/{len(statements)}] 执行中...")
                    if self._execute_raw_sql(statement):
                        success_count += 1
                    else:
                        logger.warning(f"语句 {i} 执行失败，继续执行下一条")

            logger.info(f"\n文件执行完成: {success_count}/{len(statements)} 条语句成功")
            return success_count > 0

        except Exception as e:
            logger.error(f"执行 SQL 文件失败: {str(e)}")
            return False

    def _split_sql_statements(self, sql_content: str) -> list[str]:
        """
        分割 SQL 语句
        简单按分号分割，跳过注释
        """
        statements = []
        current_statement = []
        in_function = False

        for line in sql_content.split('\n'):
            stripped = line.strip()

            # 跳过纯注释行
            if stripped.startswith('--') or not stripped:
                continue

            # 检测函数定义
            if 'CREATE OR REPLACE FUNCTION' in line.upper() or 'CREATE FUNCTION' in line.upper():
                in_function = True

            current_statement.append(line)

            # 如果在函数定义中，检测结束标记
            if in_function:
                if '$$' in line and line.count('$$') == 2:
                    in_function = False
                    statements.append('\n'.join(current_statement))
                    current_statement = []
            elif ';' in line:
                # 普通语句以分号结束
                statements.append('\n'.join(current_statement))
                current_statement = []

        # 添加最后一个语句（如果有）
        if current_statement:
            statements.append('\n'.join(current_statement))

        return statements

    def _execute_raw_sql(self, sql: str) -> bool:
        """
        执行原始 SQL（使用 psycopg2）
        """
        try:
            # 由于 Supabase Python SDK 不直接支持原始 SQL 执行
            # 我们需要使用 PostgreSQL 连接
            import psycopg2
            from urllib.parse import urlparse

            # 从 Supabase URL 构建 PostgreSQL 连接字符串
            # Supabase URL 格式: https://xxx.supabase.co
            # PostgreSQL 连接需要使用 db.xxx.supabase.co

            parsed_url = urlparse(self.supabase_url)
            project_ref = parsed_url.hostname.split('.')[0]

            # 构建 PostgreSQL 连接字符串
            # 注意：需要使用 service role key 作为密码
            db_host = f"db.{project_ref}.supabase.co"
            db_name = "postgres"
            db_user = "postgres"
            db_password = self.supabase_key.split('.')[-1] if '.' in self.supabase_key else self.supabase_key

            # 使用环境变量中的 DATABASE_URL（如果有）
            database_url = os.environ.get('DATABASE_URL')

            if database_url and 'supabase' in database_url:
                conn = psycopg2.connect(database_url)
            else:
                conn = psycopg2.connect(
                    host=db_host,
                    database=db_name,
                    user=db_user,
                    password=db_password,
                    port=5432
                )

            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
            cursor.close()
            conn.close()

            return True

        except ImportError:
            logger.error("未安装 psycopg2，正在尝试安装...")
            os.system(f"{sys.executable} -m pip install psycopg2-binary")
            return self._execute_raw_sql(sql)  # 重试

        except Exception as e:
            logger.error(f"SQL 执行错误: {str(e)}")
            logger.debug(f"SQL 内容:\n{sql[:200]}...")
            return False

    def verify_migration(self) -> bool:
        """验证迁移结果"""
        try:
            logger.info("\n" + "="*60)
            logger.info("验证迁移结果")
            logger.info("="*60)

            # 检查表是否存在
            tables_to_check = [
                'user_profiles',
                'user_login_history',
                'user_sessions'
            ]

            for table in tables_to_check:
                try:
                    result = self.client.table(table).select("*").limit(1).execute()
                    logger.info(f"✓ 表 '{table}' 存在且可访问")
                except Exception as e:
                    logger.error(f"✗ 表 '{table}' 检查失败: {str(e)}")
                    return False

            logger.info("\n✓ 迁移验证通过！")
            return True

        except Exception as e:
            logger.error(f"验证失败: {str(e)}")
            return False


def main():
    """主函数"""
    try:
        logger.info("="*60)
        logger.info("Supabase 用户认证迁移工具")
        logger.info("="*60)

        # 初始化迁移工具
        migrator = SupabaseMigrator()

        # 定义迁移文件列表
        project_root = Path(__file__).parent.parent
        migration_files = [
            project_root / "supabase" / "migrations" / "20251116000001_create_user_profiles.sql",
            project_root / "supabase" / "migrations" / "20251116000002_migrate_existing_users.sql",
            project_root / "supabase" / "migrations" / "20251116000003_create_user_sessions_tables.sql",
        ]

        # 检查文件是否存在
        for file_path in migration_files:
            if not file_path.exists():
                logger.warning(f"迁移文件不存在: {file_path}")

        # 执行迁移
        logger.info(f"\n发现 {len(migration_files)} 个迁移文件\n")

        success = True
        for file_path in migration_files:
            if file_path.exists():
                if not migrator.execute_sql_file(file_path):
                    logger.error(f"迁移文件执行失败: {file_path.name}")
                    success = False

                    # 询问是否继续
                    response = input("\n是否继续执行下一个迁移文件？(y/n): ")
                    if response.lower() != 'y':
                        break

        # 验证迁移
        if success:
            migrator.verify_migration()

        logger.info("\n" + "="*60)
        logger.info("迁移完成！")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
