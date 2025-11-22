# AI广告代投系统·核心开发手册 (Master Design Specification)

> **文档版本**: v2.2
> **发布日期**: 2025-01-21
> **文档状态**: ✅ 核心开发手册 (Single Source of Truth)
> **维护团队**: 系统架构团队
> **文档定位**: 系统开发的最高权威指导文档

---

---

## 📋 v2.1 → v2.2 变更摘要 (Changelog)

### 🎯 核心对齐: BRD_chapter1_v3.1.md

**变更日期**: 2025-01-21
**变更类型**: 业务逻辑对齐 + 架构增强

### 🔴 重大变更

1. **粉数确认状态机** (第2.3.1节)
   - 替换原日报状态机为6状态粉数确认流程
   - 引入趋势风控检查(TF-001/002/003)
   - 新增状态: raw_submitted → trend_pending → trend_ok/flagged → final_pending → final_confirmed → final_locked

2. **API路由扩展** (第1.4.4节)
   - 新增4个端点: trend-check, final-confirm, final-lock, balance-transfer
   - 支持粉数确认完整流程和死号余额迁移

3. **Ledger双账本规范** (第3.2.5节)
   - 新增PROJECT账本(粉数计费收入)和SUPPLIER账本(真实消耗成本)
   - entry_type扩展为5种: REVENUE/COST/TRANSFER_OUT/TRANSFER_IN/REVERSAL
   - 引入SELECT FOR UPDATE事务锁机制

4. **实体关系更新** (第2.2节)
   - daily_reports表新增10个字段: conversions_raw/final, real_spend, trend_flag, unit_price等
   - ad_accounts表新增supplier_id字段
   - ledger_entries表新增ledger_type, supplier_id字段

5. **业务规则补充** (第5.5节)
   - 三数据流分离原则(raw/real/final)
   - 趋势风控规则详解
   - 死号迁移规则(禁止跨供应商直接迁移)
   - final_locked后的红冲修正机制

### 🟡 次要变更

6. **流程图增强**
   - 5个Mermaid流程图: 粉数确认状态机、趋势风控、同供应商迁移、跨供应商迁移、红冲流程

7. **计费公式明确**
   - revenue = conversions_final × unit_price
   - cost = real_spend + fee
   - profit = revenue - cost

### 📊 影响范围

- **后端**: 需新增4个API端点、扩展daily_reports表、重构Ledger Service
- **前端**: 需新增粉数确认流程页面、趋势风控展示、死号迁移界面
- **数据库**: 需执行Alembic迁移添加新字段和约束

### 🔗 参考文档

-  - 业务需求基线
-  - 对齐摘要

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
AI_AD_SYSTEM_MASTER_SPEC.md (本文档 - 顶层指导手册)
    │
    ├─→ DATA_SCHEMA.md               (数据结构唯一真相源)
    ├─→ STATE_MACHINE.md              (状态机唯一真相源)
    ├─→ AUTH_SPEC.md                  (认证授权规范)
    ├─→ BUSINESS_RULES.md             (业务规则SoT)
    ├─→ ERROR_CODES.md                (错误码SoT)
    ├─→ RLS_POLICIES.md               (RLS策略参考,当前未启用)
    ├─→ API_DEVELOPMENT_FLOW.md       (API开发流程)
    └─→ MIGRATION_GUIDE_MASTER_SPEC.md (旧文档迁移指南)
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
- ✅ **AI工具必须先加载本手册再生成代码** (避免幻觉内容)

### 📖 阅读指南

#### 人类开发者

**首次阅读**:
1. 完整阅读第1-6章,理解系统全貌
2. 重点关注第2章(角色权限)和第3章(数据库规范)

**日常开发**:
1. 查阅对应章节 + 引用的SoT文档
2. 开发前检查第6.1节的开发流程清单

**Code Review**:
1. 以本手册第6.3节的检查清单为标准
2. 严格检查SoT一致性(字段类型、状态枚举、错误码)

**紧急问题快速定位**:
| 问题类型 | 查阅章节 | 关键文档 |
|---------|---------|---------|
| 认证/权限报错 | 第4.1节 | `AUTH_SPEC.md` |
| 状态流转失败 | 第2.3节 + 第5.4节 | `STATE_MACHINE.md` |
| 数据库迁移冲突 | 第3.1节 | `DATA_SCHEMA.md` |
| API错误码不明 | 第1.2.2节 | `ERROR_CODES.md` |

#### AI辅助工具 (Claude/Cursor/Copilot)

**生成代码前**:
1. 必须加载本手册 + 相关SoT文档
2. 严格遵守冲突仲裁规则,禁止自创字段/状态/角色
3. 使用第6.2节的AI Prompt模板

