---
# Cursor Rules 格式 - Claude Code 项目指令
alwaysApply: true
description: "AI 广告代投系统 - Claude Code 项目指令 (自动加载)"
version: "3.2"
author: "AI Architecture Team"
lastUpdated: "2025-12-17"

# 规则分类 (六大分类体系)
categories:
  - id: "code-style"
    name: "代码风格"
    priority: 1
    rules:
      - "使用 Pydantic v2 (ConfigDict, model_dump)"
      - "API 响应使用 Envelope 格式"
      - "错误码来自 ERROR_CODES_SOT.md"

  - id: "organization"
    name: "项目组织"
    priority: 2
    rules:
      - "ASDD 4层架构: Overview → SoT → Dev-Guides → Architecture"
      - "Router → Service → Repository 分层"
      - "模块化目录结构"

  - id: "documentation"
    name: "文档标准"
    priority: 3
    rules:
      - "SoT 文档为唯一真相来源"
      - "变更必须通过 OpenSpec 流程"
      - "版本号与 Freeze Manifest 对齐"

  - id: "infrastructure"
    name: "基础设施"
    priority: 4
    rules:
      - "认证使用 Supabase Auth"
      - "数据库变更通过 Alembic"
      - "前端 HTTP 使用 apiFetch"

  - id: "constraints"
    name: "约束规则"
    priority: 5
    rules:
      - "禁止自定义错误码/状态/角色"
      - "禁止绕过账本系统"
      - "禁止直接修改 balance"

  - id: "dependencies"
    name: "依赖规范"
    priority: 6
    rules:
      - "后端: FastAPI + SQLAlchemy 2.x + Pydantic v2"
      - "前端: Next.js 14 + TanStack Query v5 + shadcn/ui"
      - "禁止引入未批准的新依赖"

# 技术栈快速参考
techStack:
  backend:
    framework: "FastAPI"
    orm: "SQLAlchemy 2.x"
    validation: "Pydantic v2"
    auth: "Supabase Auth"
  frontend:
    framework: "Next.js 14"
    query: "TanStack Query v5"
    ui: "shadcn/ui"

# SoT 裁判链
sotChain:
  - "STATE_MACHINE.md v2.6"
  - "DATA_SCHEMA.md v5.2"
  - "BUSINESS_RULES.md v3.1"
  - "API_SOT.md v9.0"
  - "ERROR_CODES_SOT.md v2.1"
  - "AUTH_SPEC.md v2.0"
  - "LEDGER_SOT.md v1.1"
---

<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

## OpenSpec Slash Commands (Validation Automation)

| Command | Description |
|---------|-------------|
| `/openspec:proposal <name>` | Create new change proposal with validation |
| `/openspec:validate <id>` | Validate change completeness and SoT compliance |
| `/openspec:apply <id>` | Implement approved change with task tracking |
| `/openspec:archive <id>` | Archive deployed change and update specs |

**Workflow**: proposal → validate → (approval) → apply → validate → archive

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# AI 广告代投系统 - Claude Code 项目指令

> **文档版本**: v3.2 (基于 ASDD Freeze v1.0 + SoT Freeze v2.6 + Cursor Rules Format)
> **强制级别**: 自动加载，所有会话生效

---

## Category 1: Code Style (代码风格)

### 1.1 API 响应格式 (Envelope)
```python
# 成功响应
return success_response(
    data={"id": 1, "status": "pending"},
    message="操作成功"
)

# 业务错误
raise BusinessError(
    code=BusinessErrorCodes.INVALID_STATE_TRANSITION,
    message="状态转换非法"
)
```

### 1.2 错误码规范
- 所有错误码来自 `ERROR_CODES_SOT.md` v2.1
- 格式: `{"code": "VAL-001", "message": "..."}`

### 1.3 Pydantic v2 规范
```python
from pydantic import BaseModel, ConfigDict

class MySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # 使用 model_dump() 而非 dict()
    def to_dict(self):
        return self.model_dump()
```

---

## Category 2: Organization (项目组织)

### 2.1 ASDD 4层架构
```
docs/1.overview/   → 系统全局视图 (MASTER.md, PROJECT.md)
docs/2.sot/        → 单一真相来源 (STATE_MACHINE, DATA_SCHEMA, API_SOT...)
docs/3.dev-guides/ → 开发指南 (API_DEVELOPMENT_FLOW, FRONTEND_RULES...)
docs/4.architecture/ → 架构视图 (C4 模型, 数据流图)
```

### 2.2 后端分层
```
backend/
├── routers/    → API 路由 (thin layer)
├── services/   → 业务逻辑
├── models/     → SQLAlchemy 模型
├── schemas/    → Pydantic 模式
└── core/       → 核心工具 (response, error_codes, dependencies)
```

