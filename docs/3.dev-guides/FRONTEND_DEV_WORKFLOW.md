# 前端开发流程文档 v1.3

> **面向对象**: Claude Code / Cursor 等 AI 编程助手
> **核心原则**: 先读规格书 → 再找可复用 → 最后写代码
> **可追溯性**: 每个页面必须关联 SoT 文档 + 规格书 + 代码位置

### 角色名称映射表

> ⚠️ **重要**: MASTER.md v4.4 定义的业务角色与代码实现中的技术角色名有差异。

| MASTER.md 业务角色 | 代码 UserRole 枚举 | 说明 |
|-------------------|-------------------|------|
| ceo (老板) | (待实现) | 需要添加 CEO 角色枚举 |
| supervisor (主管) | `data_operator` | 日报审核、团队管理 |
| pitcher (投手) | `media_buyer` | 投放执行、日报提交 |
| project_owner | `project_owner` | 项目负责人 |
| finance | `finance` | 财务 |
| account_manager | `account_manager` | 户管 |
| admin | `admin` | 系统管理员 |

**编码时**: 使用右侧 `UserRole` 枚举值
**文档/注释中**: 可同时标注业务角色便于理解

---

### 本文档与 FRONTEND_AI_RULES 的职责边界

> ⚠️ **重要**: 本文档与 `FRONTEND_AI_RULES_v1.1.md` 互补，非重复

| 文档 | 定位 | 回答问题 | 使用场景 |
|------|------|----------|----------|
| **FRONTEND_AI_RULES** | 约束规则 | "什么能做/不能做" | 开发前检查约束 |
| **FRONTEND_DEV_WORKFLOW** (本文档) | 流程指南 | "怎么做/步骤是什么" | 开发时按步骤执行 |

**推荐工作流**:
```
1. 先读 FRONTEND_AI_RULES → 了解禁止事项、可复用资源清单
2. 再用 FRONTEND_DEV_WORKFLOW → 按 5 步法开发新页面
3. 遇到权限问题 → 回 AI_RULES §4 查权限矩阵
4. 遇到流程问题 → 回本文档对应章节
```

**内容分工**:
- **代码地图/目录结构** → 见 AI_RULES §1.1
- **可复用资源清单** → 见 AI_RULES §1.2
- **禁止行为清单** → 见 AI_RULES §2
- **权限矩阵 (7角色×10页面)** → 见 AI_RULES §4
- **Phase 1 约束** → 见 AI_RULES §5
- **开发流程/步骤** → 见本文档
- **代码模板** → 见本文档 §5
- **验收检查** → 见本文档 §6

---

## 第一章 开发流程总览

### 1.1 流程图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         前端页面开发流程                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Step 1          Step 2          Step 3          Step 4          Step 5   │
│  ┌───────┐      ┌───────┐      ┌───────┐      ┌───────┐      ┌───────┐    │
│  │ 读规格 │ ──→ │ 查复用 │ ──→ │ 定结构 │ ──→ │ 写代码 │ ──→ │ 验收  │    │
│  │  书   │      │  清单  │      │       │      │       │      │ 检查  │    │
│  └───────┘      └───────┘      └───────┘      └───────┘      └───────┘    │
│      │              │              │              │              │         │
│      ↓              ↓              ↓              ↓              ↓         │
│  ┌───────┐      ┌───────┐      ┌───────┐      ┌───────┐      ┌───────┐    │
│  │规格书 │      │现有代码│      │文件清单│      │最小改动│      │检查清单│    │
│  │摘要   │      │映射表 │      │       │      │       │      │       │    │
│  └───────┘      └───────┘      └───────┘      └───────┘      └───────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 五步法

| 步骤 | 名称 | 输入 | 输出 | 耗时占比 |
|------|------|------|------|----------|
| Step 1 | 读规格书 | 模块规格书 | 规格书摘要 | 20% |
| Step 2 | 查复用清单 | 规格书摘要 | 复用映射表 | 30% |
| Step 3 | 定结构 | 复用映射表 | 文件清单 | 10% |
| Step 4 | 写代码 | 文件清单 | 代码文件 | 30% |
| Step 5 | 验收检查 | 代码文件 | 检查报告 | 10% |

---

## 第二章 Step 1: 读规格书

### 2.1 规格书位置

```
docs/10.module-specs/
├── README.md                  # 索引 + 模块架构图
│
├── A1-dashboard.md            # 老板驾驶舱 (P0)
├── A2-fund-overview.md        # 资金总览 (P0)
├── A3-project-pnl.md          # 项目盈亏 (P0)
│
├── B1-topup-approval.md       # 充值审批 (P1)
├── B2-daily-report-review.md  # 日报审核 (P1)
├── B3-weekly-brief.md         # 周度简报 (P2)
│
├── C1-project-mgmt.md         # 项目管理 (P0)
├── C2-pitcher-mgmt.md         # 投手管理 (P2)
├── C3-spend-detail.md         # 消耗明细 (P1)
│
└── D1-monthly-settlement.md   # 月度结算 (P2)
```

### 2.2 规格书必读章节

