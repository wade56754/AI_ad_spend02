"""
SoT 守门员 Skill（预留接口）

职责：
- 验证 AI 生成的代码是否违反 SoT 规则
- 检测是否发明了 SoT 中不存在的字段/状态/错误码
- 符合 PATTERNS.md AP-AI-002 要求
"""

from typing import Dict, List, Any


def validate_against_sot(changes: Dict[str, str]) -> Dict[str, Any]:
    """
    校验生成的代码是否符合 SoT 规范。

    Args:
        changes: 文件路径 -> 文件内容的字典

    Returns:
        {
            "passed": bool,
            "violations": List[Dict],  # 违规列表
            "warnings": List[Dict],    # 警告列表
        }

        违规/警告格式:
        {
            "file": str,           # 文件路径
            "rule": str,           # 违反的规则（如 "AP-AI-002"）
            "severity": str,       # "P0" | "P1" | "P2"
            "detail": str,         # 详细描述
            "line": Optional[int], # 行号（如果可定位）
        }
    """
    # TODO: 实现 SoT 规则校验逻辑
    # 1. 检查状态枚举是否来自 STATE_MACHINE.md
    # 2. 检查错误码是否来自 ERROR_CODES_SOT.md
    # 3. 检查数据库字段是否符合 DATA_SCHEMA.md
    # 4. 检查是否直接修改 balance 字段（违反 LEDGER_SOT.md）
    # 5. 检查是否绕过账本系统

    # 当前版本：占位实现，默认通过
    return {
        "passed": True,
        "violations": [],
        "warnings": [],
    }


def check_state_machine_compliance(code: str) -> List[Dict[str, Any]]:
    """
    检查代码中的状态枚举是否符合 STATE_MACHINE.md 定义。

    Args:
        code: 代码内容

    Returns:
        违规列表
    """
    # TODO: 实现状态机检查逻辑
    return []


def check_error_code_compliance(code: str) -> List[Dict[str, Any]]:
    """
    检查代码中的错误码是否符合 ERROR_CODES_SOT.md 定义。

    Args:
        code: 代码内容

    Returns:
        违规列表
    """
    # TODO: 实现错误码检查逻辑
    return []


def check_data_schema_compliance(code: str) -> List[Dict[str, Any]]:
    """
    检查代码中的数据库字段是否符合 DATA_SCHEMA.md 定义。

    Args:
        code: 代码内容

    Returns:
        违规列表
    """
    # TODO: 实现数据结构检查逻辑
    return []


def check_ledger_compliance(code: str) -> List[Dict[str, Any]]:
    """
    检查代码是否违反账本系统规则（LEDGER_SOT.md）。

    检查项：
    - 是否直接修改 balance 字段
    - 是否绕过 ledger_entries 表
    - 是否直接 UPDATE/DELETE ledger_entries

    Args:
        code: 代码内容

    Returns:
        违规列表
    """
    # TODO: 实现账本规则检查逻辑
    # 检测关键词：
    # - "balance =" / "balance +=" / "balance -="
    # - "UPDATE ledger_entries" / "DELETE FROM ledger_entries"
    return []
