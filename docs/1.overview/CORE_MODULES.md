# CORE_MODULES.md - 核心功能模块定义

> **文档性质**: 核心业务模块定义与规则摘要
> **版本**: v1.0
> **status**: draft
> **基准**: AI编程指导文档 V5.2, MASTER.md v4.4
> **owner**: wade
> **last_reviewed**: 2025-12-22

---

## 模块总览

本系统包含 **4 大核心模块**，从管理者视角划分：

| 模块 | 管理对象 | 核心问题 | 主要功能 |
|------|---------|---------|---------|
| **投手管理** | 投手团队 | 谁在投？投得怎么样？ | 日报填报、绩效看板、归属历史 |
| **财务管理** | 资金流水 | 钱从哪来？花到哪去？ | 账本流水、对账核销、期间关账 |
| **广告账号管理** | 广告账户 | 账户够用吗？状态正常吗？ | 账户状态、归属分配、余额监控 |
| **项目管理** | 甲方项目 | 客户赚钱吗？ | 单价配置、收入统计、利润分析 |

---

## 模块关系图

```
                    ┌─────────────┐
                    │  项目管理   │ ← 甲方付款
                    │ (客户/单价) │
                    └──────┬──────┘
                           │ 项目归属
                           ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  投手管理   │────→│ 广告账号管理 │←────│  财务管理   │
│ (团队/绩效) │     │ (账户/归属)  │     │ (账本/对账) │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       │     日报填报      │    消耗记账       │
       └──────────────────→├──────────────────→┘
                           ▼
                    ┌─────────────┐
                    │   日报流程   │
                    │  (8状态机)   │
                    └─────────────┘
```

---

# 模块一：投手管理

## 1.1 业务价值

**核心问题**: 谁在投？投得怎么样？绩效如何？

**服务对象**: 主管、运营、CEO

## 1.2 功能清单

| 功能 | 说明 | 操作角色 |
|------|------|---------|
| 投手信息管理 | 姓名、团队、状态、入职日期 | admin |
| 日报填报 | 每日消耗、进粉数据提交 | pitcher |
| 日报审核 | 趋势检查、数据确认 | supervisor |
| 绩效看板 | 消耗排名、ROAS、进粉成本 | supervisor, ceo |
| 归属历史 | 投手管理过哪些账户 | account_manager |

## 1.3 核心实体

### pitchers 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| name | VARCHAR(50) | 投手名称 |
| real_name | VARCHAR(50) | 真实姓名 |
| team | VARCHAR(30) | 团队 (郑州/金边/深圳/外包) |
| type | VARCHAR(20) | 类型 (internal/outsource) |
| status | VARCHAR(20) | 状态 (active/inactive) |
| join_date | DATE | 入职日期 |
| user_id | INT | 关联用户ID |

### daily_reports 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| report_date | DATE | 报告日期 |
| pitcher_id | INT | 投手ID |
| platform | VARCHAR(20) | 平台 (FB/TK/Google) |
| region | VARCHAR(50) | 地区 |
| project_id | INT | 项目ID |
| reported_spend | DECIMAL(14,2) | 申报消耗 |
| reported_results | INT | 申报进粉 |
| platform_spend | DECIMAL(14,2) | 平台消耗 |
| confirmed_spend | DECIMAL(14,2) | 确认消耗 |
| confirmed_leads | INT | 确认进粉 |
| status | VARCHAR(20) | 状态 |

## 1.4 日报状态机 (8状态)

```
标准流转:
null → raw_submitted → trend_pending → trend_ok → final_pending
     → final_confirmed → final_locked

异常流转:
trend_pending → trend_flagged → trend_resolved → final_pending
```

### 状态说明