```yaml
必读:
  - §1 模块概述: 理解业务目标
  - §2 数据需求: 确认字段清单和 SoT
  - §3 UI 规范: 确认布局和组件
  - §5 API 接口: 确认端点和响应格式
  - §6 状态与权限: 确认角色权限

可选:
  - §4 代码块组合: 参考组合建议
  - §7 测试检查点: 验收时使用
```

### 2.3 规格书摘要模板

开发前，AI 必须输出以下摘要：

```markdown
## 规格书摘要: [模块名]

### 1. 业务目标
- 解决什么问题: [一句话描述]
- 目标用户: [角色列表]

### 2. 数据需求
- 主数据源: [表名/API]
- 核心字段: [字段列表]
- 计算字段: [公式列表]

### 3. UI 布局
- 页面类型: [列表页/详情页/表单页/Dashboard]
- 主要组件: [组件列表]

### 4. API 接口
- GET [端点]: [用途]
- POST [端点]: [用途]

### 5. 权限要求
- 可访问角色: [角色列表]
- 特殊权限: [操作权限]

### 6. SoT 追溯
- 规格书: docs/10.module-specs/[文件名]
- MASTER.md: §[章节号]
- STATE_MACHINE.md: §[章节号] (如适用)
```

---

## 第三章 Step 2: 查复用清单

### 3.1 复用检查流程

```
┌─────────────────────────────────────────────────────────────────┐
│                      复用检查流程                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐                                               │
│  │ 1. 查页面   │ → 是否有相似页面可复制？                       │
│  └──────┬──────┘   app/(dashboard)/ 下搜索                      │
│         ↓                                                       │
│  ┌─────────────┐                                               │
│  │ 2. 查组件   │ → 是否有可复用的业务组件？                     │
│  └──────┬──────┘   features/*/components/ 下搜索                │
│         ↓                                                       │
│  ┌─────────────┐                                               │
│  │ 3. 查 Hook  │ → 是否有可复用的 Hook？                        │
│  └──────┬──────┘   features/*/hooks/ 下搜索                     │
│         ↓                                                       │
│  ┌─────────────┐                                               │
│  │ 4. 查 UI    │ → 使用哪些 shadcn 组件？                       │
│  └──────┬──────┘   components/ui/ 下确认                        │
│         ↓                                                       │
│  ┌─────────────┐                                               │
│  │ 5. 查 API   │ → API 函数是否已存在？                         │
│  └─────────────┘   features/*/services/ 下搜索                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 复用映射表模板

```markdown
## 复用映射表: [模块名]

### 1. 相似页面
| 需求 | 复用来源 | 复用程度 | 改动点 |
|------|----------|----------|--------|
| 列表页 | app/(dashboard)/daily-reports/page.tsx | 90% | 改 columns |
| 详情页 | app/(dashboard)/projects/[id]/page.tsx | 70% | 改字段 |

### 2. 可复用组件
| 需求 | 复用来源 | 用法 |
|------|----------|------|
| 数据表格 | components/ui/data-table | 直接使用 |
| KPI 卡片 | components/ui/MetricCard | 直接使用 |
| 状态徽章 | components/ui/StatusBadge | 直接使用 |

### 3. 可复用 Hook
| 需求 | 复用来源 | 改动 |
|------|----------|------|
| 数据查询 | features/projects/hooks/useProjects | 改端点 |
| 权限检查 | features/auth/hooks/useAuth | 直接使用 |

### 4. UI 组件清单
| 组件 | 来源 | 用途 |
|------|------|------|
| Card | shadcn | 卡片容器 |
| Table | shadcn | 数据表格 |
| Button | shadcn | 操作按钮 |

### 5. API 函数
| 需求 | 状态 | 位置/改动 |
|------|------|----------|
| 列表查询 | 需新建 | features/[module]/services/ |
| 详情查询 | 需新建 | features/[module]/services/ |

### 6. 复用统计
- 可直接复用: X 个
- 需修改复用: X 个
- 需新建: X 个
- 预估复用率: XX%
```

### 3.3 常用复用来源速查

| 页面类型 | 最佳复用来源 | 复用程度 |
|----------|--------------|----------|
| 列表页 | `daily-reports/page.tsx` | 90% |
| 详情页 | `projects/[id]/page.tsx` | 80% |
| 表单页 | `topups/request/page.tsx` | 85% |
| Dashboard | `(dashboard)/page.tsx` | 70% |
| 审批页 | `daily-reports/review/page.tsx` | 85% |

### 3.4 复用来源验证步骤

> **重要**: 复用前必须验证文件存在且接口未变更

#### 3.4.1 AI 必须执行的验证流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    复用来源验证流程                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Step 1: 确认文件存在                                          │
│   ────────────────────                                          │
│   使用 Read 工具读取目标文件，确认路径正确                        │
│                                                                 │
│   Step 2: 确认接口签名                                          │
│   ────────────────────                                          │
│   检查组件 Props、函数参数是否与文档描述一致                      │
│                                                                 │
│   Step 3: 确认导出方式                                          │
│   ────────────────────                                          │
│   检查是 default export 还是 named export                        │
│                                                                 │
│   Step 4: 记录验证结果                                          │
│   ────────────────────                                          │
│   在复用映射表中标注"已验证"或"需更新"                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.4.2 验证示例

```typescript
// 目标: 复用 PageTemplate 组件

