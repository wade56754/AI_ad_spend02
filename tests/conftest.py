"""
pytest conftest.py - 项目级测试配置

Fix: 解决 pytest 导入路径问题
- 必须在文件最顶部设置 sys.path
- 确保 'from agents.xxx import' 可以正常工作
"""

# === 关键：必须在任何其他导入之前设置路径 ===
import sys
from pathlib import Path

# 计算项目根目录 (tests/ 的父目录)
ROOT_DIR = Path(__file__).resolve().parent.parent

# 插入到 sys.path 最前面
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# === 以下是 pytest fixtures ===
import pytest
import os

# 设置环境变量
os.environ.setdefault("PYTHONPATH", str(ROOT_DIR))


@pytest.fixture(scope="session")
def project_root():
    """返回项目根目录路径"""
    return ROOT_DIR


@pytest.fixture(scope="session")
def agents_dir():
    """返回 agents 目录路径"""
    return ROOT_DIR / "agents"


@pytest.fixture(scope="session")
def docs_dir():
    """返回 docs 目录路径"""
    return ROOT_DIR / "docs"