| 状态 | 说明 | 可操作角色 |
|------|------|-----------|
| raw_submitted | 投手已提交原始数据 | pitcher |
| trend_pending | 等待趋势检查 | system |
| trend_ok | 趋势检查通过 | system |
| trend_flagged | 趋势异常标记 | system |
| trend_resolved | 异常已解决 | supervisor |
| final_pending | 等待最终确认 | system |
| final_confirmed | 已确认 | supervisor |
| final_locked | 已锁定（终态） | system |

## 1.5 业务规则

| 规则ID | 规则描述 |
|--------|---------|
| BR-RPT-001 | 每个投手每天每地区每平台只能提交一份日报 |
| BR-RPT-002 | raw 数据只能由投手本人修改 |
| BR-RPT-003 | final_locked 后数据不可修改，只能冲正 |
| BR-RPT-004 | 趋势检查异常需主管审核后才能继续 |

---

# 模块二：财务管理

## 2.1 业务价值

**核心问题**: 钱从哪来？花到哪去？账对不对？

**服务对象**: 财务、CEO

## 2.2 功能清单

| 功能 | 说明 | 操作角色 |
|------|------|---------|
| 账本流水 | 查看收入/成本双账本 | finance |
| 充值管理 | 甲方充值、代理充值录入 | finance |
| 对账核销 | 代理账单、平台账单对账 | finance |
| 冲正调整 | 错误账务修正 | finance |
| 期间关账 | 月结锁定 | finance, ceo |
| 财务报表 | 收支汇总、利润报表 | finance, ceo |

## 2.3 核心实体

### ledger 表 (核心)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| txn_id | VARCHAR(64) | 幂等键 (UNIQUE) |
| txn_type | VARCHAR(30) | 交易类型 |
| txn_status | VARCHAR(20) | 状态 (PENDING→CONFIRMED) |
| amount | DECIMAL(14,2) | 金额（公司视角） |
| currency | VARCHAR(10) | 币种 |
| amount_usd | DECIMAL(14,2) | 美元金额 |
| fx_rate | DECIMAL(12,6) | 汇率 |
| fx_status | VARCHAR(20) | 汇率状态 |
| agency_id | INT | 代理商ID |
| account_id | INT | 账户ID |
| project_id | INT | 项目ID |
| client_id | INT | 甲方ID |
| pitcher_id | INT | 投手ID |
| is_reversal | BOOLEAN | 是否冲正记录 |
| reversal_of | BIGINT | 冲正的原记录ID |
| business_date | DATE | 业务日期 |

### period_locks 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| entity_type | VARCHAR(30) | 实体类型 (ledger/daily_report) |
| period_start | DATE | 期间开始 |
| period_end | DATE | 期间结束 |
| lock_status | VARCHAR(20) | UNLOCKED/LOCKED/FROZEN |
| locked_by | INT | 锁定人 |
| locked_at | TIMESTAMP | 锁定时间 |

## 2.4 金额符号规则

```python
# ⚠️ 核心规则：Ledger.amount 以"公司视角"记录
# 公司收钱 = 正数（+）
# 公司付钱 = 负数（-）

AMOUNT_SIGN_RULES = {
    # 资金流入（公司收钱）→ 正数
    'CLIENT_PAYMENT': 'POSITIVE',      # 甲方打款 +10000
    'AGENCY_REFUND': 'POSITIVE',       # 代理退款 +500
    'ACCOUNT_REFUND': 'POSITIVE',      # 账户退款 +200
    'ADJUSTMENT_IN': 'POSITIVE',       # 调增 +100

    # 资金流出（公司付钱）→ 负数
    'AGENCY_TRANSFER': 'NEGATIVE',     # 转款给代理 -5000
    'AGENCY_FEE': 'NEGATIVE',          # 手续费 -400
    'PLATFORM_SPEND': 'NEGATIVE',      # 平台消耗 -3000
    'BANK_FEE': 'NEGATIVE',            # 银行费 -10
    'WRITE_OFF': 'NEGATIVE',           # 坏账核销 -1000
    'ADJUSTMENT_OUT': 'NEGATIVE',      # 调减 -100

    # 冲正 → 与原记录相反
    'REVERSAL': 'OPPOSITE',
}
```

