# Next.js 项目模板

## 技术栈

| 组件 | 版本 | 说明 |
|------|------|------|
| Next.js | 16 | React 框架 (App Router) |
| TypeScript | 5.x | 类型安全 |
| TanStack Query | v5 | 服务端状态管理 |
| shadcn/ui | latest | UI 组件库 |
| Tailwind CSS | 3.x | 样式 |
| Supabase Auth | latest | 认证 |

## 项目结构

```
frontend/src/
├── app/                    # Next.js App Router
│   ├── (auth)/            # 认证相关页面
│   │   ├── login/
│   │   └── signup/
│   ├── (dashboard)/       # 仪表盘页面 (需登录)
│   │   ├── {feature}/
│   │   └── layout.tsx
│   ├── layout.tsx         # 根布局
│   └── page.tsx           # 首页
├── components/
│   ├── ui/                # shadcn/ui 组件
│   └── {feature}/         # 业务组件
├── features/
│   └── {feature}/
│       ├── api.ts         # API 调用
│       ├── hooks.ts       # React Hooks
│       ├── types.ts       # 类型定义
│       └── components/    # 功能组件
├── lib/
│   ├── api.ts             # API 客户端
│   └── utils.ts           # 工具函数
└── types/
    └── common.ts          # 通用类型
```

## 代码规范

### 类型定义
```typescript
// features/{feature}/types.ts

export interface {Model} {
  id: number;
  name: string;
  status: {Model}Status;
  created_at: string;
  updated_at: string | null;
}

export type {Model}Status = 
  | 'draft' 
  | 'pending' 
  | 'approved' 
  | 'rejected';

export interface {Model}CreateInput {
  name: string;
}

export interface {Model}UpdateInput {
  name?: string;
}

export interface {Model}ListParams {
  page?: number;
  limit?: number;
  status?: {Model}Status;
}
```

### API 调用
```typescript
// features/{feature}/api.ts
import { apiGet, apiPost, apiPut, apiDelete } from '@/lib/api';
import type { {Model}, {Model}CreateInput, {Model}ListParams } from './types';

export const {model}Api = {
  list: (params?: {Model}ListParams) => 
    apiGet<{Model}[]>('/api/v1/{models}', { params }),
  
  get: (id: number) => 
    apiGet<{Model}>(`/api/v1/{models}/${id}`),
  
  create: (data: {Model}CreateInput) =>
    apiPost<{Model}>('/api/v1/{models}', data),
  
  update: (id: number, data: {Model}UpdateInput) =>
    apiPut<{Model}>(`/api/v1/{models}/${id}`, data),
  
  delete: (id: number) =>
    apiDelete(`/api/v1/{models}/${id}`),
};
```

### React Hooks
```typescript
// features/{feature}/hooks.ts
'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { {model}Api } from './api';
import type { {Model}CreateInput, {Model}ListParams } from './types';

// 查询 Hook
export function use{Model}s(params?: {Model}ListParams) {
  return useQuery({
    queryKey: ['{models}', params],
    queryFn: () => {model}Api.list(params),
  });
}

export function use{Model}(id: number) {
  return useQuery({
    queryKey: ['{models}', id],
    queryFn: () => {model}Api.get(id),
    enabled: !!id,
  });
}

// 变更 Hook
export function useCreate{Model}() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: {Model}CreateInput) => {model}Api.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['{models}'] });
    },
  });
}

export function useUpdate{Model}() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: {Model}UpdateInput }) => 
      {model}Api.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['{models}'] });
      queryClient.invalidateQueries({ queryKey: ['{models}', variables.id] });
    },
  });
}

export function useDelete{Model}() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: number) => {model}Api.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['{models}'] });
    },
  });
}
```

### 页面组件
```tsx
// app/(dashboard)/{models}/page.tsx
'use client';

import { use{Model}s } from '@/features/{model}/hooks';
import { {Model}Table } from '@/features/{model}/components/{Model}Table';
import { {Model}CreateDialog } from '@/features/{model}/components/{Model}CreateDialog';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/PageHeader';
import { DataState } from '@/components/DataState';

export default function {Model}sPage() {
  const { data, isLoading, error } = use{Model}s();
  
  return (
    <div className="space-y-6">
      <PageHeader
        title="{Model}管理"
        description="管理系统中的{model}"
      >
        <{Model}CreateDialog>
          <Button>新建{Model}</Button>
        </{Model}CreateDialog>
      </PageHeader>
      
      <DataState
        isLoading={isLoading}
        error={error}
        isEmpty={!data?.length}
        emptyMessage="暂无数据"
      >
        <{Model}Table data={data || []} />
      </DataState>
    </div>
  );
}
```

### 表格组件
```tsx
// features/{model}/components/{Model}Table.tsx
'use client';

import { DataTable } from '@/components/ui/data-table';
import { StatusBadge } from '@/components/StatusBadge';
import type { {Model} } from '../types';
import type { ColumnDef } from '@tanstack/react-table';

const columns: ColumnDef<{Model}>[] = [
  {
    accessorKey: 'id',
    header: 'ID',
  },
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
    cell: ({ row }) => new Date(row.original.created_at).toLocaleString(),
  },
];

interface {Model}TableProps {
  data: {Model}[];
}

export function {Model}Table({ data }: {Model}TableProps) {
  return <DataTable columns={columns} data={data} />;
}
```

## 组件规范

### 必须使用 shadcn/ui
```tsx
// ✅ 正确
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog } from '@/components/ui/dialog';

// ❌ 错误 - 不要使用原生 HTML
<button>点击</button>
<input type="text" />
```

### 客户端组件
```tsx
// 需要交互的组件必须标记 'use client'
'use client';

import { useState } from 'react';
// ...
```

### 样式使用 Tailwind
```tsx
// ✅ 正确
<div className="flex items-center gap-4 p-4">

// ❌ 错误 - 不要使用内联样式
<div style={{ display: 'flex' }}>
```


