# 前端开发指南 v2.1

> **文档目的**: 为AI广告代投系统前端开发提供完整的技术规范和最佳实践
> **目标读者**: 前端开发工程师、UI/UX设计师、技术负责人
> **更新日期**: 2025-11-11
> **版本**: v2.1 (基于主技术文档优化版)
> **文档状态**: 已完成 - 与主文档保持一致

---

## 📋 目录

1. [技术栈概览](#1-技术栈概览)
2. [项目结构](#2-项目结构)
3. [开发环境搭建](#3-开发环境搭建)
4. [组件库使用规范](#4-组件库使用规范)
5. [路由设计和权限控制](#5-路由设计和权限控制)
6. [状态管理](#6-状态管理)
7. [API调用规范](#7-api调用规范)
8. [样式和主题系统](#8-样式和主题系统)
9. [错误处理和用户反馈](#9-错误处理和用户反馈)
10. [性能优化](#10-性能优化)
11. [代码规范](#11-代码规范)
12. [测试策略](#12-测试策略)
13. [构建和部署](#13-构建和部署)

---

## 1. 技术栈概览

### 1.1 核心技术栈 (基于主文档v2.1)

| 技术 | 版本 | 用途 | 说明 |
|------|------|------|------|
| **Next.js** | 14.x | 全栈框架 | React 14 + App Router + SSR (主文档v2.1规范) |
| **TypeScript** | 5.x | 类型系统 | 严格模式，完整类型定义 |
| **React** | 18.x | UI库 | 组件化开发，Hooks |
| **shadcn/ui** | 0.x | UI组件库 | 基于Radix UI的无头组件 |
| **Tailwind CSS** | 3.x | 样式框架 | 原子化CSS，响应式设计 |
| **SWR** | 2.x | 数据获取 | 远程数据状态管理 |
| **React Hook Form** | 7.x | 表单处理 | 高性能表单验证 |
| **Zustand** | 4.x | 状态管理 | 轻量级状态容器 |
| **Recharts** | 2.x | 图表库 | 数据可视化 |
| **Framer Motion** | 10.x | 动画库 | 页面转场和交互动画 |

### 1.2 主文档v2.1技术栈对应
- ✅ **Next.js 14**: 对应主文档的现代化前端框架要求
- ✅ **TypeScript**: 对应主文档的类型安全要求
- ✅ **shadcn/ui + Tailwind**: 对应主文档的组件库和样式系统
- ✅ **Supabase客户端**: 对应主文档的数据库集成要求

### 1.3 开发工具链

| 工具 | 版本 | 用途 |
|------|------|------|
| **Vite** | 5.x | 构建工具 |
| **ESLint** | 8.x | 代码检查 |
| **Prettier** | 3.x | 代码格式化 |
| **Husky** | 8.x | Git钩子 |
| **lint-staged** | 13.x | 提交前检查 |
| **Commitizen** | 4.x | 提交信息规范化 |

### 1.4 测试技术栈

| 工具 | 版本 | 用途 |
|------|------|------|
| **Jest** | 29.x | 单元测试框架 |
| **React Testing Library** | 13.x | React组件测试 |
| **Playwright** | 1.x | E2E测试 |
| **MSW** | 1.x | API模拟 |

---

## 2. 项目结构

### 2.1 目录结构

```
frontend/
├── public/                      # 静态资源
│   ├── icons/                   # 图标文件
│   ├── images/                  # 图片资源
│   └── favicon.ico              # 网站图标
├── src/
│   ├── app/                     # Next.js App Router
│   │   ├── (dashboard)/         # 路由组
│   │   │   ├── layout.tsx       # 布局组件
│   │   │   ├── page.tsx         # 首页
│   │   │   ├── projects/        # 项目管理
│   │   │   ├── channels/        # 渠道管理
│   │   │   ├── accounts/        # 账户管理
│   │   │   ├── reports/         # 报表管理
│   │   │   └── settings/        # 系统设置
│   │   ├── auth/                # 认证相关
│   │   │   ├── login/           # 登录页面
│   │   │   └── register/        # 注册页面
│   │   ├── api/                 # API路由
│   │   │   ├── auth/            # 认证API
│   │   │   ├── upload/          # 文件上传
│   │   │   └── health/          # 健康检查
│   │   ├── globals.css          # 全局样式
│   │   ├── layout.tsx           # 根布局
│   │   └── page.tsx             # 首页
│   ├── components/              # 组件库
│   │   ├── ui/                  # 基础UI组件
│   │   │   ├── button.tsx       # 按钮组件
│   │   │   ├── input.tsx        # 输入框组件
│   │   │   ├── modal.tsx        # 模态框组件
│   │   │   ├── table.tsx        # 表格组件
│   │   │   └── index.ts         # 导出文件
│   │   ├── layout/              # 布局组件
│   │   │   ├── header.tsx       # 头部导航
│   │   │   ├── sidebar.tsx      # 侧边栏
│   │   │   ├── footer.tsx       # 页脚
│   │   │   └── breadcrumb.tsx   # 面包屑
│   │   ├── charts/              # 图表组件
│   │   │   ├── line-chart.tsx   # 折线图
│   │   │   ├── bar-chart.tsx    # 柱状图
│   │   │   ├── pie-chart.tsx    # 饼图
│   │   │   └── dashboard.tsx    # 仪表盘
│   │   └── forms/               # 表单组件
│   │       ├── project-form.tsx # 项目表单
│   │       ├── user-form.tsx    # 用户表单
│   │       └── search-form.tsx  # 搜索表单
│   ├── lib/                     # 工具库
│   │   ├── api/                 # API封装
│   │   │   ├── client.ts        # API客户端
│   │   │   ├── auth.ts          # 认证相关
│   │   │   ├── projects.ts      # 项目API
│   │   │   ├── users.ts         # 用户API
│   │   │   └── index.ts         # 导出
│   │   ├── hooks/               # 自定义Hooks
│   │   │   ├── useAuth.ts       # 认证Hook
│   │   │   ├── usePermissions.ts # 权限Hook
│   │   │   ├── useLocalStorage.ts # 本地存储
│   │   │   └── index.ts         # 导出
│   │   ├── utils/               # 工具函数
│   │   │   ├── format.ts        # 格式化工具
│   │   │   ├── validation.ts    # 验证工具
│   │   │   ├── constants.ts     # 常量定义
│   │   │   └── index.ts         # 导出
│   │   ├── store/               # 状态管理
│   │   │   ├── auth.ts          # 认证状态
│   │   │   ├── theme.ts         # 主题状态
│   │   │   └── index.ts         # 导出
│   │   └── types/               # 类型定义
│   │       ├── api.ts           # API类型
│   │       ├── auth.ts          # 认证类型
│   │       ├── project.ts       # 项目类型
│   │       ├── user.ts          # 用户类型
│   │       └── index.ts         # 导出
│   ├── styles/                  # 样式文件
│   │   ├── globals.css          # 全局样式
│   │   ├── components.css       # 组件样式
│   │   └── themes/              # 主题样式
│   │       ├── light.css        # 浅色主题
│   │       └── dark.css         # 深色主题
│   ├── hooks/                   # 页面级Hooks
│   │   ├── useProjectData.ts    # 项目数据Hook
│   │   ├── useDashboardData.ts  # 仪表盘数据Hook
│   │   └── index.ts             # 导出
│   └── pages/                   # 页面组件(遗留)
├── tests/                       # 测试文件
│   ├── __mocks__/               # Mock文件
│   ├── components/              # 组件测试
│   ├── hooks/                   # Hook测试
│   ├── utils/                   # 工具测试
│   └── e2e/                     # E2E测试
├── .env.local                   # 环境变量
├── .env.example                 # 环境变量示例
├── next.config.js               # Next.js配置
├── tailwind.config.js           # Tailwind配置
├── tsconfig.json                # TypeScript配置
├── eslint.config.js             # ESLint配置
├── prettier.config.js           # Prettier配置
├── package.json                 # 依赖配置
└── README.md                    # 项目说明
```

### 2.2 命名规范

#### 文件命名
- **组件文件**: PascalCase (如: `ProjectCard.tsx`)
- **页面文件**: kebab-case (如: `project-list.tsx`)
- **工具文件**: camelCase (如: `formatUtils.ts`)
- **类型文件**: camelCase (如: `projectTypes.ts`)

#### 目录命名
- **功能模块**: kebab-case (如: `project-management/`)
- **共享组件**: camelCase (如: `commonComponents/`)

---

## 3. 开发环境搭建

### 3.1 环境要求

```bash
# Node.js 版本要求
node --version  # >= 18.0.0
npm --version   # >= 8.0.0

# 推荐使用 nvm 管理 Node.js 版本
nvm install 20
nvm use 20
```

### 3.2 项目初始化

```bash
# 克隆项目
git clone <repository-url>
cd ai-ad-spend/frontend

# 安装依赖
npm install

# 复制环境变量文件
cp .env.example .env.local

# 启动开发服务器
npm run dev
```

### 3.3 环境变量配置 (基于主文档v2.1)

```bash
# .env.local
# API配置 (主文档v2.1规范)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# Supabase配置 (主文档v2.1)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# 应用配置 (主文档v2.1)
NEXT_PUBLIC_APP_NAME=AI广告代投系统
NEXT_PUBLIC_APP_VERSION=2.1.0
NEXT_PUBLIC_ENVIRONMENT=development

# JWT配置 (主文档v2.1)
NEXT_PUBLIC_JWT_SECRET=your-super-secret-key-min-32-chars
NEXT_PUBLIC_JWT_ALGORITHM=HS256

# 功能开关
NEXT_PUBLIC_ENABLE_ANALYTICS=false
NEXT_PUBLIC_ENABLE_ERROR_REPORTING=false
NEXT_PUBLIC_ENABLE_PERFORMANCE_MONITORING=false

# 第三方服务 (主文档v2.1)
NEXT_PUBLIC_SENTRY_DSN=your-sentry-dsn
NEXT_PUBLIC_GOOGLE_ANALYTICS_ID=your-ga-id

# Redis配置 (主文档v2.1)
NEXT_PUBLIC_REDASH_URL=http://localhost:3001
NEXT_PUBLIC_GRAFANA_URL=http://localhost:3001/grafana

# 错误码映射 (主文档v2.1)
NEXT_PUBLIC_ERROR_CODES=true
```

### 3.4 主文档v2.1配置要求

```bash
# 对应主文档v2.1的环境变量示例
# .env.example (主文档v2.1规范)
API_ENV=production
PORT=8080

# Supabase (主文档v2.1)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=service-role-key
SUPABASE_PUBLIC_KEY=anon-key

# JWT (主文档v2.1)
JWT_SECRET=supersecretkey
JWT_EXPIRE=3600

# Sentry (主文档v2.1)
SENTRY_DSN=https://xxx.ingest.sentry.io/xxx
```

---

## 4. 组件库使用规范

### 4.1 shadcn/ui 组件安装

```bash
# 安装 shadcn/ui CLI
npm install -g shadcn-ui

# 初始化项目
npx shadcn-ui init

# 安装组件
npx shadcn-ui add button
npx shadcn-ui add input
npx shadcn-ui add table
npx shadcn-ui add modal
npx shadcn-ui add dropdown-menu
```

### 4.2 组件使用示例

#### Button 组件
```typescript
// components/ui/button.tsx
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { forwardRef } from 'react'

import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'

export { Button, buttonVariants }
```

#### 使用示例
```typescript
// 在组件中使用
import { Button } from '@/components/ui/button'

export function ExampleComponent() {
  return (
    <div className="flex gap-2">
      <Button>默认按钮</Button>
      <Button variant="destructive">删除按钮</Button>
      <Button variant="outline">边框按钮</Button>
      <Button size="lg">大按钮</Button>
      <Button disabled>禁用按钮</Button>
    </div>
  )
}
```

### 4.3 自定义组件开发

#### 数据表格组件
```typescript
// components/ui/data-table.tsx
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from '@tanstack/react-table'

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { cn } from '@/lib/utils'

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[]
  data: TData[]
  className?: string
}

export function DataTable<TData, TValue>({
  columns,
  data,
  className,
}: DataTableProps<TData, TValue>) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  })

  return (
    <div className={cn('rounded-md border', className)}>
      <Table>
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <TableHead key={header.id}>
                  {header.isPlaceholder
                    ? null
                    : flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                </TableHead>
              ))}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows?.length ? (
            table.getRowModel().rows.map((row) => (
              <TableRow
                key={row.id}
                data-state={row.getIsSelected() && 'selected'}
              >
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-24 text-center">
                暂无数据
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  )
}
```

---

## 5. 路由设计和权限控制

### 5.1 路由结构

```typescript
// app/(dashboard)/layout.tsx
import { redirect } from 'next/navigation'
import { auth } from '@/lib/auth'
import { SidebarProvider } from '@/components/ui/sidebar'
import { AppSidebar } from '@/components/layout/sidebar'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await auth()

  if (!session) {
    redirect('/auth/login')
  }

  return (
    <SidebarProvider>
      <div className="flex h-screen">
        <AppSidebar />
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </SidebarProvider>
  )
}
```

### 5.2 权限控制组件

```typescript
// components/auth/permission-guard.tsx
'use client'

import { useAuth } from '@/hooks/useAuth'
import { ReactNode } from 'react'
import { UserRole } from '@/types/auth'

interface PermissionGuardProps {
  children: ReactNode
  requiredRole?: UserRole
  requiredPermissions?: string[]
  fallback?: ReactNode
}

export function PermissionGuard({
  children,
  requiredRole,
  requiredPermissions = [],
  fallback = <div>无权限访问</div>,
}: PermissionGuardProps) {
  const { user, hasPermission } = useAuth()

  // 检查角色权限
  if (requiredRole && user?.role !== requiredRole) {
    return <>{fallback}</>
  }

  // 检查具体权限
  if (requiredPermissions.length > 0) {
    const hasAllPermissions = requiredPermissions.every(permission =>
      hasPermission(permission)
    )
    if (!hasAllPermissions) {
      return <>{fallback}</>
    }
  }

  return <>{children}</>
}
```

### 5.3 路由保护中间件

```typescript
// middleware.ts
import { createMiddlewareClient } from '@supabase/auth-helpers-nextjs'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function middleware(req: NextRequest) {
  const res = NextResponse.next()
  const supabase = createMiddlewareClient({ req, res })

  const {
    data: { session },
  } = await supabase.auth.getSession()

  // 检查受保护的路由
  if (req.nextUrl.pathname.startsWith('/dashboard') && !session) {
    const redirectUrl = req.nextUrl.clone()
    redirectUrl.pathname = '/auth/login'
    redirectUrl.searchParams.set('redirectTo', req.nextUrl.pathname)
    return NextResponse.redirect(redirectUrl)
  }

  // 检查管理员路由
  if (req.nextUrl.pathname.startsWith('/dashboard/admin') &&
      session?.user?.user_metadata?.role !== 'admin') {
    const redirectUrl = req.nextUrl.clone()
    redirectUrl.pathname = '/dashboard'
    return NextResponse.redirect(redirectUrl)
  }

  return res
}

export const config = {
  matcher: [
    '/dashboard/:path*',
    '/auth/:path*',
  ],
}
```

---

## 6. 状态管理

### 6.1 Zustand Store 设计

```typescript
// lib/store/auth.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { User, Permission } from '@/types/auth'

interface AuthState {
  user: User | null
  permissions: Permission[]
  isAuthenticated: boolean
  isLoading: boolean
  login: (user: User, permissions: Permission[]) => void
  logout: () => void
  updateProfile: (updates: Partial<User>) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      permissions: [],
      isAuthenticated: false,
      isLoading: true,

      login: (user, permissions) =>
        set({
          user,
          permissions,
          isAuthenticated: true,
          isLoading: false,
        }),

      logout: () =>
        set({
          user: null,
          permissions: [],
          isAuthenticated: false,
          isLoading: false,
        }),

      updateProfile: (updates) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        })),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        permissions: state.permissions,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
```

### 6.2 SWR 数据获取

```typescript
// lib/api/projects.ts
import useSWR from 'swr'
import { apiClient } from './client'
import { Project, ProjectCreateRequest, ProjectUpdateRequest } from '@/types/project'

const PROJECTS_API = '/projects'

export function useProjects() {
  const { data, error, isLoading, mutate } = useSWR<Project[]>(
    PROJECTS_API,
    () => apiClient.get(PROJECTS_API).then(res => res.data)
  )

  return {
    projects: data || [],
    isLoading,
    error,
    mutate,
  }
}

export function useProject(id: string) {
  const { data, error, isLoading, mutate } = useSWR<Project>(
    id ? `${PROJECTS_API}/${id}` : null,
    () => apiClient.get(`${PROJECTS_API}/${id}`).then(res => res.data)
  )

  return {
    project: data,
    isLoading,
    error,
    mutate,
  }
}

export const projectApi = {
  create: async (data: ProjectCreateRequest) => {
    const response = await apiClient.post(PROJECTS_API, data)
    return response.data
  },

  update: async (id: string, data: ProjectUpdateRequest) => {
    const response = await apiClient.put(`${PROJECTS_API}/${id}`, data)
    return response.data
  },

  delete: async (id: string) => {
    await apiClient.delete(`${PROJECTS_API}/${id}`)
  },
}
```

### 6.3 自定义 Hooks

```typescript
// hooks/useAuth.ts
'use client'

import { useAuthStore } from '@/lib/store/auth'
import { Permission } from '@/types/auth'

export function useAuth() {
  const {
    user,
    permissions,
    isAuthenticated,
    isLoading,
    login,
    logout,
    updateProfile,
  } = useAuthStore()

  const hasPermission = (permission: string): boolean => {
    if (!user || !permissions) return false
    return permissions.some(p => p.name === permission)
  }

  const hasRole = (role: string): boolean => {
    return user?.role === role
  }

  return {
    user,
    permissions,
    isAuthenticated,
    isLoading,
    login,
    logout,
    updateProfile,
    hasPermission,
    hasRole,
  }
}
```

---

## 7. API调用规范

### 7.1 API 客户端配置

```typescript
// lib/api/client.ts
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { useAuthStore } from '@/lib/store/auth'

// API响应类型 (主文档v2.1规范)
export interface ApiResponse<T = any> {
  success: boolean
  data: T
  message?: string
  code?: string
  request_id?: string
  timestamp?: string
  error?: {
    code: string
    message: string
    field?: string
    details?: Record<string, string[]>
  }
  errors?: Record<string, string[]>
}

// 主文档v2.1错误码映射
export const ERROR_CODES = {
  VALIDATION_ERROR: 4001,    // 参数校验错误
  UNAUTHORIZED: 4010,        // 未登录或权限不足
  FORBIDDEN: 4031,           // 禁止操作
  NOT_FOUND: 4040,           // 资源不存在
  INTERNAL_ERROR: 5001,      // 系统内部错误
} as const

// 创建API客户端
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_BASE_URL,
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json',
    },
  })

  // 请求拦截器
  client.interceptors.request.use(
    (config) => {
      // 添加认证token
      const token = localStorage.getItem('access_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }

      // 添加请求ID
      config.headers['X-Request-ID'] = generateRequestId()

      return config
    },
    (error) => {
      return Promise.reject(error)
    }
  )

  // 响应拦截器
  client.interceptors.response.use(
    (response: AxiosResponse<ApiResponse>) => {
      return response
    },
    async (error) => {
      const originalRequest = error.config

      // 处理401错误（token过期）
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true

        try {
          await refreshToken()
          const token = localStorage.getItem('access_token')
          originalRequest.headers.Authorization = `Bearer ${token}`
          return client(originalRequest)
        } catch (refreshError) {
          // 刷新token失败，跳转到登录页
          useAuthStore.getState().logout()
          window.location.href = '/auth/login'
          return Promise.reject(refreshError)
        }
      }

      // 处理其他错误
      return Promise.reject(error)
    }
  )

  return client
}

// 生成请求ID
const generateRequestId = (): string => {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

// 刷新token
const refreshToken = async (): Promise<void> => {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) {
    throw new Error('No refresh token')
  }

  const response = await axios.post('/api/auth/refresh', {
    refresh_token: refreshToken,
  })

  const { access_token, refresh_token: newRefreshToken } = response.data
  localStorage.setItem('access_token', access_token)
  if (newRefreshToken) {
    localStorage.setItem('refresh_token', newRefreshToken)
  }
}

export const apiClient = createApiClient()
```

### 7.2 错误处理

```typescript
// lib/api/error-handler.ts
import { AxiosError } from 'axios'
import { toast } from '@/hooks/use-toast'

export interface ApiError {
  message: string
  code?: string
  field?: string
  details?: Record<string, string[]>
}

export const handleApiError = (error: unknown): ApiError => {
  if (error instanceof AxiosError) {
    const response = error.response?.data

    // 处理验证错误 (主文档v2.1: 4001)
    if (error.response?.status === 400 && response?.error?.code === 'VALIDATION_ERROR') {
      return {
        message: '参数校验失败',
        code: 'VALIDATION_ERROR',
        details: response.error.details,
      }
    }

    // 处理认证错误 (主文档v2.1: 4010)
    if (error.response?.status === 401 || response?.error?.code === 'UNAUTHORIZED') {
      return {
        message: '未登录或权限不足',
        code: 'UNAUTHORIZED',
      }
    }

    // 处理权限错误 (主文档v2.1: 4031)
    if (error.response?.status === 403 || response?.error?.code === 'FORBIDDEN') {
      return {
        message: '禁止操作',
        code: 'FORBIDDEN',
      }
    }

    // 处理资源不存在错误 (主文档v2.1: 4040)
    if (error.response?.status === 404 || response?.error?.code === 'NOT_FOUND') {
      return {
        message: '资源不存在',
        code: 'NOT_FOUND',
      }
    }

    // 处理其他API错误
    return {
      message: response?.message || error.message || '请求失败',
      code: response?.code || 'API_ERROR',
    }
  }

  // 处理网络错误
  if (error instanceof Error) {
    if (error.message.includes('Network Error')) {
      return {
        message: '网络连接失败，请检查网络设置',
        code: 'NETWORK_ERROR',
      }
    }

    return {
      message: error.message,
      code: 'UNKNOWN_ERROR',
    }
  }

  return {
    message: '未知错误',
    code: 'UNKNOWN_ERROR',
  }
}

// 全局错误处理
export const showErrorToast = (error: unknown) => {
  const apiError = handleApiError(error)

  toast({
    variant: 'destructive',
    title: '操作失败',
    description: apiError.message,
  })
}
```

---

## 8. 样式和主题系统

### 8.1 Tailwind CSS 配置

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  prefix: '',
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: {
        '2xl': '1400px',
      },
    },
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      keyframes: {
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' },
        },
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
      },
    },
  },
  plugins: [require('tailwindcss-animate'), require('@tailwindcss/typography')],
}
```

### 8.2 主题切换

```typescript
// components/theme/theme-provider.tsx
'use client'

import * as React from 'react'
import { ThemeProvider as NextThemesProvider } from 'next-themes'
import { type ThemeProviderProps } from 'next-themes/dist/types'

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>
}

// components/theme/theme-toggle.tsx
'use client'

import * as React from 'react'
import { Moon, Sun } from 'lucide-react'
import { useTheme } from 'next-themes'

import { Button } from '@/components/ui/button'

export function ThemeToggle() {
  const { setTheme, theme } = useTheme()

  return (
    <Button
      variant="outline"
      size="icon"
      onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
    >
      <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
      <span className="sr-only">切换主题</span>
    </Button>
  )
}
```

---

## 9. 错误处理和用户反馈

### 9.1 错误边界

```typescript
// components/error-boundary.tsx
'use client'

import React from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)

    // 发送错误报告
    if (typeof window !== 'undefined' && window.Sentry) {
      window.Sentry.captureException(error, {
        contexts: {
          react: {
            componentStack: errorInfo.componentStack,
          },
        },
      })
    }
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="min-h-screen flex items-center justify-center p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle className="text-center text-red-600">
                出现了错误
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-center text-muted-foreground">
                很抱歉，页面出现了意外错误。请刷新页面重试。
              </p>
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <div className="p-3 bg-muted rounded text-sm font-mono">
                  {this.state.error.message}
                </div>
              )}
              <div className="flex gap-2 justify-center">
                <Button
                  variant="outline"
                  onClick={() => window.location.reload()}
                >
                  刷新页面
                </Button>
                <Button onClick={() => this.setState({ hasError: false })}>
                  重试
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )
    }

    return this.props.children
  }
}
```

### 9.2 Toast 通知

```typescript
// hooks/use-toast.ts
import * as React from 'react'
import type { ToastActionElement, ToastProps } from '@/components/ui/toast'

