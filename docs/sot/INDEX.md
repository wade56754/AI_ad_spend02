# SoT 索引（模块 → 规格映射）

> 本文件是AI编码的"查阅入口"。开发任何模块前，必须先查对应的SoT章节。

---

## 快速查阅

| 我要做什么 | 查哪里 |
|-----------|-------|
| 新增API端点 | [API开发](#api开发) |
| 修改数据库表 | [数据模型](#数据模型) |
| 处理状态流转 | [状态机](#状态机) |
| 涉及金额计算 | [财务规则](#财务规则) |
| 权限相关 | [权限控制](#权限控制) |
| 红冲/调整 | [红冲规则](#红冲规则) |

---

## 模块索引

### 投手模块 `backend/routers/daily_reports.py`

| 功能 | SoT章节 | 关键不变量 |
|------|---------|-----------|
| 日报填报 | MASTER.md §B.4 DailyReport | 投手只能操作自己账户 (R-PERM-002) |
| 日报审核 | MASTER.md §B.3 SM-1 | 6状态流转：draft→submitted→approved→confirmed→locked |
| 日报时限 | MASTER.md §A.3 | T日24:00(BJS)前提交 |

**必查状态机**: SM-1 日报状态机（6状态）

---

### 账户模块 `backend/routers/accounts.py`

| 功能 | SoT章节 | 关键不变量 |
|------|---------|-----------|
| 账户管理 | MASTER.md §B.4 AdAccount | opening_balance系统启用时一次性录入 |
| 余额快照 | MASTER.md §B.4 BalanceSnapshot | 户管T+1日09:00(BJS)前录入 |
| 可用资金 | MASTER.md §B.2 R-COST-003 | available_funds = opening_balance + Σtopup - Σad_spend |

**必查公式**: R-COST-003 可用资金计算

---

### 项目模块 `backend/routers/projects.py`

| 功能 | SoT章节 | 关键不变量 |
|------|---------|-----------|
| 项目管理 | MASTER.md §B.4 entities | 项目负责人只能看自己项目 (R-PERM-001) |
| 单价配置 | MASTER.md §B.2 R-PRICE-* | 阶梯定价采用左闭右开规则 |
| 进粉确认 | MASTER.md §B.4 LeadConfirmation | 项目负责人T+1确认，以甲方确认为准 |
| 预收款 | MASTER.md §A.2 预收款 | 甲方打款≠收入，履约完成前是负债 |

**必查规则**: R-PRICE-002 阶梯定价示例

---

### 财务模块 `backend/routers/finance.py`

| 功能 | SoT章节 | 关键不变量 |
|------|---------|-----------|
| 消耗确认 | MASTER.md §B.4 PlatformSpend | 户管T+1确认，广告费与手续费同步 |
| 账本流水 | MASTER.md §B.4 LedgerEntry | 不可UPDATE/DELETE，只能追加 |
| 红冲调整 | MASTER.md §B.2 R-REV-* | 必须ref_id + reason |
| 月结锁定 | MASTER.md §B.3 SM-3 | 财务复核→老板确认→locked |

**必查规则**: R-REV-001~004 红冲规则

---

### 对账模块 `backend/routers/reconciliation.py`

| 功能 | SoT章节 | 关键不变量 |
|------|---------|-----------|
| 客户预收对账 | MASTER.md §B.2 R-RECON-001 | prepaid_balance = client_payment - fulfilled_revenue |
| 供应链对账 | MASTER.md §B.2 R-RECON-002 | opening_balance + Σtopup - Σad_spend = current_balance |
| 差异单 | MASTER.md §B.3 SM-2 | 4状态：created→pending→resolved→closed |
| 对账阈值 | MASTER.md §A.4 | 客户≤100绿/≤1000黄/>1000红；供应链≤1绿/≤100黄/>100红 |

**必查状态机**: SM-2 差异单状态机

---

## 状态机

| 状态机 | 位置 | 状态数 | 终态 |
|--------|------|--------|------|
| SM-1 日报 | MASTER.md §B.3 | 6 | locked, voided |
| SM-2 差异单 | MASTER.md §B.3 | 4 | closed |
| SM-3 月结 | MASTER.md §B.3 | 2 | locked |

---

## 财务规则

| 规则ID | 名称 | 公式/说明 |
|--------|------|----------|
| R-COST-001 | 平台消耗 | platform_spend = ad_spend（不含手续费） |
| R-COST-002 | 总成本 | total_cost = ad_spend + service_fee |
| R-COST-003 | 可用资金 | available_funds = opening_balance + Σtopup - Σad_spend |
| R-RECON-001 | 客户预收对账 | prepaid_balance = client_payment - fulfilled_revenue |
| R-RECON-002 | 供应链对账 | opening_balance + Σtopup - Σad_spend = current_balance |

---

## 红冲规则

| 规则ID | 说明 | 适用实体 |
|--------|------|---------|
| R-REV-001 | 红冲适用范围 | 账本流水、进粉确认、平台消耗 |
| R-REV-002 | 不可删改 | 原记录不可UPDATE/DELETE |
| R-REV-003 | 必须引用 | 红冲记录必须有ref_id |
| R-REV-004 | 必须说明 | 红冲记录必须有reason |

---

## 权限控制

| 规则ID | 角色 | 数据域 |
|--------|------|-------|
| R-PERM-001 | 项目负责人 | 只能看自己负责的项目 |
| R-PERM-002 | 投手 | 只能看自己负责的账户 |
| R-PERM-003 | 主管 | 可跨团队查看 |
| R-PERM-004 | 老板 | 全局可见 |

---

## 数据模型

| 实体 | 位置 | 核心字段 | 关联规则 |
|------|------|---------|---------|
| DailyReport | §B.4 | status(6状态) | SM-1, R-PERM-002 |
| PlatformSpend | §B.4 | ad_spend, service_fee | R-COST-001, R-REV-* |
| LeadConfirmation | §B.4 | confirmed_leads, is_locked | R-REV-* |
| LedgerEntry | §B.4 | amount, ref_id, reason | R-REV-* |
| BalanceSnapshot | §B.4 | platform_balance | R-COST-003 |
| AdAccount | §B.4 | opening_balance | R-COST-003, R-RECON-002 |
| ReconciliationIssue | §B.4 | severity, status | SM-2, R-RECON-* |

---

## API开发

新增API前必查：
1. 权限：该角色能否访问该数据？→ R-PERM-*
2. 状态：操作是否符合状态机？→ SM-*
3. 金额：计算公式是否正确？→ R-COST-*, R-PRICE-*
4. 锁定：是否检查了is_locked？→ SM-3
5. 红冲：是否需要红冲机制？→ R-REV-*

---

## AI编码检查清单

开发完成后，检查以下不变量：

```markdown
[ ] 权限：投手只能操作自己账户
[ ] 权限：项目负责人只能操作自己项目
[ ] 状态机：状态流转符合SM-1/SM-2/SM-3
[ ] 金额：可用资金公式正确（含opening_balance）
[ ] 金额：平台消耗不含手续费
[ ] 锁定：locked状态数据不可修改
[ ] 红冲：有ref_id和reason
[ ] 时区：所有时间使用北京时间
[ ] Phase 1：只提示不阻断
```
