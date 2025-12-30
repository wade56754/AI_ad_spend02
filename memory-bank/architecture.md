# AI 广告代投管理系统 - 架构说明

> **版本**: v1.0
> **更新日期**: 2025-12-27
> **基准文档**: docs/sot/MASTER.md v4.6

---

## 1. 系统架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Next.js)                        │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │Dashboard│  │ 日报    │  │ 账户    │  │ 财务    │  ...   │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
│       └────────────┴────────────┴────────────┘              │
│                         │                                    │
│                    API Client                                │
└─────────────────────────┼───────────────────────────────────┘
                          │ HTTPS
┌─────────────────────────┼───────────────────────────────────┐
│                    后端 (FastAPI)                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Routers │→ │Services │→ │ Models  │→ │   DB    │        │
│  └─────────┘  └─────────┘  └─────────┘  └────┬────┘        │
└──────────────────────────────────────────────┼──────────────┘
                                               │
┌──────────────────────────────────────────────┼──────────────┐
│                    Supabase                   │              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────┴─────┐       │
│  │ PostgreSQL  │  │   Auth      │  │   Storage     │       │
│  └─────────────┘  └─────────────┘  └───────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 目录结构

```
AI_ad_spend02/
├── frontend/                    # 前端应用
│   └── src/
│       ├── app/                 # Next.js App Router 页面
│       ├── components/          # 通用 UI 组件
│       ├── features/            # 功能模块 (按业务划分)
│       │   ├── auth/            # 认证
│       │   ├── dashboard/       # 仪表盘
│       │   ├── daily-reports/   # 日报
│       │   ├── ad-accounts/     # 账户
│       │   ├── projects/        # 项目
│       │   ├── finance/         # 财务
│       │   └── ...
│       ├── hooks/               # 自定义 Hooks
│       ├── lib/                 # 工具库
│       └── types/               # TypeScript 类型
│
├── backend/                     # 后端应用
│   ├── routers/                 # API 路由定义
│   ├── services/                # 业务逻辑层
│   ├── models/                  # SQLAlchemy 模型
│   ├── schemas/                 # Pydantic 模型
│   ├── core/                    # 核心配置
│   └── tests/                   # 测试
│
├── agents/                      # AI 代理/工具
│   └── skills/
│       └── code_factory/        # AI 代码工厂 v4.3
│           ├── core/            # 核心引擎
│           ├── sot/             # SoT 加载器
│           ├── risk/            # 风险分类
│           ├── task_cards/      # 任务卡系统
│           ├── guardrails/      # 编辑防护
│           └── event_stream/    # 事件流
│
├── docs/                        # 文档
│   ├── sot/                     # 真相源文档 (SoT)
│   │   ├── MASTER.md            # 架构宪法
│   │   ├── DATA_SCHEMA.md       # 数据模型
│   │   ├── STATE_MACHINE.md     # 状态机
│   │   ├── BUSINESS_RULES.md    # 业务规则
│   │   └── ...
│   └── guides/                  # 开发指南
│       └── TASK_CARDS_v2.md     # 任务卡文档
│
├── memory-bank/                 # 项目记忆库 (本目录)
│   ├── game-design-document.md  # 需求/PRD
│   ├── tech-stack.md            # 技术栈
│   ├── implementation-plan.md   # 实施计划
│   ├── progress.md              # 进度记录
│   └── architecture.md          # 架构说明 (本文件)
│
└── .claude/                     # Claude 配置
    └── skills/                  # 技能定义
```

---

## 3. 核心文件说明

### 前端关键文件

| 路径 | 说明 |
|------|------|
| `frontend/src/app/layout.tsx` | 根布局，包含全局 Provider |
| `frontend/src/app/page.tsx` | 首页 (重定向到登录/仪表盘) |
| `frontend/src/features/*/components/` | 各模块的组件 |
| `frontend/src/features/*/services/` | 各模块的 API 调用 |
| `frontend/src/lib/supabase.ts` | Supabase 客户端配置 |

### 后端关键文件

