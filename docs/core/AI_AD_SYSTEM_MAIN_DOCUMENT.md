# AI广告代投系统核心实现规范（SoT‑Implementation）

> **版本**: v3.x 最终版
> **更新日期**: 2025‑11‑17
> **维护团队**: 系统架构团队
> **定位**: 项目实现规则唯一事实来源（SoT-Implementation）。适用于所有人类开发者与 AI 协作者，在阅读本文件并遵循引用的 SoT 文档后方可开展工作。
> **互锁文档**
> - 数据结构 SoT → `docs/core/DATA_SCHEMA.md`
> - 状态机 SoT → `docs/core/STATE_MACHINE.md`
> - API 流程规范 → `docs/core/API_DEVELOPMENT_FLOW.md`
> - 错误码 SoT → `docs/ERROR_CODES.md`

阅读顺序：先理解本文件第 1–4 章（定位、架构、角色、业务模块），之后根据职责查阅数据/接口/流程/安全等章节。AI (Claude/Cursor/Copilot) 必须在生成任何代码前加载本文件和以上 SoT。

---

## 1. 文档定位与适用边界

1. 本文件仅描述**当前已落地**的实现规范，任何未列为“当前强制”的内容均不得视为必须实现。
2. 当前架构：`Next.js 16 (App Router)` + `FastAPI` + `PostgreSQL (Supabase 托管)` + `Supabase Auth` + `Redis 缓存（仅速率限制/会话缓存，无队列）`。
3. **SoT 分层**：
   - 字段/表/索引：只看 `DATA_SCHEMA.md`。
   - 状态机：只看 `STATE_MACHINE.md`。
   - API 过程：只看 `API_DEVELOPMENT_FLOW.md`。
   - 错误码：只看 `ERROR_CODES.md`。
4. 提交代码或使用 AI 生成方案时，若与本文件冲突，必须回退并重新生成，并说明原因。
5. 本文件同时作为 `.project-rules.md` 引用的核心规范，Code Review 以此为仲裁依据。

---

## 2. 当前系统架构

### 2.1 组件说明

- **Next.js 16 前端**
  - App Router + TypeScript 严格模式，包管理器固定 `pnpm`。
  - 所有 BFF 调用统一走 `lib/api.ts::apiFetch`，禁止直接访问 Supabase/PostgreSQL。

- **FastAPI BFF**
  - 同步 SQLAlchemy + Pydantic v2（`ConfigDict(from_attributes=True)`）。
  - Service 层统一处理业务逻辑、权限过滤、审计日志。
  - `deps/supabase_auth.py` 校验 Supabase JWT 并注入 `current_user`。
  - 所有写接口必须通过 Service 层执行事务与日志。

- **PostgreSQL (Supabase 托管)**
  - Schema 唯一来源：`DATA_SCHEMA.md`。
  - 当前**未启用**数据库级 RLS，所有权限通过 Service 层 RBAC + 查询过滤实现。
  - 历史字段（如 `data_clerk_id`）仅在物理层存在，应用层必须使用新的抽象。

- **Supabase Auth**
  - 唯一身份与密码管理方案，处理注册/登录/MFA/JWT。
  - 项目数据库中不存储 password_hash/bcrypt 字段。
  - 后端使用 Supabase JWT Secret 验证 token，并通过 `user_profiles` 获得角色等业务信息。

- **Redis（缓存用途）**
  - 用于速率限制、短期缓存、会话锁。
  - **未启用**任务队列（RQ/Celery 等），任何异步需求需另行评估。

### 2.2 架构约束

1. 禁止绕过 BFF 直接访问数据库或 Supabase API。
2. 禁止在前端代码中嵌入 Supabase Admin/Service Key。
3. 禁止自建 JWT/密码方案；所有认证流程必须调用 Supabase Auth。
4. 生产部署组件仅包含：FastAPI + PostgreSQL + Supabase Auth + Redis。
5. 配置以 `.env` / `settings.py` 中的 `DATABASE_URL`, `SUPABASE_*`, `ENABLE_*` 为准，必须使用 Secret 管理。
6. 所有环境均需运行 Alembic 迁移以确保 schema 一致。

