#!/usr/bin/env python3
"""
简单的导入测试脚本
测试修复后的导入路径
"""

import os
import sys
from pathlib import Path

# 设置环境变量
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test_secret_key_32_characters_long_123456"
os.environ["ENCRYPTION_KEY"] = "test_encryption_key_32_chars_long_123456"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "test_anon_key_12345"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test_service_role_key_12345"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000,http://127.0.0.1:3000"

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    print("Testing module imports...")

    # 测试核心模块导入
    from core.config import get_settings
    print("OK: core.config imported")

    from core.db import get_db
    print("OK: core.db imported")

    from core.response import success_response, fail, ok
    print("OK: core.response imported")

    # 测试路由模块导入
    from routers import projects
    print("OK: routers.projects imported")

    from routers import ai_analytics
    print("OK: routers.ai_analytics imported")

    from routers import project_templates
    print("OK: routers.project_templates imported")

    # 测试主应用导入
    from main import app
    print("OK: main.app imported")

    print("\nAll core module import tests passed!")
    print("Import path fix successful!")

except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Other error: {e}")
    sys.exit(1)