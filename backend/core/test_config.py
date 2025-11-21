"""
测试环境专用配置
"""

import os
from typing import List

# 测试环境固定配置
TEST_CONFIG = {
    "app_name": "AI广告代投系统",
    "debug": True,
    "env_name": "test",
    "database_url": "sqlite:///:memory:",
    "secret_key": "test_secret_key_32_characters_long_123456",
    "encryption_key": "test_encryption_key_32_chars_long_123456",
    "supabase_url": "https://test.supabase.co",
    "supabase_anon_key": "test_anon_key_12345",
    "supabase_service_role_key": "test_service_role_key_12345",
    "allowed_origins": ["http://localhost:3000"],
    "log_level": "DEBUG"
}

def get_test_settings():
    """获取测试环境配置"""
    from backend.core.config import Settings
    return Settings(**TEST_CONFIG)