# AI 广告代投管理系统 - 技术栈

> **版本**: v2.0
> **更新日期**: 2026-01-02

---

## 1. 前端技术栈

| 类别 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 框架 | Next.js | 16 | App Router 模式 |
| 语言 | TypeScript | 5.6+ | 严格模式 |
| UI 组件 | shadcn/ui | latest | 基于 Radix UI (54+ 组件) |
| 样式 | Tailwind CSS | 3.x | 原子化 CSS |
| 状态管理 | TanStack Query | v5 | 服务端状态 |
| 表单 | React Hook Form | 7.x | + Zod 验证 |
| 图表 | Recharts | 2.x | 数据可视化 |
| 通知 | Sonner | latest | Toast 通知 |
| 主题 | next-themes | latest | 深色模式支持 |

### 目录结构
```
frontend/src/
├── app/                 # Next.js App Router
│   └── (dashboard)/     # 后台路由组
├── features/            # 功能模块 (按业务划分)
│   ├── auth/            # 认证
│   ├── dashboard/       # 仪表盘
│   ├── daily-reports/   # 日报管理
│   ├── ad-accounts/     # 广告账户
│   ├── projects/        # 项目管理
│   ├── finance/         # 财务管理
│   ├── topups/          # 充值管理
│   └── users/           # 用户管理
├── components/          # 通用组件
│   ├── ui/              # shadcn/ui 组件
│   ├── layout/          # 布局组件
│   └── shared/          # 共享组件
├── hooks/               # 自定义 Hooks
├── lib/                 # 工具函数
│   └── api.ts           # API 客户端 (唯一 HTTP 入口)
└── types/               # TypeScript 类型
```

---

## 2. 后端技术栈

| 类别 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 框架 | FastAPI | 0.100+ | 异步 Python |
| 语言 | Python | 3.11+ | 类型注解 |
| ORM | SQLAlchemy | 2.x | 异步模式 |
| 验证 | Pydantic | v2 | 数据模型 |
| 认证 | Supabase Auth | - | JWT Token |
| 缓存 | Redis | 7.x | 已集成 |

### 目录结构
```
backend/
├── routers/             # API 路由
├── services/            # 业务逻辑
├── models/              # 数据库模型
├── schemas/             # Pydantic 模型
├── core/                # 核心配置
│   ├── config.py        # 配置管理
│   ├── deps.py          # 依赖注入
│   ├── security.py      # 安全相关
│   └── state_machine.py # 状态机
├── exceptions/          # 自定义异常
└── tests/               # 测试
    ├── api/             # API 测试
    ├── services/        # 服务测试
    └── core/            # 核心测试
```

---

## 3. 数据库

| 类别 | 技术 | 说明 |
|------|------|------|
| 主数据库 | PostgreSQL 15 | Supabase 托管 |
| 缓存 | Redis 7.x | 会话/热数据缓存 |
| 文件存储 | Supabase Storage | 附件上传 |

### 核心表
- `users` - 用户表
- `projects` - 项目表
- `ad_accounts` - 广告账户表
- `daily_reports` - 日报表
- `topups` - 充值记录表
- `ledger_entries` - 账本流水表
- `channels` - 渠道表
- `reconciliation_batches` - 对账批次表

---

## 4. 基础设施

| 类别 | 技术 | 说明 |
|------|------|------|
| 云服务 | Supabase | BaaS 平台 |
| 部署 | Vercel | 前端托管 |
| CI/CD | GitHub Actions | 自动化 |
| 版本控制 | Git | GitHub |

---

## 5. 开发工具

| 类别 | 工具 | 说明 |
|------|------|------|
| 包管理 | npm (前端) / pip (后端) | - |
| 代码格式化 | Prettier / Black | - |
| Linting | ESLint / Ruff | - |
| 测试 | Jest / Pytest | - |
| 任务运行 | Just | Makefile 替代 |

---

## 6. 监控与可观测性

| 类别 | 技术 | 说明 |
|------|------|------|
| 错误追踪 | Sentry | 前后端错误收集 |
| 指标监控 | Prometheus | 性能指标 |
| 日志 | 结构化日志 | JSON 格式 |

---

## 7. AI 开发辅助

| 工具 | 用途 |
|------|------|
| Claude Code | AI 编程助手 |
| Task Master MCP | PRD → 任务管理 |
| Sequential Thinking MCP | 结构化思考 |
| Context7 MCP | 文档检索 |
| Playwright MCP | 浏览器自动化测试 |
