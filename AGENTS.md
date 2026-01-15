# AGENTS.md

> AI 广告代投系统 - AI Coding Agent 专属指南
>
> 版本: v1.2 | 基准: MASTER.md v4.9, PRD v5.1 | 基于 [agents.md](https://agents.md) 开放格式

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
| 前端 | Next.js 16 + TanStack Query v5 + shadcn/ui |
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
├── AGENTS.md              # AI Agent 主规则 (本文件)
├── CLAUDE.md              # Claude 专用（引用 AGENTS.md）
├── README.md              # 人类开发者文档
├── backend/
│   ├── routers/           # API 路由 (thin layer)
│   ├── services/          # 业务逻辑
│   ├── models/            # SQLAlchemy 模型
│   ├── schemas/           # Pydantic 模式
│   └── core/              # 核心工具 (response, error_codes)
├── frontend/
│   └── src/
│       ├── app/           # Next.js App Router
│       ├── components/    # 通用组件
│       └── features/      # 业务模块
├── docs/
│   ├── sot/               # SoT 真相源文档 (9 核心文档)
│   │   ├── MASTER.md      # 架构宪法 v4.6
│   │   ├── INDEX.md       # SoT 索引
│   │   ├── STATE_MACHINE.md
│   │   ├── DATA_SCHEMA.md
│   │   ├── API_SOT.md
│   │   ├── AUTH_SPEC.md
│   │   ├── ERROR_CODES_SOT.md
│   │   └── BUSINESS_RULES.md
│   ├── 1.overview/        # 项目概览
│   ├── 2.dev-guides/      # 开发指南
│   └── 3.architecture/    # 架构视图
└── openspec/              # OpenSpec 变更管理
    └── AGENTS.md
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

### 6.1 SoT 裁判链 (优先级从高到低)

```
MASTER.md v4.9                     → 架构宪法，最高优先级
STATE_MACHINE.md v2.9              → 状态机定义 (8 状态)
DATA_SCHEMA.md v5.11                → 数据模型 (23 表) + 账本规则 §3.4.4
API_SOT.md v9.7                    → API 契约 (50+ 端点)
ERROR_CODES_SOT.md v2.2            → 错误码注册表
BUSINESS_RULES.md v4.8             → 业务规则
AUTH_SPEC.md v2.2                  → 认证授权 (6 角色)
```

**规则**: 高层文档覆盖低层文档。遇到冲突时，先查 MASTER.md。

### 6.2 核心管理目标（三权清晰）

系统的唯一目标是：**支撑老板决策，而不是替代人做判断**

- **谁对钱负责**: 项目负责人申请 → 财务审核 → 老板批准
- **谁对结果负责**: 项目负责人对项目盈亏 + 团队产出负责
- **谁能纠偏**: 日级项目负责人、周级项目负责人、月级老板

**责任链简化 (PRD v5.1)**:
```
投手执行 → 项目负责人监督+盈亏负责 → 老板最终决策
```

### 6.3 Phase 1 / Phase 2 边界

| Phase | 系统行为 | 禁止行为 |
|-------|---------|----------|
| Phase 1（照亮） | 记录事实、展示状态、提示异常 | 不允许系统自动惩罚 |
| Phase 2（问责） | 引入约束、强制审批、考核关联 | 需 Phase 1 稳定运行 2 个月后启动 |

**Phase 1 特别说明**：
- 投手 KPI（CPL）在 Phase 1 仅用于「观察与沟通」，**不用于问责与考核**
- 系统可高亮异常，但不触发处罚逻辑
- 项目负责人使用 CPL 发现问题 → 沟通调整 → 记录过程

### 6.4 充值审批链（PRD v5.1）

```
投手申请 → 户管收集 → 财务审批 → 转账
```

- 日常充值不需要老板逐笔审批
- 老板可随时查看资金状态，可随时介入

**禁止**: F-009 禁止充值流程强制添加老板逐笔审批

### 6.5 数据 SoT 三层架构（PRD v5.1）

| 层级 | 数据来源 | 字段 | 用途 |
|------|---------|------|------|
| 行为记录层 | 投手自报 | daily_report.spend/conversions | 趋势监控（参考值） |
| 实际数据层 | 平台拉取 | ad_spend_daily.spend | 成本 SoT |
| 结算数据层 | 甲方确认 | conversions_final | 收入 SoT |

**关键约束**:
- 消耗 SoT = `ad_spend_daily.spend`
- **禁止**用 `daily_report.spend` 计费

```python
# 正确：使用平台数据计算成本
cost = sum(ad_spend_daily.spend for ad_spend_daily in period)

# 错误：使用投手日报计算成本
cost = sum(daily_report.spend for daily_report in period)  # ❌ 违反 SoT
```

### 6.6 成本分类（3 类）

| 类型 | 说明 | 分摊方式 |
|------|------|---------|
| ad_topup | 广告费充值（含手续费） | 分摊到项目 |
| ad_support | 广告配套（工具、素材） | 公司统一，**不分摊** |
| overhead | 后勤支出（工资、房租） | 公司级 |

```python
EXPENSE_CATEGORY = frozenset([
    "ad_topup",    # 广告费充值（含手续费）- 分摊到项目
    "ad_support",  # 广告配套（公司统一记账，不分摊）
    "overhead"     # 后勤支出（工资/房租等）- 公司级
])
```

**禁止**: F-011 禁止将广告配套分摊到项目

### 6.7 公司利润公式（PRD v5.1）

```python
公司利润 = 总收入 - 总支出
        = Σ项目收款 - (Σ广告费充值 + Σ广告配套 + Σ后勤支出)
```

### 6.8 押款定义（PRD v5.1）

```python
押款 = 代理商未消耗余额 = Σ历史充值 - Σ历史消耗
```

### 6.9 日报 8 状态机 (STATE_MACHINE.md v2.9)

```
raw_submitted → trend_pending → trend_ok/trend_flagged
→ trend_resolved → final_pending → final_confirmed → final_locked
```

**禁止使用旧状态:** `draft`, `pending`, `approved` 等

### 6.10 角色定义（6 角色 + 技术映射）

> **PRD v5.1 变更**：移除 supervisor 角色，其职责合并到 project_owner

#### 业务层角色（PRD v5.1 / MASTER v4.6 §2.4）

```python
BUSINESS_ROLES = {
    "ceo": "老板 - 资金安全、公司盈亏、最终决策",
    "project_owner": "项目负责人 - 项目盈亏、日报审核、资金使用效率",
    "finance": "财务 - 资金出入准确、对账",
    "pitcher": "投手 - CPL达标、日报准确",
    "account_manager": "户管 - 账户分配、充值收集",
    "admin": "管理员 - 系统配置（不参与业务）"
}
```

#### 技术层映射（数据库 CHECK 约束）

```python
ROLE_MAPPING = {
    "ceo": "admin",
    "project_owner": None,  # 通过 project_members 表判断
    "finance": "finance",
    "pitcher": "media_buyer",
    "account_manager": "account_manager",
    "admin": "admin"
}
```

| 业务角色(PRD v5.1) | 技术层角色 | 映射方式 |
|-------------------|-----------|---------|
| ceo | admin | 直接使用 |
| project_owner | (业务属性) | users.is_project_owner=true 或 project_members |
| finance | finance | 直接使用 |
| pitcher | media_buyer | 直接使用 |
| account_manager | account_manager | 直接使用 |
| admin | admin | 直接使用 |

**禁止使用旧角色:** `super_admin`, `accountant`, `operator`, `supervisor`, `data_operator`

### 6.11 错误码规范

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
python scripts/run_tests.py --type regression
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
- [ ] 通过回归测试 (`python scripts/run_tests.py --type regression`)
- [ ] 无硬编码的敏感信息

---

## Security Considerations

### 敏感文件

不要提交以下文件:
- `.env`, `.env.local`, `.env.production`
- `credentials.json`, `secrets.yaml`
- `*.pem`, `*.key`

---

## 禁止行为清单

| ID | 禁止行为 | 正确做法 | 来源 |
|----|---------|---------|------|
| F-001 | 自定义错误码 | 使用 ERROR_CODES_SOT.md | MASTER §9 |
| F-002 | 发明新状态 | 使用 STATE_MACHINE.md v2.9 | MASTER §9 |
| F-003 | 直接修改 balance | 通过 ledger_entries 记录 | MASTER §9 |
| F-004 | 绕过 BFF 直连数据库 | 使用 apiFetch | 安全规范 |
| F-005 | 硬编码 API 密钥 | 使用环境变量 | 安全规范 |
| F-006 | 直接 SQL 拼接 | 使用 SQLAlchemy ORM | 安全规范 |
| F-007 | 绕过认证 | 使用 Supabase Auth | 安全规范 |
| F-008 | 使用旧 Pydantic/SQLAlchemy 语法 | 使用 v2 语法 | 技术栈规范 |
| F-009 | 充值流程强制老板逐笔审批 | 日常充值由财务审批 | PRD v5.1 |
| F-010 | 使用已移除角色(supervisor) | 使用 6 角色定义 | PRD v5.1 |
| F-011 | 广告配套分摊到项目 | 公司统一记账 | PRD v5.1 |

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

# 反模式 6: 使用已移除角色
role = "supervisor"  # ❌ 已移除，使用 project_owner

# 反模式 7: 用投手日报计算成本
cost = daily_report.spend  # ❌ 应使用 ad_spend_daily.spend
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

| 文档 | 路径 | 版本 |
|------|------|------|
| 架构宪法 | `docs/sot/MASTER.md` | v4.9 |
| 状态机 | `docs/sot/STATE_MACHINE.md` | v2.9 |
| 数据模型 | `docs/sot/DATA_SCHEMA.md` | v5.11 |
| API 契约 | `docs/sot/API_SOT.md` | v9.7 |
| 错误码 | `docs/sot/ERROR_CODES_SOT.md` | v2.2 |
| 认证授权 | `docs/sot/AUTH_SPEC.md` | v2.2 |
| 开发指南 | `docs/guides/` | - |
| Claude 规则 | `CLAUDE.md` | - |

---

## Superpowers 技能库

本项目集成了 [obra/superpowers](https://github.com/obra/superpowers) 技能库，提供增强的 AI 编码工作流。

### 核心技能

| 技能 | 用途 | 文件位置 |
|------|------|----------|
| **test-driven-development** | TDD 红绿重构循环 | `.superpowers/skills/test-driven-development/` |
| **systematic-debugging** | 4 阶段根因分析 | `.superpowers/skills/systematic-debugging/` |
| **brainstorming** | 设计讨论和细化 | `.superpowers/skills/brainstorming/` |
| **writing-plans** | 创建详细实施计划 | `.superpowers/skills/writing-plans/` |
| **executing-plans** | 批量执行计划 | `.superpowers/skills/executing-plans/` |
| **subagent-driven-development** | 子代理驱动开发 | `.superpowers/skills/subagent-driven-development/` |

### TDD 铁律

```
没有失败的测试，就不能写生产代码
```

**Red-Green-Refactor 循环:**
1. **RED**: 写一个失败的测试
2. **验证 RED**: 确认测试因预期原因失败
3. **GREEN**: 写最小代码使测试通过
4. **验证 GREEN**: 确认所有测试通过
5. **REFACTOR**: 清理代码，保持绿灯

### 集成文档

详见: `.claude/skills/superpowers-integration.md`

---

## 版本同步

本文档基于：
- **MASTER.md v4.9**
- **PRD v5.1**

当上游文档更新时，需同步更新：
- 角色定义
- Phase 边界
- 禁止行为清单
- SoT 版本号

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

*最后更新: 2025-12-31 | 版本: v1.2 | 兼容 agents.md 开放格式*
