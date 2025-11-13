# Bolt.new 开发环境设置指南

## 🚀 快速开始

### 1. 打开 Bolt.new
访问：https://bolt.new/

### 2. 项目配置

在 Bolt.new 中设置项目基础信息：

```
项目名称: AI广告代投系统前端
技术栈: Next.js 15 + TypeScript + Tailwind + shadcn/ui
描述: 广告代投管理系统的前端界面，包含日报管理、账户管理、对账系统等模块
```

### 3. 依赖包配置

在 Bolt.new 中运行以下命令：

```bash
# 初始化项目
npx create-next-app@latest ai-ad-spend-frontend --typescript --tailwind --app --eslint

# 安装必要依赖
npm install @radix-ui/react-dialog @radix-ui/react-select
npm install @radix-ui/react-tabs @radix-ui/react-dropdown-menu
npm install @radix-ui/react-avatar @radix-ui/react-progress
npm install recharts axios sonner date-fns
npm install lucide-react @tanstack/react-query
npm install zustand react-hook-form @hookform/resolvers

# 安装开发工具
npm install -D @types/node @types/react @types/react-dom
npm install -D eslint eslint-config-next
npm install -D prettier eslint-config-prettier
```

### 4. 项目结构设置

在 Bolt.new 中创建以下目录结构：

```
ai-ad-spend-frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (auth)/            # 认证相关页面
│   │   ├── dashboard/         # 仪表板
│   │   ├── projects/          # 项目管理
│   │   ├── ad-accounts/       # 广告账户管理 ⭐
│   │   ├── daily-reports/     # 日报管理 ✅
│   │   ├── reconciliation/    # 对账系统 ⭐
│   │   ├── finance/           # 财务管理
│   │   └── settings/          # 系统设置
│   ├── components/            # 组件库
│   │   ├── ui/                # 基础UI组件
│   │   ├── forms/             # 表单组件
│   │   ├── charts/            # 图表组件
│   │   ├── layout/            # 布局组件
│   │   └── features/          # 业务组件
│   ├── hooks/                 # 自定义Hook
│   ├── lib/                   # 工具函数
│   ├── types/                 # TypeScript类型
│   └── store/                 # 状态管理
├── public/                     # 静态资源
├── docs/                        # 项目文档
└── .env.local                   # 环境变量
```

## 🔧 开发配置

### 1. Tailwind CSS 配置

在 `tailwind.config.js` 中：

```javascript
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#3b82f6',
        secondary: '#64748b',
        success: '#22c55e',
        warning: '#f59e0b',
        danger: '#ef4444',
        info: '#06b6d4',
      }
    }
  }
}
```

### 2. 环境变量配置

在 Bolt.new 中创建 `.env.local`：

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=AI广告代投系统
NEXT_PUBLIC_APP_VERSION=2.1
```

## 📚 开发模式

### 1. 本地开发

```bash
# 启动开发服务器
npm run dev

# 访问应用
http://localhost:3000
```

### 2. API 集成测试

```javascript
// src/lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 10000,
});

// 请求拦截器
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

## 🎯 下一步

1. 完成基础环境设置
2. 阅读 components.md 了解组件开发
3. 阅读 pages.md 了解页面开发
4. 开始开发广告账户管理界面