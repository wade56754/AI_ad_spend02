# AI广告代投系统开发文档 v2.3 - 本地开发版

> **文档版本**: v2.3 本地开发版
> **更新日期**: 2025-11-15
> **维护团队**: 系统架构团队
> **文档目的**: 提供完整的技术架构、AI辅助开发指南和本地开发部署规范

> 本文档采用**本地 Next.js 16 前端 + FastAPI 后端 + Supabase 数据库/认证**的完整技术栈，配合 Claude Code AI 协作模式，为企业级系统提供完整的开发指导。
>
> **⚠️ 重要说明**：
> - **v2.3 起正式采用本地 Next.js 16 开发模式**，所有前端代码托管在本地仓库，通过 pnpm + Vercel/自建 CI/CD 部署
> - **bolt.new 在线前端流程已正式停用**，相关章节仅作历史参考，请勿用于新功能开发
> - **Supabase 仅用于数据库和认证服务**，前端不再通过 Supabase SDK 直接操作数据库，所有写操作必须经过后端 API
> - 所有规范以本文档和 `rule/` 目录下的规则文档为准

---

## 📘 文档定位说明

### 本文档的权威性

**本文档是AI广告代投系统的唯一权威开发规范**，所有开发工作必须严格遵循本文档的技术架构、接口规范、错误码定义、状态机逻辑和权限矩阵。任何与本文档冲突的代码将无法通过Code Review和测试验收。

**三重定位**：
1. **开发者手册** - 反映项目实际实现，作为日常开发的参考指南
2. **AI规则源** - 作为Claude/Cursor/GitHub Copilot的上下文规则，约束AI生成的代码
3. **架构指南** - 保留核心设计理念和最佳实践，指导技术决策

### AI工具使用规范

**当使用Claude/Cursor/GitHub Copilot等AI辅助工具开发时，必须遵循以下规范：**

#### ⚠️ 强制要求

1. **必须将本文档完整加载为AI的上下文/规则**
   - Claude Code: 在项目根目录的 `.project-rules.md` 中引用本文档，或在对话中显式加载
   - Cursor: 在 `.cursorrules` 文件中引用本文档路径
   - GitHub Copilot: 保持本文档在编辑器打开状态，确保AI能访问