**生成代码后**:
1. 执行第6.3节的自检清单(27项)
2. 验证所有枚举值/错误码/字段类型与SoT一致

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
- [4. 安全与认证](#4-安全与认证)
  - [4.1 认证流程详解](#41-认证流程详解)
  - [4.2 环境变量与配置安全](#42-环境变量与配置安全)
  - [4.3 时区处理规范](#43-时区处理规范)
  - [4.4 敏感数据保护](#44-敏感数据保护)
- [5. 业务规则与约束](#5-业务规则与约束)
  - [5.1 核心业务规则引用](#51-核心业务规则引用)
  - [5.2 流程约束与终态保护](#52-流程约束与终态保护)
  - [5.3 数据一致性约束](#53-数据一致性约束)
  - [5.4 状态流转约束](#54-状态流转约束)
- [6. 开发工作流](#6-开发工作流)
  - [6.1 标准开发流程](#61-标准开发流程)
  - [6.2 AI辅助开发Prompt模板](#62-ai辅助开发prompt模板)
  - [6.3 Code Review检查清单](#63-code-review检查清单)
  - [6.4 开发环境配置](#64-开发环境配置)
- [附录 A: 文档变更历史](#附录-a-文档变更历史)
- [附录 B: 术语表](#附录-b-术语表)
- [附录 C: 相关资源](#附录-c-相关资源)
- [附录 D: 历史方案归档](#附录-d-历史方案归档)
- [附录 E: 开发承诺与规范](#附录-e-开发承诺与规范)

---

## 1. 系统架构与原则

### 1.1 技术栈全景

#### 前端技术栈

| 组件 | 版本/选型 | 说明 | 配置文件 |
|-----|----------|---------|------------|
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
|-----|----------|---------|------------|
| **框架** | FastAPI (latest stable) | 异步Web框架 | `requirements.txt` |
| **语言** | Python 3.11+ | 类型注解必须 | - |
| **ORM** | SQLAlchemy 2.x | 同步版本 | `backend/core/db.py` |
| **迁移** | Alembic (latest stable) | 数据库版本管理 | `alembic.ini` |
| **验证** | Pydantic v2 | `ConfigDict(from_attributes=True)` | `backend/schemas/*` |
| **认证** | Supabase Auth SDK | 唯一认证方案 | `backend/core/supabase_client.py` |
| **缓存** | Redis 7.x | 仅缓存/速率限制 | `REDIS_URL` |

**版本管理策略**:
- ✅ 主要框架保持最新稳定版 (通过CI自动检测更新)
- ✅ 向后兼容性破坏时锁定主版本号 (如 SQLAlchemy 2.x, Pydantic v2)
- ⚠️ 在 `requirements.txt` 中使用 `>=` 表示最低版本要求

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
4. ⚠️ Celery/RQ等任务队列当前未规划 (如有需求需先评估并更新架构文档)
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
  "timestamp": "2025-01-20T10:30:00Z"
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
  "timestamp": "2025-01-20T10:30:00Z"
}
```

**分页响应示例**:
```json
{
  "success": true,
  "data": {
    "items": [ /* 列表数据 */ ],
    "meta": {
      "pagination": {
        "page": 1,
        "page_size": 20,
        "total": 145,
        "total_pages": 8,
        "has_next": true,
        "has_prev": false
      }
    }
  },
  "message": "查询成功",
  "code": "SUCCESS"
}
```

**字段说明**:
- `request_id`: UUID v4格式,贯穿前后端日志,便于追踪
- `timestamp`: ISO 8601格式的UTC时间戳
- `code`: 必须来自`ERROR_CODES.md`定义的错误码
- `meta.pagination`: 分页信息(仅列表接口返回)
  - `has_next`: 是否有下一页 (便于前端显示"加载更多"按钮)
  - `has_prev`: 是否有上一页 (便于前端显示"上一页"按钮)

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
|-----|---------|---------||
| **Router** | 参数验证(Pydantic)、权限校验(`@require_role`)、响应封装 | ❌ 编写业务逻辑、直接操作数据库 |
| **Service** | 业务规则验证、事务管理、审计日志记录、数据权限过滤 | ❌ 直接暴露给前端、返回SQLAlchemy对象 |
| **Model** | ORM映射、数据库约束 | ❌ 包含业务逻辑 |

**示例** (正确的分层):
```python
# Router层 (backend/routers/daily_reports.py)
@router.post("/daily-reports")
async def create_report(
    payload: DailyReportCreate,
    service: DailyReportService = Depends(),
    current_user: Dict = Depends(require_role(["media_buyer"]))
):
    # ✅ 仅负责参数验证、权限校验、调用Service
    report = service.create_report(payload, current_user)
    return success_response(data=DailyReportResponse.model_validate(report))

# Service层 (backend/services/daily_report_service.py)
class DailyReportService:
    def create_report(self, payload: DailyReportCreate, user: Dict) -> DailyReport:
        # ✅ 执行业务逻辑、数据权限校验、事务管理
        # 1. 校验用户是否有权限访问该ad_account
        if not self._check_account_access(payload.ad_account_id, user):
            raise AuthorizationException(code=AuthErrorCodes.PERMISSION_DENIED.code)

        # 2. 校验业务规则 (如日期不能为未来)
        if payload.report_date > date.today():
            raise BusinessRuleException(code=BusinessErrorCodes.FUTURE_DATE.code)

        # 3. 创建记录并记录审计日志
        with self.db.begin():
            report = DailyReport(**payload.dict(), created_by=user.get("user", {}).id)
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
├── migrations/              # 数据库初始化/修复脚本
│   ├── 001_uuid_primary_keys.sql
│   └── 002_add_user_foreign_keys.sql
├── scripts/                 # 运维脚本
│   ├── init_db_schema.py    # 数据库架构初始化
│   └── validate_models.py   # 模型验证工具
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
|-----|---------|------|------|---------||
| **Router** | 接收HTTP请求、参数验证、权限校验 | HTTP Request | Envelope Response | 业务逻辑、数据库操作 |
| **Service** | 业务规则验证、事务管理、数据权限过滤、**审计日志记录** | Pydantic Schema + User | SQLAlchemy Model | 直接处理HTTP请求 |
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

| 角色 | 主要职责 | 数据访问范围 (SQL过滤条件) | 典型用例 |
|-----|---------|--------------------------|---------|
| **admin** | 系统配置、全局审计、紧急干预、用户管理 | 无过滤 (`WHERE 1=1`) | 修改系统配置、强制解锁流程、查看所有审计日志 |
| **finance** | 充值终审、资金监控、财务对账、账本管理 | - 充值: 无过滤<br>- 财务数据: 无过滤<br>- 项目: JOIN topup/ledger | 审批充值申请、生成财务报表、对账差异处理 |
| **data_operator** | 日报审核、数据校验、Excel导入导出 | - 项目: 无过滤<br>- 日报/账户: 全局视野 | 审核日报、批量导入消费数据、数据质量检查 |
| **account_manager** | 项目维护、成员管理、充值初审 | - 项目: `WHERE account_manager_id = :user_id`<br>- 日报: `JOIN ad_accounts ON project_id IN (...)` | 创建项目、分配账户、审核充值申请(初审) |
| **media_buyer** | 日报提交、充值申请、凭证上传 | - 账户: `WHERE assigned_to = :user_id`<br>- 日报: `WHERE created_by = :user_id` | 每日提交广告消费数据、申请充值、上传支付凭证 |

#### 2.1.3 权限矩阵 (核心操作)

**快速查询索引**:
- 用户管理: [创建用户](#创建用户) · [修改角色](#修改角色) · [禁用用户](#禁用用户)
- 项目管理: [创建项目](#创建项目) · [编辑项目](#编辑项目) · [归档项目](#归档项目)
- 日报管理: [提交日报](#提交日报) · [审核日报](#审核日报) · [查看日报](#查看日报)
- 充值管理: [发起充值](#发起充值) · [数据复核](#数据复核) · [财务审批](#财务审批)
- 对账管理: [创建批次](#创建批次) · [提交数据](#提交数据) · [确认结果](#确认结果)

| 操作 | admin | finance | data_operator | account_manager | media_buyer |
|-----|-------|---------|---------------|----------------|-------------|
| **用户管理** |
| 创建用户 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 修改他人角色 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 禁用用户 | ✅ | ❌ | ❌ | ❌ | ❌ |
| **项目管理** |
| 创建项目 | ✅ | ❌ | ❌ | ✅ | ❌ |
| 编辑项目 | ✅ | ❌ | ❌ | ✅ (仅自己管理的) | ❌ |
| 归档项目 | ✅ | ❌ | ❌ | ✅ (仅自己管理的) | ❌ |
| 查看所有项目 | ✅ | ✅ | ✅ | ❌ | ❌ |
| **日报管理** |
| 提交日报 | ✅ | ❌ | ❌ | ❌ | ✅ |
| 审核日报 | ✅ | ❌ | ✅ | ❌ | ❌ |
| 查看他人日报 | ✅ | ✅ (财务视角) | ✅ (负责范围) | ✅ (项目范围) | ❌ |
| **充值管理** |
| 发起充值申请 | ✅ | ❌ | ❌ | ✅ | ✅ |
| 数据审核 (复核) | ✅ | ❌ | ✅ | ❌ | ❌ |
| 财务审批 (终审) | ✅ | ✅ | ❌ | ❌ | ❌ |
| 标记支付完成 | ✅ | ✅ | ❌ | ❌ | ❌ |
| **对账管理** |
| 创建对账批次 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 提交对账数据 | ✅ | ❌ | ✅ | ❌ | ❌ |
| 确认对账结果 | ✅ | ✅ | ❌ | ❌ | ❌ |

**图例**:
- ✅ 允许执行
- ❌ 禁止执行
- ✅ (限定条件) 在特定条件下允许

**业务规则引用**: 详见 `BUSINESS_RULES.md` 第3章 (BR-AUTH-*, BR-PROJ-*, BR-RPT-*, BR-FIN-*, BR-RECON-*)

#### 2.1.4 数据权限过滤规则 (Service层实现)

**实现位置**: `backend/services/*_service.py`

**过滤逻辑**:
```python
class ProjectService:
    def get_projects(self, user: Dict, filters: ProjectFilters) -> List[Project]:
        query = self.db.query(Project)

        # 根据角色过滤数据
        if user.get("profile", {}).get("role") == "media_buyer":
            # 投手: 仅查看分配给自己的账户所属的项目
            query = query.join(AdAccount).filter(
                AdAccount.assigned_to == user.get("user", {}).id
            ).distinct()

        elif user.get("profile", {}).get("role") == "account_manager":
            # 客户经理: 查看自己管理的项目 (通过project_members表)
            query = query.join(ProjectMember).filter(
                ProjectMember.user_id == user.get("user", {}).id,
                ProjectMember.role.in_(["account_manager", "project_owner"])
            )

        elif user.get("profile", {}).get("role") == "data_operator":
            # 数据操作员: 全局视野,但通常按负责的投手过滤 (通过users.account_manager_id)
            # 示例: 查看所有项目,或仅查看管理的投手相关项目
            # 此处为全局视野示例
            pass

        elif user.get("profile", {}).get("role") in ["admin", "finance"]:
            # 管理员/财务: 全局视野,无需过滤
            pass

        # 应用其他过滤条件
        if filters.status:
            query = query.filter(Project.status == filters.status)

        return query.all()
```

**关键原则**:
- ✅ 数据权限必须在Service层实现 (禁止在Router层过滤)
- ✅ 使用SQL JOIN而非Python循环过滤 (性能优化)
- ✅ 基于`project_members`/`ad_accounts.assigned_to`/`users.account_manager_id`等关系表判断归属
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
         ┌─────────────────┼────────────────┐      │
         │ 一对多           │ 一对多         │      │
         ▼                  ▼                ▼      │
┌─────────────────┐  ┌─────────────────┐  ┌───────────────────────┐
│ projects        │  │ ad_accounts     │  │ daily_reports         │
│ (BIGINT PK)     │  │ (BIGINT PK)     │  │ (BIGINT PK)           │
│ - account_mgr   ├─►│ - assigned_to   │◄─┤ - created_by          │
│   _id (FK:user) │  │   (FK:users)    │  │   (FK:users)          │
│ - budget_total  │  │ - project_id    │  │ - ad_account_id (FK)  │
│ - unit_price ★  │  │   (FK:projects) │  │ - conversions_raw ★   │
└────────┬────────┘  │ - supplier_id ★ │  │ - conversions_final ★ │
         │           │   (FK:suppliers)│  │ - real_spend ★        │
         │           └─────────────────┘  │ - trend_flag ★        │
         │                                │ - unit_price ★        │
         │                                └───────────────────────┘
         │ 一对多
         ▼
┌─────────────────┐  ┌─────────────────┐  ┌───────────────────────┐
│ project_members │  │ topup_requests  │  │ ledger_entries        │
│ (BIGINT PK)     │  │ (BIGINT PK)     │  │ (BIGINT PK)           │
│ - project_id    │  │ - project_id    │  │ - project_id (FK)     │
│   (FK)          │  │   (FK)          │  │ - supplier_id (FK) ★  │
│ - user_id       │  │ - applicant_id  │  │ - entry_type ★        │
│   (FK:users)    │  │   (FK:users)    │  │   (5种类型)           │
└─────────────────┘  └────────┬────────┘  │ - ledger_type ★       │
                              │           │   (PROJECT/SUPPLIER)  │
                              │           └───────────────────────┘
                              │ 一对多
                              ▼
                     ┌─────────────────┐
                     │ topup_          │
                     │ transactions    │
                     │ (BIGINT PK)     │
                     │ - topup_request │
                     │   _id (FK)      │
                     └─────────────────┘

★ 新增字段(v2.2)
```

**新增字段说明**:

| 表 | 新增字段 | 类型 | 说明 | 引用来源 |
|---|---------|------|------|---------|
| **daily_reports** | `conversions_raw` | INTEGER | 投手提交的原始粉数 | BRD v3.1第3章 |
| **daily_reports** | `conversions_final` | INTEGER | 运营确认的最终粉数 | BRD v3.1第3章 |
| **daily_reports** | `real_spend` | DECIMAL(15,2) | 真实消耗(运营录入) | BRD v3.1第6章 |
| **daily_reports** | `trend_flag` | VARCHAR(20) | 趋势异常标记 | BRD v3.1第4.1节 |
| **daily_reports** | `unit_price` | DECIMAL(15,2) | 单粉价格 | BRD v3.1第7章 |
| **projects** | `unit_price` | DECIMAL(15,2) | 项目单粉价格 | BRD v3.1第7章 |
| **ad_accounts** | `supplier_id` | UUID | 所属供应商ID | BRD v3.1第5.2节 |
| **ledger_entries** | `ledger_type` | VARCHAR(20) | 账本类型(PROJECT/SUPPLIER) | BRD v3.1第8章 |
| **ledger_entries** | `supplier_id` | UUID | 供应商ID(SUPPLIER账本) | BRD v3.1第8章 |
| **ledger_entries** | `entry_type` | VARCHAR(20) | 5种类型(扩展) | BRD v3.1第8章 |

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
|---------|-------------|------|-----------|------|
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

#### 2.3.1 粉数确认状态机 (Conversions Confirmation Lifecycle)

> **业务背景**: 基于BRD v3.1第4章"粉数确认状态机",系统采用三数据流(raw/real/final)分离设计,
> final_conversions需经过趋势风控检查后方可锁定进入计费。

**状态枚举**: `ConversionsStatus` (定义于 `backend/models/enums.py`)

```mermaid
stateDiagram-v2
    [*] --> raw_submitted: 投手提交原始粉数
    raw_submitted --> trend_pending: 自动进入风控队列
    trend_pending --> trend_ok: 风控通过(自动)
    trend_pending --> trend_flagged: 风控异常(需人工)
    trend_flagged --> trend_resolved: 运营确认修正
    trend_ok --> final_pending: 运营填写final
    trend_resolved --> final_pending: 运营填写final
    final_pending --> final_confirmed: 运营确认final
    final_confirmed --> final_locked: 进入计费(不可逆)
    final_locked --> [*]: 终态
```

**6状态详解**:

| 状态 | 说明 | 触发条件 | 角色权限 | 可修改字段 |
|-----|------|---------|---------| -----------|
| **raw_submitted** | 投手提交原始粉数 | 投手提交daily_report | `media_buyer` | `conversions_raw`, `raw_spend` |
| **trend_pending** | 等待趋势风控检查 | 自动触发(raw提交后) | 系统自动 | 无 |
| **trend_ok** | 趋势正常 | 风控规则通过 | 系统自动 | 无 |
| **trend_flagged** | 趋势异常,需人工复核 | 风控规则触发异常 | 系统自动 | `trend_flag_reason` |
| **trend_resolved** | 运营确认异常已解决 | 运营复核后确认 | `data_operator` | `trend_resolution_note` |
| **final_pending** | 等待最终粉数确认 | 运营录入real_spend后 | `data_operator` | `conversions_final`, `real_spend` |
| **final_confirmed** | 最终粉数已确认 | 运营确认final | `data_operator` | 无 |
| **final_locked** | 已进入计费,锁定 | 系统计费后锁定 | 系统自动 | 无(仅可红冲) |

**趋势风控规则** (BRD v3.1第4.1节):

| 规则编号 | 规则名称 | 判断逻辑 | 触发后果 |
|---------|---------|---------| ---------|
| **TF-001** | 粉数骤降检查 | `conversions_raw < 昨日最大值 × 0.5` | `trend_flagged` |
| **TF-002** | 粉数骤增检查 | `conversions_raw > 昨日最大值 × 3` | `trend_flagged` |
| **TF-003** | 消耗异常检查 | `raw_spend > 昨日 × 2` | `trend_flagged` |

**业务约束**:
- ✅ `conversions_raw` ≠ `conversions_final` (允许运营调整)
- ✅ `conversions_final` 一旦确认,除红冲外不可修改
- ✅ `final_locked` 状态后,修正必须通过Ledger红冲(`entry_type=REVERSAL`)
- ❌ 禁止跳过趋势风控直接确认final
- ❌ 禁止在`final_locked`后直接修改数据库

**状态流转API**:
```
POST /api/v1/daily-reports/{id}/trend-check      # 手动触发风控
POST /api/v1/daily-reports/{id}/final-confirm    # 确认final
POST /api/v1/daily-reports/{id}/final-lock       # 锁定进入计费
```

**字段新增** (daily_reports表):
- `conversions_raw` (INTEGER): 投手提交的原始粉数
- `conversions_final` (INTEGER): 运营确认的最终粉数
- `real_spend` (DECIMAL(15,2)): 真实消耗(运营录入)
- `trend_flag` (VARCHAR(20)): 趋势异常标记(`normal`/`flagged`/`resolved`)
- `trend_flag_reason` (TEXT): 异常原因
- `trend_resolution_note` (TEXT): 运营复核说明
- `final_locked_at` (TIMESTAMPTZ): 锁定时间

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

#### 3.2.5 Ledger双账本规范 (BRD v3.1对齐)

> **业务背景**: 基于BRD v3.1第8章"两套账本设计",系统分离项目收入账本(PROJECT)和供应商成本账本(SUPPLIER),
> 实现"粉数计费"和"消耗成本"的独立核算。

**两套账本定义**:

| 账本类型 | 用途 | 关联实体 | entry_type范围 | 金额符号 |
|---------|------|---------|---------------|---------|
| **PROJECT** | 项目收入账本 | `project_id` | `REVENUE`, `REVERSAL` | 正数(收入)/负数(红冲) |
| **SUPPLIER** | 供应商成本账本 | `supplier_id` | `COST`, `TRANSFER_OUT`, `TRANSFER_IN`, `REVERSAL` | 正数(成本增加)/负数(成本减少) |

**entry_type扩展** (5种类型):

| entry_type | 账本类型 | 说明 | 触发场景 | 金额示例 |
|-----------|---------|------|---------| ---------|
| **REVENUE** | PROJECT | 粉数计费收入 | `final_locked`后自动生成 | +5000.00 (收入5000) |
| **COST** | SUPPLIER | 真实消耗成本 | 运营录入`real_spend`后生成 | +3000.00 (成本3000) |
| **TRANSFER_OUT** | SUPPLIER | 死号余额迁出 | 同供应商死号迁移 | -1234.56 (余额减少) |
| **TRANSFER_IN** | SUPPLIER | 死号余额迁入 | 同供应商死号迁移 | +1234.56 (余额增加) |
| **REVERSAL** | BOTH | 红冲修正 | `final_locked`后的修正 | -5000.00 (冲销收入) |

**计费与成本公式** (BRD v3.1第7章):

```python
# 项目收入(PROJECT账本)
revenue = conversions_final × unit_price

# 供应商成本(SUPPLIER账本)
cost = real_spend + fee  # fee通常为0或固定值

# 项目利润
profit = revenue - cost
```

**示例数据流**:

```
T+0日: 投手提交raw
├─ conversions_raw = 100
├─ raw_spend = 5000
└─ status = raw_submitted

T+0日: 系统风控检查
└─ status = trend_ok (或trend_flagged)

T+1日: 运营确认final
├─ conversions_final = 95  (运营调整-5)
├─ real_spend = 4800  (运营录入真实消耗)
└─ status = final_confirmed

T+1日: 系统计费锁定
├─ status = final_locked
├─ Ledger记录1 (PROJECT账本):
│   ├─ entry_type = REVENUE
│   ├─ amount = 95 × 50 = 4750.00
│   └─ project_id = 123
└─ Ledger记录2 (SUPPLIER账本):
    ├─ entry_type = COST
    ├─ amount = 4800.00
    └─ supplier_id = 456

项目毛利 = 4750 - 4800 = -50.00 (亏损)
```

**事务锁逻辑** (防止并发扣减):

```python
# backend/services/ledger_service.py
class LedgerService:
    def create_revenue_entry(self, report_id: int, user: Dict) -> LedgerEntry:
        """
        生成项目收入Ledger记录,使用SELECT FOR UPDATE锁

        业务规则:
        - final_locked后才可生成REVENUE记录
        - 使用数据库事务锁防止并发
        - 项目余额扣减采用原子操作
        """
        with self.db.begin():
            # 1. 锁定日报记录
            report = self.db.query(DailyReport).filter(
                DailyReport.id == report_id
            ).with_for_update().first()

            if report.status != "final_locked":
                raise BusinessRuleException(
                    code="BUS_100",
                    message="仅final_locked状态可生成Ledger记录"
                )

            # 2. 锁定项目记录
            project = self.db.query(Project).filter(
                Project.id == report.project_id
            ).with_for_update().first()

            # 3. 计算收入
            revenue = report.conversions_final * project.unit_price

            # 4. 生成PROJECT Ledger记录
            entry = LedgerEntry(
                ledger_type="PROJECT",
                entry_type="REVENUE",
                project_id=report.project_id,
                amount=revenue,
                reference_type="daily_report",
                reference_id=report.id,
                occurred_at=datetime.now(timezone.utc)
            )
            self.db.add(entry)

            # 5. 更新项目余额(原子操作)
            project.balance = project.balance - revenue

            # 6. 记录审计日志
            self._create_audit_log("CREATE_REVENUE_ENTRY", user, entry)

            self.db.flush()

        return entry
```

**红冲机制** (final_locked后的修正):

```python
# 场景: final_locked后发现粉数错误,需要修正
def create_reversal_entry(self, original_entry_id: int, user: Dict) -> LedgerEntry:
    """
    创建红冲记录,冲销原有Ledger记录

    业务规则:
    - 仅允许对final_locked的记录红冲
    - 红冲金额 = -原金额
    - 同时生成新的正确Ledger记录
    """
    with self.db.begin():
        # 1. 锁定原Ledger记录
        original = self.db.query(LedgerEntry).filter(
            LedgerEntry.id == original_entry_id
        ).with_for_update().first()

        # 2. 生成红冲记录
        reversal = LedgerEntry(
            ledger_type=original.ledger_type,
            entry_type="REVERSAL",
            project_id=original.project_id,
            supplier_id=original.supplier_id,
            amount=-original.amount,  # 负数冲销
            reference_type="reversal",
            reference_id=original.id,
            occurred_at=datetime.now(timezone.utc),
            notes=f"红冲原记录#{original.id}"
        )
        self.db.add(reversal)

        # 3. 更新项目余额
        if original.ledger_type == "PROJECT":
            project = self.db.query(Project).filter(
                Project.id == original.project_id
            ).with_for_update().first()
            project.balance = project.balance + original.amount  # 回退

        self.db.flush()

    return reversal
```

**数据库Schema**:

```sql
CREATE TABLE ledger_entries (
    id BIGSERIAL PRIMARY KEY,
    ledger_type VARCHAR(20) NOT NULL CHECK (ledger_type IN ('PROJECT', 'SUPPLIER')),
    entry_type VARCHAR(20) NOT NULL CHECK (entry_type IN ('REVENUE', 'COST', 'TRANSFER_OUT', 'TRANSFER_IN', 'REVERSAL')),
    project_id BIGINT REFERENCES projects(id) ON DELETE RESTRICT,  -- PROJECT账本必填
    supplier_id UUID REFERENCES suppliers(id) ON DELETE RESTRICT,  -- SUPPLIER账本必填
    amount DECIMAL(15,2) NOT NULL,  -- 允许负值(红冲)
    reference_type VARCHAR(20),  -- 关联类型: daily_report/topup_request/reversal
    reference_id BIGINT,  -- 关联ID
    occurred_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id) ON DELETE RESTRICT,

    -- 约束: PROJECT账本必须有project_id, SUPPLIER账本必须有supplier_id
    CHECK (
        (ledger_type = 'PROJECT' AND project_id IS NOT NULL) OR
        (ledger_type = 'SUPPLIER' AND supplier_id IS NOT NULL)
    )
);

-- 索引
CREATE INDEX idx_ledger_entries_project ON ledger_entries(project_id, occurred_at);
CREATE INDEX idx_ledger_entries_supplier ON ledger_entries(supplier_id, occurred_at);
CREATE INDEX idx_ledger_entries_type ON ledger_entries(ledger_type, entry_type);
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
from typing import Dict, Any, List

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    基础认证: 验证 Token 并返回用户对象

    返回格式:
    {
        "user": {...},  # Supabase Auth user object
        "profile": {    # 业务用户信息
            "id": "uuid",
            "email": "user@example.com",
            "role": "media_buyer",
            "is_active": True
        }
    }
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

### 4.2 环境变量与配置安全

#### 4.2.1 安全配置原则

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

### 4.3 时区处理规范

**核心原则**: 后端统一使用UTC时间存储,前端负责转换为用户本地时区显示。

**后端时间处理** (强制要求):
- ✅ 所有时间字段使用 `TIMESTAMPTZ` 类型
- ✅ Python代码中使用 `datetime.now(timezone.utc)`
- ✅ API响应使用 ISO 8601 格式 (含时区标识 `Z`)
- ❌ 禁止使用 `datetime.now()` (无时区信息)

**前端时区转换** (推荐使用 `date-fns` + `date-fns-tz`):

```typescript
// lib/datetime.ts
import { format, parseISO } from 'date-fns';
import { formatInTimeZone } from 'date-fns-tz';

/**
 * 将UTC时间转换为用户本地时区显示
 */
export function formatUTCToLocal(
  utcDateString: string,
  formatString: string = 'yyyy-MM-dd HH:mm:ss'
): string {
  const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  return formatInTimeZone(
    parseISO(utcDateString),
    userTimezone,
    formatString
  );
}

/**
 * 将本地时间转换为UTC发送给后端
 */
export function formatLocalToUTC(localDate: Date): string {
  return localDate.toISOString();  // 自动转换为UTC
}
```

### 4.4 敏感数据保护

**数据分类**:

| 分类 | 示例 | 保护措施 | 实施位置 |
|-----|------|---------|---------|
| **高敏感** | 密码、支付凭证、API Key | - 加密存储<br>- 禁止日志输出<br>- 定期轮换 | 数据库加密 + 日志过滤 |
| **中敏感** | 邮箱、手机号、真实姓名 | - 访问日志记录<br>- 脱敏显示 (如 `138****1234`) | Service 层 + 审计日志 |
| **低敏感** | 项目名称、广告消费数据 | - 基于角色的访问控制 | Service 层权限过滤 |
| **公开** | 渠道列表、系统配置 | - 无特殊保护 | - |

**日志脱敏示例**:

```python
# backend/core/logging.py
import logging
import re

class SensitiveDataFilter(logging.Filter):
    """敏感数据脱敏过滤器"""

    SENSITIVE_PATTERNS = [
        (re.compile(r'password["\']?\s*[:=]\s*["\']?([^"\']+)["\']?', re.I), 'password=***'),
        (re.compile(r'token["\']?\s*[:=]\s*["\']?([^"\']+)["\']?', re.I), 'token=***'),
        (re.compile(r'secret["\']?\s*[:=]\s*["\']?([^"\']+)["\']?', re.I), 'secret=***'),
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

> **完整业务规则详见**: `BUSINESS_RULES.md`
> 本章节仅列出核心约束,不重复定义完整规则。

### 5.1 核心业务规则引用

#### 5.1.1 认证授权规则

| 规则编号 | 规则名称 | 约束摘要 | 引用文档 |
|---------|---------|---------|---------
| **BR-AUTH-001** | 用户角色唯一性 | 每个用户有且仅有一个角色,不可自行变更 | BUSINESS_RULES.md 3.1 |
| **BR-AUTH-002** | 密码强度要求 | 长度≥8,含数字+字母+特殊字符 | BUSINESS_RULES.md 3.2 |
| **BR-AUTH-003** | 会话超时与续期 | Access Token 15分钟, Refresh Token 7天 | BUSINESS_RULES.md 3.3 |
| **BR-AUTH-004** | 最小权限原则 | 默认拒绝策略,未明确授权的操作禁止 | BUSINESS_RULES.md 3.4 |

### 5.2 流程约束与终态保护

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
    # 执行业务规则校验
    if service.has_pending_topup_requests(project_id):
        raise BusinessRuleException(
            code=BusinessErrorCodes.PROJECT_HAS_PENDING_TOPUP.code,
            message="项目存在未完成的充值申请,无法归档"
        )

    if service.has_active_ad_accounts(project_id):
        raise BusinessRuleException(
            code=BusinessErrorCodes.PROJECT_HAS_ACTIVE_ACCOUNTS.code,
            message="项目存在活跃的广告账户,无法归档"
        )

    project = service.archive_project(project_id, current_user)
    return success_response(
        data=ProjectResponse.model_validate(project),
        message="项目已归档"
    )
```

#### 5.2.2 终态保护规则

**状态机终态定义**:

| 状态机 | 终态列表 | 说明 |
|-------|---------|------|
| **日报状态机** | `approved`, `rejected` | 审核完成后不可再编辑 |
| **充值状态机** | `completed`, `cancelled`, `rejected` | 完成/取消/拒绝后不可逆转 |
| **项目状态机** | `archived` | 归档后仅可查看,不可恢复 |
| **账户状态机** | `archived` | 归档后仅可查看,不可恢复 |

### 5.3 数据一致性约束

**唯一性约束** (Service层校验示例):

```python
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

**说明**: `ConflictException` 继承自 `HTTPException`,错误码来自 `ERROR_CODES.md`,遵循 Envelope 响应格式。

### 5.4 状态流转约束

**状态流转校验** (Service层实现):

```python
# backend/services/topup_service.py
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

### 5.5 粉数确认与计费规则 (BRD v3.1对齐)

> **完整业务规则详见**: `docs/core/BRD_chapter1_v3.1.md`
> 本节列出核心约束摘要。

#### 5.5.1 三数据流分离原则

| 数据流 | 字段名 | 提交者 | 时效性 | 用途 |
|-------|-------|--------|--------|------|
| **raw数据流** | `conversions_raw`, `raw_spend` | 投手 | T+0 23:59前 | 趋势风控 |
| **real数据流** | `real_spend` | 运营 | T+1 12:00前 | 成本核算 |
| **final数据流** | `conversions_final` | 运营 | T+1 14:00前 | 计费基准 |

**业务约束**:
- ✅ `conversions_raw` 不计费,仅用于趋势风控
- ✅ `conversions_final` 计费,公式:`revenue = conversions_final × unit_price`
- ✅ `real_spend` 用于成本核算,公式:`cost = real_spend + fee`
- ❌ 禁止使用`raw_spend`计算成本
- ❌ 禁止跳过final直接计费

#### 5.5.2 趋势风控规则

**规则编号**: TF-001/002/003 (详见第2.3.1节)

**触发后的处理流程**:

```mermaid
flowchart LR
    A[投手提交raw] --> B{自动风控检查}
    B -->|通过| C[trend_ok]
    B -->|异常| D[trend_flagged]
    D --> E[运营复核]
    E -->|确认正常| F[trend_resolved]
    E -->|确认异常| G[要求投手重新提交]
    C --> H[运营填写final]
    F --> H
    H --> I[final_confirmed]
    I --> J[系统计费锁定]
    J --> K[final_locked]
```

**业务规则**:
- ✅ trend_flagged状态下,禁止进入final_pending
- ✅ 运营必须填写`trend_resolution_note`
- ✅ 风控检查自动执行,运营可手动重新检查
- ❌ 禁止关闭风控检查

#### 5.5.3 死号迁移规则

**核心约束** (BRD v3.1第5.2节):

| 场景 | 操作 | Ledger记录 | 审批流程 |
|-----|------|-----------| ---------|
| **同供应商迁移** | 余额从账户A→账户B | `TRANSFER_OUT` + `TRANSFER_IN` | Finance审批 |
| **跨供应商迁移** | ❌ 禁止直接迁移 | 拆分为: S1 `REFUND` + S2新`topup` | Finance+Admin双审 |

**同供应商迁移流程图**:

```mermaid
flowchart TD
    A[账户A标记为dead] --> B{检查供应商}
    B -->|同供应商| C[余额迁移: A→B]
    C --> D[生成TRANSFER_OUT记录]
    C --> E[生成TRANSFER_IN记录]
    D --> F[Finance审批]
    E --> F
    F -->|通过| G[账户A归档]
    F -->|拒绝| H[回滚迁移]
```

**跨供应商迁移流程图**:

```mermaid
flowchart TD
    A[账户A标记为dead] --> B{检查供应商}
    B -->|跨供应商| C[系统拒绝直接迁移]
    C --> D[Step1: 供应商S1退款]
    D --> E[生成REFUND Ledger记录]
    E --> F[Finance+Admin双审批]
    F -->|通过| G[Step2: 供应商S2充值]
    G --> H[创建新topup_request]
    H --> I[正常充值流程]
```

**业务规则**:
- ✅ 源账户必须为`dead`状态
- ✅ 迁移金额不得超过源账户余额
- ✅ 同供应商迁移: 自动生成两条Ledger记录
- ✅ 跨供应商迁移: 系统拒绝,提示操作流程
- ✅ 迁移后源账户自动归档(`archived`)
- ❌ 禁止迁移到非同项目账户

#### 5.5.4 final_locked后的修正规则

**核心原则**: `final_locked`状态后,所有修正必须通过**红冲机制**完成。

**红冲流程**:

```mermaid
flowchart LR
    A[发现final_locked数据错误] --> B[创建REVERSAL记录]
    B --> C[冲销原Ledger记录]
    C --> D[生成新的正确Ledger记录]
    D --> E[更新项目余额]
    E --> F[记录审计日志]
```

**业务规则**:
- ✅ 红冲金额 = -原金额
- ✅ 红冲后重新生成正确的Ledger记录
- ✅ 审计日志记录完整链条
- ❌ 禁止直接UPDATE daily_reports的conversions_final
- ❌ 禁止直接DELETE Ledger记录

**示例场景**:

```
原始数据:
├─ conversions_final = 100
├─ revenue = 100 × 50 = 5000
└─ Ledger记录: entry_type=REVENUE, amount=5000

发现错误(应为95粉):
├─ Step1: 创建红冲记录
│   ├─ entry_type = REVERSAL
│   ├─ amount = -5000
│   └─ notes = "红冲原记录#12345,粉数错误"
├─ Step2: 生成新记录
│   ├─ entry_type = REVENUE
│   ├─ amount = 95 × 50 = 4750
│   └─ notes = "修正后的正确记录"
└─ Step3: 更新项目余额
    └─ balance = balance + 5000 - 4750 = balance + 250
```

---

## 6. 开发工作流

### 6.1 标准开发流程

#### 6.1.1 开发前准备

**必读文档清单**:
```
✅ 第1步: 阅读本手册 (AI_AD_SYSTEM_MASTER_SPEC.md) 第1-5章
✅ 第2步: 查阅数据结构 (DATA_SCHEMA.md) 相关表定义
✅ 第3步: 查阅状态机 (STATE_MACHINE.md) 相关状态流转
✅ 第4步: 查阅错误码 (ERROR_CODES.md) 相关错误定义
✅ 第5步: 查阅业务规则 (BUSINESS_RULES.md) 相关约束
```

#### 6.1.2 实现顺序

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

### 6.2 AI辅助开发Prompt模板

**使用场景**: 向Cursor/Claude提供此Prompt,生成符合规范的完整代码

```markdown
# AI辅助开发Prompt模板

## 任务描述
我需要实现 **[功能名称]** 功能,包含完整的后端API (Schema + Service + Router)。

## 必读文档
在生成代码前,请先加载以下文档:
1. `docs/core/AI_AD_SYSTEM_MASTER_SPEC.md` (核心开发手册)
2. `docs/core/DATA_SCHEMA.md` (数据结构SoT)
3. `docs/core/STATE_MACHINE.md` (状态机SoT)
4. `docs/core/ERROR_CODES.md` (错误码SoT)

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

## 输出要求
请按以下顺序生成代码:

1. Pydantic Schema (backend/schemas/xxx.py)
2. Service层 (backend/services/xxx_service.py)
3. Router层 (backend/routers/xxx.py)
4. 单元测试 (backend/tests/unit/test_xxx.py)

## 代码规范检查清单
详见本手册第6.3节,生成代码后必须自检:
- [ ] 所有字段类型与 DATA_SCHEMA.md 一致
- [ ] 所有状态枚举引用 STATE_MACHINE.md
- [ ] 所有错误码引用 ERROR_CODES.md
- [ ] Service层包含角色数据过滤逻辑
- [ ] Router层使用 `@require_role` 校验权限
- [ ] 响应格式符合 Envelope 标准
- [ ] 无硬编码的状态/角色/错误码字符串
```

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

### 6.4 开发环境配置

#### 6.4.1 后端环境配置

**Python环境**:
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件,填入真实配置
```

**数据库迁移**:
```bash
# 初始化Alembic (仅首次)
alembic init alembic

# 创建新迁移
alembic revision -m "描述变更内容"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

#### 6.4.2 前端环境配置

**Node.js环境**:
```bash
# 安装 pnpm (如未安装)
npm install -g pnpm

# 安装依赖
pnpm install

# 配置环境变量
cp .env.local.example .env.local
# 编辑 .env.local 文件

# 启动开发服务器
pnpm dev
```

#### 6.4.3 测试覆盖率要求

**截至2025-01-20的测试覆盖率现状与目标**:

| 项目 | 目标要求 | 当前状态 | 说明 |
|------|---------|---------|------|
| 单元测试覆盖率 | ≥ 80%,核心模块 100% | 后端 ~55%,前端 ~40% | 优先补齐充值/日报 Service 层用例 |
| API 集成测试 | 每个 `/api/v1/*` 至少 1 条 Happy Path + 1 条权限用例 | 日报/充值部分已覆盖 | 项目/账户/对账待补齐 |
| 前端 e2e | 日报、充值、对账关键流程 | Playwright 已覆盖日报/充值 Happy Path | 异常 & 权限场景待补充 |
| 静态检查 | 后端:`flake8 + mypy`;前端:`pnpm lint && pnpm type-check` | CI 强制执行 | 禁止忽略 |

**测试命令**:

```bash
# 后端测试
cd backend
pytest                                    # 运行所有测试
pytest tests/unit/                        # 仅单元测试
pytest tests/integration/                 # 仅集成测试
pytest --cov=backend --cov-report=html   # 生成覆盖率报告

# 前端测试
cd frontend
pnpm lint                                 # ESLint检查
pnpm type-check                          # TypeScript类型检查
pnpm test                                # Jest单元测试
pnpm test:e2e                            # Playwright E2E测试
```

---

## 附录 A: 文档变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v2.2 | 2025-01-21 | **BRD v3.1业务逻辑对齐**<br>• 替换日报状态机为6状态粉数确认状态机(raw→trend→final→locked)<br>• 新增Ledger双账本规范(PROJECT/SUPPLIER分离核算)<br>• 新增entry_type扩展(5种类型:REVENUE/COST/TRANSFER_OUT/TRANSFER_IN/REVERSAL)<br>• 新增趋势风控规则(TF-001/002/003)<br>• 新增死号迁移规则(禁止跨供应商直接迁移)<br>• 新增final_locked红冲修正机制<br>• 新增10个数据库字段(conversions_raw/final, real_spend等)<br>• 新增4个API端点(trend-check, final-confirm, final-lock, balance-transfer)<br>• 新增5个Mermaid流程图 | 系统架构团队 |
| v2.1 | 2025-01-20 | **结构化优化与内容增强**<br>• 统一类型注解为 `Dict[str, Any]`<br>• 增强业务规则验证示例<br>• 补充数据分类实施位置<br>• 修正章节引用格式<br>• 更新测试覆盖率时效性标注 | 系统架构团队 |
| v2.0 | 2025-11-20 | **合并两份Master Design Document**<br>• 以MASTER_DESIGN_DOCUMENT.md (v1.0)为骨架<br>• 合并AI_AD_SYSTEM_MAIN_DOCUMENT.md (v3.x)的5项关键内容<br>• 完善分页响应示例、状态流转验证代码、测试覆盖率表格<br>• 增补历史方案归档、开发承诺与规范 | 系统架构团队 |
| v1.0 | 2025-11-20 | 初始版本 (MASTER_DESIGN_DOCUMENT.md)<br>• 完整6章结构<br>• SoT网络与冲突仲裁规则<br>• 技术栈全景与设计原则<br>• 核心业务模型与状态机<br>• 数据库规范与安全认证<br>• 业务规则与开发工作流 | 系统架构团队 |
| v3.x | 2025-11-17 | 旧版实现规范 (AI_AD_SYSTEM_MAIN_DOCUMENT.md)<br>• 强调SoT-Implementation定位<br>• 明确当前架构边界<br>• 历史方案归档与禁止行为清单 | 系统架构团队 |

---

## 附录 B: 术语表

| 术语 | 英文 | 说明 |
|-----|------|------|
| **SoT** | Single Source of Truth | 单一真相源,唯一权威信息来源。系统中每类信息只有一个权威文档 |
| **Envelope** | Envelope Response | 统一的API响应封装格式,包含`success`, `data/error`, `message`, `code`, `request_id`, `timestamp`字段 |
| **终态** | Final State | 状态机中的最终状态,不可再流转。如`approved`, `completed`, `archived`, `cancelled`, `rejected` |
| **逻辑删除** | Soft Delete | 通过状态标记删除,而非物理删除记录。核心业务数据必须通过状态机流转至终态而非`DELETE` |
| **户管** | Data Operator | 数据操作员,负责数据审核和投手管理。旧称`data_clerk`已废弃 |
| **投手** | Media Buyer | 媒体采购,负责日报提交和充值申请 |
| **客户经理** | Account Manager | 项目维护、成员管理、充值初审。旧称`manager`已废弃 |
| **BFF** | Backend For Frontend | 后端聚合层,FastAPI提供的API服务,所有前端请求必须通过BFF |
| **RBAC** | Role-Based Access Control | 基于角色的访问控制,系统通过5个合法角色实现权限管理 |
| **RLS** | Row Level Security | 行级安全策略,PostgreSQL特性。当前未启用,所有权限在Service层实现 |
| **UUID** | Universally Unique Identifier | 通用唯一标识符,users/channels表的主键类型,对齐Supabase Auth |
| **BIGSERIAL** | PostgreSQL Auto-increment | 自增长整数,除users/channels外所有表的主键类型 |
| **TIMESTAMPTZ** | Timestamp with Time Zone | 带时区的时间戳,所有时间字段的强制类型,代码中使用`datetime.now(timezone.utc)` |

---

## 附录 C: 相关资源

### C.1 核心文档

**SoT文档体系** (必读):
- `docs/core/DATA_SCHEMA.md` - 数据结构唯一真相源 (v5.0)
- `docs/core/STATE_MACHINE.md` - 状态机唯一真相源 (v2.5)
- `docs/core/ERROR_CODES.md` - 错误码唯一真相源
- `docs/core/BUSINESS_RULES.md` - 业务规则SoT
- `docs/core/AUTH_SPEC.md` - 认证授权规范
- `docs/core/RLS_POLICIES.md` - RLS策略参考 (当前未启用)
- `docs/core/API_DEVELOPMENT_FLOW.md` - API开发流程

**安全与策略文档**:
- `docs/security/RLS_POLICIES.md` - 当前实现行为的Implementation SoT (应用层权限)
- `docs/RLS_STRATEGY_DECISION.md` - RLS策略决策记录 (Draft v1.1)
- `docs/RLS_STRATEGY_EXEC_PLAN_A.md` - RLS方案A执行计划 (v2.0)

**模块开发文档**:
- `docs/modules/projects/API_GUIDE.md` - 项目模块API指南
- `docs/development/MODELS_REFACTOR_COMPLETE_GUIDE.md` - 模型重构指南
- `docs/development/SQLALCHEMY_OPTIMIZATION_GUIDE.md` - SQLAlchemy优化指南

### C.2 工具与外部资源

**官方文档**:
- [Supabase文档](https://supabase.com/docs) - 认证、存储、数据库托管
- [FastAPI文档](https://fastapi.tiangolo.com/) - 后端框架
- [Next.js 16文档](https://nextjs.org/docs) - 前端框架 (App Router)
- [SQLAlchemy 2.0文档](https://docs.sqlalchemy.org/en/20/) - ORM框架
- [Pydantic v2文档](https://docs.pydantic.dev/latest/) - 数据验证
- [shadcn/ui](https://ui.shadcn.com/) - UI组件库

**开发工具**:
- [Alembic文档](https://alembic.sqlalchemy.org/) - 数据库迁移
- [Playwright文档](https://playwright.dev/) - E2E测试
- [date-fns文档](https://date-fns.org/) - 前端时间处理

**代码质量**:
- [flake8](https://flake8.pycqa.org/) - Python静态检查
- [mypy](https://mypy.readthedocs.io/) - Python类型检查
- [black](https://black.readthedocs.io/) - Python代码格式化
- [ESLint](https://eslint.org/) - JavaScript/TypeScript检查

---

## 附录 D: 历史方案归档

> **重要声明**: 以下内容为历史方案归档,**不代表当前实现**,**不得作为开发依据**。
> 如需重新启用任何历史方案,必须先更新本手册及相关SoT文档并通过评审。

### D.1 bolt.new 在线前端流程

**废弃时间**: 2025-11初
**原因**: 旧版曾在bolt.new托管原型,现已完全废弃
**历史资料位置**: `docs/_archive/` (如存在)
**禁止行为**: ❌ 引用bolt.new作为部署方案或前端架构参考

### D.2 PostgreSQL RLS 策略草案

**当前状态**: 未启用 (数据库层RLS关闭)
**原因**: 应用层权限控制已实现且运行稳定,避免引入不必要复杂性
**决策文档**: `docs/RLS_STRATEGY_DECISION.md`, `docs/RLS_STRATEGY_EXEC_PLAN_A.md`
**历史内容**: 旧文档中包含`ENABLE ROW LEVEL SECURITY`与`CREATE POLICY` SQL示例
**当前实现**: 所有权限通过Service层RBAC + 查询过滤实现
**禁止行为**:
- ❌ 执行`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`
- ❌ 创建任何`CREATE POLICY`语句
- ❌ 在代码中假设RLS已启用
**未来规划**: 仅供未来升级参考,需满足以下条件才可评估启用:
- 应用层测试覆盖率 ≥ 80%
- RBAC矩阵稳定 (3个月无重大变更)
- 无即将发生的Schema重构
- 已有Session Context注入方案
- 满足多租户或合规要求

### D.3 Redis 队列 / RQ 方案

**当前状态**: 未实现
**原因**: 当前无大量异步任务需求
**当前Redis用途**: 仅用于速率限制和短期缓存
**历史规划**: 曾规划使用Redis + RQ处理异步任务 (通知、账务同步)
**禁止行为**:
- ❌ 引入Celery/RQ等任务队列
- ❌ 在Redis中创建队列/Worker
**未来评估条件**:
- 出现大量异步任务需求 (如批量通知、定时对账)
- 评估RQ vs Celery vs Cloud Functions方案
- 更新架构文档后方可实施

### D.4 本地 bcrypt / 自建 JWT

**废弃时间**: 2025-11初
**原因**: 全面迁移至Supabase Auth
**历史方案**:
- 曾在本地存储密码哈希 (`password_hash`字段 + `bcrypt`)
- 曾生成自定义JWT Token
**当前实现**:
- 所有认证通过Supabase Auth API
- 后端使用Supabase JWT Secret验证Token
- 项目数据库不存储`password_hash`字段
**禁止行为**:
- ❌ 在`users`表添加`password_hash`字段
- ❌ 使用`bcrypt`/`passlib`/`hashlib`处理密码
- ❌ 手写`jwt.encode()`/`jwt.decode()`签名验证
- ❌ 创建本地JWT Secret
**强制要求**:
- ✅ 所有认证流程必须调用Supabase Auth SDK
- ✅ Token验证必须使用`supabase.auth.get_user(token)`

### D.5 旧角色/表名兼容

**废弃命名** → **当前命名**:
- `data_clerk` → `data_operator` (角色)
- `data_clerk_id` → `data_operator_id` (字段,数据库层可能保留)
- `manager` → `account_manager` (角色)
- `recharge_requests` → `topup_requests` (表名,数据库层可能保留)

**数据库层兼容**: 物理表/字段可能保留历史名称 (通过Alembic迁移逐步重命名)
**应用层强制**:
- ✅ 代码中一律使用现行命名
- ✅ 文档中一律使用现行命名
- ❌ 禁止在新代码中使用旧名
**SQLAlchemy映射**:
```python
# ✅ 正确: 物理表名保留,逻辑名使用新名
class DataOperator(Base):
    __tablename__ = "data_clerks"  # 物理表名 (历史遗留)
    # 但在代码中引用为 DataOperator,字段使用 data_operator_id
```

---

## 附录 E: 开发承诺与规范

### E.1 强制执行承诺

**开发团队承诺**:

1. **启动前检查**:
   - [ ] 确认已阅读并理解本手册 (AI_AD_SYSTEM_MASTER_SPEC.md)
   - [ ] 查阅对应的SoT文档 (DATA_SCHEMA.md, STATE_MACHINE.md, ERROR_CODES.md等)
   - [ ] 理解任务涉及的角色权限与状态流转规则
   - [ ] 确认无需引用历史方案 (附录D)

2. **开发过程**:
   - [ ] 所有字段/表定义与`DATA_SCHEMA.md`一致
   - [ ] 所有状态枚举引用`STATE_MACHINE.md`
   - [ ] 所有错误码引用`ERROR_CODES.md`
   - [ ] 使用合法角色 (仅5个: admin, finance, data_operator, account_manager, media_buyer)
   - [ ] 遵循三层架构 (Router → Service → Model)
   - [ ] 时间字段使用`TIMESTAMPTZ` + `datetime.now(timezone.utc)`
   - [ ] 金额字段使用`Decimal(15,2)`
   - [ ] 响应格式符合Envelope标准
   - [ ] 禁止物理删除核心业务数据

3. **提交前自检**:
   - [ ] 运行`flake8 + mypy` (后端) 或 `pnpm lint && pnpm type-check` (前端)
   - [ ] 运行相关单元测试,确保覆盖率不下降
   - [ ] 运行Alembic迁移 (如有Schema变更)
   - [ ] 检查日志中无敏感信息输出
   - [ ] 验证API响应格式符合Envelope
   - [ ] 确认无硬编码密钥/Token

4. **Code Review标准**:
   - [ ] 以本手册为仲裁依据
   - [ ] 发现与SoT冲突立即拒绝合并
   - [ ] 使用第6.3节Code Review检查清单

### E.2 AI协作规范

**AI工具使用承诺** (适用于Claude/Cursor/Copilot等):

1. **加载文档顺序**:
   ```
   1. docs/core/AI_AD_SYSTEM_MASTER_SPEC.md (本手册)
   2. docs/core/DATA_SCHEMA.md (数据结构SoT)
   3. docs/core/STATE_MACHINE.md (状态机SoT)
   4. docs/core/ERROR_CODES.md (错误码SoT)
   5. 对应模块文档 (如 docs/modules/*)
   ```

2. **禁止行为清单**:
   - ❌ 发明新的字段/表/状态/角色/错误码
   - ❌ 引用bolt.new、data_clerk、强制RLS、本地bcrypt/JWT等历史方案
   - ❌ 绕过Service层直接写SQL或访问数据库
   - ❌ 更改SoT未定义的配置或技术栈
   - ❌ 使用`FLOAT`/`DOUBLE`处理金额
   - ❌ 使用`datetime.now()`而非`datetime.now(timezone.utc)`
   - ❌ 创建物理删除接口 (必须使用逻辑删除)

3. **冲突处理原则**:
   - 若AI输出与SoT冲突 → 立即停止
   - 重新加载相关SoT文档
   - 重新生成代码
   - 不得凭经验修补

4. **生成代码检查清单**:
   ```python
   # AI生成代码后必须自检
   CHECKLIST = {
       "角色": "仅使用5个合法角色",
       "字段": "与DATA_SCHEMA.md一致",
       "状态": "引用STATE_MACHINE.md枚举",
       "错误码": "来自ERROR_CODES.md",
       "响应": "符合Envelope格式",
       "认证": "使用Supabase Auth SDK",
       "时间": "TIMESTAMPTZ + UTC",
       "金额": "Decimal(15,2)",
       "删除": "逻辑删除,禁止物理删除",
       "分层": "Router → Service → Model"
   }
   ```

### E.3 变更管理规范

**业务/架构变更流程**:

1. **提出变更** → 识别影响范围 (涉及哪些SoT文档)
2. **更新SoT** → 先更新本手册及相关SoT文档
3. **评审通过** → Tech Lead/架构团队审核
4. **实施开发** → 按更新后的SoT执行
5. **测试验收** → 确保符合更新后的规范
6. **文档归档** → 更新附录A变更历史

**禁止行为**:
- ❌ 先写代码再更新文档
- ❌ 绕过SoT直接修改实现
- ❌ 未经评审引入新技术栈/架构模式

---

**END OF DOCUMENT**

**文档维护信息**:
- **版本**: v2.1
- **最后更新**: 2025-01-20
- **下次审查**: 每季度或重大变更时
- **维护责任**: 系统架构团队

**联系方式**:
- 技术问题: 请在项目Issue中讨论
- 紧急问题: 联系系统架构团队
- 文档反馈: 提交PR到`docs/core/`目录

**文档状态**: ✅ **已完成** - 本文档已完成结构化优化,可作为项目开发的最高指导标准

---

**感谢您使用本开发手册!**

请严格遵守SoT原则,确保系统质量与一致性。
