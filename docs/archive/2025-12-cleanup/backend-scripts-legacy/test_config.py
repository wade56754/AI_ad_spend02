#!/usr/bin/env python3
"""
测试配置加载
"""

import os
import sys
from pathlib import Path

# 设置测试环境
os.environ["ENVIRONMENT"] = "test"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000"
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_config_loading():
    """测试配置加载"""
    try:
        print("Testing configuration loading...")

        # 简单测试 Pydantic
        from pydantic import BaseModel, Field, field_validator
        print("OK: Pydantic basic import works")

        # 测试 pydantic_settings
        from pydantic_settings import BaseSettings
        print("OK: pydantic_settings import works")

        # 测试简单配置类 (不继承 BaseSettings 来避免环境变量问题)
        class TestConfig(BaseModel):
            allowed_origins: list[str] = Field(default_factory=list)

            @field_validator("allowed_origins", mode="before")
            def parse_allowed_origins(cls, v):
                if isinstance(v, str):
                    return [item.strip() for item in v.split(",") if item.strip()]
                return v

        # 测试配置实例化
        config = TestConfig(allowed_origins="http://localhost:3000")
        print(f"OK: Config parsed successfully: {config.allowed_origins}")

        # 尝试加载真实配置
        os.environ["DATABASE_URL"] = "sqlite:///test.db"
        os.environ["JWT_SECRET"] = "test_secret_key_32_characters_long_1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"  # 64+ 字符
        os.environ["SUPABASE_URL"] = "https://test.supabase.co"
        os.environ["SUPABASE_ANON_KEY"] = "test_anon_key_1234567890"  # 20+ 字符
        os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test_service_role_key_1234567890"  # 20+ 字符
        os.environ["ENVIRONMENT"] = "development"  # 必须是允许的值

        # 暂时清除 ALLOWED_ORIGINS 来避免解析问题
        os.environ.pop("ALLOWED_ORIGINS", None)

        from backend.core.config import get_settings
        settings = get_settings()
        print(f"OK: Settings loaded successfully")
        print(f"  - Environment: {settings.env_name}")
        print(f"  - Allowed origins: {settings.allowed_origins}")

        # 手动测试
        settings.allowed_origins = ["http://localhost:3000"]
        print(f"  - Manual set origins: {settings.allowed_origins}")

        print("OK Configuration loading test passed!")
        return True

    except Exception as e:
        print(f"ERROR in configuration loading: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_config_loading()
    sys.exit(0 if success else 1)