from pathlib import Path

# 假设当前文件在 AI_ad_spend02/agents/agents_config.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DOCS_DIR = PROJECT_ROOT / "docs"
SOT_DIR = DOCS_DIR / "2.sot"
DEV_GUIDES_DIR = DOCS_DIR / "3.dev-guides"
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DB_DIR = BACKEND_DIR / "db"

# 单一事实来源文件（按 docs/2.sot/ 实际路径）
SOT_FILES = {
    "MASTER": DOCS_DIR / "1.overview" / "MASTER.md",
    "DATA_SCHEMA": SOT_DIR / "DATA_SCHEMA.md",
    "STATE_MACHINE": SOT_DIR / "STATE_MACHINE.md",
    "BUSINESS_RULES": SOT_DIR / "BUSINESS_RULES.md",
    "API_SOT": SOT_DIR / "API_SOT.md",
    "ERROR_CODES": SOT_DIR / "ERROR_CODES_SOT.md",
    "FRONTEND_RULES": DEV_GUIDES_DIR / "FRONTEND_RULES.md",
    # UI_DESIGN_SYSTEM 暂未创建，使用 FRONTEND_RULES 替代
    "UI_DESIGN_SYSTEM": DEV_GUIDES_DIR / "FRONTEND_RULES.md",
    "DB_TEST_CASES": DB_DIR / "TEST_CASES_v2.0.md",
    "DB_INVARIANTS_SQL": DB_DIR / "db_invariants_test_v2.sql",
    "INIT_SCHEMA_SQL": DB_DIR / "init_schema.sql",
}

def read_optional(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")

