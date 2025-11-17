#!/usr/bin/env python3
"""
简化的导入测试
"""

import os
import sys
from pathlib import Path

# 设置最少的环境变量
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test_secret_key_32_characters_long_123456"
os.environ["ENCRYPTION_KEY"] = "test_encryption_key_32_chars_long_123456"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "test_anon_key_12345"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test_service_role_key_12345"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000"

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 测试基本导入
try:
    print("Testing basic imports...")

    # 测试是否可以导入pydantic
    from pydantic import BaseModel
    print("OK: pydantic imported")

    # 测试是否可以导入FastAPI
    from fastapi import FastAPI
    print("OK: fastapi imported")

    # 测试SQLAlchemy
    from sqlalchemy import create_engine
    print("OK: sqlalchemy imported")

    print("Basic dependencies OK!")

except Exception as e:
    print(f"Basic import error: {e}")
    sys.exit(1)

# 测试项目模块
try:
    print("\nTesting project modules...")

    # 临时修改环境变量以避免JSON解析问题
    os.environ.pop("ALLOWED_ORIGINS", None)

    from core.config import get_settings
    print("OK: core.config imported")

    # 创建一个简单的SQLite内存数据库用于测试
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    from core.db import get_engine
    print("OK: core.db imported")

    print("Project modules OK!")

except Exception as e:
    print(f"Project module error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nImport tests completed successfully!")