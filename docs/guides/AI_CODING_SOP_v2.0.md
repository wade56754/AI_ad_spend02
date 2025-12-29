# AI 编程 SOP v2.0 - Claude Opus 4.5 & Cursor 最佳实践

> ⚠️ **已废弃**: 本文档已被 `AI_CODING_SOP_v2.1.md` 替代
>
> **废弃原因**: 存在 5 个 P0 + 3 个 P1 缺陷，与 PROJECT_RULES.md v3.5 不一致
>
> **请使用**: [AI_CODING_SOP_v2.1.md](./AI_CODING_SOP_v2.1.md)

---

> **版本**: v2.0 (已废弃) | **适用**: Claude Code (Opus 4.5) + Cursor IDE
> **基准**: GitHub 社区最佳实践 + 项目 SoT 体系
> **生效日期**: 2025-12-28
> **废弃日期**: 2025-12-28

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

### 1.3 SoT 优先原则

```
所有技术决策的仲裁链:
MASTER.md → STATE_MACHINE.md → DATA_SCHEMA.md → API_SOT.md → 代码实现
     ↑           ↑                  ↑               ↑
     └───────────┴──────────────────┴───────────────┴── AI 只能执行，不能创造
```

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
│  ├── 读取相关 SoT 文档                                      │
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
if (user.role === 'supervisor') ...
// ✅ 使用有效角色
if (user.role === 'project_owner') ...

// ❌ 禁止使用 Phase 2 状态
status: 'trend_pending'
// ✅ 使用 Phase 1 状态
status: 'raw_submitted' | 'trend_ok' | 'final_confirmed'
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
1. 查阅 SoT 文档
   └── API_SOT.md 确认端点定义
   └── DATA_SCHEMA.md 确认数据结构
   └── STATE_MACHINE.md 确认状态流转

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

# ✅ 正确的错误处理
from core.error_codes import BusinessErrorCodes
from core.exceptions import BusinessError

if not item:
    raise BusinessError(
        code=BusinessErrorCodes.RESOURCE_NOT_FOUND,
        message="资源不存在"
    )
```

---

## 六、Git 工作流规范

### 6.1 提交前检查清单

```markdown
□ 代码是否符合 SoT 规范？
□ 是否有类型错误？(npm run type-check / mypy)
□ 是否通过 lint？(npm run lint / ruff)
□ 是否有测试覆盖？
□ 是否更新了相关文档？
□ 是否更新了 memory-bank/progress.md？
```

### 6.2 Commit Message 格式

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

### 6.3 分支策略

```
master          # 生产分支
  └── develop   # 开发分支
       ├── feature/xxx    # 功能分支
       ├── fix/xxx        # 修复分支
       └── refactor/xxx   # 重构分支
```

---

## 七、测试规范

### 7.1 测试金字塔

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

### 7.2 测试命名规范

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

### 7.3 回归测试要求

```bash
# 修改以下目录时必须运行回归测试
backend/services/*
backend/routers/*
docs/sot/*

# 运行命令
python run_tests.py --type regression

# 五连拍测试套件
1. Daily Reports API
2. Trend Risk API
3. Ledger
4. Ad Accounts
5. Topup API
```

---

## 八、安全规范

### 8.1 前端安全

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

### 8.2 后端安全

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

## 九、性能优化指南

### 9.1 前端性能

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

### 9.2 后端性能

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

## 十、调试与问题排查

### 10.1 前端调试

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

### 10.2 后端调试

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

## 十一、文档协作规范

### 11.1 SoT 文档更新流程

```
1. 识别需要变更的 SoT 文档
2. 创建 OpenSpec change proposal
3. 编写 spec deltas
4. 提交审批
5. 审批通过后执行变更
6. 更新相关代码和测试
7. 归档 change
```

### 11.2 Memory Bank 更新规则

```markdown
## 必须更新的场景

1. 完成功能开发 → 更新 progress.md
2. 添加新文件/模块 → 更新 architecture.md
3. 修改实施计划 → 更新 implementation-plan.md
4. 添加新需求 → 更新 game-design-document.md
```

---

## 十二、快速参考卡片

### 12.1 角色白名单 (6 个)

```
ceo | project_owner | finance | pitcher | account_manager | admin
```

### 12.2 日报状态 (Phase 1: 3 个)

```
raw_submitted → trend_ok → final_confirmed
```

### 12.3 充值状态 (7 个)

```
draft → pending_review → finance_approve → paid → completed
                    ↓                        ↓
                rejected                 cancelled
```

### 12.4 必须使用的组件

| 场景 | 组件 |
|------|------|
| 数据列表 | `DataTable` |
| 状态标签 | `StatusBadge` |
| 表单 | `Form` + `FormField` |
| 弹窗 | `Dialog` / `AlertDialog` |
| 通知 | `toast` (sonner) |

### 12.5 API 调用模板

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

## 十三、参考资源

### 13.1 GitHub 优秀项目

| 仓库 | 说明 |
|------|------|
| [steipete/agent-rules](https://github.com/steipete/agent-rules) | Claude Code + Cursor 规则集 |
| [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | Claude Code 资源汇总 |
| [PatrickJS/awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules) | Cursor 规则集 |
| [Matt-Dionis/claude-code-configs](https://github.com/Matt-Dionis/claude-code-configs) | Claude Code 配置生成器 |

### 13.2 项目 SoT 文档

| 文档 | 路径 |
|------|------|
| 系统宪法 | `docs/sot/MASTER.md` |
| 状态机 | `docs/sot/STATE_MACHINE.md` |
| 数据结构 | `docs/sot/DATA_SCHEMA.md` |
| API 规范 | `docs/sot/API_SOT.md` |
| 错误码 | `docs/sot/ERROR_CODES_SOT.md` |

---

**文档版本**: v2.0
**最后更新**: 2025-12-28
**维护者**: AI Architecture Team
