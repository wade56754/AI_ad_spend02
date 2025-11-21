# AI广告代投系统·核心开发手册 (Master Design Document)

> **文档版本**: v1.0
> **发布日期**: 2025-11-20
> **文档状态**: ✅ 核心开发手册 (Single Source of Truth)
> **维护团队**: 系统架构团队
> **文档定位**: 所有开发工作(人类开发和AI辅助开发)的最高指导标准

---

## 📋 文档说明

### 🎯 文档目的

本文档是**AI广告代投系统**的核心开发手册,作为分散文档的统一入口和权威指导,解决以下问题:

1. **消除歧义**: 整合并修正分散文档中的冲突和错误
2. **单一真相源**: 明确所有技术决策的最高仲裁依据
3. **开发指导**: 为人类开发者和AI辅助工具提供清晰的实现标准

### 📚 真相源网络 (SoT Network)

本手册与其他核心文档形成完整的知识体系:

```
MASTER_DESIGN_DOCUMENT.md (本文档 - 顶层指导手册)
    │
    ├─→ DATA_SCHEMA.md           (数据结构唯一真相源)
    ├─→ STATE_MACHINE.md          (状态机唯一真相源)
    ├─→ AUTH_SPEC.md              (认证授权规范)
    ├─→ BUSINESS_RULES.md         (业务规则SoT)
    ├─→ ERROR_CODES.md            (错误码SoT)
    ├─→ RLS_POLICIES.md           (RLS策略参考,当前未启用)
    └─→ API_DEVELOPMENT_FLOW.md   (API开发流程)
```

### ⚖️ 冲突仲裁规则 (Conflict Resolution)

当文档之间出现冲突时,按以下优先级仲裁:

| 领域 | 最高权威 | 说明 |
|-----|---------|------|
| **数据结构** | `DATA_SCHEMA.md` | 表结构、字段类型、主键、外键、索引、约束 |
| **状态流转** | `STATE_MACHINE.md` | 所有状态字段的枚举值、转换规则、角色权限 |
| **认证授权** | `AUTH_SPEC.md` | Supabase Auth集成、Token验证、权限模型 |
| **错误处理** | `ERROR_CODES.md` | 错误码定义、Envelope格式、HTTP状态码 |
| **业务约束** | `BUSINESS_RULES.md` | 业务规则、验证逻辑、测试用例 |
| **技术栈** | 本文档第1章 | 框架版本、部署架构、工具选型 |

**强制规则**:
- ❌ 禁止基于旧文档/init.sql/历史代码进行开发
- ❌ 禁止引用已废弃的方案(bolt.new、本地JWT、data_clerk角色等)
- ✅ 所有开发必须先查阅本手册和对应SoT文档
- ✅ 发现冲突时必须以本手册的仲裁规则为准

### 📖 阅读指南

**人类开发者**:
1. 首次阅读: 完整阅读第1-6章,理解系统全貌
2. 日常开发: 查阅对应章节 + 引用的SoT文档
3. Code Review: 以本手册为标准检查代码规范

**AI辅助工具** (Claude/Cursor/Copilot):
1. 生成代码前必须加载: 本手册 + 相关SoT文档
2. 严格遵守冲突仲裁规则,禁止自创字段/状态/角色
3. 提交前执行第10章的自检清单

---

## 目录

