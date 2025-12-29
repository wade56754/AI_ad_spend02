# AI 广告代投管理系统 - 技术栈

> **版本**: v1.0
> **更新日期**: 2025-12-27

---

## 1. 前端技术栈

| 类别 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 框架 | Next.js | 14.x | App Router 模式 |
| 语言 | TypeScript | 5.x | 严格模式 |
| UI 组件 | shadcn/ui | latest | 基于 Radix UI |
| 样式 | Tailwind CSS | 3.x | 原子化 CSS |
| 状态管理 | React Query | 5.x | 服务端状态 |
| 表单 | React Hook Form | 7.x | + Zod 验证 |
| 图表 | Recharts | 2.x | 数据可视化 |

### 目录结构
```
frontend/src/
├── app/                 # Next.js App Router
├── components/          # 通用组件
├── features/            # 功能模块 (按业务划分)
├── hooks/               # 自定义 Hooks
├── lib/                 # 工具函数
└── types/               # TypeScript 类型
```

---

## 2. 后端技术栈

| 类别 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 框架 | FastAPI | 0.100+ | 异步 Python |
| 语言 | Python | 3.11+ | 类型注解 |
| ORM | SQLAlchemy | 2.x | 异步模式 |
| 验证 | Pydantic | 2.x | 数据模型 |
| 认证 | Supabase Auth | - | JWT Token |
| 任务队列 | - | - | Phase 2 考虑 |

### 目录结构
```
backend/
├── routers/             # API 路由
├── services/            # 业务逻辑
├── models/              # 数据库模型
├── schemas/             # Pydantic 模型
├── core/                # 核心配置
└── tests/               # 测试
```

---

## 3. 数据库

| 类别 | 技术 | 说明 |
|------|------|------|
| 主数据库 | PostgreSQL 15 | Supabase 托管 |
| 缓存 | - | Phase 2 考虑 Redis |
| 文件存储 | Supabase Storage | 附件上传 |

### 核心表
- `users` - 用户表
- `projects` - 项目表
- `ad_accounts` - 广告账户表
- `daily_reports` - 日报表
- `topups` - 充值记录表
- `ledger_entries` - 账本流水表

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

## 6. AI 代码工厂

| 组件 | 版本 | 说明 |
|------|------|------|
| CodeFactory | v4.3 | 上下文增强引擎 |
| TaskCardLoader | v1.0 | 任务卡解析 |
| RiskClassifier | v1.0 | 风险分类 |
| SotLoader | v1.0 | SoT 动态加载 |

### 架构
```
Layer 1: 上下文增强 (SoT, Risk, EventStream)
Layer 2: Claude 代码生成 (Prompt)
Layer 3: 验证与修复 (Guardrails, Tracer)
```
