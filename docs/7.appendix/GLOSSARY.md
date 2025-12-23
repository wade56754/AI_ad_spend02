# 术语统一表 (Unified Glossary)

> **文档版本**: v1.0
> **发布日期**: 2025-11-26
> **文档状态**: ✅ Active
> **维护团队**: AI Architecture Team
> **最后审查**: 2025-11-26
> **文档定位**: AI_ad_spend02 项目统一术语词汇表，确保文档、代码、对话中术语一致性

---

## 📌 文档说明

本词汇表是 **AI 广告代投系统** 的统一术语参考，所有术语定义均来自 `docs/2.sot/` 目录下的 SoT 文档。

**使用原则**:
1. **数据库字段/表名/枚举值**: 必须使用英文代码格式（如 `users.role`）
2. **业务概念说明**: 使用中文（如"用户角色必须唯一"）
3. **混合场景**: 优先英文，中文解释（如"User（用户）表"）
4. **代码示例**: 严格使用英文代码

**术语冲突处理**: 当本词汇表与 SoT 文档冲突时，以对应 SoT 文档为准，并提交 Issue 修正本词汇表。

---

## 1. 核心业务术语

### 1.1 三数据流 (Three Data Flows)

**引用**: MASTER.md v4.4 §4, DATA_SCHEMA.md v5.2 §3.3.1

| 术语 | 中文名称 | 字段名 | 提交者 | 时效性 | 用途 |
|------|---------|--------|--------|--------|------|
| **raw 数据流** | 原始数据流 | `conversions_raw`, `raw_spend` | 投手 (media_buyer) | T+0 23:59 前 | 趋势风控检查 (TF-001/002/003) |
| **real 数据流** | 真实数据流 | `real_spend` | 运营 (data_operator) | T+1 12:00 前 | 成本核算基准 |
| **final 数据流** | 最终数据流 | `conversions_final` | 运营 (data_operator) | T+1 14:00 前 | 计费基准 |

**业务规则**:
- `conversions_raw` → 趋势风控输入，不参与计费
- `real_spend` → 成本计算公式: `cost = real_spend + fee`
- `conversions_final` → 收入计算公式: `revenue = conversions_final × unit_price`

---

### 1.2 双账本 (Dual-Ledger System)

**引用**: MASTER.md v4.4 §5, DATA_SCHEMA.md v5.2 §3.4.4, LEDGER_SOT.md v1.1

| 账本类型 | 英文术语 | 字段标识 | 核心实体 | 业务用途 | 允许 entry_type |
|---------|---------|---------|---------|---------|----------------|
| **PROJECT 账本** | PROJECT Ledger | `ledger_type='PROJECT'` | `project_id` | 记录项目收入 (粉数计费) | `REVENUE`, `TOPUP`, `REVERSAL` |
| **SUPPLIER 账本** | SUPPLIER Ledger | `ledger_type='SUPPLIER'` | `supplier_id` | 记录供应商成本 (真实消耗) | `COST`, `TOPUP`, `TRANSFER_OUT`, `TRANSFER_IN`, `REVERSAL` |

**核心原则**:
- **禁止直接修改余额**: 所有资金流动必须通过 `ledger_entries` 表记录
- **借方为正**: `amount > 0` 表示借方
- **贷方为负**: `amount < 0` 表示贷方（直接记录负数）
- **红冲机制**: `final_locked` 后的修正必须通过 `REVERSAL` 类型分录

---

### 1.3 粉数确认 (Lead Confirmation)

**引用**: STATE_MACHINE.md v2.6 §8, BUSINESS_RULES.md v4.1 - BR-RPT-005

| 术语 | 中文 | 英文 | 说明 |
|------|------|------|------|
| **粉数** | 粉数/转化量 | Conversions / Leads | 广告投放带来的有效转化用户数 |
| **原始粉数** | 投手提交粉数 | `conversions_raw` | T+0 当日投手提交，用于趋势监控 |
| **最终粉数** | 运营确认粉数 | `conversions_final` | T+1 运营审核后的计费基准粉数 |
| **趋势风控** | 趋势异常检测 | Trend Risk Control | 粉数/消耗异常波动检测 (TF-001/002/003) |
| **计费锁定** | 计费终态 | `final_locked` | 日报状态终态，触发账本记录创建 |