// Step 1: 读取文件确认存在
// Read: frontend/src/components/layout/page-template.tsx

// Step 2: 确认接口签名
interface PageTemplateProps {
  title: string;
  subtitle?: ReactNode;  // ✅ 注意: 是 subtitle 不是 description
  children: ReactNode;
  actions?: ReactNode;
  breadcrumbs?: ReactNode | BreadcrumbItem[];
  className?: string;
}

// Step 3: 确认导出方式
export function PageTemplate({ ... })  // ✅ named export

// Step 4: 验证结果
// ✅ 文件存在
// ✅ 接口与文档一致
// ⚠️ 注意 subtitle 而非 description
```

#### 3.4.3 验证检查清单

在使用任何复用来源前，确认：

```markdown
□ 文件路径正确（使用 Glob 或 Read 验证）
□ 组件/函数仍然 export（未被重构或删除）
□ Props/参数签名未变更
□ 依赖项仍然存在（import 来源）
□ 类型定义与预期一致
```

**如果验证失败**:
1. 更新复用映射表，标注变更
2. 寻找替代方案或调整代码
3. 在验收报告中记录差异

### 3.5 后端 API 不存在时的处理策略

> **场景**: 前端先于后端开发，或后端 API 尚未部署

#### 3.5.1 检查 API 是否存在

```bash
# 方式 1: 查看后端路由注册
grep -r "/{module}" backend/routers/

# 方式 2: 查看 API_SOT.md 是否已定义
grep -n "{module}" docs/2.sot/API_SOT.md

# 方式 3: 直接请求测试
curl -X GET http://localhost:8000/api/v1/{entities} -H "Authorization: Bearer $TOKEN"
```

#### 3.5.2 Mock 数据策略

**推荐方案**: 使用 TanStack Query 的 `placeholderData` + 条件 `enabled`

```typescript
// features/{module}/hooks/use{Module}.ts

// Mock 数据（开发阶段使用）
const MOCK_{ENTITIES}: {Entity}[] = [
  {
    id: '1',
    name: 'Mock Item 1',
    status: 'active',
    created_at: new Date().toISOString(),
  },
  // ... 更多 mock 数据
];

export function use{Entities}(params: {Entity}ListParams = {}) {
  const API_READY = false;  // TODO: 后端就绪后改为 true

  return useQuery({
    queryKey: queryKeys.{entities}.list(params),
    queryFn: () => get{Entities}(params),
    enabled: API_READY,  // API 未就绪时禁用
    placeholderData: API_READY ? undefined : {
      items: MOCK_{ENTITIES},
      total: MOCK_{ENTITIES}.length,
      page: 1,
      page_size: 20,
      total_pages: 1,
    },
  });
}
```

**切换到真实 API**:
1. 将 `API_READY` 改为 `true`
2. 删除 `MOCK_{ENTITIES}` 常量
3. 移除 `placeholderData`

#### 3.5.3 API 就绪检查清单

在开始开发前确认:

```markdown
□ API 端点已在 API_SOT.md 定义
□ 后端路由已实现 (backend/routers/{module}.py)
□ 数据库表已创建 (backend/models/{module}.py)
□ 本地可访问 http://localhost:8000/api/v1/{entities}
```

---

## 第四章 Step 3: 定结构

### 4.1 文件清单模板

```markdown
## 文件清单: [模块名]

### 1. 需要创建的文件
| 序号 | 文件路径 | 类型 | 来源 | 说明 |
|------|----------|------|------|------|
| 1 | app/(dashboard)/[module]/page.tsx | 页面 | 复制 daily-reports | 列表页 |
| 2 | app/(dashboard)/[module]/columns.tsx | 配置 | 复制 daily-reports | 表格列 |
| 3 | features/[module]/types/[module].types.ts | 类型 | 新建 | 类型定义 |
| 4 | features/[module]/services/[module]Api.ts | 服务 | 新建 | API 调用 |
| 5 | features/[module]/hooks/use[Module].ts | Hook | 复制 useProjects | 数据查询 |

### 2. 需要修改的文件
| 序号 | 文件路径 | 改动内容 |
|------|----------|----------|
| 1 | lib/api.ts | 添加 queryKeys.[module] |
| 2 | features/auth/ (如需要) | 权限检查逻辑 |

