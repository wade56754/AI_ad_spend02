"""
常量定义

基准文档: MASTER.md v4.8
版本: v5.0

变更记录:
- v5.0 (2026-01-01): 架构精简 - 统一为 6 阶段流水线，移除废弃角色
- v4.5 (2025-12-30): 重命名 CodeFactory 为 ContextEngine，统一版本号
- v4.4 (2025-12-27): 新增提示词系统
- v4.3 (2025-12-24): 新增任务卡匹配
"""

from typing import List, Set, Dict

# 版本号 - 此为代码工厂核心模块的单一版本来源
VERSION = "5.0.0"

# 6 阶段流水线名称 (与 factory.py 实现保持一致)
PHASE_NAMES: List[str] = [
    "SEARCH",  # Phase 1: 代码搜索
    "SELECT",  # Phase 2: 代码选型
    "ADAPT",  # Phase 3: 代码适配
    "ASSEMBLE",  # Phase 4: 代码组装
    "VERIFY",  # Phase 5: 代码验证
    "CONFIRM",  # Phase 6: 用户确认
]

# 高风险模块 (禁止代码工厂自动生成)
HIGH_RISK_MODULES: Set[str] = {
    "M8-LEDGER",  # 账本模块
    "M9-RECON",  # 对账模块
    "M10-PROFIT",  # 利润模块
}

# 高风险关键词
HIGH_RISK_KEYWORDS: Set[str] = {
    # 中文
    "账本",
    "对账",
    "利润",
    "冲正",
    "红冲",
    "资金安全",
    "财务审计",
    "余额",
    # 英文
    "ledger",
    "reconciliation",
    "profit",
    "reversal",
    "balance",
    "audit",
}

# SoT 文档期望版本 (2026-01-01 更新)
SOT_EXPECTED_VERSIONS: Dict[str, str] = {
    "MASTER.md": "v4.8",
    "STATE_MACHINE.md": "v2.8",
    "DATA_SCHEMA.md": "v5.7",
    "BUSINESS_RULES.md": "v4.8",
    "API_SOT.md": "v9.4",
    "ERROR_CODES_SOT.md": "v2.1",
}

# 业务角色 (MASTER.md v4.8 §2.4)
# 注意: supervisor 已废弃，合并到 project_owner
BUSINESS_ROLES: Set[str] = {
    "ceo",  # 老板
    "project_owner",  # 项目负责人
    "finance",  # 财务
    "pitcher",  # 投手
    "account_manager",  # 户管
    "admin",  # 管理员
}

# 技术角色 (数据库 CHECK 约束)
# 注意: data_operator 和 media_buyer 已废弃，使用 pitcher
TECH_ROLES: Set[str] = {
    "admin",
    "finance",
    "pitcher",  # 替代废弃的 media_buyer
    "account_manager",
}

# 日报状态 (STATE_MACHINE.md v2.8)
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
    "VAL",
    "AUTH",
    "BIZ",
    "DB",
    "INT",
    "SYS",
    "FIN",
    "RPT",
    "ACC",
    "PRJ",
    "PIT",
    "TOP",
    "IMP",
    "EXP",
    "REC",
    "SET",
}
