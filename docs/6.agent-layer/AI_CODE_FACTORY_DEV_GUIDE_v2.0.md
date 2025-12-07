# AI 代码工厂开发指南

> **版本**: v3.0
> **状态**: production
> **层级**: Tier-3 平台规范
> **Owner**: wade
> **更新日期**: 2025-12-07
> **Baseline**: MASTER.md v3.4, AI Code Factory v3.0, SoT Freeze v2.6

---

## 目录

**Part I: 基础规范**
1. [设计哲学](#1-设计哲学)
2. [代码边界定义](#2-代码边界定义) ⭐ 核心
3. [质量标准与上线门禁](#3-质量标准与上线门禁)

**Part II: 开发流程** ⭐ 核心
4. [后端开发流程](#4-后端开发流程业务模块)
5. [前端开发流程](#5-前端开发流程模块视角)
6. [API 开发流程](#6-api-开发流程接口契约视角)
7. [测试流程](#7-测试流程从单元到集成)
8. [文档编写流程](#8-文档编写流程sot--实现文档)

**Part III: 系统实现**
9. [SuperClaude Skill 架构](#9-superclaude-skill-架构)
10. [Skill 规范](#10-skill-规范)
11. [场景示例：充值审批功能](#11-场景示例充值审批功能)
12. [失败处理与报告](#12-失败处理与报告)
13. [路线图](#13-路线图)

---

# Part I: 基础规范

## 1. 设计哲学

### 1.1 核心理念

**AI 代码工厂** 是一套 **受控的** 自动化代码生成系统，基于 **SuperClaude Skill** 架构：

| 原则 | 说明 |
|------|------|
| **SoT 驱动** | 所有代码必须严格遵循 SoT 文档，AI 只能读不能改 |
| **边界清晰** | 明确可写/只读/禁区，AI 不能越界 |
| **人机协作** | 代码生成自动化，最终提交人工确认 |
| **可审计** | 每次生成都有 Plan + Report，可追溯 |
| **对话式调用** | 通过自然语言调用 Skill，无需编程接口 |

### 1.2 核心原则

```
┌─────────────────────────────────────────────────────────────┐
│                    AI 代码工厂核心原则                        │
├─────────────────────────────────────────────────────────────┤
│  1. SoT 是法律 → AI 只能读，不能改                           │
│  2. 实现层可写 → schemas/services/routers/tests             │
│  3. 模型层禁区 → models/migrations/密钥 绝不碰              │
│  4. 自动修复有限 → 最多 2 轮，失败就报告                     │
│  5. 提交需人工 → 代码生成自动，commit 人工确认               │
│  6. Skill 对话式 → 通过自然语言调用，无需 API               │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 流程关系总览

```
┌─────────────────────────────────────────────────────────────┐
│                    开发流程关系图                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  后端模块 = ai-ad-be-gen + ai-ad-test-gen                   │
│                                                              │
│  前端模块 = ai-ad-fe-gen + API 契约 + 联调测试              │
│                                                              │
│  全局治理 = ai-ad-spec-governor + ai-ad-doc-orchestrator    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 代码边界定义 ⭐

### 2.1 可写区域 (AI 可自动修改)

#### 后端

| 目录 / 文件 | 说明 |
|-------------|------|
| `backend/schemas/**` | Pydantic 请求/响应模型 |
| `backend/services/**` | 业务服务层逻辑 |
| `backend/routers/**` | FastAPI 路由层 |
| `backend/tests/**` | pytest 测试 (API/service/状态机) |

#### 前端

| 目录 / 文件 | 说明 |
|-------------|------|
| `frontend/src/modules/**` | 模块化页面 (Shell + hooks + components) |
| `frontend/src/lib/api/**` | API client 封装 |
| `frontend/tests/**` | 前端测试 |

#### 文档 & 工具

| 目录 / 文件 | 说明 |
|-------------|------|
| `docs/3.impl/**` | 实现报告 |
| `docs/reports/**` | Freeze 报告、测试报告 |
| `openspec/changes/**` | 变更记录 |

### 2.2 只读区域 (AI 只能读，不能写)

**这是"法律条文"，AI 只能背书，不能改字：**

| 目录 / 文件 | 说明 |
|-------------|------|
| `docs/2.sot/STATE_MACHINE.md` | 状态机定义 |
| `docs/2.sot/DATA_SCHEMA.md` | 数据模型定义 |
| `docs/2.sot/LEDGER_SOT.md` | 账本规则 |
| `docs/2.sot/AUTH_SPEC.md` | 认证授权规范 |
| `docs/2.sot/BUSINESS_RULES.md` | 业务规则 |
| `docs/2.sot/ERROR_CODES_SOT.md` | 错误码定义 |
| `docs/2.sot/API_SOT.md` | API 规范 |
| `docs/2.sot/*_SOT.md` | 所有 SoT 文档 |

### 2.3 禁区 (AI 绝对不能碰)

| 类别 | 文件/目录 | 原因 |
|------|----------|------|
| **配置 & 密钥** | `.env`, `.env.*`, `supabase.json` | 安全敏感 |
| **底层模型** | `backend/models/**` | 对应 DATA_SCHEMA，需 DBA 审核 |
| **数据库迁移** | `migrations/**`, `alembic/**` | 需 DBA 审核 |
| **RLS 策略** | policy 脚本 | 安全敏感 |
| **CI/CD** | `.github/workflows/**` | 基础设施 |
| **部署脚本** | `deploy/**`, `infra/**` | 基础设施 |

### 2.4 边界总结图

```
┌─────────────────────────────────────────────────────────────┐
│                      代码边界分层                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ╔═══════════════════════════════════════════════════════╗  │
│  ║  禁区 (FORBIDDEN)                                      ║  │
│  ║  models/ | migrations/ | .env | .github/workflows/    ║  │
│  ╚═══════════════════════════════════════════════════════╝  │
│                           │                                  │
│                           ▼                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  只读区 (READ-ONLY)                                    │  │
│  │  docs/2.sot/** - 所有 SoT 文档                         │  │
│  │  AI 读取作为生成依据，但不能修改                        │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                  │
│                           ▼                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  可写区 (WRITABLE)                                     │  │
│  │  schemas/ | services/ | routers/ | tests/             │  │
│  │  AI 可以自动生成和修改                                  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 质量标准与上线门禁

### 3.1 质量等级定义

| 等级 | 说明 | 处理 |
|------|------|------|
| **P0** | 阻塞级 | 必须修复，不能提交 |
| **P1** | 严重级 | 必须修复，或写明原因+计划 |
| **P2** | 建议级 | 可暂时保留，列表备查 |

### 3.2 上线门禁 (Release Gate)

| 检查项 | 要求 |
|--------|------|
| **本模块测试** | 100% 通过 |
| **全项目 pytest** | 不得新增失败 |
| **SoT 合规 - P0** | 必须为 0 |
| **SoT 合规 - P1** | 默认为 0 |
| **mypy** | 改动模块必须通过 |
| **ruff/black** | 不允许新增 lint error |
| **tsc (前端)** | 必须通过编译 |

### 3.3 P0 问题清单

| 问题类型 | 说明 | 检测方法 |
|---------|------|---------|
| 状态枚举不一致 | 使用了 SoT 未定义的状态 | /sot-check |
| 直接修改 balance | 绕过 ledger_entries | Grep 检查 |
| 错误码格式错误 | 未使用 ERROR_CODES_SOT 定义 | /sot-check |
| 缺少状态验证 | 状态转换未验证前置状态 | 代码审查 |
| 权限检查缺失 | 未按 AUTH_SPEC 校验 | 代码审查 |

---

# Part II: 开发流程 ⭐

## 4. 后端开发流程（业务模块）

> **目标**: 使用 SuperClaude Skill 在 SoT 约束下实现完整的后端模块

### 4.1 流程总览

```
┌─────────────────────────────────────────────────────────────┐
│                    后端开发流程 (6 步)                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ① 需求 → SoT 映射 ────────────────────────────── [人工]    │
│     明确模块/状态机/账本规则归属                              │
│              │                                               │
│              ▼                                               │
│  ② 调用 ai-ad-be-gen ────────────────────────── [对话式]   │
│     生成 Schema + Service + Router                          │
│              │                                               │
│              ▼                                               │
│  ③ 调用 ai-ad-test-gen ─────────────────────── [对话式]    │
│     生成测试用例                                             │
│              │                                               │
│              ▼                                               │
│  ④ 执行测试 & 修复 ──────────────────────────── [自动]     │
│     pytest + 手动修复                                        │
│              │                                               │
│              ▼                                               │
│  ⑤ SoT 合规检查 ─────────────────────────────── [对话式]   │
│     /sot-check 或 ai-ad-spec-governor                       │
│              │                                               │
│              ▼                                               │
│  ⑥ 人工确认提交 ─────────────────────────────── [人工]     │
│     git commit                                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Step 1: SoT 完整性扫描

**必读 SoT (只读)**：

| SoT 文档 | 关注内容 |
|---------|---------|
| `STATE_MACHINE.md` | 该模块涉及的状态机 |
| `LEDGER_SOT.md` | 账本分录规则 |
| `DATA_SCHEMA.md` | 表结构、字段约束 |
| `AUTH_SPEC.md` | 权限矩阵 |
| `BUSINESS_RULES.md` | 业务规则 |
| `ERROR_CODES_SOT.md` | 错误码定义 |

### 4.3 Step 2: 调用 ai-ad-be-gen

**调用方式**:

```
使用 ai-ad-be-gen 实现充值审批 API，
目标文件: schemas/topup.py, services/topup_service.py, routers/topups.py
```

**Skill 输出**:
- `backend/schemas/{module}.py` - Pydantic 模型
- `backend/services/{module}_service.py` - 业务逻辑
- `backend/routers/{module}.py` - API 路由

### 4.4 Step 3: 调用 ai-ad-test-gen

**调用方式**:

```
使用 ai-ad-test-gen 为 topup_service 生成单元测试
```

**Skill 输出**:
- `backend/tests/services/test_{module}_service.py`
- `backend/tests/api/test_{module}_api.py`

### 4.5 Step 4: 执行测试

```bash
# 执行相关测试
pytest backend/tests/services/test_topup_service.py -v
pytest backend/tests/api/test_topups_api.py -v
```

### 4.6 Step 5: SoT 合规检查

```
/sot-check backend/services/topup_service.py
```

或:

```
使用 ai-ad-spec-governor 检查 backend/services/topup_service.py 的 SoT 合规性
```

---

## 5. 前端开发流程（模块视角）

### 5.1 流程总览

```
┌─────────────────────────────────────────────────────────────┐
│                    前端开发流程 (4 步)                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ① 输入与澄清 ─────────────────────────────────── [人工]    │
│     业务需求 + 已有后端 API                                  │
│              │                                               │
│              ▼                                               │
│  ② 调用 ai-ad-fe-gen ────────────────────────── [对话式]   │
│     生成 PageShell + hooks + components                     │
│              │                                               │
│              ▼                                               │
│  ③ 接入真实 API ─────────────────────────────── [手动]     │
│     替换 mock → 真实请求                                     │
│              │                                               │
│              ▼                                               │
│  ④ 联调与验收 ───────────────────────────────── [人工]     │
│     本地联调 + 验收                                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 调用 ai-ad-fe-gen

**调用方式**:

```
使用 ai-ad-fe-gen 实现充值列表页面，模块: topups
```

**Skill 输出**:

```
frontend/src/modules/{module}/
├── {Module}PageShell.tsx       # 页面整体布局
├── hooks/
│   ├── use{Module}Filters.ts   # 本地筛选、分页、排序状态
│   └── use{Module}Data.ts      # 数据拉取 & 合并
├── components/
│   ├── {Module}Table.tsx       # 表格组件
│   └── {Module}Card.tsx        # 卡片组件
└── data/
    └── mock-data.ts            # Mock 数据
```

---

## 6. API 开发流程（接口契约视角）

### 6.1 流程总览

```
┌─────────────────────────────────────────────────────────────┐
│                    API 开发流程 (4 步)                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ① 确定 API 边界 & 资源 ───────────────────────── [人工]    │
│     "这是对哪个资源/视图的操作？"                            │
│              │                                               │
│              ▼                                               │
│  ② 定义 API 契约 ──────────────────────────────── [人工]    │
│     {MODULE}_API_CONTRACT_vX.Y.md                           │
│              │                                               │
│              ▼                                               │
│  ③ 调用 ai-ad-be-gen ────────────────────────── [对话式]   │
│     生成 Router + Schema                                    │
│              │                                               │
│              ▼                                               │
│  ④ 版本管理 & 兼容性 ──────────────────────────── [人工]    │
│     Breaking changes → 版本号 +1                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 API 契约文档格式

**文件**: `{MODULE}_API_CONTRACT_vX.Y.md`

```markdown
# TOPUP_API_CONTRACT_v1.0.md

## 1. 审批充值申请

### 请求
- **URL**: `POST /api/v1/topups/{id}/approve`
- **Method**: POST

### Path 参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | UUID | 是 | 充值记录 ID |

### 响应 (200 OK)
```json
{
  "id": "uuid",
  "status": "approved",
  "approved_by": "uuid",
  "approved_at": "2025-12-06T10:00:00Z"
}
```

### 错误码
| HTTP Status | Code | Message |
|-------------|------|---------|
| 400 | TOPUP_001 | 充值记录不存在 |
| 400 | TOPUP_002 | 当前状态不允许审批 |
| 403 | AUTH_500 | 无审批权限 |
```

---

## 7. 测试流程（从单元到集成）

### 7.1 流程总览

```
┌─────────────────────────────────────────────────────────────┐
│                    测试流程 (4 步)                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ① 测试范围识别 ───────────────────────────────── [人工]    │
│     这次改动影响哪些模块？                                   │
│              │                                               │
│              ▼                                               │
│  ② 调用 ai-ad-test-gen ─────────────────────── [对话式]    │
│     生成 Service / API / 状态机测试                         │
│              │                                               │
│              ▼                                               │
│  ③ 执行测试 ───────────────────────────────────── [命令]   │
│     pytest                                                  │
│              │                                               │
│              ▼                                               │
│  ④ 修复失败用例 ─────────────────────────────── [手动]     │
│     修复后重新测试                                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 调用 ai-ad-test-gen

**调用方式**:

```
使用 ai-ad-test-gen 为 topup_service 生成单元测试，覆盖:
1. 正向路径: 成功审批
2. 边界条件: 状态不允许审批
3. 权限检查: 无权限用户审批
```

### 7.3 质量门槛

| 检查项 | 要求 |
|--------|------|
| 本次改动测试 | 100% 通过 |
| 全局 pytest | 不得新增失败 |
| SoT 审计 | P0=0, P1=0 |

---

## 8. 文档编写流程（SoT & 实现文档）

### 8.1 文档分类

| 类别 | 主导者 | AI 权限 | 示例 |
|------|-------|--------|------|
| **SoT 文档** | 人工 | 只读 | STATE_MACHINE.md |
| **实现文档** | AI 可生成 | 可写 | IMPLEMENTATION_REPORT |
| **报告文档** | AI 可生成 | 可写 | TEST_FREEZE_REPORT |

### 8.2 调用 ai-ad-doc-orchestrator

**完整文档编排流程**:

```
使用 ai-ad-doc-orchestrator 生成 PROJECT.md，outline_exists = false
```

**工作流**:
```
OUTLINE_GENERATE → OUTLINE_REVIEW → OUTLINE_PATCH → OUTLINE_FREEZE
    → DW-FILL → DOC-ANALYZE → DOC-PATCH → MASTER-CHECK → FREEZE
```

---

# Part III: 系统实现

## 9. SuperClaude Skill 架构

### 9.1 架构概览

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SuperClaude Skill 架构                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Layer 1: 入口层 (Entry)                                      │   │
│  │  ┌────────────────┐  ┌────────────────┐                      │   │
│  │  │ Cursor 对话模式 │  │ Claude Code    │                      │   │
│  │  │ "使用 Skill..." │  │ 对话式调用     │                      │   │
│  │  └────────────────┘  └────────────────┘                      │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                    │                                 │
│                                    ▼                                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Layer 2: Skill 路由层 (Skill Router)                         │   │
│  │  .claude/skills/                                              │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ │   │
│  │  │ ai-ad-     │ │ ai-ad-     │ │ ai-ad-     │ │ ai-ad-doc- │ │   │
│  │  │ be-gen     │ │ fe-gen     │ │ test-gen   │ │ orchestrator│ │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘ │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                    │                                 │
│                            读取 │ 只读                              │
│                                    ▼                                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Layer 3: SoT 文档层 (Single Source of Truth)                 │   │
│  │  docs/2.sot/                                                  │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ │   │
│  │  │STATE_MACH │ │DATA_SCHEMA │ │ LEDGER_SOT │ │ AUTH_SPEC  │ │   │
│  │  │ API_SOT   │ │ERROR_CODES │ │BUSINESS_R  │ │            │ │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘ │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                    │                                 │
│                            生成 │ 写入                              │
│                                    ▼                                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Output: 产出层                                               │   │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐     │   │
│  │  │ backend/      │  │ frontend/     │  │ docs/reports/ │     │   │
│  │  │ schemas/      │  │ src/modules/  │  │ FREEZE_REPORT │     │   │
│  │  │ services/     │  │ lib/api/      │  │ IMPL_REPORT   │     │   │
│  │  │ routers/      │  │               │  │               │     │   │
│  │  │ tests/        │  │               │  │               │     │   │
│  │  └───────────────┘  └───────────────┘  └───────────────┘     │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.2 Skill 目录结构

```
.claude/
├── skills/                          # SuperClaude Skills 目录
│   ├── README.md                    # Skills 索引
│   │
│   ├── ai-ad-be-gen/               # 后端代码生成
│   │   └── SKILL.md
│   │
│   ├── ai-ad-fe-gen/               # 前端代码生成
│   │   └── SKILL.md
│   │
│   ├── ai-ad-test-gen/             # 测试代码生成
│   │   └── SKILL.md
│   │
│   ├── ai-ad-doc-orchestrator/     # 文档编排总控
│   │   └── SKILL.md
│   │
│   ├── ai-ad-doc-fixer/            # 文档审查修复
│   │   └── skill.md
│   │
│   ├── ai-project-doc-writer/      # 文档内容生成
│   │   └── skill.md
│   │
│   ├── ai-master-architect/        # 宪法级校验
│   │   └── skill.md
│   │
│   ├── ai-ad-spec-governor/        # SoT 合规治理
│   │   └── SKILL.md
│   │
│   └── prompt-engineer-skill/      # Prompt 工程辅助
│       └── SKILL.md
│
├── commands/                        # Slash Commands
│   ├── sot-check.md                # /sot-check
│   └── doc-agent.md                # /doc-agent
│
└── README.md                        # AI 代码工厂主入口
```

### 9.3 数据流图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        数据流 (Data Flow)                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  用户输入                                                            │
│     │                                                                │
│     │ "使用 ai-ad-be-gen 实现充值审批"                              │
│     ▼                                                                │
│  ┌─────────────┐    解析 Skill    ┌─────────────┐                   │
│  │ Cursor /    │ ────────────────→│ ai-ad-be-gen│                   │
│  │ Claude Code │                  │ SKILL.md    │                   │
│  └─────────────┘                  └─────────────┘                   │
│                                         │                            │
│                                         │ 读取 SoT                   │
│                                         ▼                            │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  SoT 文档层                                                    │  │
│  │  STATE_MACHINE v2.6 | DATA_SCHEMA v5.2 | API_SOT v9.0         │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                         │                            │
│                                         │ 生成代码                   │
│                                         ▼                            │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  产出文件                                                      │  │
│  │  ├── backend/schemas/topup.py                                 │  │
│  │  ├── backend/services/topup_service.py                        │  │
│  │  └── backend/routers/topups.py                                │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                         │                            │
│                                         │ 人工确认                   │
│                                         ▼                            │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  git add → git commit → git push                              │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 10. Skill 规范

### 10.1 SKILL.md 格式

```yaml
---
name: ai-ad-be-gen
version: "2.0"
status: production
layer: Skill

sot_dependencies:
  required:
    - docs/2.sot/DATA_SCHEMA.md
    - docs/2.sot/STATE_MACHINE.md
    - docs/2.sot/API_SOT.md
  optional:
    - docs/2.sot/LEDGER_SOT.md
    - docs/2.sot/ERROR_CODES_SOT.md

output_boundaries:
  writable:
    - backend/schemas/**
    - backend/services/**
    - backend/routers/**
  forbidden:
    - backend/models/**
    - migrations/**
---

# Skill 名称

## 1. Purpose
## 2. Input Contract
## 3. Output Contract
## 4. Constraints (必须遵守的边界)
## 5. Prompt Template
```

### 10.2 核心 Skills 清单

| Skill | 版本 | 功能 | SoT 依赖 |
|-------|------|------|----------|
| **ai-ad-be-gen** | v2.0 | 后端代码生成 | DATA_SCHEMA, STATE_MACHINE, API_SOT |
| **ai-ad-fe-gen** | v2.0 | 前端代码生成 | FRONTEND_RULES, UI_DESIGN_SYSTEM |
| **ai-ad-test-gen** | v1.0 | 测试代码生成 | TESTING_STRATEGY |
| **ai-ad-doc-orchestrator** | v5.3 | 文档编排 | 全部 SoT |
| **ai-ad-spec-governor** | v2.0 | SoT 合规治理 | 全部 SoT |

### 10.3 Slash Commands

| Command | 用途 | 示例 |
|---------|------|------|
| `/sot-check [path]` | SoT 合规检查 | `/sot-check backend/services/` |
| `/doc-agent [dir]` | 文档审计 | `/doc-agent docs/` |

---

## 11. 场景示例：充值审批功能

### 11.1 完整流程

```
Step 1: 确认 SoT 覆盖
├── STATE_MACHINE.md#topup
├── LEDGER_SOT.md#topup
├── DATA_SCHEMA.md#topups
└── AUTH_SPEC.md

Step 2: 调用 ai-ad-be-gen
"使用 ai-ad-be-gen 实现充值审批 API，
目标文件: schemas/topup.py, services/topup_service.py, routers/topups.py"
├── 生成 backend/schemas/topup.py
├── 生成 backend/services/topup_service.py
└── 生成 backend/routers/topups.py

Step 3: 调用 ai-ad-test-gen
"使用 ai-ad-test-gen 为 topup_service 生成单元测试"
├── 生成 backend/tests/services/test_topup_service.py
└── 生成 backend/tests/api/test_topups_api.py

Step 4: 执行测试
pytest backend/tests/services/test_topup_service.py -v
pytest backend/tests/api/test_topups_api.py -v

Step 5: SoT 合规检查
/sot-check backend/services/topup_service.py

Step 6: 人工确认提交
git add .
git commit -m "feat: implement topup approval flow"
git push
```

### 11.2 调用示例

**后端代码生成**:
```
使用 ai-ad-be-gen 实现充值审批 API，
目标文件: schemas/topup.py, services/topup_service.py, routers/topups.py

要求:
1. 遵循 STATE_MACHINE.md#topup 状态转换
2. 遵循 LEDGER_SOT.md#topup 账本分录规则
3. 遵循 AUTH_SPEC.md 权限矩阵
4. 使用 ERROR_CODES_SOT.md 定义的错误码
```

**测试代码生成**:
```
使用 ai-ad-test-gen 为 topup_service 生成单元测试，覆盖:
1. test_approve_success - 成功审批
2. test_approve_wrong_status - 状态不允许审批
3. test_approve_no_permission - 权限不足
4. test_ledger_entry_created - 账本分录创建
```

---

## 12. 失败处理与报告

### 12.1 失败场景

| 场景 | 处理方式 |
|------|---------|
| SoT 缺失 | 先补充 SoT 文档 |
| 测试失败 | 手动修复后重新运行 |
| 输出边界违规 | Skill 拒绝执行 |
| 权限不足 | 检查 AUTH_SPEC |

### 12.2 失败报告格式

```markdown
# TOPUP_APPROVAL_FAILURE_REPORT_v1.0.md

## 1. 当前代码状态
- 已生成文件列表
- 部分完成的功能

## 2. 失败日志摘要
- pytest 失败用例
- SoT 违规项

## 3. 推测根因
- 可能的原因分析

## 4. 建议人工介入点
- 具体文件
- 建议修复方向
```

---

## 13. 路线图

### 13.1 已完成 (Phase 1)

- [x] SuperClaude Skill 架构迁移
- [x] 核心 Skills 定义 (be-gen, fe-gen, test-gen)
- [x] SoT 裁判链完整
- [x] 代码边界定义

### 13.2 进行中 (Phase 2)

- [ ] Skill 执行日志标准化
- [ ] 自动修复 Loop 集成
- [ ] CI/CD 集成 (GitHub Actions)

### 13.3 计划中 (Phase 3)

- [ ] MCP 协议集成
- [ ] 多 Skill 并行执行
- [ ] 自动化测试覆盖率报告

---

## 附录

### A. 术语表

| 术语 | 定义 |
|------|------|
| **SuperClaude Skill** | Markdown 定义的 AI 能力单元，通过对话式调用 |
| **SoT** | Single Source of Truth，真相源文档，AI 只读 |
| **可写区** | AI 可以自动修改的代码目录 |
| **禁区** | AI 绝对不能碰的文件 |
| **输出边界** | Skill 可写/禁止的目录范围 |

### B. SoT 文档清单

| 文档 | 版本 | 用途 |
|------|------|------|
| STATE_MACHINE.md | v2.6 | 状态机定义 |
| DATA_SCHEMA.md | v5.2 | 数据模型 |
| API_SOT.md | v9.0 | API 规范 |
| ERROR_CODES_SOT.md | v2.1 | 错误码 |
| LEDGER_SOT.md | v1.1 | 账本规则 |
| AUTH_SPEC.md | v2.0 | 认证授权 |
| BUSINESS_RULES.md | v3.1 | 业务规则 |

### C. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v3.0 | 2025-12-07 | **架构迁移**: 从 Python Agent 迁移到纯 SuperClaude Skill 架构 |
| v2.1 | 2025-12-06 | 可观测性与安全增强 |
| v2.0 | 2025-12-06 | 完整重构 |
| v1.0 | 2025-12-01 | 初始版本 |

---

**文档控制**: Owner: wade | Baseline: MASTER.md v3.4, AI Code Factory v3.0, SoT Freeze v2.6
