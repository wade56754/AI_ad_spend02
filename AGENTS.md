# AGENTS.md

> AI 广告代投系统 - AI Coding Agent 专属指南
>
> 版本: 1.0 | 基于 [agents.md](https://agents.md) 开放格式

<!-- OPENSPEC:START -->
## OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

---

## Project Overview

这是一个 **AI 广告代投管理系统**，用于管理广告账户、日报审核、充值对账等业务流程。

**核心业务域:**
- 广告账户管理 (AdAccount)
- 日报审核流程 (DailyReport) - 8 状态机
- 充值与对账 (Topup/Reconciliation)
- 财务账本 (Ledger)

**技术栈:**
| 层 | 技术 |
|---|------|
| 后端 | FastAPI + SQLAlchemy 2.x + Pydantic v2 |
| 前端 | Next.js 14 + TanStack Query v5 + shadcn/ui |
| 认证 | Supabase Auth |
| 数据库 | PostgreSQL (via Supabase) |

---

## Setup Commands

```bash
# 后端环境
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 前端环境
cd frontend
pnpm install

# 数据库迁移
cd backend
alembic upgrade head
```

---

## Development Instructions

### 启动开发服务器

```bash
# 后端 (端口 8000)
cd backend
uvicorn main:app --reload --port 8000

# 前端 (端口 3000)
cd frontend
pnpm run dev
```

**重要:** 使用 `--reload` 模式进行开发，不要在 agent 会话中运行 `pnpm run build`。

### 项目结构

```
AI_ad_spend02/
├── backend/
│   ├── routers/      # API 路由 (thin layer)
│   ├── services/     # 业务逻辑
│   ├── models/       # SQLAlchemy 模型
│   ├── schemas/      # Pydantic 模式
│   └── core/         # 核心工具 (response, error_codes)
├── frontend/
│   └── src/
│       ├── app/          # Next.js App Router
│       ├── components/   # 通用组件
│       └── modules/      # 业务模块
├── docs/
│   ├── 1.overview/   # 系统概览
│   ├── 2.sot/        # SoT 真相源文档
│   ├── 3.dev-guides/ # 开发指南
│   └── 4.architecture/ # 架构图
└── agents/
    └── skills/       # AI 代码工厂子技能
```

### Monorepo 导航

在子目录工作时，相关配置文件位置:
- 后端依赖: `backend/requirements.txt`
- 前端依赖: `frontend/package.json`
- 数据库迁移: `backend/alembic/`

---

## Code Style Guidelines

### Python (后端)

```python
# 1. Pydantic v2 规范
from pydantic import BaseModel, ConfigDict

class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str

    # 使用 model_dump() 而非 dict()
    def to_dict(self):
        return self.model_dump()

# 2. API 响应格式 (Envelope)
from backend.core.response import success_response, error_response

# 成功
return success_response(data={"id": 1}, message="创建成功")

# 业务错误
from backend.core.error_codes import BusinessError, BusinessErrorCodes
raise BusinessError(code=BusinessErrorCodes.INVALID_STATE_TRANSITION)

# 3. SQLAlchemy 2.x 查询
from sqlalchemy import select
result = session.execute(select(User).where(User.id == user_id))
user = result.scalar_one_or_none()
```

### TypeScript (前端)

```typescript
// 1. 使用 TypeScript 严格模式
// 2. 组件使用 .tsx，工具使用 .ts
// 3. API 调用使用 apiFetch (禁止直连数据库)
import { apiFetch } from '@/lib/api';

// 4. 状态管理使用 TanStack Query
import { useQuery, useMutation } from '@tanstack/react-query';
```

---

## SoT (Source of Truth) 规范

**这是最重要的部分！** 所有开发必须遵循 SoT 文档。

### SoT 裁判链 (优先级从高到低)

```
MASTER.md v4.0                      → 架构宪法，最高优先级
BUSINESS_FLOW_MANAGEMENT.md        → 业务流程与责任模型
MVP_PHASE_DESIGN.md                → Phase 边界与页面定义
STATE_MACHINE.md v2.6              → 状态机定义
DATA_SCHEMA.md v5.2                → 数据模型
LEDGER_SOT.md v1.1                 → 账本规范（Phase 2）
BUSINESS_RULES.md v3.2             → 业务规则
API_SOT.md v9.0                    → API 契约
ERROR_CODES_SOT.md v2.1            → 错误码
AUTH_SPEC.md v2.0                  → 认证授权
```

### 核心管理目标（三权清晰）

系统的唯一目标是：**支撑老板决策，而不是替代人做判断**

- **谁对钱负责**：项目负责人申请 → 财务审核 → 老板批准
- **谁对结果负责**：项目负责人对盈亏负责，主管对投手产出负责
- **谁能纠偏**：日级主管、周级项目负责人、月级老板

### Phase 1 / Phase 2 边界

| Phase | 系统行为 | 禁止行为 |
|-------|---------|----------|
| Phase 1（照亮） | 记录事实、展示状态、提示异常 | 不允许系统自动惩罚 |
| Phase 2（问责） | 引入约束、强制审批、考核关联 | 需 Phase 1 稳定运行 2 个月后启动 |

### 日报 8 状态机 (STATE_MACHINE.md v2.6)

```
raw_submitted → trend_pending → trend_ok/trend_flagged
→ trend_resolved → final_pending → final_confirmed → final_locked
```

**禁止使用旧状态:** `draft`, `pending`, `approved` 等

### 合法角色 (仅 5 个)

```python
VALID_ROLES = [
    "admin",           # 系统管理员
    "finance",         # 财务
    "data_operator",   # 数据运营
    "account_manager", # 账户管理员
    "media_buyer"      # 广告投手
]
```

**禁止使用旧角色:** `super_admin`, `accountant`, `operator` 等

### 错误码规范

所有错误码必须来自 `docs/sot/ERROR_CODES_SOT.md`:

```python
# 正确
raise BusinessError(code="BIZ-STATE-001", message="状态转换非法")

# 错误 (禁止自定义)
raise HTTPException(status_code=400, detail="Invalid state")
```

---

## Testing Instructions

### 运行测试

```bash
# 后端单元测试
cd backend
pytest tests/ -v

# 运行特定测试
pytest tests/services/test_topup_service.py -v

# 前端测试
cd frontend
pnpm test

# 类型检查
cd frontend
pnpm run typecheck
```

### 回归测试 (PR 前必须通过)

```bash
python run_tests.py --type regression
```

### 测试失败处理

1. 阅读错误信息，定位失败的测试用例
2. 检查是否违反了 SoT 规范
3. 修复代码，确保符合 8 状态机和角色规范
4. 重新运行测试直到通过

---

## PR Guidelines

### Commit 消息格式

```
<type>(<scope>): <subject>

<body>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

**Type 类型:**
- `feat`: 新功能
- `fix`: Bug 修复
- `refactor`: 重构
- `docs`: 文档
- `test`: 测试
- `chore`: 构建/工具

### PR 前检查清单

- [ ] 代码符合 SoT 规范 (状态机、角色、错误码)
- [ ] 通过 lint 检查 (`ruff check backend/`)
- [ ] 通过类型检查 (`pnpm run typecheck`)
- [ ] 通过单元测试 (`pytest tests/ -v`)
- [ ] 通过回归测试 (`python run_tests.py --type regression`)
- [ ] 无硬编码的敏感信息

---

## Security Considerations

### 禁止行为

| ID | 禁止行为 | 正确做法 |
|----|---------|---------|
| S-001 | 硬编码 API 密钥 | 使用环境变量 |
| S-002 | 直接 SQL 拼接 | 使用 SQLAlchemy ORM |
| S-003 | 绕过认证 | 使用 Supabase Auth |
| S-004 | 直接修改 balance | 通过 ledger_entries 记录 |
| S-005 | 前端直连数据库 | 使用 apiFetch 调 BFF |

### 敏感文件

不要提交以下文件:
- `.env`, `.env.local`, `.env.production`
- `credentials.json`, `secrets.yaml`
- `*.pem`, `*.key`

---

## AI Code Factory

本项目集成了 AI 代码工厂 v3.0，提供 5 阶段代码生成流水线:

```
SEARCH → SELECT → ADAPT → ASSEMBLE → VERIFY
```

### 使用方式

```python
from agents.skills.code_factory import CodeFactory, FactoryConfig

config = FactoryConfig(
    project_dir=Path("."),
    search_sources={"local_project": True, "code_library": True},
    enable_sot_check=True,  # 启用 SoT 合规检查
)

factory = CodeFactory(config)
result = factory.run(requirement="实现用户充值 API")
```

### 代码适配规则

工厂会自动应用以下适配:
- Pydantic v1 → v2 (`class Config` → `model_config`)
- SQLAlchemy 1 → 2 (`session.query()` → `session.execute(select())`)
- 旧状态 → 8 状态机 (`draft` → `raw_submitted`)
- 旧角色 → 标准角色 (`super_admin` → `admin`)

---

## Anti-Patterns (立即拦截)

```python
# 反模式 1: 硬编码旧状态
class DailyReportStatus(str, Enum):
    DRAFT = "draft"  # ❌ 违反 8 状态机

# 反模式 2: 直接修改余额
ad_account.balance -= 100  # ❌ 违反账本规则

# 反模式 3: 自定义错误码
raise HTTPException(400, "Invalid")  # ❌ 缺少标准错误码

# 反模式 4: 使用旧 Pydantic 语法
class Config:
    orm_mode = True  # ❌ 应使用 ConfigDict

# 反模式 5: 使用旧 SQLAlchemy 查询
session.query(User).filter_by(id=1).first()  # ❌ 应使用 select()
```

---

## Quick Reference

### 常用命令

```bash
# 开发
uvicorn main:app --reload           # 后端
pnpm run dev                        # 前端

# 测试
pytest tests/ -v                    # 后端测试
pnpm test                          # 前端测试

# 检查
ruff check backend/                 # Python lint
pnpm run typecheck                 # TypeScript 检查

# 数据库
alembic upgrade head               # 应用迁移
alembic revision --autogenerate -m "desc"  # 创建迁移
```

### 文档位置

| 文档 | 路径 |
|------|------|
| SoT 文档 | `docs/sot/` |
| API 文档 | `docs/sot/API_SOT.md` |
| 状态机 | `docs/sot/STATE_MACHINE.md` |
| 错误码 | `docs/sot/ERROR_CODES_SOT.md` |
| 开发指南 | `docs/3.dev-guides/` |
| Claude 规则 | `CLAUDE.md` |

---

## OpenSpec 变更流程

对 SoT 的任何变更必须通过 OpenSpec 流程:

```bash
/openspec:proposal <name>  # 创建变更提案
/openspec:validate <id>    # 验证完整性
/openspec:apply <id>       # 实施变更
/openspec:archive <id>     # 归档部署
```

---

*最后更新: 2025-12-18 | 兼容 agents.md 开放格式*
