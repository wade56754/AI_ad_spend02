# TypeScript 技能 - 核心指令

> **技术栈**: Next.js 16 + TanStack Query v5 + shadcn/ui

## 必须遵守的规范

### 'use client' 指令

```typescript
// 所有交互组件必须在首行添加
'use client';

import { useState } from 'react';
// ...
```

### API 调用 (禁止 fetch/axios)

```typescript
// SoT: .cursorrules#API调用规范
import { apiGet, apiPost } from '@/lib/api';

// ✅ 正确
const data = await apiGet('/api/v1/reports');
const result = await apiPost('/api/v1/reports', { data });

// ❌ 错误
// fetch('/api/reports')
// axios.get('/api/reports')
```

### TanStack Query 使用

```typescript
import { useQuery, useMutation } from '@tanstack/react-query';

// 查询
const { data, isLoading, error } = useQuery({
  queryKey: ['reports', projectId],
  queryFn: () => apiGet(`/api/v1/reports?project_id=${projectId}`),
});

// 变更
const mutation = useMutation({
  mutationFn: (data) => apiPost('/api/v1/reports', data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['reports'] });
  },
});
```

### 组件规范 (禁止裸 HTML)

```typescript
// SoT: .cursorrules#前端组件规范

// ✅ 使用 shadcn/ui 组件
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { DataTable } from '@/components/DataTable';

// ❌ 禁止裸 HTML
// <button>, <input>, <table>, <select>, <textarea>
```

### 导入顺序

```typescript
// 1. React/Next.js
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

// 2. 第三方库
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';

// 3. UI 组件
import { Button } from '@/components/ui/button';
import { DataTable } from '@/components/DataTable';

// 4. 本地 hooks/services
import { useAuth } from '@/hooks/useAuth';
import { apiGet } from '@/lib/api';

// 5. 类型
import type { Report } from '@/types';

// 6. 样式/常量
import { REPORT_STATUS_COLORS } from '@/constants';
```

### 类名合并

```typescript
import { cn } from '@/lib/utils';

// ✅ 使用 cn() 合并类名
<div className={cn('base-class', isActive && 'active-class')} />
```

## 反模式检查表

| 反模式 | 正确做法 |
|--------|---------|
| `<button>` | `<Button>` from shadcn/ui |
| `<table>` | `<DataTable>` |
| `fetch('/api')` | `apiGet('/api/v1/...')` |
| 无 'use client' | 交互组件首行加 'use client' |
| 使用 `any` 类型 | 定义明确类型 |