## 2.5 Append-Only 规则

```python
# ⚠️ Ledger 表只能 INSERT，不能 UPDATE/DELETE

# 错误纠正方式：冲正 + 更正
# 原记录 #100: PLATFORM_SPEND, amount=-1000 (错误)
# 冲正 #101: REVERSAL, amount=+1000, reversal_of=100
# 更正 #102: PLATFORM_SPEND, amount=-800 (正确)

# 冲正规则：
# 1. 一条原记录只能被冲正一次
# 2. 禁止对冲正记录再冲正（链式冲正）
# 3. 后续调整用 ADJUSTMENT_IN/OUT
```

## 2.6 账本状态迁移

```
PENDING → APPROVED (finance/supervisor)
APPROVED → EXECUTED (finance)
EXECUTED → CONFIRMED (finance, 前提: fx_status=LOCKED)
CONFIRMED → 终态，不可变更
```

## 2.7 期间锁规则

```python
def is_period_locked(entity_type: str, date: date) -> bool:
    """检查期间是否已锁定"""
    return db.query(PeriodLock).filter(
        PeriodLock.entity_type == entity_type,
        PeriodLock.lock_status.in_(['LOCKED', 'FROZEN']),
        PeriodLock.period_start <= date,
        PeriodLock.period_end >= date
    ).exists()

# 锁定期间后禁止：
# - CONFIRMED 该期间的流水
# - 冲正该期间的流水（除非特批）
# - 修改该期间的归因
```

### 特批冲正条件

| 条件 | 要求 |
|------|------|
| 角色 | ceo 或 finance (特批权限) |
| force_override | True |
| 原因 | 至少10个字符 |

## 2.8 对账功能

### 对账类型

| 类型 | 我方数据 | 对方数据 |
|------|---------|---------|
| AGENCY | ledger (agency_id) | 代理商账单 |
| PLATFORM | platform_imports | 平台消耗报表 |
| CLIENT | ledger (client_id) | 甲方付款记录 |
| BANK | ledger | 银行流水 |

### 对账状态

```
DRAFT → IMPORTING → MATCHING → REVIEWING → RESOLVED → CLOSED
```

### 差异处理

| 差异类型 | 说明 | 处理方式 |
|---------|------|---------|
| OUR_ONLY | 我方有，对方无 | 核实后排除或调整 |
| THEIR_ONLY | 对方有，我方无 | 补录或排除 |
| AMOUNT_MISMATCH | 金额不匹配 | 调整或说明 |

## 2.9 业务规则

| 规则ID | 规则描述 |
|--------|---------|
| BR-LED-001 | 账本只能追加，不能修改删除 |
| BR-LED-002 | 金额符号必须符合交易类型规则 |
| BR-LED-003 | CONFIRMED 状态需要汇率已锁定 |
| BR-LED-004 | 锁定期间的流水需特批才能冲正 |
| BR-LED-005 | 冲正记录不可再冲正 |

---

# 模块三：广告账号管理

## 3.1 业务价值

**核心问题**: 账户够用吗？状态正常吗？谁在用？

**服务对象**: 户管、主管

## 3.2 功能清单

| 功能 | 说明 | 操作角色 |
|------|------|---------|
| 账户信息管理 | 平台账户ID、名称、类型 | account_manager |
| 代理商管理 | 代理商信息、手续费率 | admin |
| 账户状态监控 | 正常/受限/死号 | account_manager |
| 归属分配 | 分配账户给投手 | account_manager |
| 余额监控 | 账户余额、消耗速度 | account_manager |
| 死号迁移 | 业务转移到新账户 | account_manager |

## 3.3 核心实体