**8 状态机流程** (STATE_MACHINE.md v2.6 §8):
```
raw_submitted → trend_pending → trend_ok/trend_flagged → trend_resolved
→ final_pending → final_confirmed → final_locked
```

---

## 2. 状态机术语 (State Machine Terms)

**引用**: STATE_MACHINE.md v2.6

### 2.1 日报状态 (Daily Report Status - 8 State Machine)

| 状态值 | 中文名称 | 角色操作 | 业务含义 | 是否终态 |
|-------|---------|---------|---------|---------|
| `raw_submitted` | 已提交原始数据 | media_buyer | 投手提交 raw 数据 | ❌ |
| `trend_pending` | 趋势检查中 | system | 等待风控规则校验 | ❌ |
| `trend_ok` | 趋势正常 | system | 未触发风控规则 | ❌ |
| `trend_flagged` | 趋势异常 | system | 触发 TF-001/002/003 规则 | ❌ |
| `trend_resolved` | 趋势已复核 | data_operator | 运营确认"正常波动" | ❌ |
| `final_pending` | 待确认 final | data_operator | 等待运营录入 real_spend | ❌ |
| `final_confirmed` | final 已确认 | data_operator | 运营确认 conversions_final | ❌ |
| `final_locked` | 计费锁定 | system | 计费终态，触发账本创建 | ✅ |

**终态保护**: `final_locked` 后禁止修改，仅可通过 REVERSAL 红冲。

---

### 2.2 充值状态 (Topup Request Status)

**引用**: STATE_MACHINE.md v2.6 §充值申请状态机

| 状态值 | 中文名称 | 角色操作 | 业务含义 | 是否终态 |
|-------|---------|---------|---------|---------|
| `draft` | 草稿 | media_buyer/account_manager | 未提交状态 | ❌ |
| `pending_review` | 待复核 | data_operator | 等待数据运营复核 | ❌ |
| `finance_approve` | 财务批准 | finance | 财务终审通过 | ❌ |
| `paid` | 已支付 | finance | 已完成支付 | ❌ |
| `completed` | 已完成 | system | 充值完成（终态） | ✅ |
| `rejected` | 已拒绝 | data_operator/finance | 审核拒绝（终态） | ✅ |
| `cancelled` | 已取消 | 申请人 | 申请人主动取消（终态） | ✅ |

---

### 2.3 项目状态 (Project Status)

| 状态值 | 中文名称 | 业务含义 | 是否终态 |
|-------|---------|---------|---------|
| `draft` | 草稿 | 项目创建中 | ❌ |
| `active` | 活跃 | 正常运行中 | ❌ |
| `suspended` | 暂停 | 临时停用 | ❌ |
| `archived` | 已归档 | 项目归档（终态） | ✅ |

---

### 2.4 广告账户状态 (Ad Account Status)

| 状态值 | 中文名称 | 业务含义 | 是否终态 |
|-------|---------|---------|---------|
| `new` | 新建 | 账户初始状态 | ❌ |
| `testing` | 测试中 | 账户测试阶段 | ❌ |
| `active` | 活跃 | 正常投放中 | ❌ |
| `suspended` | 暂停 | 临时停用 | ❌ |
| `dead` | 死亡/不可用 | 不可恢复状态 | ❌ |
| `archived` | 已归档 | 历史归档（终态） | ✅ |

---

## 3. 角色与权限术语 (Role & Permission Terms)

**引用**: DATA_SCHEMA.md v5.2 §3.1.1, BUSINESS_RULES.md v4.1 - BR-AUTH-001

### 3.1 五大固定角色

| 角色代码 | 中文名称 | 权限级别 | 主要职责 | 关键操作权限 |
|---------|---------|---------|---------|-------------|
| `admin` | 系统管理员 | L5 (最高) | 系统配置、全局审计、紧急干预 | 所有权限 |
| `finance` | 财务 | L4 | 充值终审、资金监控、财务对账 | 充值终审、账本查询、对账管理 |
| `data_operator` | 数据运营/户管 | L3 | 日报审核、数据校验、充值复核 | 日报审核、真实消耗录入、充值复核 |
| `account_manager` | 客户经理 | L2 | 项目维护、成员管理、充值申请 | 项目管理、账户分配 |
| `media_buyer` | 投手/媒体采购 | L1 (最低) | 日报提交、充值申请、凭证上传 | 日报提交、查看自己的数据 |