- [1. 系统架构与原则](#1-系统架构与原则)
  - [1.1 技术栈全景](#11-技术栈全景)
  - [1.2 核心设计原则](#12-核心设计原则)
  - [1.3 目录结构与模块职责](#13-目录结构与模块职责)
- [2. 核心业务模型](#2-核心业务模型)
  - [2.1 角色与权限矩阵](#21-角色与权限矩阵)
  - [2.2 核心实体关系](#22-核心实体关系)
  - [2.3 业务状态机摘要](#23-业务状态机摘要)
- [3. 数据库规范](#3-数据库规范)
  - [3.1 核心表结构定义](#31-核心表结构定义)
  - [3.2 关键字段规范](#32-关键字段规范)
  - [3.3 索引与约束策略](#33-索引与约束策略)
- [4. 安全与认证](#4-安全与认证) *(待生成)*
- [5. 业务规则与约束](#5-业务规则与约束) *(待生成)*
- [6. 开发工作流](#6-开发工作流) *(待生成)*

---

## 1. 系统架构与原则

### 1.1 技术栈全景

#### 前端技术栈

| 组件 | 版本/选型 | 说明 | 配置文件 |
|-----|----------|------|---------|
| **框架** | Next.js 16 | App Router模式 | `package.json` |
| **语言** | TypeScript 5.x | 严格模式 (`strict: true`) | `tsconfig.json` |
| **包管理器** | pnpm 8.x | 固定使用,禁止npm/yarn | `pnpm-lock.yaml` |
| **UI组件** | shadcn/ui | 基于Radix UI | `components.json` |
| **样式** | Tailwind CSS 3.x | 原子化CSS | `tailwind.config.js` |
| **状态管理** | Zustand | 轻量级状态管理 | - |
| **表单** | React Hook Form + Zod | 类型安全的表单验证 | - |
| **API客户端** | 自定义 `lib/api.ts::apiFetch` | 统一请求封装 | `lib/api.ts` |

#### 后端技术栈

| 组件 | 版本/选型 | 说明 | 配置文件 |
|-----|----------|------|---------|
| **框架** | FastAPI 0.109+ | 异步Web框架 | `requirements.txt` |
| **语言** | Python 3.11+ | 类型注解必须 | - |
| **ORM** | SQLAlchemy 2.x | 同步版本 | `backend/core/db.py` |
| **迁移** | Alembic 1.13+ | 数据库版本管理 | `alembic.ini` |
| **验证** | Pydantic v2 | `ConfigDict(from_attributes=True)` | `backend/schemas/*` |
| **认证** | Supabase Auth SDK | 唯一认证方案 | `backend/core/supabase_client.py` |
| **缓存** | Redis 7.x | 仅缓存/速率限制 | `REDIS_URL` |

#### 数据库与基础设施

| 组件 | 版本/选型 | 说明 | 配置 |
|-----|----------|------|-----|
| **数据库** | PostgreSQL 15 | Supabase托管 | `DATABASE_URL` |
| **认证服务** | Supabase Auth | 用户认证、JWT管理 | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` |
| **缓存** | Redis 7.x | 速率限制、短期缓存 | `REDIS_URL` |
| **文件存储** | Supabase Storage | 凭证/附件存储 | `SUPABASE_URL` |

#### 开发工具

| 工具 | 用途 | 配置 |
|-----|------|------|
| **代码检查** | `flake8` + `mypy` | Python静态检查 | `.flake8`, `mypy.ini` |
| **代码格式化** | `black` + `isort` | Python代码格式化 | `pyproject.toml` |
| **前端检查** | ESLint + TypeScript | JS/TS静态检查 | `.eslintrc.json` |
| **测试框架** | `pytest` + Playwright | 后端单测 + 前端E2E | `pytest.ini`, `playwright.config.ts` |

#### 版本固定与兼容性

**强制要求**:
1. ✅ Next.js必须使用App Router (禁止Pages Router)
2. ✅ SQLAlchemy必须使用2.x版本 (禁止1.x的ORM API)
3. ✅ Pydantic必须使用v2 (禁止v1的`orm_mode`)
4. ❌ 禁止引入Celery/RQ等任务队列 (当前未规划)
5. ❌ 禁止使用本地bcrypt/JWT (必须通过Supabase Auth)

---

### 1.2 核心设计原则

#### 1.2.1 SoT策略 (Single Source of Truth)

**原则**: 每类信息只有一个权威来源,所有其他文档/代码必须引用而非重复定义。

| 信息类别 | 唯一来源 | 禁止行为 | 示例 |
|---------|---------|---------|------|
| **表结构** | `DATA_SCHEMA.md` | ❌ 在代码注释/API文档中重复定义字段 | 引用"见DATA_SCHEMA.md 3.3.1" |
| **状态枚举** | `STATE_MACHINE.md` | ❌ 在Service层硬编码状态列表 | 导入`enums.py::ProjectStatus` |
| **错误码** | `ERROR_CODES.md` | ❌ 自创错误码字符串 | 使用`AuthErrorCodes.INVALID_CREDENTIALS.code` |
| **角色定义** | 本文档2.1节 | ❌ 引用旧角色名(`data_clerk`) | 仅使用5个合法角色 |

**违规示例** (禁止):
```python
# ❌ 错误: 硬编码状态列表
if status not in ["draft", "pending", "approved"]:
    raise ValueError("Invalid status")

# ❌ 错误: 自创错误码
raise HTTPException(status_code=401, detail={"code": "LOGIN_FAILED"})
```

**正确示例**:
```python
# ✅ 正确: 引用状态机枚举
from backend.models.enums import ReportStatus
if status not in [s.value for s in ReportStatus]:
    raise BusinessRuleException(
        code=BusinessErrorCodes.INVALID_STATUS.code,
        message="状态无效"
    )
```

#### 1.2.2 Envelope响应格式

**所有API响应必须使用统一的Envelope格式** (定义于 `backend/core/response.py`)

**成功响应**:
```json
{
  "success": true,
  "data": { /* 业务数据 */ },
  "message": "操作成功",
  "code": "SUCCESS",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-11-20T10:30:00Z"
}
```

**失败响应**:
```json
{
  "success": false,
  "error": {
    "code": "AUTH_500",
    "message": "权限不足",
    "detail": { /* 可选的详细信息 */ }
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-11-20T10:30:00Z"
}
```

**字段说明**:
- `request_id`: UUID v4格式,贯穿前后端日志,便于追踪
- `timestamp`: ISO 8601格式的UTC时间戳
- `code`: 必须来自`ERROR_CODES.md`定义的错误码

#### 1.2.3 分层架构约束

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (Next.js App Router)                          │
│  - Server Components + Client Components                │
│  - 通过 lib/api.ts::apiFetch 调用后端                   │
│  ❌ 禁止直接访问 Supabase/数据库                        │
└────────────────┬────────────────────────────────────────┘
                 │ HTTPS + JWT Bearer Token
                 ▼
┌─────────────────────────────────────────────────────────┐
│  BFF层 (FastAPI Backend)                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Router   │→ │ Service  │→ │ Model    │              │
│  │ (路由层) │  │ (业务层) │  │ (数据层) │              │
│  └──────────┘  └──────────┘  └──────────┘              │
│  - Router: 权限校验、参数验证、响应封装                 │
│  - Service: 业务逻辑、事务管理、审计日志                │
│  - Model: SQLAlchemy模型                                │
└────────────────┬────────────────────────────────────────┘
                 │ SQLAlchemy (同步)
                 ▼
┌─────────────────────────────────────────────────────────┐
│  PostgreSQL 15 (Supabase托管)                            │
│  - 当前未启用RLS,所有权限在Service层实现                │
│  - Schema以DATA_SCHEMA.md为准                           │
└─────────────────────────────────────────────────────────┘
```

**层次职责**:

| 层次 | 职责 | 禁止行为 |
|-----|------|---------|
| **Router** | 参数验证(Pydantic)、权限校验(`@require_role`)、响应封装 | ❌ 编写业务逻辑、直接操作数据库 |
| **Service** | 业务规则验证、事务管理、审计日志、数据权限过滤 | ❌ 直接暴露给前端、返回SQLAlchemy对象 |
| **Model** | ORM映射、数据库约束 | ❌ 包含业务逻辑 |

**示例** (正确的分层):
```python
# Router层 (backend/routers/daily_reports.py)
@router.post("/daily-reports")
async def create_report(
    payload: DailyReportCreate,
    service: DailyReportService = Depends(),
    current_user: User = Depends(require_role(["media_buyer"]))
):
    # ✅ 仅负责参数验证、权限校验、调用Service
    report = service.create_report(payload, current_user)
    return success_response(data=DailyReportResponse.model_validate(report))

# Service层 (backend/services/daily_report_service.py)
class DailyReportService:
    def create_report(self, payload: DailyReportCreate, user: User) -> DailyReport:
        # ✅ 执行业务逻辑、数据权限校验、事务管理
        # 1. 校验用户是否有权限访问该ad_account
        if not self._check_account_access(payload.ad_account_id, user):
            raise AuthorizationException(code=AuthErrorCodes.PERMISSION_DENIED.code)

        # 2. 校验业务规则 (如日期不能为未来)
        if payload.report_date > date.today():
            raise BusinessRuleException(code=BusinessErrorCodes.FUTURE_DATE.code)

        # 3. 创建记录并记录审计日志
        with self.db.begin():
            report = DailyReport(**payload.dict(), created_by=user.id)
            self.db.add(report)
            self._create_audit_log("CREATE_REPORT", user, report)

        return report
```

#### 1.2.4 认证与授权原则

**核心原则**: Supabase Auth是唯一的认证方案,禁止自建JWT/密码管理。

**认证流程**:
```
1. 用户注册/登录 → Supabase Auth API
2. Supabase返回JWT (Access Token + Refresh Token)
3. 前端在所有请求中携带 Authorization: Bearer <token>
4. 后端通过Supabase Auth SDK验证Token
5. 从users表查询角色等业务信息
6. Service层根据角色过滤数据
```

**关键约束**:
- ✅ 使用Supabase Auth SDK验证Token (禁止手写JWT验证)
- ✅ 角色信息从`users.role`字段查询 (不依赖JWT Claims)
- ❌ 当前未启用数据库级RLS (所有权限在Service层实现)
- ❌ 禁止在`users`表存储`password_hash` (Supabase Auth已管理)

**权限校验示例**:
```python
# backend/deps/supabase_auth.py
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    # 1. 通过Supabase Auth验证Token
    user_data = await supabase_auth_service.verify_token(credentials.credentials)

    # 2. 从users表查询完整用户信息 (含role)
    if not user_data:
        raise AuthenticationException(code=AuthErrorCodes.INVALID_TOKEN.code)

    return user_data

def require_role(allowed_roles: List[str]):
    async def role_checker(user: Dict = Depends(get_current_user)) -> Dict:
        user_role = user.get("profile", {}).get("role")
        if user_role not in allowed_roles:
            raise AuthorizationException(code=AuthErrorCodes.PERMISSION_DENIED.code)
        return user
    return role_checker
```

---

### 1.3 目录结构与模块职责

#### 后端目录结构

```
backend/
├── alembic/                 # 数据库迁移
│   ├── versions/            # 迁移脚本 (按时间排序)
│   └── env.py               # Alembic配置
├── core/                    # 核心基础设施
│   ├── db.py                # SQLAlchemy引擎
│   ├── supabase_client.py   # Supabase Auth客户端
│   ├── error_codes.py       # 错误码定义
│   ├── response.py          # API响应封装
│   ├── dependencies.py      # FastAPI依赖注入
│   └── logging.py           # 日志配置
├── models/                  # SQLAlchemy模型
│   ├── base.py              # Base模型
│   ├── enums.py             # 枚举定义 (角色、状态等)
│   ├── core/                # 核心实体模型
│   │   ├── user.py          # users表
│   │   └── project.py       # projects表
│   ├── workflow/            # 业务流程模型
│   │   ├── daily_report.py  # daily_reports表
│   │   └── topup.py         # topup_requests表
│   └── finance/             # 财务模型
│       ├── ledger.py        # ledger_entries表
│       └── reconciliation.py # reconciliation_*表
├── schemas/                 # Pydantic模型
│   ├── daily_report.py      # 日报输入/输出Schema
│   ├── topup.py             # 充值输入/输出Schema
│   └── user.py              # 用户输入/输出Schema
├── services/                # 业务逻辑层
│   ├── daily_report_service.py
│   ├── topup_service.py
│   └── project_service.py
├── routers/                 # FastAPI路由
│   ├── daily_reports.py     # 日报API
│   ├── topup.py             # 充值API
│   └── projects.py          # 项目API
├── deps/                    # 依赖注入
│   └── supabase_auth.py     # 认证依赖
├── exceptions/              # 自定义异常
│   └── handlers.py          # 异常处理器
├── tests/                   # 测试
│   ├── unit/                # 单元测试
│   ├── integration/         # 集成测试
│   └── conftest.py          # pytest配置
└── main.py                  # FastAPI应用入口
```

#### 前端目录结构

```
frontend/
├── app/                     # Next.js App Router
│   ├── (auth)/              # 认证相关路由组
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/         # 主应用路由组
│   │   ├── projects/
│   │   ├── reports/
│   │   └── topup/
│   ├── layout.tsx           # 全局布局
│   └── page.tsx             # 首页
├── components/              # 共享组件
│   ├── ui/                  # shadcn/ui组件
│   ├── forms/               # 表单组件
│   └── layouts/             # 布局组件
├── lib/                     # 工具库
│   ├── api.ts               # API客户端 (apiFetch)
│   ├── auth.ts              # Supabase Auth封装
│   └── utils.ts             # 通用工具函数
├── hooks/                   # 自定义Hooks
│   ├── useAuth.ts           # 认证Hook
│   └── useApi.ts            # API调用Hook
├── types/                   # TypeScript类型定义
│   ├── api.ts               # API响应类型
│   └── models.ts            # 业务模型类型
└── public/                  # 静态资源
```

#### 模块职责矩阵

| 模块 | 主要职责 | 输入 | 输出 | 不应包含 |
|-----|---------|------|------|---------|
| **Router** | 接收HTTP请求、参数验证、权限校验 | HTTP Request | Envelope Response | 业务逻辑、数据库操作 |
| **Service** | 业务规则验证、事务管理、数据权限过滤、审计日志 | Pydantic Schema + User | SQLAlchemy Model | 直接处理HTTP请求 |
| **Model** | ORM映射、数据库约束 | SQLAlchemy操作 | Model实例 | 业务逻辑 |
| **Schema** | 输入/输出数据验证、序列化 | JSON/Dict | Pydantic Model | 数据库操作 |

---

## 2. 核心业务模型

### 2.1 角色与权限矩阵

#### 2.1.1 合法角色定义

**系统仅允许5个角色** (定义于 `backend/models/enums.py::UserRole`):

| 角色代码 | 角色名称 | 英文名称 | 数据库值 | 权限级别 |
|---------|---------|---------|---------|---------|
| `admin` | 系统管理员 | Administrator | `"admin"` | L5 (最高) |
| `finance` | 财务 | Finance | `"finance"` | L4 |
| `data_operator` | 数据操作员/户管 | Data Operator | `"data_operator"` | L3 |
| `account_manager` | 客户经理 | Account Manager | `"account_manager"` | L2 |
| `media_buyer` | 投手/媒体采购 | Media Buyer | `"media_buyer"` | L1 (最低) |

**历史兼容说明**:
- ⚠️ 旧角色名 `data_clerk` 已废弃,统一使用 `data_operator`
- ⚠️ 旧角色名 `manager` 已废弃,统一使用 `account_manager`
- ❌ 禁止在新代码中使用旧角色名

#### 2.1.2 角色职责与数据范围

| 角色 | 主要职责 | 数据访问范围 | 典型用例 |
|-----|---------|-------------|---------|
| **admin** | 系统配置、全局审计、紧急干预、用户管理 | 全部数据 (无限制) | 修改系统配置、强制解锁流程、查看所有审计日志 |
| **finance** | 充值终审、资金监控、财务对账、账本管理 | - 所有充值申请<br>- 所有财务数据<br>- 关联项目的基本信息 | 审批充值申请、生成财务报表、对账差异处理 |
| **data_operator** | 日报审核、数据校验、Excel导入导出 | - 负责项目范围内的日报/账户<br>- 所管理投手的数据 | 审核日报、批量导入消费数据、数据质量检查 |
| **account_manager** | 项目维护、成员管理、充值初审 | - 所管理项目及其账户<br>- 项目成员的日报 | 创建项目、分配账户、审核充值申请(初审) |
| **media_buyer** | 日报提交、充值申请、凭证上传 | - 仅分配给自己的账户<br>- 自己提交的日报/充值 | 每日提交广告消费数据、申请充值、上传支付凭证 |

#### 2.1.3 权限矩阵 (核心操作)

| 操作 | admin | finance | data_operator | account_manager | media_buyer | 引用规则 |
|-----|-------|---------|---------------|----------------|-------------|---------|
| **用户管理** |
| 创建用户 | ✅ | ❌ | ❌ | ❌ | ❌ | BR-AUTH-001 |
| 修改他人角色 | ✅ | ❌ | ❌ | ❌ | ❌ | BR-AUTH-001 |
| 禁用用户 | ✅ | ❌ | ❌ | ❌ | ❌ | - |
| **项目管理** |
| 创建项目 | ✅ | ❌ | ❌ | ✅ | ❌ | BR-PROJ-001 |
| 编辑项目 | ✅ | ❌ | ❌ | ✅ (仅自己管理的) | ❌ | - |
| 归档项目 | ✅ | ❌ | ❌ | ✅ (仅自己管理的) | ❌ | - |
| 查看所有项目 | ✅ | ✅ | ✅ | ❌ | ❌ | BR-AUTH-004 |
| **日报管理** |
| 提交日报 | ✅ | ❌ | ❌ | ❌ | ✅ | BR-RPT-001 |
| 审核日报 | ✅ | ❌ | ✅ | ❌ | ❌ | BR-RPT-002 |
| 查看他人日报 | ✅ | ✅ (财务视角) | ✅ (负责范围) | ✅ (项目范围) | ❌ | BR-AUTH-004 |
| **充值管理** |
| 发起充值申请 | ✅ | ❌ | ❌ | ✅ | ✅ | BR-FIN-001 |
| 数据审核 (复核) | ✅ | ❌ | ✅ | ❌ | ❌ | BR-FIN-002 |
| 财务审批 (终审) | ✅ | ✅ | ❌ | ❌ | ❌ | BR-FIN-002 |
| 标记支付完成 | ✅ | ✅ | ❌ | ❌ | ❌ | BR-FIN-004 |
| **对账管理** |
| 创建对账批次 | ✅ | ✅ | ❌ | ❌ | ❌ | BR-RECON-001 |
| 提交对账数据 | ✅ | ❌ | ✅ | ❌ | ❌ | - |
| 确认对账结果 | ✅ | ✅ | ❌ | ❌ | ❌ | - |

**图例**:
- ✅ 允许执行
- ❌ 禁止执行
- ✅ (限定条件) 在特定条件下允许

#### 2.1.4 数据权限过滤规则 (Service层实现)

**实现位置**: `backend/services/*_service.py`

**过滤逻辑**:
```python
class ProjectService:
    def get_projects(self, user: User, filters: ProjectFilters) -> List[Project]:
        query = self.db.query(Project)

        # 根据角色过滤数据
        if user.role == "media_buyer":
            # 投手: 仅查看分配给自己的账户所属的项目
            query = query.join(AdAccount).filter(
                AdAccount.assigned_to == user.id
            ).distinct()

        elif user.role == "account_manager":
            # 客户经理: 查看自己管理的项目 (通过project_members表)
            query = query.join(ProjectMember).filter(
                ProjectMember.user_id == user.id,
                ProjectMember.role.in_(["account_manager", "project_owner"])
            )

        elif user.role in ["admin", "finance", "data_operator"]:
            # 管理员/财务/数据操作员: 全局视野,无需过滤
            pass

        # 应用其他过滤条件
        if filters.status:
            query = query.filter(Project.status == filters.status)

        return query.all()
```

**关键原则**:
- ✅ 数据权限必须在Service层实现 (禁止在Router层过滤)
- ✅ 使用SQL JOIN而非Python循环过滤 (性能优化)
- ✅ 基于`project_members`/`ad_accounts.assigned_to`等关系表判断归属
- ❌ 禁止依赖JWT Claims中的角色 (必须从`users.role`查询)

---

### 2.2 核心实体关系

#### 2.2.1 实体关系图 (ER Diagram)

以下实体关系基于 `DATA_SCHEMA.md` 定义:

```
┌─────────────────────┐
│   users (UUID PK)   │ ◄─────────┐
│  - id (UUID)        │           │
│  - role (enum)      │           │ 多对一
│  - email (unique)   │           │
└──────────┬──────────┘           │
           │ 一对多                │
           │                      │
           ▼                      │
┌─────────────────────┐   ┌──────────────────┐
│ projects (BIGINT PK)│   │ ad_accounts      │
│  - account_manager  ├──►│  - assigned_to   │
│    _id (FK:users)   │   │    (FK:users)    │
└──────────┬──────────┘   └────────┬─────────┘
           │ 一对多                 │ 一对多
           │                       │
           ▼                       ▼
┌─────────────────────┐   ┌──────────────────┐
│ project_members     │   │ daily_reports    │
│  - project_id (FK)  │   │  - ad_account_id │
│  - user_id (FK)     │   │    (FK)          │
└─────────────────────┘   │  - created_by    │
                          │    (FK:users)    │
                          └──────────────────┘

┌─────────────────────┐
│ topup_requests      │
│  - project_id (FK)  │
│  - applicant_id     │
│    (FK:users)       │
│  - status (enum)    │ ───► 引用 STATE_MACHINE.md
└──────────┬──────────┘
           │ 一对多
           ▼
┌─────────────────────┐   ┌──────────────────┐
│ topup_transactions  │   │ ledger_entries   │
│  - topup_request_id │   │  - project_id    │
│    (FK)             │   │    (FK)          │
└─────────────────────┘   │  - amount        │
                          │    (Decimal)     │
                          └──────────────────┘
```

#### 2.2.2 核心实体说明

| 实体 | 主键类型 | 说明 | 关键字段 | 引用文档 |
|-----|---------|------|---------|---------|
| **users** | UUID | 业务用户表,与Supabase Auth同步 | `role`, `email`, `account_manager_id` | DATA_SCHEMA.md 3.1.1 |
| **projects** | BIGSERIAL | 项目主表 | `status`, `account_manager_id`, `budget_total` | DATA_SCHEMA.md 3.2.1 |
| **project_members** | BIGSERIAL | 项目成员关系表 | `project_id`, `user_id`, `role` | DATA_SCHEMA.md 3.2.2 |
| **ad_accounts** | BIGSERIAL | 广告账户表 | `project_id`, `channel_id`, `assigned_to`, `status` | DATA_SCHEMA.md 3.2.9 |
| **daily_reports** | BIGSERIAL | 日报表 | `report_date`, `ad_account_id`, `status`, `spend` | DATA_SCHEMA.md 3.3.1 |
| **topup_requests** | BIGSERIAL | 充值申请表 | `request_no`, `status`, `amount`, `urgency_level` | DATA_SCHEMA.md 3.4.1 |
| **ledger_entries** | BIGSERIAL | 资金总账 | `project_id`, `entry_type`, `amount`, `occurred_at` | DATA_SCHEMA.md 3.4.4 |
| **reconciliation_batches** | BIGSERIAL | 对账批次 | `batch_no`, `status`, `period_start`, `period_end` | DATA_SCHEMA.md 3.5.1 |

#### 2.2.3 关键外键约束

| 外键字段 | 被引用表.字段 | 类型 | ON DELETE | 说明 |
|---------|--------------|------|-----------|------|
| `users.account_manager_id` | `users.id` | UUID | SET NULL | 户管离职时投手不被删除 |
| `projects.account_manager_id` | `users.id` | UUID | RESTRICT | 禁止删除管理项目的用户 |
| `ad_accounts.assigned_to` | `users.id` | UUID | RESTRICT | 禁止删除有分配账户的用户 |
| `ad_accounts.project_id` | `projects.id` | BIGINT | CASCADE | 删除项目时级联删除账户 |
| `daily_reports.ad_account_id` | `ad_accounts.id` | BIGINT | RESTRICT | 禁止删除有日报的账户 |
| `topup_requests.project_id` | `projects.id` | BIGINT | RESTRICT | 禁止删除有充值申请的项目 |

**重要约束**:
- ✅ 外键字段类型必须与被引用主键完全一致
  - 引用`users.id`的字段必须是UUID
  - 引用`projects.id`的字段必须是BIGINT
- ❌ 禁止删除仍有关联数据的记录 (RESTRICT策略)
- ✅ 级联删除需要经过业务逻辑确认 (如归档而非物理删除)

---

### 2.3 业务状态机摘要

> **完整状态机定义**: 详见 `STATE_MACHINE.md`
> 本节仅列出关键状态流转,不重复定义状态枚举值。

#### 2.3.1 日报状态机 (Daily Report Lifecycle)

**状态枚举**: `ReportStatus` (定义于 `backend/models/enums.py`)

```
┌─────────┐   提交      ┌─────────┐   审核通过   ┌──────────┐
│  draft  │ ────────→  │ pending │ ─────────→  │ approved │
└─────────┘            └─────────┘             └──────────┘
     ▲                      │
     │ 驳回                 │ 驳回
     └──────────────────────┘
```

**角色权限**:
- `draft → pending`: `media_buyer` 提交
- `pending → approved`: `data_operator` 审核通过
- `pending → draft`: `data_operator` 驳回

**业务约束**:
- `report_date + ad_account_id` 唯一
- `report_date` 不能为未来日期
- 只有`draft`状态允许编辑

#### 2.3.2 充值状态机 (Topup Request Lifecycle)

**状态枚举**: `TopupStatus` (定义于 `backend/models/enums.py`)

```
┌─────────┐  提交  ┌──────────────┐  复核通过  ┌────────────────┐
│  draft  │ ────→ │ pending_     │ ────────→ │ finance_       │
└─────────┘       │ review       │           │ approve        │
     ▲            └──────────────┘           └────────┬───────┘
     │                   │                            │ 支付
     │ 驳回              │ 驳回                       ▼
     │                   │                    ┌──────────┐
     │                   └────────────────────┤  paid    │
     │                                        └─────┬────┘
     │                                              │ 到账确认
     └──────────────────────────────────────────────▼
                                            ┌──────────────┐
                                            │  completed   │
                                            └──────────────┘

取消路径: draft/pending_review → cancelled
拒绝路径: pending_review/finance_approve → rejected → draft
```

**角色权限**:
- `draft → pending_review`: `media_buyer`/`account_manager` 提交
- `pending_review → finance_approve`: `data_operator` 复核通过
- `finance_approve → paid`: `finance` 审批并标记支付
- `paid → completed`: `finance` 确认到账

**业务约束**:
- 终态(`completed`/`cancelled`/`rejected`)不可再流转
- 状态变更必须记录到`topup_approval_logs`
- `amount`必须大于0且符合精度要求 (Decimal(15,2))

#### 2.3.3 项目状态机 (Project Lifecycle)

**状态枚举**: `ProjectStatus` (定义于 `backend/models/enums.py`)

```
┌─────────┐  激活   ┌────────┐  暂停   ┌───────────┐
│  draft  │ ─────→ │ active │ ─────→ │ suspended │
└─────────┘        └────────┘        └───────────┘
                        │                    │
                        │ 归档               │ 归档
                        ▼                    ▼
                   ┌──────────┐         ┌──────────┐
                   │ archived │ ◄───────│ archived │
                   └──────────┘         └──────────┘
```

**角色权限**:
- `draft → active`: `account_manager` 激活项目
- `active → suspended`: `account_manager` 暂停项目
- `* → archived`: `admin`/`account_manager` 归档项目

**业务约束**:
- `archived`状态禁止编辑/创建关联资源
- 项目归档前需确认无未完成的充值申请

#### 2.3.4 广告账户状态机 (Ad Account Lifecycle)

**状态枚举**: `AccountStatus` (定义于 `backend/models/enums.py`)

```
┌──────┐  测试  ┌────────┐  激活  ┌────────┐
│ new  │ ────→ │testing │ ────→ │ active │
└──────┘       └────────┘       └────────┘
                    │                │
                    │ 暂停           │ 暂停
                    ▼                ▼
               ┌───────────┐    ┌───────────┐
               │ suspended │ ←──│ suspended │
               └───────────┘    └───────────┘
                    │                │
                    │ 死亡           │ 死亡
                    ▼                ▼
               ┌──────┐        ┌──────┐
               │ dead │ ◄──────│ dead │
               └──────┘        └──────┘
                    │
                    │ 归档
                    ▼
               ┌──────────┐
               │ archived │
               └──────────┘
```

**角色权限**:
- `new → testing`: `account_manager` 开始测试
- `testing → active`: `account_manager` 激活账户
- `* → suspended`: `account_manager` 暂停账户
- `* → dead`: `account_manager`/`admin` 标记死亡
- `dead → archived`: `admin` 归档账户

**业务约束**:
- `dead`/`archived`状态禁止提交日报
- 账户暂停时需记录`status_reason`

---

## 3. 数据库规范

> **唯一事实来源**: `DATA_SCHEMA.md`
> 本章节不重复定义表结构,仅提取关键规范和示例。

### 3.1 核心表结构定义

#### 3.1.1 主键类型规范

**强制规则**:

| 表类型 | 主键类型 | 说明 | 示例表 |
|-------|---------|------|--------|
| **用户/认证表** | UUID | 对齐Supabase Auth | `users`, `channels` |
| **核心业务表** | BIGSERIAL | 自增长整数,性能优化 | `projects`, `ad_accounts`, `daily_reports`, `topup_requests` |
| **关系表** | BIGSERIAL | 关联表也使用自增主键 | `project_members`, `topup_approval_logs` |

**修正后的示例** (基于DATA_SCHEMA.md):

```sql
-- ✅ 正确: users表使用UUID主键
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'finance', 'data_operator', 'account_manager', 'media_buyer')),
    account_manager_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ✅ 正确: projects表使用BIGSERIAL主键
CREATE TABLE projects (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL,
    account_manager_id UUID REFERENCES users(id) ON DELETE RESTRICT,  -- 注意: UUID类型
    created_by UUID REFERENCES users(id) ON DELETE RESTRICT,          -- 注意: UUID类型
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ✅ 正确: daily_reports表使用BIGSERIAL主键
CREATE TABLE daily_reports (
    id BIGSERIAL PRIMARY KEY,
    report_date DATE NOT NULL,
    ad_account_id BIGINT REFERENCES ad_accounts(id) ON DELETE RESTRICT,  -- BIGINT类型
    spend DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    status VARCHAR(20) NOT NULL,
    created_by UUID REFERENCES users(id) ON DELETE RESTRICT,             -- UUID类型
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (report_date, ad_account_id)  -- 唯一性约束
);
```

**常见错误** (禁止):
```sql
-- ❌ 错误: users表使用SERIAL而非UUID
CREATE TABLE users (
    id SERIAL PRIMARY KEY,  -- 错误: 应该是UUID
    email VARCHAR(255)
);

-- ❌ 错误: 外键类型不匹配
CREATE TABLE projects (
    id BIGSERIAL PRIMARY KEY,
    account_manager_id INTEGER REFERENCES users(id)  -- 错误: 应该是UUID
);
```

#### 3.1.2 核心表清单

以下表清单来自 `DATA_SCHEMA.md` 第2章,按模块分类:

**用户与权限**:
- `users` (UUID PK) - 业务用户表
- `user_sessions` (BIGSERIAL PK) - 登录会话
- `audit_logs` (BIGSERIAL PK) - 系统级审计日志

**项目/渠道/账户**:
- `projects` (BIGSERIAL PK) - 项目主表
- `project_members` (BIGSERIAL PK) - 项目成员
- `project_expenses` (BIGSERIAL PK) - 项目费用
- `channels` (UUID PK) - 渠道主数据
- `ad_accounts` (BIGSERIAL PK) - 广告账户
- `account_status_history` (BIGSERIAL PK) - 账户状态流水

**日报与投放数据**:
- `daily_reports` (BIGSERIAL PK) - 日报
- `daily_report_audit_logs` (BIGSERIAL PK) - 日报审计日志
- `ad_spend_daily` (UUID PK) - 外部导入日消耗

**充值与资金**:
- `topup_requests` (BIGSERIAL PK) - 充值申请
- `topup_transactions` (BIGSERIAL PK) - 充值到账流水
- `topup_approval_logs` (BIGSERIAL PK) - 充值审批操作记录
- `ledger_entries` (BIGSERIAL PK) - 资金总账

**对账模块**:
- `reconciliation_batches` (BIGSERIAL PK) - 对账批次
- `reconciliation_details` (BIGSERIAL PK) - 对账明细
- `reconciliation_adjustments` (BIGSERIAL PK) - 对账调整
- `reconciliation_reports` (BIGSERIAL PK) - 对账报告

---

### 3.2 关键字段规范

#### 3.2.1 金额字段规范

**强制要求**:
- ✅ 所有金额字段必须使用 `DECIMAL(15,2)` 类型
- ✅ 默认值为 `0.00`
- ✅ 必须添加非负约束 (除非业务明确允许负值)
- ❌ 禁止使用 `FLOAT`/`DOUBLE` (精度问题)

**示例**:
```sql
CREATE TABLE topup_requests (
    id BIGSERIAL PRIMARY KEY,
    amount DECIMAL(15,2) NOT NULL DEFAULT 0.00 CHECK (amount > 0),  -- 充值金额必须大于0
    currency VARCHAR(10) DEFAULT 'CNY'
);

CREATE TABLE ledger_entries (
    id BIGSERIAL PRIMARY KEY,
    amount DECIMAL(15,2) NOT NULL,  -- 允许负值 (贷方记账)
    entry_type VARCHAR(20) NOT NULL,
    notes TEXT
);
```

**Python代码中的处理**:
```python
from decimal import Decimal
from pydantic import BaseModel, Field

class TopupCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)  # 必须大于0,保留2位小数
    currency: str = "CNY"

# SQLAlchemy模型
from sqlalchemy import Column, Numeric
class TopupRequest(Base):
    __tablename__ = "topup_requests"
    amount = Column(Numeric(15, 2), nullable=False, default=0.00)
```

#### 3.2.2 时间字段规范

**强制要求**:
- ✅ 所有时间字段必须使用 `TIMESTAMPTZ` (带时区)
- ✅ 创建时间默认值为 `NOW()`
- ✅ 应用层统一使用UTC时间
- ✅ 更新时间通过触发器自动维护

**示例**:
```sql
CREATE TABLE daily_reports (
    id BIGSERIAL PRIMARY KEY,
    report_date DATE NOT NULL,  -- 业务日期 (无时区)
    created_at TIMESTAMPTZ DEFAULT NOW(),  -- 创建时间 (带时区)
    updated_at TIMESTAMPTZ DEFAULT NOW(),  -- 更新时间 (带时区)
    submitted_at TIMESTAMPTZ,              -- 提交时间 (可空)
    approved_at TIMESTAMPTZ                -- 审批时间 (可空)
);

-- 触发器: 自动更新updated_at
CREATE TRIGGER update_daily_reports_updated_at
    BEFORE UPDATE ON daily_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

**Python代码中的处理**:
```python
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class DailyReportCreate(BaseModel):
    report_date: date  # 业务日期

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()  # ISO 8601格式
        }

# 获取当前UTC时间
now = datetime.now(timezone.utc)
```

#### 3.2.3 状态字段规范

**强制要求**:
- ✅ 状态字段必须使用 `VARCHAR(20)` 类型
- ✅ 必须添加 `CHECK` 约束引用状态机枚举值
- ✅ 在字段说明中注明"枚举值以STATE_MACHINE.md为准"
- ❌ 禁止在数据库层使用PostgreSQL ENUM类型 (迁移不便)

**示例**:
```sql
CREATE TABLE daily_reports (
    id BIGSERIAL PRIMARY KEY,
    status VARCHAR(20) NOT NULL CHECK (status IN ('draft', 'pending', 'approved', 'rejected')),
    status_reason TEXT  -- 状态变更原因 (可选)
);

-- 不推荐: 使用PostgreSQL ENUM (迁移时需要ALTER TYPE)
-- CREATE TYPE report_status AS ENUM ('draft', 'pending', 'approved');
```

**Python代码中的处理**:
```python
# backend/models/enums.py
from enum import Enum

class ReportStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

# SQLAlchemy模型
from sqlalchemy import Column, String, CheckConstraint
class DailyReport(Base):
    __tablename__ = "daily_reports"
    status = Column(
        String(20),
        nullable=False,
        default=ReportStatus.DRAFT.value
    )
    __table_args__ = (
        CheckConstraint(
            status.in_([s.value for s in ReportStatus]),
            name='check_daily_report_status'
        ),
    )
```

#### 3.2.4 角色字段规范

**强制要求**:
- ✅ 角色字段必须使用 `VARCHAR(20)` 类型
- ✅ 必须添加 `CHECK` 约束仅允许5个合法角色
- ✅ 不允许为空 (`NOT NULL`)
- ❌ 禁止使用旧角色名 (`data_clerk`, `manager`)

**示例**:
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    role VARCHAR(20) NOT NULL CHECK (role IN (
        'admin',
        'finance',
        'data_operator',
        'account_manager',
        'media_buyer'
    ))
);
```

**Python代码中的处理**:
```python
# backend/models/enums.py
class UserRole(str, Enum):
    ADMIN = "admin"
    FINANCE = "finance"
    DATA_OPERATOR = "data_operator"
    ACCOUNT_MANAGER = "account_manager"
    MEDIA_BUYER = "media_buyer"

# Pydantic Schema
from pydantic import BaseModel, Field
class UserCreate(BaseModel):
    role: UserRole = Field(default=UserRole.MEDIA_BUYER)  # 默认最低权限角色
```

---

### 3.3 索引与约束策略

#### 3.3.1 唯一性约束

**强制要求**:
- ✅ 业务唯一键必须建立 `UNIQUE` 约束
- ✅ 唯一约束自动创建索引
- ✅ 在模型层同步校验唯一性

**关键唯一约束**:

| 表 | 唯一约束 | 说明 |
|----|---------|------|
| `users` | `email` | 邮箱全局唯一 |
| `users` | `username` | 用户名全局唯一 |
| `projects` | `name` (可选) | 项目名称建议唯一 |
| `ad_accounts` | `account_code` | 平台编号唯一 |
| `daily_reports` | `(report_date, ad_account_id)` | 每个账户每天只能有一条日报 |
| `topup_requests` | `request_no` | 充值流水号唯一 |
| `reconciliation_batches` | `batch_no` | 对账批次号唯一 |

**示例**:
```sql
-- 单列唯一约束
CREATE UNIQUE INDEX users_email_key ON users(email);

-- 组合唯一约束
CREATE UNIQUE INDEX daily_reports_date_account_key
    ON daily_reports(report_date, ad_account_id);
```

#### 3.3.2 外键约束

**强制要求**:
- ✅ 所有关联字段必须定义外键约束
- ✅ 外键字段类型必须与被引用主键完全一致
- ✅ 明确指定 `ON DELETE` 策略

**常用策略**:

| 策略 | 说明 | 适用场景 |
|-----|------|---------|
| `RESTRICT` | 禁止删除被引用记录 | 核心业务关联 (如禁止删除有日报的账户) |
| `CASCADE` | 级联删除关联记录 | 父子关系 (如删除项目时删除成员) |
| `SET NULL` | 设置为NULL | 可选关联 (如户管离职时投手的account_manager_id) |
| `SET DEFAULT` | 设置为默认值 | 极少使用 |

**示例**:
```sql
-- RESTRICT: 禁止删除有日报的账户
CREATE TABLE daily_reports (
    ad_account_id BIGINT NOT NULL REFERENCES ad_accounts(id) ON DELETE RESTRICT
);

-- CASCADE: 删除项目时级联删除成员
CREATE TABLE project_members (
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE
);

-- SET NULL: 户管离职时投手不被删除
CREATE TABLE users (
    account_manager_id UUID REFERENCES users(id) ON DELETE SET NULL
);
```

#### 3.3.3 性能索引

**索引策略**:

| 索引类型 | 使用场景 | 示例 |
|---------|---------|------|
| **单列索引** | 高频查询字段 | `status`, `created_at`, `user_id` |
| **组合索引** | 多字段联合查询 | `(project_id, status)`, `(report_date, ad_account_id)` |
| **部分索引** | 过滤特定值 | `WHERE status != 'archived'` |
| **CONCURRENTLY** | 生产环境创建索引 | `CREATE INDEX CONCURRENTLY` |

**示例**:
```sql
-- 单列索引
CREATE INDEX idx_daily_reports_status ON daily_reports(status);
CREATE INDEX idx_daily_reports_created_at ON daily_reports(created_at);

-- 组合索引 (按查询频率排序字段)
CREATE INDEX idx_topup_requests_project_status
    ON topup_requests(project_id, status);

-- 部分索引 (仅索引活跃记录)
CREATE INDEX idx_projects_active
    ON projects(account_manager_id)
    WHERE status != 'archived';

-- 生产环境创建索引 (不锁表)
CREATE INDEX CONCURRENTLY idx_ledger_project_occurred
    ON ledger_entries(project_id, occurred_at);
```

#### 3.3.4 CHECK约束

**强制要求**:
- ✅ 枚举字段必须添加 `CHECK` 约束
- ✅ 数值字段添加范围约束
- ✅ 金额字段添加非负约束 (如需要)

**示例**:
```sql
CREATE TABLE topup_requests (
    id BIGSERIAL PRIMARY KEY,
    amount DECIMAL(15,2) NOT NULL CHECK (amount > 0),  -- 金额必须大于0
    urgency_level VARCHAR(20) CHECK (urgency_level IN ('low', 'normal', 'high', 'urgent')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('draft', 'pending_review', 'finance_approve', 'paid', 'completed', 'rejected', 'cancelled'))
);

CREATE TABLE ad_accounts (
    daily_budget DECIMAL(15,2) CHECK (daily_budget >= 0),  -- 预算非负
    total_budget DECIMAL(15,2) CHECK (total_budget >= 0)
);
```

---

## 4. 安全与认证

### 4.1 认证流程详解

#### 4.1.1 Supabase Auth集成架构

**核心原则**: Supabase Auth是系统唯一的认证方案,禁止自建JWT/密码管理。

```
┌─────────────────────────────────────────────────────────────┐
│                    前端 (Next.js)                            │
│  1. 调用 Supabase Auth SDK                                   │
│  2. 存储 Access Token + Refresh Token                       │
│  3. 所有API请求携带 Bearer Token                             │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS + JWT Bearer Token
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               后端 (FastAPI)                                 │
│  ┌──────────────────────────────────────────────┐           │
│  │ 1. 提取 Authorization Header                │           │
│  │ 2. 调用 Supabase Auth SDK 验证 Token       │           │
│  │ 3. 从 users 表查询完整用户信息 (含role)    │           │
│  │ 4. 注入 current_user 到依赖                │           │
│  └──────────────────────────────────────────────┘           │
└────────────────────────┬────────────────────────────────────┘
                         │ Token 验证请求
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               Supabase Auth Service                          │
│  - 验证 JWT 签名                                             │
│  - 检查 Token 过期时间                                       │
│  - 返回用户身份信息                                          │
└─────────────────────────────────────────────────────────────┘
```

#### 4.1.2 用户注册流程

```python
# 前端 (TypeScript)
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'SecurePassword123!',
  options: {
    data: {
      full_name: '张三',
      role: 'media_buyer'  # 默认角色
    }
  }
})

# 后端 (Python) - Supabase Webhook 触发
# 在 users 表创建业务用户记录
@router.post("/webhooks/auth/user-created")
async def handle_user_created(payload: dict):
    user_id = payload['record']['id']  # UUID from Supabase Auth
    email = payload['record']['email']

    # 创建业务用户记录
    user = User(
        id=user_id,  # 使用 Supabase Auth 的 UUID
        email=email,
        role='media_buyer',  # 默认最低权限角色
        is_active=True
    )
    db.add(user)
    db.commit()
```

#### 4.1.3 Token验证流程

```python
# backend/services/supabase_auth_service.py
class SupabaseAuthService:
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        通过 Supabase Auth 验证 JWT Token

        流程:
        1. 调用 supabase.auth.get_user(token) 验证 Token
        2. 从返回的 user 对象获取 user_id
        3. 查询 users 表获取完整用户信息 (含 role)
        4. 返回用户对象

        禁止:
        - 手写 jwt.decode() 签名验证
        - 手写 Token 黑名单检查
        - 手写 jti 验证
        """
        try:
            # 通过 Supabase Auth 验证 Token
            response = self.client.auth.get_user(token)

            if not response.user:
                return None

            # 从 users 表查询完整用户信息 (含 role)
            profile = await self._get_user_profile(response.user.id)

            return {
                "user": response.user,
                "profile": profile  # 包含 role 字段
            }
        except Exception:
            return None

    async def _get_user_profile(self, user_id: str) -> Optional[Dict]:
        """从 users 表查询用户资料"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        return {
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name,
            "is_active": user.is_active
        }
```

#### 4.1.4 权限校验依赖

```python
# backend/deps/supabase_auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    基础认证: 验证 Token 并返回用户对象
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_400",
                "message": "未提供认证令牌"
            }
        )

    # 通过 Supabase Auth 验证 Token
    user_data = await supabase_auth_service.verify_token(credentials.credentials)

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_401",
                "message": "无效的认证令牌"
            }
        )

    # 检查用户是否被禁用
    if not user_data.get("profile", {}).get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "AUTH_002",
                "message": "账户已被禁用"
            }
        )

    return user_data


def require_role(allowed_roles: List[str]):
    """
    角色权限校验装饰器

    使用示例:
    @router.post("/projects")
    async def create_project(
        current_user: Dict = Depends(require_role(["admin", "account_manager"]))
    ):
        ...
    """
    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        user_role = current_user.get("profile", {}).get("role")

        if not user_role or user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "AUTH_500",
                    "message": f"需要以下角色之一: {', '.join(allowed_roles)}"
                }
            )

        return current_user

    return role_checker


# 便捷别名
require_admin = Depends(require_role(["admin"]))
require_finance = Depends(require_role(["admin", "finance"]))
require_data_operator = Depends(require_role(["admin", "data_operator"]))
```

---

### 4.2 环境变量与配置安全 🔒

#### 4.2.1 强制要求

**核心原则**: 所有敏感配置必须通过环境变量注入,严禁硬编码。

| 要求 | 说明 | 违规后果 |
|-----|------|---------|
| **✅ 必须提供 `.env.example`** | 所有环境变量必须在示例文件中列出 (敏感值使用占位符) | Code Review 不通过 |
| **❌ 禁止硬编码密钥** | 代码中不得出现真实的API Key/Secret/密码 | 安全审计失败,立即回滚 |
| **✅ 使用 Secret 管理** | 生产环境使用 Secret Manager (AWS Secrets/Vault) | 部署检查项 |
| **❌ 禁止提交 `.env`** | `.env` 文件必须在 `.gitignore` 中 | 提交前自动检查 |

#### 4.2.2 标准 `.env.example` 模板

**后端环境变量** (`backend/.env.example`):

```bash
# ========== 数据库配置 ==========
DATABASE_URL=postgresql://user:password@host:5432/dbname
# 示例: postgresql://postgres:password@localhost:5432/ai_ad_spend

# ========== Supabase 配置 ==========
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
# ⚠️ SERVICE_ROLE_KEY 拥有管理员权限,仅用于后端,禁止暴露给前端

# ========== Redis 配置 ==========
REDIS_URL=redis://localhost:6379/0
# 用于缓存和速率限制

# ========== 应用配置 ==========
ENVIRONMENT=development  # development | staging | production
DEBUG=true               # 生产环境必须为 false
SECRET_KEY=your-secret-key-for-session-signing
# 生成方式: python -c "import secrets; print(secrets.token_urlsafe(32))"

# ========== CORS 配置 ==========
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
# 生产环境示例: https://app.example.com

# ========== 日志配置 ==========
LOG_LEVEL=INFO  # DEBUG | INFO | WARNING | ERROR
SENTRY_DSN=     # 可选: Sentry错误追踪

# ========== 功能开关 ==========
ENABLE_RLS=false  # 当前未启用数据库级RLS
ENABLE_RATE_LIMITING=true
```

**前端环境变量** (`frontend/.env.local.example`):

```bash
# ========== Supabase 公开配置 ==========
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
# ⚠️ ANON_KEY 可以暴露给前端,但权限受限

# ========== API 配置 ==========
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
# 生产环境示例: https://api.example.com

# ========== 应用配置 ==========
NEXT_PUBLIC_ENVIRONMENT=development
NEXT_PUBLIC_APP_NAME=AI广告代投系统
```

#### 4.2.3 配置加载与验证

**后端配置管理** (`backend/core/settings.py`):

```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str

    # Supabase 配置
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str

    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # 应用配置
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str

    # CORS 配置
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # 功能开关
    ENABLE_RLS: bool = False
    ENABLE_RATE_LIMITING: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_production_settings()

    def _validate_production_settings(self):
        """生产环境安全检查"""
        if self.ENVIRONMENT == "production":
            # 生产环境强制要求
            assert not self.DEBUG, "生产环境禁止开启DEBUG模式"
            assert "localhost" not in self.ALLOWED_ORIGINS, "生产环境禁止允许localhost跨域"
            assert len(self.SECRET_KEY) >= 32, "SECRET_KEY长度必须>=32字符"

settings = Settings()
```

**前端配置管理** (`frontend/lib/env.ts`):

```typescript
// 环境变量类型定义
interface EnvConfig {
  supabase: {
    url: string;
    anonKey: string;
  };
  api: {
    baseUrl: string;
  };
  app: {
    environment: 'development' | 'staging' | 'production';
    name: string;
  };
}

// 环境变量验证
function validateEnv(): EnvConfig {
  const requiredVars = [
    'NEXT_PUBLIC_SUPABASE_URL',
    'NEXT_PUBLIC_SUPABASE_ANON_KEY',
    'NEXT_PUBLIC_API_BASE_URL'
  ];

  for (const varName of requiredVars) {
    if (!process.env[varName]) {
      throw new Error(`缺少必需的环境变量: ${varName}`);
    }
  }

  return {
    supabase: {
      url: process.env.NEXT_PUBLIC_SUPABASE_URL!,
      anonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    },
    api: {
      baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL!
    },
    app: {
      environment: (process.env.NEXT_PUBLIC_ENVIRONMENT as any) || 'development',
      name: process.env.NEXT_PUBLIC_APP_NAME || 'AI广告代投系统'
    }
  };
}

export const env = validateEnv();
```

#### 4.2.4 密钥管理最佳实践

| 场景 | 推荐方案 | 禁止方案 |
|-----|---------|---------|
| **本地开发** | `.env` 文件 (不提交到Git) | ❌ 硬编码在代码中 |
| **CI/CD** | GitHub Secrets / GitLab Variables | ❌ 明文写在 `.github/workflows/` |
| **生产部署** | AWS Secrets Manager / HashiCorp Vault | ❌ 明文环境变量 |
| **密钥轮换** | 定期更新 (每90天) | ❌ 永久不变的密钥 |

**密钥生成命令**:
```bash
# SECRET_KEY 生成
python -c "import secrets; print(secrets.token_urlsafe(32))"

# JWT_SECRET 生成 (Supabase自动生成,不需要手动创建)
```

---

### 4.3 时区处理规范 ⏰

#### 4.3.1 时区处理原则

**核心原则**: 后端统一使用UTC时间存储,前端负责转换为用户本地时区显示。

```
┌─────────────────────────────────────────────────────────────┐
│  前端 (Next.js)                                              │
│  - 用户输入: 本地时区 (Asia/Shanghai)                        │
│  - 发送给后端: 转换为UTC                                     │
│  - 显示给用户: UTC → 本地时区                                │
└────────────────────────┬────────────────────────────────────┘
                         │ ISO 8601 UTC格式
                         │ 2025-11-20T10:30:00Z
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  后端 (FastAPI)                                              │
│  - 存储: TIMESTAMPTZ (PostgreSQL自动处理时区)                │
│  - 处理: datetime.now(timezone.utc)                          │
│  - 返回: ISO 8601 UTC格式                                    │
└────────────────────────┬────────────────────────────────────┘
                         │ TIMESTAMPTZ
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  数据库 (PostgreSQL)                                         │
│  - 字段类型: TIMESTAMPTZ                                     │
│  - 存储: UTC时间戳                                           │
│  - NOW() 返回: UTC时间                                       │
└─────────────────────────────────────────────────────────────┘
```

#### 4.3.2 后端时间处理

**强制要求**:
- ✅ 所有时间字段使用 `TIMESTAMPTZ` 类型
- ✅ Python代码中使用 `datetime.now(timezone.utc)`
- ✅ API响应使用 ISO 8601 格式 (含时区标识 `Z`)
- ❌ 禁止使用 `datetime.now()` (无时区信息)

**后端代码示例**:
```python
from datetime import datetime, timezone
from pydantic import BaseModel, Field

# Pydantic Schema
class DailyReportCreate(BaseModel):
    report_date: date  # 业务日期 (不含时区)
    spend: Decimal

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()  # 自动转换为ISO 8601格式
        }

# SQLAlchemy Model
from sqlalchemy import Column, DateTime
class DailyReport(Base):
    __tablename__ = "daily_reports"
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat()  # 2025-11-20T10:30:00+00:00
        }

# Service层
class DailyReportService:
    def create_report(self, payload: DailyReportCreate) -> DailyReport:
        # ✅ 正确: 使用UTC时间
        now = datetime.now(timezone.utc)

        report = DailyReport(
            report_date=payload.report_date,
            spend=payload.spend,
            created_at=now,  # UTC时间
            updated_at=now
        )

        return report
```

**API响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 12345,
    "report_date": "2025-11-20",  // 业务日期 (无时区)
    "created_at": "2025-11-20T10:30:00Z",  // UTC时间 (ISO 8601)
    "submitted_at": "2025-11-20T11:45:00Z"
  },
  "timestamp": "2025-11-20T12:00:00Z"  // 响应时间戳 (UTC)
}
```

#### 4.3.3 前端时区转换

**前端时区处理库**: 推荐使用 `date-fns` + `date-fns-tz`

**安装**:
```bash
pnpm add date-fns date-fns-tz
```

**前端代码示例**:
```typescript
// lib/datetime.ts
import { format, parseISO } from 'date-fns';
import { formatInTimeZone, utcToZonedTime } from 'date-fns-tz';

/**
 * 将UTC时间转换为用户本地时区显示
 * @param utcDateString - ISO 8601 UTC格式字符串 (如 "2025-11-20T10:30:00Z")
 * @param formatString - 显示格式 (如 "yyyy-MM-dd HH:mm:ss")
 * @returns 本地时区格式化字符串
 */
export function formatUTCToLocal(
  utcDateString: string,
  formatString: string = 'yyyy-MM-dd HH:mm:ss'
): string {
  // 获取用户浏览器时区
  const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  // 将UTC时间转换为本地时区
  return formatInTimeZone(
    parseISO(utcDateString),
    userTimezone,
    formatString
  );
}

/**
 * 将本地时间转换为UTC发送给后端
 * @param localDate - 本地Date对象
 * @returns ISO 8601 UTC格式字符串
 */
export function formatLocalToUTC(localDate: Date): string {
  return localDate.toISOString();  // 自动转换为UTC
}

/**
 * 显示相对时间 (如 "2小时前")
 */
export function formatRelativeTime(utcDateString: string): string {
  const date = parseISO(utcDateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();

  const diffMinutes = Math.floor(diffMs / 60000);
  if (diffMinutes < 1) return '刚刚';
  if (diffMinutes < 60) return `${diffMinutes}分钟前`;

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}小时前`;

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}天前`;

  // 超过7天显示完整日期
  return formatUTCToLocal(utcDateString, 'yyyy-MM-dd');
}
```

**React组件使用示例**:
```typescript
// components/DateTimeDisplay.tsx
import { formatUTCToLocal, formatRelativeTime } from '@/lib/datetime';

interface DateTimeDisplayProps {
  utcDateString: string;
  showRelative?: boolean;
}

export function DateTimeDisplay({ utcDateString, showRelative = false }: DateTimeDisplayProps) {
  if (showRelative) {
    return <span title={formatUTCToLocal(utcDateString)}>{formatRelativeTime(utcDateString)}</span>;
  }

  return <span>{formatUTCToLocal(utcDateString)}</span>;
}

// 使用示例
<DateTimeDisplay utcDateString="2025-11-20T10:30:00Z" />
// 显示: 2025-11-20 18:30:00 (假设用户在 Asia/Shanghai 时区)

<DateTimeDisplay utcDateString="2025-11-20T10:30:00Z" showRelative />
// 显示: 2小时前
```

**表单提交示例**:
```typescript
// components/DailyReportForm.tsx
import { formatLocalToUTC } from '@/lib/datetime';

function handleSubmit(e: FormEvent) {
  e.preventDefault();

  const formData = {
    report_date: selectedDate,  // 业务日期 (date类型,无时区)
    spend: spendAmount,
    // ✅ 如果需要发送时间戳,转换为UTC
    submitted_at: formatLocalToUTC(new Date())  // ISO 8601 UTC格式
  };

  await apiFetch('/api/v1/daily-reports', {
    method: 'POST',
    body: JSON.stringify(formData)
  });
}
```

#### 4.3.4 时区相关业务规则

| 场景 | 处理方式 | 示例 |
|-----|---------|------|
| **日报截止时间** | 以项目配置的时区为准 | 项目时区为 `Asia/Shanghai`,则每日23:59:59之前可提交 |
| **充值审批时效** | 后端计算时间差,不受时区影响 | 72小时内必须审批 (基于UTC时间戳计算) |
| **对账周期** | 以自然月为单位,使用项目时区 | 2025年11月对账 = 2025-11-01 00:00:00 ~ 2025-11-30 23:59:59 (Asia/Shanghai) |
| **审计日志** | 统一显示UTC时间 + 用户本地时间 | `created_at: 2025-11-20T10:30:00Z (本地: 2025-11-20 18:30:00)` |

---

### 4.4 敏感数据保护

#### 4.4.1 数据分类

| 分类 | 示例 | 保护措施 |
|-----|------|---------|
| **高敏感** | 密码、支付凭证、API Key | - 加密存储<br>- 禁止日志输出<br>- 定期轮换 |
| **中敏感** | 邮箱、手机号、真实姓名 | - 访问日志记录<br>- 脱敏显示 (如 `138****1234`) |
| **低敏感** | 项目名称、广告消费数据 | - 基于角色的访问控制 |
| **公开** | 渠道列表、系统配置 | - 无特殊保护 |

#### 4.4.2 日志脱敏

**后端日志配置** (`backend/core/logging.py`):
```python
import logging
import re

class SensitiveDataFilter(logging.Filter):
    """敏感数据脱敏过滤器"""

    SENSITIVE_PATTERNS = [
        (re.compile(r'password["\']?\s*[:=]\s*["\']?([^"\']+)["\']?', re.I), 'password=***'),
        (re.compile(r'token["\']?\s*[:=]\s*["\']?([^"\']+)["\']?', re.I), 'token=***'),
        (re.compile(r'secret["\']?\s*[:=]\s*["\']?([^"\']+)["\']?', re.I), 'secret=***'),
        (re.compile(r'(\d{11})', re.I), r'\1***\2'),  # 手机号脱敏
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            message = pattern.sub(replacement, message)
        record.msg = message
        return True

# 应用过滤器
logger = logging.getLogger(__name__)
logger.addFilter(SensitiveDataFilter())
```

---

## 5. 业务规则与约束

### 5.1 核心业务规则引用

**完整业务规则详见**: `BUSINESS_RULES.md`

本章节仅列出核心约束,不重复定义完整规则。

#### 5.1.1 认证授权规则

| 规则编号 | 规则名称 | 约束摘要 | 引用文档 |
|---------|---------|---------|---------|
| **BR-AUTH-001** | 用户角色唯一性 | 每个用户有且仅有一个角色,不可自行变更 | BUSINESS_RULES.md 3.1 |
| **BR-AUTH-002** | 密码强度要求 | 长度≥8,含数字+字母+特殊字符 | BUSINESS_RULES.md 3.2 |
| **BR-AUTH-003** | 会话超时与续期 | Access Token 15分钟, Refresh Token 7天 | BUSINESS_RULES.md 3.3 |
| **BR-AUTH-004** | 最小权限原则 | 默认拒绝策略,未明确授权的操作禁止 | BUSINESS_RULES.md 3.4 |

#### 5.1.2 用户管理规则

| 规则编号 | 规则名称 | 约束摘要 | 引用文档 |
|---------|---------|---------|---------|
| **BR-USER-001** | 用户名唯一性 | 用户名全局唯一,不区分大小写 | BUSINESS_RULES.md 4.1 |
| **BR-USER-002** | 邮箱唯一性与验证 | 邮箱全局唯一,符合RFC 5322标准 | BUSINESS_RULES.md 4.2 |
| **BR-USER-003** | 户管分配规则 | 投手必须关联户管,户管可管理多个投手 | BUSINESS_RULES.md 4.3 |

---

### 5.2 流程约束与终态保护 🔒

#### 5.2.1 禁止物理删除原则

**核心原则**: 核心业务数据**禁止物理删除**,必须通过状态机流转至终态 (`archived`/`cancelled`)。

**适用范围**:

| 实体 | 禁止物理删除 | 终态 | 终态后的操作限制 |
|-----|------------|------|----------------|
| **projects** | ✅ 是 | `archived` | - 禁止编辑<br>- 禁止创建新账户/充值<br>- 可查看历史数据 |
| **ad_accounts** | ✅ 是 | `archived` | - 禁止提交日报<br>- 禁止修改配置<br>- 可查看历史日报 |
| **daily_reports** | ✅ 是 | `approved`/`rejected` | - 终态后禁止编辑<br>- 可重新提交(创建新记录) |
| **topup_requests** | ✅ 是 | `completed`/`cancelled`/`rejected` | - 终态后禁止修改<br>- 可查看审批历史 |
| **users** | ✅ 是 | 使用 `is_active=false` | - 禁用而非删除<br>- 保留审计日志 |

**实现示例**:

```python
# ❌ 错误: 物理删除
@router.delete("/projects/{project_id}")
async def delete_project(project_id: int):
    db.query(Project).filter(Project.id == project_id).delete()  # 禁止!
    db.commit()

# ✅ 正确: 归档操作
@router.post("/projects/{project_id}/archive")
async def archive_project(
    project_id: int,
    service: ProjectService = Depends(),
    current_user: Dict = Depends(require_role(["admin", "account_manager"]))
):
    """
    将项目归档 (逻辑删除)

    业务规则:
    - 归档前检查: 无未完成的充值申请
    - 归档前检查: 无处于active状态的广告账户
    - 归档操作记录审计日志
    """
    project = service.archive_project(project_id, current_user)
    return success_response(
        data=ProjectResponse.model_validate(project),
        message="项目已归档"
    )

# Service层实现
class ProjectService:
    def archive_project(self, project_id: int, user: Dict) -> Project:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ResourceNotFoundException(code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code)

        # 业务规则检查
        if project.status == "archived":
            raise BusinessRuleException(
                code=BusinessErrorCodes.INVALID_OPERATION.code,
                message="项目已归档,无需重复操作"
            )

        # 检查是否有未完成的充值申请
        pending_topups = self.db.query(TopupRequest).filter(
            TopupRequest.project_id == project_id,
            TopupRequest.status.notin_(["completed", "cancelled", "rejected"])
        ).count()

        if pending_topups > 0:
            raise BusinessRuleException(
                code=BusinessErrorCodes.INVALID_OPERATION.code,
                message=f"项目还有 {pending_topups} 个未完成的充值申请,无法归档"
            )

        # 执行归档操作
        with self.db.begin():
            project.status = "archived"
            project.updated_at = datetime.now(timezone.utc)
            project.updated_by = user.get("user", {}).id

            # 记录审计日志
            self._create_audit_log(
                action="ARCHIVE_PROJECT",
                entity_id=str(project.id),
                user=user,
                payload_before={"status": project.status},
                payload_after={"status": "archived"}
            )

        return project
```

#### 5.2.2 终态保护规则

**规则定义**:
1. **终态不可流转**: 一旦进入终态,禁止再次变更状态
2. **终态数据不可编辑**: 终态记录禁止修改业务字段
3. **级联归档**: 父实体归档时,检查子实体状态

**状态机终态定义**:

| 状态机 | 终态列表 | 说明 |
|-------|---------|------|
| **日报状态机** | `approved`, `rejected` | 审核完成后不可再编辑 |
| **充值状态机** | `completed`, `cancelled`, `rejected` | 完成/取消/拒绝后不可逆转 |
| **项目状态机** | `archived` | 归档后仅可查看,不可恢复 |
| **账户状态机** | `archived` | 归档后仅可查看,不可恢复 |

**终态检查示例**:
```python
# Service层
class DailyReportService:
    def update_report(self, report_id: int, updates: DailyReportUpdate) -> DailyReport:
        report = self.db.query(DailyReport).filter(DailyReport.id == report_id).first()

        # 终态保护检查
        FINAL_STATUSES = ["approved", "rejected"]
        if report.status in FINAL_STATUSES:
            raise BusinessRuleException(
                code=BusinessErrorCodes.INVALID_OPERATION.code,
                message=f"日报状态为 {report.status},无法编辑"
            )

        # 允许编辑
        for key, value in updates.dict(exclude_unset=True).items():
            setattr(report, key, value)

        self.db.commit()
        return report
```

---

### 5.3 数据一致性约束

#### 5.3.1 唯一性约束

**强制要求**:
- ✅ 业务唯一键必须在数据库层和应用层同时校验
- ✅ 唯一性冲突必须返回明确的错误码 (`DB_004` 或 `BIZ_003`)

**示例**:
```python
# Service层唯一性检查
class DailyReportService:
    def create_report(self, payload: DailyReportCreate, user: Dict) -> DailyReport:
        # 检查 report_date + ad_account_id 唯一性
        existing = self.db.query(DailyReport).filter(
            DailyReport.report_date == payload.report_date,
            DailyReport.ad_account_id == payload.ad_account_id
        ).first()

        if existing:
            raise ConflictException(
                code=BusinessErrorCodes.RESOURCE_ALREADY_EXISTS.code,
                message=f"日期 {payload.report_date} 的日报已存在"
            )

        # 创建记录
        report = DailyReport(**payload.dict(), created_by=user.get("user", {}).id)
        self.db.add(report)
        self.db.commit()
        return report
```

#### 5.3.2 外键完整性约束

**强制要求**:
- ✅ 所有外键字段必须在创建时验证存在性
- ✅ 外键引用的记录被删除时,根据 `ON DELETE` 策略处理

**示例**:
```python
class TopupRequestService:
    def create_request(self, payload: TopupCreate, user: Dict) -> TopupRequest:
        # 验证 project_id 存在性
        project = self.db.query(Project).filter(Project.id == payload.project_id).first()
        if not project:
            raise ResourceNotFoundException(
                code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
                message=f"项目 {payload.project_id} 不存在"
            )

        # 验证用户是否有权限访问该项目
        if not self._check_project_access(project, user):
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,
                message="您没有权限为该项目申请充值"
            )

        # 创建充值申请
        request = TopupRequest(
            project_id=payload.project_id,
            applicant_id=user.get("user", {}).id,
            amount=payload.amount,
            status="draft"
        )
        self.db.add(request)
        self.db.commit()
        return request
```

---

### 5.4 状态流转约束

#### 5.4.1 状态机校验

**强制要求**:
- ✅ 所有状态变更必须通过 `ensure_transition_allowed` 校验
- ✅ 状态变更必须记录审计日志
- ✅ 状态变更必须在事务中执行

**状态流转校验示例**:
```python
# backend/services/state_machine.py
from backend.models.enums import TopupStatus

STATE_TRANSITIONS = {
    "draft": {"pending_review", "cancelled"},
    "pending_review": {"finance_approve", "rejected"},
    "finance_approve": {"paid", "rejected"},
    "paid": {"completed"},
    "completed": set(),  # 终态
    "rejected": {"draft"},
    "cancelled": set()  # 终态
}

def ensure_transition_allowed(current: str, target: str):
    """
    校验状态流转是否合法

    参数:
        current: 当前状态
        target: 目标状态

    异常:
        BusinessRuleException: 状态流转不合法
    """
    allowed = STATE_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise BusinessRuleException(
            code=BusinessErrorCodes.STATUS_TRANSITION_NOT_ALLOWED.code,
            message=f"非法状态流转: {current} → {target}"
        )

# Service层使用
class TopupService:
    def submit_for_review(self, request_id: int, user: Dict) -> TopupRequest:
        request = self.db.query(TopupRequest).filter(TopupRequest.id == request_id).first()

        # 状态流转校验
        ensure_transition_allowed(request.status, "pending_review")

        # 执行状态变更
        with self.db.begin():
            request.status = "pending_review"
            request.updated_at = datetime.now(timezone.utc)

            # 记录审批日志
            log = TopupApprovalLog(
                topup_request_id=request.id,
                action="submit",
                from_status="draft",
                to_status="pending_review",
                operator_id=user.get("user", {}).id,
                comments="提交审核"
            )
            self.db.add(log)

        return request
```

#### 5.4.2 角色权限与状态流转

**规则**: 不同角色仅能触发特定的状态流转。

| 状态机 | 流转路径 | 允许角色 | 引用规则 |
|-------|---------|---------|---------|
| **日报** | `draft → pending` | `media_buyer` | BR-RPT-001 |
| **日报** | `pending → approved/rejected` | `data_operator` | BR-RPT-002 |
| **充值** | `draft → pending_review` | `media_buyer`, `account_manager` | BR-FIN-001 |
| **充值** | `pending_review → finance_approve` | `data_operator` | BR-FIN-002 |
| **充值** | `finance_approve → paid` | `finance` | BR-FIN-002 |
| **项目** | `* → archived` | `admin`, `account_manager` | - |

**实现示例**:
```python
class TopupService:
    def approve_by_finance(self, request_id: int, user: Dict) -> TopupRequest:
        # 角色权限检查
        if user.get("profile", {}).get("role") != "finance":
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,
                message="只有财务角色可以执行此操作"
            )

        request = self.db.query(TopupRequest).filter(TopupRequest.id == request_id).first()

        # 状态流转校验
        ensure_transition_allowed(request.status, "paid")

        # 执行审批
        with self.db.begin():
            request.status = "paid"
            request.approved_by = user.get("user", {}).id
            request.approved_at = datetime.now(timezone.utc)

            # 记录审批日志
            self._create_approval_log(request, user, "finance_approve", "财务审批通过")

        return request
```

---

## 6. 开发工作流

### 6.1 标准开发流程

#### 6.1.1 开发前准备

**必读文档清单**:
```
✅ 第1步: 阅读本手册 (MASTER_DESIGN_DOCUMENT.md) 第1-3章
✅ 第2步: 查阅数据结构 (DATA_SCHEMA.md) 相关表定义
✅ 第3步: 查阅状态机 (STATE_MACHINE.md) 相关状态流转
✅ 第4步: 查阅错误码 (ERROR_CODES.md) 相关错误定义
✅ 第5步: 查阅业务规则 (BUSINESS_RULES.md) 相关约束
✅ 第6步: 查阅API开发流程 (API_DEVELOPMENT_FLOW.md)
```

#### 6.1.2 实现顺序 (取自 API_DEVELOPMENT_FLOW.md)

```
1. 数据库迁移 (Alembic)
   ├─ 创建迁移脚本: alembic revision -m "add_xxx_table"
   ├─ 更新 SQLAlchemy 模型 (backend/models/)
   └─ 执行迁移: alembic upgrade head

2. 后端实现 (FastAPI)
   ├─ 编写 Pydantic Schema (backend/schemas/)
   ├─ 编写 Service 层逻辑 (backend/services/)
   ├─ 编写 Router 层接口 (backend/routers/)
   └─ 编写单元测试 (backend/tests/unit/)

3. 前端实现 (Next.js)
   ├─ 定义 TypeScript 类型 (frontend/types/)
   ├─ 编写 API 调用函数 (frontend/lib/api.ts)
   ├─ 实现 UI 组件 (frontend/components/)
   └─ 实现页面 (frontend/app/)

4. 测试与验收
   ├─ 运行单元测试: pytest
   ├─ 运行集成测试: pytest tests/integration/
   ├─ 运行前端E2E测试: pnpm test:e2e
   └─ 手动测试关键流程
```

---

### 6.2 AI辅助开发Prompt模板 🤖

#### 6.2.1 完整Prompt模板 (可直接复制使用)

**使用场景**: 向Cursor/Claude提供此Prompt,生成符合规范的完整代码 (Schema + Service + Router)

```markdown
# AI辅助开发Prompt模板

## 任务描述
我需要实现 **[功能名称]** 功能,包含完整的后端API (Schema + Service + Router)。

## 必读文档
在生成代码前,请先加载以下文档:
1. `docs/core/MASTER_DESIGN_DOCUMENT.md` (核心开发手册)
2. `docs/core/DATA_SCHEMA.md` (数据结构SoT)
3. `docs/core/STATE_MACHINE.md` (状态机SoT)
4. `docs/core/ERROR_CODES.md` (错误码SoT)
5. `docs/core/BUSINESS_RULES.md` (业务规则SoT)

## 强制约束
### 技术栈约束
- 后端: FastAPI + SQLAlchemy 2.x + Pydantic v2
- 数据库: PostgreSQL 15 (Supabase托管)
- 认证: Supabase Auth (唯一认证方案)
- 角色: 仅 `admin`, `finance`, `data_operator`, `account_manager`, `media_buyer`

### 架构约束
- ✅ 必须使用三层架构: Router → Service → Model
- ✅ 所有时间字段使用 TIMESTAMPTZ,代码中使用 `datetime.now(timezone.utc)`
- ✅ 所有金额字段使用 `Decimal(15,2)`
- ✅ 错误码必须引用 `ERROR_CODES.md`
- ✅ 状态字段必须引用 `STATE_MACHINE.md` 的枚举
- ❌ 禁止在Router层编写业务逻辑
- ❌ 禁止物理删除,必须通过状态机流转至 `archived`/`cancelled`

### 安全约束
- ✅ 所有写接口必须使用 `@require_role` 校验权限
- ✅ Service层必须根据角色过滤数据
- ❌ 禁止硬编码密钥/Token
- ❌ 禁止在日志中输出敏感信息

## 功能需求
### 业务描述
[详细描述业务需求,如:]
- 实现充值申请功能
- 投手/客户经理可以发起充值申请
- 数据操作员复核,财务审批
- 支持查询/提交/审批操作

### 数据模型
[引用 DATA_SCHEMA.md 中的表定义:]
- 表名: `topup_requests` (BIGSERIAL PK)
- 关键字段: `request_no`, `amount`, `status`, `project_id`, `applicant_id`
- 外键关系: `project_id` FK → `projects.id`, `applicant_id` FK → `users.id`

### 状态机
[引用 STATE_MACHINE.md:]
- 状态枚举: `draft`, `pending_review`, `finance_approve`, `paid`, `completed`, `cancelled`, `rejected`
- 关键流转: `draft → pending_review → finance_approve → paid → completed`
- 终态: `completed`, `cancelled`, `rejected`

### API端点
请实现以下API端点:
1. `POST /api/v1/topup-requests` - 创建充值申请
2. `GET /api/v1/topup-requests` - 查询充值申请列表 (含分页/过滤)
3. `GET /api/v1/topup-requests/{id}` - 查询单个充值申请
4. `POST /api/v1/topup-requests/{id}/submit` - 提交审核
5. `POST /api/v1/topup-requests/{id}/approve` - 审批通过
6. `POST /api/v1/topup-requests/{id}/reject` - 审批拒绝

## 输出要求
请按以下顺序生成代码:

### 1. Pydantic Schema (backend/schemas/topup.py)
```python
# 包含:
# - TopupCreate (创建时输入)
# - TopupUpdate (更新时输入)
# - TopupResponse (API响应)
# - TopupListResponse (列表响应,含分页)
# - TopupFilters (查询过滤参数)
```

### 2. Service层 (backend/services/topup_service.py)
```python
# 包含:
# - create_request() - 创建充值申请
# - get_requests() - 查询列表 (含角色数据过滤)
# - get_request_by_id() - 查询单个
# - submit_for_review() - 提交审核 (状态流转校验)
# - approve_request() - 审批通过 (角色权限校验)
# - reject_request() - 审批拒绝
# - _check_project_access() - 项目权限校验 (私有方法)
# - _create_approval_log() - 记录审批日志 (私有方法)
```

### 3. Router层 (backend/routers/topup.py)
```python
# 包含:
# - 所有API端点定义
# - @require_role 权限装饰器
# - Envelope格式响应封装
# - OpenAPI文档注释 (summary, description, responses)
```

### 4. 单元测试 (backend/tests/unit/test_topup_service.py)
```python
# 至少包含:
# - test_create_request_success() - 正向测试
# - test_create_request_invalid_project() - 项目不存在
# - test_create_request_no_permission() - 权限不足
# - test_submit_for_review_invalid_status() - 状态流转非法
# - test_approve_request_only_finance() - 仅财务可审批
```

## 代码规范检查清单
生成代码后,请自检以下项目:
- [ ] 所有字段类型与 DATA_SCHEMA.md 一致
- [ ] 所有状态枚举引用 STATE_MACHINE.md
- [ ] 所有错误码引用 ERROR_CODES.md
- [ ] Service层包含角色数据过滤逻辑
- [ ] Router层使用 `@require_role` 校验权限
- [ ] 响应格式符合 Envelope 标准
- [ ] 状态流转使用 `ensure_transition_allowed` 校验
- [ ] 无硬编码的状态/角色/错误码字符串
- [ ] 时间字段使用 `datetime.now(timezone.utc)`
- [ ] 金额字段使用 `Decimal` 类型

## 参考示例
请参考以下现有实现作为模板:
- Schema 示例: `backend/schemas/daily_report.py`
- Service 示例: `backend/services/daily_report_service.py`
- Router 示例: `backend/routers/daily_reports.py`

---

请开始生成代码,并在生成后说明:
1. 实现的核心功能点
2. 使用的关键设计模式
3. 遵守的核心约束
4. 需要人工Review的部分 (如业务规则细节)
```

#### 6.2.2 简化版Prompt (快速开发)

**使用场景**: 快速生成单个Service方法或Router端点

```markdown
# 快速开发Prompt

请基于 `docs/core/MASTER_DESIGN_DOCUMENT.md` 规范,生成以下代码:

## 任务
实现 **[具体功能]** (如: 充值申请审批功能)

## 约束
- 表: `[表名]` (见 DATA_SCHEMA.md)
- 状态机: `[状态枚举]` (见 STATE_MACHINE.md)
- 错误码: 引用 ERROR_CODES.md
- 角色: 仅 `[允许的角色列表]` 可执行

## 输出
请生成:
1. Service层方法 (含业务逻辑、权限校验、状态流转)
2. Router层端点 (含权限装饰器、响应封装)
3. 关键测试用例 (正向+反向)

---

请确保代码符合以下约束:
- ✅ 使用 `@require_role` 校验权限
- ✅ 使用 `ensure_transition_allowed` 校验状态流转
- ✅ 返回 Envelope 格式响应
- ❌ 禁止硬编码状态/角色/错误码
```

---

### 6.3 Code Review检查清单

#### 6.3.1 强制检查项 (不通过则拒绝合并)

**架构与设计**:
- [ ] 代码遵循Router→Service→Model三层架构
- [ ] Router层不包含业务逻辑
- [ ] Service层不直接返回SQLAlchemy对象
- [ ] 无绕过Service层直接操作数据库的代码

**数据规范**:
- [ ] 所有表/字段定义与 `DATA_SCHEMA.md` 一致
- [ ] 主键类型正确 (users表UUID, 其他表BIGSERIAL)
- [ ] 外键类型与被引用主键一致
- [ ] 时间字段使用 TIMESTAMPTZ, 代码中使用 `datetime.now(timezone.utc)`
- [ ] 金额字段使用 `Decimal(15,2)`

**状态与枚举**:
- [ ] 所有状态枚举引用 `STATE_MACHINE.md` 定义的值
- [ ] 状态流转使用 `ensure_transition_allowed` 校验
- [ ] 无硬编码的状态/角色字符串

**错误处理**:
- [ ] 所有错误码引用 `ERROR_CODES.md`
- [ ] 响应格式符合 Envelope 标准
- [ ] 异常使用自定义异常类 (BusinessRuleException等)

**安全与权限**:
- [ ] 所有写接口使用 `@require_role` 校验权限
- [ ] Service层包含角色数据过滤逻辑
- [ ] 无硬编码的API Key/Secret/密码
- [ ] 日志中无敏感信息输出

**业务规则**:
- [ ] 核心业务数据使用逻辑删除 (archived/cancelled) 而非物理删除
- [ ] 终态数据禁止再次编辑
- [ ] 唯一性约束在Service层和数据库层同时校验

#### 6.3.2 建议检查项 (提示改进)

**代码质量**:
- [ ] 类型注解完整 (Python类型提示, TypeScript接口)
- [ ] 函数/类有清晰的文档注释
- [ ] 复杂逻辑有注释说明
- [ ] 变量命名清晰 (避免 `data`, `tmp` 等模糊名称)

**性能优化**:
- [ ] 查询使用索引字段
- [ ] 避免N+1查询 (使用JOIN或eager loading)
- [ ] 大批量操作使用批处理

**测试覆盖**:
- [ ] 新增代码有对应的单元测试
- [ ] 关键业务逻辑有集成测试
- [ ] 测试覆盖率不下降

---

### 6.4 开发环境配置

#### 6.4.1 后端环境配置

**安装依赖**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**配置环境变量**:
```bash
cp .env.example .env
# 编辑 .env 文件,填入真实的配置值
```

**运行数据库迁移**:
```bash
alembic upgrade head
```

**启动开发服务器**:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 6.4.2 前端环境配置

**安装依赖**:
```bash
cd frontend
pnpm install
```

**配置环境变量**:
```bash
cp .env.local.example .env.local
# 编辑 .env.local 文件,填入真实的配置值
```

**启动开发服务器**:
```bash
pnpm dev
```

---

## 附录

### A. 文档变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2025-11-20 | 初始版本,包含第1-6章完整内容 | 系统架构团队 |

### B. 术语表

| 术语 | 英文 | 说明 |
|-----|------|------|
| **SoT** | Single Source of Truth | 单一真相源,唯一权威信息来源 |
| **Envelope** | Envelope Response | 统一的API响应封装格式 |
| **终态** | Final State | 状态机中的最终状态,不可再流转 |
| **逻辑删除** | Soft Delete | 通过状态标记删除,而非物理删除记录 |
| **户管** | Data Operator | 数据操作员,负责数据审核和投手管理 |

### C. 相关资源

**核心文档**:
- `DATA_SCHEMA.md` - 数据结构SoT
- `STATE_MACHINE.md` - 状态机SoT
- `ERROR_CODES.md` - 错误码SoT
- `BUSINESS_RULES.md` - 业务规则SoT
- `AUTH_SPEC.md` - 认证授权规范
- `RLS_POLICIES.md` - RLS策略参考 (当前未启用)
- `API_DEVELOPMENT_FLOW.md` - API开发流程

**工具与资源**:
- [Supabase文档](https://supabase.com/docs)
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [Next.js文档](https://nextjs.org/docs)
- [SQLAlchemy 2.0文档](https://docs.sqlalchemy.org/en/20/)

---

**END OF DOCUMENT**

**文档维护**:
- **版本**: v1.0 (完整版)
- **最后更新**: 2025-11-20
- **下次审查**: 每季度或重大变更时
- **维护责任**: 系统架构团队

**联系方式**:
- 技术问题: 请在项目Issue中讨论
- 紧急问题: 联系系统架构团队

---

**感谢您使用本开发手册!**
