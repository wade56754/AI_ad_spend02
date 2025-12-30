# AI 广告代投系统 - AI 编程最佳实践

> **版本**: v3.1
> **更新日期**: 2025-12-29
> **适用工具**: Claude Code (Opus 4.5) + Cursor IDE
> **基准 SoT**: MASTER.md v4.6 | STATE_MACHINE.md v2.6 | DATA_SCHEMA.md v5.2
> **核心原则**: SoT 驱动 + 防幻觉 + 小步验证 + 模式复用
> **变更说明**: v3.1 修复角色定义、版本号、权限矩阵与 MASTER.md v4.6 对齐

---

## 目录

1. [核心理念](#第一章核心理念)
2. [工作流总览](#第二章工作流总览)
3. [Claude Opus 4.5 配置](#第三章claude-opus-45-配置)
4. [Cursor IDE 配置](#第四章cursor-ide-配置)
5. [技术栈约束](#第五章技术栈约束)
6. [目录结构规范](#第六章目录结构规范)
7. [SoT 驱动开发](#第七章sot-驱动开发)
8. [防幻觉规则](#第八章防幻觉规则)
9. [ASDD 架构](#第九章asdd-架构)
10. [OpenSpec 集成](#第十章openspec-集成)
11. [代码模式库](#第十一章代码模式库)
12. [RBAC 权限系统](#第十二章rbac-权限系统)
13. [后端开发规范](#第十三章后端开发规范)
14. [Git 工作流](#第十四章git-工作流)
15. [测试规范](#第十五章测试规范)
16. [安全规范](#第十六章安全规范)
17. [性能优化](#第十七章性能优化)
18. [质量门禁](#第十八章质量门禁)
19. [快速参考](#第十九章快速参考)
20. [提示词模板](#第二十章提示词模板)

---

## 第一章：核心理念

### 1.1 AI 是配对程序员，不是自动驾驶

```
AI 不是代码生成器的替代品，它是一个需要监督的高级助手。
- 每次生成的代码都需要人工审核
- AI 可能引入逻辑错误、安全漏洞、架构问题
- 人类负责最终决策，AI 负责执行和建议
```

### 1.2 增量迭代原则

```
读取上下文 → 执行小步骤 → 验证结果 → Git 提交 → 继续下一步
            ↑                              ↓
            └──────── 发现问题则回滚 ───────┘
```

### 1.3 SoT 优先原则

**所有技术决策必须遵循 SoT 裁判链**（详见第七章）。

### 1.4 Phase 1 约束（当前阶段）

**Phase 1（照亮阶段）**：只提示、不阻断、不自动问责。

- ❌ 禁止任何自动阻断/拒绝/暂停/冻结功能
- ❌ 禁止自动惩罚机制（扣分、禁用账户等）
- ❌ 禁止强制审批流程（仅记录和提示）
- ✅ 允许：记录事实、展示状态、提示异常、高亮警告

---

## 第二章：工作流总览

### 2.1 AI 编程标准循环

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AI 编程标准循环 (35-75 分钟)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Step 1          Step 2          Step 3          Step 4          Step 5   │
│   ─────────       ─────────       ─────────       ─────────       ─────────│
│   读取上下文       确认任务        AI 生成         验证测试        提交代码  │
│      │               │               │               │               │     │
│      ▼               ▼               ▼               ▼               ▼     │
│   ┌─────┐        ┌─────┐        ┌─────┐        ┌─────┐        ┌─────┐     │
│   │memory│  ──►  │任务卡│  ──►  │代码  │  ──►  │tsc   │  ──►  │git  │     │
│   │-bank │        │+SoT │        │生成  │        │+lint│        │commit│   │
│   └─────┘        └─────┘        └─────┘        └─────┘        └─────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 每次对话必做

| 步骤 | 动作 | 验证方式 |
|------|------|---------|
| 1 | 读取 `memory-bank/progress.md` | 知道当前进度 |
| 2 | 读取 `memory-bank/architecture.md` | 知道文件位置 |
| 3 | 确认 SoT 版本对齐 | 查阅 `quick-reference.md` |
| 4 | 查阅相关 SoT 文档 | 找到约束规则 |
| 5 | 生成代码并标注来源 | `// SoT: DOC#SECTION` |
| 6 | 运行 TypeScript/pytest 检查 | 编译通过 |
| 7 | 更新 progress.md | 记录完成状态 |

### 2.3 标准提示词模板

```markdown
阅读 /memory-bank 所有文档，
阅读 progress.md 了解之前进度，
然后继续实施计划第 N 步
```

### 2.4 推荐工作流

```
读取上下文 → 执行第 N 步 → 人工验证 → Git 提交 → 新建聊天 → 执行第 N+1 步
```

---

## 第三章：Claude Opus 4.5 配置

### 3.1 深度思考模式 (Ultra Think)

Claude Opus 4.5 支持扩展思考能力，在复杂任务时使用：

```markdown
触发关键词:
- "ultra think" / "深度思考"
- "仔细分析" / "详细规划"
- 复杂架构设计、重构、性能优化
```

**最佳实践**：
```
用户: "帮我重构这个模块 ultra think"

Claude 响应模式:
1. 首先读取所有相关文件
2. 分析现有架构和依赖关系
3. 识别问题点和改进空间
4. 提出多个方案并比较
5. 选择最优方案并详细规划
6. 分步骤执行，每步验证
```

### 3.2 Plan Mode 工作流

```
┌─────────────────────────────────────────────────────────────┐
│                    Plan Mode 流程                           │
├─────────────────────────────────────────────────────────────┤
│  Phase 1: 理解需求                                          │
│  ├── 启动 Explore Agent 探索代码库                          │
│  ├── 读取相关 SoT 文档 (按裁判链优先级)                      │
│  └── 使用 AskUserQuestion 澄清歧义                          │
│                                                             │
│  Phase 2: 设计方案                                          │
│  ├── 启动 Plan Agent 设计实现                               │
│  ├── 识别关键文件和依赖                                     │
│  └── 考虑边界情况和风险                                     │
│                                                             │
│  Phase 3: 审核计划                                          │
│  ├── 读取关键文件验证可行性                                 │
│  ├── 确保符合 SoT 规范                                      │
│  └── 与用户确认最终方案                                     │
│                                                             │
│  Phase 4: 写入计划文件                                      │
│  └── 保存到 ~/.claude/plans/                                │
│                                                             │
│  Phase 5: 退出计划模式，开始执行                            │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Agent 调度策略

| Agent 类型 | 使用场景 | 并行数 |
|-----------|---------|--------|
| `Explore` | 代码库探索、模式识别 | ≤3 |
| `Plan` | 架构设计、重构规划 | ≤3 |
| `claude-code-guide` | Claude Code 使用问题 | 1 |
| `general-purpose` | 复杂多步任务 | 根据需要 |

### 3.4 Memory Bank 自动化

**每次对话开始**：
```markdown
1. 读取 memory-bank/progress.md 了解进度
2. 读取 memory-bank/implementation-plan.md 了解计划
3. 简要告知用户当前状态
```

**每完成步骤**：
```markdown
1. 更新 progress.md 记录完成状态
2. 更新 architecture.md 记录新文件
3. 使用 TodoWrite 跟踪任务进度
```

---

## 第四章：Cursor IDE 配置

### 4.1 .mdc 规则格式

`.mdc` 格式支持 YAML frontmatter，可同时兼容 Claude Code 和 Cursor：

```yaml
# .cursor/rules/frontend-react.mdc
---
description: "React/Next.js 前端开发规范"
globs: ["**/*.tsx", "**/*.ts", "src/**/*"]
alwaysApply: true
---

## 组件规范
- 使用 shadcn/ui 组件库
- 禁止手写 <button>/<input>/<table>
- 使用 cn() 合并 Tailwind 类名

## 数据获取
- 优先使用 Server Components
- 客户端状态使用 TanStack Query
- API 调用通过 lib/api.ts

## 类型安全
- 启用 TypeScript strict mode
- 禁止使用 any 类型
- Props 必须定义接口
```

### 4.2 多规则文件组织

```
.cursor/
├── rules/
│   ├── global.mdc           # 全局规则
│   ├── frontend-react.mdc   # 前端 React 规则
│   ├── frontend-api.mdc     # 前端 API 调用规则
│   ├── backend-fastapi.mdc  # 后端 FastAPI 规则
│   ├── backend-db.mdc       # 数据库规则
│   ├── testing.mdc          # 测试规则
│   └── git-workflow.mdc     # Git 工作流规则
```

### 4.3 Cursor Agent 配置

```yaml
# .cursor/rules/agents.mdc
---
description: "Cursor Agent 配置"
alwaysApply: true
---

## Code Review Agent
触发: 完成功能开发后
职责:
- 检查代码风格一致性
- 验证类型安全
- 识别潜在 bug
- 检查是否符合 SoT

## Security Agent
触发: 安全敏感代码
职责:
- 检查输入验证
- 识别 XSS/CSRF 风险
- 审核认证逻辑
- 检查敏感数据处理
```

---

## 第五章：技术栈约束

### 5.1 技术栈白名单（不可变更）

```typescript
const TECH_STACK = {
  // ========== 前端 ==========
  frontend: {
    framework: "Next.js 15 (App Router)",  // v3.1 修正: 15 而非 16
    language: "TypeScript 5.6+ (strict: true)",
    ui: "shadcn/ui + Tailwind CSS",
    icons: "lucide-react",
    charts: "recharts",
    theme: "next-themes",
    toast: "sonner",
    serverState: "TanStack Query v5",
    urlState: "nuqs (推荐) / useSearchParams",
    localState: "useState / useReducer",
    form: "react-hook-form",
    validation: "zod",
    http: "apiFetch (@/lib/api.ts)",
    auth: "Supabase Auth",
  },

  // ========== 后端 ==========
  backend: {
    framework: "FastAPI",
    orm: "SQLAlchemy 2.x",
    validation: "Pydantic v2",
    database: "PostgreSQL (Supabase)",
    auth: "Supabase Auth + JWT",
  },
} as const;
```

### 5.2 禁止使用的技术

| 禁止项 | 原因 | 替代方案 |
|--------|------|---------|
| `fetch()` 直接调用 | 无统一错误处理 | `apiGet/apiPost` |
| `axios` | 非标准依赖 | `apiFetch` |
| `supabase.from()` | 绕过 API 层 | 后端 API |
| `Redux` | 过度复杂 | TanStack Query |
| `styled-components` | 与 Tailwind 冲突 | Tailwind CSS |
| 手写 HTML 标签 | 无设计一致性 | shadcn/ui |
| `any` 类型 | 类型不安全 | 具体类型定义 |

---

## 第六章：目录结构规范

### 6.1 完整目录结构

```
project/
├── frontend/src/
│   ├── app/                          # Next.js App Router (薄壳层)
│   │   ├── (auth)/                   # 认证路由组
│   │   │   ├── login/page.tsx
│   │   │   └── layout.tsx
│   │   ├── (dashboard)/              # 仪表盘路由组
│   │   │   ├── page.tsx              # 首页 → 驾驶舱
│   │   │   ├── projects/page.tsx
│   │   │   ├── daily-reports/page.tsx
│   │   │   ├── finance/page.tsx
│   │   │   └── layout.tsx
│   │   ├── layout.tsx                # 根布局
│   │   ├── providers.tsx             # 全局 Providers
│   │   └── globals.css
│   │
│   ├── features/                     # 功能模块 (核心)
│   │   └── {module}/
│   │       ├── components/           # 业务组件
│   │       │   ├── {Module}Page.tsx
│   │       │   ├── {Module}Table.tsx
│   │       │   ├── {Module}Dialog.tsx
│   │       │   ├── columns.tsx
│   │       │   └── index.ts
│   │       ├── hooks/                # React Query hooks
│   │       │   ├── use{Module}s.ts
│   │       │   ├── useCreate{Module}.ts
│   │       │   └── index.ts
│   │       ├── services/             # API 调用
│   │       │   └── {module}Api.ts
│   │       ├── types/                # TypeScript 类型
│   │       │   └── {module}.types.ts
│   │       ├── utils/                # 工具函数 (可选)
│   │       ├── constants/            # 常量 (可选)
│   │       └── index.ts              # 模块导出
│   │
│   ├── components/
│   │   ├── ui/                       # shadcn/ui 组件 (54+)
│   │   ├── layout/                   # 布局组件
│   │   └── shared/                   # 共享业务组件
│   │
│   ├── config/                       # 配置文件
│   │   └── nav-config.ts             # 导航 + RBAC 配置
│   │
│   ├── hooks/                        # 全局 Hooks
│   ├── lib/                          # 工具库
│   │   ├── api.ts                    # API 客户端 (核心)
│   │   ├── utils.ts                  # cn() 等工具
│   │   └── format.ts                 # 格式化工具
│   │
│   └── types/                        # 全局类型
│
├── backend/
│   ├── main.py                       # FastAPI 入口
│   ├── core/                         # 核心模块
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── responses.py
│   │   └── exceptions.py
│   ├── models/                       # SQLAlchemy 模型
│   ├── schemas/                      # Pydantic schemas
│   ├── services/                     # 业务逻辑层
│   ├── routers/                      # API 路由
│   └── tests/                        # 测试
│
├── docs/
│   ├── sot/                          # 真相源文档
│   └── guides/                       # 开发指南
│
└── memory-bank/                      # 项目记忆库
    ├── progress.md
    ├── architecture.md
    ├── implementation-plan.md
    └── game-design-document.md
```

### 6.2 薄壳页面模式

```typescript
// app/(dashboard)/daily-reports/page.tsx
// 页面文件只做路由映射，实际组件在 features 中

import { DailyReportsPage } from '@/features/daily-reports';

export default function Page() {
  return <DailyReportsPage />;
}

export const metadata = {
  title: '日报管理',
};
```

---

## 第七章：SoT 驱动开发

### 7.1 SoT 裁判链

> **v3.1 修正**: 与 CLAUDE.md 裁判链对齐

```
优先级顺序 (高 → 低):

MASTER.md v4.6           ← 系统宪法、架构基准
    ↓
BUSINESS_FLOW_MANAGEMENT.md  ← 业务流程与责任模型
    ↓
MVP_PHASE_DESIGN.md      ← Phase 边界与页面定义
    ↓
STATE_MACHINE.md v2.6    ← 状态定义（禁止在其他文档重复）
    ↓
DATA_SCHEMA.md v5.2      ← 数据模型、字段类型
    ↓
LEDGER_SOT.md v1.1       ← 账本规则（Phase 2 完整启用）
    ↓
BUSINESS_RULES.md v3.2   ← 业务规则（BR-* 编号具有法律效力）
    ↓
API_SOT.md v9.0          ← API 规范、端点定义
    ↓
ERROR_CODES_SOT.md v2.1  ← 错误码定义（禁止自定义）
    ↓
AUTH_SPEC.md v2.0        ← 认证授权、RLS 策略
```

**裁判规则**: 上游文档优先级高于下游，冲突时以上游为准。

### 7.2 开发前必查 SoT

| 开发场景 | 必查文档 | 查询内容 |
|----------|---------|---------|
| 显示状态标签 | STATE_MACHINE.md | 状态枚举值、颜色定义 |
| 权限控制 | AUTH_SPEC.md + MASTER.md §2.4 | 6 角色定义 |
| API 调用 | API_SOT.md | 端点路径、请求/响应格式 |
| 表单字段 | DATA_SCHEMA.md | 字段类型、必填项 |
| 错误提示 | ERROR_CODES_SOT.md | 错误码、提示文案 |
| 金额显示 | BUSINESS_RULES.md | 金额格式化规则 |
| 财务操作 | LEDGER_SOT.md | 账本记账规则 |

### 7.3 代码来源标注规范

```typescript
// ========== 类型定义 ==========

// SoT: STATE_MACHINE.md v2.6 §2
type DailyReportStatus =
  | 'raw_submitted'
  | 'trend_pending'
  | 'trend_ok'
  | 'trend_flagged'
  | 'trend_resolved'
  | 'final_pending'
  | 'final_confirmed'
  | 'final_locked';

// SoT: MASTER.md v4.6 §2.4 + §INV-007
// 业务层角色 (PRD 层面)
type BusinessRole = 'ceo' | 'project_owner' | 'finance' | 'pitcher' | 'account_manager' | 'admin';

// 技术层角色 (数据库 CHECK 约束)
type TechRole = 'admin' | 'finance' | 'media_buyer' | 'account_manager';

// ========== 业务逻辑 ==========

// SoT: BUSINESS_RULES.md#BR-RPT-001
function validateReportDate(date: Date): boolean {
  // 日报日期不能是未来
  return date <= new Date();
}

// SoT: BUSINESS_RULES.md#BR-FIN-003
function formatMoney(amount: number): string {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
  }).format(amount);
}
```

---

## 第八章：防幻觉规则

### 8.1 五大防幻觉原则

| 原则 | 标题 | 规则 | 级别 |
|------|------|------|------|
| **AH-01** | 禁止假设数据一致 | 遇到缺失标记"待确认"，不自动填充 | BLOCKING |
| **AH-02** | 禁止自动做管理裁决 | 不生成自动拒绝/暂停/冻结代码 | BLOCKING |
| **AH-03** | 禁止引入 SoT 未定义概念 | 发现缺失 → 停止 → 询问 | BLOCKING |
| **AH-04** | 必须遵循 Phase 1 原则 | 仅提示+高亮+记录，不阻断 | WARNING |
| **AH-05** | 遇到歧义必须停止并询问 | 列出歧义点 → 询问用户 | BLOCKING |

### 8.2 禁止行为清单

> **v3.1 修正**: 角色禁止清单与 MASTER.md v4.6 §2.4 对齐

```typescript
// ❌ F-001: 自创状态值
type Status = 'pending' | 'draft';  // 不在 STATE_MACHINE.md 中

// ✅ 正确: 使用 SoT 定义的状态
// SoT: STATE_MACHINE.md v2.6 §2
type Status = 'raw_submitted' | 'trend_ok' | 'final_confirmed';


// ❌ F-002: 使用废弃/错误角色
if (user.role === 'supervisor') { ... }     // 已废弃 (PRD v2.2)
if (user.role === 'data_operator') { ... }  // 非 6 角色白名单
if (user.role === 'data_clerk') { ... }     // 已废弃

// ✅ 正确: 使用 6 业务角色或 4 技术层角色
// SoT: MASTER.md v4.6 §2.4 + §INV-007
// 业务层判断
if (businessRole === 'pitcher') { ... }     // 投手
if (businessRole === 'project_owner') { ... } // 项目负责人

// 技术层判断 (数据库角色)
if (user.role === 'media_buyer') { ... }    // pitcher 的技术映射
if (user.role === 'finance') { ... }        // 财务


// ❌ F-003: 自动阻断 (违反 Phase 1)
if (overBudget) {
  toast.error('超预算，操作被拒绝');
  return;
}

// ✅ 正确: Phase 1 只提示不阻断
if (overBudget) {
  toast.warning('提示：已超预算 30%');
  // 继续执行，不阻断
}


// ❌ F-004: 硬编码错误消息
toast.error('操作失败，请重试');

// ✅ 正确: 使用 SoT 错误码
// SoT: ERROR_CODES_SOT.md v2.1
toast.error(getErrorMessage(error.code));


// ❌ F-005: 直接 fetch
fetch('/api/...')

// ✅ 正确: 使用 apiFetch
apiGet('/api/v1/...')
```

### 8.3 5 秒扫描检查

> **v3.1 修正**: 废弃角色列表更新

```bash
# 1. 废弃角色检查 (必须无结果)
grep -r "supervisor" frontend/src/
grep -r "data_operator" frontend/src/
grep -r "data_clerk" frontend/src/

# 2. 直接 fetch 检查 (必须无结果，排除 lib/api.ts)
grep -r "fetch\(" frontend/src/ --include="*.ts" --include="*.tsx" | grep -v "lib/api"

# 3. 手写 HTML 检查
grep -rE "<button|<input|<select|<table" frontend/src/ --include="*.tsx"

# ⚠️ 以下角色是合法的，不要标记为违规:
# ✅ 业务层: ceo, project_owner, finance, pitcher, account_manager, admin
# ✅ 技术层: admin, finance, media_buyer, account_manager
```

---

## 第九章：ASDD 架构

### 9.1 架构概述

**ASDD (AI-Spec-Driven Development)** 是本项目的文档治理框架：

```
docs/1.overview/     (系统全局视图 - Freeze v1.0)
    ↓ 引用
docs/sot/           (单一真相来源 - Freeze v2.6)
    ↓ 引用
docs/3.dev-guides/  (开发指南 - Freeze v2.1)
    ↓ 引用
docs/4.architecture/ (架构视图 - Freeze v1.0)
```

### 9.2 Freeze Manifest 路径

| Layer | Freeze Manifest | 路径 |
|-------|-----------------|------|
| **Overview** | FREEZE_MANIFEST_v1.0.md | `docs/1.overview/FREEZE_MANIFEST_v1.0.md` |
| **SoT** | SOT_FREEZE_MANIFEST_v2.6.md | `docs/sot/SOT_FREEZE_MANIFEST_v2.6.md` |
| **Dev-Guides** | DEV_GUIDES_FREEZE_MANIFEST_v2.1.md | `docs/3.dev-guides/DEV_GUIDES_FREEZE_MANIFEST_v2.1.md` |
| **Architecture** | ARCHITECTURE_FREEZE_MANIFEST_v1.0.md | `docs/4.architecture/ARCHITECTURE_FREEZE_MANIFEST_v1.0.md` |

### 9.3 代码生成合规性检查

**所有代码生成前必须执行**:

```markdown
□ SoT/Dev-Guides/Architecture 对齐验证
  - 查询 SoT Layer 对应文档
  - 查询 Dev-Guides Layer 对应文档
  - 查询 Architecture Layer 对应文档
  - 确保三层定义一致，无冲突

□ Freeze 状态验证
  - 检查文档是否处于 Freeze 状态
  - 禁止修改已冻结文档 (需先提交 RFC 解冻)
  - 禁止引用未冻结文档作为实现依据

□ 版本对齐验证
  - 确保引用的 SoT 版本号与 Freeze Manifest 一致
  - 例: STATE_MACHINE.md 必须引用 v2.6
  - 例: API_SOT.md 必须引用 v9.0
```

---

## 第十章：OpenSpec 集成

### 10.1 OpenSpec 唯一变更通道

**从 v3.3 起，所有 SoT 变更必须通过 OpenSpec 流程**：

```
openspec/changes/<change-id>/
├── proposal.md        # 变更提案
├── tasks.md           # 实施清单
├── design.md          # 技术设计（可选）
└── specs/             # Spec deltas
    └── <capability>/
        └── spec.md    # ADDED/MODIFIED/REMOVED
```

### 10.2 必须走 OpenSpec 的场景

| 变更类型 | 示例 | 相关 SoT | 必须走 OpenSpec |
|---------|------|----------|-----------------|
| 状态机修改 | 新增 `trend_review` 状态 | STATE_MACHINE.md | ✅ 强制 |
| 错误码变更 | 新增 `BIZ-010` | ERROR_CODES_SOT.md | ✅ 强制 |
| API 契约变更 | 新增 `/api/v1/transfers` | API_SOT.md | ✅ 强制 |
| 数据库结构变更 | 新增 `audit_logs` 表 | DATA_SCHEMA.md | ✅ 强制 |
| 业务规则变更 | 新增 BR-LED-005 | BUSINESS_RULES.md | ✅ 强制 |
| Bug 修复 | 恢复既有行为 | - | ❌ 可跳过 |
| 文档 typo | 拼写修正 | - | ❌ 可跳过 |

### 10.3 OpenSpec 检查清单

**每次涉及 SoT 变更前**：

```markdown
□ 是否已创建 OpenSpec change？
  change-id: ____________ → openspec/changes/<id>/ 存在: ✅/❌

□ 是否已编写 spec deltas？
  检查: openspec/changes/<id>/specs/*/spec.md 存在: ✅/❌

□ 是否通过验证？
  运行: openspec validate <id> --strict → 结果: ✅/❌

□ 是否已获得审批？
  proposal.md 状态: ✅ Approved / ❌ Pending
```

### 10.4 禁止操作

1. ❌ **直接编辑 openspec/specs/** - 该目录仅由 `openspec archive` 更新
2. ❌ **无 change-id 的 SoT 修改** - 所有 SoT 变更必须关联 change-id
3. ❌ **未审批即实施** - proposal.md 未获批准前不得开始编码

---

## 第十一章：代码模式库

### 11.1 Query Hook 模式

```typescript
// features/{module}/hooks/use{Module}s.ts
import { useQuery } from '@tanstack/react-query';
import { get{Module}s } from '../services/{module}Api';
import type { {Module}ListParams } from '../types';

export function use{Module}s(params: {Module}ListParams = {}) {
  return useQuery({
    queryKey: ['{module}s', params],
    queryFn: () => get{Module}s(params),
    staleTime: 2 * 60 * 1000,  // 2 分钟新鲜期
  });
}

// 单条查询
export function use{Module}(id: number | undefined) {
  return useQuery({
    queryKey: ['{module}', id],
    queryFn: () => get{Module}(id!),
    enabled: !!id,  // 有 ID 才查询
  });
}
```

### 11.2 Mutation Hook 模式

```typescript
// features/{module}/hooks/useCreate{Module}.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { create{Module} } from '../services/{module}Api';
import type { {Module}CreateInput, ApiError } from '../types';

export function useCreate{Module}() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: {Module}CreateInput) => create{Module}(input),
    onSuccess: () => {
      // 刷新列表缓存
      queryClient.invalidateQueries({ queryKey: ['{module}s'] });
      toast.success('创建成功');
    },
    onError: (error: ApiError) => {
      // SoT: ERROR_CODES_SOT.md
      toast.error(error.message || '创建失败');
    },
  });
}
```

### 11.3 Service 层模式

```typescript
// features/{module}/services/{module}Api.ts
import { apiGet, apiPost, apiPatch, apiDelete } from '@/lib/api';
import type {
  {Module},
  {Module}CreateInput,
  {Module}UpdateInput,
  {Module}ListParams,
  PaginatedResponse,
} from '../types';

const BASE_PATH = '/api/v1/{modules}';

// 列表查询
export async function get{Module}s(
  params: {Module}ListParams = {}
): Promise<PaginatedResponse<{Module}>> {
  const searchParams = new URLSearchParams();

  if (params.page) searchParams.set('page', String(params.page));
  if (params.page_size) searchParams.set('page_size', String(params.page_size));
  if (params.status) searchParams.set('status', params.status);
  if (params.search) searchParams.set('search', params.search);

  const query = searchParams.toString();
  return apiGet<PaginatedResponse<{Module}>>(`${BASE_PATH}?${query}`);
}

// 单条查询
export async function get{Module}(id: number): Promise<{Module}> {
  return apiGet<{Module}>(`${BASE_PATH}/${id}`);
}

// 创建
export async function create{Module}(
  input: {Module}CreateInput
): Promise<{Module}> {
  return apiPost<{Module}>(BASE_PATH, input);
}

// 更新
export async function update{Module}(
  id: number,
  input: {Module}UpdateInput
): Promise<{Module}> {
  return apiPatch<{Module}>(`${BASE_PATH}/${id}`, input);
}

// 删除
export async function delete{Module}(id: number): Promise<void> {
  return apiDelete(`${BASE_PATH}/${id}`);
}
```

### 11.4 页面组件模式

```typescript
// features/{module}/components/{Module}Page.tsx
'use client';

import { useState } from 'react';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DataTable } from '@/components/ui/data-table';
import { useTableParams } from '@/hooks';
import { use{Module}s } from '../hooks';
import { columns } from './columns';
import { {Module}Dialog } from './{Module}Dialog';

export function {Module}Page() {
  // 1. URL 状态管理
  const { params, setParams } = useTableParams();

  // 2. 数据获取
  const { data, isLoading, error } = use{Module}s(params);

  // 3. 本地状态
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selected, setSelected] = useState<{Module} | null>(null);

  // 4. 事件处理
  const handleCreate = () => {
    setSelected(null);
    setDialogOpen(true);
  };

  const handleEdit = (item: {Module}) => {
    setSelected(item);
    setDialogOpen(true);
  };

  // 5. 渲染
  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{Module}管理</h1>
          <p className="text-muted-foreground">
            管理系统中的{module}数据
          </p>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="mr-2 h-4 w-4" />
          新建
        </Button>
      </div>

      {/* 数据表格 */}
      <DataTable
        columns={columns}
        data={data?.items ?? []}
        loading={isLoading}
        pagination={{
          page: params.page ?? 1,
          pageSize: params.page_size ?? 20,
          total: data?.total ?? 0,
          onPageChange: (page) => setParams({ page }),
          onPageSizeChange: (size) => setParams({ page_size: size }),
        }}
        onRowClick={handleEdit}
      />

      {/* 新建/编辑弹窗 */}
      <{Module}Dialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        data={selected}
      />
    </div>
  );
}
```

### 11.5 表单弹窗模式

```typescript
// features/{module}/components/{Module}Dialog.tsx
'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useCreate{Module}, useUpdate{Module} } from '../hooks';
import type { {Module} } from '../types';

// Zod Schema
const formSchema = z.object({
  name: z.string().min(1, '名称不能为空').max(100, '名称最多100字'),
  // ... 更多字段
});

type FormValues = z.infer<typeof formSchema>;

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  data?: {Module} | null;
}

export function {Module}Dialog({ open, onOpenChange, data }: Props) {
  const isEdit = !!data;

  // 表单
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
    },
  });

  // 编辑时填充数据
  useEffect(() => {
    if (data) {
      form.reset({
        name: data.name,
      });
    } else {
      form.reset({ name: '' });
    }
  }, [data, form]);

  // Mutations
  const createMutation = useCreate{Module}();
  const updateMutation = useUpdate{Module}();

  const isPending = createMutation.isPending || updateMutation.isPending;

  // 提交
  const onSubmit = (values: FormValues) => {
    if (isEdit && data) {
      updateMutation.mutate(
        { id: data.id, ...values },
        { onSuccess: () => onOpenChange(false) }
      );
    } else {
      createMutation.mutate(values, {
        onSuccess: () => onOpenChange(false),
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEdit ? '编辑' : '新建'}</DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>名称</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button type="submit" disabled={isPending}>
                {isPending ? '保存中...' : '保存'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
```

### 11.6 表格列定义模式

```typescript
// features/{module}/components/columns.tsx
'use client';

import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, Pencil, Trash } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { StatusBadge } from '@/components/shared';
import { formatDate, formatMoney } from '@/lib/format';
import type { {Module} } from '../types';

export const columns: ColumnDef<{Module}>[] = [
  {
    accessorKey: 'id',
    header: 'ID',
    size: 80,
  },
  {
    accessorKey: 'name',
    header: '名称',
  },
  {
    accessorKey: 'status',
    header: '状态',
    cell: ({ row }) => (
      // SoT: STATE_MACHINE.md v2.6
      <StatusBadge status={row.original.status} />
    ),
  },
  {
    accessorKey: 'amount',
    header: '金额',
    cell: ({ row }) => (
      // SoT: BUSINESS_RULES.md#BR-FIN-003
      <span className="font-mono">{formatMoney(row.original.amount)}</span>
    ),
  },
  {
    accessorKey: 'created_at',
    header: '创建时间',
    cell: ({ row }) => formatDate(row.original.created_at),
  },
  {
    id: 'actions',
    header: '操作',
    size: 80,
    cell: ({ row }) => (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem>
            <Pencil className="mr-2 h-4 w-4" />
            编辑
          </DropdownMenuItem>
          <DropdownMenuItem className="text-destructive">
            <Trash className="mr-2 h-4 w-4" />
            删除
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];
```

---

## 第十二章：RBAC 权限系统

> **v3.1 重大修正**: 本章角色定义与 MASTER.md v4.6 §2.4 及 §INV-007 完全对齐

### 12.1 角色体系（双层架构）

> **SoT: MASTER.md v4.6 §2.4 + §INV-007**

本系统采用**业务层/技术层双层角色架构**：

| 层级 | 定义来源 | 角色数量 | 说明 |
|------|---------|---------|------|
| **业务层** | PRD v2.2 / MASTER.md §2.4 | 6 个 | 面向用户的业务角色 |
| **技术层** | 数据库 CHECK 约束 | 4 个 | 系统实现的技术角色 |

#### 业务层角色（6 角色）

| 角色ID | 中文名 | 核心职责 | 权限级别 |
|--------|--------|----------|----------|
| `ceo` | 老板 | 资金安全、公司盈亏、最终决策 | L6 (最高) |
| `project_owner` | 项目负责人 | 项目盈亏、日报审核、资金使用效率 | L5 |
| `finance` | 财务 | 资金出入准确、数据真实、对账 | L4 |
| `pitcher` | 投手 | CPL 达标、日报准确、执行投放 | L2 |
| `account_manager` | 户管 | 账户分配、账户状态监控 | L3 |
| `admin` | 管理员 | 系统配置（不参与业务） | L6 (系统) |

#### 技术层角色（4 角色 - 数据库 CHECK 约束）

```sql
-- SoT: MASTER.md v4.6 §INV-007
CHECK (role IN ('admin', 'finance', 'media_buyer', 'account_manager'))
```

| 技术角色 | 对应业务角色 | 说明 |
|---------|-------------|------|
| `admin` | ceo, admin | 老板和管理员共用 admin 权限 |
| `finance` | finance | 财务角色直接映射 |
| `media_buyer` | pitcher | 投手 = 媒体采买 |
| `account_manager` | account_manager | 户管角色直接映射 |

#### 业务→技术层映射代码

```typescript
// SoT: MASTER.md v4.6 §INV-007
const ROLE_MAPPING: Record<BusinessRole, TechRole | null> = {
  ceo: 'admin',              // 老板使用 admin 权限
  project_owner: null,       // 通过 is_project_owner 或 project_members 判断
  finance: 'finance',
  pitcher: 'media_buyer',    // 投手 = 媒体采买
  account_manager: 'account_manager',
  admin: 'admin',
};

// project_owner 特殊处理
function isProjectOwner(user: User, projectId: number): boolean {
  // 方式1: 用户属性
  if (user.is_project_owner) return true;
  // 方式2: 项目成员表
  return user.project_memberships.some(
    m => m.project_id === projectId && m.role === 'owner'
  );
}
```

### 12.2 废弃角色列表

> **v3.1 修正**: 明确哪些角色已废弃

```typescript
// ❌ 禁止使用的角色
const DEPRECATED_ROLES = [
  'supervisor',     // PRD v2.2 已移除，职责合并到 project_owner
  'data_operator',  // 不在 6 角色白名单中
  'data_clerk',     // 已废弃
  'manager',        // 已废弃
  'trader',         // 已废弃
];

// ⚠️ 常见错误
// ❌ ceo 不是废弃角色！它是有效的业务层角色
// ❌ pitcher 不是废弃角色！它是有效的业务层角色（技术层用 media_buyer）
```

### 12.3 权限矩阵

> **v3.1 修正**: 基于正确的 6 业务角色

| 菜单 | ceo | project_owner | finance | pitcher | account_manager | admin |
|------|:---:|:-------------:|:-------:|:-------:|:---------------:|:-----:|
| 运营驾驶舱 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 项目管理 | ✓ | ✓ | ✓ | - | ✓ | ✓ |
| 广告账户 | ✓ | ✓ | - | ✓(只读) | ✓ | ✓ |
| 日报管理 | ✓ | ✓ | - | ✓ | - | ✓ |
| 周度简报 | ✓ | ✓ | ✓ | - | - | ✓ |
| 财务管理 | ✓ | ✓ | ✓ | - | - | ✓ |
| 充值管理 | ✓ | ✓ | ✓ | - | - | ✓ |
| 对账管理 | ✓ | - | ✓ | - | - | ✓ |
| 系统管理 | ✓ | - | - | - | - | ✓ |

### 12.4 核心权限分工

> **SoT: MASTER.md v4.6 §2.1-§2.5**

| 流程 | 发起 | 复核 | 终审 |
|------|------|------|------|
| 日报 | pitcher | project_owner | - |
| 充值 | pitcher/account_manager | account_manager | finance |
| 项目 | account_manager | - | ceo (干预) |

**资金责任链**：
```
项目负责人申请 → 财务审核 → 老板批准 → 项目负责人负责使用
```

### 12.5 导航权限配置

```typescript
// config/nav-config.ts
// SoT: MASTER.md v4.6 §2.4

// 业务层角色枚举
export type BusinessRole = 
  | 'ceo' 
  | 'project_owner' 
  | 'finance' 
  | 'pitcher' 
  | 'account_manager' 
  | 'admin';

// 技术层角色枚举 (数据库)
export type TechRole = 'admin' | 'finance' | 'media_buyer' | 'account_manager';

export const mainNavGroups: NavGroup[] = [
  {
    title: '业务管理',
    items: [
      {
        id: 'dashboard',
        title: '运营驾驶舱',
        url: '/',
        icon: LayoutDashboard,
        // 无 access = 所有角色可见
      },
      {
        id: 'daily-reports',
        title: '日报管理',
        url: '/daily-reports',
        icon: FileText,
        access: {
          roles: ['ceo', 'project_owner', 'pitcher', 'admin'],
        },
      },
    ],
  },
  {
    title: '财务管理',
    access: {
      roles: ['ceo', 'finance', 'project_owner', 'admin'],
    },
    items: [
      // 财务相关菜单...
    ],
  },
  {
    title: '系统管理',
    access: {
      roles: ['ceo', 'admin'],
    },
    items: [
      // 系统管理菜单...
    ],
  },
];
```

---

## 第十三章：后端开发规范

### 13.1 API 开发流程

```
1. 查阅 SoT 文档 (按裁判链优先级)
   └── API_SOT.md v9.0 确认端点定义
   └── DATA_SCHEMA.md v5.2 确认数据结构
   └── STATE_MACHINE.md v2.6 确认状态流转
   └── BUSINESS_RULES.md v3.2 确认业务规则

2. 数据库模型 + Alembic 迁移
   └── backend/models/{entity}.py
   └── alembic revision --autogenerate

3. Service 层 + 单元测试
   └── backend/services/{entity}_service.py
   └── backend/tests/services/test_{entity}_service.py

4. Router 层
   └── backend/routers/{entity}.py
   └── 使用 success_response() 包装响应

5. 集成测试 + 文档
   └── backend/tests/api/test_{entity}_api.py
   └── 更新 API_SOT.md
```

### 13.2 响应格式规范

```python
# ✅ 正确的响应格式
from core.responses import success_response

@router.get("/{id}")
async def get_item(id: int):
    item = await service.get_by_id(id)
    return success_response(
        data=item,
        message="获取成功"
    )

# ✅ 正确的错误处理 (错误码来自 ERROR_CODES_SOT.md v2.1)
from core.error_codes import BusinessErrorCodes
from core.exceptions import BusinessError

if not item:
    raise BusinessError(
        code=BusinessErrorCodes.RESOURCE_NOT_FOUND,
        message="资源不存在"
    )
```

### 13.3 禁止事项

```python
# ❌ 禁止 SQL 拼接
query = f"SELECT * FROM users WHERE id = {user_id}"

# ✅ 使用参数化查询
query = select(User).where(User.id == user_id)

# ❌ 禁止返回敏感字段
return user.dict()  # 可能包含 password_hash

# ✅ 使用响应模型过滤
return UserResponse.from_orm(user)

# ❌ 禁止绕过权限检查
@router.get("/admin/users")
async def get_all_users():
    return await service.get_all()

# ✅ 使用权限装饰器
@router.get("/admin/users")
@require_role(["admin"])
async def get_all_users(current_user: User = Depends(get_current_user)):
    return await service.get_all()
```

---

## 第十四章：Git 工作流

### 14.1 提交前检查清单

```markdown
□ 代码是否符合 SoT 规范？(裁判链)
□ 是否有类型错误？(npm run type-check / mypy)
□ 是否通过 lint？(npm run lint / ruff)
□ 是否有测试覆盖？
□ 是否更新了相关文档？
□ 是否更新了 memory-bank/progress.md？
```

### 14.2 Commit Message 格式

```bash
# 格式
<type>(<scope>): <description>

# 类型
feat:     新功能
fix:      Bug 修复
docs:     文档更新
style:    代码格式
refactor: 重构
test:     测试
chore:    构建/工具

# 示例
feat(daily-reports): add trend analysis chart
fix(api): correct pagination offset calculation
docs(sot): update STATE_MACHINE to v2.6
```

### 14.3 分支策略

```
master          # 生产分支
  └── develop   # 开发分支
       ├── feature/xxx    # 功能分支
       ├── fix/xxx        # 修复分支
       └── refactor/xxx   # 重构分支
```

### 14.4 OpenSpec 分支命名

```bash
# OpenSpec change 实施分支
feature/<change-id>

# 示例
feature/add-transfer-v2
feature/update-state-machine-v3

# Commit message 格式
<type>(<scope>): <description> [<change-id>]

# 示例
feat(api): add transfer endpoint [add-transfer-v2]
docs(sot): update STATE_MACHINE for 9-state [update-state-machine-v3]
```

---

## 第十五章：测试规范

### 15.1 测试金字塔

```
          E2E 测试 (Playwright)
         /                    \
       集成测试 (pytest/jest)
      /                        \
    单元测试 (pytest/vitest)
   /                            \
  ─────────────────────────────────
       测试数量递增，执行时间递增
```

### 15.2 测试命名规范

```typescript
// 前端测试
describe('DailyReportsTable', () => {
  it('should render loading state when isLoading is true', () => {})
  it('should display empty state when data is empty', () => {})
  it('should call onRowClick when row is clicked', () => {})
})

// 后端测试
class TestDailyReportService:
    def test_create_report_success(self):
    def test_create_report_invalid_date_raises_error(self):
    def test_transition_to_trend_ok_from_raw_submitted(self):
```

### 15.3 回归测试门槛（强制）

**触发条件**:

| 变更范围 | 触发条件 | 验证命令 |
|---------|---------|---------|
| `backend/services/*` | 修改任何 service 文件 | `python run_tests.py --type regression` |
| `backend/routers/*` | 修改任何 router 文件 | `python run_tests.py --type regression` |
| `docs/sot/*` | 修改任何 SoT 文档 | `python run_tests.py --type regression` |

**五连拍测试套件**:

```bash
# 方式 1: 使用 run_tests.py
python run_tests.py --type regression

# 方式 2: 手动执行（五连拍）
python -m pytest backend/tests/api/test_daily_report_flow_generated.py -q
python -m pytest backend/tests/api/test_trend_risk_flow_generated.py -q
python -m pytest backend/tests/api/test_topup_flow_generated.py -q
python -m pytest backend/tests/api/test_reconciliation_flow_generated.py -q
python -m pytest backend/tests/api/test_ledger_flow_generated.py -q
```

---

## 第十六章：安全规范

### 16.1 输入验证

```python
# ✅ Pydantic 验证
class CreateReportInput(BaseModel):
    report_date: date
    ad_account_id: int = Field(..., gt=0)
    spend: Decimal = Field(..., ge=0, decimal_places=2)
    
    @field_validator('report_date')
    def validate_date(cls, v):
        if v > date.today():
            raise ValueError('日期不能是未来')
        return v
```

### 16.2 认证授权

```python
# ✅ 使用 Supabase Auth
from core.security import get_current_user, require_role

@router.get("/protected")
async def protected_route(
    current_user: User = Depends(get_current_user)
):
    return {"user_id": current_user.id}

@router.delete("/admin/users/{id}")
@require_role(["admin"])  # 仅 admin 可访问
async def delete_user(
    id: int,
    current_user: User = Depends(get_current_user)
):
    ...
```

### 16.3 敏感数据处理

```python
# ✅ 响应模型排除敏感字段
class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    # 不包含 password_hash、api_key 等

    class Config:
        from_attributes = True
```

---

## 第十七章：性能优化

### 17.1 前端性能

```typescript
// 1. 使用 React Query 缓存
const { data } = useQuery({
  queryKey: ['reports', params],
  staleTime: 2 * 60 * 1000,  // 2 分钟缓存
});

// 2. 虚拟滚动 (大列表)
import { useVirtualizer } from '@tanstack/react-virtual';

// 3. 图片优化
import Image from 'next/image';
<Image src="/logo.png" width={100} height={100} />

// 4. 代码分割
const DashboardChart = dynamic(
  () => import('@/components/DashboardChart'),
  { ssr: false }
);
```

### 17.2 后端性能

```python
# 1. 使用数据库索引
class DailyReport(Base):
    __table_args__ = (
        Index('ix_daily_report_date_account', 'report_date', 'ad_account_id'),
    )

# 2. 批量操作
await session.execute(
    insert(DailyReport).values(reports_data)
)

# 3. 懒加载关联
relationship("AdAccount", lazy="selectin")

# 4. 分页查询
query = select(DailyReport).offset(skip).limit(limit)

# 5. 缓存热点数据
from functools import lru_cache

@lru_cache(maxsize=100)
def get_project_config(project_id: int):
    return db.query(Project).get(project_id)
```


---

## 第十八章：质量门禁

### 18.1 开发阶段门禁

| 门禁 | 命令 | 通过标准 |
|------|------|---------|
| TypeScript | `npx tsc --noEmit` | 0 errors |
| ESLint | `npm run lint` | 0 errors |
| 构建 | `npm run build` | 成功 |
| Python 类型 | `mypy backend/` | 0 errors |
| Python Lint | `ruff check backend/` | 0 errors |

### 18.2 任务完成检查清单

> **v3.1 修正**: 角色检查与 MASTER.md v4.6 对齐

```markdown
## 代码质量
- [ ] TypeScript/Python 编译通过
- [ ] ESLint/Ruff 无错误
- [ ] 无 `any` 类型

## SoT 合规
- [ ] 状态值在 STATE_MACHINE.md v2.6 中
- [ ] 角色值在 6 业务角色白名单中
- [ ] 错误码在 ERROR_CODES_SOT.md v2.1 中
- [ ] 代码有 SoT 来源标注

## 组件规范
- [ ] 使用 shadcn/ui 组件
- [ ] 无手写 HTML 标签
- [ ] 使用 apiFetch 调用 API

## 权限检查
- [ ] 无 supervisor 角色 (已废弃)
- [ ] 无 data_operator 角色 (不在白名单)
- [ ] pitcher/media_buyer 映射正确
- [ ] ceo 使用 admin 权限
```

### 18.3 每日检查清单

```markdown
## 开始前 (5 分钟)
□ 读取 memory-bank/progress.md
□ 确认今天的任务
□ 打开相关 SoT 文档

## 生成代码后 (1 分钟)
□ 5 秒扫描: 搜索 supervisor/data_operator
□ 5 秒扫描: 状态值在枚举内
□ 5 秒扫描: 代码有 SoT 标注

## 提交前 (3 分钟)
□ TypeScript/Python 编译通过
□ ESLint/Ruff 检查通过
□ progress.md 已更新
```

---

## 第十九章：快速参考

### 19.1 角色白名单

> **v3.1 修正**: 完整的双层角色定义

```typescript
// SoT: MASTER.md v4.6 §2.4 + §INV-007

// ===== 业务层角色 (6 角色) =====
const BUSINESS_ROLES = [
  'ceo',             // 老板 - 资金安全、公司盈亏、最终决策
  'project_owner',   // 项目负责人 - 项目盈亏、日报审核
  'finance',         // 财务 - 资金出入准确、对账
  'pitcher',         // 投手 - CPL 达标、日报准确
  'account_manager', // 户管 - 账户分配、状态监控
  'admin',           // 管理员 - 系统配置（不参与业务）
] as const;

// ===== 技术层角色 (4 角色 - 数据库 CHECK 约束) =====
const TECH_ROLES = ['admin', 'finance', 'media_buyer', 'account_manager'] as const;

// ===== 业务→技术层映射 =====
const ROLE_MAPPING = {
  ceo: 'admin',              // 老板使用 admin 权限
  project_owner: null,       // 通过 is_project_owner 或 project_members 判断
  finance: 'finance',
  pitcher: 'media_buyer',    // 投手 = 媒体采买
  account_manager: 'account_manager',
  admin: 'admin',
};

// ❌ 废弃角色 (禁止使用)
const DEPRECATED_ROLES = ['supervisor', 'data_operator', 'data_clerk', 'manager', 'trader'];
```

### 19.2 日报状态（8 状态机）

```typescript
// SoT: STATE_MACHINE.md v2.6 §2
const DAILY_REPORT_STATES = [
  'raw_submitted',    // 投手提交原始数据
  'trend_pending',    // 趋势风控检测中
  'trend_ok',         // 趋势正常 → 自动流转
  'trend_flagged',    // 趋势异常 → 需运营复核
  'trend_resolved',   // 运营确认"正常波动" → 继续流转
  'final_pending',    // 等待运营录入真实消耗
  'final_confirmed',  // 运营确认最终粉数
  'final_locked',     // 计费锁定 (终态)
];
```

**状态流转图**:
```
[raw_submitted] → [trend_pending]
                       ↓
         ┌─────────────┴─────────────┐
         ↓                           ↓
    [trend_ok]               [trend_flagged]
         ↓                           ↓
         │                   [trend_resolved]
         ↓                           ↓
         └─────────→ [final_pending] ←┘
                           ↓
                   [final_confirmed]
                           ↓
                    [final_locked]
```

### 19.3 充值状态（7 个）

```typescript
// SoT: STATE_MACHINE.md v2.6
const TOPUP_STATES = [
  'draft',            // 草稿
  'pending_review',   // 待复核
  'finance_approve',  // 财务审批
  'paid',             // 已支付
  'completed',        // 已完成
  'rejected',         // 已拒绝
  'cancelled',        // 已取消
];
```

**状态流转图**:
```
[draft] ──────→ [pending_review] ──────→ [finance_approve] ──────→ [paid] ──────→ [completed]
   ↓                   ↓                        ↓
[cancelled]        [rejected]               [rejected]
```

### 19.4 必须使用的组件

| 场景 | 组件 |
|------|------|
| 数据列表 | `DataTable` |
| 状态标签 | `StatusBadge` |
| 表单 | `Form` + `FormField` |
| 弹窗 | `Dialog` / `AlertDialog` |
| 通知 | `toast` (sonner) |

### 19.5 核心公式

```typescript
// SoT: BUSINESS_RULES.md v3.2

// 收入 (per_lead 按粉结算)
revenue = conversions_final × unit_price;

// 收入 (fee_rate 按服务费结算)
revenue = ad_spend × service_fee_rate;

// 成本
cost = real_spend + fee;

// 毛利
gross_profit = revenue - cost;

// CPL
cpl = ad_spend / conversions_final;

// 可用资金
available = opening_balance + Σtopup - Σad_spend;

// 押款（代理商未消耗余额）
deposit = Σhistorical_topup - Σhistorical_spend;
```

### 19.6 快速命令

```bash
# 开发
npm run dev           # 启动前端开发服务器
uvicorn main:app --reload  # 启动后端

# 检查
npx tsc --noEmit      # TypeScript 检查
npm run lint          # ESLint 检查
npm run build         # 构建检查
mypy backend/         # Python 类型检查
ruff check backend/   # Python lint

# 测试
python run_tests.py --type regression  # 回归测试

# 搜索违规（v3.1 更新）
grep -r "supervisor" frontend/src/       # 废弃角色
grep -r "data_operator" frontend/src/    # 非白名单角色
grep -r "fetch\(" frontend/src/ | grep -v "lib/api"  # 直接 fetch
```

---

## 第二十章：提示词模板

### 20.1 新建功能模块

```markdown
## 背景
项目：AI 广告代投系统
技术栈：Next.js 15 + TypeScript + shadcn/ui + TanStack Query v5

## 任务
为 [模块名] 创建完整的功能模块

## 目录结构
请在 features/[module]/ 下创建：
- components/{Module}Page.tsx
- components/{Module}Dialog.tsx
- components/columns.tsx
- hooks/use{Module}s.ts
- hooks/useCreate{Module}.ts
- services/{module}Api.ts
- types/{module}.types.ts

## SoT 约束
- 状态值：参考 STATE_MACHINE.md v2.6
- 业务角色：6 角色白名单 (ceo, project_owner, finance, pitcher, account_manager, admin)
- 技术角色：4 角色 (admin, finance, media_buyer, account_manager)
- 禁止角色：supervisor, data_operator (已废弃)
- 错误码：参考 ERROR_CODES_SOT.md v2.1
- API 路径：参考 API_SOT.md v9.0

## 验收标准
- [ ] TypeScript 编译通过
- [ ] 使用 shadcn/ui 组件
- [ ] 使用 apiFetch
- [ ] 有 SoT 来源标注
```

### 20.2 添加表格列

```markdown
## 任务
为 [模块] 表格添加 [字段] 列

## 约束
- 字段类型：参考 DATA_SCHEMA.md v5.2
- 格式化：
  - 金额使用 formatMoney()
  - 日期使用 formatDate()
  - 状态使用 StatusBadge

## 参考
现有列定义在 features/[module]/components/columns.tsx
```

### 20.3 添加表单字段

```markdown
## 任务
在 [模块]Dialog 中添加 [字段] 输入

## 约束
- 字段验证：使用 zod schema
- 必填项：参考 DATA_SCHEMA.md v5.2
- 组件：使用 FormField + 对应 UI 组件

## 示例
<FormField
  control={form.control}
  name="fieldName"
  render={({ field }) => (
    <FormItem>
      <FormLabel>字段名称</FormLabel>
      <FormControl>
        <Input {...field} />
      </FormControl>
      <FormMessage />
    </FormItem>
  )}
/>
```

### 20.4 修复 Bug

```markdown
## 问题描述
[描述问题现象]

## 复现步骤
1. [步骤1]
2. [步骤2]

## 期望行为
[应该发生什么]

## 实际行为
[实际发生什么]

## 要求
1. 分析根本原因
2. 修复问题
3. 不要破坏现有功能
4. 遵循项目代码规范
```

---

## 附录

### A. 相关文档

| 文档 | 路径 | 用途 |
|------|------|------|
| CLAUDE.md | `/CLAUDE.md` | 项目入口指南 |
| 任务卡 | `docs/guides/TASK_CARDS_v2.md` | 任务定义 |
| Memory Bank | `memory-bank/` | 项目记忆库 |

### B. SoT 文档索引

> **v3.1 修正**: 版本号与 CLAUDE.md 裁判链对齐

| 文档 | 版本 | 路径 | 核心内容 |
|------|------|------|---------|
| 系统宪法 | v4.6 | `docs/sot/MASTER.md` | 架构基准、6 角色定义 |
| 状态机 | v2.6 | `docs/sot/STATE_MACHINE.md` | 状态定义 |
| 数据结构 | v5.2 | `docs/sot/DATA_SCHEMA.md` | 核心表结构 |
| 业务规则 | v3.2 | `docs/sot/BUSINESS_RULES.md` | BR-* 规则 |
| API 规范 | v9.0 | `docs/sot/API_SOT.md` | 端点定义 |
| 错误码 | v2.1 | `docs/sot/ERROR_CODES_SOT.md` | 错误码定义 |
| 认证授权 | v2.0 | `docs/sot/AUTH_SPEC.md` | RBAC + RLS |
| 账本规则 | v1.1 | `docs/sot/LEDGER_SOT.md` | 双账本体系 |

### C. 参考项目

| 项目 | GitHub | 借鉴点 |
|------|--------|--------|
| next-shadcn-dashboard-starter | [链接](https://github.com/Kiranism/next-shadcn-dashboard-starter) | RBAC、目录结构、DataTable |
| SaaS-Boilerplate | [链接](https://github.com/ixartz/SaaS-Boilerplate) | 多租户、权限 |
| nextjs-fastapi-template | [链接](https://github.com/vintasoftware/nextjs-fastapi-template) | 前后端集成 |
| steipete/agent-rules | [链接](https://github.com/steipete/agent-rules) | Claude Code + Cursor 规则集 |
| PatrickJS/awesome-cursorrules | [链接](https://github.com/PatrickJS/awesome-cursorrules) | Cursor 规则集 |

---

## 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v3.0 | 2025-12-29 | 初始版本，合并 FRONTEND_AI_PROGRAMMING_BEST_PRACTICES.md 和 AI_CODING_SOP_v2.1.md | AI 代码工厂 |
| **v3.1** | **2025-12-29** | **P0 修复：角色定义、版本号、权限矩阵与 MASTER.md v4.6 对齐** | **AI 架构师** |

### v3.1 变更详情

**P0 修复（阻塞级）**：

1. **角色定义修正** (§12, §19.1)
   - 明确双层架构：业务层 6 角色 + 技术层 4 角色
   - `ceo` 和 `pitcher` 是有效业务角色，非废弃角色
   - `data_operator` 不在白名单中，属于废弃角色
   - 新增业务→技术层映射代码

2. **技术栈版本修正** (§5.1)
   - Next.js 16 → **15**（16 版本不存在）

3. **权限矩阵修正** (§12.3)
   - 改用正确的 6 业务角色
   - 删除 `data_operator` 列

4. **SoT 版本号修正** (§7.1, 附录 B)
   - STATE_MACHINE.md v2.7 → **v2.6**
   - DATA_SCHEMA.md v5.6 → **v5.2**
   - BUSINESS_RULES.md v4.6 → **v3.2**
   - API_SOT.md v9.4 → **v9.0**
   - ERROR_CODES_SOT.md v2.3 → **v2.1**

5. **废弃角色列表修正** (§8.2, §8.3)
   - 从废弃列表移除 `ceo` 和 `pitcher`
   - 添加 `data_operator` 到废弃列表

---

**文档版本**: v3.1
**最后更新**: 2025-12-29
**维护者**: AI 架构师
**基准 SoT**: MASTER.md v4.6 | STATE_MACHINE.md v2.6 | DATA_SCHEMA.md v5.2
