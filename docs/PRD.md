# PRD: AI 广告代投管理系统（AI 编程规格版）

> **文档版本**: v2.2 (AI Programming Spec)
> **技术基准**: MASTER.md v4.6 + STATE_MACHINE.md v2.8 + DATA_SCHEMA.md v5.6
> **用途**: Claude/AI 编程参考，减少幻觉，约束边界
> **日期**: 2025-12-27
> **状态**: Frozen
> **变更**: v2.2 基于确认的业务事实更新角色、数据SoT、成本结构、利润公式

---

## ⚠️ AI 必读：本文档使用规则

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     AI 编程三条铁律                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. 【只引用，不发明】                                                   │
│     所有状态、角色、错误码必须来自 SoT 文档                              │
│     如果 SoT 没定义 → 停止 → 询问用户                                   │
│                                                                         │
│  2. 【只提示，不阻断】                                                   │
│     Phase 1 禁止生成任何"自动拒绝/暂停/终止"的代码                       │
│     发现异常 → 记录 + 高亮 + 返回，不阻断流程                            │
│                                                                         │
│  3. 【遇歧义，必停止】                                                   │
│     遇到模糊需求 → 列出可能解释 → 询问用户                               │
│     禁止"合理推测"或"灵活处理"                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 0. SoT 版本锁定（AI 必须对齐）

```python
# ===== SoT 版本锁定 =====
SOT_VERSIONS = {
    "MASTER.md": "v4.6",
    "STATE_MACHINE.md": "v2.8",
    "DATA_SCHEMA.md": "v5.6",
    "LEDGER_SOT.md": "v1.2",
    "ERROR_CODES_SOT.md": "v2.2",
    "AUTH_SPEC.md": "v2.1",
    "BUSINESS_RULES.md": "v4.7",
    "API_SOT.md": "v9.4"
}
```

**AI 生成代码前必查**：
```
□ 步骤 0：确认当前是 Phase 1 还是 Phase 2（默认 Phase 1）
□ 步骤 1：查询相关 SoT 文档版本号是否与上述一致
□ 步骤 2：确认使用的表名/字段名在 DATA_SCHEMA.md v5.6 中存在
□ 步骤 3：确认状态流转在 STATE_MACHINE.md v2.8 白名单中
□ 步骤 4：确认角色在本文档 §1 的 6 角色中
```

---

## 1. 业务模型概览

### 1.1 核心业务流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         广告代投业务全流程                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  【阶段1: 项目启动】                                                     │
│  甲方下单 → 项目经理接单 → 户管联系代理商下户 → 账户分配给投手            │
│                                                                         │
│  【阶段2: 充值流程】                                                     │
│  投手申请充值 → 户管收集 → 财务审批 → 转账(广告费含手续费) → 代理商充值   │
│                           ↑                                             │
│                      不需要老板参与                                      │
│                                                                         │
│  【阶段3: 投放运营（每日循环）】                                          │
│  广告投放 → 甲方渠道进线                                                 │
│              ↓                                                          │
│  投手填日报(申报消耗+申报进粉) → 项目经理审核                             │
│              ↓                                                          │
│  项目经理统计实际消耗(从平台拉取)                                         │
│              ↓                                                          │
│  项目经理跟甲方确认实际进粉                                               │
│                                                                         │
│  【阶段4: 项目结算】                                                     │
│  项目结束 → 跟甲方确认有效粉 → 按有效粉计费 → 收款                        │
│                                                                         │
│  【阶段5: 死号处理】                                                     │
│  账户封禁(有余额) → 投手报清零 → 户管报代理商 → 清零 → 余额转移           │
│                                                                         │
│  【阶段6: 月度核算】                                                     │
│  统计各代理商押款 → 汇总收支 → 确认利润                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 角色职责表（6 个核心角色）

```python
# ===== 角色白名单（6 角色）=====
VALID_ROLES = frozenset([
    "ceo",             # 老板
    "project_owner",   # 项目经理
    "finance",         # 财务
    "pitcher",         # 投手
    "account_manager", # 户管
    "admin"            # 管理员
])
```

