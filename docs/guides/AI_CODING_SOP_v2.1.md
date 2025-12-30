# AI 编程 SOP v2.1 - Claude Opus 4.5 & Cursor 最佳实践

> **版本**: v2.1 | **适用**: Claude Code (Opus 4.5) + Cursor IDE
> **基准**: PROJECT_RULES.md v3.5 + STATE_MACHINE.md v2.8 + GitHub 社区最佳实践
> **生效日期**: 2025-12-28
> **变更说明**: 修复 5 个 P0 + 3 个 P1 缺陷，与 SoT 体系完全对齐

---

## 一、核心理念

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

### 1.3 SoT 优先原则 (完整 8 层裁判链)

**所有技术决策的仲裁链** (来源: PROJECT_RULES.md v3.5 §一):

```
MASTER.md v4.6 (系统宪法 - ASDD Freeze v1.0)
    ↓ 引用
STATE_MACHINE.md v2.8 (状态定义) ←─── 🚫 禁止在其他文档重复定义状态
    ↓ 引用
DATA_SCHEMA.md v5.6 (数据结构)   ←─── 📌 所有表结构、字段类型以此为准
    ↓ 引用
BUSINESS_RULES.md v4.7 (业务规则) ←─── ⚖️ BR-* 规则编号具有法律效力
    ↓ 引用
API_SOT.md v9.4 (API 契约)       ←─── 🌐 所有路径、请求/响应格式以此为准
    ↓ 引用
ERROR_CODES_SOT.md v2.2 (错误码) ←─── 🚨 禁止自定义错误码
    ↓ 引用
AUTH_SPEC.md v2.1 (认证授权)     ←─── 🔐 RLS 策略以此为准
    ↓ 引用
LEDGER_SOT.md v1.2 (账本规则)    ←─── 💰 财务逻辑禁止绕过账本
```

**裁判规则**: 上游文档优先级高于下游，冲突时以上游为准。

---

## 二、Claude Opus 4.5 专属配置

### 2.1 深度思考模式 (Ultra Think)

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

### 2.2 Plan Mode 工作流

```
┌─────────────────────────────────────────────────────────────┐
│                    Plan Mode 流程                           │
├─────────────────────────────────────────────────────────────┤
│  Phase 1: 理解需求                                          │
│  ├── 启动 Explore Agent 探索代码库                          │
│  ├── 读取相关 SoT 文档 (按 8 层裁判链优先级)                 │
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

### 2.3 Agent 调度策略

| Agent 类型 | 使用场景 | 并行数 |
|-----------|---------|--------|
| `Explore` | 代码库探索、模式识别 | 最多 3 个 |
| `Plan` | 架构设计、重构规划 | 最多 3 个 |
| `claude-code-guide` | Claude Code 使用问题 | 1 个 |
| `general-purpose` | 复杂多步任务 | 根据需要 |

### 2.4 Memory Bank 自动化

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

## 三、Cursor IDE 专属配置

### 3.1 .mdc 规则格式 (推荐)

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

### 3.2 多规则文件组织

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

### 3.3 Cursor Agent 配置

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

## Performance Agent
触发: 性能相关代码
职责:
- 分析渲染性能
- 检查 bundle size
- 识别内存泄漏
- 建议优化方案

## Security Agent
触发: 安全敏感代码
职责:
- 检查输入验证
- 识别 XSS/CSRF 风险
- 审核认证逻辑
- 检查敏感数据处理
```

---

## 四、前端开发专属规则

### 4.1 技术栈约束

```typescript
// 强制技术栈 - 不可变更
const FRONTEND_STACK = {
  framework: "Next.js 16 (App Router)",
  language: "TypeScript (strict mode)",
  ui: "shadcn/ui + Tailwind CSS",
  state: "TanStack Query v5",
  form: "react-hook-form + zod",
  http: "apiFetch (lib/api.ts)",  // 禁止 fetch/axios
}
```

### 4.2 组件开发规范

```typescript
// ✅ 正确的组件结构
'use client'  // 交互组件必须声明

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { useQuery } from '@tanstack/react-query'
import { apiGet } from '@/lib/api'

interface Props {
  id: string
  onSuccess?: () => void
}

export function MyComponent({ id, onSuccess }: Props) {
  // 1. Hooks 声明
  const [isOpen, setIsOpen] = useState(false)

  // 2. 数据获取
  const { data, isLoading } = useQuery({
    queryKey: ['item', id],
    queryFn: () => apiGet(`/api/v1/items/${id}`),
  })

  // 3. 事件处理
  const handleClick = () => {
    setIsOpen(true)
    onSuccess?.()
  }

  // 4. 渲染
  if (isLoading) return <Skeleton />

  return (
    <Button onClick={handleClick}>
      {data?.name}
    </Button>
  )
}
```