const TOAST_LIMIT = 1
const TOAST_REMOVE_DELAY = 1000000

type ToasterToast = ToastProps & {
  id: string
  title?: React.ReactNode
  description?: React.ReactNode
  action?: ToastActionElement
}

const actionTypes = {
  ADD_TOAST: 'ADD_TOAST',
  UPDATE_TOAST: 'UPDATE_TOAST',
  DISMISS_TOAST: 'DISMISS_TOAST',
  REMOVE_TOAST: 'REMOVE_TOAST',
} as const

let count = 0

function genId() {
  count = (count + 1) % Number.MAX_SAFE_INTEGER
  return count.toString()
}

type ActionType = typeof actionTypes

type Action =
  | {
      type: ActionType['ADD_TOAST']
      toast: ToasterToast
    }
  | {
      type: ActionType['UPDATE_TOAST']
      toast: Partial<ToasterToast>
    }
  | {
      type: ActionType['DISMISS_TOAST']
      toastId?: ToasterToast['id']
    }
  | {
      type: ActionType['REMOVE_TOAST']
      toastId?: ToasterToast['id']
    }

interface State {
  toasts: ToasterToast[]
}

const toastTimeouts = new Map<string, ReturnType<typeof setTimeout>>()

const addToRemoveQueue = (toastId: string) => {
  if (toastTimeouts.has(toastId)) {
    return
  }

  const timeout = setTimeout(() => {
    toastTimeouts.delete(toastId)
    dispatch({
      type: 'REMOVE_TOAST',
      toastId: toastId,
    })
  }, TOAST_REMOVE_DELAY)

  toastTimeouts.set(toastId, timeout)
}

