---
name: ai-ad-fe-gen
version: "2.0"
status: production
layer: Skill

sot_dependencies:
  required:
    - docs/2.sot/API_SOT.md
    - docs/2.sot/STATE_MACHINE.md
  optional:
    - docs/3.dev-guides/FRONTEND_DEVELOPMENT_RULES.md
    - docs/3.dev-guides/UI_DESIGN_SYSTEM.md
    - docs/3.dev-guides/UI_FLOW_SPEC.md

output_boundaries:
  writable:
    - frontend/src/modules/**
    - frontend/src/lib/api/**
    - frontend/tests/**
  forbidden:
    - frontend/node_modules/**
    - frontend/.next/**
    - .env*

baseline: AI_CODE_FACTORY_DEV_GUIDE_v2.0, SoT Freeze v2.6
---

# FE-Gen Skill - 前端代码生成

## 1. Purpose

前端代码生成 Skill，负责在 SoT 约束下生成 Next.js/React 前端代码。

**核心职责**:
- 根据 API 契约生成前端模块 (PageShell + hooks + components)
- 严格遵循 UI 设计系统和前端开发规范
- 生成类型安全的 TypeScript 代码

## 2. Input Contract

```typescript
interface FEGenInput {
  task: string;           // 任务描述，如 "实现充值列表页面"
  target_files: string[]; // 目标文件列表（相对于 frontend/）
  module?: string;        // 模块名称，如 "topups"
  api_contract?: string;  // API 契约内容 (可选)
  context?: {
    sot_snapshot?: Record<string, string>;  // SoT 文档内容快照
    existing_code?: Record<string, string>; // 现有代码快照
  };
}
```

**校验规则**:
- `task` 不能为空
- `target_files` 至少有一个文件
- 文件路径必须在可写区域内

## 3. Output Contract

```typescript
interface FEGenOutput {
  success: boolean;
  data?: {
    changes: Record<string, string>;  // 文件路径 -> 新内容
    notes: string[];                   // 自检说明
    sot_refs: string[];               // 引用的 SoT/规范条款
  };
  error?: string;
}
```

## 4. Constraints (必须遵守的边界)

### 4.1 代码边界

| 区域 | 权限 | 说明 |
|------|------|------|
| `frontend/src/modules/**` | ✅ 可写 | 模块化页面 |
| `frontend/src/lib/api/**` | ✅ 可写 | API 客户端封装 |
| `frontend/tests/**` | ✅ 可写 | 前端测试 |
| `frontend/node_modules/**` | ❌ 禁止 | 依赖目录 |
| `frontend/.next/**` | ❌ 禁止 | 构建产物 |

### 4.2 技术栈约束

- **框架**: Next.js 14+ (App Router)
- **UI 库**: shadcn/ui + Tailwind CSS
- **状态管理**: TanStack Query (React Query)
- **表单**: React Hook Form + Zod
- **类型**: TypeScript strict mode

### 4.3 前端开发规范

1. **模块结构**:
   ```
   src/modules/{module}/
   ├── {Module}PageShell.tsx     # 页面整体布局
   ├── hooks/
   │   ├── use{Module}Filters.ts # 筛选状态
   │   └── use{Module}Data.ts    # 数据获取
   ├── components/
   │   ├── {Module}Table.tsx     # 表格组件
   │   └── {Module}Card.tsx      # 卡片组件
   ├── types/
   │   └── {module}.types.ts     # 类型定义
   └── services/
       └── {module}Api.ts        # API 调用
   ```

2. **命名规范**:
   - 组件: PascalCase (`TopupTable.tsx`)
   - hooks: camelCase with `use` prefix (`useTopupData.ts`)
   - 类型文件: kebab-case (`topup.types.ts`)
   - API 文件: camelCase (`topupsApi.ts`)

3. **状态枚举**: 必须与 `STATE_MACHINE.md` 定义一致

## 5. Prompt Template

```xml
<SYSTEM>
你是"前端开发 Agent"，负责在现有 Next.js + React + TypeScript 项目中实现/重构前端模块。

必须遵守的规则：
1. API_SOT / STATE_MACHINE 作为唯一事实来源
2. 遵循 FRONTEND_DEVELOPMENT_RULES 和 UI_DESIGN_SYSTEM
3. 使用 shadcn/ui 组件库和 Tailwind CSS
4. 使用 TanStack Query 管理服务端状态
5. 严格类型标注，禁止使用 any
6. 必须在注释中标注 SoT 引用

技术栈假设：
- Next.js 14+ (App Router)
- React 18+
- TypeScript 5+
- TanStack Query v5
- shadcn/ui + Tailwind CSS
</SYSTEM>

<CONTEXT>
<DOC name="API_SOT">
{{API_SOT}}
</DOC>

<DOC name="STATE_MACHINE">
{{STATE_MACHINE}}
</DOC>

<DOC name="FRONTEND_RULES" optional="true">
{{FRONTEND_RULES}}
</DOC>

<DOC name="UI_DESIGN_SYSTEM" optional="true">
{{UI_DESIGN_SYSTEM}}
</DOC>

<DOC name="UI_FLOW_SPEC" optional="true">
{{UI_FLOW_SPEC}}
</DOC>

<API_CONTRACT optional="true">
{{API_CONTRACT}}
</API_CONTRACT>

<EXISTING_FILES>
{{EXISTING_FILES}}
</EXISTING_FILES>
</CONTEXT>

<TASK>
{{TASK}}
</TASK>

<THINKING_CHAIN>
请按以下步骤思考：

1. **API 契约分析**
   - 从 API_SOT 或 API_CONTRACT 定位需要对接的接口
   - 确定请求参数和响应类型
   - 识别分页、筛选、排序参数

2. **状态机分析**
   - 从 STATE_MACHINE 确认状态枚举定义
   - 确定状态显示样式（颜色、图标、文案）

3. **模块结构规划**
   - 确定需要创建/修改的文件
   - 规划组件层次结构
   - 设计 hooks 和数据流

4. **代码生成**
   - 生成类型定义 (types/)
   - 生成 API 服务 (services/)
   - 生成数据 hooks (hooks/)
   - 生成 UI 组件 (components/)
   - 生成页面骨架 (PageShell)

5. **自检**
   - 检查类型是否完整
   - 检查状态枚举是否与 STATE_MACHINE 一致
   - 检查是否遵循 UI 设计规范
   - 检查是否有禁区代码
</THINKING_CHAIN>

<OUTPUT_FORMAT>
只输出一段 JSON，格式如下：

{
  "changes": [
    {
      "file": "frontend/src/modules/topups/types/topup.types.ts",
      "content": "完整的文件内容"
    },
    {
      "file": "frontend/src/modules/topups/services/topupsApi.ts",
      "content": "完整的文件内容"
    },
    {
      "file": "frontend/src/modules/topups/hooks/useTopupData.ts",
      "content": "完整的文件内容"
    },
    {
      "file": "frontend/src/modules/topups/components/TopupTable.tsx",
      "content": "完整的文件内容"
    },
    {
      "file": "frontend/src/modules/topups/TopupsPageShell.tsx",
      "content": "完整的文件内容"
    }
  ],
  "notes": [
    "自检说明1",
    "自检说明2"
  ],
  "sot_refs": [
    "API_SOT.md#topups",
    "STATE_MACHINE.md#topup",
    "UI_DESIGN_SYSTEM.md#table"
  ]
}
</OUTPUT_FORMAT>
```

## 6. Code Templates

### 6.1 类型定义模板

```typescript
// frontend/src/modules/topups/types/topup.types.ts

/**
 * Topup 类型定义
 * SoT: STATE_MACHINE.md#topup, DATA_SCHEMA.md#topups
 */