---

## 3. 角色与权限模型

合法角色仅为：`admin`, `finance`, `data_operator`, `account_manager`, `media_buyer`。

| 角色 | 主要职责 | 数据访问范围 |
| --- | --- | --- |
| `admin` | 平台配置、审计、紧急干预 | 全量数据 |
| `finance` | 充值终审、资金监控、财务对账 | 财务相关项目/充值数据 |
| `data_operator` | 日报审核、数据校验、导入导出 | 负责项目范围内的数据 |
| `account_manager` | 项目维护、成员管理、充值初审 | 所管理项目及其账户 |
| `media_buyer` | 日报提交、充值申请、凭证上传 | 仅可操作分配账户/项目 |

**实现要求**

1. 路由层必须使用 `@require_role` 或 `get_current_user` + 明确校验来限制角色。
2. Service 层根据角色和项目/账户绑定关系过滤数据，Router 禁止直接编写 SQL 条件。
3. 历史命名兼容：数据库旧字段如 `data_clerk_id` 表示 `data_operator`，旧表名 `recharge_requests` 对应 `topup_requests`。**代码中不得再出现旧名**。
4. 权限矩阵与状态触发动作以 `STATE_MACHINE.md` 为准：
   - 日报：`media_buyer` 提交 → `data_operator` 审核。
   - 充值：`media_buyer`/`account_manager` 发起 → `data_operator` 复核 → `finance` 审批/支付。
   - 项目：`account_manager` 维护，`admin` 全局干预。
   - 对账：`finance` 主导，`data_operator` 提供数据。

---

## 4. 核心业务模块与状态流转

> 状态定义与合法转换详见 `STATE_MACHINE.md`。本节只描述角色职责与关键约束。

### 4.1 日报管理（Daily Reports）

- 目标：记录每日广告投放消耗、转化等指标，形成数据闭环。
- 关键场景：
  1. `media_buyer` 创建/更新草稿 (`draft`)。
  2. 提交后进入 `pending`，等待 `data_operator` 审核。
  3. 审核通过 → `approved`；驳回 → 回到 `draft`。
- 约束：
  - `ad_account_id + report_date` 唯一，重复提交需走更新。
  - 使用 `Decimal` 处理金额/指标，禁止浮点精度误差。
  - 导入/导出需记录操作日志并校验文件格式。
  - 示例 API 响应（成功/失败）可参考“第 6 章：API 设计”。

### 4.2 充值管理（Topup Requests）

- 状态：`draft → pending_review → finance_approve → paid → completed`，驳回/取消路径参见状态机。
- 角色分工：发起（`media_buyer/account_manager`）→ 复核（`data_operator`）→ 终审/支付（`finance`）。
- 关键字段（语义概述）：
  - `request_no`: 业务流水号，自增或按规则生成。
  - `amount`: 充值金额，`Decimal`。
  - `urgency_level`: 紧急程度 enum，用于排序。
  - `status`: 必须从枚举中取值，禁止写入自定义字符串。
- 状态校验代码示例（源自旧文档，已与现状对齐）：
  ```python
  STATE_TRANSITIONS = {
      "draft": {"pending_review"},
      "pending_review": {"finance_approve", "rejected"},
      "finance_approve": {"paid", "rejected"},
      "paid": {"completed"},
      "completed": set(),
      "rejected": {"draft"},
      "cancelled": set(),
  }

  def ensure_transition_allowed(current: str, target: str):
      allowed = STATE_TRANSITIONS.get(current, set())
      if target not in allowed:
          raise BusinessLogicError(
              f"非法状态流转：{current} → {target}",
              error_code=BusinessErrorCodes.INVALID_STATE_TRANSITION
          )
  ```