| 角色 | 系统标识 | 核心职责 | 关键操作 |
|------|---------|---------|---------|
| **老板** | `ceo` | 资金安全、最终决策、月度锁账 | 查看利润报表、锁账确认 |
| **项目经理** | `project_owner` | 项目盈亏、团队管理、数据统计 | 接单、分配账户、审核日报、统计实际消耗、确认有效粉 |
| **财务** | `finance` | 资金出入、审批充值、月度核算 | 审批充值、转账、利润核算 |
| **投手** | `pitcher` | 广告投放、日报填报 | 投放广告、填日报、申请充值 |
| **户管** | `account_manager` | 账户管理、代理商对接 | 联系代理商下户、处理充值、清零转移 |
| **管理员** | `admin` | 系统配置 | 用户管理、系统设置（不参与业务） |

**⚠️ 重要说明**：
- 项目经理同时承担"数据员"职责（统计实际消耗）
- 不需要单独的 `supervisor` 或 `data_operator` 角色
- 充值审批链：投手 → 户管 → 财务（**不需要老板参与**）

### 1.3 数据 SoT 体系（三层数据）

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         数据 SoT 体系                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  【第一层: 行为记录】投手日报（参考值，非财务依据）                        │
│  ┌─────────────────┐    ┌─────────────────┐                            │
│  │ 申报消耗         │    │ 申报进粉         │                            │
│  │ daily_report    │    │ daily_report    │   ← 投手每日填报            │
│  │ .reported_spend │    │ .reported_leads │                            │
│  └─────────────────┘    └─────────────────┘                            │
│           ↓                      ↓                                      │
│  【第二层: 实际数据】项目经理统计/确认                                    │
│  ┌─────────────────┐    ┌─────────────────┐                            │
│  │ 实际消耗         │    │ 实际进粉         │                            │
│  │ (成本 SoT)      │    │ (过程监控)       │   ← 项目经理统计            │
│  │ 从平台拉取       │    │ 跟甲方确认       │                            │
│  └─────────────────┘    └─────────────────┘                            │
│           ↓                      ↓                                      │
│  【第三层: 结算数据】甲方最终确认                                         │
│                         ┌─────────────────┐                            │
│                         │ 有效粉           │                            │
│                         │ (收入 SoT)       │   ← 项目结束时甲方确认      │
│                         │ 计费依据         │                            │
│                         └─────────────────┘                            │
│                                  ↓                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              收入 = 有效粉 × 单价                                 │   │
│  │              利润 = 总收入 - 总支出                               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

| 数据层 | 数据 | 来源 | 确认人 | 用途 |
|--------|------|------|--------|------|
| 行为记录 | 申报消耗 | 投手日报 | 投手 | 参考值 |
| 行为记录 | 申报进粉 | 投手日报 | 投手 | 参考值 |
| 实际数据 | **实际消耗** | 平台数据 | 项目经理 | **成本依据** |
| 实际数据 | 实际进粉 | 甲方反馈 | 项目经理 | 过程监控 |
| 结算数据 | **有效粉** | 甲方确认 | 项目经理 | **收入依据（计费）** |

---

## 2. 成本结构（3 类支出）