### 4.3 禁止事项清单

```typescript
// ❌ 禁止直接 fetch
fetch('/api/...')
// ✅ 使用 apiGet('/api/v1/...')

// ❌ 禁止手写 HTML 标签
<button>Click</button>
<input type="text" />
<table>...</table>
// ✅ 使用 shadcn/ui 组件
<Button>Click</Button>
<Input type="text" />
<DataTable columns={cols} data={data} />

// ❌ 禁止使用 any
const data: any = ...
// ✅ 定义具体类型
const data: UserResponse = ...

// ❌ 禁止使用废弃角色
if (user.role === 'data_clerk') ...   // 废弃
if (user.role === 'manager') ...      // 废弃
if (user.role === 'supervisor') ...   // 废弃 (PRD v2.2)
if (user.role === 'data_operator') ... // 废弃
if (user.role === 'media_buyer') ...  // 废弃，用 pitcher
// ✅ 使用有效角色 (6 角色白名单 - MASTER.md v4.6)
if (user.role === 'pitcher') ...
if (user.role === 'project_owner') ...
```

### 4.4 目录结构规范

```
frontend/src/
├── app/                      # Next.js App Router
│   ├── (dashboard)/          # 后台路由组
│   ├── layout.tsx            # 根布局
│   └── providers.tsx         # 全局 Providers
│
├── features/                 # 功能模块 (核心)
│   └── {module}/
│       ├── components/       # 业务组件
│       │   ├── {Module}Page.tsx
│       │   ├── {Module}Table.tsx
│       │   └── {Module}Dialog.tsx
│       ├── hooks/            # React Query hooks
│       │   └── use{Module}.ts
│       ├── services/         # API 调用
│       │   └── {module}Api.ts
│       ├── types/            # TypeScript 类型
│       │   └── {module}.types.ts
│       └── index.ts          # 统一导出
│
├── components/
│   ├── ui/                   # shadcn/ui 组件
│   ├── layout/               # 布局组件
│   └── shared/               # 共享组件
│
├── hooks/                    # 全局 hooks
├── lib/                      # 工具库
│   ├── api.ts                # API 客户端 (关键)
│   └── utils.ts              # 工具函数
└── types/                    # 全局类型
```

---

## 五、后端开发专属规则

### 5.1 API 开发流程

```
1. 查阅 SoT 文档 (按 8 层裁判链优先级)
   └── API_SOT.md v9.4 确认端点定义
   └── DATA_SCHEMA.md v5.6 确认数据结构
   └── STATE_MACHINE.md v2.8 确认状态流转
   └── BUSINESS_RULES.md v4.7 确认业务规则

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

### 5.2 响应格式规范

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

# ✅ 正确的错误处理 (错误码来自 ERROR_CODES_SOT.md v2.2)
from core.error_codes import BusinessErrorCodes
from core.exceptions import BusinessError

if not item:
    raise BusinessError(
        code=BusinessErrorCodes.RESOURCE_NOT_FOUND,
        message="资源不存在"
    )
```

---

## 六、ASDD 4 层架构 (v2.1 新增)

> 来源: PROJECT_RULES.md v3.5 §十三

### 6.1 架构概述

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

### 6.2 Freeze Manifest 路径

| Layer | Freeze Manifest | 路径 |
|-------|-----------------|------|
| **Overview** | FREEZE_MANIFEST_v1.0.md | `docs/1.overview/FREEZE_MANIFEST_v1.0.md` |
| **SoT** | SOT_FREEZE_MANIFEST_v2.6.md | `docs/sot/SOT_FREEZE_MANIFEST_v2.6.md` |
| **Dev-Guides** | DEV_GUIDES_FREEZE_MANIFEST_v2.1.md | `docs/3.dev-guides/DEV_GUIDES_FREEZE_MANIFEST_v2.1.md` |
| **Architecture** | ARCHITECTURE_FREEZE_MANIFEST_v1.0.md | `docs/4.architecture/ARCHITECTURE_FREEZE_MANIFEST_v1.0.md` |

### 6.3 代码生成合规性检查

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
  - 例: STATE_MACHINE.md 必须引用 v2.8
  - 例: API_SOT.md 必须引用 v9.4