**强制约束**:
- ❌ **禁止添加新角色**（如 `super_admin`, `manager`, `operator` 等）
- ❌ **禁止一个用户拥有多个角色**（不支持角色数组）
- ✅ 角色一旦创建，仅 `admin` 可修改（需记录审计日志）

---

### 3.2 职责分离 (Separation of Duties - SOD)

**引用**: BUSINESS_RULES.md v4.1 - BR-FIN-002

| 原则 | 说明 | 适用场景 |
|------|------|---------|
| **申请人 ≠ 审核人** | 提交申请者不能自我审批 | 充值申请、日报审核 |
| **复核人 ≠ 终审人** | 数据复核与财务终审必须分离 | 充值流程 |
| **操作人 ≠ 审计人** | 执行操作与审计查询需分离 | 审计日志访问 |

---

## 4. 数据库术语 (Database Terms)

**引用**: DATA_SCHEMA.md v5.2

### 4.1 主键与外键类型

| 实体类型 | 主键类型 | PostgreSQL 类型 | SQLAlchemy 类型 | 示例表 |
|---------|---------|----------------|----------------|--------|
| **跨系统实体** | UUID | `UUID` | `UUID(as_uuid=True)` | `users`, `channels`, `suppliers` |
| **核心业务表** | BIGSERIAL | `BIGSERIAL` | `BigInteger` | `projects`, `ad_accounts`, `daily_reports`, `topup_requests`, `ledger_entries` |

**外键一致性规则**:
- ✅ 外键类型必须与被引用主键完全一致
- ✅ 引用 `users.id` 必须是 `UUID`
- ✅ 引用 `projects.id` 必须是 `BIGINT`

---

### 4.2 金额字段规范

| 字段名 | 中文 | 数据类型 | 精度 | 说明 |
|-------|------|---------|------|------|
| `amount` | 金额 | `DECIMAL(15,2)` | 2 位小数 | 通用金额字段 |
| `balance` | 余额 | `DECIMAL(15,2)` | 2 位小数 | 账户余额（禁止直接修改） |
| `raw_spend` | 原始消耗 | `DECIMAL(15,2)` | 2 位小数 | 投手提交的消耗 (T+0) |
| `real_spend` | 真实消耗 | `DECIMAL(15,2)` | 2 位小数 | 运营录入的消耗 (T+1)，成本核算基准 |
| `unit_price` | 单粉价格 | `DECIMAL(15,2)` | 2 位小数 | 项目单粉价格 (Per Lead) |

**强制规则** (BR-FIN-003):
- ❌ **禁止使用 `float` 或 `double` 表示金额**
- ✅ Python 必须使用 `Decimal` 类型
- ✅ 前端传输使用 `string` 类型（避免精度丢失）

---

### 4.3 时间字段规范

| 字段名 | 中文 | 数据类型 | 时区 | 说明 |
|-------|------|---------|------|------|
| `created_at` | 创建时间 | `TIMESTAMPTZ` | UTC | 记录创建时间 |
| `updated_at` | 更新时间 | `TIMESTAMPTZ` | UTC | 记录最后更新时间 |
| `submitted_at` | 提交时间 | `TIMESTAMPTZ` | UTC | 业务提交时间 |
| `approved_at` | 审批时间 | `TIMESTAMPTZ` | UTC | 审批通过时间 |
| `final_locked_at` | 计费锁定时间 | `TIMESTAMPTZ` | UTC | 日报计费锁定时间戳 |

**强制规则** (BR-DATA-002):
- ✅ 数据库存储统一使用 `TIMESTAMPTZ`（带时区）
- ✅ 应用层使用 UTC: `datetime.now(timezone.utc)`
- ❌ **禁止使用 `datetime.now()` 无时区版本**

---

## 5. API 术语 (API Terms)

**引用**: API_SOT.md v9.3, ERROR_CODES_SOT.md v2.1

### 5.1 响应格式 (Envelope)