### 2.1 支出分类

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              总支出                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  【类型1: 广告费充值】ad_topup                                           │
│  ├── 定义：充值到代理商/渠道的广告费                                     │
│  ├── 特点：手续费已包含在充值金额中（如 500×1.11=555）                   │
│  ├── 归属：按代理商/渠道统计                                             │
│  ├── 示例：流苏、岳总、HT、星链-AdNova、VCC-新系统、凤凰渠道-泰华        │
│  └── 占比：约 85%+                                                      │
│                                                                         │
│  【类型2: 广告配套】ad_support                                           │
│  ├── 定义：投放所需的配套资源                                            │
│  ├── 归属：公司统一记账（不分摊到项目）                                   │
│  ├── 明细：                                                             │
│  │   • BM 购买（BM×5=$25/次）                                           │
│  │   • IP 代理（$288/40个）                                             │
│  │   • 谷歌邮箱（$14/8个）                                              │
│  │   • VPN 续费                                                         │
│  │   • ADS 工具续费                                                     │
│  │   • 防护续费                                                         │
│  │   • 主页（认证/普通/复审/中文认证）                                   │
│  │   • 个号、TK白号                                                     │
│  │   • 工单                                                             │
│  └── 占比：约 3-5%                                                      │
│                                                                         │
│  【类型3: 后勤支出】overhead                                             │
│  ├── 定义：公司日常运营开支                                              │
│  ├── 归属：公司统一记账                                                  │
│  ├── 明细：                                                             │
│  │   • 工资（所有员工）                                                  │
│  │   • 换汇                                                             │
│  │   • 外包/兼职周结算                                                   │
│  │   • 房租水电                                                         │
│  │   • 日常消耗                                                         │
│  └── 占比：约 10-12%                                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 支出类型枚举

```python
# ===== 支出类型枚举 =====
EXPENSE_CATEGORY = frozenset([
    "ad_topup",    # 广告费充值（含手续费）
    "ad_support",  # 广告配套
    "overhead"     # 后勤支出
])

# ===== 广告配套明细 =====
AD_SUPPORT_ITEMS = frozenset([
    "bm",          # BM购买
    "ip",          # IP代理
    "email",       # 谷歌邮箱
    "vpn",         # VPN续费
    "ads_tool",    # ADS工具
    "protection",  # 防护续费
    "page",        # 主页（认证/普通/复审）
    "account",     # 个号/TK白号
    "ticket"       # 工单
])

# ===== 后勤支出明细 =====
OVERHEAD_ITEMS = frozenset([
    "salary",      # 工资
    "exchange",    # 换汇
    "outsource",   # 外包/兼职
    "rent",        # 房租水电
    "daily"        # 日常消耗
])
```

### 2.3 手续费说明

```python
# ⚠️ 重要：手续费已包含在充值金额中，不单独记录
# 示例：充值 500 美金，费率 11%，实际支出 500 × 1.11 = 555

# 系统记录方式
topup_record = {
    "amount": 555,           # 实际支出金额（含手续费）
    "supplier": "流苏",       # 代理商/渠道
    "fee_included": True     # 手续费已包含
}

# 如需分析费率，可从备注中解析
# 备注示例："500*1.11=555" → 本金500，费率11%
```

---

## 3. 利润计算

### 3.1 核心公式

```python
# ===== 最简公式 =====
公司利润 = 总收入 - 总支出

# ===== 展开公式 =====
公司利润 = Σ项目收款 - (Σ广告费充值 + Σ广告配套 + Σ后勤支出)

# ===== 代码实现 =====
def calculate_profit(period: str) -> dict:
    """
    计算指定周期的利润
    
    Args:
        period: 周期标识，如 "2025-12"
    
    Returns:
        dict: 利润明细
    """
    # 总收入 = 所有项目收款
    total_income = sum(
        income.amount 
        for income in Income.query.filter_by(period=period)
    )
    
    # 总支出 = 广告充值 + 广告配套 + 后勤
    total_ad_topup = sum(
        expense.amount 
        for expense in Expense.query.filter_by(
            period=period, 
            category="ad_topup"
        )
    )
    total_ad_support = sum(
        expense.amount 
        for expense in Expense.query.filter_by(
            period=period, 
            category="ad_support"
        )
    )
    total_overhead = sum(
        expense.amount 
        for expense in Expense.query.filter_by(
            period=period, 
            category="overhead"
        )
    )
    
    total_expense = total_ad_topup + total_ad_support + total_overhead
    profit = total_income - total_expense
    
    return {
        "period": period,
        "income": total_income,
        "expense": {
            "ad_topup": total_ad_topup,
            "ad_support": total_ad_support,
            "overhead": total_overhead,
            "total": total_expense
        },
        "profit": profit,
        "margin": profit / total_income if total_income > 0 else 0
    }
```

