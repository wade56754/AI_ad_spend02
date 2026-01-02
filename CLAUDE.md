# AI广告代投管理系统

> **SoT 版本**: MASTER.md v4.9 | BUSINESS_RULES.md v5.1 | DATA_SCHEMA.md v5.10 | STATE_MACHINE.md v2.9
> **AI 模型**: Claude Opus 4.5 优化 | Cursor 兼容

---

## Claude Opus 4.5 专属配置

### 深度思考模式
当用户使用以下关键词时，启用扩展思考能力：
- `ultra think` / `深度思考` / `详细分析`
- 复杂架构设计、重构、性能优化任务

### Agent 调度策略
| Agent | 使用场景 | 并行数 |
|-------|---------|--------|
| `Explore` | 代码库探索、模式识别 | ≤3 |
| `Plan` | 架构设计、重构规划 | ≤3 |
| `claude-code-guide` | 工具使用问题 | 1 |

### Plan Mode 工作流
```
理解需求 → 设计方案 → 审核计划 → 写入计划文件 → 执行实现
    ↑ Explore Agent    ↑ Plan Agent    ↑ AskUserQuestion
```

### MCP 服务器集成

| MCP 服务器 | 用途 | 工具数 |
|-----------|------|--------|
| `taskmaster-ai` | PRD→任务管理 | 7 (core) |
| `sequential-thinking` | 结构化思考 | 1 |
| `context7` | 文档检索 | 2 |
| `playwright` | 浏览器自动化 | 20+ |
| `chrome-devtools` | 调试工具 | 15+ |

#### Task Master 工作流
```
PRD 文档 → [Task Master] parse_prd → 任务列表
    ↓
[Claude Code] TodoWrite → 任务同步
    ↓
[AI 代码工厂] /gen → 代码生成 + SoT 验证
    ↓
[Task Master] set_task_status → 状态更新
```

**核心命令**:
- `parse_prd` - 从 PRD 生成任务
- `next_task` - 获取下一个待办任务
- `expand_task` - 拆解复杂任务
- `get_tasks` - 列出所有任务

---

## 强制规则 (MANDATORY)

### 写任何代码前必须
1. **完整阅读** `memory-bank/architecture.md` - 了解项目结构
2. **完整阅读** `memory-bank/prd.md` - 了解业务规则
3. **查阅对应 SoT** - 不允许凭想象实现任何功能

### 每完成一个功能后必须
1. **更新** `memory-bank/progress.md` - 记录完成状态
2. **更新** `memory-bank/architecture.md` - 如有新文件/模块
3. **使用 TodoWrite** - 跟踪任务进度

### 推荐工作流
```
读取上下文 → 执行第 N 步 → 人工验证 → Git 提交 → 新建聊天 → 执行第 N+1 步
```

---

## Memory Bank 自动化规则

**每次对话开始**:
- 读取 `memory-bank/progress.md` 了解进度
- 读取 `memory-bank/implementation-plan.md` 了解计划
- 简要告知用户当前状态

**每完成步骤**:
- 更新 `progress.md` 记录完成状态
- 更新 `architecture.md` 记录新文件

**用户说"继续"时**:
- 读取 memory-bank，找到当前步骤，继续执行

---

## 定位
广告投放业务的"人、账户、项目、钱"管理系统，让账目清清楚楚、有据可查。

## 当前阶段
**Phase 1（照亮阶段）**：只提示、不阻断、不自动问责。老板是最终裁决人。

### Phase 1 约束
- ❌ 禁止任何自动阻断/拒绝/暂停/冻结功能
- ❌ 禁止自动惩罚机制（扣分、禁用账户等）
- ❌ 禁止强制审批流程（仅记录和提示）
- ✅ 允许：记录事实、展示状态、提示异常、高亮警告

---

## 不变量（绝对不能违反）

1. **预收款≠收入**：履约完成前是负债
2. **平台消耗不含手续费**：广告费和手续费分开核算
3. **可用资金公式**：`opening_balance + Σtopup - Σad_spend`
4. **锁定后不可改**：只能红冲（ref_id + reason）
5. **数据域隔离**：投手只看自己账户，项目负责人只看自己项目

