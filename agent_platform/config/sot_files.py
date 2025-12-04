"""
agent_platform.config.sot_files - SoT 文档路径映射

Phase 1 迁移：从 agents/agents_config.py 迁移 SOT_FILES。

对齐版本：
- SoT Freeze v2.6
- Dev-Guides Freeze vFinal
- Agent Layer Freeze v1.0

迁移文档：docs/dev/AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md
"""

from pathlib import Path
from typing import Dict, Set
from .paths import BASE_PATH


# SoT 文档路径映射 (对齐 SoT Freeze v2.6 + Dev-Guides Freeze vFinal)
SOT_FILES: Dict[str, Path] = {
    # Layer 1: Overview
    "MASTER": BASE_PATH / "docs/1.overview/MASTER.md",
    "PROJECT": BASE_PATH / "docs/1.overview/PROJECT.md",
    "ARCHITECTURE": BASE_PATH / "docs/1.overview/ARCHITECTURE.md",
    "PATTERNS": BASE_PATH / "docs/1.overview/PATTERNS.md",
    "TESTING": BASE_PATH / "docs/1.overview/TESTING.md",
    "DOMAIN": BASE_PATH / "docs/1.overview/DOMAIN.md",
    "DEPLOYMENT": BASE_PATH / "docs/1.overview/DEPLOYMENT.md",

    # Layer 2: SoT (v2.6 Freeze)
    "API_SOT": BASE_PATH / "docs/2.sot/API_SOT.md",
    "DATA_SCHEMA": BASE_PATH / "docs/2.sot/DATA_SCHEMA.md",
    "STATE_MACHINE": BASE_PATH / "docs/2.sot/STATE_MACHINE.md",
    "BUSINESS_RULES": BASE_PATH / "docs/2.sot/BUSINESS_RULES.md",
    "ERROR_CODES": BASE_PATH / "docs/2.sot/ERROR_CODES_SOT.md",
    "LEDGER_SOT": BASE_PATH / "docs/2.sot/LEDGER_SOT.md",
    "DAILY_REPORT_SOT": BASE_PATH / "docs/2.sot/DAILY_REPORT_SOT.md",
    "RECONCILIATION_SOT": BASE_PATH / "docs/2.sot/RECONCILIATION_SOT.md",
    "TRANSFER_SOT": BASE_PATH / "docs/2.sot/TRANSFER_SOT.md",
    "AUTH_SPEC": BASE_PATH / "docs/2.sot/AUTH_SPEC.md",
    "RLS_POLICIES": BASE_PATH / "docs/2.sot/RLS_POLICIES_SOT.md",
    "TOPUP_SOT": BASE_PATH / "docs/2.sot/TOPUP_SOT.md",

    # Layer 3: Dev-Guides (vFinal Freeze)
    "FRONTEND_RULES": BASE_PATH / "docs/3.dev-guides/FRONTEND_DEVELOPMENT_RULES.md",
    "UI_DESIGN_SYSTEM": BASE_PATH / "docs/3.dev-guides/UI_DESIGN_SYSTEM.md",
    "UI_FLOW_SPEC": BASE_PATH / "docs/3.dev-guides/UI_FLOW_SPEC.md",
    "API_DEV_FLOW": BASE_PATH / "docs/3.dev-guides/API_DEVELOPMENT_FLOW.md",
    "DDD_ARCHITECTURE": BASE_PATH / "docs/3.dev-guides/DDD_API_ARCHITECTURE.md",
    "TESTING_STRATEGY": BASE_PATH / "docs/3.dev-guides/TESTING_STRATEGY.md",
    "AGENT_WORKFLOW": BASE_PATH / "docs/3.dev-guides/AGENT_WORKFLOW_GUIDE.md",

    # Test artifacts (可选)
    "DB_TEST_CASES": BASE_PATH / "tests/db_invariants_test_cases.md",
    "DB_INVARIANTS_SQL": BASE_PATH / "tests/db_invariants_test_v2.sql",
}


# 关键 SoT 文件（缺失时应发出警告）
CRITICAL_SOT_FILES: Set[str] = {
    "STATE_MACHINE",
    "DATA_SCHEMA",
    "BUSINESS_RULES",
    "API_SOT",
    "ERROR_CODES",
    "LEDGER_SOT",
    "AUTH_SPEC",
}


def get_sot_path(key: str) -> Path:
    """
    获取 SoT 文件路径。

    Args:
        key: SoT 文件键名（如 "STATE_MACHINE", "DATA_SCHEMA"）

    Returns:
        SoT 文件的完整路径

    Raises:
        KeyError: 如果键名不存在
    """
    if key not in SOT_FILES:
        available = ", ".join(sorted(SOT_FILES.keys()))
        raise KeyError(f"Unknown SoT key: {key}. Available: {available}")
    return SOT_FILES[key]


def list_sot_keys() -> list:
    """列出所有 SoT 文件键名"""
    return sorted(SOT_FILES.keys())
