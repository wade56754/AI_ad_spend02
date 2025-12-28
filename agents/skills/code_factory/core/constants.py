"""
常量定义

基准文档: MASTER.md v4.6
版本: v4.3
"""

from typing import List, Set, Dict

# 版本号
VERSION = "4.4.0"

# 10 阶段流水线名称
PHASE_NAMES: List[str] = [
    "INIT",      # Phase 0: 初始化
    "RISK",      # Phase 1: 风险评估
    "PARSE",     # Phase 2: 需求解析
    "SEARCH",    # Phase 3: 代码搜索
    "SELECT",    # Phase 4: 代码选型
    "ADAPT",     # Phase 5: 代码适配
    "ASSEMBLE",  # Phase 6: 代码组装
    "VERIFY",    # Phase 7: 代码验证
    "TRACE",     # Phase 8: 来源追溯
    "OUTPUT",    # Phase 9: 输出生成
]

# 高风险模块 (禁止代码工厂自动生成)
HIGH_RISK_MODULES: Set[str] = {
    "M8-LEDGER",      # 账本模块
    "M9-RECON",       # 对账模块
    "M10-PROFIT",     # 利润模块
}

# 高风险关键词
HIGH_RISK_KEYWORDS: Set[str] = {
    # 中文
    "账本", "对账", "利润", "冲正", "红冲",
    "资金安全", "财务审计", "余额",
    # 英文
    "ledger", "reconciliation", "profit",
    "reversal", "balance", "audit",
}

# SoT 文档期望版本
SOT_EXPECTED_VERSIONS: Dict[str, str] = {
    "MASTER.md": "v4.6",
    "STATE_MACHINE.md": "v2.7",
    "DATA_SCHEMA.md": "v5.6",
    "BUSINESS_RULES.md": "v3.2",
    "API_SOT.md": "v9.0",
    "ERROR_CODES_SOT.md": "v2.1",
}

# 业务角色 (MASTER.md v4.6 §2.4)
BUSINESS_ROLES: Set[str] = {
    "ceo",             # 老板
    "project_owner",   # 项目负责人
    "finance",         # 财务
    "pitcher",         # 投手
    "account_manager", # 户管
    "admin",           # 管理员
}

# 技术角色 (数据库 CHECK 约束)
TECH_ROLES: Set[str] = {
    "admin",
    "finance",
    "data_operator",
    "account_manager",
    "media_buyer",
}

# 日报状态 (STATE_MACHINE.md v2.7)
DAILY_REPORT_STATES: Set[str] = {
    "raw_submitted",
    "trend_pending",
    "trend_ok",
    "trend_flagged",
    "trend_resolved",
    "final_pending",
    "final_confirmed",
    "final_locked",
}

# 错误码前缀
ERROR_CODE_PREFIXES: Set[str] = {
    "VAL", "AUTH", "BIZ", "DB", "INT", "SYS",
    "FIN", "RPT", "ACC", "PRJ", "PIT", "TOP",
    "IMP", "EXP", "REC", "SET",
}