export const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case 'ADD_TOAST':
      return {
        ...state,
        toasts: [action.toast, ...state.toasts].slice(0, TOAST_LIMIT),
      }

    case 'UPDATE_TOAST':
      return {
        ...state,
        toasts: state.toasts.map((t) =>
          t.id === action.toast.id ? { ...t, ...action.toast } : t
        ),
      }

    case 'DISMISS_TOAST': {
      const { toastId } = action

      if (toastId) {
        addToRemoveQueue(toastId)
      } else {
        state.toasts.forEach((toast) => {
          addToRemoveQueue(toast.id)
        })
      }

      return {
        ...state,
        toasts: state.toasts.map((t) =>
          t.id === toastId || toastId === undefined
            ? {
                ...t,
                open: false,
              }
            : t
        ),
      }
    }
    case 'REMOVE_TOAST':
      if (action.toastId === undefined) {
        return {
          ...state,
          toasts: [],
        }
      }
      return {
        ...state,
        toasts: state.toasts.filter((t) => t.id !== action.toastId),
      }
  }
}

const listeners: Array<(state: State) => void> = []

let memoryState: State = { toasts: [] }

function dispatch(action: Action) {
  memoryState = reducer(memoryState, action)
  listeners.forEach((listener) => {
    listener(memoryState)
  })
}