2. **生成任何代码前，必须先查阅本文档对应章节**
   - 编写权限控制代码 → 查阅 [第二章：核心状态机定义](#二核心状态机定义) 和 [第四章：安全策略与权限控制](#四安全策略与权限控制)
   - 创建数据库模型 → 查阅 [第三章：数据库设计](#三数据库设计)
   - 开发API接口 → 查阅 [第五章：API接口规范](#五api接口规范) 和 [第六章：错误码定义](#六错误码定义)
   - 实现业务逻辑 → 查阅 [第八章：核心业务模块](#八核心业务模块)

3. **严格遵守"零、AI辅助开发约束规则"中的强制约束**
   - 技术栈约束（仅Next.js 16 + FastAPI + PostgreSQL）
   - 5个合法角色名称（禁用data_clerk）
   - 50+统一错误码（禁止自定义错误码）
   - 统一API响应格式
   - Supabase Auth双表架构（auth.users + user_profiles）
   - 6个核心状态机定义

4. **每个章节末尾的"AI约束提示"是该章节的快速检查清单**
   - 生成代码后，对照章节末尾的约束清单自检
   - 发现违规立即修正，不得提交违规代码

#### 📚 AI优先加载章节表

不同开发任务应优先加载的章节：

| 任务类型 | 必读章节（按优先级） | 可选章节 |
|---------|---------------------|---------|
| **后端API开发** | 零 → 五 → 六 → 四 → 八 | 三、七、十 |
| **数据库模型开发** | 零 → 三 → 四 → 二 | 五、八 |
| **权限控制实现** | 零 → 四 → 二 → 五 | 八、十 |
| **前端页面开发** | 零 → 一 → 五 → 八 | 四、六、七 |
| **业务逻辑实现** | 零 → 八 → 二 → 五 → 四 | 三、六 |
| **环境配置/部署** | 七 → 十一 → 一 | 零、十 |
| **测试编写** | 零 → 十 → 五 → 八 | 四、六、七 |
| **Bug修复** | 零 → 六（错误码） → 相关业务章节 | 十 |

**解释**：
- **零** = 第零章（AI辅助开发约束规则）- 所有任务的基础
- **一** = 第一章（系统结构概览）
- **二** = 第二章（核心状态机定义）
- **三** = 第三章（数据库设计）
- **四** = 第四章（安全策略与权限控制）
- **五** = 第五章（API接口规范）
- **六** = 第六章（错误码定义）
- **七** = 第七章（环境配置）
- **八** = 第八章（核心业务模块）
- **十** = 第十章（测试策略与质量保证）
- **十一** = 第十一章（部署运维指南）

#### ✅ AI代码生成检查清单

生成代码后，必须自检以下项目（违反任何一项都不得提交）：

- [ ] 使用的角色名称仅限5个合法值（admin, account_manager, data_operator, finance, media_buyer）
- [ ] 使用的错误码来自 `core.error_codes`，未自定义新错误码
- [ ] API响应格式包含所有必需字段（success, data/error, message, code, request_id, timestamp）
- [ ] 数据库操作区分了 `auth.users`（只读）和 `user_profiles`（可写）
- [ ] 状态转换遵循6个核心状态机的定义（未创造新状态或非法转换）
- [ ] 权限控制使用 `@require_role` 装饰器，未硬编码权限逻辑
- [ ] 使用 `get_db()` 获取数据库会话，未直接实例化Session
- [ ] 日志记录使用 `structlog`，包含 `request_id` 等上下文信息
- [ ] 敏感信息（密钥、密码）未硬编码，从环境变量读取
- [ ] 异常处理统一使用 `error_response()` 而非直接抛HTTPException

### 文档维护说明

- **版本**: 当前为 v2.3 本地开发版
- **更新频率**: 随项目重大技术变更同步更新
- **维护责任**: 系统架构团队
- **反馈渠道**: 通过项目Issue或技术讨论会提出修订建议

---

## 🚫 AI/代码助手 使用硬规则（必读）

> **本节为强制性规则，违反任何一条都将导致代码被拒绝合并。**

### 1. 数据库硬规则

- ✅ **唯一真相源**：任何数据库表/字段修改必须先查阅 `docs/core/DATA_SCHEMA.md`
- ✅ **迁移管理**：只能通过 Alembic 创建数据库变更，禁止手动执行 CREATE/ALTER
- ❌ **禁止自创**：不得自创表名、字段名、类型，必须与 DATA_SCHEMA.md 一致
- ❌ **禁止RLS**：当前版本禁止启用 PostgreSQL RLS，不得执行 `ENABLE ROW LEVEL SECURITY`

### 2. 角色权限硬规则

- ✅ **5个合法角色**：`admin`, `finance`, `data_operator`, `account_manager`, `media_buyer`
- ❌ **废弃角色**：遇到 `data_clerk`、`manager`、`trader` 等立即报错纠正
- ✅ **权限装饰器**：必须使用 `@require_role` 装饰器，禁止硬编码权限判断
- ✅ **数据过滤**：Service层必须根据用户角色过滤数据，不依赖数据库RLS

### 3. 认证系统硬规则

- ✅ **Supabase Auth**：所有认证操作必须通过 Supabase Auth API
- ❌ **禁止本地密码**：不得创建 password_hash 字段或使用 bcrypt
- ❌ **禁止自定义JWT**：必须使用 SUPABASE_JWT_SECRET，不得自定义
- ✅ **双表架构**：认证信息在 auth.users（只读），业务信息在 user_profiles（可写）

### 4. API开发硬规则

- ✅ **统一响应格式**：必须包含 `success`, `data/error`, `message`, `code`, `request_id`, `timestamp`
- ✅ **错误码枚举**：必须使用 `core/error_codes.py` 中的错误码，禁止硬编码字符串
- ✅ **分页参数**：统一使用 `page` 和 `size`，不得使用 offset/limit
- ✅ **请求日志**：必须使用 `@log_requests` 装饰器记录关键操作

### 5. 前端开发硬规则

- ✅ **已实装技术**：仅使用 Next.js 16 + TypeScript + Tailwind + shadcn/ui
- ❌ **未安装库**：不得直接使用 Zustand、SWR、Storybook 等未安装的库
- ✅ **组件复用**：必须优先使用 `frontend/components/` 中已有组件
- ✅ **API调用**：必须使用 `lib/api.ts` 中的封装方法

### 6. 跨模块修改硬规则

- ⚠️ **修改前输出计划**：修改代码前必须先输出"计划修改的文件列表"
- ⚠️ **禁止无关修改**：未经用户授权，不得修改与当前任务无关的文件
- ⚠️ **保持向后兼容**：修改公共接口/组件时必须保持向后兼容

### 7. 测试环境硬规则

- ✅ **SQLite测试库**：测试环境使用 SQLite，UUID 必须转字符串
- ✅ **独立配置**：必须使用 `.env.test`，禁止使用开发/生产配置
- ✅ **Fixture隔离**：每个测试必须使用独立的数据库fixture
- ❌ **禁止真实服务**：测试中禁用SMS、Email等外部服务

---

## 📋 目录

1. [系统结构概览](#一系统结构概览)
2. [核心状态机定义](#二核心状态机定义)
3. [数据库设计](#三数据库设计)
4. [安全策略与权限控制](#四安全策略与权限控制)
5. [API接口规范](#五api接口规范)
6. [错误码定义](#六错误码定义)
7. [环境配置](#七环境配置)
8. [核心业务模块](#八核心业务模块)
9. [AI监控功能](#九ai监控功能)
10. [测试策略与质量保证](#十测试策略与质量保证)
11. [部署运维指南](#十一部署运维指南)
12. [开发阶段划分](#十二开发阶段划分)
13. [验收标准](#十三验收标准)
14. [AI辅助开发理念](#十四ai辅助开发理念)
15. [开发规范快速参考](#十五开发规范快速参考)

---

## 零、AI辅助开发约束规则 ⚠️

> **重要**: 本章节定义AI辅助开发时的强制规则，是Claude/Cursor等AI工具的核心约束。违反这些规则生成的代码将无法通过审查。

### 0.1 文档定位

本文档具有三重定位：
1. **开发者手册** - 反映项目实际实现，作为开发参考
2. **AI Rules源** - 作为Claude/Cursor的上下文规则，约束AI生成代码
3. **架构指南** - 保留核心设计理念和最佳实践

---

### 0.2 强制约束（MUST）⚠️

违反以下规则的代码将被拒绝：

**约束1: 技术栈** ⭐

✅ **允许**: Next.js 16.0.2 + TypeScript + FastAPI + Pydantic v2 + SQLAlchemy(同步) + PostgreSQL + Supabase Auth + Redis

❌ **禁止**: 其他框架、SQLAlchemy异步版、其他数据库、其他ORM

**约束2: 角色名称（5个合法角色，大小写敏感）** ⭐

```python
ALLOWED_ROLES = ["admin", "account_manager", "data_operator", "finance", "media_buyer"]

# ✅ 正确
if current_user.role == "data_operator": ...

# ❌ 错误
if current_user.role == "data_clerk": ...  # 已废弃！
```

❌ **禁止**: `data_clerk`（旧名）、中文名称、通用名称、自定义角色

**约束3: 错误码（50+统一错误码）** ⭐

```python
from core.error_codes import AuthErrorCodes, BusinessErrorCodes

# ✅ 正确
return error_response(
    code=AuthErrorCodes.EMAIL_ALREADY_EXISTS.code,
    message="邮箱已被注册",
    status_code=400
)

# ❌ 错误
raise HTTPException(status_code=400, detail="邮箱已存在")  # 直接抛异常
```

**错误码分类**: AUTH_xxx (30+) | BIZ_xxx (20+) | SYS_xxx (10+) | DB_xxx (10+) | VALIDATION_xxx (10+)

**约束4: API响应格式** ⭐

```python
# ✅ 正确：成功响应（必须包含所有字段）
{
    "success": true,
    "data": {...},
    "message": "操作成功",
    "code": "SUCCESS",
    "request_id": "uuid",      # 必需
    "timestamp": "2025-11-16T10:30:00Z"  # 必需
}

# ✅ 正确：错误响应
{
    "success": false,
    "error": {"code": "AUTH_100", "message": "邮箱已被注册"},
    "request_id": "uuid",      # 必需
    "timestamp": "2025-11-16T10:30:00Z"  # 必需
}

# ❌ 错误：自定义格式或缺少必需字段
return {"status": "ok", "result": data}  # 格式不统一
return {"success": true, "data": data}   # 缺少request_id和timestamp
```

**约束5: 数据库操作（Supabase Auth双表架构）** ⭐

✅ **允许**:
- 通过 `user_profiles` 表操作用户业务数据
- 使用 `supabase_auth_service` 操作认证数据
- 通过外键关联查询 `auth.users` (只读)

❌ **严格禁止**:
- 直接 INSERT/UPDATE/DELETE `auth.users` 表
- 在 `auth.users` 表上创建业务字段

```python
# ✅ 正确：注册用户
from services.supabase_auth_service import supabase_auth_service
result = await supabase_auth_service.register_user(
    email=email, password=password, username=username, role=role
)

# ✅ 正确：查询用户资料
user_profile = db.query(UserProfile).filter(UserProfile.id == user_id).first()

# ❌ 错误：直接操作auth.users
user = User(email=email, role="admin")  # ❌ 错误示例：User表由Supabase管理
db.add(user)  # 会失败！auth.users由Supabase管理
```

**约束6: 状态机（6个核心状态机）** ⭐

```python
# 必须遵循第二章定义的状态转换路径：

# 充值申请（6状态）
draft → pending_review → approved → paid → completed
           ↓
        rejected → draft

# 日报审核（4状态）
draft → pending → approved
          ↓
       rejected → draft

# 广告账户（6状态）
new → testing → active → suspended → dead
                  ↓         ↓
              archived  archived

# 对账（4状态）
pending → processing → completed
            ↓
          failed
```

❌ **禁止**: 跳过状态、自定义状态、违反权限的状态转换

```python
# ✅ 正确：验证状态转换
ALLOWED_TRANSITIONS = {
    "draft": ["pending"],
    "pending": ["approved", "rejected"],
    "approved": [],  # 终态
    "rejected": ["draft"]
}

if next_status not in ALLOWED_TRANSITIONS.get(current_status, []):
    return error_response(
        code=BusinessErrorCodes.STATUS_TRANSITION_NOT_ALLOWED.code,
        message=f"不允许从{current_status}转换到{next_status}"
    )
```

---

### 0.3 推荐模式（SHOULD）

**1. 三层架构**: Router (路由层) → Service (服务层) → Model (数据层)

**2. 命名规范**:
- 表名: 复数形式 (`users`, `projects`)
- 文件名: snake_case (`user_service.py`)
- 类名: PascalCase (`UserProfile`, `ProjectService`)
- 变量/函数: snake_case (`get_user_profile`)
- 常量: UPPER_CASE (`MAX_FILE_SIZE`)

**3. Pydantic模型**: 必须添加 `class Config: from_attributes = True`（Pydantic v2）

**4. 测试覆盖率**: API测试 >80% | 关键业务逻辑 100% | 状态机转换 100% | 权限检查 100%

---

### 0.4 AI代码生成流程 ⚠️

**新增API接口**:
1. 查看第五章（API响应格式）→ 第六章（错误码）→ 第四章（权限）→ 第八章（参考模块）
2. 生成代码 → 添加测试用例

**修改数据库表**:
1. 查看第三章（表结构、索引、外键）
2. 生成Alembic迁移 → 更新SQLAlchemy模型 → 更新Pydantic Schema

**实现状态机**:
1. 查看第二章（状态转换规则）→ 第四章（权限矩阵）→ 第八章（参考实现）
2. 实现状态转换 → 添加权限检查 → 添加审计日志

---

### 0.5 常见AI错误及纠正 ⚠️

| 错误类型 | ❌ 错误代码 | ✅ 正确代码 |
|---------|-----------|-----------|
| **角色名错误** | `if role == "data_clerk"` | `if role == "data_operator"` |
| **硬编码错误码** | `raise HTTPException(400, "错误")` | `error_response(code=ErrorCode.XXX.code, ...)` |
| **直接操作auth.users** | `db.query(User).filter(...)` | `db.query(UserProfile).filter(...)` |
| **自定义响应格式** | `return {"status": "ok"}` | `return success_response(data=...)` |
| **使用SQLAlchemy异步** | `async def get(db: AsyncSession)` | `def get(db: Session)` # 同步 |
| **状态跳转** | `draft → paid` # 跳过pending | `draft → pending → approved → paid` |

**关键检查清单**（AI生成代码后必须自查）:
- [ ] 角色名是否为5个合法角色之一？
- [ ] 错误码是否从`core.error_codes`导入？
- [ ] API响应是否包含`success`、`data/error`、`request_id`、`timestamp`？
- [ ] 是否使用`user_profiles`而非`auth.users`操作用户业务数据？
- [ ] 状态转换是否遵循状态机定义？
- [ ] 是否添加了权限检查装饰器（`@require_any_role`）？
- [ ] 是否使用同步版SQLAlchemy（非async）？

**详细规范参考**:
- 第二章：核心状态机定义
- 第三章：数据库设计
- 第四章：安全策略与权限控制
- 第五章：API接口规范
- 第六章：错误码定义（50+统一错误码）
- 第七章：环境配置
- 第八章：核心业务模块（12个模块）
- 第十章：测试策略与质量保证

---

## 一、系统结构概览

### 技术栈推荐（AI辅助协作组合）

#### 前端技术栈（本地 Next.js 开发）

**当前已实装**：
- **框架**：Next.js 16.0.2 + TypeScript + Tailwind CSS
- **UI组件库**：shadcn/ui（部分组件已实装）
- **路由**：App Router（`app/` 目录结构）
- **API调用**：自封装 `lib/api.ts`（基于 fetch）
- **开发环境**：本地 VS Code + pnpm
- **部署方式**：本地构建 → 手动部署

**规划中（未实装）**：
- ⚠️ **Zustand** - 状态管理（当前使用 React state）
- ⚠️ **SWR** - 数据获取（当前使用 fetch）
- ⚠️ **Storybook** - 组件开发（尚未配置）
- ⚠️ **Playwright** - E2E测试（尚未配置）
- ⚠️ **Jest** - 单元测试（尚未配置）

**AI 使用约束**：
- 生成前端代码时，**仅使用"当前已实装"的技术**
- 如需引入"规划中"的库，必须先确认 `package.json` 中是否已安装
- 优先复用 `frontend/components/` 中已有组件

#### 后端技术栈（Claude Code AI辅助开发）
- **框架**：FastAPI + Pydantic v2 + SQLAlchemy（同步版）
- **AI开发工具**：Claude Code（本地AI辅助编程）
- **数据库**：PostgreSQL（Supabase托管）
- **缓存/队列**：Redis + RQ（任务调度、通知、AI检测）
- **认证安全**：Supabase Auth + JWT验证 + 应用层RBAC
- **特色功能**：
  - AI自动生成CRUD API
  - 智能测试用例生成
  - 自动代码质量检查
  - 实时代码审查和优化建议

#### 协作桥梁技术
- **API隧道**：ngrok（本地API外网访问）
- **版本控制**：Git + GitHub/GitLab
- **实时同步**：Git hooks + 自动化部署
- **接口规范**：OpenAPI 3.0 + Swagger文档
- **跨域处理**：CORS配置 + API代理

#### 监控和运维
- **日志监控**：Loki + Promtail + Grafana + Sentry
- **性能监控**：APM工具 + 自定义指标
- **安全监控**：漏洞扫描 + 异常检测
- **部署运维**：Docker Compose + Nginx + 混合部署

### 系统架构图（AI辅助协作模式）
```
┌─────────────────────────────────────────────────────────────┐
│                本地前端层 (Next.js 16)                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  组件开发    │ │   实时预览   │ │   CI/CD部署  │           │
│  │ React/TS    │ │  pnpm dev   │ │  Vercel/CDN  │           │
│  │ shadcn/ui   │ │ Tailwind    │ │ Supabase Auth│           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │ 协作桥梁技术       │
                    │┌──────┐┌──────┐   │
                    ││ngrok ││Git   │   │
                    ││隧道  ││同步  │   │
                    │└──────┘└──────┘   │
                    └─────────┬─────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│             本地后端层 (Claude Code)                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  AI API生成  │ │   智能测试   │ │   代码审查   │           │
│  │ FastAPI     │ │  自动执行    │ │  质量保证    │           │
│  │ SQLAlchemy  │ │  pytest      │ │  Sentry联动   │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     数据与云服务层                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ PostgreSQL  │ │  Supabase   │ │   Redis/RQ   │           │
│  │  (RLS)      │ │  Auth & API │ │   任务/缓存   │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
```
`


### AI辅助开发流程图
```
开发阶段 ：
┌─────────────────────────────────────────────────────────────┐
│  需求分析 → AI设计 → 代码生成 → 质量检查 → 部署上线          │
│    │         │         │         │         │               │
│    ▼         ▼         ▼         ▼         ▼               │
│  业务描述  架构设计  AI生成   自动测试  自动部署           │
│  用户故事  接口设计  代码审查  性能分析  监控告警           │
│  功能清单  数据模型  重构优化  安全扫描  文档同步           │
└─────────────────────────────────────────────────────────────┘

技术栈协作：
Next.js 16（前端）←→ Git版本控制 ←→ Claude Code（后端）
      ↓                              ↓
  本地组件开发                   AI API生成
      ↓                              ↓
  Vercel/CDN部署             本地开发环境
      ↓                              ↓
  用户界面交互                业务逻辑处理
      ↓                              ↓
              Supabase数据库（统一数据层）
```

---

## 认证系统说明（Supabase Auth）⚠️

> **重要**：本项目使用 Supabase Auth 作为唯一认证服务提供商，**不使用本地密码存储和验证**。

### 认证架构

| 组件 | 职责 | 说明 |
|------|------|------|
| **Supabase Auth** | 用户注册、登录、JWT签发 | 托管服务，处理所有认证逻辑 |
| **auth.users表** | 存储认证凭据 | Supabase管理，应用只读 |
| **user_profiles表** | 存储业务资料 | 应用管理，存储角色、部门等 |
| **后端验证** | JWT验证、角色检查 | 使用Supabase JWT Secret验证令牌 |

### 认证流程

```mermaid
sequenceDiagram
    participant U as 用户
    participant F as 前端
    participant B as 后端API
    participant S as Supabase Auth

    U->>F: 输入邮箱密码
    F->>S: 调用 supabase.auth.signIn()
    S-->>F: 返回 JWT + 用户信息
    F->>B: 携带 JWT 调用业务API
    B->>B: 验证 JWT (使用SUPABASE_JWT_SECRET)
    B->>B: 查询 user_profiles 获取角色
    B-->>F: 返回业务数据
```

### 关键配置

```python
# core/config.py
class Settings(BaseSettings):
    # Supabase配置
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str  # 前端用
    SUPABASE_SERVICE_ROLE_KEY: str  # 后端管理用
    SUPABASE_JWT_SECRET: str  # JWT验证用（非自定义）

    class Config:
        env_file = ".env"
```

```python
# deps/supabase_auth.py
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """验证JWT并获取用户信息"""
    try:
        # 使用Supabase的JWT Secret验证
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )

        user_id = payload.get("sub")  # Supabase用户ID

        # 从user_profiles获取业务信息
        user_profile = db.query(UserProfile).filter(
            UserProfile.id == user_id
        ).first()

        return {
            "user": {
                "id": user_id,
                "email": payload.get("email"),
                "role": user_profile.role if user_profile else "media_buyer"
            }
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的令牌")
```

### AI 使用约束

**禁止事项**：
- ❌ 创建本地 password_hash 字段
- ❌ 使用 bcrypt 或其他密码哈希库
- ❌ 直接操作 auth.users 表
- ❌ 自定义 JWT_SECRET（必须使用Supabase的）
- ❌ 实现本地登录逻辑

**必须遵循**：
- ✅ 所有认证操作通过 Supabase Auth API
- ✅ 使用 supabase_auth_service 封装认证逻辑
- ✅ JWT验证使用 SUPABASE_JWT_SECRET
- ✅ 业务资料存储在 user_profiles 表
- ✅ 角色权限在应用层实现

---

## 二、核心状态机定义

### 1. 充值申请状态机
| 状态 | 描述 | 可操作角色 | 下一状态 | 自动触发条件 |
|------|------|-------------|-----------|-------------|
| **draft** | 投手提交 | 投手 | pending | 手动提交 |
| **pending** | 审核中 | 户管 | approved / rejected | 手动审批 |
| **approved** | 财务批准 | 财务 | paid | 手动批准 |
| **paid** | 已支付 | 系统 | posted | 支付确认 |
| **posted** | 已入账 | 系统 | — | 入账完成 |
| **rejected** | 被驳回 | 户管/财务 | draft | 驳回后可重新提交 |

### 2. 日报审核状态机
| 状态 | 描述 | 可操作角色 | 下一状态 | 自动触发条件 |
|------|------|-------------|-----------|-------------|
| **draft** | 投手填写 | 投手 | pending | 自动保存 |
| **pending** | 审核中 | 数据员 | approved / rejected | 提交审核 |
| **approved** | 已通过 | 系统 | — | 审核通过 |
| **rejected** | 异常退回 | 数据员 | draft | 审核驳回 |

### 3. 账户生命周期状态机
| 状态 | 说明 | 自动触发条件 | 可操作角色 |
|------|------|-----------------|-------------|
| **new** | 新建 | 创建时 | 户管 |
| **testing** | 测试期 | 7日内稳定消耗 | 系统 |
| **active** | 正常投放 | 日均>100USD | 系统 |
| **suspended** | 暂停 | 3天无消耗 | 系统/户管 |
| **dead** | 封禁 | FB返回异常 | 系统 |
| **archived** | 归档 | 管理员手动 | 管理员 |

---

### 4. 项目状态机

| 状态 | 说明 | 转换条件 | 可操作角色 |
|------|------|----------|------------|
| **active** | 活跃 | 创建时默认 | admin, account_manager |
| **paused** | 暂停 | 手动暂停 | admin, account_manager |
| **completed** | 完成 | 手动标记完成 | admin, account_manager |

**允许的转换**:
- active → paused
- active → completed
- paused → active
- paused → completed

---

### 5. 状态机设计规范 ⚠️

> **重要**: 本节定义所有状态机的通用规范和AI代码生成约束。

#### 5.1 状态机设计原则

**1. 状态定义规则**:
```python
# ✅ 正确：使用小写+下划线
ALLOWED_STATES = ["draft", "pending_review", "approved", "rejected"]

# ❌ 错误：混用大小写或中文
ALLOWED_STATES = ["Draft", "pending-review", "已批准", "REJECTED"]
```

**2. 状态转换验证**:
```python
# ✅ 正确：定义允许的转换映射
STATE_TRANSITIONS = {
    "draft": ["pending_review"],
    "pending_review": ["approved", "rejected"],
    "approved": ["paid"],
    "rejected": ["draft"],  # 允许重新提交
}

def is_valid_transition(current: str, target: str) -> bool:
    """验证状态转换是否合法"""
    return target in STATE_TRANSITIONS.get(current, [])

# 使用时必须验证
if not is_valid_transition(current_status, new_status):
    return error_response(
        code=BusinessErrorCodes.STATUS_TRANSITION_NOT_ALLOWED.code,
        message=f"不允许从{current_status}转换到{new_status}"
    )
```

**3. 状态字段定义**:
```sql
-- ✅ 正确：使用CHECK约束
status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (
    status IN ('draft', 'pending_review', 'approved', 'rejected', 'paid', 'completed')
)

-- ❌ 错误：没有约束，允许任意值
status VARCHAR(20)  -- 可能插入无效状态！
```

---

#### 5.2 系统状态机汇总表

| 模块 | 状态数 | 状态列表 | 自动转换 | 手动转换 |
|------|--------|---------|---------|---------|
| 项目 (Project) | 3 | active, paused, completed | ❌ | ✅ admin, account_manager |
| 广告账户 (AdAccount) | 6 | new, testing, active, suspended, dead, archived | ✅ testing, active, suspended, dead | ✅ archived (admin only) |
| 日报 (DailyReport) | 4 | draft, pending, approved, rejected | ❌ | ✅ media_buyer提交, data_operator审核 |
| 充值 (TopupRequest) | 6 | draft, pending_review, approved, rejected, paid, completed | ❌ | ✅ 多角色协作 |
| 对账 (Reconciliation) | 4 | pending, processing, completed, failed | ✅ processing | ✅ pending (data_operator, finance) |
| 数据导入 (ImportJob) | 4 | pending, processing, completed, failed | ✅ processing | ✅ pending (data_operator) |

---

#### 5.3 AI代码生成约束

**约束1: 状态转换必须验证**

```python
# ✅ 正确：状态转换前验证
from services.topup_service import topup_service

async def approve_topup(topup_id: str, current_user: UserProfile):
    topup = db.query(TopupRequest).filter(TopupRequest.id == topup_id).first()

    # 验证当前状态
    if topup.status != "pending_review":
        return error_response(
            code=BusinessErrorCodes.INVALID_STATUS.code,
            message=f"当前状态{topup.status}不能批准"
        )

    # 验证权限
    if current_user.role not in ["admin", "data_operator"]:
        return error_response(
            code=AuthErrorCodes.PERMISSION_DENIED.code,
            message="无权限批准充值"
        )

    # 执行状态转换
    topup.status = "approved"
    topup.approved_by = current_user.id
    topup.approved_at = datetime.now(timezone.utc)
    db.commit()

# ❌ 错误：直接修改状态，不验证
topup.status = "approved"  # 从任何状态都能转到approved？不合理！
db.commit()
```

**约束2: 状态转换触发副作用**

```python
# ✅ 正确：状态转换时执行相关操作
async def transition_ad_account_status(
    account_id: str,
    new_status: str,
    db: Session
):
    account = db.query(AdAccount).filter(AdAccount.id == account_id).first()

    # 记录状态变更历史
    status_history = AdAccountStatusHistory(
        account_id=account_id,
        old_status=account.status,
        new_status=new_status,
        changed_at=datetime.now(timezone.utc)
    )
    db.add(status_history)

    # 更新状态
    account.status = new_status
    account.updated_at = datetime.now(timezone.utc)

    # 触发通知
    if new_status == "dead":
        await send_account_dead_notification(account)

    db.commit()

# ❌ 错误：只改状态，不记录历史
account.status = new_status  # 无法追溯谁在何时修改的！
db.commit()
```

**约束3: 并发状态更新保护**

```python
# ✅ 正确：使用乐观锁或数据库事务
from sqlalchemy.orm.exc import StaleDataError

async def update_daily_report_status(report_id: str, new_status: str, db: Session):
    try:
        with db.begin():
            # 使用 for_update() 锁定行
            report = db.query(DailyReport).filter(
                DailyReport.id == report_id
            ).with_for_update().first()

            if not report:
                raise HTTPException(status_code=404, detail="日报不存在")

            # 验证状态转换
            if not is_valid_transition(report.status, new_status):
                raise HTTPException(status_code=400, detail="状态转换不允许")

            # 更新状态
            report.status = new_status
            report.updated_at = datetime.now(timezone.utc)

    except StaleDataError:
        raise HTTPException(status_code=409, detail="数据已被其他用户修改，请刷新后重试")

# ❌ 错误：不加锁，可能导致状态冲突
report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
report.status = new_status  # 可能覆盖其他用户的更新！
db.commit()
```

---

#### 5.4 状态机测试要求

AI生成状态机相关代码时，必须同时生成测试用例：

```python
# 测试状态转换有效性
def test_topup_status_transition():
    """测试充值状态转换"""

    # 测试合法转换
    assert is_valid_transition("draft", "pending_review") == True
    assert is_valid_transition("pending_review", "approved") == True
    assert is_valid_transition("approved", "paid") == True

    # 测试非法转换
    assert is_valid_transition("approved", "draft") == False
    assert is_valid_transition("paid", "pending_review") == False
    assert is_valid_transition("completed", "rejected") == False

# 测试权限控制
def test_topup_approval_permission():
    """测试充值审批权限"""

    # 投手不能审批
    with pytest.raises(HTTPException) as exc:
        approve_topup(topup_id, media_buyer_user)
    assert exc.value.status_code == 403

    # 数据员可以审批
    result = approve_topup(topup_id, data_operator_user)
    assert result["success"] == True

# 测试并发更新
def test_concurrent_status_update():
    """测试并发状态更新"""

    # 模拟两个用户同时更新
    # 应该有一个失败
    with pytest.raises(HTTPException) as exc:
        update_status_concurrently(report_id)
    assert exc.value.status_code == 409
```

### ⚠️ AI代码生成约束提示

**当AI生成涉及状态机的代码时，必须遵守以下约束：**

1. **仅使用6个已定义的核心状态机**
   - ✅ 允许：TopupRequest（6状态）、DailyReport（4状态）、Project（3状态）、AdAccount（6状态）、Reconciliation（4状态）、ImportJob（5状态）
   - ❌ 禁止：创造新的状态机、新增未定义状态、跳过中间状态

2. **状态转换必须遵循状态机定义的有向边**
   ```python
   # ✅ 正确：遵循状态机定义
   if current_status == "pending" and user.role == "data_operator":
       new_status = "approved"  # pending → approved 是合法转换

   # ❌ 错误：非法状态转换
   if current_status == "draft":
       new_status = "paid"  # draft 不能直接到 paid，必须经过 pending → approved
   ```

3. **权限检查必须对照"可操作角色"列**
   - 状态转换前必须验证 `current_user.role` 是否在该状态的"可操作角色"列表中
   - 使用 `@require_role` 装饰器而非硬编码 `if role ==` 判断

4. **自动触发条件必须在代码中体现**
   - 如充值申请的 `paid → posted` 是"入账完成"自动触发，需在支付回调中自动更新状态
   - 不应依赖手动操作来完成自动触发的状态转换

5. **状态回退必须有审计日志**
   ```python
   # ✅ 正确：记录状态变更历史
   from services.audit_service import log_status_change

   log_status_change(
       entity_type="topup_request",
       entity_id=topup_id,
       old_status="pending",
       new_status="rejected",
       operator_id=current_user.id,
       reason="金额超出预算"
   )
   ```

6. **并发状态更新必须使用乐观锁**
   - 使用 `version` 字段或 `updated_at` 时间戳防止并发冲突
   - 参考上述 `test_concurrent_status_update` 测试用例

**违反上述任何约束的代码将导致状态机混乱、权限漏洞或数据不一致问题！**

---

## 三、数据库设计

> ⚠️ **重要声明：数据库结构权威来源**
>
> **本项目数据库结构以 `docs/core/DATA_SCHEMA.md` 和 Alembic 迁移文件为唯一权威来源**。本章中出现的 SQL 示例仅用于帮助理解概念，**禁止直接作为实现依据**。实际开发时必须：
> 1. 查阅 `docs/core/DATA_SCHEMA.md` 获取最新表结构定义
> 2. 使用 Alembic 管理数据库迁移（`alembic/versions/` 目录）
> 3. 参考 `backend/models/` 中的 SQLAlchemy 模型定义

### 数据库模型总览（对齐当前实现）

#### 核心设计特点

| 特点 | 说明 | 重要性 |
|------|------|--------|
| **混合主键类型** | 用户相关表使用 UUID，业务表使用 Integer 自增 | ⭐⭐⭐ |
| **应用层权限** | 不使用 PostgreSQL RLS，所有权限在 Service 层控制 | ⭐⭐⭐ |
| **Supabase Auth** | 认证由 Supabase 托管，users 表不存储密码 | ⭐⭐⭐ |
| **完整审计** | 主要业务表都有关联的历史/审计表 | ⭐⭐ |

#### 核心表概览

| 表名 | 主键类型 | 用途 | 关键字段 | 外键关联 |
|------|----------|------|----------|----------|
| **users** | UUID | 用户基础信息 | email, name, role | roles.id |
| **channels** | UUID | 渠道管理 | name, code, service_fee_rate | users.id |
| **projects** | Integer | 项目管理 | name, status, budget | users.id |
| **ad_accounts** | Integer | 广告账户 | account_id, platform, status | projects.id, channels.id, users.id |
| **topup_requests** | Integer | 充值申请 | request_no, amount, status | ad_accounts.id, projects.id, users.id |
| **ad_spend_daily** | UUID | 日消耗记录 | date, spend, leads_count | ad_accounts.id, users.id |
| **daily_reports** | Integer | 日报管理 | report_date, spend, conversions | ad_accounts.id, users.id |
| **reconciliation_batches** | Integer | 对账批次 | batch_no, status, total_difference | users.id |
| **reconciliation_details** | Integer | 对账明细 | platform_spend, internal_spend, difference | batches.id, ad_accounts.id |

> **AI 使用约束**：生成任何数据库相关代码时，必须先查阅 `docs/core/DATA_SCHEMA.md` 确认字段名称、类型和约束。禁止根据本章节的示例 SQL 创建表或添加字段。

### 1. 核心表结构（仅供理解参考）

#### 用户认证与资料表（双表架构）⚠️

> **重要**: 本项目使用Supabase Auth管理用户认证，采用**双表架构**，AI生成代码时必须严格遵守以下规则。

##### 1. auth.users（Supabase管理的认证表）

**表说明**:
- **所有权**: Supabase Auth系统管理，应用程序**只读**
- **主键**: `id UUID` (由Supabase生成)
- **用途**: 存储认证凭据（邮箱、密码哈希、会话令牌）

**核心字段**:
```sql
-- auth.users 表（Supabase管理，只读参考）
CREATE TABLE auth.users (
    id UUID PRIMARY KEY,                    -- Supabase生成的UUID
    email VARCHAR(255) UNIQUE NOT NULL,     -- 邮箱（登录标识）
    encrypted_password VARCHAR(255),        -- 密码哈希（Supabase管理）
    email_confirmed_at TIMESTAMP,           -- 邮箱验证时间
    phone VARCHAR(20),                      -- 手机号
    phone_confirmed_at TIMESTAMP,           -- 手机验证时间
    last_sign_in_at TIMESTAMP,              -- 最后登录时间
    created_at TIMESTAMP,                   -- 创建时间
    updated_at TIMESTAMP,                   -- 更新时间
    -- 其他Supabase内部字段...
);
```

**AI约束 - 禁止操作**:
```python
# ❌ 错误：直接操作auth.users表
from models.users import User  # 错误！不存在这个模型

user_profile = UserProfile(id=user_id, email=email, role=role)  # 正确：操作user_profiles
db.add(user)  # 会失败！auth.users由Supabase管理

# ❌ 错误：尝试修改auth.users
user = db.query(User).filter(User.email == email).first()
user.role = "admin"  # auth.users表没有role字段！
```

**正确做法**:
```python
# ✅ 正确：使用Supabase Auth Service注册用户
from services.supabase_auth_service import supabase_auth_service

result = await supabase_auth_service.register_user(
    email=email,
    password=password,
    username=username,
    role=role  # 会自动创建user_profiles记录
)
```

---

##### 2. user_profiles（应用业务资料表）

**表说明**:
- **所有权**: 应用程序管理，可读写
- **主键**: `id UUID` (外键关联 `auth.users.id`)
- **用途**: 存储业务相关的用户资料、权限、偏好设置

**完整定义**:
```sql
CREATE TABLE user_profiles (
    -- 关联Supabase Auth（主键 + 外键）
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,

    -- 基本信息（6个字段）
    username VARCHAR(50) UNIQUE,            -- 用户名（可选）
    full_name VARCHAR(100),                 -- 全名
    phone VARCHAR(20),                      -- 手机号（业务用）
    avatar_url VARCHAR(500),                -- 头像URL
    department VARCHAR(100),                -- 部门
    position VARCHAR(100),                  -- 职位

    -- 角色和权限（2个字段）⚠️
    role VARCHAR(20) NOT NULL DEFAULT 'media_buyer' CHECK (
        role IN ('admin', 'account_manager', 'data_operator', 'finance', 'media_buyer')
    ),
    account_manager_id UUID REFERENCES user_profiles(id),  -- 上级经理ID

    -- 状态字段（5个字段）
    is_active BOOLEAN DEFAULT true NOT NULL,
    is_verified BOOLEAN DEFAULT false,
    email_verified BOOLEAN DEFAULT false,
    phone_verified BOOLEAN DEFAULT false,
    last_login_at TIMESTAMP,
    last_login_ip VARCHAR(45),
    login_count INTEGER DEFAULT 0,

    -- 偏好设置（3个JSON字段）
    preferences JSONB DEFAULT '{}'::jsonb NOT NULL,        -- 用户偏好
    notification_settings JSONB DEFAULT '{}'::jsonb NOT NULL,  -- 通知设置
    profile_metadata JSONB DEFAULT '{}'::jsonb NOT NULL,   -- 扩展元数据
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'zh-CN',

    -- 审计字段（4个字段）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by UUID REFERENCES user_profiles(id),
    updated_by UUID REFERENCES user_profiles(id)
);

-- 索引（性能优化）
CREATE UNIQUE INDEX idx_user_profiles_username ON user_profiles(username) WHERE username IS NOT NULL;
CREATE INDEX idx_user_profiles_role ON user_profiles(role);
CREATE INDEX idx_user_profiles_active ON user_profiles(is_active);
CREATE INDEX idx_user_profiles_manager ON user_profiles(account_manager_id);
CREATE INDEX idx_user_profiles_created_at ON user_profiles(created_at);
CREATE INDEX idx_user_profiles_department ON user_profiles(department);
```

**AI约束 - 正确使用**:
```python
# ✅ 正确：查询用户资料
from models.user_profile import UserProfile

user_profile = db.query(UserProfile).filter(
    UserProfile.id == user_id
).first()

# ✅ 正确：更新用户资料
user_profile.role = "account_manager"
user_profile.department = "运营部"
user_profile.updated_by = current_user.id
db.commit()

# ✅ 正确：检查权限
if user_profile.role in ["admin", "account_manager"]:
    # 执行管理操作
    pass
```

---

##### 3. user_login_history（登录历史表）

**用途**: 记录所有登录尝试（成功/失败），用于安全审计和异常检测。

```sql
CREATE TABLE user_login_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255),                     -- 记录未注册用户的尝试

    -- 登录信息
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    logout_time TIMESTAMP,
    login_type VARCHAR(20) DEFAULT 'password' NOT NULL,  -- password, oauth, sso
    status VARCHAR(20) DEFAULT 'success' NOT NULL,       -- success, failed
    failure_reason VARCHAR(255),

    -- 设备和位置
    ip_address VARCHAR(45),
    user_agent TEXT,
    device_info JSONB,
    country VARCHAR(50),
    city VARCHAR(100)
);

CREATE INDEX idx_login_history_user ON user_login_history(user_id);
CREATE INDEX idx_login_history_time ON user_login_history(login_time);
CREATE INDEX idx_login_history_status ON user_login_history(status);
CREATE INDEX idx_login_history_ip ON user_login_history(ip_address);
```

---

##### 4. user_sessions（用户会话表）

**用途**: 管理活跃的用户会话，支持多设备登录和会话撤销。

```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- 会话信息
    session_token VARCHAR(500) UNIQUE NOT NULL,  -- JWT token哈希
    device_info JSONB,                           -- 设备信息

    -- 状态和时间
    is_active BOOLEAN DEFAULT true NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_sessions_active ON user_sessions(is_active);
CREATE INDEX idx_sessions_expires ON user_sessions(expires_at);
```

---

##### 5. AI代码生成规范总结

**注册新用户**:
```python
# ✅ 唯一正确方式
from services.supabase_auth_service import supabase_auth_service

result = await supabase_auth_service.register_user(
    email="user@example.com",
    password="SecurePass123!",
    username="john_doe",
    full_name="John Doe",
    role="media_buyer",
    account_manager_id=manager_uuid
)
# 自动创建: auth.users + user_profiles
```

**登录认证**:
```python
# ✅ 正确
result = await supabase_auth_service.login_user(
    email=email,
    password=password,
    remember_me=True
)
# 返回: user信息 + session令牌
```

**查询用户信息**:
```python
# ✅ 正确：查询业务资料
user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
print(user.role, user.department, user.full_name)

# ❌ 错误：尝试查询auth.users
user = db.query(User).filter(User.email == email).first()  # User模型不存在！
```

**更新用户资料**:
```python
# ✅ 正确：更新user_profiles
user_profile = db.query(UserProfile).filter(UserProfile.id == user_id).first()
user_profile.full_name = "New Name"
user_profile.department = "新部门"
db.commit()

# ❌ 错误：尝试更新auth.users
user.email = "new@example.com"  # 邮箱变更需要通过Supabase API
```

**修改密码**:
```python
# ✅ 正确：通过Supabase服务
await supabase_auth_service.update_password(
    new_password="NewSecurePass123!",
    access_token=current_token
)

# ❌ 错误：尝试本地密码处理
# 密码由Supabase Auth管理，不在本地处理
```

#### 项目表 (projects)
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    client_name VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed')),
    budget DECIMAL(12,2),
    start_date DATE,
    end_date DATE,
    manager_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_manager ON projects(manager_id);
```

#### 渠道表 (channels)
```sql
CREATE TABLE channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    company_name VARCHAR(200) NOT NULL,
    contact_info JSONB,
    service_fee_rate DECIMAL(5,2) DEFAULT 0.05,
    account_setup_fee DECIMAL(10,2) DEFAULT 0,
    min_recharge_amount DECIMAL(10,2) DEFAULT 100,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 广告账户表 (ad_accounts)
```sql
CREATE TABLE ad_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    account_id VARCHAR(100) NOT NULL, -- FB账号ID
    platform VARCHAR(20) NOT NULL DEFAULT 'facebook',
    status VARCHAR(20) NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'testing', 'active', 'suspended', 'dead', 'archived')),
    daily_budget DECIMAL(10,2),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    assigned_user_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    channel_id UUID REFERENCES channels(id) ON DELETE SET NULL,
    api_credentials JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ad_accounts_project ON ad_accounts(project_id);
CREATE INDEX idx_ad_accounts_user ON ad_accounts(assigned_user_id);
CREATE INDEX idx_ad_accounts_status ON ad_accounts(status);
```

#### 日报表 (daily_reports)
```sql
CREATE TABLE daily_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ad_account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    report_date DATE NOT NULL,
    spend DECIMAL(10,2) NOT NULL,
    impressions BIGINT,
    clicks BIGINT,
    conversions INTEGER,
    cpl DECIMAL(8,2), -- cost per lead
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('draft', 'pending', 'approved', 'rejected')),
    submitted_at TIMESTAMP,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ad_account_id, report_date)
);

CREATE INDEX idx_daily_reports_account_date ON daily_reports(ad_account_id, report_date);
CREATE INDEX idx_daily_reports_status ON daily_reports(status);
```

#### 充值申请表 (recharge_requests)
```sql
CREATE TABLE recharge_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    ad_account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    amount DECIMAL(10,2) NOT NULL,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'pending', 'approved', 'rejected', 'paid', 'posted')),
    data_clerk_id UUID REFERENCES users(id),
    data_clerk_approved_at TIMESTAMP,
    finance_id UUID REFERENCES users(id),
    finance_approved_at TIMESTAMP,
    paid_at TIMESTAMP,
    posted_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_recharge_requests_project ON recharge_requests(project_id);
CREATE INDEX idx_recharge_requests_status ON recharge_requests(status);
```

### 2. 外键约束规则

所有资金类表必须包含完整的外键追溯：
```sql
-- 外键约束示例
ALTER TABLE daily_reports
ADD CONSTRAINT fk_daily_reports_account
FOREIGN KEY (ad_account_id) REFERENCES ad_accounts(id) ON DELETE CASCADE;

ALTER TABLE daily_reports
ADD CONSTRAINT fk_daily_reports_user
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
```

### ⚠️ AI代码生成约束提示

**当AI生成涉及数据库操作的代码时，必须遵守以下约束：**

1. **严格遵守Supabase Auth双表架构**
   ```python
   # ✅ 正确：区分两个表的职责
   from models.user_profile import UserProfile  # 业务数据，可写

   # 读取用户信息
   user_profile = db.query(UserProfile).filter(UserProfile.id == user_id).first()

   # 更新业务资料（仅操作user_profiles表）
   user_profile.full_name = "新名字"
   db.commit()

   # ❌ 错误：尝试写入auth.users表
   from supabase import create_client
   supabase.table("auth.users").update({"email": "new@example.com"})  # 禁止！auth.users只读
   ```

2. **仅使用已定义的表和字段**
   - ✅ 允许：本章节SQL定义的所有表（user_profiles, projects, channels, ad_accounts, daily_reports, topup_requests等）
   - ❌ 禁止：创建未定义的新表、添加未定义的字段、修改表结构

3. **外键关联必须正确**
   ```python
   # ✅ 正确：遵循外键定义
   project = Project(
       name="新项目",
       created_by=user_id  # user_id 必须是 user_profiles.id（UUID），而非auth.users.id
   )

   # ❌ 错误：引用不存在的外键
   project = Project(
       name="新项目",
       channel_id=999  # channels表的主键是UUID，不是整数！
   )
   ```

4. **主键必须使用UUID**
   - 所有表的主键都是UUID类型，使用 `gen_random_uuid()` 或后端生成
   - 禁止使用Integer自增主键

5. **状态字段必须使用CHECK约束定义的枚举值**
   ```python
   # ✅ 正确：使用已定义的状态值
   ad_account.status = "active"  # ad_accounts.status允许的6个值之一

   # ❌ 错误：使用未定义的状态值
   ad_account.status = "运行中"  # 中文状态值，违反CHECK约束！
   ```

6. **时间戳字段必须使用UTC时间**
   ```python
   from datetime import datetime, timezone

   # ✅ 正确：使用UTC时间
   daily_report.submitted_at = datetime.now(timezone.utc)

   # ❌ 错误：使用本地时间
   daily_report.submitted_at = datetime.now()  # 缺少时区信息
   ```

7. **JSONB字段必须验证结构**
   ```python
   # ✅ 正确：验证JSONB字段结构
   from pydantic import BaseModel, ValidationError

   class ContactInfo(BaseModel):
       phone: str
       email: str
       address: Optional[str]

   try:
       contact_info = ContactInfo(**channel.contact_info)
   except ValidationError as e:
       raise HTTPException(status_code=400, detail="联系方式格式错误")

   # ❌ 错误：直接操作未验证的JSONB
   channel.contact_info = {"随便写": "任意值"}  # 缺少结构验证
   ```

8. **索引使用必须对应查询场景**
   - 高频查询字段必须创建索引（如 `daily_reports(ad_account_id, report_date)`）
   - 避免在低基数字段创建索引（如 `is_active`）

**违反上述任何约束的代码将导致数据库错误、性能问题或数据不一致！**

---

## 四、安全策略与权限控制

> ⚠️ **重要：当前版本权限控制立场**
>
> **当前正式版本不启用数据库级 RLS（Row Level Security）**，所有权限控制通过应用层 RBAC 与查询过滤实现。
>
> 本章节中关于 RLS 的内容，仅作为未来优化/高级方案参考，**不得在当前版本中直接启用**。实际开发中：
> - ✅ 使用 Service 层的 `@require_role` 装饰器进行权限控制
> - ✅ 在查询时手动添加用户过滤条件（如 `filter(DailyReport.user_id == current_user.id)`）
> - ❌ 不要执行 `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`
> - ❌ 不要创建 PostgreSQL POLICY

### 角色定义与权限矩阵 ⚠️

#### 当前有效角色（仅5个）

| 角色标识 | 角色名称 | 权限范围 | 典型用户 |
|----------|----------|----------|----------|
| `admin` | 系统管理员 | 全部权限，系统配置 | 技术负责人 |
| `account_manager` | 项目经理 | 管理项目、分配账户、审批日报 | 户管、项目负责人 |
| `data_operator` | 数据操作员 | 管理账户、审核日报、数据导入 | 数据员、运营人员 |
| `finance` | 财务人员 | 财务审批、对账、成本分析 | 财务专员 |
| `media_buyer` | 媒体投放员 | 提交日报、申请充值、查看自己数据 | 投手、广告优化师 |

> **AI 使用约束**：
> - 生成任何权限相关代码/配置时，**只能使用上述5个角色枚举**
> - 遇到 `data_clerk`、`manager`、`trader` 等旧角色名，应视为错误并立即纠正
> - 角色名称区分大小写，必须全小写

### 1. 应用层权限控制（当前实现）

#### 基于装饰器的权限控制
```python
# core/permissions.py
from functools import wraps
from fastapi import HTTPException, status

def require_role(allowed_roles: list):
    """权限装饰器，检查用户角色"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未登录"
                )

            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要角色: {', '.join(allowed_roles)}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

#### Service层数据过滤示例
```python
# services/daily_report_service.py
async def get_user_daily_reports(db: Session, current_user: User):
    """根据用户角色返回不同范围的日报"""
    query = db.query(DailyReport)

    if current_user.role == "admin":
        # 管理员看所有日报
        pass
    elif current_user.role in ["account_manager", "data_operator"]:
        # 户管和数据员看自己管理的项目下的日报
        query = query.join(AdAccount).join(Project).filter(
            Project.account_manager_id == current_user.id
        )
    elif current_user.role == "media_buyer":
        # 投手只看自己提交的日报
        query = query.filter(DailyReport.created_by == current_user.id)
    else:
        # 其他角色无权限
        return []

    return query.all()
```

---

### 2. RLS策略参考（未来可选方案）

> ⚠️ **注意：以下RLS内容仅为未来升级设计草案，当前版本禁止执行**

<details>
<summary>点击展开 RLS 策略示例（仅供参考，不要执行）</summary>

```sql
-- ⚠️ 不要执行！仅供未来参考
-- 启用RLS
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE topup_requests ENABLE ROW LEVEL SECURITY;

-- 项目访问策略
CREATE POLICY project_access_policy ON projects
    USING (
        current_setting('app.current_role') = 'admin'
        OR created_by = current_setting('app.current_user_id')::uuid
        OR EXISTS (
            SELECT 1 FROM ad_accounts
            WHERE ad_accounts.project_id = projects.id
            AND ad_accounts.assigned_user_id = current_setting('app.current_user_id')::uuid
        )
    );

-- 广告账户访问策略
CREATE POLICY ad_account_access_policy ON ad_accounts
    USING (
        current_setting('app.current_role') = 'admin'
        OR current_setting('app.current_role') = 'data_operator'
        OR assigned_user_id = current_setting('app.current_user_id')::uuid
    );

-- 日报访问策略
CREATE POLICY daily_report_access_policy ON daily_reports
    USING (
        current_setting('app.current_role') = 'admin'
        OR current_setting('app.current_role') = 'data_operator'
        OR user_id = current_setting('app.current_user_id')::uuid
        OR EXISTS (
            SELECT 1 FROM ad_accounts
            WHERE ad_accounts.id = daily_reports.ad_account_id
            AND ad_accounts.assigned_user_id = current_setting('app.current_user_id')::uuid
        )
    );

-- 充值请求访问策略
CREATE POLICY recharge_request_access_policy ON recharge_requests
    USING (
        current_setting('app.current_role') = 'admin'
        OR current_setting('app.current_role') IN ('data_operator', 'finance')
        OR user_id = current_setting('app.current_user_id')::uuid
    );
```

</details>

---

### 3. 权限矩阵详情

#### 3.1 角色定义和层级

```python
# 核心角色定义（大小写敏感）
ALLOWED_ROLES = [
    "admin",           # 系统管理员（最高权限）
    "account_manager", # 账户经理（管理团队和项目）
    "data_operator",   # 数据员（日报审核、账户分配）
    "finance",         # 财务（充值审批、对账管理）
    "media_buyer"      # 投手（日报提交、充值申请）
]

# 角色层级（数字越大权限越高）
ROLE_HIERARCHY = {
    "media_buyer": 1,
    "data_operator": 2,
    "finance": 2,
    "account_manager": 3,
    "admin": 4
}
```

---

#### 3.2 详细权限矩阵

| 功能模块 | admin | account_manager | data_operator | finance | media_buyer |
|---------|-------|-----------------|---------------|---------|-------------|
| **用户管理** | | | | | |
| 创建用户 | ✅ 全部 | ✅ 下级用户 | ❌ | ❌ | ❌ |
| 修改用户资料 | ✅ 全部 | ✅ 团队成员 | ❌ | ❌ | 🔒 仅自己 |
| 停用/激活用户 | ✅ 全部 | ✅ 团队成员 | ❌ | ❌ | ❌ |
| 分配上级经理 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 查看用户列表 | ✅ 全部 | ✅ 团队成员 | ✅ 全部 | ✅ 全部 | 🔒 仅自己 |
| | | | | | |
| **项目管理** | | | | | |
| 创建项目 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 编辑项目 | ✅ 全部 | ✅ 负责项目 | ❌ | ❌ | ❌ |
| 删除/归档项目 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 查看项目 | ✅ 全部 | ✅ 负责项目 | ✅ 全部 | ✅ 全部 | 🔒 参与项目 |
| 设置项目预算 | ✅ | ✅ 负责项目 | ❌ | ✅ 查看 | ❌ |
| | | | | | |
| **广告账户管理** | | | | | |
| 创建账户 | ✅ | ✅ | ✅ | ❌ | ❌ |
| 分配账户给投手 | ✅ 全部 | ✅ 项目内 | ✅ 全部 | ❌ | ❌ |
| 修改账户状态 | ✅ 全部 | ✅ 项目内 | ✅ 全部 | ❌ | ❌ |
| 删除账户 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 查看账户 | ✅ 全部 | ✅ 项目内 | ✅ 全部 | ✅ 全部 | 🔒 分配给我的 |
| 设置账户预算 | ✅ | ✅ 项目内 | ✅ | ❌ | ❌ |
| | | | | | |
| **日报管理** | | | | | |
| 提交日报 | ✅ | ✅ | ✅ | ✅ | ✅ 分配账户 |
| 编辑草稿日报 | ✅ 全部 | ✅ 团队日报 | ✅ 全部 | ❌ | 🔒 自己的 |
| 审核日报 | ✅ | ✅ 项目内 | ✅ 全部 | ❌ | ❌ |
| 驳回日报 | ✅ | ✅ 项目内 | ✅ 全部 | ❌ | ❌ |
| 删除日报 | ✅ | ❌ | ❌ | ❌ | 🔒 草稿状态 |
| 查看日报 | ✅ 全部 | ✅ 项目内 | ✅ 全部 | ✅ 全部 | 🔒 自己的 |
| | | | | | |
| **充值管理** | | | | | |
| 申请充值 | ✅ | ✅ | ✅ | ✅ | ✅ 分配账户 |
| 初审充值申请 | ✅ | ✅ 项目内 | ✅ 全部 | ❌ | ❌ |
| 终审/批准充值 | ✅ | ❌ | ❌ | ✅ 全部 | ❌ |
| 财务打款确认 | ✅ | ❌ | ❌ | ✅ | ❌ |
| 到账确认 | ✅ 全部 | ✅ 项目内 | ✅ 全部 | ❌ | ❌ |
| 查看充值记录 | ✅ 全部 | ✅ 项目内 | ✅ 全部 | ✅ 全部 | 🔒 自己申请的 |
| | | | | | |
| **对账管理** | | | | | |
| 创建对账报告 | ✅ | ❌ | ✅ | ✅ | ❌ |
| 执行对账 | ✅ | ❌ | ✅ | ✅ | ❌ |
| 审核对账结果 | ✅ | ❌ | ❌ | ✅ | ❌ |
| 导出对账报表 | ✅ | ✅ 项目内 | ✅ | ✅ | ❌ |
| 查看对账记录 | ✅ 全部 | ✅ 项目内 | ✅ 全部 | ✅ 全部 | ❌ |
| | | | | | |
| **报表分析** | | | | | |
| 查看项目报表 | ✅ 全部 | ✅ 负责项目 | ✅ 全部 | ✅ 全部 | 🔒 参与项目 |
| 查看账户报表 | ✅ 全部 | ✅ 项目内 | ✅ 全部 | ✅ 全部 | 🔒 分配账户 |
| 查看财务报表 | ✅ | ✅ 负责项目 | ✅ 基础 | ✅ 全部 | ❌ |
| 导出数据 | ✅ 全部 | ✅ 项目内 | ✅ 全部 | ✅ 全部 | 🔒 自己数据 |
| | | | | | |
| **系统管理** | | | | | |
| 查看审计日志 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 系统配置 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 数据备份 | ✅ | ❌ | ❌ | ❌ | ❌ |

**图例**:
- ✅ = 有权限
- ❌ = 无权限
- 🔒 = 有限权限（仅自己的数据）

---

#### 2.3 AI权限检查代码规范

**FastAPI路由权限装饰器**:
```python
from core.permissions import require_role, require_any_role

# ✅ 正确：单角色检查
@router.post("/api/projects")
@require_role(["admin", "account_manager"])  # 只有admin和account_manager可以创建项目
async def create_project(...):
    pass

# ✅ 正确：多角色检查
@router.get("/api/daily-reports")
@require_any_role(["admin", "account_manager", "data_operator", "finance"])
async def list_reports(...):
    pass

# ❌ 错误：使用中文角色名
@require_role(["管理员", "户管"])  # 错误！必须用英文
async def some_endpoint(...):
    pass

# ❌ 错误：使用旧角色名
@require_role(["data_clerk"])  # 错误！应该是data_operator
async def some_endpoint(...):
    pass
```

**Service层权限检查**:
```python
from core.permissions import has_permission

# ✅ 正确：检查用户是否有权限访问项目
def get_project(project_id: str, current_user: UserProfile, db: Session):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 权限检查
    if current_user.role == "admin":
        # 管理员可以查看所有项目
        return project
    elif current_user.role == "account_manager":
        # 账户经理只能查看负责的项目
        if project.manager_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此项目")
        return project
    elif current_user.role in ["data_operator", "finance"]:
        # 数据员和财务可以查看所有项目
        return project
    elif current_user.role == "media_buyer":
        # 投手只能查看参与的项目（通过ad_accounts关联）
        has_access = db.query(AdAccount).filter(
            AdAccount.project_id == project_id,
            AdAccount.assigned_user_id == current_user.id
        ).first()
        if not has_access:
            raise HTTPException(status_code=403, detail="无权访问此项目")
        return project
    else:
        raise HTTPException(status_code=403, detail="角色未定义")
```

**RLS策略示例**:
```sql
-- ✅ 正确：user_profiles表的RLS策略
CREATE POLICY "用户只能查看自己的资料或管理员/经理可查看团队资料"
ON user_profiles FOR SELECT
USING (
    auth.uid() = id  -- 用户可以查看自己
    OR
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND up.role IN ('admin', 'account_manager', 'data_operator', 'finance')
    )  -- 管理角色可以查看所有
);

-- ✅ 正确：daily_reports表的RLS策略
CREATE POLICY "投手只能查看自己的日报"
ON daily_reports FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND (
            up.role IN ('admin', 'account_manager', 'data_operator', 'finance')  -- 管理角色查看全部
            OR
            (up.role = 'media_buyer' AND daily_reports.user_id = up.id)  -- 投手查看自己的
        )
    )
);
```

---

#### 2.4 常见权限错误和修正

**错误1: 硬编码角色名**
```python
# ❌ 错误
if user.role == "管理员":
    pass

# ✅ 正确
if user.role == "admin":
    pass
```

**错误2: 使用废弃的角色名**
```python
# ❌ 错误
if user.role == "data_clerk":  # 旧名称
    pass

# ✅ 正确
if user.role == "data_operator":  # 新名称
    pass
```

**错误3: 权限检查不完整**
```python
# ❌ 错误：缺少角色检查
@router.get("/api/projects/{id}")
async def get_project(id: str):
    return db.query(Project).filter(Project.id == id).first()

# ✅ 正确：添加权限检查
@router.get("/api/projects/{id}")
@require_any_role(["admin", "account_manager", "data_operator", "finance", "media_buyer"])
async def get_project(
    id: str,
    current_user: UserProfile = Depends(get_current_user)
):
    # 根据角色过滤数据
    project = project_service.get_project(id, current_user, db)
    return project
```

**错误4: 忘记检查数据所有权**
```python
# ❌ 错误：投手可以看到其他投手的日报
@router.get("/api/daily-reports")
async def list_reports(current_user: UserProfile = Depends(get_current_user)):
    return db.query(DailyReport).all()  # 返回所有日报！

# ✅ 正确：根据角色过滤
@router.get("/api/daily-reports")
async def list_reports(current_user: UserProfile = Depends(get_current_user)):
    query = db.query(DailyReport)

    if current_user.role == "media_buyer":
        # 投手只能看自己的
        query = query.filter(DailyReport.user_id == current_user.id)
    elif current_user.role in ["admin", "data_operator", "finance"]:
        # 管理角色可以看全部
        pass
    elif current_user.role == "account_manager":
        # 账户经理只能看负责项目的
        query = query.join(AdAccount).join(Project).filter(
            Project.manager_id == current_user.id
        )

    return query.all()
```

---

### 3. RLS策略完整说明 ⚠️

> **重要**: Row Level Security (RLS) 是本项目数据安全的核心机制，通过PostgreSQL的原生RLS功能实现数据隔离，AI生成代码时必须确保RLS策略正确启用。

#### 3.1 RLS策略概述

**什么是RLS**:
- PostgreSQL的行级安全策略（Row Level Security）
- 在数据库层面强制执行数据访问控制
- 每个用户只能看到/修改自己有权限的数据
- 即使应用层权限被绕过，数据库层仍然受保护

**RLS的优势**:
1. **安全性高**: 数据隔离在数据库层强制执行，无法绕过
2. **代码简洁**: 不需要在每个查询中手写权限过滤逻辑
3. **一致性强**: 所有数据库访问（包括直连）都受RLS保护
4. **审计友好**: 所有数据访问自动受控，便于审计

**本项目RLS设计原则**:
- 所有核心业务表都启用RLS
- 使用Supabase Auth的`auth.uid()`获取当前用户ID
- 结合`user_profiles`表的角色信息进行权限判断
- 支持5种角色的差异化访问控制

---

#### 3.2 完整表级RLS策略

> **AI约束**: 创建新表时必须同步创建对应的RLS策略，以下是所有核心表的RLS策略定义。

##### 3.2.1 用户资料表（user_profiles）

```sql
-- 启用RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- 策略1: SELECT - 用户可以查看自己，管理角色可查看所有
CREATE POLICY "user_profiles_select_policy"
ON user_profiles FOR SELECT
USING (
    auth.uid() = id  -- 用户可以查看自己的资料
    OR
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND up.role IN ('admin', 'account_manager', 'data_operator', 'finance')
    )  -- 管理角色可以查看所有用户
);

-- 策略2: INSERT - 只有admin可以创建用户
CREATE POLICY "user_profiles_insert_policy"
ON user_profiles FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND up.role = 'admin'
    )
);

-- 策略3: UPDATE - 用户可以更新自己，管理员可更新所有
CREATE POLICY "user_profiles_update_policy"
ON user_profiles FOR UPDATE
USING (
    auth.uid() = id  -- 用户可以更新自己
    OR
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND up.role IN ('admin', 'account_manager')  -- 管理员和经理可以更新团队成员
    )
)
WITH CHECK (
    auth.uid() = id
    OR
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND up.role IN ('admin', 'account_manager')
    )
);

-- 策略4: DELETE - 只有admin可以删除
CREATE POLICY "user_profiles_delete_policy"
ON user_profiles FOR DELETE
USING (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND up.role = 'admin'
    )
);
```

##### 3.2.2 项目表（projects）

```sql
-- 启用RLS
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- 策略1: SELECT - 根据角色差异化访问
CREATE POLICY "projects_select_policy"
ON projects FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND (
            up.role IN ('admin', 'data_operator', 'finance')  -- 全部可见
            OR
            (up.role = 'account_manager' AND projects.account_manager_id = up.id)  -- 经理看负责的
            OR
            (up.role = 'media_buyer' AND EXISTS (
                SELECT 1 FROM ad_accounts aa
                WHERE aa.project_id = projects.id
                AND aa.assigned_user_id = up.id
            ))  -- 投手看参与的
        )
    )
);

-- 策略2: INSERT - 只有admin和account_manager可以创建项目
CREATE POLICY "projects_insert_policy"
ON projects FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND up.role IN ('admin', 'account_manager')
    )
);

-- 策略3: UPDATE - admin全部可改，经理改负责的
CREATE POLICY "projects_update_policy"
ON projects FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND (
            up.role = 'admin'
            OR
            (up.role = 'account_manager' AND projects.account_manager_id = up.id)
        )
    )
);

-- 策略4: DELETE - 只有admin可以删除项目
CREATE POLICY "projects_delete_policy"
ON projects FOR DELETE
USING (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND up.role = 'admin'
    )
);
```

##### 3.2.3 广告账户表（ad_accounts）

```sql
-- 启用RLS
ALTER TABLE ad_accounts ENABLE ROW LEVEL SECURITY;

-- 策略1: SELECT - 根据角色和分配关系访问
CREATE POLICY "ad_accounts_select_policy"
ON ad_accounts FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND (
            up.role IN ('admin', 'data_operator', 'finance')  -- 全部可见
            OR
            (up.role = 'account_manager' AND EXISTS (
                SELECT 1 FROM projects p
                WHERE p.id = ad_accounts.project_id
                AND p.account_manager_id = up.id
            ))  -- 经理看项目内的
            OR
            (up.role = 'media_buyer' AND ad_accounts.assigned_user_id = up.id)  -- 投手看分配的
        )
    )
);

-- 策略2: INSERT - admin, account_manager, data_operator可创建
CREATE POLICY "ad_accounts_insert_policy"
ON ad_accounts FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND up.role IN ('admin', 'account_manager', 'data_operator')
    )
);

-- 策略3: UPDATE - 同INSERT
CREATE POLICY "ad_accounts_update_policy"
ON ad_accounts FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND up.role IN ('admin', 'account_manager', 'data_operator')
    )
);

-- 策略4: DELETE - 只有admin可删除
CREATE POLICY "ad_accounts_delete_policy"
ON ad_accounts FOR DELETE
USING (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND up.role = 'admin'
    )
);
```

##### 3.2.4 日报表（daily_reports）

```sql
-- 启用RLS
ALTER TABLE daily_reports ENABLE ROW LEVEL SECURITY;

-- 策略1: SELECT - 投手看自己的，管理角色看全部/项目内
CREATE POLICY "daily_reports_select_policy"
ON daily_reports FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND (
            up.role IN ('admin', 'data_operator', 'finance')  -- 全部可见
            OR
            (up.role = 'account_manager' AND EXISTS (
                SELECT 1 FROM ad_accounts aa
                JOIN projects p ON p.id = aa.project_id
                WHERE aa.id = daily_reports.ad_account_id
                AND p.account_manager_id = up.id
            ))  -- 经理看项目内的
            OR
            (up.role = 'media_buyer' AND daily_reports.submitted_by = up.id)  -- 投手看自己的
        )
    )
);

-- 策略2: INSERT - 所有角色都可以提交日报（但必须是分配给自己的账户）
CREATE POLICY "daily_reports_insert_policy"
ON daily_reports FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND (
            up.role IN ('admin', 'account_manager', 'data_operator', 'finance')
            OR
            (up.role = 'media_buyer' AND EXISTS (
                SELECT 1 FROM ad_accounts aa
                WHERE aa.id = daily_reports.ad_account_id
                AND aa.assigned_user_id = up.id
            ))
        )
    )
);

-- 策略3: UPDATE - 草稿状态可修改，审核后只有admin可改
CREATE POLICY "daily_reports_update_policy"
ON daily_reports FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND (
            (up.role = 'admin')  -- admin全部可改
            OR
            (daily_reports.status = 'draft' AND daily_reports.submitted_by = up.id)  -- 草稿状态作者可改
            OR
            (up.role IN ('account_manager', 'data_operator') AND daily_reports.status IN ('pending', 'rejected'))  -- 管理角色可审核
        )
    )
);

-- 策略4: DELETE - 只能删除自己的草稿
CREATE POLICY "daily_reports_delete_policy"
ON daily_reports FOR DELETE
USING (
    daily_reports.status = 'draft'
    AND
    (
        daily_reports.submitted_by = auth.uid()
        OR
        EXISTS (
            SELECT 1 FROM user_profiles up
            WHERE up.id = auth.uid()
            AND up.role = 'admin'
        )
    )
);
```

##### 3.2.5 充值申请表（topup_requests）

```sql
-- 启用RLS
ALTER TABLE topup_requests ENABLE ROW LEVEL SECURITY;

-- 策略1: SELECT - 根据角色查看
CREATE POLICY "topup_requests_select_policy"
ON topup_requests FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND (
            up.role IN ('admin', 'data_operator', 'finance')  -- 全部可见
            OR
            (up.role = 'account_manager' AND EXISTS (
                SELECT 1 FROM projects p
                WHERE p.id = topup_requests.project_id
                AND p.account_manager_id = up.id
            ))  -- 经理看项目内的
            OR
            (up.role = 'media_buyer' AND topup_requests.applicant_id = up.id)  -- 投手看自己申请的
        )
    )
);

-- 策略2: INSERT - 所有角色都可以申请充值
CREATE POLICY "topup_requests_insert_policy"
ON topup_requests FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND up.role IN ('admin', 'account_manager', 'data_operator', 'finance', 'media_buyer')
    )
);

-- 策略3: UPDATE - 根据状态和角色
CREATE POLICY "topup_requests_update_policy"
ON topup_requests FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND (
            (up.role = 'admin')  -- admin全部可改
            OR
            (up.role IN ('account_manager', 'data_operator') AND topup_requests.status IN ('pending_review', 'approved'))  -- 初审
            OR
            (up.role = 'finance' AND topup_requests.status IN ('approved', 'paid'))  -- 财务审批和打款
            OR
            (topup_requests.status = 'draft' AND topup_requests.applicant_id = up.id)  -- 草稿状态申请人可改
        )
    )
);

-- 策略4: DELETE - 只能删除自己的草稿
CREATE POLICY "topup_requests_delete_policy"
ON topup_requests FOR DELETE
USING (
    topup_requests.status = 'draft'
    AND
    (
        topup_requests.applicant_id = auth.uid()
        OR
        EXISTS (
            SELECT 1 FROM user_profiles up
            WHERE up.id = auth.uid()
            AND up.role = 'admin'
        )
    )
);
```

##### 3.2.6 对账表（reconciliations）

```sql
-- 启用RLS
ALTER TABLE reconciliations ENABLE ROW LEVEL SECURITY;

-- 策略1: SELECT - admin, data_operator, finance全部可见，经理看项目内的
CREATE POLICY "reconciliations_select_policy"
ON reconciliations FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND (
            up.role IN ('admin', 'data_operator', 'finance')
            OR
            (up.role = 'account_manager' AND EXISTS (
                SELECT 1 FROM projects p
                WHERE p.id = reconciliations.project_id
                AND p.account_manager_id = up.id
            ))
        )
    )
);

-- 策略2: INSERT - 只有admin, data_operator, finance可以创建对账
CREATE POLICY "reconciliations_insert_policy"
ON reconciliations FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND up.role IN ('admin', 'data_operator', 'finance')
    )
);

-- 策略3: UPDATE - 同INSERT
CREATE POLICY "reconciliations_update_policy"
ON reconciliations FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND up.role IN ('admin', 'data_operator', 'finance')
    )
);

-- 策略4: DELETE - 只有admin可删除
CREATE POLICY "reconciliations_delete_policy"
ON reconciliations FOR DELETE
USING (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND up.role = 'admin'
    )
);
```

##### 3.2.7 审计日志表（audit_logs）

```sql
-- 启用RLS
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- 策略1: SELECT - 只有admin可以查看审计日志
CREATE POLICY "audit_logs_select_policy"
ON audit_logs FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND up.role = 'admin'
    )
);

-- 策略2: INSERT - 系统自动插入，所有已认证用户都可以
CREATE POLICY "audit_logs_insert_policy"
ON audit_logs FOR INSERT
WITH CHECK (auth.uid() IS NOT NULL);

-- 策略3: UPDATE - 禁止更新审计日志
-- 不创建UPDATE策略，确保审计日志不可修改

-- 策略4: DELETE - 只有admin可删除过期日志
CREATE POLICY "audit_logs_delete_policy"
ON audit_logs FOR DELETE
USING (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND up.role = 'admin'
    )
);
```

---

#### 3.3 RLS策略测试方法

**测试1: 验证投手只能看到自己的日报**
```sql
-- 以投手身份登录（模拟）
SET LOCAL app.current_user_id = '550e8400-e29b-41d4-a716-446655440000';
SET LOCAL app.current_role = 'media_buyer';

-- 查询日报（应该只返回该投手提交的）
SELECT * FROM daily_reports;

-- 预期结果：只返回 submitted_by = '550e8400-...' 的记录
```

**测试2: 验证admin可以看到所有数据**
```sql
-- 以admin身份登录
SET LOCAL app.current_user_id = 'admin-uuid';
SET LOCAL app.current_role = 'admin';

-- 查询所有表
SELECT COUNT(*) FROM user_profiles;  -- 应返回所有用户
SELECT COUNT(*) FROM projects;       -- 应返回所有项目
SELECT COUNT(*) FROM daily_reports;  -- 应返回所有日报
```

**测试3: 验证account_manager只能看到负责项目的数据**
```sql
-- 以account_manager身份登录
SET LOCAL app.current_user_id = 'manager-uuid';
SET LOCAL app.current_role = 'account_manager';

-- 查询项目
SELECT * FROM projects WHERE account_manager_id = 'manager-uuid';

-- 预期结果：只返回该经理负责的项目
```

**测试4: 验证权限隔离**
```sql
-- 投手A尝试查看投手B的日报
SET LOCAL app.current_user_id = 'buyer-a-uuid';
SET LOCAL app.current_role = 'media_buyer';

SELECT * FROM daily_reports WHERE submitted_by = 'buyer-b-uuid';

-- 预期结果：空结果集（RLS策略阻止）
```

---

#### 3.4 AI代码生成约束 ⚠️

**约束1: 创建新表必须同步创建RLS策略**
```sql
-- ✅ 正确：创建表后立即启用RLS和创建策略
CREATE TABLE new_table (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES user_profiles(id),
    data TEXT
);

-- 立即启用RLS
ALTER TABLE new_table ENABLE ROW LEVEL SECURITY;

-- 创建策略
CREATE POLICY "new_table_select_policy"
ON new_table FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND (up.role = 'admin' OR new_table.user_id = up.id)
    )
);

-- ❌ 错误：创建表后忘记启用RLS
CREATE TABLE new_table (...);
-- 没有后续的RLS配置！数据将完全暴露！
```

**约束2: 策略必须覆盖所有操作（SELECT, INSERT, UPDATE, DELETE）**
```sql
-- ✅ 正确：4个策略覆盖所有操作
CREATE POLICY "table_select_policy" ON table FOR SELECT USING (...);
CREATE POLICY "table_insert_policy" ON table FOR INSERT WITH CHECK (...);
CREATE POLICY "table_update_policy" ON table FOR UPDATE USING (...);
CREATE POLICY "table_delete_policy" ON table FOR DELETE USING (...);

-- ❌ 错误：只创建了SELECT策略，其他操作被默认拒绝
CREATE POLICY "table_select_policy" ON table FOR SELECT USING (...);
-- 用户无法INSERT/UPDATE/DELETE！
```

**约束3: 策略中必须使用Supabase Auth函数**
```python
# ✅ 正确：使用auth.uid()获取当前用户
USING (auth.uid() = user_id)

# ❌ 错误：使用session变量（不适用于Supabase）
USING (current_setting('app.current_user_id')::uuid = user_id)
```

**约束4: 复杂权限判断应该在策略中完成**
```sql
-- ✅ 正确：RLS策略中完整的权限判断
CREATE POLICY "complex_access_policy"
ON some_table FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND (
            up.role = 'admin'
            OR
            (up.role = 'account_manager' AND some_table.project_id IN (
                SELECT id FROM projects WHERE account_manager_id = up.id
            ))
            OR
            (up.role = 'media_buyer' AND some_table.user_id = up.id)
        )
    )
);

-- ❌ 错误：策略太简单，依赖应用层过滤
CREATE POLICY "simple_policy"
ON some_table FOR SELECT
USING (true);  -- 所有人都能看到！安全漏洞！
```

---

#### 3.5 常见问题和解决方案

**问题1: RLS策略导致查询性能下降**

**原因**: 复杂的子查询在RLS策略中可能影响性能。

**解决方案**:
```sql
-- 优化前：多次子查询
CREATE POLICY "slow_policy"
ON daily_reports FOR SELECT
USING (
    EXISTS (SELECT 1 FROM user_profiles WHERE id = auth.uid() AND role = 'admin')
    OR
    EXISTS (SELECT 1 FROM ad_accounts WHERE ...)
);

-- 优化后：减少子查询次数
CREATE POLICY "fast_policy"
ON daily_reports FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND (
            up.role = 'admin'
            OR EXISTS (SELECT 1 FROM ad_accounts WHERE ...)
        )
    )
);

-- 同时添加索引
CREATE INDEX idx_user_profiles_id_role ON user_profiles(id, role);
```

**问题2: 用户无法访问自己应该能看到的数据**

**原因**: RLS策略配置错误或遗漏。

**排查方法**:
```sql
-- 1. 检查RLS是否启用
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public';

-- 2. 查看表的所有策略
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies
WHERE tablename = 'your_table';

-- 3. 测试特定用户的访问
SET LOCAL app.current_user_id = 'test-user-uuid';
SET LOCAL app.current_role = 'media_buyer';
SELECT * FROM your_table;
```

**问题3: 系统管理员也无法访问数据**

**原因**: 策略过于严格，甚至限制了admin。

**解决方案**:
```sql
-- ✅ 正确：admin总是有完全访问权限
CREATE POLICY "safe_policy"
ON some_table FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM user_profiles up
        WHERE up.id = auth.uid()
        AND (
            up.role = 'admin'  -- admin优先
            OR
            (其他角色的条件...)
        )
    )
);
```

**问题4: 迁移数据时RLS策略阻止操作**

**解决方案**:
```sql
-- 临时禁用RLS（仅在迁移时）
ALTER TABLE some_table DISABLE ROW LEVEL SECURITY;

-- 执行迁移
-- ... 数据迁移操作 ...

-- 重新启用RLS
ALTER TABLE some_table ENABLE ROW LEVEL SECURITY;
```

### ⚠️ AI代码生成约束提示

**当AI生成涉及权限控制的代码时，必须遵守以下约束：**

1. **仅使用5个合法角色枚举值**
   ```python
   # ✅ 正确：使用合法角色
   from core.permissions import ALLOWED_ROLES

   if current_user.role in ["admin", "account_manager"]:
       # 执行管理操作

   # ❌ 错误：使用废弃或自定义角色
   if current_user.role == "data_clerk":  # data_clerk已废弃！
   if current_user.role == "超级管理员":  # 禁止中文角色名
   ```

2. **必须使用@require_role装饰器进行权限控制**
   ```python
   from core.permissions import require_role

   # ✅ 正确：使用装饰器
   @router.post("/projects")
   @require_role(["admin", "account_manager"])
   async def create_project(
       project: ProjectCreate,
       current_user: AuthenticatedUser = Depends(get_current_user)
   ):
       # 创建项目

   # ❌ 错误：硬编码权限检查
   @router.post("/projects")
   async def create_project(project: ProjectCreate):
       if request.user.role != "admin":  # 硬编码，缺少审计
           raise HTTPException(403)
   ```

3. **RLS策略必须与后端权限一致**
   - 后端API使用 `@require_role` 限制的操作，RLS策略也必须限制相同角色
   - 避免RLS策略允许但后端禁止，或反之

4. **数据隔离必须遵循业务规则**
   ```python
   # ✅ 正确：投手只能查看自己的日报
   @router.get("/daily-reports")
   @require_role(["media_buyer", "data_operator", "admin"])
   async def get_daily_reports(
       current_user: AuthenticatedUser = Depends(get_current_user),
       db: Session = Depends(get_db)
   ):
       query = db.query(DailyReport)
       if current_user.role == "media_buyer":
           query = query.filter(DailyReport.user_id == current_user.id)
       return query.all()

   # ❌ 错误：未进行数据隔离
   @router.get("/daily-reports")
   async def get_daily_reports(db: Session = Depends(get_db)):
       return db.query(DailyReport).all()  # 所有人都能看到所有日报
   ```

5. **敏感操作必须记录审计日志**
   ```python
   from services.audit_service import log_audit

   # ✅ 正确：记录审计日志
   @router.delete("/projects/{project_id}")
   @require_role(["admin"])
   async def delete_project(
       project_id: str,
       current_user: AuthenticatedUser = Depends(get_current_user),
       db: Session = Depends(get_db)
   ):
       project = db.query(Project).filter(Project.id == project_id).first()
       db.delete(project)
       db.commit()

       # 记录审计日志
       await log_audit(
           action="project.delete",
           user_id=current_user.id,
           resource_type="project",
           resource_id=project_id,
           details={"project_name": project.name}
       )
       return success_response(message="项目已删除")

   # ❌ 错误：敏感操作未记录
   @router.delete("/projects/{project_id}")
   async def delete_project(project_id: str, db: Session = Depends(get_db)):
       db.query(Project).filter(Project.id == project_id).delete()
       db.commit()  # 直接删除，无审计记录
   ```

6. **JWT令牌验证必须使用统一依赖**
   ```python
   from deps.supabase_auth import get_current_user

   # ✅ 正确：使用统一依赖注入
   @router.get("/me")
   async def get_me(current_user: Dict = Depends(get_current_user)):
       return current_user

   # ❌ 错误：手动解析JWT
   @router.get("/me")
   async def get_me(request: Request):
       token = request.headers.get("authorization").split(" ")[1]
       payload = jwt.decode(token, SECRET_KEY)  # 手动解析，不安全
       return payload
   ```

**违反上述任何约束的代码将导致权限漏洞、数据泄露或审计失效！**

---

## 五、API接口规范

### 1. 统一响应结构
```json
{
  "success": true,
  "data": {...},
  "message": "操作成功",
  "code": "SUCCESS",
  "request_id": "uuid-string",
  "timestamp": "2025-11-11T10:30:00Z"
}
```

### 2. 错误响应结构
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "参数验证失败",
    "details": {
      "field": "email",
      "reason": "邮箱格式不正确"
    }
  },
  "request_id": "uuid-string",
  "timestamp": "2025-11-11T10:30:00Z"
}
```

---

### 3. 成功响应示例（12个核心模块）⚠️

> **AI约束**: 所有成功响应必须包含 `success: true`、`data`、`message`、`code`、`request_id`、`timestamp` 六个字段。

#### 3.1 用户管理模块
```json
// POST /api/v1/users - 创建用户
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "newuser",
    "role": "media_buyer",
    "is_active": true,
    "created_at": "2025-11-11T10:30:00Z"
  },
  "message": "用户创建成功",
  "code": "SUCCESS",
  "request_id": "req-123456",
  "timestamp": "2025-11-11T10:30:05Z"
}

// GET /api/v1/users/{id} - 获取用户详情
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "username": "testuser",
      "full_name": "测试用户",
      "role": "account_manager",
      "department": "运营部",
      "position": "项目经理",
      "is_active": true,
      "last_login_at": "2025-11-11T09:00:00Z"
    },
    "profile": {
      "timezone": "Asia/Shanghai",
      "language": "zh-CN",
      "preferences": {
        "theme": "dark",
        "notifications_enabled": true
      }
    }
  },
  "message": "获取成功",
  "code": "SUCCESS",
  "request_id": "req-123457",
  "timestamp": "2025-11-11T10:30:06Z"
}
```

#### 3.2 项目管理模块
```json
// POST /api/v1/projects - 创建项目
{
  "success": true,
  "data": {
    "project_id": "proj-001",
    "project_name": "Facebook广告项目A",
    "client_name": "甲方公司",
    "status": "active",
    "budget": 100000.00,
    "start_date": "2025-11-01",
    "end_date": "2025-12-31",
    "account_manager_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2025-11-11T10:30:00Z"
  },
  "message": "项目创建成功",
  "code": "SUCCESS",
  "request_id": "req-123458",
  "timestamp": "2025-11-11T10:30:07Z"
}

// GET /api/v1/projects?page=1&size=10 - 分页查询项目
{
  "success": true,
  "data": {
    "items": [
      {
        "project_id": "proj-001",
        "project_name": "Facebook广告项目A",
        "status": "active",
        "total_budget": 100000.00,
        "total_spend": 35000.00,
        "roi": 2.35
      }
    ],
    "pagination": {
      "page": 1,
      "size": 10,
      "total": 45,
      "pages": 5
    }
  },
  "message": "查询成功",
  "code": "SUCCESS",
  "request_id": "req-123459",
  "timestamp": "2025-11-11T10:30:08Z"
}
```

#### 3.3 广告账户模块
```json
// POST /api/v1/ad-accounts - 创建广告账户
{
  "success": true,
  "data": {
    "account_id": "acc-fb-001",
    "account_name": "FB账户001",
    "channel": "facebook",
    "status": "new",
    "assigned_user_id": null,
    "project_id": "proj-001",
    "created_at": "2025-11-11T10:30:00Z"
  },
  "message": "账户创建成功",
  "code": "SUCCESS",
  "request_id": "req-123460",
  "timestamp": "2025-11-11T10:30:09Z"
}

// PATCH /api/v1/ad-accounts/{id}/status - 更新账户状态
{
  "success": true,
  "data": {
    "account_id": "acc-fb-001",
    "old_status": "testing",
    "new_status": "active",
    "updated_at": "2025-11-11T10:30:00Z",
    "updated_by": "550e8400-e29b-41d4-a716-446655440000"
  },
  "message": "账户状态更新成功",
  "code": "SUCCESS",
  "request_id": "req-123461",
  "timestamp": "2025-11-11T10:30:10Z"
}
```

#### 3.4 日报管理模块
```json
// POST /api/v1/daily-reports - 提交日报
{
  "success": true,
  "data": {
    "report_id": "report-20251111-001",
    "ad_account_id": "acc-fb-001",
    "report_date": "2025-11-10",
    "spend": 1500.00,
    "conversions": 45,
    "status": "pending",
    "submitted_by": "550e8400-e29b-41d4-a716-446655440000",
    "submitted_at": "2025-11-11T10:30:00Z"
  },
  "message": "日报提交成功，等待审核",
  "code": "SUCCESS",
  "request_id": "req-123462",
  "timestamp": "2025-11-11T10:30:11Z"
}

// POST /api/v1/daily-reports/{id}/approve - 审核日报
{
  "success": true,
  "data": {
    "report_id": "report-20251111-001",
    "status": "approved",
    "approved_by": "550e8400-e29b-41d4-a716-446655440001",
    "approved_at": "2025-11-11T11:00:00Z",
    "original_conversions": 45,
    "confirmed_conversions": 43,
    "adjustment_reason": "实际核验后调整"
  },
  "message": "日报审核通过",
  "code": "SUCCESS",
  "request_id": "req-123463",
  "timestamp": "2025-11-11T11:00:05Z"
}
```

#### 3.5 充值管理模块
```json
// POST /api/v1/topups - 创建充值申请
{
  "success": true,
  "data": {
    "topup_id": "topup-20251111-001",
    "project_id": "proj-001",
    "ad_account_id": "acc-fb-001",
    "amount": 5000.00,
    "status": "draft",
    "applicant_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2025-11-11T10:30:00Z"
  },
  "message": "充值申请创建成功",
  "code": "SUCCESS",
  "request_id": "req-123464",
  "timestamp": "2025-11-11T10:30:12Z"
}

// POST /api/v1/topups/{id}/approve - 财务审批充值
{
  "success": true,
  "data": {
    "topup_id": "topup-20251111-001",
    "status": "approved",
    "approved_by": "550e8400-e29b-41d4-a716-446655440002",
    "approved_at": "2025-11-11T12:00:00Z",
    "approved_amount": 5000.00,
    "payment_due_date": "2025-11-12"
  },
  "message": "充值申请已批准",
  "code": "SUCCESS",
  "request_id": "req-123465",
  "timestamp": "2025-11-11T12:00:05Z"
}
```

#### 3.6 对账管理模块
```json
// POST /api/v1/reconciliation/run - 执行对账
{
  "success": true,
  "data": {
    "reconciliation_id": "recon-20251111-001",
    "project_id": "proj-001",
    "period_start": "2025-11-01",
    "period_end": "2025-11-10",
    "total_spend": 35000.00,
    "total_topup": 40000.00,
    "balance": 5000.00,
    "discrepancy": 0.00,
    "status": "completed",
    "created_at": "2025-11-11T10:30:00Z"
  },
  "message": "对账完成",
  "code": "SUCCESS",
  "request_id": "req-123466",
  "timestamp": "2025-11-11T10:30:13Z"
}

// GET /api/v1/reconciliation/{id}/details - 对账明细
{
  "success": true,
  "data": {
    "reconciliation_id": "recon-20251111-001",
    "summary": {
      "total_spend": 35000.00,
      "total_topup": 40000.00,
      "balance": 5000.00
    },
    "spend_details": [
      {
        "date": "2025-11-01",
        "account_id": "acc-fb-001",
        "spend": 1500.00,
        "conversions": 45
      }
    ],
    "topup_details": [
      {
        "date": "2025-11-01",
        "topup_id": "topup-001",
        "amount": 5000.00,
        "status": "paid"
      }
    ]
  },
  "message": "查询成功",
  "code": "SUCCESS",
  "request_id": "req-123467",
  "timestamp": "2025-11-11T10:30:14Z"
}
```

#### 3.7 渠道管理模块
```json
// GET /api/v1/channels - 获取渠道列表
{
  "success": true,
  "data": {
    "channels": [
      {
        "channel_id": "facebook",
        "channel_name": "Facebook",
        "is_active": true,
        "account_count": 45,
        "total_spend": 125000.00
      },
      {
        "channel_id": "google",
        "channel_name": "Google Ads",
        "is_active": true,
        "account_count": 23,
        "total_spend": 87000.00
      }
    ]
  },
  "message": "查询成功",
  "code": "SUCCESS",
  "request_id": "req-123468",
  "timestamp": "2025-11-11T10:30:15Z"
}
```

#### 3.8 审计日志模块
```json
// GET /api/v1/audit-logs?entity_type=project&entity_id=proj-001
{
  "success": true,
  "data": {
    "logs": [
      {
        "log_id": "log-001",
        "entity_type": "project",
        "entity_id": "proj-001",
        "action": "update",
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_name": "张三",
        "changes": {
          "budget": {
            "old": 80000.00,
            "new": 100000.00
          }
        },
        "ip_address": "192.168.1.100",
        "created_at": "2025-11-11T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 156
    }
  },
  "message": "查询成功",
  "code": "SUCCESS",
  "request_id": "req-123469",
  "timestamp": "2025-11-11T10:30:16Z"
}
```

#### 3.9 分账管理模块
```json
// GET /api/v1/ledger/balance?project_id=proj-001
{
  "success": true,
  "data": {
    "project_id": "proj-001",
    "current_balance": 5000.00,
    "total_income": 40000.00,
    "total_expense": 35000.00,
    "last_transaction_at": "2025-11-11T10:00:00Z",
    "ledger_entries": [
      {
        "entry_id": "ledger-001",
        "transaction_type": "topup",
        "amount": 5000.00,
        "balance_after": 10000.00,
        "created_at": "2025-11-11T09:00:00Z"
      }
    ]
  },
  "message": "查询成功",
  "code": "SUCCESS",
  "request_id": "req-123470",
  "timestamp": "2025-11-11T10:30:17Z"
}
```

#### 3.10 AI监控模块
```json
// GET /api/v1/ai/anomalies?account_id=acc-fb-001
{
  "success": true,
  "data": {
    "anomalies": [
      {
        "anomaly_id": "anom-001",
        "account_id": "acc-fb-001",
        "anomaly_type": "spend_spike",
        "severity": "high",
        "description": "消耗突增200%",
        "detected_at": "2025-11-11T10:00:00Z",
        "metrics": {
          "baseline": 1500.00,
          "current": 4500.00,
          "deviation": 200.0
        }
      }
    ]
  },
  "message": "查询成功",
  "code": "SUCCESS",
  "request_id": "req-123471",
  "timestamp": "2025-11-11T10:30:18Z"
}

// POST /api/v1/ai/predict-lifetime
{
  "success": true,
  "data": {
    "account_id": "acc-fb-001",
    "predicted_lifetime_days": 45,
    "confidence": 0.85,
    "factors": {
      "avg_daily_spend": 1500.00,
      "spend_trend": "stable",
      "historical_pattern": "normal"
    },
    "recommendation": "账户运行稳定，建议持续监控"
  },
  "message": "预测完成",
  "code": "SUCCESS",
  "request_id": "req-123472",
  "timestamp": "2025-11-11T10:30:19Z"
}
```

#### 3.11 数据导入模块
```json
// POST /api/v1/import/daily-reports - 批量导入日报
{
  "success": true,
  "data": {
    "job_id": "import-20251111-001",
    "status": "processing",
    "total_rows": 150,
    "processed_rows": 0,
    "success_count": 0,
    "error_count": 0,
    "started_at": "2025-11-11T10:30:00Z"
  },
  "message": "导入任务已创建，正在处理",
  "code": "SUCCESS",
  "request_id": "req-123473",
  "timestamp": "2025-11-11T10:30:20Z"
}

// GET /api/v1/import/jobs/{job_id}/status - 查询导入状态
{
  "success": true,
  "data": {
    "job_id": "import-20251111-001",
    "status": "completed",
    "total_rows": 150,
    "processed_rows": 150,
    "success_count": 145,
    "error_count": 5,
    "errors": [
      {
        "row": 23,
        "error": "广告账户不存在",
        "data": {"account_id": "acc-invalid-001"}
      }
    ],
    "started_at": "2025-11-11T10:30:00Z",
    "completed_at": "2025-11-11T10:32:00Z"
  },
  "message": "导入完成",
  "code": "SUCCESS",
  "request_id": "req-123474",
  "timestamp": "2025-11-11T10:32:05Z"
}
```

#### 3.12 统计分析模块
```json
// GET /api/v1/analytics/dashboard?project_id=proj-001
{
  "success": true,
  "data": {
    "project_id": "proj-001",
    "period": {
      "start": "2025-11-01",
      "end": "2025-11-11"
    },
    "summary": {
      "total_spend": 35000.00,
      "total_conversions": 1250,
      "avg_cpa": 28.00,
      "roi": 2.35,
      "active_accounts": 8,
      "active_campaigns": 23
    },
    "trends": {
      "spend_trend": [
        {"date": "2025-11-01", "spend": 1500.00},
        {"date": "2025-11-02", "spend": 1800.00}
      ],
      "conversion_trend": [
        {"date": "2025-11-01", "conversions": 45},
        {"date": "2025-11-02", "conversions": 52}
      ]
    }
  },
  "message": "查询成功",
  "code": "SUCCESS",
  "request_id": "req-123475",
  "timestamp": "2025-11-11T10:30:21Z"
}
```

---

### 4. 错误响应示例（5个错误类别）⚠️

> **AI约束**: 所有错误响应必须使用 `core/error_codes.py` 中定义的错误码，禁止硬编码错误信息。

#### 4.1 认证错误（AUTH_xxx）
```json
// 登录失败 - AUTH_001
{
  "success": false,
  "error": {
    "code": "AUTH_001",
    "message": "用户名或密码错误",
    "details": null
  },
  "request_id": "req-error-001",
  "timestamp": "2025-11-11T10:30:00Z"
}

// 邮箱已存在 - AUTH_100
{
  "success": false,
  "error": {
    "code": "AUTH_100",
    "message": "该邮箱已被注册",
    "details": {
      "email": "user@example.com"
    }
  },
  "request_id": "req-error-002",
  "timestamp": "2025-11-11T10:30:01Z"
}

// Token过期 - AUTH_003
{
  "success": false,
  "error": {
    "code": "AUTH_003",
    "message": "登录已过期，请重新登录",
    "details": {
      "expired_at": "2025-11-11T09:00:00Z"
    }
  },
  "request_id": "req-error-003",
  "timestamp": "2025-11-11T10:30:02Z"
}

// 权限不足 - AUTH_005
{
  "success": false,
  "error": {
    "code": "AUTH_005",
    "message": "权限不足，无法执行该操作",
    "details": {
      "required_role": "admin",
      "current_role": "media_buyer",
      "action": "delete_user"
    }
  },
  "request_id": "req-error-004",
  "timestamp": "2025-11-11T10:30:03Z"
}
```

#### 4.2 业务逻辑错误（BIZ_xxx）
```json
// 状态转换不允许 - BIZ_001
{
  "success": false,
  "error": {
    "code": "BIZ_001",
    "message": "不允许从approved状态转换到draft状态",
    "details": {
      "entity_type": "daily_report",
      "entity_id": "report-001",
      "current_status": "approved",
      "target_status": "draft",
      "allowed_transitions": ["approved"]
    }
  },
  "request_id": "req-error-005",
  "timestamp": "2025-11-11T10:30:04Z"
}

// 预算超限 - BIZ_002
{
  "success": false,
  "error": {
    "code": "BIZ_002",
    "message": "充值金额超出项目剩余预算",
    "details": {
      "project_id": "proj-001",
      "requested_amount": 50000.00,
      "remaining_budget": 20000.00,
      "total_budget": 100000.00,
      "spent": 80000.00
    }
  },
  "request_id": "req-error-006",
  "timestamp": "2025-11-11T10:30:05Z"
}

// 重复提交 - BIZ_003
{
  "success": false,
  "error": {
    "code": "BIZ_003",
    "message": "该日期的日报已存在",
    "details": {
      "account_id": "acc-fb-001",
      "report_date": "2025-11-10",
      "existing_report_id": "report-20251110-001"
    }
  },
  "request_id": "req-error-007",
  "timestamp": "2025-11-11T10:30:06Z"
}
```

#### 4.3 系统错误（SYS_xxx）
```json
// 内部服务器错误 - SYS_001
{
  "success": false,
  "error": {
    "code": "SYS_001",
    "message": "服务器内部错误，请稍后重试",
    "details": null
  },
  "request_id": "req-error-008",
  "timestamp": "2025-11-11T10:30:07Z"
}

// 外部服务不可用 - SYS_002
{
  "success": false,
  "error": {
    "code": "SYS_002",
    "message": "外部服务暂时不可用",
    "details": {
      "service": "Supabase Auth",
      "retry_after": 60
    }
  },
  "request_id": "req-error-009",
  "timestamp": "2025-11-11T10:30:08Z"
}

// 速率限制 - SYS_003
{
  "success": false,
  "error": {
    "code": "SYS_003",
    "message": "请求过于频繁，请稍后再试",
    "details": {
      "limit": 100,
      "window": "1 minute",
      "retry_after": 30
    }
  },
  "request_id": "req-error-010",
  "timestamp": "2025-11-11T10:30:09Z"
}
```

#### 4.4 数据库错误（DB_xxx）
```json
// 记录不存在 - DB_001
{
  "success": false,
  "error": {
    "code": "DB_001",
    "message": "项目不存在",
    "details": {
      "entity_type": "project",
      "entity_id": "proj-999"
    }
  },
  "request_id": "req-error-011",
  "timestamp": "2025-11-11T10:30:10Z"
}

// 外键约束违反 - DB_002
{
  "success": false,
  "error": {
    "code": "DB_002",
    "message": "无法删除，存在关联记录",
    "details": {
      "entity_type": "project",
      "entity_id": "proj-001",
      "constraint": "有5个广告账户关联到此项目"
    }
  },
  "request_id": "req-error-012",
  "timestamp": "2025-11-11T10:30:11Z"
}

// 唯一约束违反 - DB_003
{
  "success": false,
  "error": {
    "code": "DB_003",
    "message": "记录已存在",
    "details": {
      "entity_type": "ad_account",
      "field": "account_name",
      "value": "FB账户001"
    }
  },
  "request_id": "req-error-013",
  "timestamp": "2025-11-11T10:30:12Z"
}
```

#### 4.5 参数验证错误（VALIDATION_xxx）
```json
// 必填字段缺失 - VALIDATION_001
{
  "success": false,
  "error": {
    "code": "VALIDATION_001",
    "message": "参数验证失败",
    "details": {
      "field": "project_id",
      "error": "该字段为必填项"
    }
  },
  "request_id": "req-error-014",
  "timestamp": "2025-11-11T10:30:13Z"
}

// 数据格式错误 - VALIDATION_002
{
  "success": false,
  "error": {
    "code": "VALIDATION_002",
    "message": "邮箱格式不正确",
    "details": {
      "field": "email",
      "value": "invalid-email",
      "expected": "有效的邮箱格式 (example@domain.com)"
    }
  },
  "request_id": "req-error-015",
  "timestamp": "2025-11-11T10:30:14Z"
}

// 数值范围错误 - VALIDATION_003
{
  "success": false,
  "error": {
    "code": "VALIDATION_003",
    "message": "金额必须大于0",
    "details": {
      "field": "amount",
      "value": -100,
      "min": 0.01,
      "max": 1000000
    }
  },
  "request_id": "req-error-016",
  "timestamp": "2025-11-11T10:30:15Z"
}

// 多字段验证错误
{
  "success": false,
  "error": {
    "code": "VALIDATION_001",
    "message": "多个字段验证失败",
    "details": [
      {
        "field": "email",
        "error": "邮箱格式不正确"
      },
      {
        "field": "password",
        "error": "密码长度必须至少8个字符"
      },
      {
        "field": "amount",
        "error": "金额必须大于0"
      }
    ]
  },
  "request_id": "req-error-017",
  "timestamp": "2025-11-11T10:30:16Z"
}
```

---

### 5. AI代码生成约束 ⚠️

#### 约束1: 必须使用统一响应函数
```python
# ✅ 正确：使用utils.response中的标准函数
from utils.response import success_response, error_response
from core.error_codes import AuthErrorCodes, BusinessErrorCodes

# 成功响应
return success_response(
    data={"user_id": user.id, "email": user.email},
    message="用户创建成功"
)

# 错误响应
return error_response(
    code=AuthErrorCodes.EMAIL_ALREADY_EXISTS.code,
    message=AuthErrorCodes.EMAIL_ALREADY_EXISTS.message,
    status_code=AuthErrorCodes.EMAIL_ALREADY_EXISTS.status_code
)

# ❌ 错误：手动构造响应
return {
    "success": True,
    "data": user,
    "message": "成功"  # 缺少code、request_id、timestamp
}

# ❌ 错误：硬编码错误信息
return error_response(
    code="EMAIL_EXISTS",  # 应使用错误码类
    message="邮箱已存在",
    status_code=400
)
```

#### 约束2: request_id和timestamp自动生成
```python
# ✅ 正确：success_response和error_response会自动添加
from utils.response import success_response

return success_response(
    data=data,
    message="操作成功"
    # request_id和timestamp会自动生成
)

# ❌ 错误：手动添加这些字段
return {
    "success": True,
    "data": data,
    "request_id": str(uuid.uuid4()),  # 不需要手动添加
    "timestamp": datetime.utcnow().isoformat()
}
```

#### 约束3: 分页响应格式
```python
# ✅ 正确：分页响应使用标准格式
from schemas.response import PaginatedResponse

return success_response(
    data={
        "items": items,
        "pagination": {
            "page": page,
            "size": size,
            "total": total,
            "pages": (total + size - 1) // size
        }
    }
)

# ❌ 错误：非标准分页格式
return {
    "data": items,
    "page": page,
    "total": total  # 缺少success、message等字段
}
```

#### 约束4: 错误详情结构化
```python
# ✅ 正确：结构化的错误详情
return error_response(
    code=BusinessErrorCodes.STATUS_TRANSITION_NOT_ALLOWED.code,
    message=f"不允许从{current_status}转换到{target_status}",
    details={
        "entity_type": "daily_report",
        "entity_id": report_id,
        "current_status": current_status,
        "target_status": target_status,
        "allowed_transitions": STATE_TRANSITIONS.get(current_status, [])
    },
    status_code=400
)

# ❌ 错误：缺少详细信息
return error_response(
    code="ERROR",
    message="状态转换失败",  # 信息不够详细
    status_code=400
)
```

#### 约束5: 异常处理标准模式
```python
# ✅ 正确：完整的异常处理
from core.error_codes import AuthErrorCodes, BusinessErrorCodes, SystemErrorCodes
from utils.response import error_response
import structlog

logger = structlog.get_logger(__name__)

try:
    # 业务逻辑
    result = await service.create_user(data)
    return success_response(data=result, message="创建成功")

except HTTPException as e:
    # FastAPI HTTPException - 直接返回
    return error_response(
        code=getattr(e, 'error_code', 'HTTP_ERROR'),
        message=e.detail,
        status_code=e.status_code
    )

except ValidationError as e:
    # Pydantic验证错误
    return error_response(
        code="VALIDATION_001",
        message="参数验证失败",
        details=e.errors(),
        status_code=422
    )

except Exception as e:
    # 未预期错误
    logger.error("unexpected_error", error=str(e), exc_info=True)
    return error_response(
        code=SystemErrorCodes.INTERNAL_ERROR.code,
        message="服务器内部错误",
        status_code=500
    )

# ❌ 错误：泛化异常处理
except Exception as e:
    return {"error": str(e)}  # 格式不统一，缺少错误码
```

---

### 6. 接口实现示例

#### 新建充值申请
```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

# Pydantic模型
class TopupCreate(BaseModel):
    project_id: str
    ad_account_id: str
    amount: float
    notes: str = None

    class Config:
        from_attributes = True

# API路由
@router.post('/api/topups/request')
async def create_topup(
    req: TopupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建充值申请"""
    try:
        # 验证权限
        account = db.query(AdAccount).filter(
            AdAccount.id == req.ad_account_id,
            AdAccount.project_id == req.project_id,
            AdAccount.assigned_user_id == current_user.id
        ).first()

        if not account:
            raise HTTPException(status_code=403, detail="无权限操作该账户")

        # 创建充值申请
        topup = RechargeRequest(
            project_id=req.project_id,
            ad_account_id=req.ad_account_id,
            user_id=current_user.id,
            amount=req.amount,
            notes=req.notes,
            status='draft'
        )

        db.add(topup)
        db.commit()
        db.refresh(topup)

        # 记录操作日志
        await log_action('topup', 'create', current_user.id, topup.id)

        return {
            "success": True,
            "data": topup,
            "message": "充值申请提交成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="内部服务器错误")
```

#### 对账接口
```python
@router.post('/api/reconciliation/run')
async def run_reconciliation(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """执行对账"""
    try:
        # 验证权限（财务或管理员）
        if current_user.role not in ['finance', 'admin']:
            raise HTTPException(status_code=403, detail="权限不足")

        # 获取项目数据
        spend_records = db.query(DailyReport).filter(
            DailyReport.project_id == project_id,
            DailyReport.status == 'approved'
        ).all()

        # 获取充值记录
        topup_records = db.query(RechargeRequest).filter(
            RechargeRequest.project_id == project_id,
            RechargeRequest.status == 'posted'
        ).all()

        # 计算差异
        total_spend = sum(record.spend for record in spend_records)
        total_topup = sum(record.amount for record in topup_records)
        difference = total_topup - total_spend

        # 创建对账记录
        reconciliation = Reconciliation(
            project_id=project_id,
            total_spend=total_spend,
            total_topup=total_topup,
            difference=difference,
            created_by=current_user.id
        )

        db.add(reconciliation)
        db.commit()
        db.refresh(reconciliation)

        return {
            "success": True,
            "data": {
                "reconciliation_id": reconciliation.id,
                "project_id": project_id,
                "total_spend": float(total_spend),
                "total_topup": float(total_topup),
                "difference": float(difference)
            },
            "message": "对账完成"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="对账失败")
```

### ⚠️ AI代码生成约束提示

**当AI生成API接口代码时，必须遵守以下约束：**

1. **必须使用统一响应格式**
   ```python
   from utils.response import success_response, error_response
   from core.error_codes import AuthErrorCodes, BusinessErrorCodes

   # ✅ 正确：成功响应（包含所有必需字段）
   @router.post("/projects")
   async def create_project(project: ProjectCreate):
       new_project = create_project_logic(project)
       return success_response(
           data={"project": new_project},
           message="项目创建成功",
           status_code=201
       )

   # ❌ 错误：直接返回字典（缺少必需字段）
   @router.post("/projects")
   async def create_project(project: ProjectCreate):
       new_project = create_project_logic(project)
       return {"project": new_project}  # 缺少success、code、request_id等字段
   ```

2. **必须使用预定义错误码**
   ```python
   # ✅ 正确：使用错误码枚举
   from core.error_codes import AuthErrorCodes

   return error_response(
       code=AuthErrorCodes.EMAIL_ALREADY_EXISTS.code,
       message="邮箱已被注册",
       status_code=400
   )

   # ❌ 错误：硬编码错误码或直接抛异常
   raise HTTPException(status_code=400, detail="邮箱已存在")  # 缺少错误码和request_id
   return {"error": "EMAIL_EXISTS"}  # 不符合统一格式
   ```

3. **路由必须遵循RESTful约定**
   ```python
   # ✅ 正确：RESTful路由设计
   @router.get("/projects")          # 列表
   @router.post("/projects")         # 创建
   @router.get("/projects/{id}")     # 详情
   @router.put("/projects/{id}")     # 更新
   @router.delete("/projects/{id}")  # 删除

   # ❌ 错误：非RESTful路由
   @router.get("/get-all-projects")      # 使用动词
   @router.post("/create-new-project")   # 使用动词
   @router.get("/projects/detail/{id}")  # 冗余路径
   ```

4. **请求体和响应必须使用Pydantic模型**
   ```python
   from pydantic import BaseModel, Field

   # ✅ 正确：使用Pydantic模型
   class ProjectCreate(BaseModel):
       name: str = Field(..., min_length=1, max_length=200)
       budget: Decimal = Field(..., gt=0)
       client_name: str

   @router.post("/projects")
   async def create_project(project: ProjectCreate):
       # FastAPI自动验证请求体
       return success_response(data={"project": project.dict()})

   # ❌ 错误：使用原始字典
   @router.post("/projects")
   async def create_project(project: dict):
       # 缺少类型验证
       name = project.get("name")  # 可能为None或错误类型
   ```

5. **分页查询必须使用统一参数**
   ```python
   from schemas.response import PaginatedResponse

   # ✅ 正确：统一分页参数
   @router.get("/projects")
   async def get_projects(
       page: int = Query(1, ge=1),
       size: int = Query(20, ge=1, le=100),
       db: Session = Depends(get_db)
   ):
       total = db.query(Project).count()
       projects = db.query(Project).offset((page-1)*size).limit(size).all()

       return success_response(
           data={
               "items": projects,
               "total": total,
               "page": page,
               "size": size,
               "pages": (total + size - 1) // size
           }
       )

   # ❌ 错误：非统一分页参数
   @router.get("/projects")
   async def get_projects(
       offset: int = 0,  # 应使用page
       limit: int = 50   # 应使用size
   ):
       pass
   ```

6. **异常处理必须统一**
   ```python
   # ✅ 正确：统一异常处理
   from exceptions import ValidationError, AuthenticationError

   try:
       validate_project_data(project)
   except ValidationError as e:
       return error_response(
           code=e.error_code,
           message=str(e),
           status_code=400
       )
   except Exception as e:
       logger.error(f"创建项目失败: {e}")
       return error_response(
           code=BusinessErrorCodes.OPERATION_FAILED.code,
           message="操作失败，请稍后重试",
           status_code=500
       )

   # ❌ 错误：直接抛异常或不处理
   validate_project_data(project)  # 异常会导致500错误，缺少错误码
   ```

7. **必须包含请求日志和审计**
   ```python
   from core.logging import log_requests

   # ✅ 正确：使用日志装饰器
   @router.post("/projects")
   @log_requests("project")
   @require_role(["admin", "account_manager"])
   async def create_project(
       project: ProjectCreate,
       current_user: AuthenticatedUser = Depends(get_current_user)
   ):
       # 自动记录请求日志和审计信息
       pass

   # ❌ 错误：无日志记录
   @router.post("/projects")
   async def create_project(project: ProjectCreate):
       # 缺少日志，无法追踪问题
       pass
   ```

**违反上述任何约束的代码将导致API不一致、难以调试或安全问题！**

---

## 六、错误码定义（50+统一错误码）⚠️

> **重要**: 本项目定义了50+个标准错误码，AI生成代码时**必须使用**`core/error_codes.py`中的预定义错误码，**禁止硬编码字符串**。

### 1. 错误码结构和命名规则

**命名规则**:
```python
# 错误码格式: <分类>_<编号>
# 分类前缀:
- AUTH_xxx      # 认证/授权错误
- BIZ_xxx       # 业务逻辑错误
- SYS_xxx       # 系统错误
- DB_xxx        # 数据库错误
- VALIDATION_xxx # 参数验证错误

# 编号规则: 三位数字，按功能模块分组
# 示例:
AUTH_001  # 认证-登录错误第1个
AUTH_100  # 认证-注册错误第1个
AUTH_200  # 认证-密码错误第1个
```

**错误码基类**:
```python
# backend/core/error_codes.py
class ErrorCode:
    """错误码基类"""
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code           # 错误码字符串，如 "AUTH_001"
        self.message = message     # 错误描述，如 "用户名或密码错误"
        self.status_code = status_code  # HTTP状态码，如 401

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "status_code": self.status_code
        }
```

---

### 2. 认证错误码（AuthErrorCodes）⚠️

**总计26个认证错误码**，按功能分为7组：

#### 2.1 登录相关 (AUTH_001 - AUTH_099)

| 错误码 | 属性名 | 错误信息 | HTTP状态码 | 使用场景 |
|--------|--------|----------|------------|----------|
| AUTH_001 | INVALID_CREDENTIALS | 用户名或密码错误 | 401 | 登录凭据验证失败 |
| AUTH_002 | ACCOUNT_DISABLED | 账户已被禁用 | 403 | 用户账户被管理员停用 |
| AUTH_003 | TOKEN_REVOKED | 令牌已被撤销 | 401 | 用户主动登出或管理员撤销 |
| AUTH_004 | USER_NOT_FOUND | 用户不存在或已被禁用 | 404 | 查询用户不存在 |
| AUTH_005 | TOKEN_REFRESH_FAILED | 令牌刷新失败 | 401 | Refresh Token无效或过期 |

#### 2.2 注册相关 (AUTH_100 - AUTH_199)

| 错误码 | 属性名 | 错误信息 | HTTP状态码 | 使用场景 |
|--------|--------|----------|------------|----------|
| AUTH_100 | EMAIL_ALREADY_EXISTS | 邮箱已被注册 | 400 | 注册时邮箱重复 |
| AUTH_101 | USERNAME_ALREADY_EXISTS | 用户名已被使用 | 400 | 注册时用户名重复 |
| AUTH_102 | REGISTER_FAILED | 注册失败，请稍后重试 | 500 | Supabase注册失败 |

#### 2.3 密码相关 (AUTH_200 - AUTH_299)

| 错误码 | 属性名 | 错误信息 | HTTP状态码 | 使用场景 |
|--------|--------|----------|------------|----------|
| AUTH_200 | PASSWORD_TOO_SHORT | 密码长度至少8位 | 400 | 密码长度不足 |
| AUTH_201 | PASSWORD_MISSING_DIGIT | 密码必须包含至少一个数字 | 400 | 密码缺少数字 |
| AUTH_202 | PASSWORD_MISSING_LETTER | 密码必须包含至少一个字母 | 400 | 密码缺少字母 |
| AUTH_203 | PASSWORD_MISSING_SPECIAL | 密码必须包含至少一个特殊字符 | 400 | 密码缺少特殊字符 |
| AUTH_204 | OLD_PASSWORD_WRONG | 旧密码错误 | 400 | 修改密码时旧密码验证失败 |
| AUTH_205 | RESET_TOKEN_INVALID | 重置令牌无效或已过期 | 400 | 密码重置令牌失效 |
| AUTH_206 | PASSWORD_CHANGE_FAILED | 密码修改失败 | 500 | Supabase密码修改失败 |

#### 2.4 邮箱验证 (AUTH_300 - AUTH_399)

| 错误码 | 属性名 | 错误信息 | HTTP状态码 | 使用场景 |
|--------|--------|----------|------------|----------|
| AUTH_300 | EMAIL_NOT_VERIFIED | 邮箱未验证 | 403 | 需要邮箱验证的操作 |
| AUTH_301 | EMAIL_VERIFICATION_FAILED | 邮箱验证失败 | 400 | 验证令牌无效 |
| AUTH_302 | EMAIL_ALREADY_VERIFIED | 邮箱已验证 | 400 | 重复验证 |

#### 2.5 Token相关 (AUTH_400 - AUTH_499)

| 错误码 | 属性名 | 错误信息 | HTTP状态码 | 使用场景 |
|--------|--------|----------|------------|----------|
| AUTH_400 | TOKEN_MISSING | 未提供认证令牌 | 401 | 请求头缺少Authorization |
| AUTH_401 | TOKEN_INVALID | 无效的认证令牌 | 401 | JWT格式错误或签名验证失败 |
| AUTH_402 | TOKEN_EXPIRED | 令牌已过期 | 401 | JWT过期时间已过 |

#### 2.6 权限相关 (AUTH_500 - AUTH_599)

| 错误码 | 属性名 | 错误信息 | HTTP状态码 | 使用场景 |
|--------|--------|----------|------------|----------|
| AUTH_500 | PERMISSION_DENIED | 权限不足 | 403 | 用户无权限执行操作 |
| AUTH_501 | ROLE_NOT_ALLOWED | 角色权限不足 | 403 | 角色不在允许列表中 |

#### 2.7 通用认证错误 (AUTH_900 - AUTH_999)

| 错误码 | 属性名 | 错误信息 | HTTP状态码 | 使用场景 |
|--------|--------|----------|------------|----------|
| AUTH_900 | LOGIN_FAILED | 登录失败，请稍后重试 | 500 | 登录过程未知错误 |
| AUTH_901 | LOGOUT_FAILED | 登出失败 | 500 | 登出过程错误 |
| AUTH_999 | AUTHENTICATION_ERROR | 认证失败 | 401 | 通用认证错误 |

---

### 3. 业务错误码（BusinessErrorCodes）

**总计9个业务错误码**，按功能分为4组：

#### 3.1 通用业务错误 (BIZ_001 - BIZ_099)

| 错误码 | 属性名 | 错误信息 | HTTP状态码 | 使用场景 |
|--------|--------|----------|------------|----------|
| BIZ_001 | INVALID_OPERATION | 无效的操作 | 400 | 业务逻辑不允许的操作 |
| BIZ_002 | RESOURCE_NOT_FOUND | 资源不存在 | 404 | 查询的资源不存在 |
| BIZ_003 | RESOURCE_ALREADY_EXISTS | 资源已存在 | 409 | 创建时资源冲突 |

#### 3.2 金额相关 (BIZ_100 - BIZ_199)

| 错误码 | 属性名 | 错误信息 | HTTP状态码 | 使用场景 |
|--------|--------|----------|------------|----------|
| BIZ_100 | INVALID_AMOUNT | 金额无效 | 400 | 金额为负数或格式错误 |
| BIZ_101 | INSUFFICIENT_BALANCE | 余额不足 | 400 | 账户余额不足以支付 |

#### 3.3 日期相关 (BIZ_200 - BIZ_299)

| 错误码 | 属性名 | 错误信息 | HTTP状态码 | 使用场景 |
|--------|--------|----------|------------|----------|
| BIZ_200 | INVALID_DATE_RANGE | 日期范围无效 | 400 | 开始日期晚于结束日期 |
| BIZ_201 | DATE_IN_FUTURE | 日期不能为未来 | 400 | 日报日期为未来日期 |

#### 3.4 状态相关 (BIZ_300 - BIZ_399)

| 错误码 | 属性名 | 错误信息 | HTTP状态码 | 使用场景 |
|--------|--------|----------|------------|----------|
| BIZ_300 | INVALID_STATUS | 状态无效 | 400 | 状态值不在允许范围内 |
| BIZ_301 | STATUS_TRANSITION_NOT_ALLOWED | 状态转换不允许 | 400 | 状态机不允许的转换 |

---

### 4. 系统错误码（SystemErrorCodes）

**总计4个系统错误码**：

| 错误码 | 属性名 | 错误信息 | HTTP状态码 | 使用场景 |
|--------|--------|----------|------------|----------|
| SYS_001 | INTERNAL_ERROR | 系统内部错误 | 500 | 未捕获的异常 |
| SYS_002 | SERVICE_UNAVAILABLE | 服务暂时不可用 | 503 | 依赖服务不可用 |
| SYS_003 | TIMEOUT | 请求超时 | 504 | 请求处理超时 |
| SYS_004 | RATE_LIMIT_EXCEEDED | 请求过于频繁 | 429 | API限流触发 |

---

### 5. 数据库错误码（DatabaseErrorCodes）

**总计5个数据库错误码**：

| 错误码 | 属性名 | 错误信息 | HTTP状态码 | 使用场景 |
|--------|--------|----------|------------|----------|
| DB_001 | CONNECTION_FAILED | 数据库连接失败 | 500 | 数据库连接池耗尽 |
| DB_002 | QUERY_FAILED | 数据库查询失败 | 500 | SQL执行错误 |
| DB_003 | CONSTRAINT_VIOLATION | 数据完整性约束违反 | 400 | 违反CHECK约束 |
| DB_004 | UNIQUE_VIOLATION | 唯一性约束违反 | 409 | 违反UNIQUE约束 |
| DB_005 | FOREIGN_KEY_VIOLATION | 外键约束违反 | 400 | 违反FOREIGN KEY约束 |

---

### 6. 参数验证错误码（ValidationErrorCodes）

**总计6个验证错误码**：

| 错误码 | 属性名 | 错误信息 | HTTP状态码 | 使用场景 |
|--------|--------|----------|------------|----------|
| VALIDATION_001 | REQUIRED_FIELD_MISSING | 必填字段缺失 | 400 | Pydantic验证缺少必填字段 |
| VALIDATION_002 | INVALID_FORMAT | 格式无效 | 400 | 字段格式不符合要求 |
| VALIDATION_003 | INVALID_EMAIL | 邮箱格式无效 | 400 | 邮箱格式验证失败 |
| VALIDATION_004 | INVALID_PHONE | 电话格式无效 | 400 | 电话格式验证失败 |
| VALIDATION_005 | VALUE_OUT_OF_RANGE | 值超出范围 | 400 | 数值超出min/max限制 |
| VALIDATION_006 | INVALID_ENUM_VALUE | 枚举值无效 | 400 | 值不在枚举定义中 |

---

### 7. AI代码生成规范 ⚠️

**规则1: 必须从error_codes.py导入**

```python
# ✅ 正确：导入错误码类
from core.error_codes import (
    AuthErrorCodes,
    BusinessErrorCodes,
    SystemErrorCodes,
    DatabaseErrorCodes,
    ValidationErrorCodes
)

# ❌ 错误：不导入直接使用字符串
return error_response(
    code="AUTH_001",  # 硬编码！
    message="用户名或密码错误",
    status_code=401
)
```

**规则2: 使用ErrorCode对象的属性**

```python
# ✅ 正确：使用错误码对象的所有属性
from core.error_codes import AuthErrorCodes

return error_response(
    code=AuthErrorCodes.EMAIL_ALREADY_EXISTS.code,        # "AUTH_100"
    message=AuthErrorCodes.EMAIL_ALREADY_EXISTS.message,  # "邮箱已被注册"
    status_code=AuthErrorCodes.EMAIL_ALREADY_EXISTS.status_code  # 400
)

# ❌ 错误：混用硬编码
return error_response(
    code=AuthErrorCodes.EMAIL_ALREADY_EXISTS.code,  # 正确
    message="邮箱已存在",  # 错误！应该用.message
    status_code=400  # 错误！应该用.status_code
)
```

**规则3: 异常处理中使用错误码**

```python
# ✅ 正确：在异常处理中使用错误码
from core.error_codes import AuthErrorCodes, BusinessErrorCodes
from fastapi import HTTPException

try:
    # 业务逻辑
    if duplicate_email:
        raise HTTPException(
            status_code=AuthErrorCodes.EMAIL_ALREADY_EXISTS.status_code,
            detail=AuthErrorCodes.EMAIL_ALREADY_EXISTS.message
        )
except Exception as e:
    # 统一错误响应
    return error_response(
        code=SystemErrorCodes.INTERNAL_ERROR.code,
        message=str(e),
        status_code=SystemErrorCodes.INTERNAL_ERROR.status_code
    )
```

**规则4: 状态转换错误使用BIZ_301**

```python
# ✅ 正确：状态机转换错误
from core.error_codes import BusinessErrorCodes

if not is_valid_transition(current_status, new_status):
    return error_response(
        code=BusinessErrorCodes.STATUS_TRANSITION_NOT_ALLOWED.code,
        message=f"不能从{current_status}转换到{new_status}",
        status_code=BusinessErrorCodes.STATUS_TRANSITION_NOT_ALLOWED.status_code
    )

# ❌ 错误：自定义状态错误码
return error_response(
    code="INVALID_STATUS_CHANGE",  # 不存在的错误码！
    message="状态转换失败",
    status_code=400
)
```

---

### 8. 错误响应格式规范

**标准错误响应**:
```json
{
  "success": false,
  "error": {
    "code": "AUTH_100",
    "message": "邮箱已被注册"
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-11-16T08:30:00Z"
}
```

**带详细信息的错误响应**:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_001",
    "message": "必填字段缺失",
    "details": {
      "field": "email",
      "reason": "邮箱字段不能为空"
    }
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-11-16T08:30:00Z"
}
```

**错误响应生成函数**:
```python
# backend/utils/response.py
from typing import Any, Dict, Optional
from core.error_codes import ErrorCode

def error_response(
    code: str,
    message: str,
    status_code: int = 400,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """生成标准错误响应"""
    error_data = {
        "code": code,
        "message": message
    }
    if details:
        error_data["details"] = details

    return {
        "success": False,
        "error": error_data,
        "request_id": generate_request_id(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
```

---

### 9. 常见错误码使用场景

**场景1: 用户注册**
```python
# 邮箱重复 → AUTH_100
# 用户名重复 → AUTH_101
# 密码太短 → AUTH_200
# 密码缺数字 → AUTH_201
# 注册失败 → AUTH_102

if existing_user:
    return error_response(
        code=AuthErrorCodes.EMAIL_ALREADY_EXISTS.code,
        message=AuthErrorCodes.EMAIL_ALREADY_EXISTS.message,
        status_code=AuthErrorCodes.EMAIL_ALREADY_EXISTS.status_code
    )
```

**场景2: 用户登录**
```python
# 密码错误 → AUTH_001
# 账户禁用 → AUTH_002
# Token过期 → AUTH_402
# 权限不足 → AUTH_500

if not await supabase_auth_service.verify_user(email, password):  # 使用Supabase验证
    return error_response(
        code=AuthErrorCodes.INVALID_CREDENTIALS.code,
        message=AuthErrorCodes.INVALID_CREDENTIALS.message,
        status_code=AuthErrorCodes.INVALID_CREDENTIALS.status_code
    )
```

**场景3: 状态转换**
```python
# 状态转换不允许 → BIZ_301

if current_status == "approved" and new_status == "draft":
    return error_response(
        code=BusinessErrorCodes.STATUS_TRANSITION_NOT_ALLOWED.code,
        message="已批准的申请不能退回草稿",
        status_code=BusinessErrorCodes.STATUS_TRANSITION_NOT_ALLOWED.status_code
    )
```

**场景4: 资源不存在**
```python
# 资源不存在 → BIZ_002

project = db.query(Project).filter(Project.id == project_id).first()
if not project:
    return error_response(
        code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
        message="项目不存在",
        status_code=BusinessErrorCodes.RESOURCE_NOT_FOUND.status_code
    )
```

---

## 七、环境配置

### 测试环境配置（SQLite + pytest）⚠️

#### 为什么测试使用 SQLite

| 对比项 | PostgreSQL（生产） | SQLite（测试） |
|--------|-------------------|----------------|
| **启动速度** | 需要Docker/服务启动 | 内存数据库，毫秒级 |
| **依赖管理** | 需要安装PostgreSQL | Python内置支持 |
| **隔离性** | 需要创建测试数据库 | 每个测试独立内存库 |
| **CI/CD兼容** | 需要配置数据库服务 | 零配置，开箱即用 |

#### SQLite 与 PostgreSQL 差异处理

**关键差异点**：
1. **UUID 处理**：SQLite 中 UUID 按字符串存储
2. **DECIMAL 类型**：SQLite 使用 REAL 近似
3. **时区处理**：SQLite 不支持时区感知的 TIMESTAMP
4. **数组/JSON**：SQLite 的 JSON 支持有限

**测试代码规范**：
```python
# conftest.py - 测试配置示例
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

@pytest.fixture(scope="function")
def test_db():
    """创建测试用内存数据库"""
    # 使用 SQLite 内存数据库
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    # 创建会话
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    # 创建测试数据时，UUID 必须转字符串
    test_user = User(
        id=str(uuid.uuid4()),  # ⚠️ 重要：UUID转字符串
        email="test@example.com",
        role="admin"
    )
    db.add(test_user)
    db.commit()

    yield db

    db.close()
```

#### 真实可用的 .env.test 示例

```bash
# .env.test - 测试环境配置
# ⚠️ 注意：测试环境使用 SQLite，不需要 PostgreSQL

# 基础配置
ENV=test
DEBUG=true
TESTING=true

# 数据库（SQLite内存库）
DATABASE_URL=sqlite:///:memory:
# 或使用文件数据库进行调试
# DATABASE_URL=sqlite:///./test.db

# Supabase配置（使用测试项目）
SUPABASE_URL=https://test-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test-service

# JWT（测试用固定密钥）
JWT_SECRET=test-secret-key-for-unit-tests-only
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Redis（使用fakeredis）
REDIS_URL=redis://localhost:6379/1
USE_FAKE_REDIS=true

# 日志
LOG_LEVEL=DEBUG
LOG_FORMAT=json

# 禁用外部服务
ENABLE_SMS=false
ENABLE_EMAIL=false
ENABLE_WEBHOOK=false
```

#### pytest 配置和 markers

```ini
# pytest.ini
[tool:pytest]
testpaths = backend/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=backend
    --cov-report=term-missing
    --cov-report=html

markers =
    unit: 单元测试（不需要数据库）
    integration: 集成测试（需要数据库）
    permissions: 权限相关测试
    slow: 慢速测试（>1秒）
    auth: 认证相关测试
    api: API端点测试
    service: Service层测试
    model: Model层测试

# 异步测试配置
asyncio_mode = auto
```

**运行测试示例**：
```bash
# 运行所有测试
pytest

# 只运行单元测试
pytest -m unit

# 运行权限测试
pytest -m permissions

# 运行特定模块
pytest backend/tests/test_auth_service.py

# 带覆盖率报告
pytest --cov=backend --cov-report=html
```

---

### 1. 本地开发环境配置

#### ngrok隧道配置
```bash
# 安装ngrok
npm install -g ngrok

# 启动本地后端（在另一个终端）
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 创建ngrok隧道
ngrok http 8000

# 输出示例：
# Forwarding https://random-string.ngrok.io -> http://localhost:8000
# 复制 https://random-string.ngrok.io 到前端环境变量中
```

#### 后端环境变量配置 ⚠️

> **重要**: 以下环境变量列表与`backend/.env.example`同步，AI生成配置或部署脚本时必须参考此清单。

**完整环境变量清单**（共130+配置项）：

**1. 应用基础配置**
```bash
APP_NAME=AI广告代投系统
APP_VERSION=2.3.0
DEBUG=false
ENV_NAME=production  # development/staging/production
```

**2. 数据库配置**
```bash
# 生产环境必须使用PostgreSQL
DATABASE_URL=postgresql://username:password@localhost:5432/ai_ad_spend_prod

# 连接池配置
POOL_SIZE=20
MAX_OVERFLOW=30
POOL_TIMEOUT=30
DB_POOL_PRE_PING=true
DB_POOL_RECYCLE=3600
```

**3. 审计配置**
```bash
# RLS配置（预留参数，当前版本未启用）
ENABLE_RLS=false                # ⚠️ 当前版本保持false，未来可能启用

# 审计日志（当前已启用）
ENABLE_AUDIT_LOG=true           # 启用审计日志
AUDIT_LOG_RETENTION_DAYS=365    # 审计日志保留天数
AUDIT_LOG_INCLUDE_SENSITIVE=false  # 是否记录敏感信息
```

**4. JWT和加密配置** 🔐
```bash
# ⚠️ 生成强随机密钥: openssl rand -hex 32
JWT_SECRET=your_64_character_jwt_secret_key_here
ENCRYPTION_KEY=your_32_character_encryption_key_here
PASSWORD_SALT_ROUNDS=12

# 令牌过期时间
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

**5. Supabase配置** （托管数据库+Auth）
```bash
# 获取地址: https://supabase.com/dashboard/project/_/settings/api
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here
SUPABASE_JWT_SECRET=your_supabase_jwt_secret_here
```

**6. CORS和API安全**
```bash
# 生产环境必须限制允许的域名
ALLOWED_ORIGINS=["https://yourdomain.com"]

RATE_LIMIT=1000              # 请求频率限制（次/分钟）
RATE_WINDOW=60               # 限流窗口（秒）
MAX_FILE_SIZE=10485760       # 最大文件上传大小（10MB）
BCRYPT_ROUNDS=12             # 密码加密轮数
```

**7. 日志配置**
```bash
LOG_LEVEL=INFO               # DEBUG/INFO/WARNING/ERROR/CRITICAL
LOG_FORMAT=json              # json/text
LOG_REQUEST_ID_ENABLED=true  # 请求ID追踪
```

**8. AI监控配置** 🤖
```bash
AI_MONITORING_ENABLED=true            # 启用AI监控
AI_ANOMALY_DETECTION_ENABLED=true     # 异常检测
AI_PREDICTION_ENABLED=true            # 寿命预测
AI_MODEL_VERSION=1.0                  # AI模型版本
```

**9. 通知配置**
```bash
NOTIFICATION_ENABLED=true
EMAIL_NOTIFICATIONS_ENABLED=true
SMS_NOTIFICATIONS_ENABLED=false
SLACK_WEBHOOK_URL=                    # Slack通知webhook
```

**10. 安全强化配置**
```bash
STRICT_CONFIG=0                       # 1=强制强密码和安全配置
SESSION_TIMEOUT=1800                  # 会话超时（秒）
MAX_LOGIN_ATTEMPTS=5                  # 最大登录失败次数
```

**11. Redis配置** （缓存+任务队列）
```bash
REDIS_URL=redis://localhost:6379/0
REDIS_DB=0
REDIS_PASSWORD=
REDIS_MAX_CONNECTIONS=20

# 任务队列
TASK_QUEUE_ENABLED=true
TASK_QUEUE_BROKER_URL=redis://localhost:6379/1
TASK_QUEUE_RESULT_BACKEND=redis://localhost:6379/2
```

**12. 监控配置** （Sentry）
```bash
SENTRY_DSN=your_sentry_dsn_here
SENTRY_TRACES_SAMPLE_RATE=1.0
SENTRY_ENVIRONMENT=production
```

**13. 外部服务配置**
```bash
# SMTP邮件
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_USE_TLS=true

# Facebook API
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret
FACEBOOK_API_VERSION=v18.0
```

**14. 文件存储配置**
```bash
STORAGE_TYPE=local              # local/s3

# AWS S3 (可选)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
AWS_S3_BUCKET=
STORAGE_BASE_URL=
```

**15. 性能监控配置**
```bash
PERFORMANCE_MONITORING_ENABLED=true
METRICS_COLLECTION_INTERVAL=60       # 指标收集间隔（秒）
SLOW_QUERY_THRESHOLD=1000            # 慢查询阈值（毫秒）
```

**16. 数据备份配置**
```bash
BACKUP_ENABLED=true
BACKUP_SCHEDULE="0 2 * * *"          # Cron表达式：每天凌晨2点
BACKUP_RETENTION_DAYS=90             # 备份保留天数
BACKUP_ENCRYPTION_KEY=your_backup_encryption_key
```

---

**AI配置生成约束**:

```python
# ✅ 正确：从环境变量加载配置
from core.config import get_settings

settings = get_settings()
database_url = settings.DATABASE_URL
jwt_secret = settings.JWT_SECRET

# ❌ 错误：硬编码配置
database_url = "postgresql://localhost/db"  # 安全风险！
jwt_secret = "my-secret-key"  # 不安全！

# ✅ 正确：验证必需配置
if not settings.SUPABASE_URL:
    raise ValueError("SUPABASE_URL is required")

# ✅ 正确：提供默认值
log_level = settings.LOG_LEVEL or "INFO"
```

**关键配置检查清单**:

AI部署或生成配置脚本时，必须确认以下配置已正确设置：

1. ✅ `DATABASE_URL` - 生产环境必须使用PostgreSQL
2. ✅ `JWT_SECRET` - 必须64字符以上强随机密钥
3. ✅ `SUPABASE_URL` 和 `SUPABASE_SERVICE_ROLE_KEY` - Supabase认证必需
4. ✅ `ALLOWED_ORIGINS` - 生产环境必须限制域名
5. ✅ `ENABLE_RLS=true` - 必须启用行级安全
6. ✅ `ENABLE_AUDIT_LOG=true` - 必须启用审计日志
7. ✅ `REDIS_URL` - 缓存和任务队列必需
8. ✅ `LOG_LEVEL=INFO` - 生产环境不能为DEBUG

**安全警告** 🔐:

```bash
# ❌ 绝对禁止
- 将 .env 文件提交到Git仓库
- 在日志中打印敏感配置（JWT_SECRET, DATABASE_URL等）
- 在前端代码中暴露后端配置
- 使用弱密钥或默认密钥

# ✅ 安全实践
- 使用 openssl rand -hex 32 生成强随机密钥
- 使用环境变量管理敏感配置
- 定期轮换密钥（至少每季度一次）
- 使用.env.example作为模板，不包含真实值
```

---

### AI环境配置约束补充 ⚠️

**约束1: 环境切换必须使用配置类**

```python
# ✅ 正确：使用配置类管理不同环境
from core.config import get_settings

settings = get_settings()  # 自动根据ENV_NAME加载对应配置

if settings.ENV_NAME == "production":
    # 生产环境额外检查
    assert settings.DEBUG is False, "生产环境不能开启DEBUG"
    assert "localhost" not in settings.ALLOWED_ORIGINS, "生产环境不能允许localhost"
    assert len(settings.JWT_SECRET) >= 64, "JWT密钥长度必须≥64字符"

# ❌ 错误：硬编码环境判断
import os
if os.getenv("ENV") == "prod":  # 字段名不一致！
    database_url = "postgresql://..."  # 硬编码！
```

**约束2: 配置验证必须在启动时执行**

```python
# ✅ 正确：在应用启动时验证关键配置
from fastapi import FastAPI
from core.config import get_settings, validate_config

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    settings = get_settings()

    # 验证必需配置
    validate_config(settings)  # 如缺失必需配置会抛出异常

    # 额外检查
    if settings.ENABLE_RLS and not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError("启用RLS时必须配置SUPABASE_SERVICE_ROLE_KEY")

    # 日志安全检查
    logger.info(f"应用启动: ENV={settings.ENV_NAME}, DEBUG={settings.DEBUG}")
    # ⚠️ 不要打印敏感配置
    # logger.info(f"JWT_SECRET={settings.JWT_SECRET}")  # 危险！

# ❌ 错误：运行时才发现配置缺失
def some_function():
    # 这里才发现配置缺失，但应用已启动
    if not settings.DATABASE_URL:
        raise ValueError("缺少DATABASE_URL")
```

**约束3: 前端配置必须严格隔离**

```typescript
// ✅ 正确：前端仅暴露公开配置
// frontend/.env.local
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
NEXT_PUBLIC_ENV=production

// ❌ 错误：前端暴露后端敏感配置
NEXT_PUBLIC_DATABASE_URL=postgresql://...  // 危险！绝对不能暴露
NEXT_PUBLIC_JWT_SECRET=...                 // 危险！前端不需要
SUPABASE_SERVICE_ROLE_KEY=...              // 危险！仅限后端使用
```

**约束4: 配置加密存储**

```python
# ✅ 正确：敏感配置加密存储（生产环境推荐）
from cryptography.fernet import Fernet
from core.config import get_settings

settings = get_settings()

# 使用专用加密密钥解密配置
if settings.ENCRYPTION_KEY:
    cipher = Fernet(settings.ENCRYPTION_KEY.encode())
    decrypted_db_password = cipher.decrypt(
        settings.DATABASE_PASSWORD_ENCRYPTED.encode()
    ).decode()
    database_url = f"postgresql://user:{decrypted_db_password}@host/db"

# ❌ 错误：明文存储敏感配置
# DATABASE_URL=postgresql://user:plaintext_password@host/db  // 不安全
```

**约束5: Docker环境配置传递**

```yaml
# ✅ 正确：通过docker-compose.yml传递环境变量
version: '3.8'
services:
  backend:
    image: backend:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}  # 从宿主机环境变量读取
      - JWT_SECRET=${JWT_SECRET}
      - SUPABASE_URL=${SUPABASE_URL}
    env_file:
      - .env.production  # 或使用专用环境文件

# ❌ 错误：硬编码敏感配置
version: '3.8'
services:
  backend:
    environment:
      - DATABASE_URL=postgresql://user:password@db/prod  # 硬编码！
      - JWT_SECRET=my-secret-123                         # 不安全！
```

**约束6: 配置文件权限管理**

```bash
# ✅ 正确：限制.env文件权限（Linux/Mac）
chmod 600 backend/.env
chmod 600 frontend/.env.local

# 确认.gitignore包含敏感文件
cat .gitignore | grep -E "\.env$|\.env\.local$|\.env\.production"

# ❌ 错误：配置文件权限过松
# -rw-r--r--  .env  # 所有用户可读！危险
```

**常见配置错误预防清单**:

| 错误类型 | 错误示例 | 正确做法 | 检测方法 |
|---------|---------|---------|----------|
| 硬编码密钥 | `JWT_SECRET="123"` | 使用 `openssl rand -hex 32` | CI/CD扫描 |
| 暴露数据库密码 | URL包含明文密码 | 使用环境变量 | 日志审计 |
| DEBUG未关闭 | `DEBUG=true` in prod | `DEBUG=false` | 启动检查 |
| CORS配置错误 | `ALLOWED_ORIGINS=["*"]` | 限制具体域名 | 安全扫描 |
| RLS未启用 | `ENABLE_RLS=false` | `ENABLE_RLS=true` | 部署检查清单 |
| 前端暴露后端KEY | `NEXT_PUBLIC_DB_URL` | 仅暴露必要配置 | 构建时检查 |

---

### 2. Docker配置
```yaml
# docker-compose.yml
version: '3.8'

services:
  # 后端服务
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/ai_ad_spend
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads

  # 数据库
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=ai_ad_spend
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # Redis缓存
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Nginx反向代理
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
```

### ⚠️ AI代码生成约束提示

**当AI生成涉及环境配置和部署的代码时，必须遵守以下约束：**

1. **环境变量必须在.env文件中定义**
   ```bash
   # ✅ 正确：.env.example文件示例
   # Database
   DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
   SUPABASE_URL=https://xxx.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=eyJ...

   # JWT
   JWT_SECRET=your-secret-key-here
   JWT_ALGORITHM=HS256
   JWT_EXPIRE_MINUTES=30

   # ❌ 错误：硬编码在代码中
   DATABASE_URL = "postgresql://user:pass@localhost:5432/dbname"  # 硬编码
   ```

2. **配置必须使用Pydantic Settings**
   ```python
   from pydantic_settings import BaseSettings

   # ✅ 正确：使用Pydantic Settings
   class Settings(BaseSettings):
       DATABASE_URL: str
       SUPABASE_URL: str
       JWT_SECRET: str

       class Config:
           env_file = ".env"
           case_sensitive = True

   settings = Settings()

   # ❌ 错误：使用os.getenv无验证
   import os
   DATABASE_URL = os.getenv("DATABASE_URL")  # 可能为None，无类型检查
   ```

3. **不同环境必须有独立配置**
   ```bash
   # ✅ 正确：多环境配置
   .env.development    # 开发环境
   .env.test          # 测试环境
   .env.production    # 生产环境

   # 在代码中根据环境加载
   from core.config import get_settings
   settings = get_settings()  # 自动根据ENV变量加载对应配置

   # ❌ 错误：所有环境共用一个配置
   .env  # 开发和生产混用，容易出错
   ```

4. **敏感信息必须加密存储**
   ```python
   # ✅ 正确：敏感信息加密
   from cryptography.fernet import Fernet

   cipher = Fernet(settings.ENCRYPTION_KEY)
   encrypted_token = cipher.encrypt(api_token.encode())

   # ❌ 错误：明文存储敏感信息
   db_user.api_token = "sk-1234567890abcdef"  # 明文存储API密钥
   ```

5. **Docker部署必须使用docker-compose**
   ```yaml
   # ✅ 正确：使用docker-compose管理多服务
   version: '3.8'
   services:
     backend:
       build: ./backend
       env_file: .env.production
       depends_on:
         - postgres
         - redis

   # ❌ 错误：手动启动多个容器
   docker run -d backend
   docker run -d postgres
   docker run -d redis  # 缺少依赖管理和网络配置
   ```

6. **数据库迁移必须使用Alembic**
   ```bash
   # ✅ 正确：使用Alembic管理数据库版本
   alembic revision --autogenerate -m "Add user_profiles table"
   alembic upgrade head

   # ❌ 错误：手动执行SQL文件
   psql -f create_tables.sql  # 无版本控制，难以回滚
   ```

7. **日志配置必须区分环境**
   ```python
   # ✅ 正确：根据环境配置日志级别
   import structlog
   from core.config import settings

   log_level = "DEBUG" if settings.ENV == "development" else "INFO"
   structlog.configure(
       processors=[...],
       logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
   )

   # ❌ 错误：生产环境输出DEBUG日志
   logging.basicConfig(level=logging.DEBUG)  # 生产环境会输出大量调试信息
   ```

8. **测试环境必须使用独立数据库**
   ```python
   # ✅ 正确：测试使用内存数据库或测试专用数据库
   # conftest.py
   @pytest.fixture(scope="session")
   def test_db():
       if settings.ENV == "test":
           db_url = "postgresql://test:test@localhost:5433/test_db"
       engine = create_engine(db_url)
       yield engine

   # ❌ 错误：测试使用开发或生产数据库
   engine = create_engine(settings.DATABASE_URL)  # 可能污染生产数据
   ```

**违反上述任何约束的代码将导致配置混乱、安全漏洞或部署失败！**

---

## 八、核心业务模块（12个模块）⚠️

> **重要**: 本章节文档化了系统的12个核心业务模块。AI生成代码时必须遵循模块索引中的路由路径、状态机和权限要求。详细实现参考 `backend/routers/` 和 `backend/services/` 目录中的实际代码。

### 模块索引

| # | 模块名称 | 路由前缀 | 核心模型 | 状态机 | 主要权限 | 实现文件 |
|---|---------|---------|---------|--------|---------|---------|
| 1 | 用户管理 | `/api/v1/auth` | UserProfile | 无 | admin, account_manager | `routers/authentication.py` |
| 2 | 项目管理 | `/api/v1/projects` | Project | 3状态 | admin, account_manager | `routers/projects.py` |
| 3 | 广告账户 | `/api/v1/ad-accounts` | AdAccount | 6状态 | admin, account_manager, data_operator | `routers/ad_accounts.py` |
| 4 | 渠道管理 | `/api/v1/channels` | Channel | 无 | admin | `routers/channels.py` |
| 5 | 日报管理 | `/api/v1/daily-reports` | DailyReport | 4状态 | 所有角色 | `routers/reports.py` |
| 6 | 充值管理 | `/api/v1/topups` | TopupRequest | 6状态 | 所有角色 | `routers/topup.py` |
| 7 | 对账管理 | `/api/v1/reconciliation` | Reconciliation | 4状态 | admin, data_operator, finance | `routers/reconciliation.py` |
| 8 | 审计日志 | `/api/v1/audit-logs` | AuditLog | 无 | admin | `services/audit_service.py` |
| 9 | 账本管理 | `/api/v1/ledger` | LedgerEntry | 无 | admin, finance | `routers/ledger.py` (规划中) |
| 10 | AI监控 | `/api/v1/ai-monitoring` | AIMonitoringLog | 无 | admin, account_manager | `routers/ai_analytics.py` (规划中) |
| 11 | 数据导入 | `/api/v1/imports` | ImportJob | 5状态 | data_operator, finance | `routers/import_jobs.py` |
| 12 | 报表分析 | `/api/v1/reports` | - | 无 | 所有角色 | `routers/analytics.py` (规划中) |

---

### 关键状态机定义 ⚠️

**状态机1: 项目状态（Project）- 3状态**
```
active ⇄ paused → completed
```

**状态机2: 广告账户（AdAccount）- 6状态**
```
new → testing → active → suspended → dead
                  ↓         ↓
              archived  archived
```

**状态机3: 日报（DailyReport）- 4状态**
```
draft → pending → approved
          ↓
       rejected → draft（可重新提交）
```

**状态机4: 充值（TopupRequest）- 6状态**
```
draft → pending_review → approved → paid → completed
           ↓
        rejected
```

**状态机5: 对账（Reconciliation）- 4状态**
```
pending → processing → completed
            ↓
          failed
```

**状态机6: 数据导入（ImportJob）- 5状态**
```
pending → processing → completed
            ↓
          failed
```

> **参考**: 完整的状态转换规则和权限控制详见 [第二章：核心状态机定义](#二核心状态机定义)

---

### 权限控制矩阵 ⚠️

| 操作类型 | admin | account_manager | data_operator | finance | media_buyer |
|---------|-------|----------------|--------------|---------|-------------|
| 创建项目 | ✅ 全部 | ✅ 自己负责 | ❌ | ❌ | ❌ |
| 分配账户 | ✅ 全部 | ✅ 项目内 | ✅ 全部 | ❌ | ❌ |
| 提交日报 | ✅ 全部 | ✅ 项目内 | ✅ 全部 | ❌ | ✅ 仅自己账户 |
| 审核日报 | ✅ 全部 | ✅ 项目内 | ✅ 全部 | ❌ | ❌ |
| 充值初审 | ✅ 全部 | ✅ 项目内 | ✅ 全部 | ❌ | ❌ |
| 充值终审/打款 | ✅ 全部 | ❌ | ❌ | ✅ 全部 | ❌ |
| 执行对账 | ✅ 全部 | ❌ | ✅ 全部 | ✅ 全部 | ❌ |
| 查看审计日志 | ✅ 全部 | ❌ | ❌ | ❌ | ❌ |

> **参考**: 完整的权限矩阵和RLS策略详见 [第四章：安全策略与权限控制](#四安全策略与权限控制)

---

### AI代码生成约束 ⚠️

**约束1: 路由路径必须符合模块索引**
```python
# ✅ 正确
@router.post("/api/v1/daily-reports")  # 符合模块索引定义

# ❌ 错误
@router.post("/api/reports/daily")  # 路径不符合规范
@router.post("/daily-reports")      # 缺少API版本前缀
```

**约束2: 状态转换必须验证**
```python
# ✅ 正确：日报状态转换验证
ALLOWED_TRANSITIONS = {
    "draft": ["pending"],
    "pending": ["approved", "rejected"],
    "rejected": ["draft"],
    "approved": []  # 终态
}

if new_status not in ALLOWED_TRANSITIONS.get(current_status, []):
    return error_response(
        code=BusinessErrorCodes.STATUS_TRANSITION_NOT_ALLOWED.code,
        message=f"不允许从{current_status}转换到{new_status}"
    )

# ❌ 错误：未验证状态转换
report.status = new_status  # 直接修改，未检查合法性！
```

**约束3: 权限检查必须完整**
```python
# ✅ 正确：使用装饰器验证权限
from deps.auth import require_any_role

@router.patch("/api/v1/ad-accounts/{id}/assign")
@require_any_role(["admin", "account_manager", "data_operator"])
async def assign_account(
    id: int,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 二次验证：account_manager仅能分配项目内账户
    if current_user["role"] == "account_manager":
        account = db.query(AdAccount).filter(AdAccount.id == id).first()
        if account.project.manager_id != current_user["id"]:
            return error_response(
                code=AuthErrorCodes.PERMISSION_DENIED.code,
                message="您只能分配自己负责项目的账户"
            )

# ❌ 错误：缺少权限检查
@router.patch("/api/v1/ad-accounts/{id}/assign")
async def assign_account(id: int, db: Session = Depends(get_db)):
    # 没有任何权限验证！
    pass
```

**约束4: 唯一约束必须检查**
```python
# ✅ 正确：日报唯一约束（ad_account_id + report_date）
existing = db.query(DailyReport).filter(
    DailyReport.ad_account_id == ad_account_id,
    DailyReport.report_date == report_date
).first()

if existing:
    return error_response(
        code=BusinessErrorCodes.RESOURCE_ALREADY_EXISTS.code,
        message="该账户当日日报已存在"
    )

# ❌ 错误：未检查唯一约束
new_report = DailyReport(...)
db.add(new_report)
db.commit()  # 可能违反数据库唯一约束导致异常
```

**约束5: 状态变更必须记录审计日志**
```python
# ✅ 正确：记录状态变更日志
from services.audit_service import audit_service

await audit_service.log(
    user_id=current_user["id"],
    action="daily_report.approve",
    resource_type="daily_report",
    resource_id=report.id,
    details={
        "old_status": "pending",
        "new_status": "approved"
    }
)

# ❌ 错误：状态变更未记录审计日志
report.status = "approved"
db.commit()  # 无法追溯谁、何时、为何审批
```

### ⚠️ AI代码生成约束提示

**当AI生成核心业务模块代码时，必须遵守以下约束：**

1. **仅使用12个已定义的核心模块**
   - ✅ 允许：用户管理、项目管理、渠道管理、广告账户管理、日报管理、充值申请、财务对账、成本分析、数据导入、AI监控、审计日志、通知系统
   - ❌ 禁止：创建未定义的新模块、修改模块路由前缀、跨模块混合职责

2. **必须遵循模块索引中的路由前缀**
   ```python
   # ✅ 正确：使用定义的路由前缀
   router = APIRouter(prefix="/api/v1/projects", tags=["项目管理"])

   # ❌ 错误：使用未定义的路由前缀
   router = APIRouter(prefix="/projects", tags=["项目"])  # 缺少/api/v1
   router = APIRouter(prefix="/api/v1/project", tags=["项目"])  # 单数形式错误
   ```

3. **业务逻辑必须在Service层实现**
   ```python
   # ✅ 正确：Controller → Service → Repository 分层
   # routers/projects.py
   @router.post("/projects")
   async def create_project(
       project: ProjectCreate,
       db: Session = Depends(get_db)
   ):
       return await project_service.create_project(db, project)

   # services/project_service.py
   async def create_project(db: Session, project: ProjectCreate):
       # 业务逻辑：验证、计算、状态管理
       new_project = Project(**project.dict())
       db.add(new_project)
       db.commit()
       return new_project

   # ❌ 错误：业务逻辑直接写在Router中
   @router.post("/projects")
   async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
       # 验证逻辑
       if not project.name:
           raise HTTPException(400)
       # 业务计算
       total_budget = project.budget * 1.05
       # 数据库操作
       db.add(Project(name=project.name, budget=total_budget))
       db.commit()  # 业务逻辑和数据访问混在一起
   ```

4. **状态转换必须遵循对应状态机**
   ```python
   # ✅ 正确：遵循状态机定义
   from services.topup_service import approve_topup_request

   # 会自动检查状态转换是否合法 (pending → approved)
   await approve_topup_request(topup_id, current_user)

   # ❌ 错误：绕过状态机直接修改状态
   topup = db.query(TopupRequest).filter_by(id=topup_id).first()
   topup.status = "paid"  # 跳过了approved状态，违反状态机
   db.commit()
   ```

5. **权限控制必须对应角色矩阵**
   ```python
   # ✅ 正确：根据模块索引使用正确的角色
   @router.post("/daily-reports")
   @require_role(["media_buyer", "data_operator"])  # 日报模块的合法角色
   async def create_daily_report(...):
       pass

   # ❌ 错误：使用不相关的角色
   @router.post("/daily-reports")
   @require_role(["finance"])  # 财务角色不应创建日报
   async def create_daily_report(...):
       pass
   ```

6. **关联数据必须遵循外键约束**
   ```python
   # ✅ 正确：验证外键关联
   from services.project_service import get_project_by_id

   project = await get_project_by_id(db, project_id)
   if not project:
       return error_response(
           code=BusinessErrorCodes.PROJECT_NOT_FOUND.code,
           message="项目不存在",
           status_code=404
       )

   daily_report = DailyReport(project_id=project.id, ...)

   # ❌ 错误：不验证外键关联
   daily_report = DailyReport(
       project_id=project_id,  # 可能不存在，导致外键约束错误
       ...
   )
   db.add(daily_report)
   db.commit()  # 可能抛出IntegrityError
   ```

7. **敏感操作必须记录审计日志**
   - 创建/删除项目
   - 状态转换（日报审批、充值审批等）
   - 财务对账确认
   - 用户角色变更

8. **跨模块调用必须通过Service层**
   ```python
   # ✅ 正确：通过Service调用其他模块
   from services.project_service import get_project_by_id
   from services.ad_account_service import get_accounts_by_project

   project = await get_project_by_id(db, project_id)
   accounts = await get_accounts_by_project(db, project_id)

   # ❌ 错误：直接跨模块数据库查询
   project = db.query(Project).filter_by(id=project_id).first()
   accounts = db.query(AdAccount).filter_by(project_id=project_id).all()  # 跨模块查询
   ```

**违反上述任何约束的代码将导致模块职责混乱、业务逻辑错误或系统架构破坏！**

---


## 九、AI监控功能（参考）

> **说明**: 本章描述AI监控功能的规划和接口定义。实际开发中，AI功能作为可选模块，需根据业务需求和数据积累情况决定是否实施。

### 1. AI监控模块定义

**Router**: `backend/routers/ai_analytics.py`（规划中）
**Service**: `backend/services/ai_monitoring_service.py`
**Models**: `AIMonitoringLog`, `AnomalyDetectionResult`

**核心功能**:
```python
# 1. 异常检测
- 账户消耗异常（突增/骤降超过阈值）
- 转化率异常（低于历史平均值）
- CPL异常（成本过高）

# 2. 寿命预测
- 预测账户剩余寿命（基于历史数据）
- 风险等级评估（低/中/高/严重）

# 3. 性能监控
- 点击率（CTR）趋势
- 转化率趋势
- ROI趋势
```

**数据依赖**:
- `daily_reports` - 日报数据（消耗、点击、转化）
- `ad_accounts` - 账户状态和历史
- `topup_requests` - 充值历史

---

### 2. AI触发时机（建议）

| 功能模块 | 触发时机 | 数据要求 | 输出 |
|---------|---------|---------|------|
| 消耗异常检测 | 每日凌晨2点 | 至少7天历史数据 | 异常账户列表 + 告警 |
| 性能监控 | 每日凌晨2点 | 至少14天历史数据 | 性能下降账户列表 |
| 寿命预测 | 每周一凌晨3点 | 至少30天历史数据 | 高风险账户列表 |
| 实时异常告警 | 日报提交时 | 当前日报 + 7天历史 | 即时告警通知 |

---

### 3. AI约束和限制 ⚠️

**AI代码生成约束**:

```python
# ✅ 正确：AI模块作为可选功能
if settings.AI_MONITORING_ENABLED:
    from services.ai_monitoring_service import ai_monitor
    anomalies = await ai_monitor.detect_anomalies(data)
else:
    # AI功能未启用，跳过
    pass

# ❌ 错误：AI模块作为必需依赖
from services.ai_monitoring_service import ai_monitor  # 如果模块不存在会报错！
anomalies = await ai_monitor.detect_anomalies(data)

# ✅ 正确：检查数据量是否足够
if len(historical_data) < 7:
    logger.warning("历史数据不足，跳过AI检测")
    return []

# ❌ 错误：不检查数据量直接执行
result = ai_monitor.detect(historical_data)  # 数据不足会得到不准确结果！
```

**实施建议**:
1. **P2阶段实施**：AI功能属于增强功能，应在核心业务稳定后再开发
2. **数据积累**：至少积累30天以上数据再启用AI预测
3. **人工验证**：AI告警需要人工确认，不能自动执行操作
4. **逐步优化**：从简单规则开始，逐步引入机器学习模型

---

### 4. 生产环境部署检查清单 ⚠️

> **重要**: 在部署到生产环境前，必须完成以下所有检查项，确保系统稳定性和安全性。

#### 4.1 环境配置检查

**必须项** ✅:
- [ ] `DATABASE_URL` 使用生产PostgreSQL（Supabase）
- [ ] `SUPABASE_URL` 和 `SUPABASE_SERVICE_ROLE_KEY` 配置正确
- [ ] `JWT_SECRET` 使用强随机密钥（≥64字符）
- [ ] `API_ENV` 设置为 `production`
- [ ] `DEBUG` 设置为 `false`
- [ ] `ALLOWED_ORIGINS` 配置生产域名
- [ ] `CORS_ALLOW_CREDENTIALS` 设置为 `true`

**安全配置** 🔒:
- [ ] `ENABLE_RLS` 设置为 `true`（强制启用RLS）
- [ ] `ENABLE_AUDIT_LOG` 设置为 `true`
- [ ] `AUDIT_LOG_RETENTION_DAYS` ≥365
- [ ] `PASSWORD_MIN_LENGTH` ≥8
- [ ] `JWT_EXPIRATION_HOURS` ≤24
- [ ] `REFRESH_TOKEN_EXPIRATION_DAYS` ≤30

**性能配置** ⚡:
- [ ] `DATABASE_POOL_SIZE` 根据负载设置（建议10-50）
- [ ] `DATABASE_MAX_OVERFLOW` 设置合理值
- [ ] `REDIS_ENABLED` 设置为 `true`
- [ ] `REDIS_URL` 配置正确
- [ ] `CACHE_TTL` 设置合理过期时间

---

#### 4.2 数据库检查

**RLS策略启用** 🔐:
```sql
-- 验证所有核心表都启用了RLS
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN (
    'user_profiles', 'projects', 'ad_accounts',
    'daily_reports', 'topup_requests', 'reconciliations'
);

-- 预期结果：所有表的rowsecurity应该为true
```

**索引检查** 📊:
```sql
-- 检查关键索引是否存在
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename IN ('user_profiles', 'projects', 'daily_reports')
ORDER BY tablename, indexname;

-- 必需索引列表：
-- user_profiles: idx_user_profiles_role, idx_user_profiles_active
-- projects: idx_projects_manager, idx_projects_status
-- daily_reports: idx_daily_reports_account, idx_daily_reports_date
```

**数据完整性** ✓:
```sql
-- 检查是否有孤立数据
-- 1. 检查ad_accounts是否都关联到有效项目
SELECT COUNT(*) FROM ad_accounts aa
LEFT JOIN projects p ON p.id = aa.project_id
WHERE p.id IS NULL;
-- 预期结果：0

-- 2. 检查daily_reports是否都关联到有效账户
SELECT COUNT(*) FROM daily_reports dr
LEFT JOIN ad_accounts aa ON aa.id = dr.ad_account_id
WHERE aa.id IS NULL;
-- 预期结果：0

-- 3. 检查是否有无效角色
SELECT COUNT(*) FROM user_profiles
WHERE role NOT IN ('admin', 'account_manager', 'data_operator', 'finance', 'media_buyer');
-- 预期结果：0
```

---

#### 4.3 API接口检查

**健康检查** 💚:
```bash
# 1. 后端健康检查
curl https://api.yourdomain.com/health
# 预期响应：{"status":"healthy","version":"2.2.0"}

# 2. 数据库连接检查
curl https://api.yourdomain.com/health/db
# 预期响应：{"status":"connected","latency_ms":<100}

# 3. Redis连接检查
curl https://api.yourdomain.com/health/redis
# 预期响应：{"status":"connected"}
```

**认证流程** 🔑:
```bash
# 1. 注册新用户（应该成功）
curl -X POST https://api.yourdomain.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Password123!","username":"testuser"}'

# 2. 登录（应该返回token）
curl -X POST https://api.yourdomain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"test@example.com","password":"Password123!"}'

# 3. 验证token（应该返回用户信息）
curl -X GET https://api.yourdomain.com/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

**权限控制** 🛡️:
```bash
# 使用media_buyer token尝试创建用户（应该返回403）
curl -X POST https://api.yourdomain.com/api/v1/users \
  -H "Authorization: Bearer <media_buyer_token>" \
  -H "Content-Type: application/json" \
  -d '{"email":"newuser@example.com","password":"Pass123!","role":"media_buyer"}'
# 预期响应：{"success":false,"error":{"code":"AUTH_005"}}
```

---

#### 4.4 前端检查

**构建验证** 🏗️:
```bash
# 1. 构建前端
cd frontend
npm run build

# 2. 检查构建产物大小（应该<10MB）
du -sh .next

# 3. 检查关键chunk大小
ls -lh .next/static/chunks/pages

# 4. 运行生产模式
npm run start
```

**关键页面检查** 📄:
- [ ] 登录页面正常加载（/auth/login）
- [ ] 注册页面正常加载（/auth/sign-up）
- [ ] 仪表盘正常加载（/dashboard）
- [ ] 日报页面正常加载（/daily-reports）
- [ ] 充值页面正常加载（/topup）
- [ ] 对账页面正常加载（/reconciliation）

**响应式测试** 📱:
- [ ] 桌面端（≥1920px）显示正常
- [ ] 笔记本（1366px-1920px）显示正常
- [ ] 平板（768px-1366px）显示正常
- [ ] 手机（<768px）显示正常

---

#### 4.5 安全检查

**SQL注入测试** 💉:
```bash
# 尝试SQL注入（应该被过滤）
curl -X GET "https://api.yourdomain.com/api/v1/projects?search=' OR '1'='1"
# 预期：返回空结果或错误，不应返回所有数据

# 尝试路径遍历（应该被拒绝）
curl -X GET "https://api.yourdomain.com/api/v1/files?path=../../etc/passwd"
# 预期：返回403或404
```

**XSS测试** 🚫:
```bash
# 尝试注入脚本（应该被转义）
curl -X POST https://api.yourdomain.com/api/v1/projects \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"project_name":"<script>alert(1)</script>"}'
# 预期：数据被存储为纯文本，不执行脚本
```

**CORS检查** 🌐:
```bash
# 验证CORS配置
curl -H "Origin: https://malicious.com" \
  -H "Access-Control-Request-Method: POST" \
  -X OPTIONS https://api.yourdomain.com/api/v1/auth/login

# 预期：不应返回Access-Control-Allow-Origin: https://malicious.com
```

**敏感信息泄露** 🔍:
- [ ] 错误响应不包含堆栈跟踪
- [ ] 日志不包含密码、token等敏感信息
- [ ] API文档未在生产环境暴露（/docs, /redoc）
- [ ] `.env`文件不在git仓库中

---

#### 4.6 性能检查

**响应时间** ⏱️:
```bash
# 1. 测试API响应时间（应该<200ms）
curl -w "@curl-format.txt" -o /dev/null -s https://api.yourdomain.com/api/v1/projects

# curl-format.txt内容：
# time_namelookup:  %{time_namelookup}\n
# time_connect:  %{time_connect}\n
# time_total:  %{time_total}\n

# 2. 批量请求测试（使用ab或wrk）
ab -n 1000 -c 10 https://api.yourdomain.com/health
```

**数据库查询优化** 🗄️:
```sql
-- 检查慢查询（执行时间>1秒）
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE mean_exec_time > 1000
ORDER BY mean_exec_time DESC
LIMIT 10;

-- 检查缺失索引
SELECT schemaname, tablename, attname
FROM pg_stats
WHERE schemaname = 'public'
AND n_distinct > 100
AND correlation < 0.1;
```

---

#### 4.7 监控和告警

**Prometheus指标** 📈:
```bash
# 验证指标暴露
curl https://api.yourdomain.com/metrics

# 预期输出包含：
# http_requests_total{...}
# http_request_duration_seconds{...}
# database_connections{...}
```

**日志检查** 📝:
- [ ] 日志格式统一（JSON格式）
- [ ] 日志级别配置正确（生产环境使用INFO或WARNING）
- [ ] 关键操作有日志记录（登录、权限变更、财务操作）
- [ ] 日志轮转配置正确（按天或按大小）

**告警配置** 🚨:
- [ ] CPU使用率>80%告警
- [ ] 内存使用率>85%告警
- [ ] 磁盘使用率>90%告警
- [ ] API错误率>5%告警
- [ ] 数据库连接数>80%告警

---

#### 4.8 备份和恢复

**数据库备份** 💾:
```bash
# 1. 验证自动备份任务
# Supabase会自动备份，验证备份列表
# 手动备份命令（如果需要）：
pg_dump -h <host> -U <user> -d <database> > backup_$(date +%Y%m%d).sql

# 2. 测试恢复流程（在测试环境）
psql -h <test_host> -U <user> -d <test_db> < backup.sql
```

**配置备份** 📋:
- [ ] `.env`文件安全存储（密钥管理系统）
- [ ] nginx配置备份
- [ ] SSL证书备份
- [ ] 部署脚本备份

---

#### 4.9 最终检查清单

**部署前最后确认** ✅:
- [ ] 所有测试通过（单元测试、集成测试、E2E测试）
- [ ] 代码已合并到主分支并打tag
- [ ] 数据库迁移已在测试环境验证
- [ ] RLS策略已测试并启用
- [ ] 所有环境变量已配置
- [ ] 监控告警已配置
- [ ] 备份策略已实施
- [ ] 回滚计划已准备
- [ ] 团队成员已通知
- [ ] 文档已更新

**部署后验证** 🔍:
- [ ] 健康检查通过
- [ ] 登录功能正常
- [ ] 关键业务流程可用（日报、充值、对账）
- [ ] 监控数据正常上报
- [ ] 日志正常输出
- [ ] 性能指标在预期范围内
- [ ] 无异常告警

---

## 十、测试策略与质量保证 ⚠️

> **重要**: 测试是保证代码质量的关键，AI生成代码时必须同步生成相应的测试用例，本章定义了完整的测试策略和质量标准。

### 1. 测试金字塔结构

**测试层级**（从下到上）:
```
        ▲
       / \
      /E2E\        10% - 端到端测试（关键业务流程）
     /─────\
    /  集成  \      30% - 集成测试（API接口、数据库）
   /─────────\
  /   单元测试  \    60% - 单元测试（函数、类方法）
 /─────────────\
```

**覆盖率目标**:
- **单元测试覆盖率**: ≥80%
- **集成测试覆盖率**: ≥70%
- **E2E测试覆盖率**: 核心流程100%
- **关键模块覆盖率**: ≥90%（认证、权限、财务、对账）

---

### 2. 单元测试规范 ⚠️

**Python后端单元测试（pytest）**:

```python
# backend/tests/test_auth_service.py
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from services.supabase_auth_service import SupabaseAuthService
from core.error_codes import AuthErrorCodes

class TestSupabaseAuthService:
    """认证服务单元测试"""

    @pytest.fixture
    def auth_service(self):
        """创建认证服务实例"""
        return SupabaseAuthService()

    @pytest.fixture
    def mock_supabase_client(self):
        """模拟Supabase客户端"""
        return Mock()

    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service, mock_supabase_client):
        """测试用户注册成功"""
        # Arrange - 准备测试数据
        email = "test@example.com"
        password = "Password123!"
        username = "testuser"

        mock_response = Mock()
        mock_response.user = Mock(id="user-uuid", email=email)
        mock_supabase_client.auth.admin.create_user.return_value = mock_response

        # 注入mock
        auth_service._provider.get_admin_client = Mock(return_value=mock_supabase_client)

        # Act - 执行测试
        result = await auth_service.register_user(
            email=email,
            password=password,
            username=username
        )

        # Assert - 验证结果
        assert result["email"] == email
        assert result["user_id"] == "user-uuid"
        assert "message" in result
        mock_supabase_client.auth.admin.create_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, auth_service, mock_supabase_client):
        """测试重复邮箱注册"""
        # Arrange
        email = "duplicate@example.com"
        mock_supabase_client.auth.admin.create_user.side_effect = Exception("duplicate")

        auth_service._provider.get_admin_client = Mock(return_value=mock_supabase_client)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register_user(
                email=email,
                password="Password123!",
                username="testuser"
            )

        assert exc_info.value.status_code == 400
        assert "已被注册" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_login_user_success(self, auth_service):
        """测试登录成功"""
        # 测试实现...
        pass

    @pytest.mark.asyncio
    async def test_login_user_invalid_credentials(self, auth_service):
        """测试登录凭据错误"""
        # 测试实现...
        pass
```

**TypeScript前端单元测试（Vitest）**:

```typescript
// frontend/tests/components/LoginForm.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { LoginForm } from '@/components/auth/LoginForm'

describe('LoginForm', () => {
  it('should render login form with email and password fields', () => {
    render(<LoginForm />)

    expect(screen.getByLabelText(/邮箱/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/密码/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument()
  })

  it('should show validation errors for empty fields', async () => {
    render(<LoginForm />)

    const submitButton = screen.getByRole('button', { name: /登录/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/邮箱不能为空/i)).toBeInTheDocument()
      expect(screen.getByText(/密码不能为空/i)).toBeInTheDocument()
    })
  })

  it('should call onSubmit with email and password', async () => {
    const mockOnSubmit = vi.fn()
    render(<LoginForm onSubmit={mockOnSubmit} />)

    fireEvent.change(screen.getByLabelText(/邮箱/i), {
      target: { value: 'test@example.com' }
    })
    fireEvent.change(screen.getByLabelText(/密码/i), {
      target: { value: 'Password123!' }
    })

    const submitButton = screen.getByRole('button', { name: /登录/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'Password123!'
      })
    })
  })

  it('should display error message on login failure', async () => {
    const mockOnSubmit = vi.fn().mockRejectedValue(
      new Error('用户名或密码错误')
    )
    render(<LoginForm onSubmit={mockOnSubmit} />)

    // 填写表单并提交
    // ... (省略填写逻辑)

    await waitFor(() => {
      expect(screen.getByText(/用户名或密码错误/i)).toBeInTheDocument()
    })
  })
})
```

---

### 3. 集成测试规范 ⚠️

**后端API集成测试**:

```python
# backend/tests/test_authentication_api.py
import pytest
from httpx import AsyncClient
from fastapi import status

@pytest.mark.asyncio
class TestAuthenticationAPI:
    """认证API集成测试"""

    async def test_register_login_flow(self, client: AsyncClient):
        """测试完整的注册-登录流程"""
        # 1. 注册新用户
        register_data = {
            "email": "integration_test@example.com",
            "password": "Password123!",
            "username": "integration_user"
        }

        response = await client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == register_data["email"]

        # 2. 登录
        login_data = {
            "identifier": register_data["email"],
            "password": register_data["password"]
        }

        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "token" in data["data"]

        access_token = data["data"]["token"]["access_token"]

        # 3. 验证token有效性
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["user"]["email"] == register_data["email"]

    async def test_permission_enforcement(self, client: AsyncClient, test_user_token):
        """测试权限控制"""
        # 使用media_buyer token尝试访问admin接口
        headers = {"Authorization": f"Bearer {test_user_token['access_token']}"}

        response = await client.post("/api/v1/users", headers=headers, json={
            "email": "newuser@example.com",
            "password": "Password123!",
            "role": "media_buyer"
        })

        # 应该返回403权限不足
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert data["error"]["code"] == "AUTH_005"
```

**数据库集成测试**:

```python
# backend/tests/test_daily_report_service.py
import pytest
from sqlalchemy.orm import Session
from services.daily_report_service import DailyReportService
from models.daily_report import DailyReport

@pytest.mark.asyncio
class TestDailyReportService:
    """日报服务集成测试（包含数据库操作）"""

    @pytest.fixture
    def service(self, db: Session):
        return DailyReportService(db)

    async def test_create_report_with_transaction(self, service, db, test_user):
        """测试创建日报（包含事务）"""
        # Arrange
        report_data = {
            "ad_account_id": "test-account-001",
            "report_date": "2025-11-11",
            "spend": 1500.00,
            "conversions": 45
        }

        # Act
        report = await service.create_report(
            data=report_data,
            user_id=test_user.id
        )

        # Assert
        assert report.id is not None
        assert report.status == "draft"

        # 验证数据库中确实存在
        db_report = db.query(DailyReport).filter(
            DailyReport.id == report.id
        ).first()
        assert db_report is not None
        assert db_report.spend == 1500.00

    async def test_transaction_rollback_on_error(self, service, db):
        """测试错误时事务回滚"""
        initial_count = db.query(DailyReport).count()

        # 尝试创建无效日报（应该失败）
        with pytest.raises(Exception):
            await service.create_report(
                data={"invalid": "data"},
                user_id="invalid-user-id"
            )

        # 验证数据库未被修改
        final_count = db.query(DailyReport).count()
        assert final_count == initial_count
```

---

### 4. E2E测试规范 ⚠️

**关键业务流程E2E测试（Playwright）**:

```typescript
// frontend/tests/e2e/daily-report-flow.spec.ts
import { test, expect } from '@playwright/test'

test.describe('日报提交流程', () => {
  test('投手提交日报并等待审核', async ({ page }) => {
    // 1. 登录为投手
    await page.goto('/auth/login')
    await page.fill('[name="email"]', 'buyer@example.com')
    await page.fill('[name="password"]', 'Password123!')
    await page.click('button[type="submit"]')

    await expect(page).toHaveURL('/dashboard')

    // 2. 导航到日报页面
    await page.click('text=日报管理')
    await expect(page).toHaveURL('/daily-reports')

    // 3. 点击"新建日报"
    await page.click('text=新建日报')

    // 4. 填写日报表单
    await page.selectOption('[name="ad_account_id"]', 'acc-fb-001')
    await page.fill('[name="spend"]', '1500')
    await page.fill('[name="conversions"]', '45')
    await page.fill('[name="notes"]', '测试日报')

    // 5. 提交日报
    await page.click('button[type="submit"]')

    // 6. 验证提交成功提示
    await expect(page.locator('text=日报提交成功')).toBeVisible()

    // 7. 验证日报列表中显示新日报
    await expect(page.locator('text=pending')).toBeVisible()
  })

  test('数据员审核日报流程', async ({ page }) => {
    // 1. 登录为数据员
    await page.goto('/auth/login')
    await page.fill('[name="email"]', 'operator@example.com')
    await page.fill('[name="password"]', 'Password123!')
    await page.click('button[type="submit"]')

    // 2. 进入待审核日报列表
    await page.click('text=日报管理')
    await page.click('text=待审核')

    // 3. 点击第一条待审核日报
    await page.click('.report-item:first-child')

    // 4. 审核通过
    await page.fill('[name="confirmed_conversions"]', '43')
    await page.fill('[name="adjustment_reason"]', '实际核验后调整')
    await page.click('text=审核通过')

    // 5. 验证审核成功
    await expect(page.locator('text=审核成功')).toBeVisible()
    await expect(page.locator('text=approved')).toBeVisible()
  })
})

test.describe('充值申请流程', () => {
  test('完整的充值申请-审批流程', async ({ page, context }) => {
    // 测试投手申请 → 数据员初审 → 财务审批 → 打款确认的完整流程
    // ... (省略详细实现)
  })
})
```

---

### 5. AI代码生成测试约束 ⚠️

**约束1: 必须为新功能编写测试**
```python
# ✅ 正确：创建功能的同时创建测试
# backend/services/new_service.py
class NewService:
    async def process_data(self, data):
        # 业务逻辑
        return result

# backend/tests/test_new_service.py
class TestNewService:
    @pytest.mark.asyncio
    async def test_process_data_success(self):
        # 测试用例
        pass

# ❌ 错误：只写功能代码，没有测试
# backend/services/new_service.py
class NewService:
    async def process_data(self, data):
        return result
# 没有对应的测试文件！
```

**约束2: 测试必须独立且可重复**
```python
# ✅ 正确：使用fixture准备测试数据
@pytest.fixture
def test_user(db):
    user = UserProfile(
        email="test@example.com",
        role="media_buyer"
    )
    db.add(user)
    db.commit()
    yield user
    db.delete(user)
    db.commit()

def test_user_service(test_user):
    # 使用fixture创建的测试数据
    assert test_user.email == "test@example.com"

# ❌ 错误：测试依赖外部数据或其他测试
def test_dependent():
    # 假设数据库中已存在某个用户
    user = db.query(User).first()  # 可能不存在！
    assert user is not None
```

**约束3: 测试命名必须清晰**
```python
# ✅ 正确：测试名称描述测试内容
def test_register_user_with_duplicate_email_should_return_400():
    pass

def test_login_with_invalid_password_should_return_401():
    pass

# ❌ 错误：测试名称不明确
def test_1():
    pass

def test_auth():
    pass
```

---

### 6. 测试环境配置

**测试数据库配置**:
```python
# backend/tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.db import Base

# 测试数据库URL（独立于开发/生产数据库）
TEST_DATABASE_URL = "postgresql://test:test@localhost:5432/ai_ad_test"

@pytest.fixture(scope="session")
def test_engine():
    """创建测试数据库引擎"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db(test_engine):
    """为每个测试创建独立的数据库session"""
    connection = test_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
```

**前端测试配置**:
```typescript
// frontend/vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './tests/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'tests/',
        '**/*.d.ts',
        '**/*.config.*',
      ]
    }
  }
})
```

---

### 7. 持续集成测试

**GitHub Actions配置**:
```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests with coverage
        run: |
          cd backend
          pytest --cov=. --cov-report=xml --cov-report=term
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run tests
        run: |
          cd frontend
          npm run test:coverage
```

---

## 十一、部署运维指南

> **说明**: 本章提供完整的生产环境部署和运维指导。详细的部署检查清单参见 [第九章 4节：生产环境部署检查清单](#4-生产环境部署检查清单-)。

### 1. 生产部署流程 ⚠️

**步骤1: 环境准备**
```bash
# 1. 确认服务器环境（Linux推荐 Ubuntu 22.04 LTS）
uname -a

# 2. 安装必需软件
apt update && apt install -y docker.io docker-compose nginx postgresql-client redis-tools

# 3. 配置防火墙
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
ufw enable

# 4. 配置域名DNS
# A记录指向服务器IP，CNAME配置www子域名
```

**步骤2: 代码部署**
```bash
# 1. 克隆代码库
git clone https://github.com/your-org/ai-ad-spend.git /opt/ai-ad-spend
cd /opt/ai-ad-spend

# 2. 切换到发布分支/标签
git checkout tags/v2.3.0  # 或 main 分支

# 3. 复制并配置环境变量
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.production

# 编辑配置文件（参考第七章环境配置）
nano backend/.env
nano frontend/.env.production
```

**步骤3: 数据库初始化**
```bash
# 1. 运行数据库迁移
cd backend
alembic upgrade head

# 2. 验证RLS策略已启用
psql $DATABASE_URL -c "
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('user_profiles', 'projects', 'ad_accounts');
"
# 预期：所有表 rowsecurity = t

# 3. 创建初始管理员用户（通过Supabase Dashboard或API）
```

**步骤4: 构建和启动服务**
```bash
# 1. 构建镜像
docker-compose -f docker-compose.prod.yml build

# 2. 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 3. 验证服务健康
curl http://localhost:8000/health
curl http://localhost:3000  # 前端应返回HTML
```

**步骤5: 配置Nginx反向代理**
```bash
# 1. 创建Nginx配置（见本章节4. Nginx配置）
nano /etc/nginx/sites-available/ai-ad-spend

# 2. 启用站点
ln -s /etc/nginx/sites-available/ai-ad-spend /etc/nginx/sites-enabled/
nginx -t  # 测试配置
systemctl reload nginx

# 3. 配置SSL证书（使用Let's Encrypt）
apt install certbot python3-certbot-nginx
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

**步骤6: 配置监控和告警**
```bash
# 1. 启动Prometheus + Grafana
docker-compose -f docker-compose.monitoring.yml up -d

# 2. 访问Grafana配置仪表板
# http://your-server:3001 (默认账号: admin/admin)

# 3. 配置告警通知（邮件/Slack/钉钉）
```

---

### 2. CI/CD自动化部署 ⚠️

**GitHub Actions配置示例**:

```yaml
# .github/workflows/deploy-production.yml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run tests
        run: |
          cd backend && pytest -v
          cd ../frontend && npm test

      - name: Build Docker images
        run: |
          docker build -t backend:${{ github.ref_name }} ./backend
          docker build -t frontend:${{ github.ref_name }} ./frontend

      - name: Deploy to production server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.PROD_HOST }}
          username: ${{ secrets.PROD_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/ai-ad-spend
            git pull origin main
            git checkout ${{ github.ref_name }}
            docker-compose -f docker-compose.prod.yml down
            docker-compose -f docker-compose.prod.yml up -d
            docker-compose -f docker-compose.prod.yml logs -f --tail=50
```

---

### 3. 备份和恢复策略 ⚠️

**自动化备份配置**:

```bash
# /opt/backup/daily-backup.sh
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/ai-ad-spend"

# 1. 备份PostgreSQL数据库
pg_dump $DATABASE_URL | gzip > "$BACKUP_DIR/db_backup_$DATE.sql.gz"

# 2. 备份Redis数据
redis-cli --rdb "$BACKUP_DIR/redis_backup_$DATE.rdb"

# 3. 备份配置文件
tar -czf "$BACKUP_DIR/config_backup_$DATE.tar.gz" /opt/ai-ad-spend/backend/.env /opt/ai-ad-spend/frontend/.env.production

# 4. 清理30天前的备份
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +30 -delete

# 5. 上传到远程存储（可选）
# aws s3 sync $BACKUP_DIR s3://your-backup-bucket/ai-ad-spend/
```

**定时任务配置**:
```bash
# 配置cron（每天凌晨2点执行备份）
crontab -e
# 添加以下行：
0 2 * * * /opt/backup/daily-backup.sh >> /var/log/backup.log 2>&1
```

**数据恢复流程**:
```bash
# 1. 停止服务
docker-compose -f docker-compose.prod.yml down

# 2. 恢复数据库
gunzip < db_backup_20250115_020000.sql.gz | psql $DATABASE_URL

# 3. 恢复Redis（如需要）
redis-cli --rdb redis_backup_20250115_020000.rdb

# 4. 重启服务
docker-compose -f docker-compose.prod.yml up -d

# 5. 验证数据完整性
psql $DATABASE_URL -c "SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM projects;"
```

---

### 4. 性能优化建议 ⚠️

**数据库优化**:
```sql
-- 1. 创建索引（如未自动创建）
CREATE INDEX CONCURRENTLY idx_daily_reports_date ON daily_reports(report_date);
CREATE INDEX CONCURRENTLY idx_daily_reports_account ON daily_reports(ad_account_id);
CREATE INDEX CONCURRENTLY idx_topup_status ON topup_requests(status);

-- 2. 更新统计信息
ANALYZE daily_reports;
ANALYZE ad_accounts;
ANALYZE topup_requests;

-- 3. 定期清理过期数据（可选）
DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '365 days';
```

**Redis缓存策略**:
```python
# 缓存热点数据（项目列表、账户状态等）
from redis import Redis
from functools import wraps

redis_client = Redis.from_url(settings.REDIS_URL)

def cache_result(key_prefix: str, expire: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{args}:{kwargs}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expire, json.dumps(result))
            return result
        return wrapper
    return decorator

@cache_result("project_list", expire=600)
async def get_projects(user_id: str):
    # 查询数据库...
    pass
```

**前端性能优化**:
```typescript
// 1. 启用Next.js增量静态再生成（ISR）
export async function getStaticProps() {
  return {
    props: { ... },
    revalidate: 60  // 60秒后重新生成
  }
}

// 2. 图片优化
import Image from 'next/image'
<Image src="/logo.png" width={200} height={50} alt="Logo" />

// 3. 代码分割（动态导入）
const DynamicComponent = dynamic(() => import('./HeavyComponent'))
```

---

### 5. 故障排查指南 ⚠️

**问题1: 数据库连接失败**
```bash
# 症状：API返回500错误，日志显示"database connection failed"

# 排查步骤：
1. 检查数据库服务状态
   docker-compose ps postgres  # 或 systemctl status postgresql

2. 验证连接字符串
   psql $DATABASE_URL -c "SELECT 1"

3. 检查防火墙规则
   ufw status | grep 5432

4. 查看连接池状态
   psql -c "SELECT count(*) FROM pg_stat_activity;"

# 解决方案：
- 重启数据库服务
- 检查DATABASE_URL配置是否正确
- 增加连接池大小（POOL_SIZE）
```

**问题2: RLS策略导致数据无法访问**
```bash
# 症状：用户登录后无法看到数据

# 排查步骤：
1. 验证RLS策略是否启用
   psql -c "SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname='public';"

2. 检查当前用户的auth.uid()
   psql -c "SELECT auth.uid();"

3. 测试RLS策略（以特定用户身份）
   SET LOCAL app.current_user_id = 'user-uuid-here';
   SELECT * FROM daily_reports;  # 应该只返回该用户可见的数据

# 解决方案：
- 确认Supabase JWT配置正确
- 检查user_profiles表中用户角色设置
- 验证RLS策略的WHERE条件
```

**问题3: 内存占用过高**
```bash
# 排查步骤：
1. 查看容器资源使用
   docker stats

2. 检查数据库连接泄漏
   psql -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

3. 查看慢查询
   psql -c "SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# 解决方案：
- 限制Docker容器内存（docker-compose.yml中设置mem_limit）
- 关闭无用的数据库连接
- 优化慢查询（添加索引、重写SQL）
```

**问题4: API响应缓慢**
```bash
# 排查步骤：
1. 查看API响应时间（Prometheus metrics）
   curl http://localhost:8000/metrics | grep http_request_duration

2. 启用SQL查询日志
   # backend/.env
   DATABASE_ECHO=true  # SQLAlchemy打印SQL

3. 使用APM工具追踪（Sentry, New Relic等）

# 解决方案：
- 添加Redis缓存层
- 优化数据库查询（N+1问题）
- 启用数据库连接池预热
- 考虑使用CDN加速静态资源
```

---

### 6. 监控和运维配置

#### 后端监控配置
```python
# 监控中间件
from fastapi import Request
import time
import logging
from prometheus_client import Counter, Histogram, generate_latest

# Prometheus指标
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    # 记录指标
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    REQUEST_DURATION.observe(time.time() - start_time)

    return response

# 健康检查端点
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.2.0",
        "environment": os.getenv("API_ENV", "development")
    }
```

### 3. 传统部署架构（备用方案）
```
┌─────────────────────────────────────────────────────────────┐
│                      负载均衡层                              │
│                   Nginx Reverse Proxy                       │
│                   SSL Termination                           │
│                   Rate Limiting                             │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      应用服务层                              │
│  ┌─────────────┐              ┌─────────────┐               │
│  │  Frontend   │              │   Backend    │               │
│  │ Next.js App │              │ FastAPI App  │               │
│  └─────────────┘              └─────────────┘               │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      数据服务层                              │
│  ┌─────────────┐              ┌─────────────┐               │
│  │ PostgreSQL  │              │    Redis     │               │
│  │ Supabase    │              │    Cache     │               │
│  └─────────────┘              └─────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

### 2. 监控配置
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ai-ad-spend-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

rule_files:
  - "alert_rules.yml"
```

### 3. 告警规则
```yaml
# alert_rules.yml
groups:
  - name: application
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "应用错误率过高"

      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "数据库连接失败"
```

### 4. Nginx配置
```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name yourdomain.com;

        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

---

## 十二、开发阶段划分 ⚠️

> **说明**: 项目采用P0/P1/P2优先级分阶段开发，确保核心功能优先上线。

### P0阶段：核心业务功能（3-4周）

**目标**: 完成核心业务流程，支持基本运营。

**核心模块**:
1. **用户认证和权限系统**（Supabase Auth + RLS）
2. **项目管理**（创建项目、分配经理、预算管理）
3. **广告账户管理**（账户分配、状态管理）
4. **日报管理**（提交→审核→确认完整流程）
5. **充值管理**（申请→审核→支付→确认完整流程）

**验收标准**:
- ✅ 5种角色权限控制生效
- ✅ 日报和充值的完整业务流程可用
- ✅ RLS策略全部启用并测试通过
- ✅ API响应格式统一，错误码规范

---

### P1阶段：财务和数据（2-3周）

**目标**: 完善财务管理和数据分析功能。

**核心模块**:
1. **对账模块**（自动对账、差异分析、对账报告）
2. **财务管理**（预算分析、成本追踪、ROI计算）
3. **数据导入**（批量导入日报、数据清洗验证）
4. **基础报表**（消耗报表、转化报表、项目报表）

**验收标准**:
- ✅ 财务对账流程完整且准确
- ✅ 数据导入支持批量操作和错误提示
- ✅ 报表数据准确，支持导出

---

### P2阶段：AI和自动化（2-3周）

**目标**: 引入AI功能和自动化通知。

**核心模块**:
1. **AI异常检测**（消耗异常、账户异常监控）
2. **账户寿命预测**（基于历史数据预测）
3. **自动化通知**（邮件通知、站内消息）
4. **高级报表**（多维度分析、自定义报表）

**验收标准**:
- ✅ AI检测准确率>80%
- ✅ 通知及时送达（延迟<5分钟）
- ✅ 高级报表支持多维度筛选

---

### P3阶段：性能和扩展（1-2周）

**目标**: 优化性能，完善监控和容灾。

**核心任务**:
1. **性能优化**（数据库查询优化、Redis缓存）
2. **监控告警**（Prometheus + Grafana）
3. **容灾备份**（自动备份、恢复演练）
4. **API文档**（完整API文档和使用示例）

**验收标准**:
- ✅ API响应时间<200ms（P95）
- ✅ 监控覆盖率>90%
- ✅ 备份恢复流程验证通过

---

## 十三、验收标准

### 功能验收标准
- ✅ **核心流程完整**：日报提交→审核→数据确认；充值申请→审核→支付→入账
- ✅ **权限控制严格**：所有操作都有权限验证，RLS策略生效
- ✅ **状态机正确**：所有状态转换都符合业务规则，不允许跳级
- ✅ **数据一致性**：所有资金表都包含完整的外键追溯

### 技术验收标准
- ✅ **API响应统一**：所有API都遵循统一的响应格式和错误码规范
- ✅ **日志记录完整**：所有写操作都记录操作日志，支持审计追踪
- ✅ **性能达标**：API响应时间<200ms，数据库查询优化到位
- ✅ **安全配置**：JWT、CORS、限流等安全措施配置完善

### 运维验收标准
- ✅ **监控覆盖**：关键业务指标、系统性能都有监控覆盖
- ✅ **告警及时**：异常情况能及时发现和通知
- ✅ **备份可靠**：数据备份和恢复流程经过验证
- ✅ **部署自动化**：支持一键部署和回滚

### 文档验收标准
- ✅ **API文档完整**：所有接口都有详细的文档和示例
- ✅ **部署文档清晰**：部署步骤清晰，配置文件完整
- ✅ **运维手册详细**：故障处理、性能调优指南完善
- ✅ **代码规范统一**：代码风格统一，注释完整

### AI辅助开发验收标准
- ✅ **AI代码质量**：AI生成的代码符合项目规范，通过代码审查
- ✅ **测试覆盖率**：AI生成的测试用例覆盖95%以上代码路径
- ✅ **性能基准达标**：AI优化的代码满足性能要求，响应时间<200ms
- ✅ **安全扫描通过**：AI自动安全扫描无高危漏洞，通过安全审计
- ✅ **文档同步完整**：AI生成的文档与代码保持同步，准确可靠

---

## 十四、AI辅助开发理念（参考）

> **说明**: 本章节描述AI辅助开发的理想模式，供参考。实际开发中AI用于辅助生成代码，但需要人工审查和测试。

### 核心原则

**1. AI辅助，人工审查**
- AI可快速生成代码框架和样板代码
- 所有AI生成的代码必须经过人工审查
- 关键业务逻辑需要人工编写或深度验证

**2. 质量优先**
- AI生成的代码必须通过测试覆盖率要求（80%+）
- 必须符合项目代码规范和安全标准
- 必须经过安全扫描，无高危漏洞

**3. 约束驱动**
- 通过本文档约束AI生成代码的质量
- 强制规则（技术栈、角色名、错误码）必须遵守
- 推荐模式（代码结构、命名规范）应该遵循

**4. 迭代优化**
- AI生成代码 → 人工审查 → 修正优化 → 测试验证
- 持续积累最佳实践，更新文档约束
- 提升AI辅助开发的准确率和效率

### 适用场景

**AI辅助生成**:
- ✅ CRUD API接口（参考第八章模块示例）
- ✅ 数据模型定义（参考第三章表结构）
- ✅ 测试用例（参考现有test文件）
- ✅ API文档（根据代码注释生成）

**人工编写**:
- ⚠️ 复杂业务逻辑（状态机、对账算法等）
- ⚠️ 安全关键代码（认证、权限、加密等）
- ⚠️ 性能优化代码（缓存策略、数据库优化等）
- ⚠️ 架构设计决策

### 质量保证

**代码审查清单**:
1. 是否符合本文档的强制约束？
2. 是否使用正确的角色名和错误码？
3. 是否包含必要的权限检查？
4. 是否有充分的错误处理？
5. 是否有对应的测试用例？
6. 是否符合项目代码规范？

（详细的AI开发流程和代码示例已移至项目Wiki，供需要时参考）

---

## 十五、开发规范快速参考

### 1. 需求描述规范

**清晰的需求要包含**:
- 功能目标（做什么）
- 用户角色（谁使用）
- 业务流程（怎么做）
- 技术要求（状态机、权限、日志等）

**示例**:
> 实现充值申请的三级审批流程，包含投手提交(draft→pending)、数据员初审(pending→approved/rejected)、财务终审支付(approved→paid→posted)三个步骤。

### 2. 代码审查清单

**强制检查项**:
- [ ] 使用正确的5个角色名（admin, account_manager, data_operator, finance, media_buyer）
- [ ] 使用标准错误码（AuthErrorCodes.XXX.code）
- [ ] 返回标准响应格式（success, data/error, message, code）
- [ ] 不直接操作auth.users表
- [ ] 包含权限检查（@Depends(get_current_user)）
- [ ] 添加审计日志（关键操作）

**推荐检查项**:
- [ ] 使用Service层处理业务逻辑
- [ ] 添加Pydantic模型验证
- [ ] 编写测试用例（覆盖率>80%）
- [ ] 添加代码注释和文档字符串

### 3. 常见错误预防

**错误1: 角色名错误**
```python
# ❌ 错误
if user.role == "data_clerk":  # 旧名称

# ✅ 正确
if user.role == "data_operator":
```

**错误2: 硬编码错误码**
```python
# ❌ 错误
raise HTTPException(400, "邮箱已存在")

# ✅ 正确
return error_response(
    code=AuthErrorCodes.EMAIL_ALREADY_EXISTS.code,
    message="邮箱已被注册",
    status_code=400
)
```

**错误3: 直接操作auth.users**
```python
# ❌ 错误
user = db.query(User).filter(User.email == email).first()

# ✅ 正确
user_profile = db.query(UserProfile).filter(...).first()
```

### 4. 测试要求

**必需测试**:
- API测试（每个端点）
- 权限测试（不同角色）
- 状态机测试（所有转换）
- 错误处理测试（异常情况）

**覆盖率要求**:
- API接口: > 80%
- 关键业务逻辑: 100%
- 状态机转换: 100%

### 5. 安全检查

**必须避免**:
- SQL注入（使用ORM参数化查询）
- XSS攻击（前端输出转义）
- 权限绕过（每个接口检查权限）
- 敏感信息泄露（日志脱敏）
- 硬编码密钥（使用环境变量）

**安全最佳实践**:
- 所有API使用JWT认证
- 敏感操作记录审计日志
- 密码由Supabase Auth安全管理
- 配置CORS白名单
- 应用层RBAC权限控制

---

## 📚 相关文档

- [SYSTEM_OVERVIEW.md](./SYSTEM_OVERVIEW.md) - 系统架构详细说明
- [BACKEND_API_GUIDE.md](./BACKEND_API_GUIDE.md) - 后端API开发指南
- [DATA_SCHEMA.md](./DATA_SCHEMA.md) - 数据库详细设计
- [FRONTEND_GUIDE.md](./FRONTEND_GUIDE.md) - 前端开发指南
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - 部署运维指南
- [SECURITY_CONFIG.md](./SECURITY_CONFIG.md) - 安全配置规范
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) - 测试策略文档
- [MONITORING_OPS.md](./MONITORING_OPS.md) - 监控运维文档
- [STATE_MACHINE.md](./STATE_MACHINE.md) - 状态机设计文档

---

**文档版本**: v2.3 本地开发版
**最后更新**: 2025-11-15
**下次审查**: AI技术栈重大更新时
**维护责任人**: 系统架构团队
**新增特色**: 整合Next.js 16本地前端开发和Claude Code后端AI协作的完整技术规范，新增6大核心章节AI约束提示