| 字段名 | 类型 | 说明 | 示例 |
|-------|------|------|------|
| `success` | `boolean` | 请求是否成功 | `true` / `false` |
| `data` | `any` | 业务数据 | `{"id": 1, "name": "..."}` |
| `message` | `string` | 操作提示信息 | "操作成功" |
| `code` | `string` | 业务错误码 | "BIZ_001" |
| `request_id` | `string (UUID)` | 请求追踪 ID | "550e8400-e29b-..." |
| `timestamp` | `string (ISO 8601)` | 响应时间戳 | "2025-11-26T10:00:00Z" |

**成功响应示例**:
```json
{
  "success": true,
  "data": {"id": 123, "status": "active"},
  "message": "操作成功",
  "code": "SUCCESS",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-11-26T10:00:00Z"
}
```

**错误响应示例**:
```json
{
  "success": false,
  "error": {
    "code": "BIZ_003",
    "message": "状态转换非法",
    "details": {"from": "approved", "to": "pending"}
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-11-26T10:00:00Z"
}
```

---

### 5.2 错误码分类

**引用**: ERROR_CODES_SOT.md v2.1

| 前缀 | 类别 | HTTP 状态码范围 | 使用场景 |
|------|------|----------------|---------|
| `AUTH_` | 认证授权错误 | 401, 403, 404 | Token 无效、权限不足、用户不存在 |
| `BIZ_` | 业务逻辑错误 | 400, 404, 409 | 业务规则验证失败、资源不存在 |
| `VALIDATION_` | 参数验证错误 | 400 | 必填字段缺失、格式无效 |
| `SYS_` | 系统错误 | 429, 500, 503, 504 | 系统内部错误、服务不可用 |
| `DB_` | 数据库错误 | 400, 409, 500 | 唯一性约束违反、外键约束违反 |
| `STATE_` | 状态机错误 | 400, 403, 409 | 非法状态流转、终态非法回退 |
| `TREND_` | 趋势风控错误 | 200, 400 | 粉数骤降、粉数骤增、消耗异常 |

**常用错误码**:
- `AUTH_500`: 权限不足
- `BIZ_002`: 资源不存在
- `BIZ_301`: 状态转换不允许
- `STATE_400`: 非法状态流转
- `STATE_402`: 终态非法回退
- `TREND_001`: 趋势风控触发

---

## 6. 业务流程术语 (Business Process Terms)

**引用**: BUSINESS_RULES.md v4.1

### 6.1 充值流程 (Topup Process)

| 术语 | 中文 | 说明 |
|------|------|------|
| **Topup Request** | 充值申请 | 向广告账户充值的申请流程 |
| **Applicant** | 申请人 | 发起充值申请的用户 (`media_buyer` 或 `account_manager`) |
| **Reviewer** | 复核人 | 数据运营复核 (`data_operator`) |
| **Approver** | 终审人 | 财务终审 (`finance`) |
| **Voucher** | 充值凭证 | 充值单据的 URL 路径 |
| **Dual-write** | 双写 | 充值成功后同时写入 `topup_transactions` 和 `ledger_entries` |

---

### 6.2 对账流程 (Reconciliation Process)

| 术语 | 中文 | 说明 |
|------|------|------|
| **Reconciliation Batch** | 对账批次 | 定期对账的批次单位 |
| **System Spend** | 系统消耗 | 日报中的 `real_spend` 汇总 |
| **External Spend** | 外部消耗 | 从广告平台导入的消耗数据 |
| **Difference Amount** | 差异金额 | `system_spend - external_spend` |
| **Adjustment** | 调账 | 对差异进行调整的操作 |

---

### 6.3 日报流程 (Daily Report Process)

| 术语 | 中文 | 说明 |
|------|------|------|
| **Daily Report** | 日报 | 每日广告投放数据报告 |
| **Trend Flag** | 趋势标记 | 固定枚举: `normal` / `flagged` / `resolved` |
| **Trend Flag Reason** | 风控触发原因 | 如 "TF-001: 粉数骤降 50%" |
| **Trend Resolution Note** | 运营复核说明 | 运营确认"正常波动"的说明 |
| **Reversal** | 红冲 | `final_locked` 后的修正机制 |

---

## 7. 技术架构术语 (Technical Architecture Terms)

**引用**: MASTER.md v4.4

### 7.1 ASDD (AI-Spec-Driven Development)