### 3. 不需要改动的文件
- components/ui/* (直接使用)
- features/auth/* (直接使用)
- lib/utils.ts (直接使用)

### 4. 开发顺序
1. types → 2. services → 3. hooks → 4. page → 5. columns
```

### 4.2 添加 queryKeys 模板

> **位置**: `lib/api.ts` 文件末尾的 `queryKeys` 对象中

```typescript
// 在 lib/api.ts 的 queryKeys 对象中添加新模块
export const queryKeys = {
  // ... 现有 keys

  // 新增模块 (复制此模板)
  {entities}: {
    all: ['{entities}'] as const,
    list: (params?: Record<string, any>) =>
      [...queryKeys.{entities}.all, 'list', params] as const,
    lists: (params?: Record<string, any>) =>
      [...queryKeys.{entities}.all, 'list', params] as const,
    detail: (id: string | number) =>
      [...queryKeys.{entities}.all, 'detail', String(id)] as const,
    // 可选: 按关联实体查询
    byProject: (projectId: string | number, params?: Record<string, any>) =>
      [...queryKeys.{entities}.all, 'byProject', String(projectId), params] as const,
  },
};
```

### 4.3 占位符替换规则表

> **重要**: 本文档所有代码模板使用以下占位符，AI 必须按规则替换

#### 4.3.1 命名转换规则

| 占位符 | 格式 | 转换规则 | 示例输入 | 示例输出 |
|--------|------|----------|----------|----------|
| `{Entity}` | PascalCase 单数 | 首字母大写，无分隔 | daily report | `DailyReport` |
| `{entity}` | camelCase 单数 | 首字母小写，无分隔 | daily report | `dailyReport` |
| `{Entities}` | PascalCase 复数 | 首字母大写，加 s/es | daily report | `DailyReports` |
| `{entities}` | camelCase 复数 | 首字母小写，加 s/es | daily report | `dailyReports` |
| `{module}` | kebab-case | 全小写，连字符分隔 | daily report | `daily-reports` |
| `{MODULE}` | SCREAMING_SNAKE | 全大写，下划线分隔 | daily report | `DAILY_REPORTS` |

#### 4.3.2 复数形式规则

| 单数结尾 | 复数规则 | 示例 |
|----------|----------|------|
| 辅音 + y | 去 y 加 ies | `entity` → `entities` |
| s, x, ch, sh | 加 es | `status` → `statuses` |
| 其他 | 加 s | `report` → `reports` |

#### 4.3.3 完整示例：日报模块

假设开发"日报"模块，替换如下：

| 占位符 | 替换值 |
|--------|--------|
| `{Entity}` | `DailyReport` |
| `{entity}` | `dailyReport` |
| `{Entities}` | `DailyReports` |
| `{entities}` | `dailyReports` |
| `{module}` | `daily-reports` |
| `{MODULE}` | `DAILY_REPORTS` |

**文件路径示例**:
```
features/{module}/types/{module}.types.ts
→ features/daily-reports/types/daily-reports.types.ts

hooks/use{Module}.ts
→ hooks/useDailyReports.ts

queryKeys.{entities}.list()
→ queryKeys.dailyReports.list()
```

### 4.4 标准模块结构

```
features/{module}/
├── index.ts                    # 模块导出
├── types/
│   └── {module}.types.ts       # 类型定义
├── services/
│   └── {module}Api.ts          # API 调用
├── hooks/
│   └── use{Module}.ts          # 数据查询 Hook
└── components/
    ├── {Module}Table.tsx       # 表格组件 (如需要)
    └── {Module}Form.tsx        # 表单组件 (如需要)

app/(dashboard)/{module}/
├── page.tsx                    # 列表页
├── columns.tsx                 # 表格列定义
├── [id]/
│   └── page.tsx                # 详情页
└── create/
    └── page.tsx                # 创建页
```

---

## 第五章 Step 4: 写代码

### 5.1 代码编写顺序

```
┌─────────────────────────────────────────────────────────────────┐
│                      代码编写顺序                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1. 类型定义          2. API 服务          3. 数据 Hook        │
│   ┌──────────┐        ┌──────────┐        ┌──────────┐         │
│   │  types/  │   →    │ services/│   →    │  hooks/  │         │
│   └──────────┘        └──────────┘        └──────────┘         │
│        ↓                   ↓                   ↓                │
│   定义接口            调用 apiFetch       封装 useQuery         │
│                                                                 │
│   ─────────────────────────────────────────────────────────    │
│                                                                 │
│   4. 页面组件          5. 表格列           6. 权限配置          │
│   ┌──────────┐        ┌──────────┐        ┌──────────┐         │
│   │  page.tsx│   →    │columns.tsx│  →    │permissions│        │
│   └──────────┘        └──────────┘        └──────────┘         │
│        ↓                   ↓                   ↓                │
│   复制模板页面         定义列配置         添加权限矩阵          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 各步骤代码模板

#### 5.2.1 类型定义

```typescript
// features/{module}/types/{module}.types.ts

/**
 * [模块名] 类型定义
 * SoT: docs/10.module-specs/[规格书].md §2
 */

// 主实体类型
export interface {Entity} {
  id: string;
  // 从规格书 §2.数据需求 复制字段
  created_at: string;
  updated_at: string;
}

// 列表查询参数
export interface {Entity}ListParams {
  page?: number;
  page_size?: number;
  // 从规格书 §5.API接口 复制筛选参数
}

// 创建/更新表单
export interface {Entity}FormData {
  // 从规格书 §3.UI规范 复制表单字段
}
```

#### 5.2.2 API 服务

```typescript
// features/{module}/services/{module}Api.ts