```

### 6.4 Agent 文件操作规范

```markdown
Q: 我要修改 STATE_MACHINE.md，是否允许？
A: 查询 docs/sot/SOT_FREEZE_MANIFEST_v2.6.md
   → STATE_MACHINE.md status: frozen → 禁止直接修改
   → 必须提交 RFC → 解冻 → 修改 → 重新 Freeze

Q: 我要引用 DATA_SCHEMA.md，应该用哪个版本？
A: 查询 docs/sot/SOT_FREEZE_MANIFEST_v2.6.md
   → DATA_SCHEMA.md v5.6 (frozen) → 使用 v5.6
```

---

## 七、OpenSpec 集成规则 (v2.1 完善)

> 来源: PROJECT_RULES.md v3.5 §十四

### 7.1 OpenSpec 唯一变更通道

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

### 7.2 必须走 OpenSpec 的场景

| 变更类型 | 示例 | 相关 SoT | 必须走 OpenSpec |
|---------|------|----------|-----------------|
| 状态机修改 | 新增 `trend_review` 状态 | STATE_MACHINE.md | ✅ 强制 |
| 错误码变更 | 新增 `BIZ-010` | ERROR_CODES_SOT.md | ✅ 强制 |
| API 契约变更 | 新增 `/api/v1/transfers` | API_SOT.md | ✅ 强制 |
| 数据库结构变更 | 新增 `audit_logs` 表 | DATA_SCHEMA.md | ✅ 强制 |
| 业务规则变更 | 新增 BR-LED-005 | BUSINESS_RULES.md | ✅ 强制 |
| Bug 修复 | 恢复既有行为 | - | ❌ 可跳过 |
| 文档 typo | 拼写修正 | - | ❌ 可跳过 |

### 7.3 Claude/SuperClaude OpenSpec 检查清单

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

### 7.4 禁止操作

1. ❌ **直接编辑 openspec/specs/** - 该目录仅由 `openspec archive` 更新
2. ❌ **无 change-id 的 SoT 修改** - 所有 SoT 变更必须关联 change-id
3. ❌ **未审批即实施** - proposal.md 未获批准前不得开始编码

### 7.5 分支与 Commit 命名规范

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

### 7.6 OpenSpec 与 ASDD 映射

| OpenSpec 概念 | ASDD 等价物 |
|---------------|------------|
| `openspec/specs/` | `docs/sot/` (SoT Layer) |
| `proposal.md` | RFC in `docs/1.overview/` |
| `design.md` | Architecture views in `docs/4.architecture/` |
| `tasks.md` | Dev-Guides 实施清单 |

---

## 八、Git 工作流规范

### 8.1 提交前检查清单

```markdown
□ 代码是否符合 SoT 规范？(8 层裁判链)
□ 是否有类型错误？(npm run type-check / mypy)
□ 是否通过 lint？(npm run lint / ruff)
□ 是否有测试覆盖？
□ 是否更新了相关文档？
□ 是否更新了 memory-bank/progress.md？
```

### 8.2 Commit Message 格式

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
docs(sot): update STATE_MACHINE to v2.7
```

### 8.3 分支策略

```
master          # 生产分支
  └── develop   # 开发分支
       ├── feature/xxx    # 功能分支
       ├── fix/xxx        # 修复分支
       └── refactor/xxx   # 重构分支
```

---

## 九、测试规范 (v2.1 完善)

### 9.1 测试金字塔

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

### 9.2 测试命名规范

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

### 9.3 回归测试门槛 (强制)

> 来源: PROJECT_RULES.md v3.5 §十三

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
python -m pytest backend/tests/ledger -q
python -m pytest backend/tests/ad_accounts -q
python -m pytest backend/tests/test_topup_api.py -q -k "not skip"
```

**CI/CD 强制规则**:
- `.github/workflows/backend-regression.yml` workflow **MUST** 通过
- 任何 PR 如果修改了上述范围，Backend Regression Tests job **MUST** 显示 ✅ 通过
- 如果回归测试失败，**禁止合并**（block merge）

**违规处理**:
1. ❌ **CI 自动阻止合并**（GitHub Actions 失败）
2. 🔴 **Reviewer 必须拒绝 PR**
3. 📝 **开发者必须修复**

**PR 描述格式**:
```markdown
## Regression Test Results

✅ All regression tests passed

- Daily Reports API: 33 passed
- Trend Risk API: 17 passed
- Ledger: 54 passed (3 skipped)
- Ad Accounts: 51 passed
- Topup API: 22 passed

