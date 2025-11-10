"""
数据库连接和会话管理模块
提供安全的数据库连接配置和会话管理
"""

import ssl
from typing import Generator, Optional
from urllib.parse import urlparse

from sqlalchemy import create_engine, MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from backend.core.config import get_settings

# 获取配置
settings = get_settings()

# 数据库基础配置
metadata = MetaData()
Base = declarative_base(metadata=metadata)

# 全局引擎和会话工厂
_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


class DatabaseConfig:
    """数据库配置管理"""

    @staticmethod
    def create_ssl_context() -> Optional[ssl.SSLContext]:
        """创建SSL连接上下文"""
        if settings.is_development():
            # 开发环境可以选择不使用SSL
            return None

        try:
            # 生产环境强制使用SSL
            context = ssl.create_default_context()
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED

            # 如果有自定义CA证书
            # context.load_verify_locations('path/to/ca.crt')

            return context
        except Exception as e:
            print(f"警告: SSL上下文创建失败: {e}")
            return None

    @staticmethod
    def get_database_url() -> str:
        """获取数据库连接URL"""
        database_url = settings.database_url

        # 为PostgreSQL添加SSL参数
        if database_url.startswith('postgresql://'):
            parsed = urlparse(database_url)

            # 构建查询参数
            query_params = []

            # 强制SSL（生产环境）
            if not settings.is_development():
                query_params.append('sslmode=require')
            else:
                query_params.append('sslmode=prefer')

            # 应用名称
            query_params.append('application_name=ai_finance_backend')

            # 连接超时
            query_params.append('connect_timeout=10')

            # 如果有查询参数，添加到URL
            if query_params:
                separator = '&' if '?' in database_url else '?'
                database_url += separator + '&'.join(query_params)

        return database_url

    @staticmethod
    def get_engine_kwargs() -> dict:
        """获取引擎配置参数"""
        kwargs = {
            # 连接池配置
            "pool_size": settings.pool_size,
            "max_overflow": settings.max_overflow,
            "pool_timeout": settings.pool_timeout,
            "pool_recycle": 3600,  # 1小时回收连接
            "pool_pre_ping": True,  # 连接前ping测试

            # 查询配置
            "echo": settings.debug,  # 开发环境打印SQL
            "echo_pool": settings.debug,  # 开发环境打印连接池信息

            # 隔离级别
            "isolation_level": "READ_COMMITTED",
        }

        # 添加SSL配置
        ssl_context = DatabaseConfig.create_ssl_context()
        if ssl_context:
            kwargs["connect_args"] = {
                "sslcontext": ssl_context
            }

        # SQLite特殊配置
        if settings.database_url.startswith('sqlite'):
            kwargs.update({
                "poolclass": StaticPool,
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": settings.pool_timeout
                }
            })

        return kwargs


def get_engine() -> Engine:
    """创建数据库引擎"""
    global _engine

    if _engine is None:
        database_url = DatabaseConfig.get_database_url()
        engine_kwargs = DatabaseConfig.get_engine_kwargs()

        _engine = create_engine(database_url, **engine_kwargs)

        print(f"✅ 数据库引擎创建成功")
        print(f"   数据库: {database_url.split('@')[-1] if '@' in database_url else 'SQLite'}")
        print(f"   连接池大小: {settings.pool_size}")
        print(f"   SSL: {'启用' if DatabaseConfig.create_ssl_context() else '禁用'}")

    return _engine


def get_session_factory() -> sessionmaker:
    """创建会话工厂"""
    global _SessionLocal

    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )

    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    用于FastAPI依赖注入
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()

    try:
        yield db
    except Exception as e:
        # 发生异常时回滚
        db.rollback()
        print(f"数据库会话异常: {e}")
        raise
    finally:
        # 确保会话关闭
        db.close()


class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        self.engine = get_engine()
        self.SessionLocal = get_session_factory()

    def create_tables(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            print("✅ 数据库表创建成功")
        except Exception as e:
            print(f"❌ 数据库表创建失败: {e}")
            raise

    def drop_tables(self):
        """删除所有表（谨慎使用）"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            print("⚠️ 数据库表已删除")
        except Exception as e:
            print(f"❌ 数据库表删除失败: {e}")
            raise

    def check_connection(self) -> bool:
        """检查数据库连接"""
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False

    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()

    def execute_sql(self, sql: str) -> any:
        """执行SQL语句"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(sql)
                return result
        except Exception as e:
            print(f"❌ SQL执行失败: {e}")
            raise


class DatabaseHealthChecker:
    """数据库健康检查器"""

    @staticmethod
    def check_connection_pool() -> dict:
        """检查连接池状态"""
        try:
            engine = get_engine()
            pool = engine.pool

            return {
                "status": "healthy",
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    @staticmethod
    def check_database_latency() -> dict:
        """检查数据库延迟"""
        try:
            import time
            start_time = time.time()

            engine = get_engine()
            with engine.connect() as conn:
                conn.execute("SELECT 1")

            latency = (time.time() - start_time) * 1000  # 转换为毫秒

            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "performance": "good" if latency < 100 else "slow" if latency < 500 else "poor"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "latency_ms": None
            }


# 全局数据库管理器实例
db_manager = DatabaseManager()

# 初始化函数
def init_database():
    """初始化数据库"""
    try:
        # 检查连接
        if not db_manager.check_connection():
            raise Exception("数据库连接失败")

        # 创建表
        db_manager.create_tables()

        print("✅ 数据库初始化完成")
        return True
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False


# 便捷函数
def get_db_session() -> Session:
    """获取数据库会话（便捷函数）"""
    return db_manager.get_session()


def execute_raw_sql(sql: str, params: dict = None) -> any:
    """执行原生SQL（便捷函数）"""
    try:
        with db_manager.get_session() as session:
            result = session.execute(sql, params or {})
            session.commit()
            return result
    except Exception as e:
        print(f"❌ SQL执行失败: {e}")
        raise
