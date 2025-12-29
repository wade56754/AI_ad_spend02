"""
高风险关键词和模块定义

基准文档: MASTER.md v4.6
版本: v4.2
"""

from typing import Set

# 高风险模块 (禁止代码工厂自动生成)
HIGH_RISK_MODULES: Set[str] = {
    # 财务核心模块
    "M8-LEDGER",      # 账本模块
    "M9-RECON",       # 对账模块
    "M10-PROFIT",     # 利润模块

    # 权限敏感模块
    "AUTH",           # 认证模块
    "PERMISSION",     # 权限模块
}

# 高风险关键词 (中文)
HIGH_RISK_KEYWORDS_CN: Set[str] = {
    # 财务相关
    "账本", "对账", "利润", "冲正", "红冲",
    "资金安全", "财务审计", "余额", "结算",
    "支付", "退款", "转账",

    # 权限相关
    "超级管理员", "越权", "提权",
    "密码", "密钥", "令牌",

    # 数据安全
    "删库", "清空数据", "全部删除",
}

# 高风险关键词 (英文)
HIGH_RISK_KEYWORDS_EN: Set[str] = {
    # Finance
    "ledger", "reconciliation", "profit",
    "reversal", "balance", "audit",
    "settlement", "payment", "refund",

    # Security
    "superadmin", "privilege", "escalation",
    "password", "secret", "token", "credential",

    # Data
    "drop_table", "truncate", "delete_all",
}

# 合并关键词
HIGH_RISK_KEYWORDS: Set[str] = HIGH_RISK_KEYWORDS_CN | HIGH_RISK_KEYWORDS_EN

# 中等风险关键词 (需要额外确认)
MEDIUM_RISK_KEYWORDS: Set[str] = {
    # 中文
    "批量", "导入", "导出", "同步",
    "迁移", "备份", "恢复",

    # 英文
    "batch", "import", "export", "sync",
    "migrate", "backup", "restore",
}