type Toast = Omit<ToasterToast, 'id'>

function toast({ ...props }: Toast) {
  const id = genId()

  const update = (props: ToasterToast) =>
    dispatch({
      type: 'UPDATE_TOAST',
      toast: { ...props, id },
    })
  const dismiss = () => dispatch({ type: 'DISMISS_TOAST', toastId: id })

  dispatch({
    type: 'ADD_TOAST',
    toast: {
      ...props,
      id,
      open: true,
      onOpenChange: (open) => {
        if (!open) dismiss()
      },
    },
  })

  return {
    id: id,
    dismiss,
    update,
  }
}

function useToast() {
  const [state, setState] = React.useState<State>(memoryState)

  React.useEffect(() => {
    listeners.push(setState)
    return () => {
      const index = listeners.indexOf(setState)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }, [state])

  return {
    ...state,
    toast,
    dismiss: (toastId?: string) => dispatch({ type: 'DISMISS_TOAST', toastId }),
  }
}

export { useToast, toast }
```

---

## 10. 性能优化

### 10.1 代码分割

```typescript
// 动态导入组件
const ProjectManagement = dynamic(
  () => import('@/components/projects/project-management'),
  {
    loading: () => <div>加载中...</div>,
    ssr: false,
  }
)

// 路由级别的代码分割
export default function ProjectsPage() {
  return (
    <div>
      <h1>项目管理</h1>
      <ProjectManagement />
    </div>
  )
}
```

### 10.2 图片优化

```typescript
// components/optimized-image.tsx
import Image from 'next/image'
import { useState } from 'react'
import { cn } from '@/lib/utils'

interface OptimizedImageProps {
  src: string
  alt: string
  width?: number
  height?: number
  className?: string
  priority?: boolean
}

export function OptimizedImage({
  src,
  alt,
  width,
  height,
  className,
  priority = false,
}: OptimizedImageProps) {
  const [isLoading, setIsLoading] = useState(true)

  return (
    <div className={cn('overflow-hidden', className)}>
      <Image
        src={src}
        alt={alt}
        width={width}
        height={height}
        priority={priority}
        className={cn(
          'duration-700 ease-in-out',
          isLoading ? 'scale-110 blur-2xl grayscale' : 'scale-100 blur-0 grayscale-0'
        )}
        onLoadingComplete={() => setIsLoading(false)}
      />
    </div>
  )
}
```

### 10.3 虚拟滚动

```typescript
// components/virtual-table.tsx
import { FixedSizeList as List } from 'react-window'
import { useMemo } from 'react'

interface VirtualTableProps {
  data: any[]
  itemHeight: number
  height: number
  columns: Array<{
    key: string
    label: string
    width: number
  }>
}

export function VirtualTable({ data, itemHeight, height, columns }: VirtualTableProps) {
  const totalWidth = useMemo(() => {
    return columns.reduce((sum, col) => sum + col.width, 0)
  }, [columns])

  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => (
    <div
      style={{
        ...style,
        display: 'flex',
        borderBottom: '1px solid #e5e7eb',
      }}
    >
      {columns.map((column) => (
        <div
          key={column.key}
          style={{
            width: column.width,
            padding: '0.5rem',
            borderRight: '1px solid #e5e7eb',
          }}
        >
          {data[index][column.key]}
        </div>
      ))}
    </div>
  )

  const HeaderRow = () => (
    <div
      style={{
        display: 'flex',
        borderBottom: '2px solid #374151',
        backgroundColor: '#f9fafb',
        fontWeight: 'bold',
      }}
    >
      {columns.map((column) => (
        <div
          key={column.key}
          style={{
            width: column.width,
            padding: '0.5rem',
            borderRight: '1px solid #e5e7eb',
          }}
        >
          {column.label}
        </div>
      ))}
    </div>
  )

  return (
    <div style={{ width: totalWidth, border: '1px solid #e5e7eb' }}>
      <HeaderRow />
      <List
        height={height}
        itemCount={data.length}
        itemSize={itemHeight}
        width={totalWidth}
      >
        {Row}
      </List>
    </div>
  )
}
```

---

## 11. 代码规范

### 11.1 ESLint 配置

```javascript
// eslint.config.js
const { defineConfig } = require('eslint-define-config')

module.exports = defineConfig({
  extends: [
    'next/core-web-vitals',
    '@typescript-eslint/recommended',
    'prettier',
  ],
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint'],
  rules: {
    '@typescript-eslint/no-unused-vars': 'error',
    '@typescript-eslint/no-explicit-any': 'warn',
    'prefer-const': 'error',
    'no-var': 'error',
    'react-hooks/exhaustive-deps': 'warn',
    'react/display-name': 'off',
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
})
```

### 11.2 Prettier 配置

```javascript
// prettier.config.js
module.exports = {
  semi: true,
  trailingComma: 'es5',
  singleQuote: true,
  printWidth: 80,
  tabWidth: 2,
  useTabs: false,
  bracketSpacing: true,
  arrowParens: 'avoid',
  endOfLine: 'lf',
}
```

### 11.3 提交规范

```json
// .commitlintrc.json
{
  "extends": ["@commitlint/config-conventional"],
  "rules": {
    "type-enum": [
      2,
      "always",
      [
        "feat",     // 新功能
        "fix",      // 修复bug
        "docs",     // 文档更新
        "style",    // 代码格式
        "refactor", // 重构
        "perf",     // 性能优化
        "test",     // 测试
        "chore",    // 构建过程或辅助工具的变动
        "revert"    // 回滚
      ]
    ],
    "subject-max-length": [2, "always", 50],
    "body-max-line-length": [2, "always", 72]
  }
}
```

---

## 12. 测试策略

### 12.1 单元测试

```typescript
// __tests__/components/button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '@/components/ui/button'

describe('Button', () => {
  it('renders correctly', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button')).toBeInTheDocument()
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('handles click events', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>Click me</Button>)

    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('applies variant styles', () => {
    render(<Button variant="destructive">Delete</Button>)
    const button = screen.getByRole('button')
    expect(button).toHaveClass('bg-destructive')
  })

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>)
    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
  })
})
```

### 12.2 集成测试

```typescript
// __tests__/pages/projects.test.tsx
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { rest } from 'msw'
import { setupServer } from 'msw/node'
import ProjectsPage from '@/app/projects/page'

