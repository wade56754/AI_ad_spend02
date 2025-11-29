"""
AI财务系统配置管理模块
提供安全的环境变量配置管理，支持验证和默认值
"""

import os
import secrets
from functools import lru_cache
from typing import Any, List, Optional, Union

from pydantic import field_validator, Field
from pydantic_settings import BaseSettings


class SecurityConfig(BaseSettings):
    """安全相关配置"""
    jwt_secret: str = Field(..., min_length=64, description="JWT密钥，至少64字符")
    jwt_access_token_expire_minutes: int = Field(30, ge=5, le=1440, description="访问令牌过期时间（分钟）")
    jwt_refresh_token_expire_days: int = Field(7, ge=1, le=365, description="刷新令牌过期时间（天）")
    encryption_key: str = Field(..., min_length=32, description="数据加密密钥，至少32字符")

    @field_validator('jwt_secret')
    def validate_jwt_secret(cls, v):
        """验证JWT密钥强度"""
        if len(v) < 64:
            raise ValueError('JWT密钥长度必须至少64字符')
        # 检查是否是开发环境的弱密钥
        if 'dev' in v.lower() or 'example' in v.lower() or 'test' in v.lower():
            if os.getenv('ENV_NAME') == 'production':
                raise ValueError('生产环境不能使用开发环境密钥')
        return v


class Settings(BaseSettings):
    """主配置类，整合所有配置模块"""

    model_config = {
        'env_file': '.env',
        'env_file_encoding': 'utf-8',
        'case_sensitive': False,
        'extra': 'ignore',
    }
    app_name: str = Field("AI Finance Backend", description="应用名称")
    debug: bool = Field(False, description="调试模式")
    env_name: str = Field("development", description="运行环境")

    # 数据库配置
    database_url: str = Field("sqlite:///./ai_ad_spend_dev.db", description="数据库连接URL")
    pool_size: int = Field(20, ge=1, le=100, description="数据库连接池大小")
    max_overflow: int = Field(30, ge=0, le=100, description="数据库连接池最大溢出")
    pool_timeout: int = Field(30, ge=1, le=300, description="数据库连接池超时时间（秒）")

    # JWT和安全配置 - 从环境变量读取，无硬编码
    jwt_secret: str = Field(..., min_length=64, description="JWT密钥")
    jwt_access_token_expire_minutes: int = Field(30, ge=5, le=1440, description="JWT访问令牌过期时间（分钟）")
    jwt_refresh_token_expire_days: int = Field(7, ge=1, le=365, description="JWT刷新令牌过期时间（天）")
    encryption_key: str = Field(..., min_length=32, description="数据加密密钥")

    # Supabase配置 - 从环境变量读取，无硬编码
    supabase_url: str = Field(..., description="Supabase项目URL")
    supabase_anon_key: str = Field(..., min_length=20, description="Supabase匿名密钥")
    supabase_service_role_key: str = Field(..., min_length=20, description="Supabase服务角色密钥")
    supabase_fallback_url: Optional[str] = Field(None, description="备用Supabase项目URL")
    supabase_fallback_anon_key: Optional[str] = Field(None, description="备用Supabase匿名密钥")
    supabase_fallback_service_role_key: Optional[str] = Field(None, description="备用Supabase服务角色密钥")
    auto_failover: bool = Field(True, description="发生限额或故障时自动切换备用提供商")
    failback_after_seconds: int = Field(600, ge=10, le=86400, description="回切到主提供商的等待秒数")

    @property
    def supabase_key(self) -> str:
        """兼容性属性"""
        return self.supabase_anon_key

    @property
    def supabase_service_key(self) -> str:
        """兼容性属性"""
        return self.supabase_service_role_key

    # CORS配置
    # 注意：pydantic-settings 2.x 在 DotEnvSettingsSource 阶段会先尝试解析类型
    # 使用 Union[str, List[str]] 允许从 .env 读取逗号分隔字符串
    allowed_origins: Union[str, List[str]] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"],
        description="允许的源地址列表"
    )

    # API配置
    rate_limit: int = Field(100, ge=1, le=10000, description="API限流请求数")
    rate_window: int = Field(60, ge=1, le=3600, description="API限流时间窗口（秒）")
    max_file_size: int = Field(10485760, ge=1024, le=104857600, description="最大文件大小（字节）")

    # 日志配置
    log_level: str = Field("INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$", description="日志级别")

    @field_validator("allowed_origins", mode="before")
    def parse_allowed_origins(cls, v: Any) -> List[str]:
        """解析允许的源地址列表"""
        # 处理空字符串情况
        if isinstance(v, str) and not v.strip():
            return []
        if isinstance(v, str) and v.strip().startswith("["):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # JSON解析失败，按逗号分隔处理
                return [item.strip() for item in v.strip("[]").split(",") if item.strip()]
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v or []

    @field_validator("env_name")
    def validate_env_name(cls, v):
        """验证环境名称"""
        allowed_envs = ['development', 'staging', 'production']
        if v not in allowed_envs:
            raise ValueError(f'环境名称必须是以下之一: {allowed_envs}')
        return v

    @field_validator('database_url')
    def validate_database_url(cls, v):
        """验证数据库连接URL格式"""
        if not v.startswith(('postgresql://', 'mysql://', 'sqlite:///')):
            raise ValueError('数据库URL格式不正确')

        # 在所有环境中都不允许使用明显的弱密码
        weak_passwords = ['password', '123456', 'admin', 'test', 'root', 'guest']
        for weak_pw in weak_passwords:
            if weak_pw in v.lower():
                raise ValueError(f'数据库URL包含弱密码: {weak_pw}')

        return v

    @field_validator('supabase_url')
    def validate_supabase_url(cls, v):
        """验证Supabase URL格式"""
        if not v.startswith('https://') or '.supabase.co' not in v:
            raise ValueError('Supabase URL格式不正确')
        return v

    @field_validator('supabase_fallback_url')
    def validate_supabase_fallback_url(cls, v):
        if v is None or not str(v).strip():
            return None
        if not str(v).startswith('https://') or '.supabase.co' not in str(v):
            raise ValueError('备用Supabase URL格式不正确')
        return v

    def _validate_consistency(self):
        """验证配置一致性"""
        # 检查生产环境配置安全性
        if self.env_name == 'production':
            if self.debug:
                raise ValueError('生产环境不能开启调试模式')
            if self.log_level == 'DEBUG':
                raise ValueError('生产环境不能使用DEBUG日志级别')

    def __init__(self, **data):
        super().__init__(**data)
        self._validate_consistency()

    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return self.env_name == 'production'

    def is_development(self) -> bool:
        """判断是否为开发环境"""
        return self.env_name == 'development'

    def get_allowed_origins(self) -> List[str]:
        """获取允许的CORS源地址列表"""
        return self.allowed_origins

    def generate_secure_secret(self, length: int = 64) -> str:
        """生成安全的随机密钥"""
        return secrets.token_urlsafe(length)

    def validate_config(self) -> bool:
        """验证所有配置"""
        try:
            # 触发所有配置验证
            self.dict()
            return True
        except Exception as e:
            print(f"配置验证失败: {e}")
            return False

    