---

## 合法角色（仅 6 个）

> **来源**: MASTER.md v4.9 §2.4
> **PRD v2.2 变更**: 移除 supervisor 角色，其职责合并到 project_owner

| 角色ID | 中文名 | 职责范围 | 系统权限 |
|--------|--------|----------|----------|
| `ceo` | 老板 | 资金安全、公司盈亏、最终决策 | 全部可见，批准充值，锁定结算 |
| `project_owner` | 项目负责人 | 项目盈亏、资金使用效率、日报审核 | 申请充值，审核日报，调配投手 |
| `finance` | 财务 | 资金出入准确、数据真实、对账 | 审核充值，更新资金表，锁定结算 |
| `pitcher` | 投手 | CPL 达标、日报准确、执行投放 | 填报日报，查看自己数据 |
| `account_manager` | 户管 | 账户分配、账户状态监控 | 管理账户分配，收集充值需求 |
| `admin` | 管理员 | 系统配置（不参与业务） | 系统设置 |

### 废弃角色（禁止使用）

| 角色 | 状态 | 替代方案 |
|------|------|---------|
| `supervisor` | ❌ 已废弃 (PRD v2.2) | 合并到 project_owner |
| `data_operator` | ❌ 已废弃 | 不在宪法中 |
| `media_buyer` | ❌ 非标准 | 使用 pitcher |

> ⚠️ **重要**: 代码中如存在 `media_buyer`、`data_operator`、`supervisor`，应修正为宪法定义的角色

---

## 核心公式

```
收入 (per_lead): revenue = conversions_final × unit_price
收入 (fee_rate): revenue = ad_spend × service_fee_rate
成本: cost = real_spend + fee
毛利: gross_profit = revenue - cost
CPL: cpl = ad_spend / conversions_final
```

---

## 技术栈约束

### 后端
- **框架**: FastAPI
- **ORM**: SQLAlchemy 2.x
- **验证**: Pydantic v2
- **数据库**: PostgreSQL (Supabase)
- **认证**: Supabase Auth + JWT

### 前端
- **框架**: Next.js 16 (App Router)
- **语言**: TypeScript (strict mode)
- **UI**: shadcn/ui + Tailwind CSS
- **HTTP**: `apiFetch` (lib/api.ts) - **禁止 fetch/axios**
- **状态**: TanStack Query v5
- **表单**: react-hook-form + zod

---

## 开发前必做

1. 读 `memory-bank/architecture.md` 了解项目结构
2. 读 `memory-bank/prd.md` 了解需求
3. 查 `docs/sot/MASTER.md` 确认规则
4. 查 `docs/sot/BR-*.md` 获取详细业务规则
5. 检查 `docs/sot/STATE_MACHINE.md` 状态机是否符合
6. 查 `docs/guides/TASK_CARDS_v2.md` 获取任务卡

---

## 任务复杂度分级

| 级别 | 类型 | 流程 | SoT查阅 |
|------|------|------|---------|
| **L1** | 快速修复 | 直接执行 | 无 |
| **L2** | 简单增强 | SoT查阅→执行 | DATA_SCHEMA, STATE_MACHINE |
| **L3** | 功能开发 | Plan Mode→执行→测试 | + API_SOT, BUSINESS_RULES |
| **L4** | 架构变更 | OpenSpec→审批→实施→回归 | 全部SoT |

> 详见: `docs/guides/TASK_COMPLEXITY.md`

---

## 常用命令

```bash
just dev              # 启动开发环境
just test             # 运行测试
just ci-check         # PR门禁
just release-check    # 上线门禁
./scripts/sot-scan.sh # SoT 5秒扫描 (防幻觉检查)
```

---

## 关键文件

### SoT 文档（真相源）
| 优先级 | 文件 | 说明 |
|--------|------|------|
| 1 | `docs/sot/MASTER.md` | 系统全局规则、角色定义 |
| 2 | `docs/sot/DATA_SCHEMA.md` | 数据库模型、字段定义 |
| 3 | `docs/sot/STATE_MACHINE.md` | 状态机规范 |
| 4 | `docs/sot/BUSINESS_RULES.md` | 业务规则索引 |
| 5 | `docs/sot/API_SOT.md` | API 规范 |
| 6 | `docs/sot/AUTH_SPEC.md` | 认证授权规范 |
| 7 | `docs/sot/ERROR_CODES.md` | 错误码定义 |

