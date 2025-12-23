# 架构决策记录 (Architecture Decision Records)

> **文档版本**: v1.0
> **发布日期**: 2025-11-26
> **文档状态**: ✅ Active
> **维护团队**: AI Architecture Team
> **最后审查**: 2025-11-26
> **文档定位**: AI_ad_spend02 项目重大架构决策的历史记录与裁决依据

---

## 📌 文档说明

本文档采用 **ADR (Architecture Decision Record)** 格式，记录 AI 广告代投系统的所有重大架构决策。

**ADR 编号规则**:
- `ADR-001` ~ `ADR-099`: 系统架构与基础设施
- `ADR-100` ~ `ADR-199`: 数据库与数据架构
- `ADR-200` ~ `ADR-299`: API 与接口设计
- `ADR-300` ~ `ADR-399`: 前端架构与 UI
- `ADR-400` ~ `ADR-499`: 业务流程与状态机
- `ADR-500` ~ `ADR-599`: 安全与权限
- `ADR-600` ~ `ADR-699`: 部署与运维
- `ADR-700` ~ `ADR-799`: 文档与协作

**状态定义**:
- **Proposed**: 提议中，尚未正式实施
- **Accepted**: 已接受并实施
- **Superseded**: 已被后续决策替代
- **Deprecated**: 已废弃，但保留记录

---

## 目录