import { apiFetch, apiFetchPaginated, apiPost, apiPatch } from '@/lib/api';
import type { {Entity}, {Entity}ListParams, {Entity}FormData } from '../types';

/**
 * [模块名] API 服务
 * SoT: docs/10.module-specs/[规格书].md §5
 */

// 列表查询
export async function get{Entities}(params: {Entity}ListParams = {}) {
  return apiFetchPaginated<{Entity}>('/api/v1/{entities}', { params });
}

// 详情查询
export async function get{Entity}(id: string) {
  return apiFetch<{Entity}>(`/api/v1/{entities}/${id}`);
}

// 创建
export async function create{Entity}(data: {Entity}FormData) {
  return apiPost<{Entity}>('/api/v1/{entities}', data);
}

// 更新
export async function update{Entity}(id: string, data: Partial<{Entity}FormData>) {
  return apiPatch<{Entity}>(`/api/v1/{entities}/${id}`, data);
}
```

#### 5.2.3 数据 Hook

```typescript
// features/{module}/hooks/use{Module}.ts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/api';
import { get{Entities}, get{Entity}, create{Entity}, update{Entity} } from '../services';
import type { {Entity}ListParams, {Entity}FormData } from '../types';

/**
 * [模块名] 数据 Hook
 * SoT: docs/10.module-specs/[规格书].md
 */

// 列表查询
export function use{Entities}(params: {Entity}ListParams = {}) {
  return useQuery({
    queryKey: queryKeys.{entities}.list(params),
    queryFn: () => get{Entities}(params),
  });
}

// 详情查询
export function use{Entity}(id: string) {
  return useQuery({
    queryKey: queryKeys.{entities}.detail(id),
    queryFn: () => get{Entity}(id),
    enabled: !!id,
  });
}

// 创建 Mutation
export function useCreate{Entity}() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {Entity}FormData) => create{Entity}(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.{entities}.list() });
    },
  });
}
```

#### 5.2.3a 错误处理标准模式

> **重要**: 所有 Mutation 必须包含错误处理，使用 toast 提示用户

```typescript
// features/{module}/hooks/use{Module}.ts

import { useToast } from '@/hooks/use-toast';
import { isApiError } from '@/lib/api';

// 带完整错误处理的 Mutation
export function useCreate{Entity}() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: {Entity}FormData) => create{Entity}(data),
    onSuccess: (result) => {
      // 1. 刷新列表缓存
      queryClient.invalidateQueries({ queryKey: queryKeys.{entities}.list() });

      // 2. 成功提示
      toast({
        title: '创建成功',
        description: `${result.name} 已创建`,
      });
    },
    onError: (error) => {
      // 3. 错误处理
      if (isApiError(error)) {
        toast({
          variant: 'destructive',
          title: '创建失败',
          description: error.message,
        });
      } else {
        toast({
          variant: 'destructive',
          title: '网络错误',
          description: '请检查网络连接后重试',
        });
      }
    },
  });
}

// 在组件中使用
function CreateForm() {
  const { mutate, isPending } = useCreate{Entity}();

  const handleSubmit = (data: {Entity}FormData) => {
    mutate(data);  // 错误已在 hook 中处理
  };

  return (
    <Button onClick={() => handleSubmit(formData)} disabled={isPending}>
      {isPending ? '提交中...' : '提交'}
    </Button>
  );
}
```

**错误处理检查清单**:
- [ ] Mutation 有 `onError` 回调
- [ ] 使用 `isApiError()` 区分 API 错误和网络错误
- [ ] 错误信息使用 toast 展示
- [ ] 按钮在 `isPending` 时禁用，防止重复提交

#### 5.2.4 页面组件

```typescript
// app/(dashboard)/{module}/page.tsx
'use client';

/**
 * [模块名] 列表页
 * SoT: docs/10.module-specs/[规格书].md §3
 * 权限: [角色列表]
 */

import { use{Entities} } from '@/features/{module}/hooks';
import { DataTable } from '@/components/ui/data-table';
import { PageTemplate } from '@/components/layout/page-template';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/data-state';
import { columns } from './columns';

export default function {Entity}ListPage() {
  const { data, isLoading, error, refetch } = use{Entities}();

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} onRetry={refetch} />;
  if (!data?.items.length) return <EmptyState message="暂无数据" />;

  return (
    <PageTemplate
      title="[页面标题]"
      subtitle="[页面描述]"
    >
      <DataTable columns={columns} data={data.items} />
    </PageTemplate>
  );
}
```

#### 5.2.5 表格列定义

```typescript
// app/(dashboard)/{module}/columns.tsx
'use client';

/**
 * [模块名] 表格列定义
 * SoT: docs/10.module-specs/[规格书].md §3.UI规范
 */

import type { ColumnDef } from '@tanstack/react-table';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { format } from 'date-fns';  // 日期格式化使用 date-fns
import type { {Entity} } from '@/features/{module}/types';