### 业务规则子模块
| 文件 | 规则数 | 说明 |
|------|--------|------|
| `docs/sot/BR-AUTH.md` | 6 | 认证授权规则 |
| `docs/sot/BR-USER.md` | 5 | 用户角色规则 |
| `docs/sot/BR-PROJ.md` | 8 | 项目管理规则 |
| `docs/sot/BR-ACCT.md` | 6 | 广告账户规则 |
| `docs/sot/BR-FIN.md` | 10 | 财务流程规则 |
| `docs/sot/BR-RPT.md` | 9 | 日报管理规则 |
| `docs/sot/BR-RECON.md` | 7 | 对账流程规则 |
| `docs/sot/BR-PROFIT.md` | 6 | 利润统计规则 |
| `docs/sot/BR-DATA.md` | 5 | 数据完整性规则 |

### Memory Bank (项目记忆库)
| 文件 | 用途 |
|------|------|
| `memory-bank/prd.md` | 需求/PRD - 做什么 |
| `memory-bank/tech-stack.md` | 技术栈 - 用什么 |
| `memory-bank/implementation-plan.md` | 实施计划 - 怎么做 |
| `memory-bank/progress.md` | 进度记录 - 做到哪了 |
| `memory-bank/architecture.md` | 架构说明 - 每个文件干什么 |

### 开发指南
- **任务卡**: `docs/guides/TASK_CARDS_v2.md`（57 个任务卡）
- **AI SOP**: `docs/guides/AI_CODING_SOP_v2.0.md`（AI 编程规范）

---

## AI 防幻觉原则

- **AH-01**: 禁止假设数据一致 - 遇到缺失标记"待确认"
- **AH-02**: 禁止自动做管理裁决 - 不生成自动拒绝/暂停代码
- **AH-03**: 禁止引入 SoT 未定义概念 - 发现缺失→停止→询问
- **AH-04**: 必须遵循 Phase 1 软性原则 - 提示+高亮+记录
- **AH-05**: 遇到歧义必须停止并询问 - 停止→列出歧义→询问

---

## 代码生成自检清单

### 生成前检查
```
□ 确认 Phase 1 (日报只用 3 状态)
□ 确认角色在 6 角色白名单内 (无 supervisor)
□ 确认 API 端点在 API_SOT.md 中存在
□ 确认使用必须的组件 (DataTable, StatusBadge)
```

### 生成后检查
```
□ 第一行是否为 'use client' (交互页面)
□ 是否使用了禁止的角色 (supervisor)
□ 是否使用了 Phase 2 日报状态
□ 是否手写了 table/fetch (禁止)
□ 错误处理是否完整 (try-catch/onError)
□ toast 通知是否完整 (成功/失败)
```

---

## 快速参考

### 日报状态 (Phase 1: 3 个)
```
raw_submitted → trend_ok → final_confirmed
```

### 充值状态 (7 个)
```
draft → pending_review → finance_approve → paid → completed
                    ↓                        ↓
                rejected                 cancelled
```

### 必须使用的组件
| 场景 | 组件 |
|------|------|
| 数据列表 | `DataTable` |
| 状态标签 | `StatusBadge` |
| 表单 | `Form` + `FormField` |
| 弹窗 | `Dialog` / `AlertDialog` |
| 通知 | `toast` (sonner) |

---

## 反模式（禁止）

```typescript
// ❌ 直接 fetch
fetch('/api/...')  // → 使用 apiGet('/api/v1/...')

// ❌ supervisor 角色
if (user.role === 'supervisor')  // → 使用 'project_owner'

// ❌ Phase 2 状态
status="trend_pending"  // → 使用 "raw_submitted"

// ❌ 手写 table
<table>...</table>  // → 使用 <DataTable />

// ❌ 缺少 'use client'
export default function Page() { useState() }  // → 第一行加 'use client'
```
