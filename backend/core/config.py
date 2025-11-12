"""
AI财务系统配置管理模块
提供安全的环境变量配置管理，支持验证和默认值
"""

import os
import secrets
from functools import lru_cache
from typing import Any, List, Optional

from pydantic import validator, Field
from pydantic_settings import BaseSettings


class SecurityConfig(BaseSettings):
    """安全相关配置"""
    jwt_secret: str = Field(..., min_length=64, description="JWT密钥，至少64字符")
    jwt_access_token_expire_minutes: int = Field(30, ge=5, le=1440, description="访问令牌过期时间（分钟）")
    jwt_refresh_token_expire_days: int = Field(7, ge=1, le=365, description="刷新令牌过期时间（天）")
    encryption_key: str = Field(..., min_length=32, description="数据加密密钥，至少32字符")

    @validator('jwt_secret')
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
    app_name: str = Field("AI Finance Backend", description="应用名称")
    debug: bool = Field(False, description="调试模式")
    env_name: str = Field("development", description="运行环境")

    # 数据库配置
    database_url: str = Field(..., description="数据库连接URL")
    pool_size: int = Field(20, ge=1, le=100, description="数据库连接池大小")
    max_overflow: int = Field(30, ge=0, le=100, description="数据库连接池最大溢出")

    # JWT和安全配置
    jwt_secret: str = Field(..., min_length=64, description="JWT密钥")
    jwt_access_token_expire_minutes: int = Field(30, ge=5, le=1440, description="JWT访问令牌过期时间（分钟）")
    jwt_refresh_token_expire_days: int = Field(7, ge=1, le=365, description="JWT刷新令牌过期时间（天）")
    encryption_key: str = Field(..., min_length=32, description="数据加密密钥")

    # Supabase配置
    supabase_url: str = Field(..., description="Supabase项目URL")
    supabase_key: str = Field(..., min_length=20, description="Supabase匿名密钥")
    supabase_service_key: Optional[str] = Field(None, description="Supabase服务密钥")

    # CORS配置
    allowed_origins: List[str] = Field(default_factory=list, description="允许的源地址列表")

    # API配置
    rate_limit: int = Field(100, ge=1, le=10000, description="API限流请求数")
    rate_window: int = Field(60, ge=1, le=3600, description="API限流时间窗口（秒）")
    max_file_size: int = Field(10485760, ge=1024, le=104857600, description="最大文件大小（字节）")

    # 日志配置
    log_level: str = Field("INFO", regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$", description="日志级别")

    @validator("allowed_origins", pre=True)
    def parse_allowed_origins(cls, v: Any) -> List[str]:
        """解析允许的源地址列表"""
        if isinstance(v, str) and v.strip().startswith("["):
            import json
            return json.loads(v)
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @validator("env_name")
    def validate_env_name(cls, v):
        """验证环境名称"""
        allowed_envs = ['development', 'staging', 'production']
        if v not in allowed_envs:
            raise ValueError(f'环境名称必须是以下之一: {allowed_envs}')
        return v

    @validator('database_url')
    def validate_database_url(cls, v):
        """验证数据库连接URL格式"""
        if not v.startswith(('postgresql://', 'mysql://', 'sqlite:///')):
            raise ValueError('数据库URL格式不正确')
        # 检查是否包含弱密码
        if 'password' in v.lower() or '123' in v or 'admin' in v:
            if os.getenv('ENV_NAME') == 'production':
                raise ValueError('生产环境不能使用弱密码')
        return v

    @validator('supabase_url')
    def validate_supabase_url(cls, v):
        """验证Supabase URL格式"""
        if not v.startswith('https://') or '.supabase.co' not in v:
            raise ValueError('Supabase URL格式不正确')
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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

        @classmethod
        def parse_env_var(cls, field_name: str, raw_value: str):
            if field_name == "allowed_origins":
                return raw_value
            return super().parse_env_var(field_name, raw_value)


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
    return Settings()


# 导出主要配置实例
settings = get_settings()

# 配置验证
if not validate_environment():
    raise ValueError("环境配置验证失败，请检查配置文件")

print(f"✅ 配置加载成功 - 环境: {settings.env_name}")
print(f"✅ 数据库配置: {settings.database_url[:20]}...")
print(f"✅ JWT配置: 已配置")
print(f"✅ CORS配置: {settings.allowed_origins}")