- 业务要点：
  - 每次状态变更必须写入 `topup_approval_logs`，包含操作者和备注。
  - 支付凭证上传后需通知审批链路。
  - `finance` 标记支付成功后自动生成资金流水并更新账户余额。

### 4.3 项目与广告账户管理

- 项目/账号生命周期（如 `new/testing/active/suspended/...`）详见 `STATE_MACHINE.md`。
- `account_manager` 维护成员与分配，`media_buyer` 仅能查看属于自己的项目/账户。
- 禁止删除仍有关联日报/充值/对账的数据，需先走解关联流程。

### 4.4 对账与财务

- `finance` 基于 `daily_reports`, `topup_requests`, `ledger_entries` 完成对账。
- 状态机定义异常处理流程（差异待确认、已调账等），实现时按状态机执行。
- 对账结果需同步至财务报表，并向相关角色发送通知。

---

## 5. 数据与存储规范

1. **唯一事实来源**：`DATA_SCHEMA.md`。本节不再给出完整 `CREATE TABLE`。
2. **字段引用方式**：仅用自然语言解释，如“`daily_reports.report_date` 控制唯一性”。不得在此处增删字段。
3. **命名兼容说明**：
   - 历史字段 `data_clerk_id` → `data_operator_id`。
   - 历史表 `recharge_requests` → `topup_requests`。
   - 代码与新文档中一律使用现行命名。
4. **迁移流程**：
   - 只允许通过 Alembic 迁移改变 schema。
   - PR 前必须 `alembic upgrade head` 并更新 `alembic/versions/*`。
5. **多环境一致性**：
   - `DATABASE_URL` 指向 Supabase PostgreSQL。
   - 本地/CI 若使用 Docker/Postgres，也必须同步迁移、保持结构一致。
6. **数据校验与一致性**：
   - Pydantic 模型用于输入校验，Service 层负责业务合法性。
   - 金额、数量字段使用 `Decimal` 和数据库约束（CHECK、UNIQUE）。
   - 重要字段需设定默认值和非空约束，避免产生「脏数据」。

---

## 6. API 设计与交互规范

### 6.1 BFF 边界与调用方式

- 所有前端或外部调用均通过 FastAPI `/api/v1/*`，统一 RBAC/Audit。
- 禁止前端直接访问 Supabase 数据库 API（除 Auth 模块外）。
- `lib/api.ts::apiFetch` 必须附带 JWT、写入 `request_id`、统一处理错误。

### 6.2 响应 Envelope 与错误码

- 标准响应示例（成功）：
  ```json
  {
    "success": true,
    "data": {
      "report_id": "report-20251111-001"
    },
    "message": "日报提交成功，等待审核",
    "code": "SUCCESS",
    "request_id": "req-12345",
    "timestamp": "2025-11-17T08:00:00Z"
  }
  ```
- 失败响应示例：
  ```json
  {
    "success": false,
    "error": {
      "code": "BIZ_201",
      "message": "日期不能为未来",
      "detail": {
        "field": "report_date"
      }
    },
    "request_id": "req-67890",
    "timestamp": "2025-11-17T08:01:00Z"
  }
  ```
- `code` 必须来自 `docs/ERROR_CODES.md`（示例：`AuthErrorCodes.EMAIL_ALREADY_EXISTS.code`）。
- 路由层统一调用 `core.response.success_response/error_response`。

### 6.3 常用依赖与示例

```python
from fastapi import Depends, HTTPException, status
from core.dependencies import get_current_user, require_role
from schemas.daily_reports import DailyReportCreate
from services.daily_report_service import DailyReportService

@router.post(
    "/daily-reports",
    response_model=StandardResponse[DailyReportResponse],
    summary="提交日报"
)
async def create_daily_report(
    payload: DailyReportCreate,
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(require_role(["media_buyer"]))
):
    report = service.create_report(payload, current_user)
    return success_response(data=DailyReportResponse.model_validate(report))
```

