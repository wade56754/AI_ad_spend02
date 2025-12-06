# AI 代码工厂开发指南

> **版本**: v2.0
> **状态**: active
> **层级**: Tier-3 平台规范
> **Owner**: wade
> **创建日期**: 2025-12-06
> **Baseline**: MASTER.md v3.5, Agent Layer Freeze v1.0, SoT Freeze v2.6

---

## 目录

1. [设计哲学](#1-设计哲学)
2. [代码边界定义](#2-代码边界定义) ⭐ 核心
3. [开发流程与自动化](#3-开发流程与自动化) ⭐ 核心
4. [质量标准与上线门禁](#4-质量标准与上线门禁)
5. [系统架构](#5-系统架构)
6. [Skill 规范](#6-skill-规范)
7. [Command 与 Flow 规范](#7-command-与-flow-规范)
8. [场景示例：充值审批功能](#8-场景示例充值审批功能)
9. [失败处理与报告](#9-失败处理与报告)
10. [路线图](#10-路线图)

---

## 1. 设计哲学

### 1.1 核心理念

**AI 代码工厂** 是一套 **受控的** 自动化代码生成系统：

| 原则 | 说明 |
|------|------|
| **SoT 驱动** | 所有代码必须严格遵循 SoT 文档，AI 只能读不能改 |
| **边界清晰** | 明确可写/只读/禁区，AI 不能越界 |
| **人机协作** | 代码生成自动化，最终提交人工确认 |
| **可审计** | 每次生成都有 Plan + Report，可追溯 |

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
| `backend/core/error_codes.py` | ⚠️ 需走专门 flow，不能随意改 |

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
| `agents/skills/**` | Skill 描述文档 (非 SoT) |

### 2.2 只读区域 (AI 只能读，不能写)

**这是"法律条文"，AI 只能背书，不能改字：**

| 目录 / 文件 | 说明 |
|-------------|------|
| `docs/2.sot/MASTER_SPEC.md` | 主规范 |
| `docs/2.sot/STATE_MACHINE.md` | 状态机定义 |
| `docs/2.sot/DATA_SCHEMA.md` | 数据模型定义 |
| `docs/2.sot/LEDGER_SOT.md` | 账本规则 |
| `docs/2.sot/AUTH_SPEC.md` | 认证授权规范 |
| `docs/2.sot/BUSINESS_RULES.md` | 业务规则 |
| `docs/2.sot/ERROR_CODES_SOT.md` | 错误码定义本体 |
| `docs/2.sot/API_SOT.md` | API 规范 |
| `docs/2.sot/*_SOT.md` | 所有 SoT 文档 |

> **如果要改 SoT**：只能人工改，或开专门的 `doc-architect` 流程由人盯着改。

### 2.3 禁区 (AI 绝对不能碰)

| 类别 | 文件/目录 | 原因 |
|------|----------|------|
| **配置 & 密钥** | `.env`, `.env.*`, `supabase.json` | 安全敏感 |
| **底层模型** | `backend/models/**` | 对应 DATA_SCHEMA，需 DBA 审核 |
| **数据库迁移** | `migrations/**`, `alembic/**` | 需 DBA 审核 |
| **RLS 策略** | policy 脚本 | 安全敏感 |
| **CI/CD** | `.github/workflows/**` | 基础设施 |
| **部署脚本** | `deploy/**`, `infra/**` | 基础设施 |
| **依赖锁文件** | `package-lock.json`, `pnpm-lock.yaml` | 可读不可写 |
| **虚拟环境** | `.venv/**`, `node_modules/**` | 系统生成 |

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

## 3. 开发流程与自动化 ⭐

### 3.1 完整流程图

```
┌─────────────────────────────────────────────────────────────┐
│                    AI 代码工厂开发流程                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ① 需求输入 ──────────────────────────────────── [人工]     │
│     /agent be 实现充值审批                                   │
│              │                                               │
│              ▼                                               │
│  ② 读取 SoT + 生成 Plan ──────────────────────── [自动]     │
│     读取: STATE_MACHINE / LEDGER_SOT / AUTH_SPEC ...        │
│     产出: PLAN_xxx.md (变更清单 + 设计要点)                  │
│              │                                               │
│              ▼  (可选: --require-plan-approve 需人工确认)    │
│  ③ 生成代码 ──────────────────────────────────── [自动]     │
│     调用 BEAgent / FEAgent / TestAgent                      │
│     产出: routers/ services/ schemas/ tests/                │
│              │                                               │
│              ▼                                               │
│  ④ 自动审查 ──────────────────────────────────── [自动]     │
│     SoT 对齐检查 (状态机/账本/权限/错误码)                   │
│     静态检查 (ruff/mypy/tsc)                                │
│              │                                               │
│              ▼  发现 P0/P1?                                  │
│  ⑤ 自动修复 Loop ─────────────────────────────── [自动]     │
│     最多 2 轮: 分析失败 → 生成补丁 → 重跑测试                │
│              │                                               │
│              ▼  第 3 次还失败?                               │
│  ⑥ 跑测试 ────────────────────────────────────── [自动]     │
│     pytest: 本模块相关测试                                   │
│     可选: 全量 pytest                                        │
│              │                                               │
│              ▼  全部通过?                                    │
│  ⑦ 生成报告 ──────────────────────────────────── [自动]     │
│     IMPLEMENTATION_REPORT + TEST_FREEZE_REPORT              │
│              │                                               │
│              ▼                                               │
│  ⑧ 人工确认 + 提交 ──────────────────────────── [人工]     │
│     review diff → git commit → git push                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 各阶段详解

| 阶段 | 自动/人工 | 输入 | 输出 | 说明 |
|------|----------|------|------|------|
| ① 需求输入 | 👤 人工 | 用户命令 | 任务描述 | `/agent be xxx` 或 CLI |
| ② 读取 SoT + Plan | 🤖 自动 | SoT 文档 | `PLAN_xxx.md` | 可选人工审批 |
| ③ 生成代码 | 🤖 自动 | Plan + SoT | 代码文件 | 调用对应 Agent |
| ④ 自动审查 | 🤖 自动 | 生成的代码 | 审查报告 | SoT 对齐 + 静态检查 |
| ⑤ 自动修复 | 🤖 自动 | 失败信息 | 修复补丁 | **最多 2 轮** |
| ⑥ 跑测试 | 🤖 自动 | 代码 | 测试结果 | pytest |
| ⑦ 生成报告 | 🤖 自动 | 全部结果 | 报告文件 | 实现 + Freeze 报告 |
| ⑧ 确认提交 | 👤 人工 | diff + 报告 | git commit | 人工最终把关 |

### 3.3 自动修复策略

```
┌─────────────────────────────────────────────────────────────┐
│                    自动修复 Loop                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  触发条件:                                                   │
│  - pytest 断言失败                                          │
│  - SoT 审查发现 P0/P1                                       │
│  - 静态检查问题 (类型/lint)                                 │
│                                                              │
│  修复流程:                                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Round 1: 分析失败 → 生成补丁 → 重跑测试              │   │
│  │          (修明显 bug / 漏测)                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                    │                                         │
│                    ▼ 还失败?                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Round 2: 分析失败 → 生成补丁 → 重跑测试              │   │
│  │          (补细节或小逻辑错误)                         │   │
│  └──────────────────────────────────────────────────────┘   │
│                    │                                         │
│                    ▼ 还失败?                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 停止! 生成 FAILURE_REPORT_xxx.md                     │   │
│  │ - 当前代码状态                                        │   │
│  │ - 失败日志摘要                                        │   │
│  │ - 推测根因                                            │   │
│  │ - 建议人工介入点                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 质量标准与上线门禁

### 4.1 质量等级定义

| 等级 | 说明 | 处理 |
|------|------|------|
| **P0** | 阻塞级 | 必须修复，不能提交 |
| **P1** | 严重级 | 必须修复，或写明原因+计划 |
| **P2** | 建议级 | 可暂时保留，列表备查 |

### 4.2 上线门禁 (Release Gate)

#### 目标标准 (写在规范里)

| 检查项 | 要求 |
|--------|------|
| **本模块测试** | 100% 通过，不得有 xfail 伪装 |
| **全项目 pytest** | 不得新增失败/error |
| **SoT 合规 - P0** | 必须为 0 |
| **SoT 合规 - P1** | 默认为 0，保留需写明原因 |
| **mypy** | 改动模块必须通过 |
| **ruff/black** | 不允许新增 lint error |
| **tsc (前端)** | 必须通过编译 |
| **ESLint (前端)** | 不允许新增 error |

#### 当前执行策略 (分阶段落地)

| Phase | 强制要求 | 建议但不强制 |
|-------|---------|-------------|
| **Phase 1 (现在)** | 相关 pytest 100%<br>全局不新增失败<br>P0=0, P1=0 | mypy/ruff 对改动文件 |
| **Phase 2** | + mypy/ruff 改动模块强制<br>+ tsc/ESLint 改动模块强制 | 全项目静态检查 |
| **Phase 3** | CI 全项目: pytest + mypy + lint 全绿 | - |

### 4.3 P0 问题清单

| 问题类型 | 说明 | 检测方法 |
|---------|------|---------|
| 状态枚举不一致 | 使用了 SoT 未定义的状态 | /sot-check |
| 直接修改 balance | 绕过 ledger_entries | Grep 检查 |
| 错误码格式错误 | 未使用 ERROR_CODES_SOT 定义 | /sot-check |
| 缺少状态验证 | 状态转换未验证前置状态 | 代码审查 |
| 权限检查缺失 | 未按 AUTH_SPEC 校验 | 代码审查 |
| 账本分录错误 | 不符合 LEDGER_SOT | 代码审查 |

---

## 5. 系统架构

### 5.1 目录结构

```
AI_ad_spend02/
├── .claude/                          # Claude Code 配置层
│   ├── commands/                     # Slash 命令入口
│   │   ├── agent.md                  # /agent - 单 Agent 调用
│   │   ├── orch.md                   # /orch - 多 Agent 工作流
│   │   ├── sot-check.md              # /sot-check - SoT 合规检查
│   │   └── doc-agent.md              # /doc-agent - 文档审计
│   │
│   ├── skills/                       # Skill 定义 (Prompt 工厂)
│   │   └── ai-ad-{domain}-{func}/    # 按领域-功能命名
│   │
│   └── agents/                       # Sub-Agent 定义
│       ├── codex-loop.md             # 代码审查修复循环
│       ├── doc-architect.md          # 文档架构
│       └── doc-fixer.md              # 文档修复
│
├── agent_platform/                   # 核心框架层 (CLI/MCP 模式)
│   ├── core/                         # 协议定义
│   ├── llm/                          # LLM 客户端
│   └── cli.py                        # CLI 入口
│
├── agents/                           # 业务实现层
│   ├── agent_core/                   # Agent 实现
│   │   ├── be_agent.py               # 后端 Agent
│   │   ├── fe_agent.py               # 前端 Agent
│   │   ├── test_agent.py             # 测试 Agent
│   │   └── orchestrator_agent.py     # 编排 Agent
│   └── skills/                       # Skill 函数
│
├── docs/2.sot/                       # SoT 文档层 (只读!)
│   ├── STATE_MACHINE.md
│   ├── DATA_SCHEMA.md
│   ├── LEDGER_SOT.md
│   └── ...
│
└── backend/                          # 后端代码 (可写区)
    ├── schemas/                      # ✅ 可写
    ├── services/                     # ✅ 可写
    ├── routers/                      # ✅ 可写
    ├── tests/                        # ✅ 可写
    └── models/                       # ❌ 禁区
```

### 5.2 两种运行模式

```
┌─────────────────────────────┬───────────────────────────────────┐
│   模式 A: Claude 对话模式    │    模式 B: CLI/MCP 批处理模式      │
│         (主要)              │           (辅助)                   │
├─────────────────────────────┼───────────────────────────────────┤
│ /agent be 实现API           │  python -m agent_platform.cli ... │
│        ↓                    │           ↓                       │
│ Claude 读取 .claude/skills/ │  Python Agent 执行器              │
│        ↓                    │           ↓                       │
│ 生成代码并写入文件           │  批量生成多个文件                  │
├─────────────────────────────┼───────────────────────────────────┤
│ 不需要 LLM API Key          │ 需要 LLM API Key                  │
└─────────────────────────────┴───────────────────────────────────┘
```

---

## 6. Skill 规范

### 6.1 SKILL.md 格式

```markdown
---
name: ai-ad-be-gen-skill
version: "1.0"
status: production

sot_dependencies:
  required:
    - docs/2.sot/DATA_SCHEMA.md
    - docs/2.sot/STATE_MACHINE.md
    - docs/2.sot/API_SOT.md
  optional:
    - docs/2.sot/LEDGER_SOT.md
    - docs/2.sot/ERROR_CODES_SOT.md
---

# Skill 名称

## 1. Purpose
## 2. Input Contract
## 3. Output Contract
## 4. Constraints (必须遵守的边界)
## 5. Prompt Template
```

### 6.2 Skill 行数标准

| 状态 | 行数 | 说明 |
|------|------|------|
| ✅ 健康 | < 500 | 保持 |
| ⚠️ 警告 | 500-1000 | 建议拆分 |
| ❌ 必须拆分 | > 1000 | 立即拆分 |

---

## 7. Command 与 Flow 规范

### 7.1 Command 清单

| Command | 用途 | 示例 |
|---------|------|------|
| `/agent <type> <action>` | 单 Agent | `/agent be 实现充值审批` |
| `/orch <flow> <task>` | 多 Agent 工作流 | `/orch be_then_test 实现日报` |
| `/sot-check [path]` | SoT 合规检查 | `/sot-check backend/` |
| `/doc-agent [dir]` | 文档审计 | `/doc-agent docs/` |

### 7.2 Agent Types

| Type | Key | SoT 依赖 |
|------|-----|---------|
| Backend | `be` | STATE_MACHINE, DATA_SCHEMA, API_SOT, LEDGER_SOT, AUTH_SPEC |
| Frontend | `fe` | FRONTEND_RULES, UI_DESIGN_SYSTEM |
| Test | `test` | TESTING_STRATEGY, STATE_MACHINE |
| Doc | `doc` | 全部 SoT |
| Review | `review` | 全部 SoT |

### 7.3 预定义 Flows

| Flow ID | 步骤 | 产出 |
|---------|------|------|
| `be_only` | be-gen | Router + Service + Schema |
| `test_only` | test-gen | test_xxx.py |
| `be_then_test` | be-gen → test-gen | 后端代码 + 测试 |
| `full` | be-gen → fe-gen → test-gen | 全栈代码 |

---

## 8. 场景示例：充值审批功能

### 8.1 触发命令

```bash
/agent be 实现充值审批
```

### 8.2 读取的 SoT 文档

| SoT 文档 | 读取内容 |
|---------|---------|
| `STATE_MACHINE.md` | topups 状态机: draft → pending_approval → approved/rejected |
| `LEDGER_SOT.md` | 审批后写哪些 ledger 分录、分录类型、币种、方向 |
| `DATA_SCHEMA.md` | topups 表结构、相关的 ledger_entries / wallets 表 |
| `AUTH_SPEC.md` | 谁有权限审批 (admin/finance/data_operator) |
| `BUSINESS_RULES.md` | 审批条件、金额上限、是否需双人审批 |
| `ERROR_CODES_SOT.md` | TOPUP_001 (找不到申请)、TOPUP_002 (状态不允许) |

### 8.3 生成的文件

#### 后端代码

| 文件 | 内容 |
|------|------|
| `backend/services/topup_service.py` | `approve_topup()`, `reject_topup()` 方法 |
| `backend/routers/topups.py` | `POST /api/v1/topups/{id}/approve`<br>`POST /api/v1/topups/{id}/reject` |
| `backend/schemas/topups.py` | 审批请求体、响应模型 |

#### 测试

| 文件 | 内容 |
|------|------|
| `backend/tests/services/test_topup_service.py` | 正常审批、状态不合法拒绝、权限不足 |
| `backend/tests/api/test_topups_api.py` | API 级联测试、HTTP 状态码 |
| `backend/tests/test_state_machine_transitions.py` | 状态机路径测试 |

#### 报告

| 文件 | 内容 |
|------|------|
| `TOPUP_APPROVAL_IMPLEMENTATION_REPORT_v1.0.md` | 实现细节 + SoT 对齐结果 |
| `TOPUP_APPROVAL_TEST_FREEZE_REPORT_v1.0.md` | 测试结果 + Freeze 状态 |

### 8.4 自动运行的检查

```bash
# 1. SoT 对齐检查
/sot-check backend/services/topup_service.py
/sot-check backend/routers/topups.py

# 2. pytest 模块相关
pytest backend/tests/services/test_topup_service.py -v
pytest backend/tests/api/test_topups_api.py -v
pytest backend/tests/test_state_machine_transitions.py -k "topup" -v

# 3. 静态检查 (仅改动文件)
ruff check backend/services/topup_service.py
mypy backend/services/topup_service.py
```

### 8.5 成功后的人工步骤

```bash
# 1. Review diff
git diff

# 2. 看报告
cat TOPUP_APPROVAL_IMPLEMENTATION_REPORT_v1.0.md
cat TOPUP_APPROVAL_TEST_FREEZE_REPORT_v1.0.md

# 3. 确认无误后提交
git add .
git commit -m "feat: implement topup approval flow"
git push origin feature/topup-approval
```

---

## 9. 失败处理与报告

### 9.1 失败报告格式

```markdown
# TOPUP_APPROVAL_FAILURE_REPORT_v1.0.md

## 1. 当前代码状态
- 已生成文件列表
- 部分完成的功能

## 2. 失败日志摘要
- pytest 失败用例
- SoT 违规项
- 静态检查错误

## 3. 推测根因
- 可能的原因分析

## 4. 建议人工介入点
- 具体文件
- 具体用例
- 建议修复方向
```

### 9.2 失败后的处理流程

```
失败报告生成后:
  ↓
人工查看 FAILURE_REPORT
  ↓
选择:
  A) 手动修复 → 重新运行 /agent test
  B) 调整需求 → 重新运行 /agent be
  C) 升级 SoT → 人工修改 SoT 后重试
```

---

## 10. 路线图

### 10.1 Phase 1 (当前)

- [x] 边界定义文档化
- [x] 开发流程规范化
- [x] 质量标准明确
- [ ] 基础 Skill 实现 (be-gen, test-gen)
- [ ] 自动修复 Loop (2 轮)

### 10.2 Phase 2

- [ ] CI 集成 (GitHub Actions: pytest + ruff)
- [ ] pre-commit hooks (black/ruff)
- [ ] mypy 强制通过
- [ ] 前端 Agent (fe-gen)

### 10.3 Phase 3

- [ ] 全项目 CI 绿灯门禁
- [ ] 自动 commit 到 feature branch
- [ ] MCP 协议集成
- [ ] 多 Agent 并行

---

## 附录

### A. 术语表

| 术语 | 定义 |
|------|------|
| **SoT** | Single Source of Truth，真相源文档，AI 只读 |
| **可写区** | AI 可以自动修改的代码目录 |
| **禁区** | AI 绝对不能碰的文件 |
| **自动修复 Loop** | 失败后自动重试，最多 2 轮 |
| **上线门禁** | 代码提交前必须满足的质量标准 |

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
| v2.0 | 2025-12-06 | 完整重构：边界定义 + 开发流程 + 自动化策略 |
| v1.0 | 2025-12-01 | 初始版本 |

---

**文档控制**: Owner: wade | Baseline: MASTER.md v3.5, Agent Layer Freeze v1.0, SoT Freeze v2.6
