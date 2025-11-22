# 前端开发规范 v2.0 (Production-Ready)

**文档版本**: v2.0
**发布日期**: 2025-01-20
**审查状态**: ✅ 已通过架构审查
**维护团队**: 前端架构团队
**适用范围**: Next.js 16 App Router + TypeScript 5.x

---

## 📋 目录

- [1. 技术栈](#1-技术栈)
- [2. 项目结构](#2-项目结构)
- [3. 认证与授权架构](#3-认证与授权架构)
- [4. API Client 分层设计](#4-api-client-分层设计)
- [5. Provider 结构](#5-provider-结构)
- [6. 中间件与路由守卫](#6-中间件与路由守卫)
- [7. 状态管理](#7-状态管理)
- [8. 数据获取策略](#8-数据获取策略)
- [9. 表单开发](#9-表单开发)
- [10. 错误处理](#10-错误处理)
- [11. 组件开发规范](#11-组件开发规范)
- [12. 样式规范](#12-样式规范)
- [13. TypeScript 规范](#13-typescript-规范)
- [14. 环境变量](#14-环境变量)
- [15. 性能优化](#15-性能优化)
- [16. 测试规范](#16-测试规范)
- [17. 开发铁律](#17-开发铁律)

---

## 1. 技术栈

### 1.1 核心框架（锁定版本）

| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 16.x (App Router) | 全栈框架 |
| React | 19.x | UI 库 |
| TypeScript | 5.x | 类型系统 |
| Node.js | ≥ 20.x | 运行时 |

### 1.2 状态管理

| 技术 | 用途 | 禁止场景 |
|------|------|---------|
| **SWR** | 服务端数据缓存 | ❌ 不用于 UI 状态 |
| **Zustand** | 客户端 UI 状态 | ❌ 不用于 API 数据 |
| **React Context** | 跨组件传递（主题、国际化） | ❌ 不用于频繁变更的数据 |

### 1.3 UI 组件

- **shadcn/ui** (基于 Radix UI)
- **Tailwind CSS** 3.4+
- **Lucide React** (图标)

### 1.4 表单与验证

- **React Hook Form** 7.x
- **Zod** 3.x (与后端 Pydantic Schema 对齐)

---

## 2. 项目结构

```
frontend/
├── app/
│   ├── (auth)/              # 路由组: 公开页面
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── layout.tsx
│   ├── (dashboard)/         # 路由组: 需认证
│   │   ├── layout.tsx       # 共享布局 + 认证检查
│   │   ├── projects/
│   │   │   ├── page.tsx
│   │   │   └── [id]/
│   │   │       └── page.tsx
│   │   ├── ad-accounts/
│   │   └── topups/
│   ├── api/                 # API Routes (优先用 Server Actions)
│   │   └── auth/
│   ├── layout.tsx           # 根布局 (Providers)
│   ├── providers.tsx        # 🆕 Client-only providers
│   ├── error.tsx
│   └── not-found.tsx
│
├── components/
│   ├── ui/                  # shadcn/ui 组件
│   ├── features/            # 业务组件
│   │   ├── projects/
│   │   ├── ad-accounts/
│   │   └── topups/
│   ├── layouts/
│   │   ├── DashboardLayout.tsx
│   │   └── Sidebar.tsx
│   └── shared/
│       ├── ErrorBoundary.tsx
│       └── LoadingSpinner.tsx
│
├── lib/
│   ├── api/                 # 🆕 API Client 分层
│   │   ├── server.ts        # Server Components 专用
│   │   ├── client.ts        # Client Components 专用
│   │   └── types.ts         # 共享类型
│   ├── auth/                # 🆕 认证工具
│   │   ├── session.ts       # 服务端 session 操作
│   │   └── client.ts        # 客户端认证逻辑
│   ├── utils.ts
│   ├── cn.ts
│   └── validators.ts        # Zod schemas
│
├── hooks/
│   ├── useAuth.ts           # 客户端认证 hook
│   ├── useProjects.ts       # SWR 封装
│   └── useMounted.ts        # 🆕 SSR 安全 hook
│
├── stores/
│   ├── authStore.ts         # 🆕 SSR-safe
│   └── uiStore.ts
│
├── types/
│   ├── api.ts
│   ├── models.ts
│   └── enums.ts
│
├── middleware.ts            # 🆕 路由守卫
├── .env.local
├── .env.example
└── next.config.ts
```

---

## 3. 认证与授权架构

### 3.1 认证策略（httpOnly Cookie 优先）

#### 3.1.1 登录流程

```
用户登录
  ↓
后端验证成功
  ↓
返回 { access_token, refresh_token }
  ↓
前端存储：
  - httpOnly Cookie (主要) ← 推荐
  - localStorage (降级方案)
  ↓
Middleware 自动验证
```

#### 3.1.2 Token 存储策略

| 方案 | 安全性 | 使用场景 |
|------|--------|---------|
| **httpOnly Cookie** | ✅ 高（防 XSS） | 生产环境推荐 |
| **localStorage** | ⚠️ 中（易受 XSS 攻击） | 开发环境 / 移动端 |

**生产环境配置** (后端):
```python
# FastAPI 设置 Cookie
response.set_cookie(
    key="access_token",
    value=token,
    httponly=True,  # 防止 JS 访问
    secure=True,    # 仅 HTTPS
    samesite="lax", # CSRF 防护
    max_age=900     # 15分钟
)
```

**前端读取** (自动携带):
```typescript
// Server Components: cookies 自动携带
// Client Components: fetch 自动携带（credentials: 'include'）
```

---

### 3.2 服务端 Session 操作

```typescript
// lib/auth/session.ts (Server-only)
import { cookies } from 'next/headers';

/**
 * 获取服务端 session token
 * 仅在 Server Components / Server Actions / Middleware 中使用
 */
export async function getServerSession(): Promise<string | null> {
  const cookieStore = await cookies();
  return cookieStore.get('access_token')?.value || null;
}

/**
 * 清除 session (登出)
 */
export async function clearServerSession() {
  const cookieStore = await cookies();
  cookieStore.delete('access_token');
  cookieStore.delete('refresh_token');
}
```

---

### 3.3 客户端 Auth Store (SSR-safe)

```typescript
// stores/authStore.ts
'use client';

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

export interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'finance' | 'data_operator' | 'account_manager' | 'media_buyer';
}

interface AuthState {
  user: User | null;
  token: string | null;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      setAuth: (user, token) => set({ user, token }),
      clearAuth: () => set({ user: null, token: null }),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => {
        // ✅ SSR 安全检查
        if (typeof window === 'undefined') {
          return {
            getItem: () => null,
            setItem: () => {},
            removeItem: () => {},
          };
        }
        return localStorage;
      }),
    }
  )
);

/**
 * 获取客户端 session (非 Hook 版本)
 * ⚠️ 仅在浏览器环境调用
 */
export function getClientSession() {
  if (typeof window === 'undefined') {
    return { user: null, token: null };
  }
  return useAuthStore.getState();
}
```

---

## 4. API Client 分层设计

### 4.1 架构原则

```
┌─────────────────────────────────────────┐
│   Server Components / Server Actions   │
│   使用 lib/api/server.ts               │
│   Token 来源: cookies()                │
└─────────────────────────────────────────┘
                  ↓
        ┌─────────────────┐
        │  Backend API    │
        └─────────────────┘
                  ↑
┌─────────────────────────────────────────┐
│      Client Components                 │
│      使用 lib/api/client.ts            │
│      Token 来源: Zustand / localStorage│
└─────────────────────────────────────────┘
```

---

### 4.2 服务端 API Client

```typescript
// lib/api/server.ts
import { cookies } from 'next/headers';

const API_BASE = process.env.NEXT_PUBLIC_API_URL!;

export class ServerApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string
  ) {
    super(message);
    this.name = 'ServerApiError';
  }
}

/**
 * 服务端 API 请求
 * ✅ 仅在 Server Components / Server Actions / Route Handlers 使用
 * ✅ 自动从 cookies 获取 token
 */
export async function serverFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const cookieStore = await cookies();
  const token = cookieStore.get('access_token')?.value;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
    cache: 'no-store', // 禁用缓存，使用 SWR 管理
  });

  if (!response.ok) {
    const json = await response.json().catch(() => ({}));
    throw new ServerApiError(
      response.status,
      json.code || 'UNKNOWN_ERROR',
      json.message || 'Request failed'
    );
  }

  const json = await response.json();
  return json.data as T; // 解包 Envelope
}

/**
 * GET 请求
 */
export async function serverGet<T>(
  endpoint: string,
  params?: Record<string, any>
): Promise<T> {
  const query = params ? `?${new URLSearchParams(params)}` : '';
  return serverFetch<T>(`${endpoint}${query}`, { method: 'GET' });
}

/**
 * POST 请求
 */
export async function serverPost<T>(
  endpoint: string,
  data?: any
): Promise<T> {
  return serverFetch<T>(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
```

**使用示例**:
```typescript
// app/(dashboard)/projects/page.tsx (Server Component)
import { serverGet } from '@/lib/api/server';
import type { Project } from '@/types/models';

export default async function ProjectsPage() {
  // ✅ 服务端获取数据，自动携带 cookie token
  const projects = await serverGet<Project[]>('/projects');

  return <ProjectList projects={projects} />;
}
```

---

### 4.3 客户端 API Client

```typescript
// lib/api/client.ts
'use client';

import { getClientSession } from '@/stores/authStore';

const API_BASE = process.env.NEXT_PUBLIC_API_URL!;

export class ClientApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: any
  ) {
    super(message);
    this.name = 'ClientApiError';
  }
}

/**
 * 客户端 API 请求
 * ✅ 仅在 Client Components 使用
 * ✅ 自动从 Zustand 获取 token
 * ❌ 不调用 toast（由调用方处理）
 */
export async function clientFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const { token } = getClientSession();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include', // ✅ 携带 cookies（如果后端使用 httpOnly）
  });

  if (!response.ok) {
    const json = await response.json().catch(() => ({}));
    throw new ClientApiError(
      response.status,
      json.code || 'UNKNOWN_ERROR',
      json.message || 'Request failed',
      json.data
    );
  }

  const json = await response.json();
  return json.data as T;
}

/**
 * GET 请求
 */
export async function clientGet<T>(
  endpoint: string,
  params?: Record<string, any>
): Promise<T> {
  const query = params ? `?${new URLSearchParams(params)}` : '';
  return clientFetch<T>(`${endpoint}${query}`, { method: 'GET' });
}

/**
 * POST 请求
 */
export async function clientPost<T>(
  endpoint: string,
  data?: any
): Promise<T> {
  return clientFetch<T>(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * PUT 请求
 */
export async function clientPut<T>(
  endpoint: string,
  data?: any
): Promise<T> {
  return clientFetch<T>(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

/**
 * DELETE 请求
 */
export async function clientDelete<T>(endpoint: string): Promise<T> {
  return clientFetch<T>(endpoint, { method: 'DELETE' });
}
```

**使用示例**:
```typescript
// components/features/projects/CreateProjectButton.tsx
'use client';

import { clientPost } from '@/lib/api/client';
import { toast } from 'sonner';

export function CreateProjectButton() {
  const handleCreate = async (data: any) => {
    try {
      await clientPost('/projects', data);
      toast.success('创建成功');
    } catch (error) {
      if (error instanceof ClientApiError) {
        toast.error(error.message);
      }
    }
  };

  return <Button onClick={handleCreate}>创建</Button>;
}
```

---

### 4.4 共享类型定义

```typescript
// lib/api/types.ts

/**
 * Envelope 响应格式（与后端对齐）
 */
export interface ApiResponse<T = any> {
  data: T;
  success: boolean;
  message?: string;
  code?: string;
}

/**
 * 分页响应
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
```

---

## 5. Provider 结构

### 5.1 根布局 Provider 组织

```typescript
// app/providers.tsx
'use client';

import { SWRConfig } from 'swr';
import { Toaster } from 'sonner';
import { ThemeProvider } from 'next-themes';
import type { ReactNode } from 'react';

/**
 * 全局 Provider 配置
 * ⚠️ 必须是 Client Component
 */
export function Providers({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      <SWRConfig
        value={{
          refreshInterval: 0,
          revalidateOnFocus: false,
          revalidateOnReconnect: true,
          dedupingInterval: 2000,
          shouldRetryOnError: false,
          onError: (error) => {
            console.error('SWR Error:', error);
          },
        }}
      >
        {children}
        <Toaster position="top-right" />
      </SWRConfig>
    </ThemeProvider>
  );
}
```

### 5.2 根布局引用

```typescript
// app/layout.tsx
import { Providers } from './providers';
import './globals.css';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

---

## 6. 中间件与路由守卫

### 6.1 认证中间件

```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * 需要认证的路由前缀
 */
const PROTECTED_ROUTES = ['/dashboard', '/projects', '/ad-accounts', '/topups'];

/**
 * 公开路由
 */
const PUBLIC_ROUTES = ['/login', '/register', '/forgot-password'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get('access_token')?.value;

  // 检查是否为受保护路由
  const isProtectedRoute = PROTECTED_ROUTES.some((route) =>
    pathname.startsWith(route)
  );

  // 检查是否为公开路由
  const isPublicRoute = PUBLIC_ROUTES.some((route) =>
    pathname.startsWith(route)
  );

  // 未登录访问受保护路由 → 重定向登录页
  if (isProtectedRoute && !token) {
    const url = request.nextUrl.clone();
    url.pathname = '/login';
    url.searchParams.set('callbackUrl', pathname);
    return NextResponse.redirect(url);
  }

  // 已登录访问公开路由 → 重定向仪表盘
  if (isPublicRoute && token) {
    const url = request.nextUrl.clone();
    url.pathname = '/dashboard';
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

/**
 * 配置 Middleware 匹配路径
 */
export const config = {
  matcher: [
    /*
     * 匹配所有路径除了:
     * - api (API routes)
     * - _next/static (静态文件)
     * - _next/image (图片优化)
     * - favicon.ico (图标)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
```

---

## 7. 状态管理

### 7.1 Zustand (客户端 UI 状态)

#### 7.1.1 UI Store

```typescript
// stores/uiStore.ts
'use client';

import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark' | 'system';
  toggleSidebar: () => void;
  setTheme: (theme: UIState['theme']) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  theme: 'system',
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setTheme: (theme) => set({ theme }),
}));
```

### 7.2 SWR (服务端数据)

#### 7.2.1 数据获取 Hook

```typescript
// hooks/useProjects.ts
'use client';

import useSWR from 'swr';
import { clientGet, clientPost, clientPut, clientDelete } from '@/lib/api/client';
import type { Project } from '@/types/models';

const PROJECTS_KEY = '/projects';

/**
 * 获取项目列表
 */
export function useProjects() {
  const { data, error, isLoading, mutate } = useSWR<Project[]>(
    PROJECTS_KEY,
    () => clientGet<Project[]>(PROJECTS_KEY)
  );

  return {
    projects: data,
    isLoading,
    isError: !!error,
    mutate,
  };
}

/**
 * 获取单个项目
 */
export function useProject(id: string | null) {
  const { data, error, isLoading } = useSWR<Project>(
    id ? `/projects/${id}` : null,
    () => clientGet<Project>(`/projects/${id}`)
  );

  return {
    project: data,
    isLoading,
    isError: !!error,
  };
}

/**
 * 创建项目
 */
export function useCreateProject() {
  const { mutate } = useSWR(PROJECTS_KEY);

  const createProject = async (data: Partial<Project>) => {
    const newProject = await clientPost<Project>(PROJECTS_KEY, data);
    mutate(); // 刷新列表
    return newProject;
  };

  return { createProject };
}

/**
 * 更新项目
 */
export function useUpdateProject() {
  const { mutate } = useSWR(PROJECTS_KEY);

  const updateProject = async (id: string, data: Partial<Project>) => {
    const updated = await clientPut<Project>(`/projects/${id}`, data);
    mutate();
    mutate(`/projects/${id}`, updated, false);
    return updated;
  };

  return { updateProject };
}

/**
 * 删除项目（乐观更新）
 */
export function useDeleteProject() {
  const { mutate } = useSWR(PROJECTS_KEY);

  const deleteProject = async (id: string) => {
    // 乐观更新
    mutate(
      (current) => current?.filter((p) => p.id !== id),
      false
    );

    try {
      await clientDelete(`/projects/${id}`);
      mutate(); // 重新验证
    } catch (error) {
      mutate(); // 回滚
      throw error;
    }
  };

  return { deleteProject };
}
```

---

## 8. 数据获取策略

### 8.1 Server Components (推荐)

```typescript
// app/(dashboard)/projects/page.tsx
import { serverGet } from '@/lib/api/server';
import { ProjectList } from '@/components/features/projects/ProjectList';

export default async function ProjectsPage() {
  // ✅ 服务端获取数据
  const projects = await serverGet<Project[]>('/projects');

  return (
    <div>
      <h1>项目列表</h1>
      <ProjectList initialData={projects} />
    </div>
  );
}
```

### 8.2 Client Components + SWR

```typescript
// components/features/projects/ProjectList.tsx
'use client';

import { useProjects } from '@/hooks/useProjects';

export function ProjectList({ initialData }: { initialData?: Project[] }) {
  const { projects, isLoading } = useProjects();

  // 优先使用 SWR 数据，降级到 initialData
  const data = projects || initialData;

  if (isLoading && !data) return <div>加载中...</div>;

  return (
    <div>
      {data?.map((project) => (
        <ProjectCard key={project.id} project={project} />
      ))}
    </div>
  );
}
```

### 8.3 Server Actions (表单提交)

```typescript
// app/actions/projects.ts
'use server';

import { serverPost } from '@/lib/api/server';
import { revalidatePath } from 'next/cache';

export async function createProject(formData: FormData) {
  const data = {
    name: formData.get('name') as string,
    description: formData.get('description') as string,
  };

  try {
    await serverPost('/projects', data);
    revalidatePath('/projects'); // 刷新页面缓存
    return { success: true };
  } catch (error) {
    return { success: false, error: '创建失败' };
  }
}
```

---

## 9. 表单开发

### 9.1 Zod Schema (与后端对齐)

```typescript
// lib/validators.ts
import { z } from 'zod';

/**
 * 项目创建 Schema
 * ✅ 与后端 Pydantic Schema 对齐
 */
export const createProjectSchema = z.object({
  name: z.string()
    .min(2, '项目名称至少2个字符')
    .max(100, '项目名称最多100个字符'),

  description: z.string().optional(),

  timezone: z.string()
    .regex(/^[A-Za-z_]+\/[A-Za-z_]+$/, '时区格式无效')
    .default('Asia/Shanghai'),

  budget: z.number()
    .positive('预算必须大于0')
    .optional(),
});

export type CreateProjectInput = z.infer<typeof createProjectSchema>;
```

### 9.2 表单组件

```typescript
// components/features/projects/ProjectForm.tsx
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { createProjectSchema, type CreateProjectInput } from '@/lib/validators';
import { useCreateProject } from '@/hooks/useProjects';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

export function ProjectForm({ onSuccess }: { onSuccess?: () => void }) {
  const { createProject } = useCreateProject();

  const form = useForm<CreateProjectInput>({
    resolver: zodResolver(createProjectSchema),
    defaultValues: {
      name: '',
      timezone: 'Asia/Shanghai',
    },
  });

  const onSubmit = async (data: CreateProjectInput) => {
    try {
      await createProject(data);
      toast.success('创建成功');
      form.reset();
      onSuccess?.();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '创建失败');
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>项目名称</FormLabel>
              <FormControl>
                <Input placeholder="输入项目名称" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button type="submit" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? '创建中...' : '创建项目'}
        </Button>
      </form>
    </Form>
  );
}
```

---

## 10. 错误处理

### 10.1 错误边界

```typescript
// components/shared/ErrorBoundary.tsx
'use client';

import { Component, type ReactNode } from 'react';
import { Button } from '@/components/ui/button';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-screen items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold">出错了</h2>
            <p className="text-muted-foreground mt-2">{this.state.error?.message}</p>
            <Button
              onClick={() => this.setState({ hasError: false })}
              className="mt-4"
            >
              重试
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### 10.2 全局错误处理

```typescript
// app/error.tsx
'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Global error:', error);
  }, [error]);

  return (
    <div className="flex h-screen items-center justify-center">
      <div className="text-center">
        <h2 className="text-2xl font-bold">系统错误</h2>
        <p className="text-muted-foreground mt-2">{error.message}</p>
        <Button onClick={reset} className="mt-4">
          重试
        </Button>
      </div>
    </div>
  );
}
```

### 10.3 错误码映射

```typescript
// config/errorMessages.ts
export const ERROR_MESSAGES: Record<string, string> = {
  AUTH_100: '邮箱已存在',
  AUTH_101: '用户名已存在',
  AUTH_400: '未提供认证凭据',
  AUTH_402: 'Token 已过期',
  AUTH_500: '权限不足',
  BIZ_200: '输入参数无效',
  BIZ_201: '日期格式错误',
  BIZ_202: '操作无效',
  UNKNOWN_ERROR: '未知错误',
};

export function getErrorMessage(code: string): string {
  return ERROR_MESSAGES[code] || ERROR_MESSAGES.UNKNOWN_ERROR;
}
```

---

## 11. 组件开发规范

### 11.1 组件模板

```typescript
// components/features/projects/ProjectCard.tsx
'use client';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/cn';
import type { Project } from '@/types/models';

export interface ProjectCardProps {
  project: Project;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
  className?: string;
}

/**
 * 项目卡片组件
 */
export function ProjectCard({
  project,
  onEdit,
  onDelete,
  className,
}: ProjectCardProps) {
  return (
    <Card className={cn('p-4', className)}>
      <h3 className="text-lg font-semibold">{project.name}</h3>
      <p className="text-sm text-muted-foreground">{project.description}</p>

      <div className="mt-4 flex gap-2">
        {onEdit && (
          <Button size="sm" onClick={() => onEdit(project.id)}>
            编辑
          </Button>
        )}
        {onDelete && (
          <Button
            size="sm"
            variant="destructive"
            onClick={() => onDelete(project.id)}
          >
            删除
          </Button>
        )}
      </div>
    </Card>
  );
}
```

### 11.2 SSR 安全 Hook

```typescript
// hooks/useMounted.ts
'use client';

import { useEffect, useState } from 'react';

/**
 * 检查组件是否已挂载（客户端渲染完成）
 * 用于避免 SSR hydration 错误
 */
export function useMounted() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return mounted;
}
```

**使用示例**:
```typescript
'use client';

import { useMounted } from '@/hooks/useMounted';

export function ThemeToggle() {
  const mounted = useMounted();

  // ✅ 避免 SSR 时访问 localStorage
  if (!mounted) {
    return <div className="w-10 h-10" />; // 占位
  }

  return <Button>Toggle Theme</Button>;
}
```

---

## 12. 样式规范

### 12.1 cn 工具函数

```typescript
// lib/cn.ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

### 12.2 使用示例

```typescript
import { cn } from '@/lib/cn';

export function Button({ className, variant }: ButtonProps) {
  return (
    <button
      className={cn(
        'px-4 py-2 rounded font-medium',
        variant === 'primary' && 'bg-blue-500 text-white',
        variant === 'secondary' && 'bg-gray-200',
        className
      )}
    >
      Click
    </button>
  );
}
```

---

## 13. TypeScript 规范

### 13.1 模型类型

```typescript
// types/models.ts

export enum UserRole {
  Admin = 'admin',
  Finance = 'finance',
  DataOperator = 'data_operator',
  AccountManager = 'account_manager',
  MediaBuyer = 'media_buyer',
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type ProjectStatus = 'draft' | 'active' | 'suspended' | 'archived';

export interface Project {
  id: string;
  name: string;
  description?: string;
  status: ProjectStatus;
  timezone: string;
  budget?: number;
  created_by: string;
  created_at: string;
  updated_at: string;
}
```

### 13.2 tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "jsx": "preserve",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "skipLibCheck": true,
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

---

## 14. 环境变量

### 14.1 .env.local

```bash
# API 配置
NEXT_PUBLIC_API_URL=http://localhost:8000

# 认证配置 (后端 Supabase)
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx...

# 可选: Sentry
NEXT_PUBLIC_SENTRY_DSN=https://xxx@sentry.io/xxx
```

### 14.2 类型安全检查

```typescript
// config/env.ts
const env = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL,
  supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL,
  supabaseAnonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
};

// 验证必填项
Object.entries(env).forEach(([key, value]) => {
  if (!value) {
    throw new Error(`Missing environment variable: ${key}`);
  }
});

export default env;
```

---

## 15. 性能优化

### 15.1 动态导入

```typescript
import dynamic from 'next/dynamic';

const HeavyChart = dynamic(
  () => import('@/components/features/charts/HeavyChart'),
  {
    loading: () => <div>加载中...</div>,
    ssr: false,
  }
);
```

### 15.2 图片优化

```typescript
import Image from 'next/image';

export function Logo() {
  return (
    <Image
      src="/logo.png"
      alt="Logo"
      width={200}
      height={50}
      priority
    />
  );
}
```

---

## 16. 测试规范

### 16.1 单元测试 (Vitest)

```typescript
// hooks/__tests__/useProjects.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { useProjects } from '../useProjects';

describe('useProjects', () => {
  it('should fetch projects', async () => {
    const { result } = renderHook(() => useProjects());

    await waitFor(() => expect(result.current.projects).toBeDefined());
    expect(result.current.projects).toHaveLength(3);
  });
});
```

### 16.2 组件测试

```typescript
// components/__tests__/ProjectCard.test.tsx
import { render, screen } from '@testing-library/react';
import { ProjectCard } from '../ProjectCard';

describe('ProjectCard', () => {
  it('renders project name', () => {
    const project = { id: '1', name: 'Test Project' };
    render(<ProjectCard project={project} />);

    expect(screen.getByText('Test Project')).toBeInTheDocument();
  });
});
```

---

## 17. 开发铁律

### ✅ 强制要求

1. **Server Components 使用 `serverFetch`，Client Components 使用 `clientFetch`**
2. **所有 Props 必须定义 TypeScript Interface**
3. **禁止在 API Client 内部调用 toast/alert**
4. **禁止使用 `useEffect` 获取数据（用 SWR 或 Server Components）**
5. **禁止直接使用 `fetch`（必须用封装的 API client）**
6. **优先使用 shadcn/ui 组件**
7. **localStorage/window 访问前必须检查 `typeof window !== 'undefined'`**
8. **环境变量必须以 `NEXT_PUBLIC_` 开头（客户端访问）**

### 🚫 严格禁止

1. ❌ **在 Server Components 使用 `useState`/`useEffect`**
2. ❌ **在 Client Components 使用 `cookies()`/`headers()`**
3. ❌ **绕过 Middleware 直接访问受保护路由**
4. ❌ **将敏感信息存储在 localStorage**（使用 httpOnly cookies）
5. ❌ **手写 CSS（除非 Tailwind 无法实现）**

---

## 📚 参考文档

- [Next.js 16 Docs](https://nextjs.org/docs)
- [React 19 Docs](https://react.dev)
- [SWR Docs](https://swr.vercel.app)
- [Zustand Docs](https://zustand.docs.pmnd.rs)
- [shadcn/ui Docs](https://ui.shadcn.com)

---

## 📝 变更历史

### v2.0 (2025-01-20)
**重大架构优化**
- ✅ 修正 API Client SSR 不安全问题（分层设计）
- ✅ 修正 Zustand localStorage SSR 崩溃
- ✅ 新增 Middleware 路由守卫章节
- ✅ 新增 Provider 结构章节
- ✅ 新增服务端 Session 操作
- ✅ 新增环境变量、测试规范
- ✅ 移除 API Client 内部 toast 调用
- ✅ 完善 SSR 安全指南

### v1.0 (2025-01-20)
- 初始版本

---

> **版权声明**: 本文档为 AI 广告代投系统的内部技术文档。
> **维护团队**: 前端架构团队
> **文档仓库**: `docs/core/FRONTEND_SPEC_v2.md`