// 状态枚举 - 对齐 STATE_MACHINE.md#topup
export type TopupStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "executed"
  | "failed";

// 充值记录
export interface Topup {
  id: string;
  amount: number;
  status: TopupStatus;
  created_at: string;
  approved_by?: string;
  approved_at?: string;
}

// 列表响应
export interface TopupListResponse {
  items: Topup[];
  total: number;
  page: number;
  page_size: number;
}

// 筛选参数
export interface TopupFilters {
  status?: TopupStatus;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}
```

### 6.2 API 服务模板

```typescript
// frontend/src/modules/topups/services/topupsApi.ts

import { apiFetch } from "@/lib/api/apiFetch";
import type { Topup, TopupListResponse, TopupFilters } from "../types/topup.types";

/**
 * Topups API 服务
 * SoT: API_SOT.md#topups
 */

const BASE_URL = "/api/v1/topups";

export const topupsApi = {
  // 获取列表
  async list(filters: TopupFilters = {}): Promise<TopupListResponse> {
    const params = new URLSearchParams();
    if (filters.status) params.set("status", filters.status);
    if (filters.page) params.set("page", String(filters.page));
    if (filters.page_size) params.set("page_size", String(filters.page_size));

    return apiFetch<TopupListResponse>(`${BASE_URL}?${params.toString()}`);
  },

  // 获取详情
  async get(id: string): Promise<Topup> {
    return apiFetch<Topup>(`${BASE_URL}/${id}`);
  },

  // 审批
  async approve(id: string, comment?: string): Promise<Topup> {
    return apiFetch<Topup>(`${BASE_URL}/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ comment }),
    });
  },

  // 拒绝
  async reject(id: string, reason: string): Promise<Topup> {
    return apiFetch<Topup>(`${BASE_URL}/${id}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    });
  },
};
```

### 6.3 数据 Hook 模板

```typescript
// frontend/src/modules/topups/hooks/useTopupData.ts

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { topupsApi } from "../services/topupsApi";
import type { TopupFilters } from "../types/topup.types";