# 安全配置生成器
class ConfigGenerator:
    """配置生成器，用于生成安全的配置"""

    @staticmethod
    def generate_jwt_secret() -> str:
        """生成JWT密钥"""
        return secrets.token_urlsafe(64)

    @staticmethod
    def generate_encryption_key() -> str:
        """生成加密密钥"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_secure_config_template() -> str:
        """生成安全配置模板"""
        return f"""# 自动生成的安全配置
JWT_SECRET={ConfigGenerator.generate_jwt_secret()}
ENCRYPTION_KEY={ConfigGenerator.generate_encryption_key()}
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
API_RATE_LIMIT=100
API_RATE_WINDOW=60
LOG_LEVEL=INFO
ENV_NAME=production
"""


# 配置验证函数
def validate_environment() -> bool:
    """验证环境配置"""
    settings = get_settings()
    return settings.validate_config()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    import os

    # 清理冲突的环境变量
    conflicting_vars = ["ALLOWED_ORIGINS"]
    for var in conflicting_vars:
        if var in os.environ:
            # 如果环境变量存在但格式不正确，清除它
            value = os.environ[var]
            if isinstance(value, str):
                if not value.strip() or (not value.strip().startswith("[") and "," in value):
                    print(f"WARNING: 清理冲突的环境变量: {var}={value}")
                    os.environ[var] = ""

    try:
        # 尝试加载配置 - 临时忽略环境变量
        import os
        env_backup = os.environ.copy()

        # 清理有问题的环境变量
        problem_vars = ["ALLOWED_ORIGINS"]
        for var in problem_vars:
            if var in os.environ:
                del os.environ[var]

        settings = Settings()

        # 恢复环境变量
        os.environ.clear()
        os.environ.update(env_backup)

        # 验证关键配置
        if not settings.allowed_origins:
            print("WARNING: ALLOWED_ORIGINS 为空，使用默认值")
            settings.allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

        print(f"SUCCESS: 配置加载成功 - 环境: {settings.env_name}")
        print(f"   - 数据库: {settings.database_url}")
        print(f"   - 允许源: {settings.allowed_origins}")

        return settings

    except Exception as e:
        print(f"ERROR: 配置加载失败: {e}")
        print("RETRY: 使用安全默认配置...")

        # 提供默认配置（所有环境）- 使用生成的临时密钥
        return Settings(
            app_name="AI广告代投系统",
            debug=True,
            env_name="development",
            database_url="sqlite:///./ai_ad_spend_dev.db",
            jwt_secret=secrets.token_urlsafe(64),
            encryption_key=secrets.token_urlsafe(32),
            supabase_url=os.getenv("SUPABASE_URL", "https://placeholder.supabase.co"),
            supabase_anon_key=os.getenv("SUPABASE_ANON_KEY", "placeholder_anon_key_change_in_production"),
            supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", "placeholder_service_key_change_in_production"),
            allowed_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
            log_level="DEBUG"
        )


# 暂时注释掉模块级别的配置初始化，避免测试环境问题
# settings = get_settings()
# 配置验证
# if not validate_environment():
#     raise ValueError("环境配置验证失败，请检查配置文件")

    @field_validator('jwt_secret')
    def validate_jwt_secret_strength(cls, v, info):
        """验证JWT密钥强度和安全性"""
        import warnings
        
        # 检查长度要求
        if len(v) < 64:
            raise ValueError('JWT密钥长度必须至少64字符')
        
        # 检查是否使用了不安全的默认值
        weak_patterns = [
            'dev_secret', 'test_secret', 'example_secret', 'sample_secret',
            'your_64_character', 'changeme', 'password', 'secret123',
            '1234567890abcdefghijklmnopqrstuvwxyz'
        ]
        
        for pattern in weak_patterns:
            if pattern.lower() in v.lower():
                if info.data.get('env_name') == 'production':
                    raise ValueError('生产环境不能使用弱JWT密钥')
                else:
                    warnings.warn(
                        f'检测到弱JWT密钥模式: {pattern}。建议使用openssl rand -hex 32生成强密钥',
                        UserWarning
                    )
        
        return v

    @field_validator('encryption_key')
    def validate_encryption_key_strength(cls, v, info):
        """验证加密密钥强度和安全性"""
        import warnings
        
        # 检查长度要求
        if len(v) < 32:
            raise ValueError('加密密钥长度必须至少32字符')
        
        # 检查是否使用了不安全的默认值
        weak_patterns = [
            'dev_encryption', 'test_encryption', 'example_encryption',
            'your_32_character', 'changeme', 'password', 'key123',
            '12345678901234567890123456789012'
        ]
        
        for pattern in weak_patterns:
            if pattern.lower() in v.lower():
                if info.data.get('env_name') == 'production':
                    raise ValueError('生产环境不能使用弱加密密钥')
                else:
                    warnings.warn(
                        f'检测到弱加密密钥模式: {pattern}。建议使用openssl rand -hex 16生成强密钥',
                        UserWarning
                    )
        
        return v

    @field_validator('database_url')
    def validate_database_url_security(cls, v, info):
        """验证数据库URL安全性"""
        import warnings
        
        # 检查是否在生产环境使用SQLite
        if v.startswith('sqlite://') and info.data.get('env_name') == 'production':
            raise ValueError('生产环境必须使用PostgreSQL，不能使用SQLite')
        
        # 检查数据库URL中是否包含明文密码
        if ':' in v and '@' in v and 'password' in v.lower():
            warnings.warn(
                '数据库URL中可能包含明文密码。建议使用环境变量或连接池',
                UserWarning
            )
        
        return v