- `require_role` 接受合法角色列表；`get_current_user` 返回经过 Supabase JWT 校验的用户对象。
- 所有 Router 方法需要 `summary/description/tags` 描述，便于文档生成。

### 6.4 分页与过滤

- Query 参数统一：`page`, `page_size`, `status`, `project_id`, `start_date`, `end_date` 等。
- 响应包含 `meta.pagination`：
  ```json
  "meta": {
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 145,
      "total_pages": 8
    }
  }
  ```

### 6.5 审计与日志

- 写操作需记录 `ip_address`, `user_agent`, `performed_by`。
- 关键流程（审批、支付、删除）必须写入 `audit_logs`。
- `request_id` 贯穿前后端，便于日志关联。

---

## 7. 开发生命周期与代码结构

1. **目录职责**
   - `backend/models/*`: SQLAlchemy 模型。
   - `backend/schemas/*`: Pydantic 输入/输出。
   - `backend/services/*`: 业务逻辑、权限、事务、审计。
   - `backend/routers/*`: HTTP 路由与响应封装。
   - `frontend/app/*`: App Router 页面、标准布局。

2. **实现顺序（取自 `API_DEVELOPMENT_FLOW.md`）**
   1. 查阅 SoT 文档（本文件 + Data + State + API + Errors）与模块设计。
   2. 更新/创建数据库模型及 Alembic 迁移。
   3. 编写 Service 层及单元测试。
   4. 暴露 Router，编写前端调用。
   5. 补充集成/e2e 测试与文档，验收后合并。

3. **代码风格约束**
   - Python 使用类型注解，配合 `flake8 + mypy`。
   - 前端 TypeScript 全量开启严格模式，组件优先 `shadcn/ui`。
   - 禁止在 Router 中直接操作数据库；禁止在 Service 外部处理业务事务。
   - 所有提交需通过 lint + type-check + 相关测试。

---

## 8. 安全策略

### 8.1 当前强制措施

1. **Supabase Auth**：唯一身份来源（注册/登录/密码/多因子）。
2. **JWT 验证**：通过 `Authorization: Bearer <token>`，使用 Supabase 提供的 `JWT_SECRET` 验证。禁止自建 token。
3. **Service 层 RBAC**：所有写接口必须校验角色 + 数据范围。
4. **数据隔离**：当前不启用 PostgreSQL RLS；禁止执行 `ENABLE ROW LEVEL SECURITY`。
5. **敏感信息保护**：
   - 日志中禁止输出凭证/个人信息。
   - 支付凭证等文件必须存储在受控存储（Supabase Storage 等），并记录访问日志。
6. **配置安全**：
   - Secrets（`SUPABASE_SERVICE_ROLE_KEY`, `JWT_SECRET` 等）必须由密钥管理系统注入。
   - 禁止硬编码 API Key/密码。
7. **审计与告警**：
   - 关键操作写入 `audit_logs`，异常情况通过监控告警渠道通知值班人员。

### 8.2 未来可选增强（规划，当前未启用）

> 以下方案仅供参考，**不得**作为当下实现依据。如需落地，必须更新本 SoT 并通过评审。

- **RLS & Supabase Policy**：评估性能后逐表启用。需要重新设计迁移与应用层逻辑。
- **Redis 队列/RQ**：若出现大量异步任务（通知、账务同步）再引入。
- **本地 JWT 扩展/双 Token**：用于对接非 Supabase 系统时可评估。
- **零信任/双人审批**：对高风险操作增加额外审批步骤。
- **安全等级提升**：如数据库加密、字段脱敏、数据水印等。

---

## 9. 测试与质量要求