export const columns: ColumnDef<{Entity}>[] = [
  {
    accessorKey: 'name',
    header: '名称',
  },
  {
    accessorKey: 'status',
    header: '状态',
    cell: ({ row }) => (
      <StatusBadge status={row.original.status} />
    ),
  },
  {
    accessorKey: 'created_at',
    header: '创建时间',
    cell: ({ row }) => format(new Date(row.original.created_at), 'yyyy-MM-dd HH:mm'),
  },
  // 从规格书 §3.UI规范 复制其他列
  // 金额格式化: new Intl.NumberFormat('zh-CN', { style: 'currency', currency: 'CNY' }).format(value)
];
```

#### 5.2.6 权限配置

> **注意**: 当前权限配置集成在 `features/auth/` 模块中。
> 页面级权限通过 `useAuth().hasPermission()` 检查。

```typescript
// 方式 1: 使用 useAuth 进行权限检查
import { useAuth } from '@/features/auth/hooks/useAuth';

function MyPage() {
  const { user, hasRole } = useAuth();

  // 角色映射 (MASTER.md v4.4 → 代码实现)
  // ceo         → (待实现)
  // supervisor  → 'data_operator'
  // pitcher     → 'media_buyer'
  // project_owner → 'project_owner'
  // finance     → 'finance'
  // account_manager → 'account_manager'
  // admin       → 'admin'

  if (!hasRole(['data_operator', 'admin'])) {
    return <AccessDenied />;
  }

  return <PageContent />;
}

// 方式 2: 路由中间件 (app/(dashboard)/layout.tsx)
// 已有权限守卫，无需额外配置
```

### 5.3 代码追溯注释规范

每个文件必须包含追溯注释：

```typescript
/**
 * [文件描述]
 * 
 * @sot docs/10.module-specs/[规格书].md
 * @master MASTER.md §[章节]
 * @permission [角色列表]
 * @phase Phase 1
 */
```

---

## 第六章 Step 5: 验收检查

### 6.1 验收检查清单

```markdown
## 验收检查: [模块名]

### 1. 规格书对齐检查
□ 所有字段与规格书 §2 一致
□ UI 布局与规格书 §3 一致
□ API 端点与规格书 §5 一致
□ 权限与规格书 §6 一致

### 2. 代码规范检查
□ 无 any 类型
□ 使用 apiFetch 调用 API
□ 使用 queryKeys 管理缓存
□ 使用 shadcn 组件
□ 遵循 Phase 1 规则（不阻断）

### 3. 复用检查
□ 未重复造轮子
□ 使用现有组件
□ 遵循模块结构

### 4. 追溯性检查
□ 每个文件有 @sot 注释
□ 类型定义有字段来源注释
□ 权限配置有规格书引用

### 5. 功能测试
□ 列表页正常加载
□ 筛选/分页正常
□ 详情页正常显示
□ 表单提交正常
□ 权限控制生效

### 6. 边界测试
□ 空数据显示 EmptyState
□ 加载中显示 LoadingState
□ 错误显示 ErrorState
□ 异常数据高亮（不阻断）
```

### 6.2 自动化测试要求

> **最低要求**: TypeScript 编译通过 + ESLint 无错误

#### 6.2.1 必须通过的检查

```bash
# 1. TypeScript 类型检查 (必须)
pnpm typecheck
# 或
npx tsc --noEmit

# 2. ESLint 检查 (必须)
pnpm lint

# 3. 构建检查 (推荐)
pnpm build
```

**检查结果要求**:
| 检查项 | 要求 | 说明 |
|--------|------|------|
| TypeScript | ✅ 0 errors | 类型错误会导致生产构建失败 |
| ESLint | ✅ 0 errors | 警告可接受，错误必须修复 |
| Build | ✅ 成功 | 确保生产环境可部署 |

#### 6.2.2 常见类型错误及修复

```typescript
// 错误 1: Property 'xxx' does not exist on type '{}'
// 修复: 添加类型断言或定义接口
const data = response.data as MyType;

// 错误 2: Argument of type 'string | undefined' is not assignable
// 修复: 添加空值检查
if (id) {
  doSomething(id);  // id 已被收窄为 string
}

// 错误 3: Type 'number' is not assignable to type 'string'
// 修复: 使用 String() 转换
const idStr = String(numericId);
```

#### 6.2.3 单元测试 (可选但推荐)

```typescript
// features/{module}/__tests__/use{Module}.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { use{Entities} } from '../hooks';