/**
 * Topup 数据 Hook
 * 使用 TanStack Query 管理服务端状态
 */

// Query Keys
export const topupKeys = {
  all: ["topups"] as const,
  lists: () => [...topupKeys.all, "list"] as const,
  list: (filters: TopupFilters) => [...topupKeys.lists(), filters] as const,
  details: () => [...topupKeys.all, "detail"] as const,
  detail: (id: string) => [...topupKeys.details(), id] as const,
};

// 列表查询
export function useTopupList(filters: TopupFilters = {}) {
  return useQuery({
    queryKey: topupKeys.list(filters),
    queryFn: () => topupsApi.list(filters),
  });
}

// 详情查询
export function useTopupDetail(id: string) {
  return useQuery({
    queryKey: topupKeys.detail(id),
    queryFn: () => topupsApi.get(id),
    enabled: !!id,
  });
}

// 审批 Mutation
export function useApproveTopup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, comment }: { id: string; comment?: string }) =>
      topupsApi.approve(id, comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: topupKeys.lists() });
    },
  });
}

// 拒绝 Mutation
export function useRejectTopup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      topupsApi.reject(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: topupKeys.lists() });
    },
  });
}
```

### 6.4 表格组件模板

```tsx
// frontend/src/modules/topups/components/TopupTable.tsx

"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Topup, TopupStatus } from "../types/topup.types";

/**
 * Topup 表格组件
 * SoT: UI_DESIGN_SYSTEM.md#table
 */

interface TopupTableProps {
  data: Topup[];
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
  isLoading?: boolean;
}

// 状态样式映射 - 对齐 STATE_MACHINE.md#topup
const statusConfig: Record<TopupStatus, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  pending: { label: "待审批", variant: "outline" },
  approved: { label: "已审批", variant: "default" },
  rejected: { label: "已拒绝", variant: "destructive" },
  executed: { label: "已执行", variant: "secondary" },
  failed: { label: "失败", variant: "destructive" },
};