| 路径 | 说明 |
|------|------|
| `backend/main.py` | FastAPI 应用入口 |
| `backend/core/config.py` | 配置管理 |
| `backend/core/deps.py` | 依赖注入 (认证、数据库) |
| `backend/routers/*.py` | API 路由定义 |
| `backend/services/*.py` | 业务逻辑实现 |
| `backend/models/*.py` | 数据库模型 |

### SoT 文档

| 路径 | 说明 | 优先级 |
|------|------|--------|
| `docs/sot/MASTER.md` | 系统全局规则、角色定义 | 1 |
| `docs/sot/DATA_SCHEMA.md` | 数据库模型、字段定义 | 2 |
| `docs/sot/STATE_MACHINE.md` | 日报状态机规范 | 3 |
| `docs/sot/BUSINESS_RULES.md` | 业务规则、验证逻辑 | 4 |
| `docs/sot/API_SOT.md` | API 规范 | 5 |

### AI 代码工厂

| 路径 | 说明 |
|------|------|
| `agents/skills/code_factory/__init__.py` | 模块导出 |
| `agents/skills/code_factory/core/factory.py` | 核心引擎 (build_context, verify_code) |
| `agents/skills/code_factory/task_cards/loader.py` | 任务卡解析器 |
| `agents/skills/code_factory/sot/loader.py` | SoT 动态加载 |
| `agents/skills/code_factory/risk/classifier.py` | 风险分类器 |

---

## 4. 数据流

### 日报提交流程
```
用户填写日报 (前端)
       ↓
POST /api/v1/daily-reports (API)
       ↓
DailyReportService.create() (Service)
       ↓
状态机检查 (STATE_MACHINE.md)
       ↓
业务规则验证 (BUSINESS_RULES.md)
       ↓
数据库写入 (Model)
       ↓
账本记录 (M8)
       ↓
返回结果
```

### 认证流程
```
用户登录 (前端)
       ↓
Supabase Auth
       ↓
获取 JWT Token
       ↓
API 请求携带 Token
       ↓
后端验证 Token
       ↓
获取用户角色
       ↓
权限检查
```

---

## 5. 模块依赖关系

```
M1 认证 ──► M2 用户 ──► M3 项目 ──► M4 渠道
                │              │           │
                │              │           ▼
                │              └──────► M5 账户
                │                          │
                │                          ▼
                │                      M6 日报
                │                          │
                └──────────► M7 充值 ◄─────┘
                                 │
                                 ▼
                             M8 账本
                              │   │
                              ▼   ▼
                        M9 对账   M10 利润
                                     │
                                     ▼
                                 M11 周报
```

---

## 6. 安全架构

### 认证
- Supabase Auth (JWT)
- Token 有效期: 24 小时
- 刷新机制: 自动刷新

### 授权
- 基于角色的访问控制 (RBAC)
- 6 角色: ceo, project_owner, finance, pitcher, account_manager, admin
- 数据域隔离: 投手只看自己账户

### 数据安全
- HTTPS 传输加密
- 敏感数据脱敏
- 审计日志记录

---

## 7. 扩展点

| 扩展点 | 当前状态 | 未来计划 |
|--------|----------|----------|
| 缓存层 | ✅ Redis (TASK-PERF-001) | 已完成 |
| 消息队列 | 无 | RabbitMQ/Celery |
| 监控 | ✅ Sentry + Prometheus (TASK-PERF-003) | 已完成 |
| 搜索 | PostgreSQL | Elasticsearch |

### 7.1 APM 监控 (Phase 3)

**Sentry 集成**:
- 错误追踪和异常捕获
- 性能分析 (traces, profiles)
- 敏感信息过滤

**Prometheus 指标**:
- HTTP 请求计数和响应时间
- 业务指标 (日报、充值、对账)
- 缓存命中率

**配置**:
```bash
# .env
SENTRY_DSN=https://xxx@sentry.io/xxx
SENTRY_ENABLED=true
PROMETHEUS_ENABLED=true
```