### ad_accounts 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| account_id | VARCHAR(50) | 平台账户ID (UNIQUE) |
| account_name | VARCHAR(100) | 账户名称 |
| account_type | VARCHAR(50) | 类型 (二不限/美金户/绑卡户) |
| agency_id | INT | 代理商ID |
| platform | VARCHAR(20) | 平台 (FB/TK/Google) |
| fee_rate | DECIMAL(5,4) | 手续费率 |
| status | VARCHAR(20) | 状态 |
| current_pitcher_id | INT | 当前投手 |

### agencies 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| name | VARCHAR(100) | 代理商名称 |
| short_name | VARCHAR(50) | 简称 |
| fee_rate | DECIMAL(5,4) | 默认手续费率 (8%) |
| status | VARCHAR(20) | 状态 |
| contact_info | JSONB | 联系方式 |
| bank_info | JSONB | 收款信息 |

### account_ownership_history 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| account_id | INT | 账户ID |
| pitcher_id | INT | 投手ID |
| project_id | INT | 项目ID |
| region | VARCHAR(50) | 地区 |
| effective_from | DATE | 生效开始 |
| effective_to | DATE | 生效结束 |
| change_type | VARCHAR(20) | ASSIGN/TRANSFER/RECALL |

## 3.4 账户状态

```
active (正常) → idle (闲置) → suspended (受限) → banned (死号)

注意：死号是终态，不可恢复
```

### 状态说明

| 状态 | 说明 | 可操作 |
|------|------|-------|
| active | 正常使用中 | 可投放 |
| idle | 暂时闲置 | 可重新激活 |
| suspended | 平台限制 | 等待解封或转死号 |
| banned | 永久封禁 | 只能迁移，不可恢复 |

## 3.5 归因规则

```python
# 消耗归因遵循「投放行为决定归属」原则

def get_attribution(account_id: int, spend_date: date):
    """获取消耗归因"""
    ownership = db.query(AccountOwnershipHistory).filter(
        AccountOwnershipHistory.account_id == account_id,
        AccountOwnershipHistory.effective_from <= spend_date,
        (AccountOwnershipHistory.effective_to >= spend_date) |
        (AccountOwnershipHistory.effective_to.is_(None))
    ).first()

    return {
        'pitcher_id': ownership.pitcher_id,
        'project_id': ownership.project_id,
        'region': ownership.region
    }

# 归因规则：
# 1. 按账户归属历史确定投手
# 2. 按投手确定项目
# 3. 归因不因事后协商改变
```

## 3.6 业务规则

| 规则ID | 规则描述 |
|--------|---------|
| BR-ACC-001 | 同一账户同一时间只能归属一个投手 |
| BR-ACC-002 | 死号不可恢复，只能迁移业务 |
| BR-ACC-003 | 账户归属变更需记录历史 |
| BR-ACC-004 | 消耗归因按投放时的归属确定 |

---

# 模块四：项目管理

## 4.1 业务价值

**核心问题**: 客户赚钱吗？利润多少？

**服务对象**: 主管、财务、CEO

## 4.2 功能清单

| 功能 | 说明 | 操作角色 |
|------|------|---------|
| 甲方管理 | 甲方信息、联系方式 | admin |
| 项目信息管理 | 项目名、地区、平台 | supervisor |
| 单价配置 | 基础单价、阶梯价格 | supervisor |
| 收入统计 | 进粉数 × 单价 | finance |
| 成本统计 | 消耗 + 手续费 | finance |
| 利润分析 | 收入 - 成本 | ceo |

## 4.3 核心实体

### clients 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| name | VARCHAR(100) | 甲方名称 |
| short_name | VARCHAR(50) | 简称 |
| contact_info | JSONB | 联系方式 |
| payment_terms | VARCHAR(200) | 付款条款 |
| status | VARCHAR(20) | 状态 |