export function TopupTable({ data, onApprove, onReject, isLoading }: TopupTableProps) {
  if (isLoading) {
    return <div className="text-center py-8">加载中...</div>;
  }

  if (!data.length) {
    return <div className="text-center py-8 text-muted-foreground">暂无数据</div>;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>ID</TableHead>
          <TableHead>金额</TableHead>
          <TableHead>状态</TableHead>
          <TableHead>创建时间</TableHead>
          <TableHead>操作</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((topup) => {
          const status = statusConfig[topup.status];
          return (
            <TableRow key={topup.id}>
              <TableCell className="font-mono text-sm">
                {topup.id.slice(0, 8)}...
              </TableCell>
              <TableCell>¥{topup.amount.toLocaleString()}</TableCell>
              <TableCell>
                <Badge variant={status.variant}>{status.label}</Badge>
              </TableCell>
              <TableCell>
                {new Date(topup.created_at).toLocaleString("zh-CN")}
              </TableCell>
              <TableCell>
                {topup.status === "pending" && (
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => onApprove?.(topup.id)}
                    >
                      审批
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onReject?.(topup.id)}
                    >
                      拒绝
                    </Button>
                  </div>
                )}
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
```

### 6.5 页面骨架模板

```tsx
// frontend/src/modules/topups/TopupsPageShell.tsx

"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { TopupTable } from "./components/TopupTable";
import { useTopupList, useApproveTopup, useRejectTopup } from "./hooks/useTopupData";
import type { TopupStatus, TopupFilters } from "./types/topup.types";

/**
 * 充值管理页面
 * SoT: UI_FLOW_SPEC.md#topup-management
 */

export function TopupsPageShell() {
  const [filters, setFilters] = useState<TopupFilters>({
    page: 1,
    page_size: 20,
  });

  const { data, isLoading, error } = useTopupList(filters);
  const approveMutation = useApproveTopup();
  const rejectMutation = useRejectTopup();

  const handleStatusChange = (status: string) => {
    setFilters((prev) => ({
      ...prev,
      status: status === "all" ? undefined : (status as TopupStatus),
      page: 1,
    }));
  };

  const handleApprove = (id: string) => {
    approveMutation.mutate({ id });
  };

  const handleReject = (id: string) => {
    const reason = prompt("请输入拒绝原因");
    if (reason) {
      rejectMutation.mutate({ id, reason });
    }
  };

  if (error) {
    return (
      <div className="text-center py-8 text-destructive">
        加载失败: {error.message}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">充值管理</h1>
      </div>

      {/* 筛选条 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">筛选条件</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Select
              value={filters.status ?? "all"}
              onValueChange={handleStatusChange}
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                <SelectItem value="pending">待审批</SelectItem>
                <SelectItem value="approved">已审批</SelectItem>
                <SelectItem value="rejected">已拒绝</SelectItem>
                <SelectItem value="executed">已执行</SelectItem>
                <SelectItem value="failed">失败</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* 数据表格 */}
      <Card>
        <CardContent className="pt-6">
          <TopupTable
            data={data?.items ?? []}
            isLoading={isLoading}
            onApprove={handleApprove}
            onReject={handleReject}
          />
        </CardContent>
      </Card>

      {/* 分页信息 */}
      {data && (
        <div className="text-sm text-muted-foreground text-center">
          共 {data.total} 条记录，第 {data.page} / {Math.ceil(data.total / data.page_size)} 页
        </div>
      )}
    </div>
  );
}
```

## 7. Self-Check Checklist

| 检查项 | 验证方法 | P0/P1 |
|--------|---------|-------|
| 类型完整性 | 无 any 类型 | P0 |
| 状态枚举一致性 | 对比 STATE_MACHINE.md | P0 |
| API 对接正确性 | 对比 API_SOT.md | P0 |
| 禁区检查 | 不生成 node_modules/.next | P0 |
| UI 组件使用 | 使用 shadcn/ui | P1 |
| Hook 命名规范 | use 前缀 | P1 |
| 错误处理 | 有 error 状态展示 | P1 |

## 8. Version History

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0 | 2025-12-06 | 重构：对齐 AI_CODE_FACTORY_DEV_GUIDE_v2.0，增加完整代码模板 |
| v1.0 | 2025-11-01 | 初始版本 |

---

**文档控制**: Owner: wade | Baseline: AI_CODE_FACTORY_DEV_GUIDE_v2.0