### 2.3 前端模块结构
```
frontend/src/modules/{module}/
├── hooks/      → TanStack Query hooks
├── services/   → API 调用
├── types/      → TypeScript 类型
└── components/ → 模块专用组件
```

---

## Category 3: Constraints (约束规则)

### 3.1 禁止行为清单
| ID | 禁止行为 | 正确做法 |
|----|---------|---------|
| F-001 | 自定义错误码 | 使用 ERROR_CODES_SOT.md |
| F-002 | 发明新状态 | 使用 STATE_MACHINE.md v2.6 |
| F-003 | 直接修改 balance | 通过 ledger_entries 记录 |
| F-004 | 绕过 BFF 直连数据库 | 使用 apiFetch |
| F-005 | 使用旧角色名 | 仅用 5 个标准角色 |

### 3.2 合法角色 (仅 5 个)
```python
VALID_ROLES = [
    "admin",           # 系统管理员
    "finance",         # 财务
    "data_operator",   # 数据运营
    "account_manager", # 账户管理员
    "media_buyer"      # 广告投手
]
```

### 3.3 日报 8 状态机 (STATE_MACHINE.md v2.6)
```
raw_submitted → trend_pending → trend_ok/trend_flagged
→ trend_resolved → final_pending → final_confirmed → final_locked
```

---

## Category 4: Workflow (工作流程)

### 4.1 API 开发流程
```
1. 查阅 SoT 文档 (按裁判链优先级)
2. 数据库模型 + Alembic 迁移
3. Service 层 + 单元测试
4. Router 层 + API 测试
5. 集成测试 + 文档更新
```

### 4.2 SoT 变更流程 (OpenSpec)
```
创建 change proposal → 编写 spec deltas → 验证 → 审批 → 实施
```

### 4.3 回归测试 (PR 前必须通过)
```bash
python run_tests.py --type regression
```

---

## Category 5: AI Behavior (AI 行为)

### 5.1 每次开发前必做
1. 查询对应 SoT 文档 (按裁判链优先级)
2. 找到相关业务规则编号 (如 BR-RPT-001)
3. 检查现有代码是否符合规则
4. 符合 → 继续开发 | 不符合 → 先修复或提 RFC

### 5.2 职责声明
- **执行裁判规则，而非创造规则**
- 遇到未覆盖场景 → 提出 RFC，而非自行扩展
- 违规处理: PR 自动拒绝 / 代码回滚

### 5.3 反模式识别
```python
# 立即拦截以下代码:

# 反模式 1: 硬编码旧状态
class DailyReportStatus(str, Enum):
    DRAFT = "draft"  # 违反 8 状态机

# 反模式 2: 直接修改余额
ad_account.balance -= 100  # 违反账本规则

# 反模式 3: 自定义错误码
raise HTTPException(400, "Invalid")  # 缺少标准错误码
```

---

## Category 6: Dependencies (依赖规范)

### 6.1 后端依赖
- FastAPI (ASGI 框架)
- SQLAlchemy 2.x (ORM, 同步模式)
- Pydantic v2 (数据验证)
- Alembic (数据库迁移)
- Supabase Auth (认证)

### 6.2 前端依赖
- Next.js 14 (App Router)
- TanStack Query v5 (服务器状态)
- shadcn/ui + Tailwind CSS (UI)
- TypeScript (严格模式)

### 6.3 禁止依赖
- 本地 bcrypt / 自建 JWT
- Redis 队列 (RQ/Celery)
- 直接 Supabase 数据库连接 (Auth 除外)

---

## 快速参考

### SoT 裁判链
```
STATE_MACHINE.md v2.6 → DATA_SCHEMA.md v5.2 → BUSINESS_RULES.md v3.2
→ API_SOT.md v9.0 → ERROR_CODES_SOT.md v2.1 → AUTH_SPEC.md v2.0
→ LEDGER_SOT.md v1.1
```

### 详细规则
- **完整规则**: `.claude/PROJECT_RULES.md` v3.5
- **Spec-Kit 命令**: `.claude/skills/ai-ad-spec-kit/SKILL.md`
- **文档导航**: `docs/README.md`

---

**生效日期**: 2025-12-17 | **基准**: ASDD Freeze + SoT Freeze v2.6 + Cursor Rules Format

**版本历史**:
- v3.2 (2025-12-17): 整合 Cursor Rules 六大分类体系，添加 YAML frontmatter
- v3.1 (2025-11-25): 基于 ASDD Freeze v1.0 + SoT Freeze v1.0
- v3.0 (2025-11-24): 初始版本
