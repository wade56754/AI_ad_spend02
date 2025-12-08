"""
agents/tests/conftest.py - Agent 测试配置

确保测试文件可以正确导入 agents 模块。
"""

import sys
import os
from pathlib import Path

# 获取项目根目录 (agents/tests/ -> agents/ -> project_root/)
project_root = Path(__file__).resolve().parent.parent.parent

# 确保项目根目录在 sys.path 最前面
project_root_str = str(project_root)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)
elif sys.path[0] != project_root_str:
    sys.path.remove(project_root_str)
    sys.path.insert(0, project_root_str)

# 设置 PYTHONPATH 环境变量
os.environ.setdefault("PYTHONPATH", project_root_str)