### 3.2 项目毛利（可选，用于项目级分析）

```python
# 项目毛利 = 项目收款 - 项目广告费充值
def calculate_project_gross_profit(project_id: str) -> dict:
    """
    计算单个项目的毛利
    注意：广告配套和后勤支出不分摊到项目
    """
    project_income = sum(
        income.amount 
        for income in Income.query.filter_by(project_id=project_id)
    )
    project_ad_topup = sum(
        expense.amount 
        for expense in Expense.query.filter_by(
            project_id=project_id,
            category="ad_topup"
        )
    )
    
    return {
        "project_id": project_id,
        "income": project_income,
        "ad_topup": project_ad_topup,
        "gross_profit": project_income - project_ad_topup
    }
```

### 3.3 押款统计

```python
# ===== 押款定义 =====
# 押款 = 代理商那边未消耗完的广告费余额
# 押款 = Σ历史充值 - Σ历史消耗

def calculate_supplier_deposit(supplier_id: str) -> Decimal:
    """
    计算指定代理商的押款（未消耗余额）
    
    Args:
        supplier_id: 代理商ID
    
    Returns:
        Decimal: 押款金额
    """
    # 历史充值总额
    total_topup = sum(
        topup.amount 
        for topup in Topup.query.filter_by(supplier_id=supplier_id)
    )
    
    # 历史消耗总额
    total_spend = sum(
        spend.amount 
        for spend in AdSpend.query.filter_by(supplier_id=supplier_id)
    )
    
    return total_topup - total_spend
```

---

## 4. 状态机白名单

### 4.1 日报状态机

```python
# ===== Phase 1 简化版（3 状态，当前使用）=====
PHASE1_DAILY_REPORT_STATUS = frozenset([
    "raw_submitted",    # 投手已提交
    "trend_ok",         # 项目经理已审核
    "final_confirmed"   # 数据已确认
])

# ===== Phase 1 合法流转 =====
PHASE1_TRANSITIONS = {
    "raw_submitted": ["trend_ok"],           # 项目经理审核
    "trend_ok": ["final_confirmed"],         # 确认数据
    "final_confirmed": []                     # 终态
}

# ===== Phase 1 跳过的状态（禁止使用）=====
PHASE1_SKIPPED_STATUS = frozenset([
    "trend_pending",    # 跳过
    "trend_flagged",    # 跳过
    "trend_resolved",   # 跳过
    "final_pending",    # 跳过
    "final_locked"      # 跳过
])
```

### 4.2 充值状态机

```python
# ===== 充值状态 =====
TOPUP_STATUS = frozenset([
    "draft",            # 草稿（投手创建）
    "pending_review",   # 待审核（户管已提交）
    "approved",         # 已审批（财务通过）
    "paid",             # 已转账
    "completed",        # 已完成（代理商已充值）
    "rejected",         # 已拒绝
    "cancelled"         # 已取消
])

# ===== 充值审批链（不含老板）=====
TOPUP_APPROVAL_CHAIN = [
    ("pitcher", "draft"),           # 投手创建
    ("account_manager", "pending_review"),  # 户管提交
    ("finance", "approved"),        # 财务审批
    ("finance", "paid"),            # 财务转账
    ("account_manager", "completed") # 户管确认到账
]
```

### 4.3 账户状态

```python
AD_ACCOUNT_STATUS = frozenset([
    "new",        # 新建
    "testing",    # 测试中
    "active",     # 正常使用
    "suspended",  # 暂停
    "dead",       # 死户（终态）
    "archived"    # 归档（终态）
])
```

---

## 5. AI 防幻觉原则（AH-01 ~ AH-05）

### AH-01: 禁止假设数据一致