describe('use{Entities}', () => {
  it('should fetch {entities} list', async () => {
    const queryClient = new QueryClient();
    const wrapper = ({ children }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );

    const { result } = renderHook(() => use{Entities}(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.items).toBeDefined();
  });
});
```

### 6.3 验收报告模板

```markdown
## 验收报告: [模块名]

### 基本信息
- 开发日期: YYYY-MM-DD
- 规格书版本: [版本号]
- 开发者: [AI/人]

### 文件清单
| 文件 | 状态 | 行数 |
|------|------|------|
| features/{module}/types/{module}.types.ts | ✅ 新建 | XX |
| features/{module}/services/{module}Api.ts | ✅ 新建 | XX |
| features/{module}/hooks/use{Module}.ts | ✅ 新建 | XX |
| app/(dashboard)/{module}/page.tsx | ✅ 新建 | XX |
| app/(dashboard)/{module}/columns.tsx | ✅ 新建 | XX |

### 复用统计
- 直接复用: X 个组件
- 修改复用: X 个文件
- 新建: X 个文件
- 复用率: XX%

### 检查结果
| 检查项 | 结果 |
|--------|------|
| 规格书对齐 | ✅ PASS |
| 代码规范 | ✅ PASS |
| 复用检查 | ✅ PASS |
| 追溯性 | ✅ PASS |
| 功能测试 | ✅ PASS |

### 遗留问题
- (如有)

### SoT 追溯
- 规格书: docs/10.module-specs/[文件名]
- MASTER.md: §[章节]
- FRONTEND_AI_RULES: v1.1
```

---

## 第七章 快速开发指南

### 7.1 一页速查卡

```
┌─────────────────────────────────────────────────────────────────┐
│                    前端页面开发速查卡                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: 读规格书                                               │
│  ─────────────────                                              │
│  位置: docs/10.module-specs/[模块].md                           │
│  必读: §1概述 §2数据 §3UI §5API §6权限                          │
│                                                                 │
│  Step 2: 查复用                                                 │
│  ─────────────────                                              │
│  页面: app/(dashboard)/ 找相似                                  │
│  组件: components/ui/ 确认                                      │
│  Hook: features/*/hooks/ 找现成                                 │
│                                                                 │
│  Step 3: 定结构                                                 │
│  ─────────────────                                              │
│  types → services → hooks → page → columns                     │
│                                                                 │
│  Step 4: 写代码                                                 │
│  ─────────────────                                              │
│  复制模板 → 改参数 → 加注释                                     │
│                                                                 │
│  Step 5: 验收                                                   │
│  ─────────────────                                              │
│  规格书对齐 → 代码规范 → 复用检查 → 追溯性                      │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  禁止事项                                                       │
│  ─────────────────                                              │
│  ✗ 不读规格书直接开发                                           │
│  ✗ 重复造轮子（不查复用）                                       │
│  ✗ 使用 any 类型                                                │
│  ✗ 直接 fetch（必须用 apiFetch）                                │
│  ✗ Phase 1 阻断用户操作                                         │
│  ✗ 无追溯注释                                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 模块优先级与开发顺序

```
P0 (必须先完成)
├── A1-dashboard.md        老板驾驶舱
├── A2-fund-overview.md    资金总览
├── A3-project-pnl.md      项目盈亏
└── C1-project-mgmt.md     项目管理

P1 (第二批)
├── B1-topup-approval.md   充值审批
├── B2-daily-report-review.md 日报审核
└── C3-spend-detail.md     消耗明细

P2 (第三批)
├── B3-weekly-brief.md     周度简报
├── C2-pitcher-mgmt.md     投手管理
└── D1-monthly-settlement.md 月度结算
```

### 7.3 开发命令速查

```bash
# 1. 类型检查
pnpm typecheck

# 2. 启动开发服务器
pnpm dev

# 3. 代码格式化
pnpm format

# 4. 构建检查
pnpm build
```

---

## 第八章 示例：日报审核页开发

### 8.1 Step 1: 读规格书

```markdown
## 规格书摘要: 日报审核

### 1. 业务目标
- 解决什么问题: 主管审核投手提交的日报数据
- 目标用户: supervisor (代码: data_operator), ceo (待实现)

### 2. 数据需求
- 主数据源: daily_reports 表
- 核心字段: id, date, project_id, pitcher_id, conversions, spend, status
- 计算字段: CPL = spend / conversions

### 3. UI 布局
- 页面类型: 列表页 + 操作
- 主要组件: DataTable, StatusBadge, Button

### 4. API 接口
- GET /api/v1/daily-reports?status=pending_review
- POST /api/v1/daily-reports/{id}/review

### 5. 权限要求
- 可访问角色: data_operator (主管), admin
- 特殊权限: daily_report:review
- 角色映射: supervisor → data_operator (参见 §5.2.6)

### 6. SoT 追溯
- 规格书: docs/10.module-specs/B2-daily-report-review.md
- MASTER.md: §3.1 Phase 1, §6.5 日报审核
- STATE_MACHINE.md: §8 日报状态机
```

### 8.2 Step 2: 查复用

> **已验证**: 以下路径已于 2025-12-23 通过 Read 工具确认存在

```markdown
## 复用映射表: 日报审核

### 1. 相似页面
| 需求 | 复用来源 | 复用程度 | 验证状态 |
|------|----------|----------|----------|
| 列表页 | features/daily-reports/components/DailyReportsPage.tsx | 95% | ✅ 已验证 |

### 2. 可复用组件
| 组件 | 复用来源 | 验证状态 |
|------|----------|----------|
| DataTable | components/ui/data-table/ | ✅ 已验证 |
| StatusBadge | features/daily-reports/components/StatusBadge.tsx | ✅ 已验证 |
| ActionButtons | features/daily-reports/components/ActionButtons.tsx | ✅ 已验证 |
| FlagTrendDialog | features/daily-reports/components/FlagTrendDialog.tsx | ✅ 已验证 |

### 3. 可复用 Hook
| Hook | 复用来源 | 验证状态 |
|------|----------|----------|
| useDailyReports | features/daily-reports/hooks/useDailyReports.ts | ✅ 已验证 |
| useDailyReportActions | features/daily-reports/hooks/useDailyReportActions.ts | ✅ 已验证 |
| useAuth | features/auth/hooks/useAuth.ts | ✅ 已验证 |

### 4. 实际模块结构 (已验证)
```
features/daily-reports/
├── index.ts
├── components/
│   ├── index.ts
│   ├── DailyReportsPage.tsx       # 列表页主组件
│   ├── DailyReportsTable.tsx      # 表格组件
│   ├── DailyReportDetail.tsx      # 详情组件
│   ├── DailyReportForm.tsx        # 表单组件
│   ├── StatusBadge.tsx            # 状态徽章
│   ├── ActionButtons.tsx          # 操作按钮
│   ├── FlagTrendDialog.tsx        # 标记趋势对话框
│   ├── ResolveFlagDialog.tsx      # 解决标记对话框
│   └── ConfirmFinalDialog.tsx     # 确认最终对话框
├── hooks/
│   ├── index.ts
│   ├── useDailyReports.ts         # 数据查询 Hook
│   └── useDailyReportActions.ts   # 操作 Hook
├── services/
│   ├── index.ts
│   └── dailyReportsApi.ts         # API 调用
└── types/
    ├── index.ts
    └── dailyReport.types.ts       # 类型定义
```

### 5. 复用统计
- 复用率: 85%
```

### 8.3 Step 3: 定结构

```markdown
## 文件清单: 日报审核

### 需要创建
1. app/(dashboard)/daily-reports/review/page.tsx (基于 DailyReportsPage.tsx 模式)

### 需要修改
1. features/daily-reports/services/dailyReportsApi.ts (添加 reviewDailyReport)
2. features/daily-reports/hooks/useDailyReportActions.ts (添加 useReviewDailyReport)

### 已存在可直接使用
1. features/daily-reports/components/StatusBadge.tsx
2. features/daily-reports/hooks/useDailyReports.ts
3. features/daily-reports/types/dailyReport.types.ts
```

### 8.4 Step 4: 写代码

```typescript
// app/(dashboard)/daily-reports/review/page.tsx
'use client';

/**
 * 日报审核页
 * @sot docs/10.module-specs/B2-daily-report-review.md
 * @master MASTER.md §6.5
 * @permission data_operator, admin (业务角色: supervisor)
 * @phase Phase 1
 */

import { useDailyReports } from '@/features/daily-reports/hooks';
import { DataTable } from '@/components/ui/data-table';
import { PageTemplate } from '@/components/layout/page-template';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/data-state';
import { columns } from './columns';

export default function DailyReportReviewPage() {
  // 只查询待审核的日报
  const { data, isLoading, error, refetch } = useDailyReports({
    status: 'trend_pending',
  });

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} onRetry={refetch} />;
  if (!data?.items.length) return <EmptyState message="暂无待审核日报" />;

  return (
    <PageTemplate
      title="日报审核"
      subtitle="审核投手提交的日报数据"
    >
      <DataTable columns={columns} data={data.items} />
    </PageTemplate>
  );
}
```

### 8.5 Step 5: 验收

```markdown
## 验收报告: 日报审核