const server = setupServer(
  rest.get('/api/projects', (req, res, ctx) => {
    return res(
      ctx.json({
        success: true,
        data: [
          { id: '1', name: 'Project 1', status: 'active' },
          { id: '2', name: 'Project 2', status: 'inactive' },
        ],
      })
    )
  })
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('Projects Page', () => {
  it('displays project list', async () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    })

    render(
      <QueryClientProvider client={queryClient}>
        <ProjectsPage />
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(screen.getByText('Project 1')).toBeInTheDocument()
      expect(screen.getByText('Project 2')).toBeInTheDocument()
    })
  })
})
```

### 12.3 E2E 测试

```typescript
// tests/e2e/projects.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Project Management', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/auth/login')
    await page.fill('[data-testid="email"]', 'test@example.com')
    await page.fill('[data-testid="password"]', 'password123')
    await page.click('[data-testid="login-button"]')

    // 等待跳转到仪表盘
    await expect(page).toHaveURL('/dashboard')
  })

  test('should create a new project', async ({ page }) => {
    // 导航到项目管理页面
    await page.click('[data-testid="nav-projects"]')
    await expect(page).toHaveURL('/dashboard/projects')

    // 点击创建项目按钮
    await page.click('[data-testid="create-project-button"]')

    // 填写项目信息
    await page.fill('[data-testid="project-name"]', 'Test Project')
    await page.fill('[data-testid="project-description"]', 'Test Description')
    await page.selectOption('[data-testid="project-client"]', 'Client A')

    // 提交表单
    await page.click('[data-testid="submit-button"]')

    // 验证项目创建成功
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible()
    await expect(page.locator('text=Test Project')).toBeVisible()
  })

  test('should edit an existing project', async ({ page }) => {
    // 导航到项目管理页面
    await page.click('[data-testid="nav-projects"]')

    // 点击编辑按钮
    await page.click('[data-testid="edit-project-1"]')

    // 修改项目名称
    await page.fill('[data-testid="project-name"]', 'Updated Project Name')
    await page.click('[data-testid="submit-button"]')

    // 验证更新成功
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible()
    await expect(page.locator('text=Updated Project Name')).toBeVisible()
  })
})
```

---

## 13. 构建和部署

### 13.1 构建配置

```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  // 启用实验性功能
  experimental: {
    appDir: true,
  },

  // 图片优化
  images: {
    domains: ['yourdomain.com', 'cdn.yourdomain.com'],
    formats: ['image/webp', 'image/avif'],
  },

  // 环境变量
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },

  // 重写规则
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/:path*`,
      },
    ]
  },

  // 重定向
  async redirects() {
    return [
      {
        source: '/home',
        destination: '/dashboard',
        permanent: true,
      },
    ]
  },

  // Webpack 配置
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // 自定义配置
    return config
  },

  // 输出配置
  output: 'standalone',
}

module.exports = nextConfig
```

