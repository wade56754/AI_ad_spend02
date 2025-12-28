"""
pytest 配置与通用 fixtures

基准文档: MASTER.md v4.6
版本: v4.2
"""

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def project_root():
    """项目根目录"""
    return Path(__file__).parent.parent.parent.parent.parent


@pytest.fixture
def temp_dir():
    """临时目录 fixture"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_python_code():
    """示例 Python 代码"""
    return '''
from enum import Enum

class UserRole(Enum):
    """用户角色"""
    ADMIN = "admin"
    PITCHER = "pitcher"
    FINANCE = "finance"

def get_user_role(user_id: str) -> str:
    """获取用户角色"""
    return UserRole.ADMIN.value

def check_status(status: str) -> bool:
    """检查状态"""
    if status == "draft":
        return True
    return False
'''


@pytest.fixture
def sample_sot_data():
    """示例 SoT 数据"""
    from agents.skills.code_factory.sot.loader import LoadedSotData

    return LoadedSotData(
        roles={"admin", "pitcher", "finance", "ceo", "project_owner", "account_manager"},
        states={
            "daily_reports": {"draft", "submitted", "approved", "rejected", "locked"},
            "topup_requests": {"pending", "approved", "rejected", "completed"},
        },
        error_codes={"VAL", "AUTH", "BIZ", "SYS"},
        legacy_mapping={"supervisor": "admin"},
        versions={
            "MASTER.md": "v4.6",
            "STATE_MACHINE.md": "v2.7",
            "DATA_SCHEMA.md": "v5.6",
        },
    )


@pytest.fixture
def mock_sot_files(temp_dir):
    """创建模拟 SoT 文件"""
    sot_dir = temp_dir / "docs" / "sot"
    sot_dir.mkdir(parents=True)

    # MASTER.md
    master_content = '''# MASTER.md
version: v4.6

## 角色定义
| 角色 ID | 名称 |
|---------|------|
| admin | 管理员 |
| pitcher | 投手 |
| finance | 财务 |
| ceo | 老板 |
| project_owner | 项目负责人 |
| account_manager | 户管 |
'''
    (sot_dir / "MASTER.md").write_text(master_content, encoding="utf-8")

    # STATE_MACHINE.md
    state_content = '''# STATE_MACHINE.md
version: v2.7

## daily_reports 状态
| 状态 | 说明 |
|------|------|
| draft | 草稿 |
| submitted | 已提交 |
| approved | 已审批 |
| rejected | 已驳回 |
| locked | 已锁定 |
'''
    (sot_dir / "STATE_MACHINE.md").write_text(state_content, encoding="utf-8")

    # DATA_SCHEMA.md
    schema_content = '''# DATA_SCHEMA.md
version: v5.6

## 数据模型
'''
    (sot_dir / "DATA_SCHEMA.md").write_text(schema_content, encoding="utf-8")

    return temp_dir


@pytest.fixture
def sample_task_data():
    """示例任务数据"""
    return {
        "requirement": "添加用户权限检查功能",
        "module_id": "M3-USERS",
    }
