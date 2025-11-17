#!/usr/bin/env python3
"""
简化的pytest运行脚本
"""

import os
import sys
from pathlib import Path

# 设置环境变量
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test_secret_key_32_characters_long_123456"
os.environ["ENCRYPTION_KEY"] = "test_encryption_key_32_chars_long_123456"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "test_anon_key_12345"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test_service_role_key_12345"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000"

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

if __name__ == "__main__":
    import pytest

    # 设置pytest参数
    pytest_args = [
        "-v",  # 详细输出
        "--tb=short",  # 简短的错误回溯
        "-x",  # 遇到第一个失败就停止
        "--disable-warnings",  # 禁用警告
    ]

    # 如果有命令行参数，添加到pytest参数中
    if len(sys.argv) > 1:
        pytest_args.extend(sys.argv[1:])
    else:
        # 默认运行测试文件
        pytest_args.append("tests/")

    print(f"Running pytest with args: {' '.join(pytest_args)}")

    # 运行pytest
    exit_code = pytest.main(pytest_args)
    sys.exit(exit_code)