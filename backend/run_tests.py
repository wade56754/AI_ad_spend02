#!/usr/bin/env python3
"""
运行测试脚本
解决模块导入路径问题
"""

import os
import sys
from pathlib import Path

# 将项目根目录添加到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ["PYTHONPATH"] = str(project_root)
os.environ["ENVIRONMENT"] = "test"

if __name__ == "__main__":
    import pytest

    # 运行指定的测试文件
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        print(f"运行测试文件: {test_file}")
        sys.exit(pytest.main([test_file, "-v", "--tb=short"]))
    else:
        # 运行所有测试
        print("运行所有测试...")
        sys.exit(pytest.main(["-v", "--tb=short"]))