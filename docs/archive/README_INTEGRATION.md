# 集成业务功能到 Supabase Starter

## ✅ 已完成的配置

1. ✅ Supabase Starter 框架已下载
2. ✅ API 客户端已复制到 `lib/api.ts`
3. ✅ 环境变量示例已创建

## 🚀 快速开始

### 1. 配置环境变量

创建 `.env.local` 文件（或复制 `.env.local.example`）：

```env
NEXT_PUBLIC_SUPABASE_URL=https://jzmcoivxhiyidizncyaq.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp6bWNvaXZ4aGl5aWRpem5jeWFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIzMTc4MTEsImV4cCI6MjA3Nzg5MzgxMX0.PIr4EdBjfyCgRa48IxK6yLS0yIER-_3qvd-Mv-4I7rw
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### 2. 添加业务页面

将现有页面复制到 `app/` 目录：

```bash
# 从现有 frontend 目录复制页面
cp -r ../frontend/app/report app/
cp -r ../frontend/app/finance app/
cp -r ../frontend/app/reconcile app/

# 创建分析页面目录
mkdir -p app/analytics
mkdir -p app/settings
```

### 3. 更新导航菜单

修改 `app/page.tsx` 或创建导航组件，添加业务页面链接。

### 4. 启动项目

```bash
npm install
npm run dev
```

## 📁 项目结构

```
with-supabase-app/
├── app/
│   ├── auth/              # 认证页面（Starter 自带）
│   ├── protected/         # 受保护页面示例
│   ├── report/spend/      # 投手消耗上报（需要添加）
│   ├── finance/ledger/    # 财务收支录入（需要添加）
│   ├── reconcile/         # 对账结果（需要添加）
│   ├── analytics/         # 分析报表（需要添加）
│   └── settings/           # 设置管理（需要添加）
├── components/
│   └── ui/                # shadcn/ui 组件
├── lib/
│   ├── supabase/          # Supabase 客户端
│   ├── api.ts             # FastAPI 调用（已添加）
│   └── utils.ts            # 工具函数
└── middleware.ts           # Next.js 中间件
```

## 🎯 使用说明

### 调用后端 API

使用 `lib/api.ts` 中的函数：

```typescript
import { postAdSpend, getReconciliations } from '@/lib/api'

// 在组件中使用
const result = await postAdSpend({...})
```

### 使用 Supabase（可选）

如果需要认证或实时功能：

```typescript
import { createClient } from '@/lib/supabase/client'

const supabase = createClient()
const { data: { user } } = await supabase.auth.getUser()
```

### 使用 UI 组件

Starter 框架包含 shadcn/ui 组件，可以直接使用：

```typescript
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
```

## 📝 注意事项

1. **认证保护**：中间件默认会保护所有路由，如果不需要认证，可以修改 `middleware.ts`
2. **环境变量**：确保 `.env.local` 文件已配置
3. **API 调用**：继续使用 `lib/api.ts` 调用 FastAPI 后端
4. **页面路由**：使用 Next.js App Router 的文件夹路由

## 🔧 下一步

1. 复制业务页面到 `app/` 目录
2. 创建导航菜单
3. 测试功能
4. 根据需要调整认证保护

现在可以开始添加业务功能了！