| 术语 | 中文 | 说明 |
|------|------|------|
| **ASDD** | AI 规格驱动开发 | 基于 AI 辅助的规格驱动开发方法论 |
| **SoT** | 唯一真相源 | Single Source of Truth，规范文档的最高优先级 |
| **裁判链** | 仲裁优先级 | 多个 SoT 文档冲突时的裁决顺序 |
| **Freeze** | 版本冻结 | 规范文档达到稳定版本，禁止随意修改 |
| **RFC** | 需求变更申请 | Request For Change，规范修改的正式流程 |

---

### 7.2 SoT 裁判链 (Arbitration Chain)

**引用**: PROJECT_RULES.md v3.1 §1

```
MASTER.md v4.4 (系统宪法)
    ↓
STATE_MACHINE.md v2.6 (状态定义)
    ↓
DATA_SCHEMA.md v5.2 (数据结构)
    ↓
BUSINESS_RULES.md v4.1 (业务规则)
    ↓
API_SOT.md v9.3 (API 契约)
    ↓
ERROR_CODES_SOT.md v2.1 (错误码)
    ↓
AUTH_SPEC.md v2.0 (认证授权)
    ↓
LEDGER_SOT.md v1.1 (账本规则)
```

**冲突处理**: 优先级高的文档裁决优先级低的文档。

---

### 7.3 四层文档架构

**引用**: MASTER.md v4.4 §文档架构

| 层级 | 目录 | 说明 | 适用人员 |
|------|------|------|---------|
| **Tier 1: Overview** | `docs/1.overview/` | 系统架构、总体设计 | 架构师、Tech Lead |
| **Tier 2: SoT** | `docs/2.sot/` | 规范真相源（最高优先级） | 所有开发者 |
| **Tier 3: Dev Guides** | `docs/3.dev-guides/` | 开发指南、最佳实践 | 后端/前端开发 |
| **Tier 4: Appendix** | `docs/4.appendix/` | 词汇表、决策记录、检查清单 | 全员参考 |

---

## 8. 代码规范术语 (Code Convention Terms)

### 8.1 后端术语

| 术语 | 说明 | 示例 |
|------|------|------|
| **Schema** | Pydantic 数据模型 | `backend/schemas/daily_report.py` |
| **Service** | 业务逻辑服务 | `backend/services/daily_report_service.py` |
| **Router** | FastAPI 路由 | `backend/routers/daily_reports.py` |
| **Model** | SQLAlchemy 数据库模型 | `backend/models/daily_report.py` |
| **Exception Handler** | 异常处理器 | `backend/core/exceptions.py` |

---

### 8.2 前端术语

| 术语 | 说明 | 示例 |
|------|------|------|
| **apiFetch** | 统一 API 调用工具 | `lib/api.ts::apiFetch()` |
| **App Router** | Next.js 路由模式 | `app/` 目录结构 |
| **Server Component** | 服务端组件 | 默认所有组件 |
| **Client Component** | 客户端组件 | 标记 `'use client'` 的组件 |

---

## 9. 历史兼容术语 (Legacy Terms - 仅供理解旧代码)

**⚠️ 以下术语已废弃，禁止在新代码中使用**

| 旧术语 | 新术语 | 迁移时间 | 说明 |
|-------|--------|---------|------|
| `data_clerk` | `data_operator` | 2025-11 | 旧角色名 |
| `manager` | `account_manager` | 2025-11 | 旧角色名 |
| `recharge_requests` | `topup_requests` | 2025-11 | 旧表名 |
| `user_profiles` | `users` | 2025-11 | 旧表名 |
| 4 状态机 (`draft/pending/approved/rejected`) | 8 状态机 (见 §2.1) | 2025-11 | 旧日报状态机 |

---

## 10. 变更历史

### v1.0 (2025-11-26)
- ✅ 初始版本发布
- ✅ 整合 SoT Freeze v1.0 所有术语
- ✅ 新增三数据流、双账本、8 状态机术语
- ✅ 新增 API Envelope 术语、错误码分类
- ✅ 新增 ASDD 方法论术语
- ✅ 新增历史兼容术语表

---

## 📧 维护与反馈

**维护团队**: AI Architecture Team
**术语提议**: 通过 GitHub Issue 提交新术语或术语修正
**冲突报告**: 发现术语与 SoT 文档冲突时，立即提交 Issue

---

> **版权声明**: 本文档为 AI 广告代投系统的内部技术文档，仅供授权人员使用。