```python
# ❌ 错误：假设数据一定存在
def get_daily_report(report_id):
    report = db.query(DailyReport).get(report_id)
    return report.spend  # 如果 report 为 None 会崩溃

# ✅ 正确：处理数据缺失
def get_daily_report(report_id):
    report = db.query(DailyReport).get(report_id)
    if not report:
        return {"status": "not_found", "data": None}
    return {"status": "ok", "data": report}
```

### AH-02: 禁止自动做管理裁决

```python
# ❌ 错误：自动拒绝/暂停
if cpl > target * 1.5:
    report.status = "rejected"  # 禁止！

# ✅ 正确：只记录 + 高亮
if cpl > target * 1.5:
    report.alert_level = "warning"  # 仅标记
    log_anomaly(report_id, "CPL 超标 50%")  # 仅记录
```

### AH-03: 禁止引入 SoT 未定义的概念

```python
# ❌ 错误：发明新角色
def check_permission(user):
    if user.role == "data_operator":  # SoT 没有这个角色！
        return True

# ✅ 正确：使用 SoT 定义的角色
def check_permission(user):
    if user.role == "project_owner":  # 项目经理承担数据统计职责
        return True
```

### AH-04: 必须遵循 Phase 1 软性原则

```python
# Phase 1 行为模式
PHASE1_BEHAVIOR = {
    "发现异常": "记录 + 高亮",      # 不阻断
    "超出阈值": "提示 + 返回",      # 不拒绝
    "数据不完整": "标记待确认",     # 不报错
    "审批超时": "通知相关人",       # 不升级
}
```

### AH-05: 遇到歧义必须停止并询问

```python
# ❌ 错误：自行决定
def calculate_fee(amount):
    return amount * 0.03  # 用户没说费率，禁止猜测！

# ✅ 正确：停止并询问
def calculate_fee(amount, fee_rate=None):
    if fee_rate is None:
        raise AmbiguityError(
            "费率未定义",
            options=["从代理商配置读取", "固定费率"],
            action="请用户确认"
        )
    return amount * fee_rate
```

---

## 6. 核心业务规则

### 6.1 充值流程

```python
# ===== 充值审批链 =====
# 投手申请 → 户管收集 → 财务审批 → 转账 → 代理商充值
# 注意：不需要老板参与！

TOPUP_WORKFLOW = {
    "step1": {
        "action": "创建充值申请",
        "actor": "pitcher",
        "from_status": None,
        "to_status": "draft"
    },
    "step2": {
        "action": "提交审核",
        "actor": "account_manager",
        "from_status": "draft",
        "to_status": "pending_review"
    },
    "step3": {
        "action": "审批通过",
        "actor": "finance",
        "from_status": "pending_review",
        "to_status": "approved"
    },
    "step4": {
        "action": "转账",
        "actor": "finance",
        "from_status": "approved",
        "to_status": "paid"
    },
    "step5": {
        "action": "确认到账",
        "actor": "account_manager",
        "from_status": "paid",
        "to_status": "completed"
    }
}
```

### 6.2 日报流程

```python
# ===== 日报流程 =====
DAILY_REPORT_WORKFLOW = {
    "step1": {
        "action": "填写日报",
        "actor": "pitcher",
        "content": ["申报消耗", "申报进粉"],
        "to_status": "raw_submitted"
    },
    "step2": {
        "action": "审核日报",
        "actor": "project_owner",  # 项目经理
        "content": ["核对数据", "标记异常"],
        "to_status": "trend_ok"
    },
    "step3": {
        "action": "确认数据",
        "actor": "project_owner",  # 项目经理统计实际消耗
        "content": ["统计实际消耗", "确认进粉"],
        "to_status": "final_confirmed"
    }
}
```

### 6.3 死号处理流程

```python
# ===== 死号清零流程 =====
DEAD_ACCOUNT_WORKFLOW = {
    "step1": {
        "action": "报告清零",
        "actor": "pitcher",
        "description": "账户被封禁，有余额未消耗"
    },
    "step2": {
        "action": "提交代理商",
        "actor": "account_manager",
        "description": "联系代理商申请清零"
    },
    "step3": {
        "action": "代理商清零",
        "actor": "external",  # 代理商操作
        "description": "代理商将余额清零出来"
    },
    "step4": {
        "action": "余额转移",
        "actor": "account_manager",
        "description": "将清零余额转移到其他账户"
    }
}
```