### projects 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| name | VARCHAR(100) | 项目名称 |
| client_id | INT | 甲方ID |
| region | VARCHAR(50) | 地区 |
| platform | VARCHAR(20) | 平台 |
| base_price | DECIMAL(10,2) | 基础单价 |
| price_rules | JSONB | 阶梯价格规则 |
| status | VARCHAR(20) | 状态 |
| start_date | DATE | 开始日期 |
| end_date | DATE | 结束日期 |

## 4.4 计费公式

```python
# 收入计算
revenue = conversions_final × unit_price

# 成本计算
cost = real_spend × (1 + fee_rate)

# 利润计算
profit = revenue - cost
profit_rate = profit / revenue × 100%
```

## 4.5 阶梯价格规则

```python
# price_rules JSON 结构示例
{
    "type": "tiered",
    "tiers": [
        {"min": 0, "max": 1000, "price": 50},
        {"min": 1001, "max": 5000, "price": 45},
        {"min": 5001, "max": null, "price": 40}
    ]
}

def calculate_revenue(conversions: int, price_rules: dict) -> Decimal:
    """计算阶梯价格收入"""
    if price_rules.get('type') != 'tiered':
        return conversions * price_rules.get('base_price', 0)

    total = 0
    remaining = conversions
    for tier in price_rules['tiers']:
        tier_max = tier['max'] or float('inf')
        tier_count = min(remaining, tier_max - tier['min'])
        if tier_count > 0:
            total += tier_count * tier['price']
            remaining -= tier_count
        if remaining <= 0:
            break
    return total
```

## 4.6 项目状态

| 状态 | 说明 |
|------|------|
| active | 进行中 |
| paused | 暂停 |
| completed | 已完成 |
| cancelled | 已取消 |

## 4.7 业务规则

| 规则ID | 规则描述 |
|--------|---------|
| BR-PRJ-001 | 终态后项目单价不可修改 |
| BR-PRJ-002 | 阶梯价格按进粉数累计计算 |
| BR-PRJ-003 | 项目收入 = SUM(日报收入) |
| BR-PRJ-004 | 项目成本 = SUM(日报成本) |

---

# 附录

## A. 角色权限矩阵

| 角色 | 投手管理 | 财务管理 | 账号管理 | 项目管理 |
|------|---------|---------|---------|---------|
| pitcher | 填报日报 | - | - | - |
| account_manager | 查看绩效 | - | 全部功能 | - |
| supervisor | 审核日报、绩效看板 | - | 查看 | 单价配置 |
| project_owner | 查看绩效 | 申请充值 | 查看 | 全部功能 |
| finance | - | 全部功能 | 查看 | 查看 |
| ceo | 绩效看板 | 关账审批、报表 | 查看 | 利润分析 |
| admin | 投手信息 | - | 代理商管理 | 甲方管理 |

## B. 幂等性规则

```python
# txn_id 生成规则（不含时间戳，保证幂等）
def generate_txn_id(source_type, source_ref, date, amount, currency, entity_id=''):
    data = f"{source_type}|{source_ref}|{date}|{amount}|{currency}|{entity_id}"
    return hashlib.sha256(data.encode()).hexdigest()

# 冲正 txn_id
def generate_reversal_txn_id(original_id):
    return f"REV_{original_id}_v1"

# 日报幂等键
# UNIQUE (report_date, pitcher_id, region, platform)
```

## C. SoT 引用索引

| 模块 | 主要 SoT 文档 |
|------|-------------|
| 投手管理 | DAILY_REPORT_SOT.md, STATE_MACHINE.md §8 |
| 财务管理 | LEDGER_SOT.md, RECONCILIATION_SOT.md |
| 账号管理 | DATA_SCHEMA.md, BUSINESS_RULES.md |
| 项目管理 | DATA_SCHEMA.md, BUSINESS_RULES.md |

---

## 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2025-12-22 | 初始版本，4大核心模块定义 | Claude Code |

---

**文档版本**: v1.0
**创建日期**: 2025-12-22
**基准文档**: AI编程指导文档 V5.2, MASTER.md v4.4
**维护者**: 系统架构师