### 检查结果
| 检查项 | 结果 |
|--------|------|
| 规格书对齐 | ✅ PASS |
| 代码规范 | ✅ PASS |
| 复用检查 | ✅ 复用率 85% |
| 追溯性 | ✅ 所有文件有注释 |
| 功能测试 | ✅ PASS |

### SoT 追溯
- 规格书: docs/10.module-specs/B2-daily-report-review.md
- MASTER.md: §3.1, §6.5
- STATE_MACHINE.md: §8
```

---

## 附录 A: 追溯矩阵模板

```markdown
## 追溯矩阵: [模块名]

| 代码文件 | 规格书章节 | MASTER.md | 其他 SoT |
|----------|------------|-----------|----------|
| types/{module}.types.ts | §2 数据需求 | - | DATA_SCHEMA.md |
| services/{module}Api.ts | §5 API 接口 | - | API_SOT.md |
| hooks/use{Module}.ts | §5 API 接口 | - | - |
| page.tsx | §3 UI 规范 | §6 页面定义 | - |
| columns.tsx | §3 UI 规范 | - | - |
| permissions.ts | §6 权限 | §2.4 角色 | AUTH_SPEC.md |
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.3 | 2025-12-23 | P2 优化: 职责边界说明、占位符规则、复用验证、示例对齐实际代码 |
| v1.2 | 2025-12-23 | P1 增强: queryKeys 模板、Mock 策略、测试要求、错误处理模板 |
| v1.1 | 2025-12-23 | P0 缺陷修复: PageTemplate props、date-fns、角色映射、权限配置 |
| v1.0 | 2025-12-23 | 初始版本 |

---

**文档维护者**: AI 编程助手
**生效范围**: 所有前端页面开发任务
**前置文档**: FRONTEND_AI_RULES_v1.1.md, 10.module-specs/*.md