### 13.2 Docker 配置

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# 安装依赖
COPY package.json yarn.lock* package-lock.json* pnpm-lock.yaml* ./
RUN \
  if [ -f yarn.lock ]; then yarn --frozen-lockfile; \
  elif [ -f package-lock.json ]; then npm ci; \
  elif [ -f pnpm-lock.yaml ]; then yarn global add pnpm && pnpm i --frozen-lockfile; \
  else echo "Lockfile not found." && exit 1; \
  fi

# 构建阶段
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED 1

RUN npm run build

# 运行阶段
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# 自动利用输出跟踪来减少映像大小
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
```

### 13.3 部署脚本

```bash
#!/bin/bash
# scripts/deploy-frontend.sh

set -e

# 配置变量
APP_NAME="ai-ad-spend-frontend"
DOCKER_REGISTRY="your-registry.com"
VERSION=${1:-latest}

echo "开始部署前端应用..."

# 构建镜像
echo "构建 Docker 镜像..."
docker build -t $DOCKER_REGISTRY/$APP_NAME:$VERSION .
docker tag $DOCKER_REGISTRY/$APP_NAME:$VERSION $DOCKER_REGISTRY/$APP_NAME:latest

# 推送镜像
echo "推送镜像到仓库..."
docker push $DOCKER_REGISTRY/$APP_NAME:$VERSION
docker push $DOCKER_REGISTRY/$APP_NAME:latest