**Commit**: `ac2335c`
**Test Command**: `python run_tests.py --type regression`
**CI Status**: ✅ [Backend Regression Tests](https://github.com/.../actions/runs/...)
```

---

## 十、安全规范

### 10.1 前端安全

```typescript
// ❌ 禁止硬编码敏感信息
const API_KEY = "sk-xxxx"

// ✅ 使用环境变量
const API_URL = process.env.NEXT_PUBLIC_API_URL

// ❌ 禁止直接渲染用户输入
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// ✅ 使用文本节点
<div>{userInput}</div>

// ❌ 禁止在 URL 中暴露敏感信息
/api/users?token=xxx

// ✅ 使用 Authorization header
headers: { Authorization: `Bearer ${token}` }
```

### 10.2 后端安全

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

## 十一、性能优化指南

### 11.1 前端性能

```typescript
// 1. 使用 React.memo 避免不必要渲染
export const ExpensiveComponent = React.memo(({ data }) => {
  return <div>{/* 复杂渲染 */}</div>
})

// 2. 使用 useMemo 缓存计算结果
const sortedData = useMemo(() =>
  data.sort((a, b) => a.date - b.date),
  [data]
)

// 3. 使用 useCallback 缓存函数
const handleClick = useCallback(() => {
  setOpen(true)
}, [])

// 4. 数据分页加载
const { data } = useInfiniteQuery({
  queryKey: ['items'],
  queryFn: ({ pageParam = 1 }) => getItems(pageParam),
  getNextPageParam: (lastPage) => lastPage.nextPage,
})

// 5. 图片懒加载
import Image from 'next/image'
<Image src={url} loading="lazy" />
```

### 11.2 后端性能

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

## 十二、调试与问题排查

### 12.1 前端调试

```typescript
// 1. React Query Devtools
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

// 2. 网络请求日志
console.log('[API Request]', url, options)
console.log('[API Response]', data)

// 3. 组件渲染追踪
useEffect(() => {
  console.log('[Render]', componentName, props)
})

// 4. 性能分析
import { Profiler } from 'react'
<Profiler id="Component" onRender={onRenderCallback}>
```

### 12.2 后端调试

```python
# 1. 请求日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 2. SQL 查询日志
import sqlalchemy
sqlalchemy.logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

# 3. 断点调试
import pdb; pdb.set_trace()
# 或使用 breakpoint()

# 4. 异步调试
import asyncio
asyncio.get_event_loop().set_debug(True)
```

---

## 十三、快速参考卡片

### 13.1 角色白名单 (6 个) ✅ 已修正

> 来源: MASTER.md v4.6 §2.4 (6 角色白名单)

```python
VALID_ROLES = [
    "ceo",             # 老板 - 资金安全、公司盈亏、最终决策
    "project_owner",   # 项目负责人 - 项目盈亏、日报审核
    "finance",         # 财务 - 资金出入准确、对账
    "pitcher",         # 投手 - CPL达标、日报准确
    "account_manager", # 户管 - 账户分配、状态监控
    "admin"            # 管理员 - 系统配置（不参与业务）
]

# ❌ 废弃角色 (禁止使用)
DEPRECATED_ROLES = ["supervisor", "data_operator", "media_buyer", "data_clerk", "manager"]
```

**核心权限分工**:
| 流程 | 发起 | 复核 | 终审 |
|------|------|------|------|
| 日报 | pitcher | project_owner | - |
| 充值 | pitcher/account_manager | project_owner | finance |
| 项目 | project_owner | - | admin (干预) |

### 13.2 日报状态 (8 状态机) ✅ 已修正

> 来源: STATE_MACHINE.md v2.8 §8

```python
DAILY_REPORT_STATES = [
    "raw_submitted",    # 投手提交原始数据 (conversions_raw, raw_spend)
    "trend_pending",    # 趋势风控检测中
    "trend_ok",         # 趋势正常 → 自动流转
    "trend_flagged",    # 趋势异常 (TF-001: 粉数骤降 >50%) → 需运营复核
    "trend_resolved",   # 运营确认"正常波动" → 继续流转
    "final_pending",    # 等待运营录入真实消耗 (real_spend)
    "final_confirmed",  # 运营确认最终粉数 (conversions_final)
    "final_locked"      # 计费锁定 (终态) → 触发账本记录创建
]
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

**关键业务规则**:
- **BR-RPT-001**: `conversions_raw != conversions_final` 时，差异 >20% 必须标记 `trend_flagged`
- **BR-RPT-002**: 只有 `final_locked` 状态的日报才能参与账本计算
- **BR-RPT-003**: `final_locked` 后禁止修改

### 13.3 充值状态 (7 个) ✅ 已修正

> 来源: STATE_MACHINE.md v2.8

```python
TOPUP_STATES = [
    "draft",            # 草稿
    "pending_review",   # 待复核
    "finance_approve",  # 财务审批
    "paid",             # 已支付
    "completed",        # 已完成
    "rejected",         # 已拒绝
    "cancelled"         # 已取消
]
```

**状态流转图** (已修正):
```
[draft] ──────→ [pending_review] ──────→ [finance_approve] ──────→ [paid] ──────→ [completed]
   ↓                   ↓                        ↓
[cancelled]        [rejected]               [rejected]
```

**转换规则**:
- `cancelled` 只能从 `draft` 到达
- `rejected` 可从 `pending_review` 或 `finance_approve` 到达

### 13.4 必须使用的组件

| 场景 | 组件 |
|------|------|
| 数据列表 | `DataTable` |
| 状态标签 | `StatusBadge` |
| 表单 | `Form` + `FormField` |
| 弹窗 | `Dialog` / `AlertDialog` |
| 通知 | `toast` (sonner) |

### 13.5 API 调用模板

```typescript
// 查询
const { data, isLoading } = useQuery({
  queryKey: ['items', params],
  queryFn: () => apiGet('/api/v1/items', params),
})

// 变更
const mutation = useMutation({
  mutationFn: (data) => apiPost('/api/v1/items', data),
  onSuccess: () => {
    queryClient.invalidateQueries(['items'])
    toast.success('操作成功')
  },
})
```

---

## 十四、参考资源

### 14.1 GitHub 优秀项目

| 仓库 | 说明 |
|------|------|
| [steipete/agent-rules](https://github.com/steipete/agent-rules) | Claude Code + Cursor 规则集 |
| [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | Claude Code 资源汇总 |
| [PatrickJS/awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules) | Cursor 规则集 |
| [Matt-Dionis/claude-code-configs](https://github.com/Matt-Dionis/claude-code-configs) | Claude Code 配置生成器 |

### 14.2 项目 SoT 文档 (完整版本索引)

| 文档 | 版本 | 路径 | 核心内容 |
|------|------|------|---------|
| 系统宪法 | v4.6 | `docs/sot/MASTER.md` | ASDD Freeze 基准 |
| 状态机 | v2.8 | `docs/sot/STATE_MACHINE.md` | 8 状态机定义 |
| 数据结构 | v5.6 | `docs/sot/DATA_SCHEMA.md` | 核心表结构 |
| 业务规则 | v4.7 | `docs/sot/BUSINESS_RULES.md` | BR-* 规则编号 |
| API 规范 | v9.4 | `docs/sot/API_SOT.md` | 端点定义 |
| 错误码 | v2.2 | `docs/sot/ERROR_CODES_SOT.md` | 错误码定义 |
| 认证授权 | v2.1 | `docs/sot/AUTH_SPEC.md` | RBAC + RLS |
| 账本规则 | v1.2 | `docs/sot/LEDGER_SOT.md` | 双账本体系 |

---

## 十五、版本变更历史

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| v2.1 | 2025-12-28 | 🔴 修复 5 个 P0 + 3 个 P1 缺陷，与 PROJECT_RULES.md v3.5 完全对齐 |
| v2.0 | 2025-12-28 | 基于 GitHub 社区最佳实践初版 |

### v2.1 修复清单

| ID | 级别 | 缺陷 | 修复内容 |
|----|------|------|---------|
| P0-001 | 🔴 | 角色体系混淆 | 改为正确的 5 角色体系 |
| P0-002 | 🔴 | SoT 裁判链不完整 | 补充完整 8 层裁判链 |
| P0-003 | 🔴 | 日报状态机脱节 | 改为 8 状态机 |
| P0-004 | 🔴 | 缺失 ASDD 架构 | 新增第六章 |
| P0-005 | 🔴 | OpenSpec 简化 | 完善第七章 |
| P1-001 | 🟠 | 回归测试不完整 | 完善第九章 9.3 节 |
| P1-002 | 🟠 | 版本号缺失 | 全文添加版本号 |
| P1-003 | 🟠 | 充值流程图错误 | 修正 13.3 节流程图 |

---

**文档版本**: v2.1
**最后更新**: 2025-12-28
**维护者**: AI Architecture Team
**基准文档**: PROJECT_RULES.md v3.5 + STATE_MACHINE.md v2.8