### 系统架构 (ADR-001 ~ ADR-099)
- [ADR-001: 采用 FastAPI + Supabase 技术栈](#adr-001-采用-fastapi--supabase-技术栈)
- [ADR-002: 禁用 Redis 队列，仅用于缓存](#adr-002-禁用-redis-队列仅用于缓存)
- [ADR-003: 采用同步 SQLAlchemy，禁用异步](#adr-003-采用同步-sqlalchemy禁用异步)
- [ADR-004: 前端必须通过 BFF 访问后端](#adr-004-前端必须通过-bff-访问后端)

### 数据库与数据架构 (ADR-100 ~ ADR-199)
- [ADR-101: 采用双账本 (PROJECT/SUPPLIER) 架构](#adr-101-采用双账本-projectsupplier-架构)
- [ADR-102: 采用三数据流 (raw/real/final) 分离设计](#adr-102-采用三数据流-rawrealfinal-分离设计)
- [ADR-103: 主键类型规则：UUID vs BIGSERIAL](#adr-103-主键类型规则uuid-vs-bigserial)
- [ADR-104: 禁止物理删除核心业务数据](#adr-104-禁止物理删除核心业务数据)
- [ADR-105: 金额字段必须使用 DECIMAL(15,2)](#adr-105-金额字段必须使用-decimal152)

### API 与接口设计 (ADR-200 ~ ADR-299)
- [ADR-201: 采用 Envelope 统一响应格式](#adr-201-采用-envelope-统一响应格式)
- [ADR-202: 错误码必须集中定义在 ERROR_CODES_SOT.md](#adr-202-错误码必须集中定义在-error_codes_sotmd)
- [ADR-203: API 路由必须使用平面化结构](#adr-203-api-路由必须使用平面化结构)

### 前端架构与 UI (ADR-300 ~ ADR-399)
- [ADR-301: 采用 Next.js App Router 模式](#adr-301-采用-nextjs-app-router-模式)
- [ADR-302: UI 组件库采用 shadcn/ui](#adr-302-ui-组件库采用-shadcnui)

### 业务流程与状态机 (ADR-400 ~ ADR-499)
- [ADR-401: 日报采用 8 状态机替代 4 状态机](#adr-401-日报采用-8-状态机替代-4-状态机)
- [ADR-402: 终态不可回退，仅可红冲](#adr-402-终态不可回退仅可红冲)
- [ADR-403: 充值流程必须实现三层审批 (SOD)](#adr-403-充值流程必须实现三层审批-sod)

### 安全与权限 (ADR-500 ~ ADR-599)
- [ADR-501: 采用 Supabase Auth，禁用本地 JWT](#adr-501-采用-supabase-auth禁用本地-jwt)
- [ADR-502: 当前版本禁用 RLS，使用 Service 层 RBAC](#adr-502-当前版本禁用-rls使用-service-层-rbac)
- [ADR-503: 角色固定为 5 个，禁止扩展](#adr-503-角色固定为-5-个禁止扩展)

### 文档与协作 (ADR-700 ~ ADR-799)
- [ADR-701: 采用 SoT 裁判链体系](#adr-701-采用-sot-裁判链体系)
- [ADR-702: 文档分为四层架构](#adr-702-文档分为四层架构)
- [ADR-703: 规范文档达到 Freeze 版本后禁止随意修改](#adr-703-规范文档达到-freeze-版本后禁止随意修改)

---

## 系统架构 (ADR-001 ~ ADR-099)

---

### ADR-001: 采用 FastAPI + Supabase 技术栈

**编号**: ADR-001
**状态**: ✅ Accepted
**决策日期**: 2025-10
**决策人**: AI Architecture Team
**影响范围**: 后端框架、数据库、认证

#### 背景 (Context)

项目初期需要选择后端技术栈，需满足以下需求：
- 快速开发、类型安全、异步支持
- PostgreSQL 数据库托管服务
- 内置认证服务，减少自研成本
- 易于与 AI 辅助开发工具（Claude Code）集成

#### 决策 (Decision)

采用以下技术栈：
- **后端框架**: FastAPI
- **数据库**: PostgreSQL 15 (Supabase 托管)
- **认证**: Supabase Auth
- **ORM**: SQLAlchemy (同步版本)

#### 理由 (Rationale)

**FastAPI**:
- 基于 Pydantic 的类型验证，减少参数校验代码
- 自动生成 OpenAPI 文档
- 高性能，支持异步（虽然项目使用同步版）

**Supabase**:
- 提供托管 PostgreSQL，减少运维成本
- 内置 Auth 服务，支持 JWT、OAuth
- 提供 REST API / GraphQL / Realtime 订阅（未来扩展）

#### 影响 (Consequences)

**正面影响**:
- ✅ 开发效率提升 30%（类型检查 + 文档生成）
- ✅ 认证模块无需自研，安全性有保障
- ✅ 数据库托管，减少运维负担

**负面影响**:
- ❌ Supabase 锁定：迁移成本较高
- ❌ 社区生态相比 Django 较小

**缓解措施**:
- 通过 Service 层隔离数据库访问，降低迁移成本
- 关键业务逻辑在 Service 层实现，与框架解耦

#### 相关文档
- `MASTER.md` v3.4 §技术栈
- `API_SOT.md` v9.0 §统一规范

---

### ADR-002: 禁用 Redis 队列，仅用于缓存

**编号**: ADR-002
**状态**: ✅ Accepted
**决策日期**: 2025-10
**决策人**: AI Architecture Team
**影响范围**: 后端架构、异步任务处理

#### 背景

系统需要异步任务处理（如日报导入、对账批处理），可选方案：
1. Redis 队列 + RQ/Celery
2. 同步处理 + 数据库任务表
3. Supabase Functions (Edge Functions)

#### 决策

**禁用 Redis 队列 (RQ/Celery)**，仅使用 Redis 作为：
- Session 缓存
- 速率限制计数器
- 短期数据缓存

异步任务通过 **数据库任务表 + 定时轮询** 实现。

#### 理由

**禁用队列的原因**:
- ❌ 增加架构复杂度（需要 Worker 进程管理）
- ❌ 当前业务量小，同步处理足够（日报/充值量级 < 1000/天）
- ❌ RQ/Celery 需要额外运维（进程监控、失败重试）

**数据库任务表方案**:
- ✅ 简单可靠，事务一致性有保障
- ✅ 任务状态持久化，便于审计
- ✅ 失败重试机制清晰（基于状态机）

#### 影响

**正面影响**:
- ✅ 架构简化，降低运维成本
- ✅ 任务执行过程可追溯

**负面影响**:
- ❌ 处理延迟较高（轮询间隔 1-5 分钟）
- ❌ 不适合高并发异步场景

**未来迁移路径**:
- 当日报量级超过 5000/天时，重新评估引入消息队列

#### 相关文档
- `MASTER.md` v3.4 §技术栈

---

### ADR-003: 采用同步 SQLAlchemy，禁用异步

**编号**: ADR-003
**状态**: ✅ Accepted
**决策日期**: 2025-10
**影响范围**: 后端 ORM

#### 背景

SQLAlchemy 支持同步和异步两种模式，需选择一种。

#### 决策

**采用同步 SQLAlchemy**，禁用异步。

#### 理由

- ✅ 同步代码更易调试、理解
- ✅ 避免 `async/await` 传染性（所有函数都需要 async）
- ✅ 当前业务并发量小（QPS < 100），同步性能足够
- ✅ AI 辅助工具对同步代码支持更好

#### 影响

**正面影响**:
- ✅ 代码可读性强
- ✅ 降低学习成本

**负面影响**:
- ❌ 高并发场景性能受限

**未来迁移**:
- 当 QPS 超过 500 时，考虑迁移至异步

#### 相关文档
- `MASTER.md` v3.4 §技术栈

---

### ADR-004: 前端必须通过 BFF 访问后端

**编号**: ADR-004
**状态**: ✅ Accepted
**决策日期**: 2025-10
**影响范围**: 前后端交互

#### 背景

前端访问后端数据有两种方案：
1. 直接调用 Supabase API (REST/GraphQL)
2. 通过 FastAPI BFF (Backend for Frontend) 层

#### 决策

**前端必须通过 FastAPI BFF 访问后端**，禁止直连 Supabase 数据库。

**例外**: 认证相关操作 (`signInWithPassword` / `signOut`) 可直接调用 Supabase Auth。

#### 理由

**禁止直连数据库**:
- ❌ 绕过业务规则校验（状态机、权限、审计）
- ❌ 数据安全风险（前端可直接操作数据库）
- ❌ 无法集中记录审计日志

**BFF 层优势**:
- ✅ 统一权限校验 (`@require_role` 装饰器)
- ✅ 统一错误码处理
- ✅ 统一审计日志记录
- ✅ 业务逻辑集中在 Service 层

#### 影响

**正面影响**:
- ✅ 数据安全性提升
- ✅ 业务规则强制执行

**负面影响**:
- ❌ 增加一层 API 调用（延迟 +10~30ms）

#### 实施规范

```typescript
// ✅ 正确：使用 apiFetch
import { apiFetch } from '@/lib/api'
const data = await apiFetch('/api/v1/projects')

// ❌ 错误：直接调用 Supabase
import { supabase } from '@/lib/supabase'
const { data } = await supabase.from('projects').select('*')

// ✅ 例外：认证操作
const { data } = await supabase.auth.signInWithPassword({...})
```

#### 相关文档
- `API_SOT.md` v9.0 §2.2 认证与授权
- `PROJECT_RULES.md` v3.1 §4 前端禁止绕过 BFF

---

## 数据库与数据架构 (ADR-100 ~ ADR-199)

---

### ADR-101: 采用双账本 (PROJECT/SUPPLIER) 架构

**编号**: ADR-101
**状态**: ✅ Accepted
**决策日期**: 2025-11
**影响范围**: 财务模块、账本设计

#### 背景

系统需要追踪两类资金流：
1. **项目收入**: 基于粉数计费（`revenue = conversions_final × unit_price`）
2. **供应商成本**: 基于真实消耗（`cost = real_spend + fee`）

单账本设计无法清晰区分两类账户的资金流。

#### 决策

采用 **双账本架构**:
- **PROJECT 账本**: 记录项目收入（粉数计费）
- **SUPPLIER 账本**: 记录供应商成本（真实消耗）

通过 `ledger_entries.ledger_type` 字段区分：
- `ledger_type='PROJECT'` → `project_id` 必填
- `ledger_type='SUPPLIER'` → `supplier_id` 必填

#### 理由

**双账本优势**:
- ✅ 清晰分离项目收入与供应商成本
- ✅ 支持独立的财务对账
- ✅ 支持项目毛利计算: `profit = revenue - cost`
- ✅ 支持供应商账户余额追踪

**单账本问题**:
- ❌ 收入与成本混在一起，难以对账
- ❌ 无法独立追踪供应商余额

#### 影响

**正面影响**:
- ✅ 财务流程清晰
- ✅ 支持多供应商场景

**负面影响**:
- ❌ 查询复杂度增加（需要 JOIN 两个账本）

#### 实施规范

```python
# PROJECT 账本：记录项目收入
LedgerEntry(
    ledger_type='PROJECT',
    project_id=123,
    entry_type='REVENUE',
    amount=Decimal('1000.00'),  # conversions_final × unit_price
    notes='日报 #456 粉数计费'
)

# SUPPLIER 账本：记录供应商成本
LedgerEntry(
    ledger_type='SUPPLIER',
    supplier_id=uuid('...'),
    entry_type='COST',
    amount=Decimal('-800.00'),  # -(real_spend + fee)
    notes='日报 #456 真实消耗'
)
```

#### 相关文档
- `LEDGER_SOT.md` v1.1 §2 双账本体系
- `DATA_SCHEMA.md` v5.2 §3.4.4 ledger_entries 表
- `MASTER.md` v3.4 §5 双账本架构

---

### ADR-102: 采用三数据流 (raw/real/final) 分离设计

**编号**: ADR-102
**状态**: ✅ Accepted
**决策日期**: 2025-11
**影响范围**: 日报模块、粉数确认流程

#### 背景

广告投放数据有三个时间节点：
1. **T+0 当日**: 投手提交初步数据
2. **T+1 上午**: 运营录入真实消耗
3. **T+1 下午**: 运营确认最终粉数

传统单一数据流（`spend` / `conversions`）无法追溯历史版本。

#### 决策

采用 **三数据流分离设计**:

| 数据流 | 字段 | 提交者 | 时效性 | 用途 |
|-------|------|--------|--------|------|
| **raw** | `conversions_raw`, `raw_spend` | 投手 | T+0 23:59 前 | 趋势风控 (TF-001/002/003) |
| **real** | `real_spend` | 运营 | T+1 12:00 前 | 成本核算 |
| **final** | `conversions_final` | 运营 | T+1 14:00 前 | 计费基准 |

#### 理由

**三数据流优势**:
- ✅ 数据不可变性：历史版本永久保留
- ✅ 审计可追溯：任何修改都有记录
- ✅ 支持趋势风控：对比 raw 和 final 粉数差异
- ✅ 职责分离：投手提交 raw，运营确认 final

**单数据流问题**:
- ❌ 数据覆盖：无法追溯历史版本
- ❌ 审计困难：修改记录不清晰

#### 影响

**正面影响**:
- ✅ 数据完整性高
- ✅ 审计合规

**负面影响**:
- ❌ 存储成本增加（3 倍字段）

#### 实施规范

```python
# T+0 投手提交 raw 数据
daily_report.conversions_raw = 100
daily_report.raw_spend = Decimal('500.00')
daily_report.status = 'raw_submitted'

# T+1 运营录入 real 数据
daily_report.real_spend = Decimal('480.00')
daily_report.status = 'final_pending'

# T+1 运营确认 final 数据
daily_report.conversions_final = 95
daily_report.status = 'final_confirmed'

# 计费公式
revenue = daily_report.conversions_final * project.unit_price
cost = daily_report.real_spend + fee
```

#### 相关文档
- `MASTER.md` v3.4 §4 三数据流设计
- `DATA_SCHEMA.md` v5.2 §3.3.1 daily_reports 表
- `STATE_MACHINE.md` v2.6 §8 粉数确认状态机

---

### ADR-103: 主键类型规则：UUID vs BIGSERIAL

**编号**: ADR-103
**状态**: ✅ Accepted
**决策日期**: 2025-10
**影响范围**: 数据库设计

#### 背景

PostgreSQL 主键类型选择：
- `UUID`: 全局唯一，适合分布式系统
- `BIGSERIAL`: 自增整数，性能更好

#### 决策

**分类规则**:
- **跨系统实体**: 使用 UUID（如 `users`, `channels`, `suppliers`）
- **核心业务表**: 使用 BIGSERIAL（如 `projects`, `ad_accounts`, `daily_reports`）

#### 理由

**UUID 适用场景**:
- ✅ 与外部系统同步（Supabase Auth）
- ✅ 需要全局唯一 ID

**BIGSERIAL 适用场景**:
- ✅ 性能更好（索引更小）
- ✅ 便于调试（连续整数）
- ✅ 节省存储空间

#### 影响

**外键一致性规则**:
- ✅ 外键类型必须与被引用主键一致
- ✅ 引用 `users.id` 必须是 `UUID`
- ✅ 引用 `projects.id` 必须是 `BIGINT`

#### 相关文档
- `DATA_SCHEMA.md` v5.2 §1.1 主键规则

---

### ADR-104: 禁止物理删除核心业务数据

**编号**: ADR-104
**状态**: ✅ Accepted
**决策日期**: 2025-10
**影响范围**: 数据库操作

#### 背景

核心业务数据（项目/账户/充值/日报/账本）删除后无法恢复，影响审计。

#### 决策

**禁止物理删除以下表数据**:
- `projects`, `ad_accounts`, `daily_reports`
- `topup_requests`, `ledger_entries`
- `reconciliation_batches`

**必须通过状态标记删除**:
- 项目: `status='archived'`
- 账户: `status='archived'`
- 日报: `status='cancelled'` (仅 draft 可取消)

#### 理由

- ✅ 审计合规：历史数据永久保留
- ✅ 数据恢复：误删可恢复
- ✅ 关联查询：外键关联不会断裂

#### 影响

**正面影响**:
- ✅ 数据完整性高

**负面影响**:
- ❌ 存储成本增加

#### 相关文档
- `BUSINESS_RULES.md` v3.1 - BR-DATA-001

---

### ADR-105: 金额字段必须使用 DECIMAL(15,2)

**编号**: ADR-105
**状态**: ✅ Accepted
**决策日期**: 2025-10
**影响范围**: 数据库设计、后端代码

#### 背景

金额字段精度问题：
- `FLOAT/DOUBLE`: 精度丢失（0.1 + 0.2 ≠ 0.3）
- `DECIMAL`: 精确小数运算

#### 决策

**所有金额字段必须使用 `DECIMAL(15,2)`**:
- PostgreSQL: `DECIMAL(15,2)`
- SQLAlchemy: `Numeric(15,2)`
- Python: `Decimal` 类型
- TypeScript: `string` (传输) / `number` (展示)

#### 理由

- ✅ 精确计算：避免浮点数精度问题
- ✅ 财务合规：金额计算必须精确到分

#### 影响

**强制规则**:
- ❌ **禁止使用 `float` 或 `double` 表示金额**
- ✅ Python 必须使用 `Decimal` 类型
- ✅ 前端传输使用 `string` 类型

#### 相关文档
- `DATA_SCHEMA.md` v5.2 §1.1 数据类型规范
- `BUSINESS_RULES.md` v3.1 - BR-FIN-003

---

## API 与接口设计 (ADR-200 ~ ADR-299)

---

### ADR-201: 采用 Envelope 统一响应格式

**编号**: ADR-201
**状态**: ✅ Accepted
**决策日期**: 2025-10
**影响范围**: API 响应格式

#### 背景

API 响应格式不统一，前端解析困难。

#### 决策

**采用 Envelope 统一响应格式**:

```json
{
  "success": true,
  "data": {...},
  "message": "操作成功",
  "code": "SUCCESS",
  "request_id": "550e8400-e29b-...",
  "timestamp": "2025-11-26T10:00:00Z"
}
```

#### 理由

- ✅ 前端统一解析逻辑
- ✅ 便于添加元信息（request_id / timestamp）
- ✅ 错误码标准化

#### 影响

**禁止行为**:
- ❌ 直接返回 `{"id": 1, "name": "..."}`
- ✅ 必须使用 `success_response(data={...})`

#### 相关文档
- `API_SOT.md` v9.0 §4 响应格式规范

---

### ADR-202: 错误码必须集中定义在 ERROR_CODES_SOT.md

**编号**: ADR-202
**状态**: ✅ Accepted
**决策日期**: 2025-10
**影响范围**: 错误处理

#### 背景

错误码分散定义，前后端不一致。

#### 决策

**所有错误码必须在 `ERROR_CODES_SOT.md` 中集中定义**，禁止在代码中自创错误码。

#### 理由

- ✅ 错误码唯一性保证
- ✅ 前后端对照表清晰
- ✅ 便于维护和文档生成

#### 影响

**禁止行为**:
```python
# ❌ 错误：自创错误码
raise HTTPException(400, "Invalid request")

# ✅ 正确：使用标准错误码
raise BusinessError(code=BusinessErrorCodes.INVALID_OPERATION)
```

#### 相关文档
- `ERROR_CODES_SOT.md` v2.1

---

### ADR-203: API 路由必须使用平面化结构

**编号**: ADR-203
**状态**: ✅ Accepted
**决策日期**: 2025-10
**影响范围**: API 路由设计

#### 背景

RESTful 嵌套路由 `/projects/{project_id}/ad-accounts` 过深，前端调用复杂。

#### 决策

**采用平面化路由结构**:
- ✅ `/api/v1/ad-accounts?project_id={project_id}`
- ❌ `/api/v1/projects/{project_id}/ad-accounts`

#### 理由

- ✅ URL 简洁
- ✅ 前端查询更灵活
- ✅ 避免嵌套层级过深

#### 相关文档
- `API_SOT.md` v9.0 §2.1 路由规范

---

## 业务流程与状态机 (ADR-400 ~ ADR-499)

---

### ADR-401: 日报采用 8 状态机替代 4 状态机

**编号**: ADR-401
**状态**: ✅ Accepted
**决策日期**: 2025-11
**影响范围**: 日报模块、粉数确认流程

#### 背景

原 4 状态机 (`draft/pending/approved/rejected`) 无法满足粉数确认流程需求：
- 无法区分趋势风控阶段
- 无法区分 raw 数据和 final 数据

#### 决策

采用 **8 状态机**:
```
raw_submitted → trend_pending → trend_ok/trend_flagged → trend_resolved
→ final_pending → final_confirmed → final_locked
```

#### 理由

- ✅ 清晰区分数据流转阶段
- ✅ 支持趋势风控
- ✅ 支持职责分离（投手 → 系统 → 运营）

#### 影响

**迁移路径**:
- 旧代码使用 4 状态机的必须升级
- 数据库需要迁移脚本

#### 相关文档
- `STATE_MACHINE.md` v2.6 §8 粉数确认状态机
- `BUSINESS_RULES.md` v3.1 - BR-RPT-005

---

### ADR-402: 终态不可回退，仅可红冲

**编号**: ADR-402
**状态**: ✅ Accepted
**决策日期**: 2025-11
**影响范围**: 状态机设计

#### 背景

终态数据（`final_locked` / `completed`）回退会导致账本数据不一致。

#### 决策

**终态不可回退**:
- `final_locked` 后禁止修改日报数据
- `completed` 后禁止修改充值数据

**修正机制**:
- 使用 `REVERSAL` 类型分录进行红冲

#### 理由

- ✅ 数据完整性保证
- ✅ 审计合规

#### 相关文档
- `BUSINESS_RULES.md` v3.1 - BR-RPT-004
- `STATE_MACHINE.md` v2.6 终态保护规则

---

### ADR-403: 充值流程必须实现三层审批 (SOD)

**编号**: ADR-403
**状态**: ✅ Accepted
**决策日期**: 2025-10
**影响范围**: 充值模块

#### 背景

财务合规要求：充值流程需职责分离 (SOD)。

#### 决策

**充值流程三层审批**:
1. **申请**: `media_buyer` / `account_manager`
2. **复核**: `data_operator`
3. **终审**: `finance`

**SOD 规则**:
- 申请人 ≠ 复核人 ≠ 终审人

#### 理由

- ✅ 防止舞弊
- ✅ 财务合规

#### 相关文档
- `BUSINESS_RULES.md` v3.1 - BR-FIN-002

---

## 安全与权限 (ADR-500 ~ ADR-599)

---

### ADR-501: 采用 Supabase Auth，禁用本地 JWT

**编号**: ADR-501
**状态**: ✅ Accepted
**决策日期**: 2025-10
**影响范围**: 认证模块

#### 背景

自建 JWT 认证系统需要维护 Token 刷新、撤销、密钥轮换等复杂逻辑。

#### 决策

**采用 Supabase Auth**，禁用本地 JWT/bcrypt 实现。

#### 理由

- ✅ 减少安全漏洞风险
- ✅ 减少自研成本
- ✅ 内置密码加密、Token 刷新

#### 相关文档
- `AUTH_SPEC.md` v2.0 §3 认证机制

---

### ADR-502: 当前版本禁用 RLS，使用 Service 层 RBAC

**编号**: ADR-502
**状态**: ✅ Accepted
**决策日期**: 2025-10
**影响范围**: 权限控制

#### 背景

Supabase 提供 RLS (Row Level Security)，但配置复杂，调试困难。

#### 决策

**当前版本禁用 RLS**，通过 Service 层实现 RBAC。

**未来规划**:
- 当用户量超过 1000 时，重新评估启用 RLS

#### 理由

- ✅ 降低复杂度
- ✅ 便于调试

#### 相关文档
- `AUTH_SPEC.md` v2.0 §5 授权机制

---

### ADR-503: 角色固定为 5 个，禁止扩展

**编号**: ADR-503
**状态**: ✅ Accepted
**决策日期**: 2025-10
**影响范围**: 权限设计

#### 背景

角色过多导致权限矩阵复杂。

#### 决策

**固定 5 个角色**:
- `admin`, `finance`, `data_operator`, `account_manager`, `media_buyer`

**禁止扩展**:
- 不允许添加新角色（如 `super_admin`, `manager`）

#### 理由

- ✅ 权限矩阵清晰
- ✅ 降低测试复杂度

#### 相关文档
- `DATA_SCHEMA.md` v5.2 §3.1.1 users 表
- `BUSINESS_RULES.md` v3.1 - BR-AUTH-001

---

## 文档与协作 (ADR-700 ~ ADR-799)

---

### ADR-701: 采用 SoT 裁判链体系

**编号**: ADR-701
**状态**: ✅ Accepted
**决策日期**: 2025-11
**影响范围**: 文档架构

#### 背景

多文档冲突时缺乏明确裁决规则。

#### 决策

采用 **SoT 裁判链**:
```
MASTER.md → STATE_MACHINE.md → DATA_SCHEMA.md → BUSINESS_RULES.md
→ API_SOT.md → ERROR_CODES_SOT.md → AUTH_SPEC.md → LEDGER_SOT.md
```

**冲突处理**: 优先级高的文档裁决优先级低的文档。

#### 理由

- ✅ 冲突裁决规则清晰
- ✅ 降低文档维护成本

#### 相关文档
- `PROJECT_RULES.md` v3.1 §1 SoT 裁判链

---

### ADR-702: 文档分为四层架构

**编号**: ADR-702
**状态**: ✅ Accepted
**决策日期**: 2025-11
**影响范围**: 文档组织

#### 背景

文档分散，查找困难。

#### 决策

**四层文档架构**:
- Tier 1: `docs/1.overview/` - 系统架构
- Tier 2: `docs/2.sot/` - 规范真相源
- Tier 3: `docs/3.dev-guides/` - 开发指南
- Tier 4: `docs/4.appendix/` - 附录

#### 理由

- ✅ 文档层次清晰
- ✅ 便于查找

#### 相关文档
- `MASTER.md` v3.4 §文档架构

---

### ADR-703: 规范文档达到 Freeze 版本后禁止随意修改

**编号**: ADR-703
**状态**: ✅ Accepted
**决策日期**: 2025-11
**影响范围**: 文档维护

#### 背景

规范文档频繁修改导致代码与文档不一致。

#### 决策

**Freeze 规则**:
- 规范文档达到 Freeze 版本后，禁止随意修改
- 修改必须通过 RFC 流程

**当前 Freeze 版本**:
- MASTER.md v4.4 (ASDD Freeze v1.0)
- STATE_MACHINE.md v2.6 (SoT Freeze v1.0)
- DATA_SCHEMA.md v5.2
- API_SOT.md v9.3

#### 理由

- ✅ 文档稳定性
- ✅ 代码与文档一致性

#### 相关文档
- `PROJECT_RULES.md` v3.1 §13 规则总纲生效声明

---

## 变更历史

### v1.0 (2025-11-26)
- ✅ 初始版本发布
- ✅ 记录 20+ 核心架构决策
- ✅ 覆盖系统架构、数据库、API、前端、业务流程、安全、文档领域

---

## 📧 维护与反馈

**维护团队**: AI Architecture Team
**决策提议**: 通过 GitHub Issue 提交新 ADR 或修订现有 ADR
**RFC 流程**: 重大架构变更必须先提交 RFC，经架构委员会评审后形成 ADR

---

> **版权声明**: 本文档为 AI 广告代投系统的内部技术文档，仅供授权人员使用。