| 项目 | 目标要求 | 当前状态（2025‑11） | 说明 |
| --- | --- | --- | --- |
| 单元测试覆盖率 | ≥ 80%，核心模块 100% | 后端 ~55%，前端 ~40% | 优先补齐充值/日报 Service 层用例 |
| API 集成测试 | 每个 `/api/v1/*` 至少 1 条 Happy Path + 1 条权限用例 | 日报/充值部分已覆盖 | 项目/账户/对账待补齐 |
| 前端 e2e | 日报、充值、对账关键流程 | Playwright 已覆盖日报/充值 Happy Path | 异常 & 权限场景待补充 |
| 静态检查 | 后端：`flake8 + mypy`；前端：`pnpm lint && pnpm type-check` | CI 强制执行 | 禁止忽略 |
| 性能压测 | 核心 API P95 < 500ms | 仅有本地压测 | 生产前需补齐脚本与基线 |

> **要求**：提交 PR 前必须运行相关测试。若覆盖率下降，需在 PR 描述中说明原因和补齐计划。

---

## 10. AI & 工具使用规范

1. **必读文档**：在生成任何代码/配置前，必须让 AI 加载：
   - 本文件（SoT-Implementation）
   - `DATA_SCHEMA.md`
   - `STATE_MACHINE.md`
   - `API_DEVELOPMENT_FLOW.md`
   - `ERROR_CODES.md`
   - 对应模块文档（如 `docs/modules/*`、设计稿等）

2. **禁止行为**：
   - 发明新的字段/表/状态/角色/错误码。
   - 引用 bolt.new、data_clerk、强制 RLS、本地 bcrypt/JWT 等历史方案作为当前实现。
   - 绕过 Service 层直接写 SQL 或访问数据库。
   - 更改 SoT 未定义的配置或技术栈。

3. **提交前自检**：
   - [ ] 使用的角色仅为 5 个合法值。
   - [ ] 字段/表引用与 `DATA_SCHEMA.md` 一致。
   - [ ] 状态流转符合 `STATE_MACHINE.md`。
   - [ ] 错误码来自 `ERROR_CODES.md`。
   - [ ] 响应格式符合统一 Envelope。
   - [ ] Supabase Auth 调用与真实实现一致。

4. **冲突处理**：若 AI 输出与 SoT 冲突，必须立即停止、重载文档、重新生成；不得凭经验修补。

5. **工具配置**：
   - `.project-rules.md`、`CLAUDE.md`、`.cursorrules` 必须引用本文件。
   - 在 Claude/Cursor 中对话时，需要声明本文件作为最高优先级规则。

---

## 附录 A：历史 / 废弃 / 未来方案（仅供参考）

> 以下内容不代表当前实现，**不得作为开发依据**。如需重新启用，需先更新 SoT 并通过评审。

### A.1 bolt.new 在线前端流程
- 旧版曾在 bolt.new 托管原型，现已完全废弃。历史资料位于 `docs/_archive/`。

### A.2 PostgreSQL RLS 策略草案
- 旧文档中包含 `ENABLE ROW LEVEL SECURITY` 与 `CREATE POLICY` SQL 示例。当前未启用，示例仅供未来升级参考。

### A.3 Redis 队列 / RQ 方案
- 曾规划使用 Redis + RQ 处理异步任务，但尚未实现。目前 Redis 仅用于缓存/速率限制。

### A.4 本地 bcrypt / 自建 JWT
- 历史方案曾在本地存储密码哈希并生成自定义 JWT。现阶段全部替换为 Supabase Auth，禁止回退。

### A.5 旧角色/表名
- `data_clerk` → `data_operator`; `recharge_requests` → `topup_requests`。数据库层可能保留历史名称，应用层和文档只使用现行命名。

---

**执行承诺**

- 开发团队在开始任务前必须确认已阅读并理解本文件。
- Code Review 按此 SoT 执行，发现冲突需立即纠正。
- 业务/架构变更必须先更新本文件及相关 SoT，再进入开发环节。
