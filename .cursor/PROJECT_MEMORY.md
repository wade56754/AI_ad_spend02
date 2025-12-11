# AI 广告代投系统 - 项目记忆文档 (Claude Context Transfer)

> **导出日期**: 2025-12-11
> **项目版本**: ASDD Freeze v1.0 + SoT Freeze v2.6
> **文档用途**: AI Agent 上下文恢复、跨会话知识传承
> **使用方法**: 新会话开始时，将此文档内容发送给 Claude，确保完整理解项目上下文

---

## 🚨 CRITICAL: 开始开发前必读

### 强制规则 (违反将导致代码回滚)

1. **禁止重复定义状态枚举** - 所有状态必须引用 `STATE_MACHINE.md v2.6`
2. **禁止自定义错误码** - 必须来自 `ERROR_CODES_SOT.md v2.1`
3. **禁止直接修改 balance** - 必须通过 `ledger_entries` 表记录
4. **禁止跳过状态流转** - 必须按状态机定义的顺序流转
5. **禁止前端绕过 BFF** - 必须使用 `apiFetch` 调用 FastAPI
6. **禁止直接修改 models/** - 必须先更新 DATA_SCHEMA.md → 生成 Alembic 迁移

### SoT 裁判链 (技术决策优先级)

```
STATE_MACHINE.md v2.6  →  DATA_SCHEMA.md v5.2  →  BUSINESS_RULES.md v3.2
→  API_SOT.md v9.0  →  ERROR_CODES_SOT.md v2.1  →  AUTH_SPEC.md v2.0
→  LEDGER_SOT.md v1.1  →  PROFIT_SOT.md v1.1  →  RECONCILIATION_SOT.md v1.0
```

**开发前必做**:
1. 查询对应 SoT 文档
2. 找到相关业务规则编号 (BR-*)
3. 检查现有代码是否符合规则

---

## 一、项目概述

### 1.1 系统定位
**AI 广告代投系统** - 面向广告代理商的全链路运营管理平台

**核心业务流程**:
```
媒体投放 → 日报提交 → 风控审核 → 计费入账 → 对账结算 → 利润分析
```

### 1.2 技术栈 (不可变更)

| 层级 | 技术 | 备注 |
|------|------|------|
| **后端** | FastAPI + SQLAlchemy (同步) | 禁止异步 ORM |
| **数据库** | PostgreSQL 15 (Supabase) | 禁止手动 DDL |
| **认证** | Supabase Auth | 禁止自建 JWT/bcrypt |
| **前端** | Next.js 16.0.2 (App Router) | TypeScript 严格模式 |
| **UI** | shadcn/ui + Tailwind CSS | 禁止其他 UI 库 |
| **状态** | TanStack Query | 禁止 Redux/Zustand |

---

## 二、核心状态机

### 2.1 日报 8 状态机 (最重要!)

```
                                    ┌─────────────────┐
                                    │ raw_submitted   │ ← 投手提交
                                    └────────┬────────┘
                                             ↓ 自动触发趋势检测
                                    ┌─────────────────┐
                                    │ trend_pending   │
                                    └────────┬────────┘
                          ┌──────────────────┼──────────────────┐
                          ↓                  ↓                  ↓
                 ┌────────────────┐ ┌────────────────┐
                 │   trend_ok     │ │ trend_flagged  │ ← TF-001/002/003
                 └────────┬───────┘ └────────┬───────┘
                          │                  ↓ 运营审核
                          │         ┌────────────────┐
                          │         │ trend_resolved │
                          │         └────────┬───────┘
                          └──────────────────┼──────────────────┘
                                             ↓
                                    ┌─────────────────┐
                                    │ final_pending   │ ← 等待录入 real_spend
                                    └────────┬────────┘
                                             ↓ 运营确认
                                    ┌─────────────────┐
                                    │ final_confirmed │ ← 确认 conversions_final
                                    └────────┬────────┘
                                             ↓ 财务锁定
                                    ┌─────────────────┐
                                    │ final_locked    │ ← 触发账本: REVENUE + COST
                                    └─────────────────┘
```

**状态枚举值** (禁止在代码中重新定义):
```python
DAILY_REPORT_STATES = [
    "raw_submitted", "trend_pending", "trend_ok", "trend_flagged",
    "trend_resolved", "final_pending", "final_confirmed", "final_locked"
]
```

### 2.2 风控规则 (TF Rules)

| 规则 | 名称 | 触发条件 | 处理 |
|------|------|---------|------|
| TF-001 | 粉数骤降 | 当日粉数较前7日均值下降 >50% | → trend_flagged |
| TF-002 | 粉数骤增 | 当日粉数较前7日均值增长 >100% | → trend_flagged |
| TF-003 | 消耗异常 | raw_spend 与 real_spend 差异 >20% | → trend_flagged |

### 2.3 其他状态机

**充值状态**: `draft → pending_review → finance_approve → paid → completed` (可 `cancelled`/`rejected`)

**账户状态**: `new → testing → active → suspended → dead → archived`

**项目状态**: `draft → active → suspended → archived`

---

## 三、五角色权限体系

| 角色 | 代码值 | 职责 | 关键权限 |
|------|--------|------|----------|
| 系统管理员 | `admin` | 全局管理 | 全部权限 |
| 财务 | `finance` | 资金管理 | 充值终审、对账、利润报表 |
| 数据运营 | `data_operator` | 数据审核 | 日报审核、趋势处理 |
| 账户管理员 | `account_manager` | 客户管理 | 项目管理、账户分配 |
| 广告投手 | `media_buyer` | 投放执行 | 日报提交、充值申请 |

**禁止使用旧角色名**: `data_clerk`, `manager`, `trader` (历史遗留)

---

## 四、账本体系 (双账本)

### 4.1 入账类型

| entry_type | 符号 | 触发场景 | 公式 |
|------------|------|---------|------|
| `TOPUP` | + | 充值 completed | amount |
| `REVENUE` | + | 日报 final_locked | conversions_final × unit_price |
| `COST` | - | 日报 final_locked | -(real_spend + fee) |
| `TRANSFER_IN` | + | 调拨入账 | amount |
| `TRANSFER_OUT` | - | 调拨出账 | -amount |
| `ADJUSTMENT` | ± | 对账调整 | ±amount |

### 4.2 核心公式

```python
# 日报锁定时创建双账本分录
REVENUE = conversions_final × unit_price   # 正数
COST = -(real_spend + fee)                 # 负数

# 账户余额 = 所有分录金额之和
balance = SUM(ledger_entries.amount) WHERE ad_account_id = ?

# 利润计算
gross_profit = total_revenue - total_cost
gross_margin_pct = (gross_profit / total_revenue) × 100%
```

### 4.3 对账差异计算

```python
difference = our_total_spend - supplier_total_spend
difference_rate = (difference / supplier_total_spend) × 100%

# 调整建议
if difference > 10:    → "decrease" (我方多记，红冲)
if difference < -10:   → "increase" (我方少记，补录)
if |diff| <= 10:       → "writeoff" (核销)
```

---

## 五、后端架构

### 5.1 目录结构

```
backend/
├── routers/              # API 路由层 (Thin Layer)
│   ├── daily_reports.py  # /api/v1/daily-reports
│   ├── topup.py          # /api/v1/topups
│   ├── transfers.py      # /api/v1/transfers
│   ├── ledger.py         # /api/v1/ledger
│   ├── reconciliation.py # /api/v1/reconciliation
│   └── finance_profit.py # /api/v1/finance/profit
│
├── services/             # 业务逻辑层 (Fat Layer)
│   ├── daily_report_service.py      # 日报 CRUD + 状态流转
│   ├── trend_risk_control_service.py # 趋势风控 (TF-001/002/003)
│   ├── ledger_service.py            # 双账本操作
│   ├── topup_service.py             # 充值流程
│   ├── transfer_service.py          # 余额调拨
│   ├── reconciliation_service.py    # 对账差异计算
│   └── finance/profit_service.py    # 利润聚合
│
├── models/               # 数据模型 (禁止直接修改!)
├── core/                 # 核心模块
│   ├── error_codes.py    # 错误码枚举
│   └── permissions.py    # 权限定义
└── migrations/           # Alembic 迁移
```

### 5.2 关键 Service 方法

| Service | 方法 | 用途 |
|---------|------|------|
| `daily_report_service` | `transition_status()` | 状态流转 (带验证) |
| `trend_risk_control_service` | `check_trend_risk()` | TF 规则检测 |
| `ledger_service` | `create_billing_entries()` | 双账本入账 |
| `reconciliation_service` | `run_reconciliation()` | 执行对账 |
| `reconciliation_service` | `calculate_difference()` | 差异计算 |
| `profit_service` | `aggregate_profit()` | 利润聚合 |

---

## 六、前端架构 (Feature-Based)

### 6.1 目录结构

```
frontend/src/
├── features/                 # 功能模块 (每个模块独立)
│   ├── daily-reports/        # 日报管理
│   ├── topups/               # 充值管理
│   ├── transfers/            # 调拨管理
│   ├── ledger/               # 账本查询
│   ├── reconciliation/       # 对账管理
│   ├── finance-profit/       # 利润报表
│   ├── ad-accounts/          # 广告账户
│   ├── projects/             # 项目管理
│   ├── dashboard/            # 运营驾驶舱
│   └── ...
│
├── components/ui/            # shadcn/ui 组件
├── lib/api.ts                # apiFetch 封装 (必须使用)
└── hooks/                    # 全局 Hooks
```

### 6.2 Feature 模块结构

```
feature/
├── components/       # UI 组件
│   └── XxxPage.tsx   # 页面组件
├── hooks/            # React Hooks
│   └── useXxx.ts     # TanStack Query hooks
├── services/         # API 调用
│   └── xxxApi.ts     # apiFetch 封装
├── types/            # TypeScript 类型
│   └── xxx.types.ts  # 接口定义
└── index.ts          # 模块导出
```

---

## 七、数据库核心表

### 7.1 主键规则

| 主键类型 | 适用表 |
|---------|-------|
| UUID | `users`, `channels` (跨系统实体) |
| BIGSERIAL | `projects`, `ad_accounts`, `daily_reports`, `topup_requests`, `ledger_entries` |

### 7.2 核心表字段

```sql
-- daily_reports (日报)
id, ad_account_id, report_date, status,
conversions_raw, conversions_final,  -- 粉数 (原始/最终)
raw_spend, real_spend,               -- 消耗 (原始/真实)
reviewed_by, reviewed_at, notes

-- ledger_entries (账本分录)
id, ad_account_id, entry_type, amount, entry_date,
related_entity_type, related_entity_id  -- 关联实体 (可追溯)

-- profit_aggregates (利润聚合)
id, period_type, period_start, period_end,
project_id, ad_account_id,
total_revenue, total_cost, gross_profit, gross_margin_pct,
is_locked, locked_by, locked_at
```

---

## 八、错误码体系

### 8.1 分类

| 前缀 | 类别 | HTTP | 示例 |
|------|------|------|------|
| `SYS_` | 系统错误 | 500 | SYS_001 数据库连接失败 |
| `AUTH_` | 认证授权 | 401/403 | AUTH_001 未登录 |
| `VAL_` | 验证错误 | 400 | VAL_001 参数缺失 |
| `BIZ_` | 业务逻辑 | 400/422 | BIZ_003 状态转换非法 |
| `RES_` | 资源错误 | 404/409 | RES_001 资源不存在 |

### 8.2 Transfer 错误码 (最新实现)

| 码 | 名称 | 说明 |
|----|------|------|
| BIZ_610 | TRANSFER_DUPLICATE_REQUEST | 重复调拨请求 |
| BIZ_611 | TRANSFER_SAME_ACCOUNT | 源=目标账户 |
| BIZ_612 | TRANSFER_SOURCE_NOT_DEAD | 源账户非死户 |
| BIZ_613 | TRANSFER_TARGET_NOT_ACTIVE | 目标账户非活跃 |
| BIZ_614 | TRANSFER_CROSS_SUPPLIER | 跨供应商调拨 |
| BIZ_615 | TRANSFER_ALREADY_PROCESSED | 已处理 |
| BIZ_616 | TRANSFER_INSUFFICIENT_BALANCE | 余额不足 |
| BIZ_617 | TRANSFER_INVALID_AMOUNT | 无效金额 |
| BIZ_618 | TRANSFER_LEDGER_ERROR | 账本错误 |
| BIZ_619 | TRANSFER_STATE_ERROR | 状态错误 |

---

## 九、已完成功能 (P0-P2)

### 9.1 P0 核心功能 ✅
- [x] 日报 8 状态机流转
- [x] 趋势风控 (TF-001/002/003)
- [x] 双账本计费 (REVENUE/COST)
- [x] 错误码规范化

### 9.2 P1 重要功能 ✅
- [x] 日报风控自动化触发
- [x] final_locked → Ledger 入账
- [x] 对账差异计算 + 调整建议
- [x] 利润聚合 (daily/weekly/monthly)
- [x] Transfer 供应商一致性检查

### 9.3 P2 常规功能 ✅
- [x] 数据导入导出 (CSV/Excel/PDF)
- [x] 批量操作 (8种类型)
- [x] 搜索筛选增强
- [x] Loading/Error 状态管理
- [x] 表单验证

---

## 十、关键文件路径速查

### 10.1 SoT 文档 (真相来源)
```
docs/2.sot/STATE_MACHINE.md      # 状态机
docs/2.sot/DATA_SCHEMA.md        # 数据结构
docs/2.sot/BUSINESS_RULES.md     # 业务规则
docs/2.sot/API_SOT.md            # API 契约
docs/2.sot/ERROR_CODES_SOT.md    # 错误码
docs/2.sot/LEDGER_SOT.md         # 账本规则
docs/2.sot/PROFIT_SOT.md         # 利润规则
docs/2.sot/RECONCILIATION_SOT.md # 对账规则
```

### 10.2 后端关键文件
```
backend/services/daily_report_service.py       # 日报业务
backend/services/trend_risk_control_service.py # 风控
backend/services/ledger_service.py             # 账本
backend/services/reconciliation_service.py     # 对账
backend/services/finance/profit_service.py     # 利润
backend/core/error_codes.py                    # 错误码
```

### 10.3 前端关键文件
```
frontend/src/lib/api.ts                        # apiFetch
frontend/src/features/*/hooks/useXxx.ts        # TanStack Query
frontend/src/features/*/services/xxxApi.ts     # API 调用
```

---

## 十一、可用 MCP 工具

| MCP | 工具 | 用途 |
|-----|------|------|
| **21st Magic** | `component_builder` | 构建新 UI 组件 |
| | `component_refiner` | 改进现有组件 |
| **Context7** | `get-library-docs` | 获取库最新文档 |
| **Supabase** | `execute_sql` | 执行 SQL 查询 |
| | `apply_migration` | 应用迁移 |
| **Sequential Thinking** | `sequentialthinking` | 复杂问题推理 |

---

## 十二、代码模式速查

### 12.1 后端 - Service 层
```python
# 状态流转 (必须通过 Service)
from backend.services.daily_report_service import DailyReportService
service = DailyReportService(db)
service.transition_status(report_id, new_status, user_id)

# 账本入账 (禁止直接改 balance)
from backend.services.ledger_service import LedgerService
ledger = LedgerService(db)
ledger.create_entry(
    ad_account_id=123,
    entry_type="REVENUE",
    amount=Decimal("1000.00"),
    related_entity_type="daily_report",
    related_entity_id=456
)
```

### 12.2 后端 - 错误抛出
```python
from backend.core.exceptions import BusinessLogicError
from backend.core.error_codes import ErrorCodes

# 正确方式
raise BusinessLogicError(
    message="状态转换非法",
    error_code=ErrorCodes.BIZ_003.code
)

# 错误方式 (禁止!)
raise HTTPException(400, "状态错误")
```

### 12.3 前端 - API 调用
```typescript
// 正确方式 - 使用 apiFetch
import { apiFetch } from '@/lib/api'
const data = await apiFetch('/api/v1/daily-reports')

// 错误方式 (禁止!)
const data = await fetch('/api/...')
const { data } = await supabase.from('...').select('*')
```

---

## 十三、常见反模式 (立即拦截)

```python
# ❌ 反模式 1: 硬编码旧状态
class DailyReportStatus(Enum):
    DRAFT = "draft"
    APPROVED = "approved"  # 错! 应该是 8 状态机

# ❌ 反模式 2: 直接修改余额
ad_account.balance -= 100
db.commit()  # 错! 必须通过 ledger_entries

# ❌ 反模式 3: 自定义错误码
raise HTTPException(400, "Invalid data")  # 错! 应用 VAL-001

# ❌ 反模式 4: 跳过状态流转
report.status = "final_locked"  # 错! 必须按顺序

# ❌ 反模式 5: 缺少可追溯性
LedgerEntry(amount=100, entry_type="SPEND")
# 错! 缺少 related_entity_type + related_entity_id
```

---

## 十四、快速开始新任务

### 14.1 开发新功能前
1. 阅读本文档确认项目上下文
2. 查询相关 SoT 文档 (按裁判链优先级)
3. 确认现有代码是否已实现
4. 遵循强制规则开发

### 14.2 修改现有功能前
1. 先 Read 相关文件理解现有实现
2. 确认修改是否符合 SoT 规则
3. 如涉及状态/表结构变更，必须先更新 SoT 文档

### 14.3 调试问题时
1. 检查是否违反强制规则
2. 查看 SoT 文档确认业务逻辑
3. 检查错误码是否正确使用

---

**文档版本**: v2.0 (优化版)
**导出日期**: 2025-12-11
**适用场景**: Claude 跨会话上下文传递
**基准版本**: SoT Freeze v2.6 + ASDD Freeze v1.0
