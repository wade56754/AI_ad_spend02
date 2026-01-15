# AI 广告代投系统 - 功能任务卡文档

> **文档版本**: v2.0
> **生成日期**: 2025-12-27
> **基准文档**: MASTER.md v4.9, BUSINESS_RULES.md v5.2, STATE_MACHINE.md v2.9, DATA_SCHEMA.md v5.11, PRD v5.1
> **用途**: AI 编程开发任务分解与跟踪
> **变更说明**: 修复 P0-P2 缺陷，增加 Phase 分组、模块依赖图、测试要求
> **归档说明**: 文中历史引用统一以 PRD v5.1 与 DATA_SCHEMA.md §3.4.4 为准

---

## 文档目录

1. [模块依赖关系图](#模块依赖关系图)
2. [Phase 分组视图](#phase-分组视图)
3. [M1 认证模块 (AUTH)](#m1-认证模块-auth)
4. [M2 用户模块 (USER)](#m2-用户模块-user)
5. [M3 项目模块 (PROJ)](#m3-项目模块-proj)
6. [M4 渠道模块 (CHANNEL)](#m4-渠道模块-channel)
7. [M5 广告账户模块 (ACCT)](#m5-广告账户模块-acct)
8. [M6 日报模块 (RPT)](#m6-日报模块-rpt)
9. [M7 充值模块 (FIN)](#m7-充值模块-fin)
10. [M8 账本模块 (LEDGER)](#m8-账本模块-ledger)
11. [M9 对账模块 (RECON)](#m9-对账模块-recon)
12. [M10 利润模块 (PROFIT)](#m10-利润模块-profit)
13. [M11 周报模块 (WEEKLY)](#m11-周报模块-weekly)
14. [附录](#附录)

---

## SoT 版本对齐表（任务卡基准）

| 文档 | 版本 | 路径 | 状态 |
|------|------|------|------|
| MASTER.md | v4.9 | docs/sot/MASTER.md | Frozen |
| STATE_MACHINE.md | v2.9 | docs/sot/STATE_MACHINE.md | Frozen |
| DATA_SCHEMA.md | v5.11 | docs/sot/DATA_SCHEMA.md | Frozen |
| BUSINESS_RULES.md | v5.2 | docs/sot/BUSINESS_RULES.md | Frozen |
| ERROR_CODES_SOT.md | v2.2 | docs/sot/ERROR_CODES_SOT.md | Frozen |
| AUTH_SPEC.md | v2.2 | docs/sot/AUTH_SPEC.md | Frozen |
| 账本规则 | merged | docs/sot/DATA_SCHEMA.md §3.4.4 | Frozen |
| API_SOT.md | v9.7 | docs/sot/API_SOT.md | Frozen |
| PRD_v5.1.md | v5.1 | docs/PRD_v5.1.md | Frozen |

> 说明：账本规则以 DATA_SCHEMA.md §3.4.4 为唯一来源。

---

## 角色白名单（6 角色）

> **来源**: MASTER.md v4.9 §2.4, PRD v5.1 §2.2

| 角色ID | 中文名 | 职责范围 |
|--------|--------|----------|
| `ceo` | 老板 | 资金安全、公司盈亏、最终决策 |
| `project_owner` | 项目负责人 | 项目盈亏、日报审核、统计实际消耗、确认有效粉 |
| `finance` | 财务 | 资金出入准确、数据真实、对账 |
| `pitcher` | 投手 | CPL 达标、日报准确、执行投放 |
| `account_manager` | 户管 | 账户分配、账户状态监控 |
| `admin` | 管理员 | 系统配置（不参与业务） |

⚠️ **禁止使用的旧角色**: `supervisor`（已合并到 project_owner）、`data_operator`（已移除）、`media_buyer`（技术层角色，业务层用 pitcher）

---

## 模块依赖关系图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         模块依赖关系                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   M1 认证 ──────► M2 用户 ──────► M3 项目 ──────► M4 渠道               │
│                      │              │    │           │                  │
│                      │              │    │           ▼                  │
│                      │              │    └──────► M5 账户               │
│                      │              │                │                  │
│                      │              ▼                ▼                  │
│                      │          M7 充值 ◄────────► M6 日报              │
│                      │              │                │                  │
│                      │              └────────┬───────┘                  │
│                      │                       │                          │
│                      │                       ▼                          │
│                      │                   M8 账本                        │
│                      │                    │   │                         │
│                      │                    ▼   ▼                         │
│                      │              M9 对账   M10 利润                  │
│                      │                                                  │
│                      └──────────────────► M11 周报                      │
│                                                                         │
│  图例: ──► 强依赖（必须先完成）   - - ► 弱依赖（可并行）                │
└─────────────────────────────────────────────────────────────────────────┘
```

**关键路径**: M1 → M2 → M3 → M5 → M6 → M8 → M10

---

## Phase 分组视图

### Phase 1 任务清单（MVP 核心）

> Phase 1 原则：记录事实、展示状态、提示异常，**不强制阻断**

| 模块 | 任务卡 | 说明 |
|------|--------|------|
| M1 认证 | TASK-AUTH-001 ~ 005 | 全部 |
| M2 用户 | TASK-USER-001 ~ 005 | 全部 |
| M3 项目 | TASK-PROJ-001 ~ 006 | 全部 |
| M4 渠道 | TASK-CHAN-001 ~ 004 | 全部 |
| M5 账户 | TASK-ACCT-001 ~ 006 | 全部 |
| M6 日报 | TASK-RPT-001/002/003/007 | Phase 1 简化版（3 状态） |
| M7 充值 | TASK-FIN-001 ~ 007 | 全部 |
| M8 账本 | TASK-LEDGER-001 ~ 004 | 全部 |
| M10 利润 | TASK-PROFIT-001 ~ 004 | 全部 |
| M11 周报 | TASK-WEEKLY-001 ~ 003 | 全部（可选提交） |

### Phase 2 任务清单（增强功能）

> Phase 2 原则：引入约束、强制审批、考核关联

| 模块 | 任务卡 | 说明 |
|------|--------|------|
| M6 日报 | TASK-RPT-004/005/006/008/009 | 完整 8 状态机 |
| M9 对账 | TASK-RECON-001 ~ 004 | 对账批次管理 |

---

## 开发优先级说明

| 优先级 | 模块 | 说明 | 预估工时 |
|--------|------|------|----------|
| **P0** | M1 认证、M2 用户、M3 项目、M5 账户、M6 日报(Phase 1) | MVP 核心，必须先做 | 85h |
| **P1** | M4 渠道、M7 充值 | 核心业务支撑 | 32h |
| **P2** | M8 账本、M9 对账、M10 利润 | 财务闭环 | 39h |
| **P3** | M11 周报、M6 日报(Phase 2) | 管理功能 | 16h |

---

## 通用测试要求

> 每个任务卡的测试用例必须覆盖以下场景：

```markdown
### 测试要求
- □ 正向场景测试（正常流程）
- □ 负向场景测试（权限拒绝、状态非法、参数错误）
- □ 边界场景测试（空值、极值、特殊字符）
- □ 幂等性测试（重复提交）
```

---

# M1 认证模块 (AUTH)

> **规则模块**: BR-AUTH (6 条规则)
> **关联 SoT**: AUTH_SPEC.md v2.2, ERROR_CODES_SOT.md v2.2
> **优先级**: P0
> **Phase**: Phase 1

## TASK-AUTH-001: 用户登录 API

### 关联文档
- BUSINESS_RULES.md BR-AUTH-001（登录必须验证）
- AUTH_SPEC.md v2.2 §3（JWT Token 规范）
- ERROR_CODES_SOT.md v2.2（AUTH_400/AUTH_401）

### 输入
- 用户表（users）已存在
- Supabase Auth 配置完成

### 输出
- `backend/schemas/auth.py` - LoginRequest, LoginResponse, TokenPayload
- `backend/services/auth_service.py` - login(), validate_token()
- `backend/routers/auth.py` - POST /api/v1/auth/login
- `backend/tests/test_auth_api.py` - 登录测试用例

### 验收标准
- □ POST /api/v1/auth/login 返回 JWT Token
- □ Token 包含 user_id, role, exp 字段
- □ Token 有效期不超过 24 小时（BR-AUTH-002）
- □ 无效凭证返回 AUTH_400 错误码
- □ Token 过期返回 AUTH_401 错误码
- □ 测试覆盖：正向登录、错误密码、不存在用户、账户停用

---

## TASK-AUTH-002: 用户登出 API

### 关联文档
- AUTH_SPEC.md v2.2 §4（Token 失效）
- ERROR_CODES_SOT.md v2.2（AUTH_401）

### 输入
- TASK-AUTH-001 已完成

### 输出
- `backend/services/auth_service.py` - logout()
- `backend/routers/auth.py` - POST /api/v1/auth/logout
- `backend/tests/test_auth_api.py` - 登出测试用例

### 验收标准
- □ POST /api/v1/auth/logout 返回成功
- □ 登出后原 Token 失效
- □ 未认证请求返回 AUTH_401

---

## TASK-AUTH-003: Token 刷新 API

### 关联文档
- AUTH_SPEC.md v2.2 §5（Token 刷新）
- BUSINESS_RULES.md BR-AUTH-002（Token 有效期）

### 输入
- TASK-AUTH-001 已完成

### 输出
- `backend/services/auth_service.py` - refresh_token()
- `backend/routers/auth.py` - POST /api/v1/auth/refresh
- `backend/tests/test_auth_api.py` - 刷新测试用例

### 验收标准
- □ POST /api/v1/auth/refresh 返回新 Token
- □ 使用 Refresh Token 刷新（非 Access Token）
- □ 新 Token 有效期不超过 24 小时

---

## TASK-AUTH-004: 权限校验中间件

### 关联文档
- BUSINESS_RULES.md BR-AUTH-003（角色唯一性）
- BUSINESS_RULES.md BR-AUTH-004（权限继承禁止）
- MASTER.md v4.9 §2.4（6 角色定义）

### 输入
- TASK-AUTH-001 已完成
- 6 角色定义：ceo, project_owner, finance, pitcher, account_manager, admin

### 输出
- `backend/core/dependencies.py` - get_current_user(), require_role()
- `backend/core/permissions.py` - 权限常量、角色映射
- `backend/tests/test_permissions.py` - 权限测试用例

### 验收标准
- □ 实现 get_current_user 依赖注入
- □ 实现 require_role 装饰器
- □ 角色枚举仅包含 6 个合法角色
- □ 无 supervisor/data_operator/media_buyer 角色
- □ 无权限操作返回 AUTH_403

---

## TASK-AUTH-005: 职责分离校验

### 关联文档
- BUSINESS_RULES.md BR-AUTH-006（职责分离）
- MASTER.md v4.9 §9 INV-004（职责分离）

### 输入
- TASK-AUTH-004 已完成

### 输出
- `backend/core/permissions.py` - check_separation_of_duties()
- `backend/tests/test_permissions.py` - 职责分离测试

### 验收标准
- □ 日报提交者不能是审核者
- □ 充值申请者不能是审批者
- □ 违反职责分离返回 BIZ_001

---

# M2 用户模块 (USER)

> **规则模块**: BR-USER (5 条规则)
> **关联 SoT**: MASTER.md v4.9 §2.4, DATA_SCHEMA.md v5.11 §users
> **优先级**: P0
> **Phase**: Phase 1

## TASK-USER-001: 用户列表 API

### 关联文档
- BUSINESS_RULES.md BR-USER-001（角色枚举固定）
- DATA_SCHEMA.md v5.11 §users 表

### 输入
- 认证模块已完成

### 输出
- `backend/schemas/user.py` - UserResponse, UserListResponse
- `backend/services/user_service.py` - list_users()
- `backend/routers/users.py` - GET /api/v1/users
- `backend/tests/test_user_api.py` - 列表测试用例

### 验收标准
- □ GET /api/v1/users 返回用户列表
- □ 支持分页（page, page_size）
- □ 支持角色筛选
- □ 非 admin 仅能查看同项目用户

---

## TASK-USER-002: 用户详情 API

### 关联文档
- DATA_SCHEMA.md v5.11 §users 表
- ERROR_CODES_SOT.md v2.2（BIZ_002）

### 输入
- TASK-USER-001 已完成

### 输出
- `backend/services/user_service.py` - get_user()
- `backend/routers/users.py` - GET /api/v1/users/{id}
- `backend/tests/test_user_api.py` - 详情测试用例

### 验收标准
- □ GET /api/v1/users/{id} 返回用户详情
- □ 用户不存在返回 BIZ_002
- □ 包含用户角色、关联项目信息

---

## TASK-USER-003: 创建用户 API

### 关联文档
- BUSINESS_RULES.md BR-USER-002（角色不可为空）
- BUSINESS_RULES.md BR-USER-003（角色变更审计）
- AUTH_SPEC.md v2.2（密码规范）

### 输入
- TASK-USER-001 已完成

### 输出
- `backend/schemas/user.py` - UserCreate
- `backend/services/user_service.py` - create_user()
- `backend/routers/users.py` - POST /api/v1/users
- `backend/tests/test_user_api.py` - 创建测试用例

### 验收标准
- □ POST /api/v1/users 创建用户
- □ 必须指定角色（BR-USER-002）
- □ 角色仅允许 6 个合法值
- □ 密码满足强度要求（8位+大小写+数字）
- □ 仅 admin/ceo 可创建用户

---

## TASK-USER-004: 更新用户 API

### 关联文档
- BUSINESS_RULES.md BR-USER-003（角色变更审计）
- BUSINESS_RULES.md BR-USER-004（禁止自我提权）

### 输入
- TASK-USER-003 已完成

### 输出
- `backend/schemas/user.py` - UserUpdate
- `backend/services/user_service.py` - update_user()
- `backend/routers/users.py` - PUT /api/v1/users/{id}
- `backend/tests/test_user_api.py` - 更新测试用例

### 验收标准
- □ PUT /api/v1/users/{id} 更新用户
- □ 用户不能修改自己的角色（BR-USER-004）
- □ 角色变更记录审计日志
- □ 仅 admin/ceo 可修改用户

---

## TASK-USER-005: 用户停用/启用 API

### 关联文档
- DATA_SCHEMA.md v5.11 §users 表（is_active 字段）
- BUSINESS_RULES.md BR-USER-005（admin 角色限制）

### 输入
- TASK-USER-003 已完成

### 输出
- `backend/services/user_service.py` - deactivate_user(), activate_user()
- `backend/routers/users.py` - POST /api/v1/users/{id}/deactivate, POST /api/v1/users/{id}/activate
- `backend/tests/test_user_api.py` - 停用/启用测试用例

### 验收标准
- □ 停用后用户无法登录
- □ admin 角色不能被停用
- □ 仅 admin/ceo 可执行操作
- □ 记录审计日志

---

# M3 项目模块 (PROJ)

> **规则模块**: BR-PROJ (8 条规则)
> **关联 SoT**: STATE_MACHINE.md v2.9 §5, DATA_SCHEMA.md v5.11 §projects
> **优先级**: P0
> **Phase**: Phase 1

## TASK-PROJ-001: 项目列表 API

### 关联文档
- DATA_SCHEMA.md v5.11 §projects 表
- STATE_MACHINE.md v2.9 §5（项目状态机）

### 输入
- 用户模块已完成

### 输出
- `backend/schemas/project.py` - ProjectResponse, ProjectListResponse
- `backend/services/project_service.py` - list_projects()
- `backend/routers/projects.py` - GET /api/v1/projects
- `backend/tests/test_project_api.py` - 列表测试用例

### 验收标准
- □ GET /api/v1/projects 返回项目列表
- □ 支持状态筛选（draft/active/suspended/archived）
- □ pitcher 仅能看到已分配的项目
- □ project_owner 仅能看到负责的项目

---

## TASK-PROJ-002: 项目详情 API

### 关联文档
- DATA_SCHEMA.md v5.11 §projects 表
- BUSINESS_RULES.md BR-PROJ-001（项目必须有负责人）

### 输入
- TASK-PROJ-001 已完成

### 输出
- `backend/services/project_service.py` - get_project()
- `backend/routers/projects.py` - GET /api/v1/projects/{id}
- `backend/tests/test_project_api.py` - 详情测试用例

### 验收标准
- □ GET /api/v1/projects/{id} 返回项目详情
- □ 包含项目负责人（owner_id → user）
- □ 包含项目状态、预算、结算模式
- □ 项目不存在返回 BIZ_002

---

## TASK-PROJ-003: 创建项目 API

### 关联文档
- BUSINESS_RULES.md BR-PROJ-001（项目必须有负责人）
- BUSINESS_RULES.md BR-PROJ-002（结算模式不可变）
- BUSINESS_RULES.md BR-PROJ-006（预算必须大于零）
- STATE_MACHINE.md v2.9 §5（初始状态 draft）

### 输入
- TASK-PROJ-001 已完成
- 用户模块已完成

### 输出
- `backend/schemas/project.py` - ProjectCreate
- `backend/services/project_service.py` - create_project()
- `backend/routers/projects.py` - POST /api/v1/projects
- `backend/tests/test_project_api.py` - 创建测试用例

### 验收标准
- □ POST /api/v1/projects 创建项目
- □ 必须指定 owner_id（BR-PROJ-001）
- □ 必须指定结算模式（per_lead/fee_rate）
- □ 预算必须大于零（BR-PROJ-006）
- □ per_lead 模式必须指定 unit_price > 0（BR-PROJ-007）
- □ fee_rate 模式必须指定 service_rate 0-100%（BR-PROJ-008）
- □ 初始状态为 draft
- □ 仅 admin/ceo 可创建

---

## TASK-PROJ-004: 更新项目 API

### 关联文档
- BUSINESS_RULES.md BR-PROJ-002（结算模式不可变）
- STATE_MACHINE.md v2.9 §5（状态流转）

### 输入
- TASK-PROJ-003 已完成

### 输出
- `backend/schemas/project.py` - ProjectUpdate
- `backend/services/project_service.py` - update_project()
- `backend/routers/projects.py` - PUT /api/v1/projects/{id}
- `backend/tests/test_project_api.py` - 更新测试用例

### 验收标准
- □ PUT /api/v1/projects/{id} 更新项目
- □ 结算模式（settlement_type）不可修改（BR-PROJ-002）
- □ archived 状态项目不可修改（BR-PROJ-004）
- □ 仅 admin/ceo/project_owner 可修改

---

## TASK-PROJ-005: 项目状态流转 API

### 关联文档
- STATE_MACHINE.md v2.9 §5（项目状态机）
- BUSINESS_RULES.md BR-PROJ-003（状态流转合法性）
- BUSINESS_RULES.md BR-PROJ-004（归档不可逆）

### 输入
- TASK-PROJ-003 已完成

### 输出
- `backend/services/project_service.py` - activate_project(), suspend_project(), archive_project()
- `backend/routers/projects.py` - POST /api/v1/projects/{id}/activate, POST /api/v1/projects/{id}/suspend, POST /api/v1/projects/{id}/archive
- `backend/tests/test_project_api.py` - 状态流转测试用例

### 验收标准
- □ draft → active（激活）
- □ active → suspended（暂停）
- □ suspended → active（恢复）
- □ active/suspended → archived（归档）
- □ archived 不可逆，仅 admin 可回退 [AUDIT]
- □ 非法状态转换返回 STATE_400

---

## TASK-PROJ-006: 项目成员管理 API

### 关联文档
- DATA_SCHEMA.md v5.11 §project_members 表
- BUSINESS_RULES.md BR-PROJ-001（项目必须有负责人）

### 输入
- TASK-PROJ-003 已完成
- 用户模块已完成

### 输出
- `backend/schemas/project_member.py` - ProjectMemberCreate, ProjectMemberResponse
- `backend/services/project_member_service.py` - add_member(), remove_member(), list_members()
- `backend/routers/project_members.py` - GET/POST/DELETE /api/v1/projects/{id}/members
- `backend/tests/test_project_member_api.py` - 成员管理测试用例

### 验收标准
- □ GET /api/v1/projects/{id}/members 返回成员列表
- □ POST /api/v1/projects/{id}/members 添加成员
- □ DELETE /api/v1/projects/{id}/members/{user_id} 移除成员
- □ 项目负责人不能被移除
- □ 仅 admin/ceo/project_owner 可管理成员

---

# M4 渠道模块 (CHANNEL)

> **规则模块**: BR-ACCT 扩展（渠道属于账户管理范畴）
> **关联 SoT**: STATE_MACHINE.md v2.9 §6, DATA_SCHEMA.md v5.11 §channels
> **优先级**: P1
> **Phase**: Phase 1

## TASK-CHAN-001: 渠道列表 API

### 关联文档
- STATE_MACHINE.md v2.9 §6.1（渠道状态机）
- DATA_SCHEMA.md v5.11 §channels 表

### 输入
- 认证模块已完成

### 输出
- `backend/schemas/channel.py` - ChannelResponse, ChannelListResponse
- `backend/services/channel_service.py` - list_channels()
- `backend/routers/channels.py` - GET /api/v1/channels
- `backend/tests/test_channel_api.py` - 列表测试用例

### 验收标准
- □ GET /api/v1/channels 返回渠道列表
- □ 支持状态筛选（active/inactive）
- □ 包含渠道名称、平台类型、费率信息

---

## TASK-CHAN-002: 创建渠道 API

### 关联文档
- STATE_MACHINE.md v2.9 §6.1（初始状态 active）
- DATA_SCHEMA.md v5.11 §channels 表

### 输入
- TASK-CHAN-001 已完成

### 输出
- `backend/schemas/channel.py` - ChannelCreate
- `backend/services/channel_service.py` - create_channel()
- `backend/routers/channels.py` - POST /api/v1/channels
- `backend/tests/test_channel_api.py` - 创建测试用例

### 验收标准
- □ POST /api/v1/channels 创建渠道
- □ 初始状态为 active
- □ 必须指定手续费率
- □ 仅 admin/account_manager 可创建

---

## TASK-CHAN-003: 渠道评审 API

### 关联文档
- STATE_MACHINE.md v2.9 §6.2（渠道评审状态机）

### 输入
- TASK-CHAN-002 已完成

### 输出
- `backend/schemas/channel_review.py` - ChannelReviewCreate, ChannelReviewResponse
- `backend/services/channel_review_service.py` - create_review(), approve_review(), reject_review()
- `backend/routers/channel_reviews.py` - POST/PUT /api/v1/channels/{id}/reviews
- `backend/tests/test_channel_review_api.py` - 评审测试用例

### 验收标准
- □ 状态流转：draft → pending → approved/rejected
- □ 提交：account_manager/pitcher
- □ 审核：project_owner/admin [AUDIT]
- □ 终态不可回退

---

## TASK-CHAN-004: 渠道开户申请 API

### 关联文档
- STATE_MACHINE.md v2.9 §6.3（开户申请状态机）

### 输入
- TASK-CHAN-002 已完成

### 输出
- `backend/schemas/channel_account_request.py` - ChannelAccountRequestCreate
- `backend/services/channel_account_request_service.py` - create_request(), approve_request()
- `backend/routers/channel_account_requests.py` - POST/PUT /api/v1/channels/{id}/account-requests
- `backend/tests/test_channel_account_request_api.py` - 开户申请测试用例

### 验收标准
- □ 状态流转：draft → pending → approved/rejected
- □ 提交：account_manager/pitcher
- □ 审批：account_manager/admin [AUDIT]
- □ 批准后自动创建 ad_account

---

# M5 广告账户模块 (ACCT)

> **规则模块**: BR-ACCT (6 条规则)
> **关联 SoT**: STATE_MACHINE.md v2.9 §7, DATA_SCHEMA.md v5.11 §ad_accounts
> **优先级**: P0
> **Phase**: Phase 1

## TASK-ACCT-001: 账户列表 API

### 关联文档
- BUSINESS_RULES.md BR-ACCT-001（账户必须归属渠道）
- STATE_MACHINE.md v2.9 §7.1（账户状态机）
- DATA_SCHEMA.md v5.11 §ad_accounts 表

### 输入
- 渠道模块已完成
- 项目模块已完成

### 输出
- `backend/schemas/ad_account.py` - AdAccountResponse, AdAccountListResponse
- `backend/services/ad_account_service.py` - list_ad_accounts()
- `backend/routers/ad_accounts.py` - GET /api/v1/ad-accounts
- `backend/tests/test_ad_account_api.py` - 列表测试用例

### 验收标准
- □ GET /api/v1/ad-accounts 返回账户列表
- □ 支持状态筛选（new/testing/active/suspended/dead/archived）
- □ 支持渠道、项目、投手筛选
- □ pitcher 仅能看到已分配的账户

---

## TASK-ACCT-002: 账户详情 API

### 关联文档
- DATA_SCHEMA.md v5.11 §ad_accounts 表
- BUSINESS_RULES.md BR-ACCT-004（余额不可为负）

### 输入
- TASK-ACCT-001 已完成

### 输出
- `backend/services/ad_account_service.py` - get_ad_account()
- `backend/routers/ad_accounts.py` - GET /api/v1/ad-accounts/{id}
- `backend/tests/test_ad_account_api.py` - 详情测试用例

### 验收标准
- □ GET /api/v1/ad-accounts/{id} 返回账户详情
- □ 包含余额、状态、关联渠道/项目/投手
- □ 账户不存在返回 BIZ_002

---

## TASK-ACCT-003: 创建账户 API

### 关联文档
- BUSINESS_RULES.md BR-ACCT-001（账户必须归属渠道）
- STATE_MACHINE.md v2.9 §7.1（初始状态 new）

### 输入
- TASK-ACCT-001 已完成
- 渠道模块已完成

### 输出
- `backend/schemas/ad_account.py` - AdAccountCreate
- `backend/services/ad_account_service.py` - create_ad_account()
- `backend/routers/ad_accounts.py` - POST /api/v1/ad-accounts
- `backend/tests/test_ad_account_api.py` - 创建测试用例

### 验收标准
- □ POST /api/v1/ad-accounts 创建账户
- □ 必须指定 channel_id（BR-ACCT-001）
- □ 初始状态为 new
- □ 初始余额为 0
- □ 仅 admin/account_manager 可创建

---

## TASK-ACCT-004: 账户分配 API

### 关联文档
- BUSINESS_RULES.md BR-ACCT-002（账户分配唯一性）
- BUSINESS_RULES.md BR-ACCT-005（分配记录审计）

### 输入
- TASK-ACCT-003 已完成
- 用户模块已完成
- 项目模块已完成

### 输出
- `backend/schemas/ad_account.py` - AdAccountAssign
- `backend/services/ad_account_service.py` - assign_account()
- `backend/routers/ad_accounts.py` - POST /api/v1/ad-accounts/{id}/assign
- `backend/tests/test_ad_account_api.py` - 分配测试用例

### 验收标准
- □ POST /api/v1/ad-accounts/{id}/assign 分配账户
- □ 必须指定 project_id 和 pitcher_id
- □ 同一账户同一时间只能分配给一个投手（BR-ACCT-002）
- □ 分配变更记录审计日志（BR-ACCT-005）
- □ 仅 admin/account_manager 可分配

---

## TASK-ACCT-005: 账户状态流转 API

### 关联文档
- STATE_MACHINE.md v2.9 §7.1（账户状态机）
- BUSINESS_RULES.md BR-ACCT-006（停用账户禁止操作）

### 输入
- TASK-ACCT-003 已完成

### 输出
- `backend/services/ad_account_service.py` - activate_account(), suspend_account(), mark_dead(), archive_account()
- `backend/routers/ad_accounts.py` - POST /api/v1/ad-accounts/{id}/activate, suspend, mark-dead, archive
- `backend/tests/test_ad_account_api.py` - 状态流转测试用例

### 验收标准
- □ 状态流转：new → testing → active → suspended → dead/archived
- □ 终态（dead/archived）仅 admin 可回退 [AUDIT]
- □ 非法状态转换返回 STATE_400
- □ 记录状态变更历史（account_status_history）

---

## TASK-ACCT-006: 账户预警 API

### 关联文档
- STATE_MACHINE.md v2.9 §7.3（账户预警状态机）

### 输入
- TASK-ACCT-003 已完成

### 输出
- `backend/schemas/account_alert.py` - AccountAlertCreate, AccountAlertResponse
- `backend/services/account_alert_service.py` - create_alert(), ack_alert(), resolve_alert()
- `backend/routers/account_alerts.py` - GET/POST/PUT /api/v1/ad-accounts/{id}/alerts
- `backend/tests/test_account_alert_api.py` - 预警测试用例

### 验收标准
- □ 状态流转：open → ack → resolved
- □ 创建：system/project_owner
- □ 确认/解决：account_manager/admin [AUDIT]
- □ 预警类型支持：余额不足、异常消耗等

---

# M6 日报模块 (RPT)

> **规则模块**: BR-RPT (9 条规则)
> **关联 SoT**: STATE_MACHINE.md v2.9 §8, DATA_SCHEMA.md v5.11 §daily_reports
> **优先级**: P0
> **Phase**: Phase 1 (简化版) + Phase 2 (完整版)

## Phase 1 日报状态机（3 状态）

```python
# Phase 1 简化版状态
PHASE1_DAILY_REPORT_STATUS = ["raw_submitted", "trend_ok", "final_confirmed"]

# Phase 1 状态流转
raw_submitted → trend_ok → final_confirmed
```

## Phase 2 日报状态机（8 状态）

```python
# Phase 2 完整版状态
PHASE2_DAILY_REPORT_STATUS = [
    "raw_submitted", "trend_pending", "trend_ok", "trend_flagged",
    "trend_resolved", "final_pending", "final_confirmed", "final_locked"
]
```

---

## TASK-RPT-001: 日报列表 API

> **Phase**: Phase 1

### 关联文档
- STATE_MACHINE.md v2.9 §8（日报状态机）
- DATA_SCHEMA.md v5.11 §daily_reports 表

### 输入
- 账户模块已完成
- 项目模块已完成

### 输出
- `backend/schemas/daily_report.py` - DailyReportResponse, DailyReportListResponse
- `backend/services/daily_report_service.py` - list_daily_reports()
- `backend/routers/daily_reports.py` - GET /api/v1/daily-reports
- `backend/tests/test_daily_report_api.py` - 列表测试用例

### 验收标准
- □ GET /api/v1/daily-reports 返回日报列表
- □ 支持日期范围、状态、项目、投手筛选
- □ pitcher 仅能看到自己提交的日报
- □ project_owner 能看到负责项目的所有日报

---

## TASK-RPT-002: 日报详情 API

> **Phase**: Phase 1

### 关联文档
- DATA_SCHEMA.md v5.11 §daily_reports 表
- BUSINESS_RULES.md BR-RPT-005（三数据流定义）

### 输入
- TASK-RPT-001 已完成

### 输出
- `backend/services/daily_report_service.py` - get_daily_report()
- `backend/routers/daily_reports.py` - GET /api/v1/daily-reports/{id}
- `backend/tests/test_daily_report_api.py` - 详情测试用例

### 验收标准
- □ GET /api/v1/daily-reports/{id} 返回日报详情
- □ 包含 raw/real/final 三数据流字段
- □ 包含状态、CPL 计算值、异常标记
- □ 日报不存在返回 BIZ_002

---

## TASK-RPT-003: 提交日报 API

> **Phase**: Phase 1

### 关联文档
- BUSINESS_RULES.md BR-RPT-001（日报提交人）
- BUSINESS_RULES.md BR-RPT-006（raw 数据提交者）
- STATE_MACHINE.md v2.9 §8（初始状态 raw_submitted）

### 输入
- TASK-RPT-001 已完成
- 账户模块已完成

### 输出
- `backend/schemas/daily_report.py` - DailyReportCreate
- `backend/services/daily_report_service.py` - create_daily_report()
- `backend/routers/daily_reports.py` - POST /api/v1/daily-reports
- `backend/tests/test_daily_report_api.py` - 提交测试用例

### 验收标准
- □ POST /api/v1/daily-reports 提交日报
- □ 必须由 pitcher 提交（BR-RPT-001）
- □ 必须指定 ad_account_id, date, spend, conversions
- □ 同一账户同一日期不可重复提交
- □ 初始状态为 raw_submitted
- □ 记录审计日志 [AUDIT]

---

## TASK-RPT-004: 趋势检查 API（Phase 2）

> **Phase**: Phase 2
> **启用条件**: Feature Flag `ENABLE_FULL_DAILY_REPORT_SM=true`

### 关联文档
- STATE_MACHINE.md v2.9 §8.2（Phase 2 完整版）
- BUSINESS_RULES.md BR-RPT-004（状态流转合法性）

### 输入
- TASK-RPT-003 已完成
- **Phase 2 启用条件**：Feature Flag ENABLE_FULL_DAILY_REPORT_SM=true

### 输出
- `backend/services/daily_report_service.py` - trigger_trend_check()
- `backend/routers/daily_reports.py` - POST /api/v1/daily-reports/{id}/trend-check
- `backend/tests/test_daily_report_api.py` - 趋势检查测试用例

### 验收标准
- □ POST /api/v1/daily-reports/{id}/trend-check 触发趋势检查
- □ 系统自动执行：raw_submitted → trend_pending → trend_ok/trend_flagged
- □ 异常检测规则：TF-001 粉数骤降、TF-002 CPL 超标、TF-003 消耗异常
- □ Phase 1 跳过此步骤（直接返回成功）

---

## TASK-RPT-005: 趋势复核 API（Phase 2）

> **Phase**: Phase 2
> **启用条件**: Feature Flag `ENABLE_FULL_DAILY_REPORT_SM=true`

### 关联文档
- STATE_MACHINE.md v2.9 §8.2（trend_flagged → trend_resolved）
- BUSINESS_RULES.md BR-RPT-002（日报审核人）

### 输入
- TASK-RPT-004 已完成
- **Phase 2 启用条件**：Feature Flag ENABLE_FULL_DAILY_REPORT_SM=true

### 输出
- `backend/schemas/daily_report.py` - TrendResolveRequest
- `backend/services/daily_report_service.py` - resolve_trend()
- `backend/routers/daily_reports.py` - POST /api/v1/daily-reports/{id}/trend-resolve
- `backend/tests/test_daily_report_api.py` - 趋势复核测试用例

### 验收标准
- □ POST /api/v1/daily-reports/{id}/trend-resolve 趋势复核
- □ 必须由 project_owner 执行（BR-RPT-002）
- □ 必须填写 trend_resolution_note
- □ 状态流转：trend_flagged → trend_resolved
- □ Phase 1 跳过此步骤

---

## TASK-RPT-006: 录入实际消耗 API（Phase 2）

> **Phase**: Phase 2
> **启用条件**: Feature Flag `ENABLE_FULL_DAILY_REPORT_SM=true`

### 关联文档
- BUSINESS_RULES.md BR-RPT-007（real 数据提交者）
- STATE_MACHINE.md v2.9 §8.4（real_spend 字段）

### 输入
- TASK-RPT-003 已完成
- **Phase 2 启用条件**

### 输出
- `backend/schemas/daily_report.py` - RealSpendUpdate
- `backend/services/daily_report_service.py` - update_real_spend()
- `backend/routers/daily_reports.py` - PUT /api/v1/daily-reports/{id}/real-spend
- `backend/tests/test_daily_report_api.py` - 实际消耗测试用例

### 验收标准
- □ PUT /api/v1/daily-reports/{id}/real-spend 录入实际消耗
- □ 必须由 project_owner 执行（BR-RPT-007）
- □ Phase 1 不使用此字段

---

## TASK-RPT-007: 确认最终数据 API

> **Phase**: Phase 1 + Phase 2

### 关联文档
- BUSINESS_RULES.md BR-RPT-008（final 数据提交者）
- STATE_MACHINE.md v2.9 §8（final_pending → final_confirmed）

### 输入
- TASK-RPT-003 已完成

### 输出
- `backend/schemas/daily_report.py` - FinalConfirmRequest
- `backend/services/daily_report_service.py` - confirm_final()
- `backend/routers/daily_reports.py` - PUT /api/v1/daily-reports/{id}/final-confirm
- `backend/tests/test_daily_report_api.py` - 确认最终数据测试用例

### 验收标准
- □ PUT /api/v1/daily-reports/{id}/final-confirm 确认最终数据
- □ 必须由 project_owner 执行（BR-RPT-008）
- □ Phase 1：raw_submitted → trend_ok → final_confirmed
- □ Phase 2：final_pending → final_confirmed
- □ 记录审计日志 [AUDIT]

---

## TASK-RPT-008: 计费锁定 API（Phase 2）

> **Phase**: Phase 2
> **启用条件**: Feature Flag `ENABLE_FULL_DAILY_REPORT_SM=true`

### 关联文档
- STATE_MACHINE.md v2.9 §8（final_confirmed → final_locked）
- BUSINESS_RULES.md BR-RPT-009（final 数据不可改）

### 输入
- TASK-RPT-007 已完成
- **Phase 2 启用条件**：Feature Flag ENABLE_FULL_DAILY_REPORT_SM=true

### 输出
- `backend/services/daily_report_service.py` - lock_final()
- `backend/routers/daily_reports.py` - POST /api/v1/daily-reports/{id}/final-lock
- `backend/tests/test_daily_report_api.py` - 计费锁定测试用例

### 验收标准
- □ Phase 1 不启用此功能
- □ POST /api/v1/daily-reports/{id}/final-lock 计费锁定
- □ Phase 2：系统自动执行或手动触发
- □ 锁定后 conversions_final 不可修改（BR-RPT-009）
- □ 记录 final_locked_at 时间戳
- □ 生成 Ledger 账本记录

---

## TASK-RPT-009: 日报红冲 API（Phase 2）

> **Phase**: Phase 2
> **启用条件**: Feature Flag `ENABLE_FULL_DAILY_REPORT_SM=true`

### 关联文档
- STATE_MACHINE.md v2.9 §8.8（红冲修正机制）
- DATA_SCHEMA.md v5.11 §3.4.4（REVERSAL 类型）

### 输入
- TASK-RPT-008 已完成
- 账本模块已完成
- **Phase 2 启用条件**

### 输出
- `backend/schemas/daily_report.py` - ReversalRequest
- `backend/services/daily_report_service.py` - create_reversal()
- `backend/routers/daily_reports.py` - POST /api/v1/daily-reports/{id}/reversal
- `backend/tests/test_daily_report_api.py` - 红冲测试用例

### 验收标准
- □ Phase 1 不启用此功能
- □ POST /api/v1/daily-reports/{id}/reversal 创建红冲
- □ 仅 admin 可执行 [AUDIT] 强制
- □ 仅 final_locked 状态可红冲
- □ 创建 REVERSAL 账本记录
- □ 禁止直接 UPDATE daily_reports

---

# M7 充值模块 (FIN)

> **规则模块**: BR-FIN (10 条规则)
> **关联 SoT**: STATE_MACHINE.md v2.9 §9, DATA_SCHEMA.md v5.11 §3.4.4, PRD v5.1 §6.1
> **优先级**: P1
> **Phase**: Phase 1

## 充值状态机

```python
# 充值状态（来源: PRD v5.1 §4.2）
TOPUP_STATUS = [
    "draft",            # 草稿（投手创建）
    "pending_review",   # 待审核（户管已提交）
    "finance_approve",  # 财务已批准
    "paid",             # 已转账
    "completed",        # 已完成（代理商已充值）
    "rejected",         # 已拒绝
    "cancelled"         # 已取消
]

# 充值审批链（不含老板）
# pitcher → account_manager → finance → finance → account_manager
```

---

## TASK-FIN-001: 充值申请列表 API

### 关联文档
- STATE_MACHINE.md v2.9 §9（充值状态机）
- DATA_SCHEMA.md v5.11 §topup_requests 表

### 输入
- 账户模块已完成
- 项目模块已完成

### 输出
- `backend/schemas/topup_request.py` - TopupRequestResponse, TopupRequestListResponse
- `backend/services/topup_service.py` - list_topup_requests()
- `backend/routers/topup_requests.py` - GET /api/v1/topup-requests
- `backend/tests/test_topup_api.py` - 列表测试用例

### 验收标准
- □ GET /api/v1/topup-requests 返回充值申请列表
- □ 支持状态、项目、日期筛选
- □ pitcher 仅能看到自己的申请

---

## TASK-FIN-002: 创建充值申请 API

### 关联文档
- BUSINESS_RULES.md BR-FIN-001（充值必须申请）
- STATE_MACHINE.md v2.9 §9（初始状态 draft）

### 输入
- TASK-FIN-001 已完成
- 账户模块已完成

### 输出
- `backend/schemas/topup_request.py` - TopupRequestCreate
- `backend/services/topup_service.py` - create_topup_request()
- `backend/routers/topup_requests.py` - POST /api/v1/topup-requests
- `backend/tests/test_topup_api.py` - 创建测试用例

### 验收标准
- □ POST /api/v1/topup-requests 创建充值申请
- □ 必须指定 ad_account_id, amount
- □ amount 必须大于 0
- □ 初始状态为 draft
- □ pitcher/account_manager 可创建

---

## TASK-FIN-003: 提交充值申请 API

### 关联文档
- STATE_MACHINE.md v2.9 §9（draft → pending_review）

### 输入
- TASK-FIN-002 已完成

### 输出
- `backend/services/topup_service.py` - submit_topup_request()
- `backend/routers/topup_requests.py` - POST /api/v1/topup-requests/{id}/submit
- `backend/tests/test_topup_api.py` - 提交测试用例

### 验收标准
- □ POST /api/v1/topup-requests/{id}/submit 提交申请
- □ 状态流转：draft → pending_review
- □ pitcher/account_manager 可提交
- □ 记录审计日志 [AUDIT]

---

## TASK-FIN-004: 财务审批 API

### 关联文档
- BUSINESS_RULES.md BR-FIN-002（充值审批人）
- STATE_MACHINE.md v2.9 §9（pending_review → finance_approve/rejected）

### 输入
- TASK-FIN-003 已完成

### 输出
- `backend/schemas/topup_request.py` - TopupApprovalRequest
- `backend/services/topup_service.py` - approve_topup(), reject_topup()
- `backend/routers/topup_requests.py` - POST /api/v1/topup-requests/{id}/approve, POST /api/v1/topup-requests/{id}/reject
- `backend/tests/test_topup_api.py` - 审批测试用例

### 验收标准
- □ POST /api/v1/topup-requests/{id}/approve 审批通过
- □ POST /api/v1/topup-requests/{id}/reject 审批拒绝
- □ 状态流转：pending_review → finance_approve（通过）
- □ 状态流转：pending_review → rejected（拒绝）
- □ 必须由 finance 执行（BR-FIN-002）
- □ 拒绝必须填写原因
- □ 记录审计日志 [AUDIT]

---

## TASK-FIN-005: 确认转账 API

### 关联文档
- STATE_MACHINE.md v2.9 §9（finance_approve → paid）
- BUSINESS_RULES.md BR-FIN-010（资金流水审计）

### 输入
- TASK-FIN-004 已完成

### 输出
- `backend/schemas/topup_request.py` - TopupPaidRequest
- `backend/services/topup_service.py` - mark_paid()
- `backend/routers/topup_requests.py` - POST /api/v1/topup-requests/{id}/mark-paid
- `backend/tests/test_topup_api.py` - 转账确认测试用例

### 验收标准
- □ POST /api/v1/topup-requests/{id}/mark-paid 确认转账
- □ 状态流转：finance_approve → paid
- □ 必须由 finance 执行
- □ 记录转账凭证/时间
- □ 记录审计日志 [AUDIT]

---

## TASK-FIN-006: 确认到账 API

### 关联文档
- STATE_MACHINE.md v2.9 §9（paid → completed）
- DATA_SCHEMA.md v5.11 §3.4.4（账本记录）

### 输入
- TASK-FIN-005 已完成
- 账本模块已完成

### 输出
- `backend/services/topup_service.py` - confirm_completed()
- `backend/routers/topup_requests.py` - POST /api/v1/topup-requests/{id}/complete
- `backend/tests/test_topup_api.py` - 到账确认测试用例

### 验收标准
- □ POST /api/v1/topup-requests/{id}/complete 确认到账
- □ 状态流转：paid → completed
- □ finance/account_manager 可执行
- □ 创建 Ledger 账本记录
- □ 更新账户余额
- □ completed 为终态，不可回退

---

## TASK-FIN-007: 取消充值申请 API

### 关联文档
- STATE_MACHINE.md v2.9 §9（→ cancelled）

### 输入
- TASK-FIN-002 已完成

### 输出
- `backend/services/topup_service.py` - cancel_topup_request()
- `backend/routers/topup_requests.py` - POST /api/v1/topup-requests/{id}/cancel
- `backend/tests/test_topup_api.py` - 取消测试用例

### 验收标准
- □ POST /api/v1/topup-requests/{id}/cancel 取消申请
- □ 仅 draft/pending_review 状态可取消
- □ cancelled 为终态
- □ 记录审计日志 [AUDIT]

---

# M8 账本模块 (LEDGER)

> **规则模块**: BR-FIN 扩展（账本属于财务范畴）
> **关联 SoT**: DATA_SCHEMA.md v5.11 §3.4.4, DATA_SCHEMA.md v5.11 §ledger_entries
> **优先级**: P2
> **Phase**: Phase 1

## TASK-LEDGER-001: 账本记录列表 API

### 关联文档
- DATA_SCHEMA.md v5.11 §3.4.4（双账本架构）
- DATA_SCHEMA.md v5.11 §ledger_entries 表

### 输入
- 认证模块已完成

### 输出
- `backend/schemas/ledger.py` - LedgerEntryResponse, LedgerEntryListResponse
- `backend/services/ledger_service.py` - list_ledger_entries()
- `backend/routers/ledger.py` - GET /api/v1/ledger-entries
- `backend/tests/test_ledger_api.py` - 列表测试用例

### 验收标准
- □ GET /api/v1/ledger-entries 返回账本记录
- □ 支持 ledger_type 筛选（PROJECT/SUPPLIER）
- □ 支持 entry_type 筛选（REVENUE/COST/REVERSAL 等）
- □ 仅 finance/admin 可查看

---

## TASK-LEDGER-002: 创建账本记录 Service

### 关联文档
- DATA_SCHEMA.md v5.11 §3.4.4（账本类型定义）
- BUSINESS_RULES.md BR-FIN-009（双账本原则）
- BUSINESS_RULES.md BR-FIN-007（锁定后不可改）

### 输入
- TASK-LEDGER-001 已完成

### 输出
- `backend/services/ledger_service.py` - create_ledger_entry(), create_dual_entries()
- `backend/tests/test_ledger_service.py` - 账本创建测试用例

### 验收标准
- □ 支持 PROJECT/SUPPLIER 双账本
- □ 双账本必须在同一事务中创建（with db.begin()）
- □ 金额使用 Decimal(15,2)
- □ 禁止直接 UPDATE/DELETE
- □ 记录 created_by, created_at

---

## TASK-LEDGER-003: 红冲记录 Service

### 关联文档
- DATA_SCHEMA.md v5.11 §3.4.4（REVERSAL 类型）
- BUSINESS_RULES.md BR-FIN-008（红冲必须有理由）

### 输入
- TASK-LEDGER-002 已完成

### 输出
- `backend/services/ledger_service.py` - create_reversal()
- `backend/tests/test_ledger_service.py` - 红冲测试用例

### 验收标准
- □ 创建 entry_type=REVERSAL 记录
- □ amount = -原金额
- □ 必须提供 ref_id 和 reason（BR-FIN-008）
- □ 仅 admin 可执行 [AUDIT]

---

## TASK-LEDGER-004: 余额计算 Service

### 关联文档
- DATA_SCHEMA.md v5.11 §3.4.4（余额公式）
- BUSINESS_RULES.md BR-FIN-006（可用资金公式）

### 输入
- TASK-LEDGER-002 已完成

### 输出
- `backend/services/ledger_service.py` - calculate_balance(), calculate_project_balance(), calculate_supplier_balance()
- `backend/tests/test_ledger_service.py` - 余额计算测试用例

### 验收标准
- □ 项目余额 = Σ(REVENUE) - Σ(COST_ALLOCATION) - Σ(REVERSAL)
- □ 供应商余额 = Σ(COST) - Σ(TRANSFER_OUT) + Σ(TRANSFER_IN) - Σ(REVERSAL)
- □ 可用资金公式参考 DATA_SCHEMA.md v5.11 §3.4.4
- □ 押款 = 历史充值 - 历史消耗（PRD v5.1）

---

# M9 对账模块 (RECON)

> **规则模块**: BR-RECON (7 条规则)
> **关联 SoT**: STATE_MACHINE.md v2.9 §11, DATA_SCHEMA.md v5.11 §reconciliation_batches
> **优先级**: P2
> **Phase**: Phase 2

## TASK-RECON-001: 对账批次列表 API（Phase 2）

> **Phase**: Phase 2

### 关联文档
- STATE_MACHINE.md v2.9 §11.1（对账批次状态机）
- DATA_SCHEMA.md v5.11 §reconciliation_batches 表

### 输入
- 账本模块已完成
- **Phase 2 启用条件**

### 输出
- `backend/schemas/reconciliation.py` - ReconciliationBatchResponse, ReconciliationBatchListResponse
- `backend/services/reconciliation_service.py` - list_reconciliation_batches()
- `backend/routers/reconciliation.py` - GET /api/v1/reconciliation-batches
- `backend/tests/test_reconciliation_api.py` - 列表测试用例

### 验收标准
- □ GET /api/v1/reconciliation-batches 返回对账批次列表
- □ 支持状态、月份筛选
- □ 仅 finance/admin 可查看

---

## TASK-RECON-002: 创建对账批次 API（Phase 2）

> **Phase**: Phase 2

### 关联文档
- BUSINESS_RULES.md BR-RECON-001（对账周期）
- BUSINESS_RULES.md BR-RECON-002（对账发起人）
- STATE_MACHINE.md v2.9 §11.1（初始状态 draft）

### 输入
- TASK-RECON-001 已完成
- **Phase 2 启用条件**

### 输出
- `backend/schemas/reconciliation.py` - ReconciliationBatchCreate
- `backend/services/reconciliation_service.py` - create_reconciliation_batch()
- `backend/routers/reconciliation.py` - POST /api/v1/reconciliation-batches
- `backend/tests/test_reconciliation_api.py` - 创建测试用例

### 验收标准
- □ POST /api/v1/reconciliation-batches 创建对账批次
- □ 必须指定对账月份
- □ 同一月份不可重复创建
- □ 必须由 finance 发起（BR-RECON-002）
- □ 初始状态为 draft

---

## TASK-RECON-003: 对账批次状态流转 API（Phase 2）

> **Phase**: Phase 2

### 关联文档
- STATE_MACHINE.md v2.9 §11.1（对账批次状态机）
- BUSINESS_RULES.md BR-RECON-004（对账状态流转）
- BUSINESS_RULES.md BR-RECON-005（完成后不可逆）

### 输入
- TASK-RECON-002 已完成
- **Phase 2 启用条件**

### 输出
- `backend/services/reconciliation_service.py` - submit_batch(), approve_batch(), mark_needs_adjustment(), complete_batch()
- `backend/routers/reconciliation.py` - POST /api/v1/reconciliation-batches/{id}/submit, approve, adjust, complete
- `backend/tests/test_reconciliation_api.py` - 状态流转测试用例

### 验收标准
- □ draft → pending_review（提交）
- □ pending_review → approved（审批通过）
- □ pending_review → needs_adjustment（需调整）
- □ needs_adjustment → approved（调整后审批）
- □ approved → completed（完成）
- □ completed 为终态，不可回退（BR-RECON-005）

---

## TASK-RECON-004: 对账明细管理 API（Phase 2）

> **Phase**: Phase 2

### 关联文档
- STATE_MACHINE.md v2.9 §11.2（对账明细状态机）
- BUSINESS_RULES.md BR-RECON-003（差异阈值）
- BUSINESS_RULES.md BR-RECON-006（差异必须记录）

### 输入
- TASK-RECON-002 已完成
- **Phase 2 启用条件**

### 输出
- `backend/schemas/reconciliation.py` - ReconciliationDetailResponse
- `backend/services/reconciliation_service.py` - list_details(), confirm_detail(), adjust_detail()
- `backend/routers/reconciliation.py` - GET/PUT /api/v1/reconciliation-batches/{id}/details
- `backend/tests/test_reconciliation_api.py` - 明细管理测试用例

### 验收标准
- □ GET /api/v1/reconciliation-batches/{id}/details 返回明细列表
- □ 状态流转：pending → confirmed/adjusted
- □ 差异超过阈值必须人工确认（BR-RECON-003）
- □ 调整必须记录原因（BR-RECON-006）
- □ 调整必须由 finance 审批（BR-RECON-007）

---

# M10 利润模块 (PROFIT)

> **规则模块**: BR-PROFIT (6 条规则)
> **关联 SoT**: DATA_SCHEMA.md v5.11 §3.4.4, DATA_SCHEMA.md v5.11 §3.6, PRD v5.1 §2
> **优先级**: P2
> **Phase**: Phase 1

## TASK-PROFIT-001: 项目利润报表 API

### 关联文档
- BUSINESS_RULES.md BR-PROFIT-001（收入公式 per_lead）
- BUSINESS_RULES.md BR-PROFIT-002（收入公式 fee_rate）
- BUSINESS_RULES.md BR-PROFIT-004（毛利公式）
- PRD v5.1 附录B（利润公式）

### 输入
- 日报模块已完成
- 账本模块已完成

### 输出
- `backend/schemas/profit.py` - ProjectProfitResponse, ProjectProfitListResponse
- `backend/services/profit_service.py` - get_project_profit_report()
- `backend/routers/profit.py` - GET /api/v1/profit/projects
- `backend/tests/test_profit_api.py` - 项目利润测试用例

### 验收标准
- □ GET /api/v1/profit/projects 返回项目利润报表
- □ 支持日期范围筛选
- □ per_lead 模式：收入 = conversions_final × unit_price
- □ fee_rate 模式：收入 = ad_spend × service_rate
- □ 毛利 = 收入 - 项目成本（BR-PROFIT-004）
- □ 项目成本 = ad_topup（广告费充值，已含手续费）

---

## TASK-PROFIT-002: CPL 计算 Service

### 关联文档
- BUSINESS_RULES.md BR-PROFIT-005（CPL 公式）
- BUSINESS_RULES.md BR-PROFIT-006（低量标记）
- MASTER.md v4.9 §4.5.2（边界场景）

### 输入
- 日报模块已完成

### 输出
- `backend/services/profit_service.py` - calculate_cpl()
- `backend/tests/test_profit_service.py` - CPL 计算测试用例

### 验收标准
- □ CPL = spend / conversions（BR-PROFIT-005）
- □ 0 转化时 CPL 显示 "N/A"
- □ 进粉数 < 5 时标记"低量不稳定"（BR-PROFIT-006）
- □ 冷启动期（7天）数据仅供观察

---

## TASK-PROFIT-003: 成本计算 Service

### 关联文档
- BUSINESS_RULES.md BR-PROFIT-003（成本公式）
- MASTER.md v4.9 §4.5.9（成本分类口径）
- PRD v5.1 §2.2（支出类型枚举）

### 输入
- 账本模块已完成

### 输出
- `backend/services/profit_service.py` - calculate_cost()
- `backend/tests/test_profit_service.py` - 成本计算测试用例

### 验收标准
- □ 项目成本 = ad_topup（广告费充值，已含手续费）
- □ 成本分类（PRD v5.1 §2.2）：
  - ad_topup：广告费充值（含手续费），归属项目
  - ad_support：广告配套（公司统一，不分摊到项目）
  - overhead：后勤支出（公司统一，不分摊到项目）
- □ 广告配套（ad_support）和后勤支出（overhead）不分摊到项目

---

## TASK-PROFIT-004: 公司利润汇总 API

### 关联文档
- MASTER.md v4.9 §4.5.10（公司利润公式）
- PRD v5.1 附录B（利润公式）

### 输入
- TASK-PROFIT-001 已完成
- 账本模块已完成

### 输出
- `backend/schemas/profit.py` - CompanyProfitResponse
- `backend/services/profit_service.py` - get_company_profit_report()
- `backend/routers/profit.py` - GET /api/v1/profit/company
- `backend/tests/test_profit_api.py` - 公司利润测试用例

### 验收标准
- □ GET /api/v1/profit/company 返回公司利润汇总
- □ 公司利润 = 总收入 - 总支出（PRD v5.1）
- □ 总支出 = ad_topup + ad_support + overhead
- □ 支持日期范围筛选
- □ 仅 ceo/admin 可查看

---

# M11 周报模块 (WEEKLY)

> **规则模块**: 无独立规则模块
> **关联 SoT**: DATA_SCHEMA.md v5.11 §weekly_reports, MASTER.md v4.9 附录C
> **优先级**: P3
> **Phase**: Phase 1（可选提交）+ Phase 2（必须提交）

## TASK-WEEKLY-001: 周报列表 API

### 关联文档
- DATA_SCHEMA.md v5.11 §weekly_reports 表

### 输入
- 项目模块已完成

### 输出
- `backend/schemas/weekly_report.py` - WeeklyReportResponse, WeeklyReportListResponse
- `backend/services/weekly_report_service.py` - list_weekly_reports()
- `backend/routers/weekly_reports.py` - GET /api/v1/weekly-reports
- `backend/tests/test_weekly_report_api.py` - 列表测试用例

### 验收标准
- □ GET /api/v1/weekly-reports 返回周报列表
- □ 支持周次、项目、负责人筛选

---

## TASK-WEEKLY-002: 创建周报 API

### 关联文档
- DATA_SCHEMA.md v5.11 §weekly_reports 表

### 输入
- TASK-WEEKLY-001 已完成

### 输出
- `backend/schemas/weekly_report.py` - WeeklyReportCreate
- `backend/services/weekly_report_service.py` - create_weekly_report()
- `backend/routers/weekly_reports.py` - POST /api/v1/weekly-reports
- `backend/tests/test_weekly_report_api.py` - 创建测试用例

### 验收标准
- □ POST /api/v1/weekly-reports 创建周报
- □ 必须指定 project_id, week_start_date
- □ 包含周消耗、周进粉、问题、下周计划
- □ project_owner 可创建

---

## TASK-WEEKLY-003: 提交周报 API

### 关联文档
- MASTER.md v4.9 附录 C（Phase 2 周报必须提交）

### 输入
- TASK-WEEKLY-002 已完成

### 输出
- `backend/services/weekly_report_service.py` - submit_weekly_report()
- `backend/routers/weekly_reports.py` - POST /api/v1/weekly-reports/{id}/submit
- `backend/tests/test_weekly_report_api.py` - 提交测试用例

### 验收标准
- □ POST /api/v1/weekly-reports/{id}/submit 提交周报
- □ Phase 1：可选提交（不强制）
- □ Phase 2：周五下班前必须提交（Feature Flag 控制）

---

# 附录

## 附录 A：任务卡统计

| 模块 | 任务数 | 优先级 | Phase | 预估工时 |
|------|--------|--------|-------|----------|
| M1 认证 | 5 | P0 | Phase 1 | 15h |
| M2 用户 | 5 | P0 | Phase 1 | 12h |
| M3 项目 | 6 | P0 | Phase 1 | 18h |
| M4 渠道 | 4 | P1 | Phase 1 | 12h |
| M5 账户 | 6 | P0 | Phase 1 | 18h |
| M6 日报 | 4 | P0 | Phase 1 | 16h |
| M6 日报 | 5 | P3 | Phase 2 | 14h |
| M7 充值 | 7 | P1 | Phase 1 | 20h |
| M8 账本 | 4 | P2 | Phase 1 | 15h |
| M9 对账 | 4 | P2 | Phase 2 | 12h |
| M10 利润 | 4 | P2 | Phase 1 | 12h |
| M11 周报 | 3 | P3 | Phase 1/2 | 8h |
| **合计** | **57** | - | - | **172h** |

### Phase 分组统计

| Phase | 任务数 | 预估工时 |
|-------|--------|----------|
| Phase 1 | 48 | 146h |
| Phase 2 | 9 | 26h |

---

## 附录 B：SoT 文档快速索引

| 文档 | 路径 | 用途 |
|------|------|------|
| MASTER.md | docs/sot/MASTER.md | 架构宪法，角色定义 |
| STATE_MACHINE.md | docs/sot/STATE_MACHINE.md | 状态机定义 |
| DATA_SCHEMA.md | docs/sot/DATA_SCHEMA.md | 数据库表结构 |
| BUSINESS_RULES.md | docs/sot/BUSINESS_RULES.md | 业务规则索引 |
| ERROR_CODES_SOT.md | docs/sot/ERROR_CODES_SOT.md | 错误码定义 |
| AUTH_SPEC.md | docs/sot/AUTH_SPEC.md | 认证授权规范 |
| DATA_SCHEMA.md §3.4.4 | docs/sot/DATA_SCHEMA.md | 账本规则（已合并） |
| API_SOT.md | docs/sot/API_SOT.md | API 端点定义 |
| PRD_v5.1.md | docs/PRD_v5.1.md | 产品需求文档 |

---

## 附录 C：角色权限速查表

> **来源**: MASTER.md v4.9 §2.4, PRD v5.1 §2.2

| 操作 | ceo | project_owner | finance | pitcher | account_manager | admin |
|------|-----|---------------|---------|---------|-----------------|-------|
| 创建用户 | ✓ | - | - | - | - | ✓ |
| 创建项目 | ✓ | - | - | - | - | ✓ |
| 管理项目成员 | ✓ | ✓ | - | - | - | ✓ |
| 创建渠道 | - | - | - | - | ✓ | ✓ |
| 审批渠道评审 | - | ✓ | - | - | - | ✓ |
| 创建账户 | - | - | - | - | ✓ | ✓ |
| 分配账户 | - | - | - | - | ✓ | ✓ |
| 提交日报 | - | - | - | ✓ | - | - |
| 审核日报 | - | ✓ | - | - | - | ✓ |
| 统计实际消耗 | - | ✓ | - | - | - | - |
| 确认有效粉 | - | ✓ | - | - | - | - |
| 创建充值 | - | - | - | ✓ | ✓ | - |
| 审批充值 | - | - | ✓ | - | - | ✓ |
| 确认到账 | - | - | ✓ | - | ✓ | - |
| 发起对账 | - | - | ✓ | - | - | ✓ |
| 查看利润 | ✓ | - | ✓ | - | - | ✓ |
| 红冲操作 | - | - | - | - | - | ✓ |

---

## 附录 D：错误码速查表

> **来源**: ERROR_CODES_SOT.md v2.2

| 错误码 | HTTP | 含义 | 使用场景 |
|--------|------|------|----------|
| AUTH_400 | 400 | 认证失败 | 用户名或密码错误 |
| AUTH_401 | 401 | 未认证 | Token 缺失或过期 |
| AUTH_403 | 403 | 无权限 | 角色不允许此操作 |
| STATE_400 | 400 | 状态转换非法 | 不符合状态机定义 |
| STATE_402 | 400 | 终态非法回退 | 尝试修改已确认数据 |
| BIZ_001 | 400 | 无效的操作 | 违反业务规则 |
| BIZ_002 | 404 | 资源不存在 | 根据 ID 查询未找到 |
| BIZ_100 | 400 | 金额非法 | 金额 ≤ 0 |
| BIZ_101 | 400 | 余额不足 | 转账/消耗超出余额 |
| BIZ_402 | 400 | 红冲缺少原因 | 红冲操作未提供 reason |
| VAL_001 | 400 | 参数校验失败 | 必填字段缺失 |

---

## 附录 E：变更历史

### v2.0 (2025-12-27)

**P0 修复**:
- 修复 `data_operator` → `project_owner`（TASK-CHAN-003）
- 修复 `media_buyer` → `pitcher`（TASK-CHAN-003/004, TASK-FIN-003）
- 修复 `approved` → `finance_approve`（TASK-FIN-004）
- 标注 Phase 2 任务卡（TASK-RPT-004/005/006/008/009, TASK-RECON-001~004）

**P1 修复**:
- 修复成本公式（TASK-PROFIT-003）
- 增加渠道模块规则引用（M4）
- 完善 Phase 2 标注
- 修正账本余额公式（TASK-LEDGER-004）
- 统一错误码为 STATE_400

**P2 修复**:
- 修正 SoT 文档路径（ASDD 4层架构）
- 扩展权限表
- 增加 Phase 分组视图
- 增加模块依赖图
- 增加通用测试要求
- 增加错误码速查表

**新增内容**:
- 角色白名单说明
- 模块依赖关系图
- Phase 分组视图
- 通用测试要求
- 附录 D 错误码速查表
- 附录 E 变更历史

### v1.0 (2025-12-27)

- 初始版本，57 个任务卡

---

**文档版本**: v2.0
**生成日期**: 2025-12-27
**最后更新**: 2025-12-27
**维护者**: AI Architecture Team
**审查状态**: 已通过 SoT 合规审查