### 6.4 项目结算流程

```python
# ===== 项目结算流程 =====
PROJECT_SETTLEMENT_WORKFLOW = {
    "step1": {
        "action": "确认有效粉",
        "actor": "project_owner",
        "description": "跟甲方确认最终有效粉数"
    },
    "step2": {
        "action": "计算收入",
        "formula": "收入 = 有效粉 × 单价"
    },
    "step3": {
        "action": "收款",
        "actor": "finance",
        "description": "向甲方收款"
    }
}
```

---

## 7. 禁止行为清单

### 7.1 代码级禁止

| 编号 | 禁止行为 | 正确做法 |
|------|---------|---------|
| F-001 | 发明新状态 | 只使用 STATE_MACHINE.md 定义的状态 |
| F-002 | 发明新角色 | 只使用本文档 §1.2 的 6 角色 |
| F-003 | 发明新错误码 | 只使用 ERROR_CODES_SOT.md |
| F-004 | UPDATE ledger_entries | 只能 INSERT，修正用 REVERSAL |
| F-005 | DELETE ledger_entries | 禁止删除，修正用 REVERSAL |
| F-006 | 直接修改 balance | 通过 ledger_entries 计算 |
| F-007 | 绕过状态机改 status | 必须通过状态转换函数 |
| F-008 | Phase 1 生成阻断代码 | 只能记录 + 高亮 + 返回 |
| F-009 | 充值流程添加老板审批 | 充值只需财务审批 |
| F-010 | 使用不存在的角色 | 如 data_operator、supervisor |

### 7.2 业务级禁止

| 编号 | 禁止行为 | Phase 1 正确做法 |
|------|---------|-----------------|
| B-001 | 自动停投 | 标记异常 + 通知项目经理 |
| B-002 | 自动止损 | 标记异常 + 通知项目经理 |
| B-003 | 对账红灯阻断 | 标红 + 生成差异单 |
| B-004 | SLA 超时自动升级 | 记录超时 + 通知 |
| B-005 | 自动扣绩效 | Phase 2 再做 |
| B-006 | 强制审批流程 | 可绕行但记录 |

---

## 8. API 响应格式

```python
# 成功响应（Envelope 格式）
{
    "success": True,
    "data": { ... },
    "message": "操作成功",
    "timestamp": "2025-12-27T10:00:00Z"
}

# 业务错误响应
{
    "success": False,
    "error": {
        "code": "STATE_400",
        "message": "状态转换非法",
        "details": { ... }
    },
    "timestamp": "2025-12-27T10:00:00Z"
}
```

---

## 9. 验收检查清单（AI 自检）

### 9.1 代码生成前检查

```
□ 步骤 0：确认 Phase（默认 Phase 1）
□ 步骤 1：确认角色是否在 6 角色白名单内
□ 步骤 2：确认状态是否在状态机白名单内
□ 步骤 3：确认充值流程不含老板审批
□ 步骤 4：确认数据 SoT（行为记录 vs 实际数据 vs 结算数据）
□ 步骤 5：确认利润公式（收入 - 支出）
```

### 9.2 代码生成后检查

```
□ 是否使用了 SoT 未定义的状态？
□ 是否使用了 SoT 未定义的角色（如 data_operator）？
□ 是否直接 UPDATE/DELETE 了 ledger_entries？
□ 是否生成了"自动拒绝/暂停/终止"的代码？
□ 充值流程是否错误地添加了老板审批？
□ 错误码是否来自 ERROR_CODES_SOT.md？
□ API 响应是否使用 Envelope 格式？
□ 利润计算是否使用正确公式（收入-支出）？
```

---

## 10. 错误码速查