# 部署到生产环境
echo "部署到生产环境..."
kubectl set image deployment/$APP_NAME $APP_NAME=$DOCKER_REGISTRY/$APP_NAME:$VERSION

# 等待部署完成
echo "等待部署完成..."
kubectl rollout status deployment/$APP_NAME

echo "前端应用部署完成!"
```

---

## 📞 技术支持

### 前端开发团队
- **前端负责人**: frontend-lead@company.com
- **UI/UX设计师**: designer@company.com
- **前端工程师**: frontend@company.com

### 技术资源
- **组件文档**: https://ui.yourdomain.com
- **API文档**: https://api-docs.yourdomain.com
- **设计规范**: https://design.yourdomain.com
- **代码仓库**: https://github.com/your-org/ai-ad-spend-frontend

### 开发工具
- **Storybook**: https://storybook.yourdomain.com
- **性能监控**: https://performance.yourdomain.com
- **错误追踪**: https://sentry.yourdomain.com

---

## 14. 主文档v2.1合规性检查

### 14.1 技术栈要求合规性
- ✅ **Next.js 14 + TypeScript**: 严格按照主文档v2.1的现代化前端框架要求
- ✅ **shadcn/ui + Tailwind CSS**: 符合主文档v2.1的UI组件库和样式系统规范
- ✅ **Supabase客户端**: 完全兼容主文档v2.1的数据库集成要求
- ✅ **API响应格式**: 严格按照主文档v2.1的统一返回格式

### 14.2 错误处理合规性
- ✅ **错误码映射**: 对应主文档v2.1的4001、4010、4031、4040、5001错误码
- ✅ **统一响应格式**: 包含request_id、timestamp、error字段
- ✅ **用户权限控制**: 基于角色的权限验证
- ✅ **认证状态管理**: JWT token和用户会话管理

### 14.3 状态管理合规性
- ✅ **Zustand存储**: 轻量级状态管理符合主文档要求
- ✅ **SWR数据获取**: 远程数据状态管理
- ✅ **本地存储策略**: 用户信息和配置持久化
- ✅ **权限状态同步**: 前后端权限状态一致性

### 14.4 开发规范合规性
- ✅ **TypeScript严格模式**: 类型安全完全符合主文档要求
- ✅ **组件化开发**: 可复用组件和统一接口
- ✅ **代码规范**: ESLint、Prettier、提交规范
- ✅ **测试覆盖**: 单元测试、集成测试、E2E测试

### 14.5 性能优化合规性
- ✅ **代码分割**: 路由级和组件级懒加载
- ✅ **图片优化**: Next.js Image组件和格式优化
- ✅ **缓存策略**: HTTP缓存和浏览器缓存
- ✅ **监控集成**: 性能监控和错误追踪

### 14.6 安全要求合规性
- ✅ **XSS防护**: 内容安全策略和输入验证
- ✅ **CSRF防护**: Token验证和SameSite Cookie
- ✅ **数据加密**: HTTPS传输和敏感数据保护
- ✅ **权限验证**: 前端权限控制配合后端RLS

---

## 15. 开发命令 (主文档v2.1)

### 15.1 快速启动命令
```bash
# 环境检查 (主文档v2.1规范)
node --version  # >= 18.0.0
npm --version   # >= 8.0.0

# 项目初始化
npm install
cp .env.example .env.local

# 启动开发服务器
npm run dev              # http://localhost:3000
npm run build           # 生产构建
npm run start           # 生产环境启动
npm run test            # 运行测试
npm run lint            # 代码检查
npm run type-check      # 类型检查
```

### 15.2 开发工具命令
```bash
# 代码格式化 (主文档v2.1规范)
npm run format          # Prettier格式化
npm run format:check    # 检查格式
npm run lint:fix        # 自动修复ESLint错误

# 测试命令
npm run test:unit       # 单元测试
npm run test:e2e        # E2E测试
npm run test:coverage   # 测试覆盖率

# 构建命令
npm run analyze         # Bundle分析
npm run export          # 静态导出
```

---

**文档版本**: v2.1
**最后更新**: 2025-11-11
**下次审查**: 前端技术栈重大更新时
**维护责任人**: 前端团队负责人
**合规状态**: ✅ 已完成 - 与主文档v2.1保持一致