| 错误码 | HTTP | 含义 | 使用场景 |
|--------|------|------|---------|
| AUTH_401 | 401 | 未认证 | Token 缺失/过期 |
| AUTH_403 | 403 | 无权限 | 角色不允许此操作 |
| STATE_400 | 400 | 状态转换非法 | 不符合状态机定义 |
| STATE_402 | 400 | 终态非法回退 | 尝试修改已确认数据 |
| BIZ_001 | 400 | 无效的操作 | 违反业务规则 |
| BIZ_002 | 404 | 资源不存在 | 根据 ID 查询未找到 |
| BIZ_101 | 400 | 余额不足 | 转账/消耗超出余额 |
| VALIDATION_001 | 400 | 参数校验失败 | 必填字段缺失 |

---

## 附录 A：v2.2 变更日志

| 变更项 | v2.1 | v2.2 | 说明 |
|--------|------|------|------|
| 角色数量 | 7 个 | **6 个** | 移除 supervisor，项目经理承担数据统计 |
| 数据 SoT | 单层 | **三层** | 行为记录/实际数据/结算数据 |
| 消耗 SoT | ad_spend_daily.spend | **项目经理统计** | 基于实际业务 |
| 计费依据 | conversions | **有效粉** | 项目结束甲方确认 |
| 成本分类 | 未明确 | **3 类** | 充值/配套/后勤 |
| 手续费 | 可能单独 | **包含在充值中** | 简化模型 |
| 广告配套归属 | 可能分摊 | **公司统一** | 不分摊到项目 |
| 利润公式 | 复杂 | **收入-支出** | 简化 |
| 充值审批 | 未明确 | **不含老板** | 投手→户管→财务 |
| 押款定义 | 未定义 | **代理商未消耗余额** | 新增 |

---

## 附录 B：快速引用

```python
# ===== 复制此块到代码文件顶部 =====

# 角色白名单（6 个）
VALID_ROLES = frozenset([
    "ceo", "project_owner", "finance", 
    "pitcher", "account_manager", "admin"
])

# Phase 1 日报状态
PHASE1_REPORT_STATUS = frozenset([
    "raw_submitted", "trend_ok", "final_confirmed"
])

# 支出分类
EXPENSE_CATEGORY = frozenset([
    "ad_topup",    # 广告费充值（含手续费）
    "ad_support",  # 广告配套（公司统一）
    "overhead"     # 后勤支出（公司统一）
])

# 利润公式
def calc_profit(income, expense):
    """利润 = 总收入 - 总支出"""
    return income - expense

# 充值审批链（不含老板）
TOPUP_APPROVERS = ["account_manager", "finance"]

# 押款计算
def calc_deposit(total_topup, total_spend):
    """押款 = 历史充值 - 历史消耗"""
    return total_topup - total_spend
```

---

## 附录 C：业务术语对照

| 业务术语 | 系统字段/概念 | 说明 |
|---------|--------------|------|
| 甲方 | client | 客户，付款方 |
| 代理商/渠道 | supplier | 广告费充值对象 |
| 有效粉 | confirmed_leads | 甲方最终确认的进粉数 |
| 实际消耗 | actual_spend | 项目经理统计的平台消耗 |
| 押款 | supplier_deposit | 代理商未消耗余额 |
| 广告配套 | ad_support | BM/IP/主页/个号等 |
| 后勤支出 | overhead | 工资/房租/日常等 |
| 项目毛利 | gross_profit | 项目收款 - 项目广告费 |
| 公司利润 | net_profit | 总收入 - 总支出 |

---

**文档版本**: v2.2 (AI Programming Spec)
**基准文档**: MASTER.md v4.6, STATE_MACHINE.md v2.8, DATA_SCHEMA.md v5.6
**用途**: Claude/AI 编程参考
**最后更新**: 2025-12-27
**变更说明**: 基于确认的业务事实更新角色(6个)、数据SoT(三层)、成本结构(3类)、利润公式(收入-支出)
