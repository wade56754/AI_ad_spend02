# AI 广告代投系统 - Claude 提示词库 v2.0

> **文档版本**: v2.0 (Claude 最佳实践优化版)
> **修订日期**: 2025-12-28
> **基准文档**: TASK_CARDS_v2.md v2.0
> **任务总数**: 57 个
> **结构**: 9 标签 XML 格式

---

## 目录

- [使用说明](#使用说明)
- [系统约束（全局前置）](#系统约束全局前置)
- [M1 认证模块 (AUTH)](#m1-认证模块-auth)
- [M2 用户模块 (USER)](#m2-用户模块-user)
- [M3 项目模块 (PROJ)](#m3-项目模块-proj)
- [M4 渠道模块 (CHANNEL)](#m4-渠道模块-channel)
- [M5 广告账户模块 (ACCT)](#m5-广告账户模块-acct)
- [M6 日报模块 (RPT)](#m6-日报模块-rpt)
- [M7 充值模块 (FIN)](#m7-充值模块-fin)
- [M8 账本模块 (LEDGER)](#m8-账本模块-ledger)
- [M9 对账模块 (RECON)](#m9-对账模块-recon)
- [M10 利润模块 (PROFIT)](#m10-利润模块-profit)
- [M11 周报模块 (WEEKLY)](#m11-周报模块-weekly)
- [附录](#附录)

---

## 使用说明

### 执行步骤

```
1. 复制 SYSTEM_CONSTRAINT 块（必须）
2. 复制对应任务的提示词
3. 粘贴到 Claude CLI / Web
4. 验证输出 → 运行测试
5. 更新 Memory Bank 进度
```

### 9 标签结构

| 标签 | 用途 | 必填 |
|------|------|------|
| `<system_constraint>` | SoT 约束、角色白名单、防幻觉规则 | ✓ 全局 |
| `<context>` | 项目、技术栈、模块、前置依赖 | ✓ |
| `<task>` | 一句话任务描述 | ✓ |
| `<input>` | 必填/可选输入 | ✓ |
| `<deliverables>` | 产出文件清单 | ✓ |
| `<constraints>` | 业务规则（肯定指令） | ✓ |
| `<error_handling>` | 错误场景、错误码 | ✓ |
| `<examples>` | 正常/边界/错误场景示例 | ✓ |
| `<output_format>` | thinking + implementation + verification | ✓ |

---

# 系统约束（全局前置）

> ⚠️ **每次执行任务前必须先加载此块**

```xml
<system_constraint>
  <sot_versions>
    MASTER.md v4.6 | STATE_MACHINE.md v2.7 | DATA_SCHEMA.md v5.6
    BUSINESS_RULES.md v4.7 | ERROR_CODES.md v2.3 | AUTH_SPEC.md v2.2
    LEDGER_SOT.md v1.2 | API_SOT.md v9.4
  </sot_versions>

  <role_whitelist>
    仅允许 6 个角色: ceo, project_owner, finance, pitcher, account_manager, admin
    禁止使用: supervisor, data_operator, media_buyer
  </role_whitelist>

  <phase_rules>
    当前: Phase 1
    Phase 1 原则: 记录事实、展示状态、提示异常，禁止强制阻断
    Phase 2 原则: 引入约束、强制审批、考核关联
  </phase_rules>

  <anti_hallucination>
    AH-01: 禁止假设数据一致 - 遇到缺失标记"待确认"
    AH-02: 禁止自动做管理裁决 - 禁止生成自动拒绝/暂停/终止代码
    AH-03: 禁止引入 SoT 未定义概念 - 发现缺失→停止→询问
    AH-04: 必须遵循 Phase 边界 - Phase 1 = 提示+高亮+记录
    AH-05: 遇到歧义必须停止并询问
  </anti_hallucination>

  <code_standards>
    后端: FastAPI + SQLAlchemy 2.x + Pydantic v2
    响应格式: {"code": 0, "message": "success", "data": {...}}
    错误格式: {"code": "ERROR_CODE", "message": "描述", "data": null}
    命名: 文件 snake_case, 类 PascalCase, 函数 snake_case
  </code_standards>

  <pre_coding_checklist>
    □ 角色在 6 角色白名单中
    □ 状态在 STATE_MACHINE.md 定义
    □ 错误码来自 ERROR_CODES.md
    □ 遵循 Phase 1 原则（只提示不阻断）
  </pre_coding_checklist>
</system_constraint>
```

---

# M1 认证模块 (AUTH)

> 优先级: P0 | Phase: Phase 1 | 任务数: 5

## TASK-AUTH-001: 用户登录 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>auth</module>
  <task_id>TASK-AUTH-001</task_id>
  <prerequisites>users 表已存在</prerequisites>
  <sot>AUTH_SPEC.md v2.2 §3, ERROR_CODES.md v2.3, BR-AUTH-001/002</sot>
</context>

<task>实现 POST /api/v1/auth/login 用户登录 API</task>

<input>
  <required>
    users 表: id, email, password_hash, role, is_active, project_id
    JWT Token 规范: HS256, 有效期 24h
  </required>
</input>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/auth.py | LoginRequest, LoginResponse, TokenPayload |
  | backend/services/auth_service.py | login(), validate_token() |
  | backend/routers/auth.py | POST /api/v1/auth/login |
  | backend/tests/test_auth_api.py | 6 个测试用例 |
</deliverables>

<constraints>
  <rule>Token 有效期固定 24 小时（86400 秒）</rule>
  <rule>Token payload 包含: user_id, role, exp</rule>
  <rule>密码验证使用 bcrypt</rule>
  <rule>角色值仅允许 6 个白名单值</rule>
  <rule>安全原则: 用户不存在和密码错误返回相同消息</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 用户不存在/密码错误 | AUTH_400 | 400 | 邮箱或密码错误 |
  | 账户停用 | AUTH_400 | 400 | 账户已停用 |
  | Token 过期 | AUTH_401 | 401 | Token 已过期 |
  | Token 无效 | AUTH_401 | 401 | 无效的 Token |
</error_handling>

<examples>
  <example name="正常登录">
    <request>POST /api/v1/auth/login {"email": "admin@example.com", "password": "Admin123!"}</request>
    <response>{"code": 0, "message": "登录成功", "data": {"access_token": "eyJ...", "token_type": "bearer", "expires_in": 86400}}</response>
  </example>
  <example name="密码错误">
    <request>POST /api/v1/auth/login {"email": "admin@example.com", "password": "wrong"}</request>
    <response>{"code": "AUTH_400", "message": "邮箱或密码错误", "data": null}</response>
  </example>
  <example name="账户停用">
    <request>POST /api/v1/auth/login {"email": "disabled@example.com", "password": "xxx"}</request>
    <response>{"code": "AUTH_400", "message": "账户已停用", "data": null}</response>
  </example>
</examples>

<output_format>
  <thinking>1. 分析 Token 规范 2. 确认安全策略 3. 设计错误处理</thinking>
  <implementation>依次输出 4 个文件完整代码</implementation>
  <verification>pytest backend/tests/test_auth_api.py -v</verification>
</output_format>

<acceptance_criteria>
  □ POST /api/v1/auth/login 返回 JWT Token
  □ Token 包含 user_id, role, exp
  □ Token 有效期 24 小时
  □ 测试覆盖: 正向登录、错误密码、不存在用户、账户停用
</acceptance_criteria>
```

---

## TASK-AUTH-002: 用户登出 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>auth</module>
  <task_id>TASK-AUTH-002</task_id>
  <prerequisites>TASK-AUTH-001 已完成</prerequisites>
  <sot>AUTH_SPEC.md v2.2 §4</sot>
</context>

<task>实现 POST /api/v1/auth/logout 用户登出 API</task>

<input>
  <required>TASK-AUTH-001 实现的登录功能</required>
  <optional>Redis 配置（用于 Token 黑名单）</optional>
</input>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/services/auth_service.py | 扩展 logout() 方法 |
  | backend/routers/auth.py | POST /api/v1/auth/logout |
  | backend/tests/test_auth_api.py | 3 个登出测试用例 |
</deliverables>

<constraints>
  <rule>登出后原 Token 立即失效</rule>
  <rule>需要有效 Token 才能调用</rule>
  <rule>重复登出返回成功（幂等）</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 未提供 Token | AUTH_401 | 401 | 未认证 |
  | Token 已过期 | AUTH_401 | 401 | Token 已过期 |
</error_handling>

<examples>
  <example name="正常登出">
    <request>POST /api/v1/auth/logout Headers: Authorization: Bearer eyJ...</request>
    <response>{"code": 0, "message": "登出成功", "data": {"logged_out_at": "2025-12-28T10:00:00Z"}}</response>
  </example>
  <example name="重复登出">
    <request>POST /api/v1/auth/logout (已登出的 Token)</request>
    <response>{"code": 0, "message": "登出成功", "data": null}</response>
  </example>
</examples>

<output_format>
  <thinking>1. 设计 Token 失效机制 2. 确保幂等性</thinking>
  <implementation>输出修改的文件</implementation>
  <verification>pytest backend/tests/test_auth_api.py::TestLogout -v</verification>
</output_format>

<acceptance_criteria>
  □ POST /api/v1/auth/logout 返回成功
  □ 登出后原 Token 失效
  □ 重复登出返回成功（幂等）
</acceptance_criteria>
```

---

## TASK-AUTH-003: Token 刷新 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>auth</module>
  <task_id>TASK-AUTH-003</task_id>
  <prerequisites>TASK-AUTH-001 已完成</prerequisites>
  <sot>AUTH_SPEC.md v2.2 §5, BR-AUTH-002</sot>
</context>

<task>实现 POST /api/v1/auth/refresh Token 刷新 API</task>

<input>
  <required>Refresh Token 规范: 有效期 7 天</required>
</input>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/auth.py | RefreshRequest |
  | backend/services/auth_service.py | refresh_token() |
  | backend/routers/auth.py | POST /api/v1/auth/refresh |
  | backend/tests/test_auth_api.py | 3 个刷新测试用例 |
</deliverables>

<constraints>
  <rule>使用 Refresh Token 刷新（非 Access Token）</rule>
  <rule>新 Access Token 有效期 24 小时</rule>
  <rule>Refresh Token 有效期 7 天</rule>
  <rule>刷新后旧 Access Token 失效</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | Refresh Token 无效 | AUTH_401 | 401 | 无效的刷新令牌 |
  | Refresh Token 过期 | AUTH_401 | 401 | 刷新令牌已过期 |
  | 用户已停用 | AUTH_400 | 400 | 账户已停用 |
</error_handling>

<examples>
  <example name="正常刷新">
    <request>POST /api/v1/auth/refresh {"refresh_token": "eyJ...refresh..."}</request>
    <response>{"code": 0, "message": "刷新成功", "data": {"access_token": "eyJ...", "token_type": "bearer", "expires_in": 86400}}</response>
  </example>
</examples>

<output_format>
  <thinking>1. 设计双 Token 机制 2. 确认有效期规则</thinking>
  <implementation>输出相关文件</implementation>
  <verification>pytest backend/tests/test_auth_api.py::TestRefresh -v</verification>
</output_format>

<acceptance_criteria>
  □ POST /api/v1/auth/refresh 返回新 Token
  □ 使用 Refresh Token 刷新
  □ 新 Token 有效期 24 小时
</acceptance_criteria>
```

---

## TASK-AUTH-004: 权限校验中间件

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>auth</module>
  <task_id>TASK-AUTH-004</task_id>
  <prerequisites>TASK-AUTH-001 已完成</prerequisites>
  <sot>MASTER.md v4.6 §2.4, BR-AUTH-003/004</sot>
</context>

<task>实现权限校验中间件，支持角色级别的访问控制</task>

<input>
  <required>
    6 角色白名单: ceo, project_owner, finance, pitcher, account_manager, admin
    禁止角色: supervisor, data_operator, media_buyer
  </required>
</input>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/core/dependencies.py | get_current_user(), require_role() |
  | backend/core/permissions.py | UserRole 枚举, 权限常量 |
  | backend/tests/test_permissions.py | 8 个权限测试用例 |
</deliverables>

<constraints>
  <rule>角色枚举仅包含 6 个合法角色</rule>
  <rule>权限不可继承（ceo 不自动拥有 admin 权限）</rule>
  <rule>每个用户仅有一个角色</rule>
  <rule>使用 Literal 类型约束角色值</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | Token 缺失 | AUTH_401 | 401 | 未认证 |
  | Token 无效 | AUTH_401 | 401 | 无效的 Token |
  | 无权限操作 | AUTH_403 | 403 | 无权限执行此操作 |
</error_handling>

<examples>
  <example name="权限通过">
    admin 调用 GET /api/v1/users → 成功
  </example>
  <example name="权限拒绝">
    pitcher 调用 POST /api/v1/users → {"code": "AUTH_403", "message": "无权限执行此操作"}
  </example>
</examples>

<output_format>
  <thinking>1. 设计依赖注入 2. 设计装饰器模式</thinking>
  <implementation>输出相关文件</implementation>
  <verification>pytest backend/tests/test_permissions.py -v</verification>
</output_format>

<acceptance_criteria>
  □ get_current_user 依赖注入可用
  □ require_role 装饰器可用
  □ 角色枚举仅 6 个值
  □ 无权限返回 AUTH_403
</acceptance_criteria>
```

---

## TASK-AUTH-005: 职责分离校验

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>auth</module>
  <task_id>TASK-AUTH-005</task_id>
  <prerequisites>TASK-AUTH-004 已完成</prerequisites>
  <sot>BR-AUTH-006, MASTER.md v4.6 §9 INV-004</sot>
</context>

<task>实现职责分离校验，防止同一用户执行互斥操作</task>

<input>
  <required>
    职责分离规则:
    1. 日报提交者 ≠ 日报审核者
    2. 充值申请者 ≠ 充值审批者
    3. 对账发起者 ≠ 对账审批者
  </required>
</input>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/core/permissions.py | check_separation_of_duties() |
  | backend/tests/test_permissions.py | 5 个职责分离测试 |
</deliverables>

<constraints>
  <rule>职责分离规则不可绕过</rule>
  <rule>admin 角色也受职责分离约束</rule>
  <rule>系统自动操作不受限制</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 违反职责分离 | BIZ_001 | 400 | 违反职责分离原则 |
</error_handling>

<examples>
  <example name="违规">
    pitcher_001 提交日报后尝试审核自己的日报 → BIZ_001
  </example>
  <example name="合规">
    pitcher_001 提交 → project_owner_002 审核 → 成功
  </example>
</examples>

<output_format>
  <thinking>1. 设计检查函数 2. 确定适用场景</thinking>
  <implementation>输出相关文件</implementation>
  <verification>pytest backend/tests/test_permissions.py::TestSOD -v</verification>
</output_format>

<acceptance_criteria>
  □ 日报提交者不能是审核者
  □ 充值申请者不能是审批者
  □ 违反返回 BIZ_001
</acceptance_criteria>
```

---

# M2 用户模块 (USER)

> 优先级: P0 | Phase: Phase 1 | 任务数: 5

## TASK-USER-001: 用户列表 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>user</module>
  <task_id>TASK-USER-001</task_id>
  <prerequisites>认证模块已完成</prerequisites>
  <sot>DATA_SCHEMA.md v5.6 §users, BR-USER-001</sot>
</context>

<task>实现 GET /api/v1/users 用户列表 API</task>

<input>
  <required>users 表, get_current_user 依赖</required>
  <data_isolation>admin 查看全部, 其他角色仅查看同 project_id</data_isolation>
</input>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/user.py | UserResponse, UserListResponse |
  | backend/services/user_service.py | list_users() |
  | backend/routers/users.py | GET /api/v1/users |
  | backend/tests/test_user_api.py | 5 个测试用例 |
</deliverables>

<constraints>
  <rule>分页参数: page 默认 1, page_size 默认 20 最大 100</rule>
  <rule>角色筛选仅接受 6 个白名单值</rule>
  <rule>返回字段: id, email, name, role, project_id, created_at</rule>
  <rule>非 admin 自动过滤: User.project_id == current_user.project_id</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 无效角色筛选 | VAL_001 | 400 | 无效的角色值 |
  | 未认证 | AUTH_401 | 401 | 未认证 |
</error_handling>

<examples>
  <example name="正常列表">
    <request>GET /api/v1/users?page=1&page_size=20</request>
    <response>{"code": 0, "data": {"items": [...], "total": 50, "page": 1, "page_size": 20}}</response>
  </example>
  <example name="角色筛选">
    <request>GET /api/v1/users?role=pitcher</request>
    <response>仅返回 pitcher 角色用户</response>
  </example>
  <example name="无效角色">
    <request>GET /api/v1/users?role=supervisor</request>
    <response>{"code": "VAL_001", "message": "无效的角色值"}</response>
  </example>
</examples>

<output_format>
  <thinking>1. 确认数据隔离逻辑 2. 设计分页 3. 角色筛选白名单</thinking>
  <implementation>依次输出 4 个文件</implementation>
  <verification>pytest backend/tests/test_user_api.py::TestListUsers -v</verification>
</output_format>

<acceptance_criteria>
  □ GET /api/v1/users 返回分页列表
  □ 支持 page, page_size 参数
  □ 支持 role 筛选
  □ 非 admin 只能查看同项目用户
</acceptance_criteria>
```

---

## TASK-USER-002: 用户详情 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>user</module>
  <task_id>TASK-USER-002</task_id>
  <prerequisites>TASK-USER-001 已完成</prerequisites>
  <sot>DATA_SCHEMA.md v5.6 §users, ERROR_CODES.md BIZ_002</sot>
</context>

<task>实现 GET /api/v1/users/{id} 用户详情 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/services/user_service.py | get_user() |
  | backend/routers/users.py | GET /api/v1/users/{id} |
  | backend/tests/test_user_api.py | 3 个详情测试 |
</deliverables>

<constraints>
  <rule>包含用户角色、关联项目信息</rule>
  <rule>返回字段: id, email, name, role, project_id, project_name, created_at</rule>
  <rule>非 admin 仅能查看同项目用户</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 用户不存在 | BIZ_002 | 404 | 用户不存在 |
  | 无权限查看 | AUTH_403 | 403 | 无权限查看此用户 |
</error_handling>

<examples>
  <example name="正常获取">
    <request>GET /api/v1/users/123</request>
    <response>{"code": 0, "data": {"id": 123, "email": "...", "role": "pitcher", ...}}</response>
  </example>
  <example name="不存在">
    <request>GET /api/v1/users/999</request>
    <response>{"code": "BIZ_002", "message": "用户不存在"}</response>
  </example>
</examples>

<output_format>
  <thinking>1. 设计权限检查 2. 关联查询项目信息</thinking>
  <implementation>输出相关文件</implementation>
  <verification>pytest backend/tests/test_user_api.py::TestGetUser -v</verification>
</output_format>

<acceptance_criteria>
  □ GET /api/v1/users/{id} 返回详情
  □ 用户不存在返回 BIZ_002
  □ 包含关联项目信息
</acceptance_criteria>
```

---

## TASK-USER-003: 创建用户 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>user</module>
  <task_id>TASK-USER-003</task_id>
  <prerequisites>TASK-USER-001 已完成</prerequisites>
  <sot>BR-USER-002/003, AUTH_SPEC.md</sot>
</context>

<task>实现 POST /api/v1/users 创建用户 API</task>

<input>
  <required>
    密码强度: 最少 8 位, 包含大小写, 包含数字
  </required>
</input>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/user.py | UserCreate |
  | backend/services/user_service.py | create_user() |
  | backend/routers/users.py | POST /api/v1/users |
  | backend/tests/test_user_api.py | 6 个创建测试 |
</deliverables>

<constraints>
  <rule>必须指定角色（仅 6 个白名单值）</rule>
  <rule>密码满足强度要求</rule>
  <rule>仅 admin/ceo 可创建用户</rule>
  <rule>邮箱和用户名唯一性检查</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 角色缺失 | VAL_001 | 400 | 角色不能为空 |
  | 密码太弱 | VAL_001 | 400 | 密码强度不足 |
  | 邮箱已存在 | BIZ_001 | 400 | 邮箱已被使用 |
  | 无权限 | AUTH_403 | 403 | 无权限创建用户 |
</error_handling>

<examples>
  <example name="正常创建">
    <request>POST /api/v1/users {"email": "new@example.com", "password": "Password123", "role": "pitcher", "name": "新用户"}</request>
    <response>{"code": 0, "data": {"id": 124, "email": "new@example.com", ...}}</response>
  </example>
  <example name="邮箱冲突">
    <request>POST /api/v1/users {"email": "existing@example.com", ...}</request>
    <response>{"code": "BIZ_001", "message": "邮箱已被使用"}</response>
  </example>
</examples>

<output_format>
  <thinking>1. 密码强度验证 2. 唯一性检查 3. 权限控制</thinking>
  <implementation>输出相关文件</implementation>
  <verification>pytest backend/tests/test_user_api.py::TestCreateUser -v</verification>
</output_format>

<acceptance_criteria>
  □ POST /api/v1/users 创建用户
  □ 必须指定角色
  □ 密码满足强度要求
  □ 仅 admin/ceo 可创建
</acceptance_criteria>
```

---

## TASK-USER-004: 更新用户 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>user</module>
  <task_id>TASK-USER-004</task_id>
  <prerequisites>TASK-USER-003 已完成</prerequisites>
  <sot>BR-USER-003/004</sot>
</context>

<task>实现 PUT /api/v1/users/{id} 更新用户 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/user.py | UserUpdate |
  | backend/services/user_service.py | update_user() |
  | backend/routers/users.py | PUT /api/v1/users/{id} |
  | backend/tests/test_user_api.py | 5 个更新测试 |
</deliverables>

<constraints>
  <rule>用户不能修改自己的角色（BR-USER-004）</rule>
  <rule>角色变更记录审计日志</rule>
  <rule>仅 admin/ceo 可修改用户</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 自我提权 | BIZ_001 | 400 | 不能修改自己的角色 |
  | 用户不存在 | BIZ_002 | 404 | 用户不存在 |
  | 邮箱冲突 | BIZ_001 | 400 | 邮箱已被使用 |
</error_handling>

<examples>
  <example name="正常更新">
    <request>PUT /api/v1/users/123 {"name": "新名字"}</request>
    <response>{"code": 0, "data": {"id": 123, "name": "新名字", ...}}</response>
  </example>
  <example name="自我提权">
    <request>admin_001 修改自己的角色为 ceo</request>
    <response>{"code": "BIZ_001", "message": "不能修改自己的角色"}</response>
  </example>
</examples>

<output_format>
  <thinking>1. 自我提权检查 2. 审计日志</thinking>
  <implementation>输出相关文件</implementation>
  <verification>pytest backend/tests/test_user_api.py::TestUpdateUser -v</verification>
</output_format>

<acceptance_criteria>
  □ PUT /api/v1/users/{id} 更新用户
  □ 不能修改自己的角色
  □ 角色变更记录日志
</acceptance_criteria>
```

---

## TASK-USER-005: 用户停用/启用 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>user</module>
  <task_id>TASK-USER-005</task_id>
  <prerequisites>TASK-USER-003 已完成</prerequisites>
  <sot>DATA_SCHEMA.md §users is_active, BR-USER-005</sot>
</context>

<task>实现 POST /api/v1/users/{id}/deactivate 和 /activate API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/services/user_service.py | deactivate_user(), activate_user() |
  | backend/routers/users.py | POST deactivate, activate |
  | backend/tests/test_user_api.py | 4 个停用/启用测试 |
</deliverables>

<constraints>
  <rule>停用后用户无法登录</rule>
  <rule>admin 角色不能被停用（BR-USER-005）</rule>
  <rule>仅 admin/ceo 可执行</rule>
  <rule>不能停用自己</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 停用 admin | BIZ_001 | 400 | 不能停用 admin 用户 |
  | 停用自己 | BIZ_001 | 400 | 不能停用自己 |
  | 用户不存在 | BIZ_002 | 404 | 用户不存在 |
</error_handling>

<examples>
  <example name="正常停用">
    <request>POST /api/v1/users/123/deactivate</request>
    <response>{"code": 0, "message": "用户已停用"}</response>
  </example>
  <example name="停用 admin">
    <request>POST /api/v1/users/{admin_id}/deactivate</request>
    <response>{"code": "BIZ_001", "message": "不能停用 admin 用户"}</response>
  </example>
</examples>

<output_format>
  <thinking>1. admin 保护 2. 自我保护</thinking>
  <implementation>输出相关文件</implementation>
  <verification>pytest backend/tests/test_user_api.py::TestDeactivate -v</verification>
</output_format>

<acceptance_criteria>
  □ POST deactivate/activate 可用
  □ admin 不能被停用
  □ 不能停用自己
  □ 停用后无法登录
</acceptance_criteria>
```
# M3 项目模块 (PROJ)

> 优先级: P0 | Phase: Phase 1 | 任务数: 6

## TASK-PROJ-001: 项目列表 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>project</module>
  <task_id>TASK-PROJ-001</task_id>
  <prerequisites>用户模块已完成</prerequisites>
  <sot>DATA_SCHEMA.md v5.6 §projects, BR-PROJ-001</sot>
</context>

<task>实现 GET /api/v1/projects 项目列表 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/project.py | ProjectResponse, ProjectListResponse |
  | backend/services/project_service.py | list_projects() |
  | backend/routers/projects.py | GET /api/v1/projects |
  | backend/tests/test_project_api.py | 5 个测试用例 |
</deliverables>

<constraints>
  <rule>支持分页: page, page_size</rule>
  <rule>支持状态筛选: active, inactive</rule>
  <rule>返回字段: id, name, client_name, billing_mode, status, created_at</rule>
  <rule>非 ceo/admin 仅查看已分配项目</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 未认证 | AUTH_401 | 401 | 未认证 |
</error_handling>

<examples>
  <example name="正常列表">
    <request>GET /api/v1/projects?status=active</request>
    <response>{"code": 0, "data": {"items": [...], "total": 10}}</response>
  </example>
</examples>

<output_format>
  <thinking>1. 数据权限隔离 2. 分页设计</thinking>
  <implementation>依次输出 4 个文件</implementation>
  <verification>pytest backend/tests/test_project_api.py::TestListProjects -v</verification>
</output_format>

<acceptance_criteria>
  □ GET /api/v1/projects 返回项目列表
  □ 支持分页和状态筛选
  □ 数据权限隔离生效
</acceptance_criteria>
```

---

## TASK-PROJ-002: 项目详情 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>project</module>
  <task_id>TASK-PROJ-002</task_id>
  <prerequisites>TASK-PROJ-001 已完成</prerequisites>
  <sot>DATA_SCHEMA.md v5.6 §projects</sot>
</context>

<task>实现 GET /api/v1/projects/{id} 项目详情 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/services/project_service.py | get_project() |
  | backend/routers/projects.py | GET /api/v1/projects/{id} |
  | backend/tests/test_project_api.py | 3 个详情测试 |
</deliverables>

<constraints>
  <rule>包含项目成员列表</rule>
  <rule>包含关联账户数量统计</rule>
  <rule>非项目成员无权查看（除 ceo/admin）</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 项目不存在 | BIZ_002 | 404 | 项目不存在 |
  | 无权限查看 | AUTH_403 | 403 | 无权限查看此项目 |
</error_handling>

<examples>
  <example name="正常获取">
    <request>GET /api/v1/projects/1</request>
    <response>{"code": 0, "data": {"id": 1, "name": "项目A", "members": [...], "account_count": 5}}</response>
  </example>
</examples>

<acceptance_criteria>
  □ GET /api/v1/projects/{id} 返回详情
  □ 包含成员列表和账户统计
  □ 权限控制生效
</acceptance_criteria>
```

---

## TASK-PROJ-003: 创建项目 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>project</module>
  <task_id>TASK-PROJ-003</task_id>
  <prerequisites>TASK-PROJ-001 已完成</prerequisites>
  <sot>BR-PROJ-002/003, DATA_SCHEMA.md §projects</sot>
</context>

<task>实现 POST /api/v1/projects 创建项目 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/project.py | ProjectCreate |
  | backend/services/project_service.py | create_project() |
  | backend/routers/projects.py | POST /api/v1/projects |
  | backend/tests/test_project_api.py | 5 个创建测试 |
</deliverables>

<constraints>
  <rule>必须指定 billing_mode: per_lead 或 fee_rate</rule>
  <rule>必须指定 project_owner</rule>
  <rule>仅 ceo/admin 可创建</rule>
  <rule>项目名称唯一性检查</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 名称重复 | BIZ_001 | 400 | 项目名称已存在 |
  | billing_mode 缺失 | VAL_001 | 400 | 计费模式不能为空 |
  | 无权限 | AUTH_403 | 403 | 无权限创建项目 |
</error_handling>

<examples>
  <example name="正常创建">
    <request>POST /api/v1/projects {"name": "新项目", "client_name": "客户A", "billing_mode": "per_lead", "project_owner_id": 10}</request>
    <response>{"code": 0, "data": {"id": 5, "name": "新项目", ...}}</response>
  </example>
</examples>

<acceptance_criteria>
  □ POST /api/v1/projects 创建项目
  □ 必须指定 billing_mode 和 project_owner
  □ 仅 ceo/admin 可创建
</acceptance_criteria>
```

---

## TASK-PROJ-004: 更新项目 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>project</module>
  <task_id>TASK-PROJ-004</task_id>
  <prerequisites>TASK-PROJ-003 已完成</prerequisites>
  <sot>BR-PROJ-004</sot>
</context>

<task>实现 PUT /api/v1/projects/{id} 更新项目 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/project.py | ProjectUpdate |
  | backend/services/project_service.py | update_project() |
  | backend/routers/projects.py | PUT /api/v1/projects/{id} |
  | backend/tests/test_project_api.py | 4 个更新测试 |
</deliverables>

<constraints>
  <rule>billing_mode 变更需记录日志</rule>
  <rule>project_owner 变更需记录日志</rule>
  <rule>仅 ceo/admin 可更新</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 项目不存在 | BIZ_002 | 404 | 项目不存在 |
  | 名称冲突 | BIZ_001 | 400 | 项目名称已存在 |
</error_handling>

<acceptance_criteria>
  □ PUT /api/v1/projects/{id} 更新项目
  □ 关键变更记录日志
  □ 仅 ceo/admin 可更新
</acceptance_criteria>
```

---

## TASK-PROJ-005: 项目成员管理 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>project</module>
  <task_id>TASK-PROJ-005</task_id>
  <prerequisites>TASK-PROJ-003 已完成</prerequisites>
  <sot>DATA_SCHEMA.md §project_members, BR-PROJ-005</sot>
</context>

<task>实现项目成员增删查 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/project_member.py | ProjectMemberCreate, ProjectMemberResponse |
  | backend/services/project_member_service.py | add_member(), remove_member(), list_members() |
  | backend/routers/project_members.py | GET/POST/DELETE /api/v1/projects/{id}/members |
  | backend/tests/test_project_member_api.py | 6 个测试用例 |
</deliverables>

<constraints>
  <rule>一个用户可属于多个项目</rule>
  <rule>project_owner 自动成为项目成员</rule>
  <rule>ceo/admin/project_owner 可管理成员</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 用户已是成员 | BIZ_001 | 400 | 用户已是项目成员 |
  | 用户不存在 | BIZ_002 | 404 | 用户不存在 |
  | 移除 project_owner | BIZ_001 | 400 | 不能移除项目负责人 |
</error_handling>

<examples>
  <example name="添加成员">
    <request>POST /api/v1/projects/1/members {"user_id": 10}</request>
    <response>{"code": 0, "message": "成员添加成功"}</response>
  </example>
</examples>

<acceptance_criteria>
  □ 成员增删查 API 可用
  □ 不能移除 project_owner
  □ 权限控制生效
</acceptance_criteria>
```

---

## TASK-PROJ-006: 项目统计 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>project</module>
  <task_id>TASK-PROJ-006</task_id>
  <prerequisites>TASK-PROJ-002 已完成</prerequisites>
  <sot>PRD.md v2.2 §2</sot>
</context>

<task>实现 GET /api/v1/projects/{id}/stats 项目统计 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/project.py | ProjectStatsResponse |
  | backend/services/project_service.py | get_project_stats() |
  | backend/routers/projects.py | GET /api/v1/projects/{id}/stats |
  | backend/tests/test_project_api.py | 3 个统计测试 |
</deliverables>

<constraints>
  <rule>统计指标: 账户数、总消耗、总进粉、平均 CPL</rule>
  <rule>支持日期范围筛选</rule>
  <rule>仅项目成员可查看</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 项目不存在 | BIZ_002 | 404 | 项目不存在 |
</error_handling>

<examples>
  <example name="获取统计">
    <request>GET /api/v1/projects/1/stats?start_date=2025-01-01&end_date=2025-01-31</request>
    <response>{"code": 0, "data": {"account_count": 10, "total_spend": 50000, "total_conversions": 1000, "avg_cpl": 50}}</response>
  </example>
</examples>

<acceptance_criteria>
  □ GET stats 返回统计数据
  □ 支持日期范围筛选
  □ 仅项目成员可查看
</acceptance_criteria>
```

---

# M4 渠道模块 (CHANNEL)

> 优先级: P1 | Phase: Phase 1 | 任务数: 4

## TASK-CHAN-001: 渠道列表 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>channel</module>
  <task_id>TASK-CHAN-001</task_id>
  <prerequisites>项目模块已完成</prerequisites>
  <sot>DATA_SCHEMA.md v5.6 §channels, BR-CHAN-001</sot>
</context>

<task>实现 GET /api/v1/channels 渠道列表 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/channel.py | ChannelResponse, ChannelListResponse |
  | backend/services/channel_service.py | list_channels() |
  | backend/routers/channels.py | GET /api/v1/channels |
  | backend/tests/test_channel_api.py | 4 个测试用例 |
</deliverables>

<constraints>
  <rule>渠道属于平台级别（不属于项目）</rule>
  <rule>返回字段: id, name, platform, status, fee_rate</rule>
  <rule>支持平台筛选: wechat, douyin, kuaishou, baidu 等</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 未认证 | AUTH_401 | 401 | 未认证 |
</error_handling>

<examples>
  <example name="正常列表">
    <request>GET /api/v1/channels?platform=wechat</request>
    <response>{"code": 0, "data": {"items": [{"id": 1, "name": "微信渠道A", "platform": "wechat", ...}]}}</response>
  </example>
</examples>

<acceptance_criteria>
  □ GET /api/v1/channels 返回渠道列表
  □ 支持平台筛选
</acceptance_criteria>
```

---

## TASK-CHAN-002: 创建渠道 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>channel</module>
  <task_id>TASK-CHAN-002</task_id>
  <prerequisites>TASK-CHAN-001 已完成</prerequisites>
  <sot>BR-CHAN-002/003</sot>
</context>

<task>实现 POST /api/v1/channels 创建渠道 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/channel.py | ChannelCreate |
  | backend/services/channel_service.py | create_channel() |
  | backend/routers/channels.py | POST /api/v1/channels |
  | backend/tests/test_channel_api.py | 4 个创建测试 |
</deliverables>

<constraints>
  <rule>仅 account_manager/admin 可创建</rule>
  <rule>必须指定平台和手续费率</rule>
  <rule>渠道名称唯一</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 名称重复 | BIZ_001 | 400 | 渠道名称已存在 |
  | 无权限 | AUTH_403 | 403 | 无权限创建渠道 |
</error_handling>

<acceptance_criteria>
  □ POST /api/v1/channels 创建渠道
  □ 仅 account_manager/admin 可创建
  □ 名称唯一性检查
</acceptance_criteria>
```

---

## TASK-CHAN-003: 渠道评审 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>channel</module>
  <task_id>TASK-CHAN-003</task_id>
  <prerequisites>TASK-CHAN-002 已完成</prerequisites>
  <sot>BR-CHAN-004, STATE_MACHINE.md §channel</sot>
</context>

<task>实现 POST /api/v1/channels/{id}/review 渠道评审 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/services/channel_service.py | review_channel() |
  | backend/routers/channels.py | POST /api/v1/channels/{id}/review |
  | backend/tests/test_channel_api.py | 4 个评审测试 |
</deliverables>

<constraints>
  <rule>仅 project_owner/admin 可审批</rule>
  <rule>状态流转: pending → approved/rejected</rule>
  <rule>职责分离: 创建者不能是审批者</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 状态非法 | STATE_400 | 400 | 状态转换非法 |
  | 职责分离 | BIZ_001 | 400 | 违反职责分离原则 |
</error_handling>

<examples>
  <example name="审批通过">
    <request>POST /api/v1/channels/1/review {"action": "approve"}</request>
    <response>{"code": 0, "message": "渠道已审批通过"}</response>
  </example>
</examples>

<acceptance_criteria>
  □ 评审 API 可用
  □ 状态流转正确
  □ 职责分离生效
</acceptance_criteria>
```

---

## TASK-CHAN-004: 更新渠道 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>channel</module>
  <task_id>TASK-CHAN-004</task_id>
  <prerequisites>TASK-CHAN-002 已完成</prerequisites>
  <sot>BR-CHAN-005</sot>
</context>

<task>实现 PUT /api/v1/channels/{id} 更新渠道 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/channel.py | ChannelUpdate |
  | backend/services/channel_service.py | update_channel() |
  | backend/routers/channels.py | PUT /api/v1/channels/{id} |
  | backend/tests/test_channel_api.py | 3 个更新测试 |
</deliverables>

<constraints>
  <rule>仅 account_manager/admin 可更新</rule>
  <rule>fee_rate 变更记录日志</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 渠道不存在 | BIZ_002 | 404 | 渠道不存在 |
</error_handling>

<acceptance_criteria>
  □ PUT /api/v1/channels/{id} 更新渠道
  □ fee_rate 变更记录日志
</acceptance_criteria>
```

---

# M5 广告账户模块 (ACCT)

> 优先级: P0 | Phase: Phase 1 | 任务数: 6

## TASK-ACCT-001: 账户列表 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>ad_account</module>
  <task_id>TASK-ACCT-001</task_id>
  <prerequisites>项目模块、渠道模块已完成</prerequisites>
  <sot>DATA_SCHEMA.md v5.6 §ad_accounts, BR-ACCT-001</sot>
</context>

<task>实现 GET /api/v1/ad-accounts 广告账户列表 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/ad_account.py | AdAccountResponse, AdAccountListResponse |
  | backend/services/ad_account_service.py | list_ad_accounts() |
  | backend/routers/ad_accounts.py | GET /api/v1/ad-accounts |
  | backend/tests/test_ad_account_api.py | 5 个测试用例 |
</deliverables>

<constraints>
  <rule>返回字段: id, name, platform, project_id, assigned_pitcher_id, status, balance</rule>
  <rule>支持筛选: project_id, status, assigned_pitcher_id</rule>
  <rule>pitcher 仅查看已分配账户</rule>
  <rule>project_owner 查看项目内所有账户</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 未认证 | AUTH_401 | 401 | 未认证 |
</error_handling>

<examples>
  <example name="正常列表">
    <request>GET /api/v1/ad-accounts?project_id=1&status=active</request>
    <response>{"code": 0, "data": {"items": [...], "total": 20}}</response>
  </example>
</examples>

<acceptance_criteria>
  □ GET /api/v1/ad-accounts 返回账户列表
  □ 支持多维度筛选
  □ 数据权限隔离生效
</acceptance_criteria>
```

---

## TASK-ACCT-002: 账户详情 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>ad_account</module>
  <task_id>TASK-ACCT-002</task_id>
  <prerequisites>TASK-ACCT-001 已完成</prerequisites>
  <sot>DATA_SCHEMA.md v5.6 §ad_accounts</sot>
</context>

<task>实现 GET /api/v1/ad-accounts/{id} 账户详情 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/services/ad_account_service.py | get_ad_account() |
  | backend/routers/ad_accounts.py | GET /api/v1/ad-accounts/{id} |
  | backend/tests/test_ad_account_api.py | 3 个详情测试 |
</deliverables>

<constraints>
  <rule>包含关联项目、渠道、投手信息</rule>
  <rule>包含余额和最近充值记录</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 账户不存在 | BIZ_002 | 404 | 账户不存在 |
  | 无权限 | AUTH_403 | 403 | 无权限查看此账户 |
</error_handling>

<acceptance_criteria>
  □ GET /api/v1/ad-accounts/{id} 返回详情
  □ 包含关联信息
</acceptance_criteria>
```

---

## TASK-ACCT-003: 创建账户 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>ad_account</module>
  <task_id>TASK-ACCT-003</task_id>
  <prerequisites>TASK-ACCT-001 已完成</prerequisites>
  <sot>BR-ACCT-002/003</sot>
</context>

<task>实现 POST /api/v1/ad-accounts 创建账户 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/ad_account.py | AdAccountCreate |
  | backend/services/ad_account_service.py | create_ad_account() |
  | backend/routers/ad_accounts.py | POST /api/v1/ad-accounts |
  | backend/tests/test_ad_account_api.py | 5 个创建测试 |
</deliverables>

<constraints>
  <rule>仅 account_manager/admin 可创建</rule>
  <rule>必须关联项目和渠道</rule>
  <rule>账户名称在项目内唯一</rule>
  <rule>初始余额为 0</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 项目不存在 | BIZ_002 | 404 | 项目不存在 |
  | 渠道不存在 | BIZ_002 | 404 | 渠道不存在 |
  | 名称重复 | BIZ_001 | 400 | 账户名称已存在 |
</error_handling>

<acceptance_criteria>
  □ POST /api/v1/ad-accounts 创建账户
  □ 必须关联项目和渠道
  □ 初始余额为 0
</acceptance_criteria>
```

---

## TASK-ACCT-004: 账户分配 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>ad_account</module>
  <task_id>TASK-ACCT-004</task_id>
  <prerequisites>TASK-ACCT-003 已完成</prerequisites>
  <sot>BR-ACCT-004, STATE_MACHINE.md §ad_account</sot>
</context>

<task>实现 POST /api/v1/ad-accounts/{id}/assign 账户分配 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/services/ad_account_service.py | assign_account() |
  | backend/routers/ad_accounts.py | POST /api/v1/ad-accounts/{id}/assign |
  | backend/tests/test_ad_account_api.py | 4 个分配测试 |
</deliverables>

<constraints>
  <rule>仅 account_manager/admin 可分配</rule>
  <rule>只能分配给 pitcher 角色</rule>
  <rule>被分配者必须是项目成员</rule>
  <rule>状态流转: unassigned → assigned</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 非 pitcher 角色 | BIZ_001 | 400 | 只能分配给投手 |
  | 非项目成员 | BIZ_001 | 400 | 用户不是项目成员 |
  | 已分配 | STATE_400 | 400 | 账户已分配 |
</error_handling>

<examples>
  <example name="正常分配">
    <request>POST /api/v1/ad-accounts/1/assign {"pitcher_id": 10}</request>
    <response>{"code": 0, "message": "账户已分配"}</response>
  </example>
</examples>

<acceptance_criteria>
  □ 分配 API 可用
  □ 只能分配给项目内的 pitcher
  □ 状态流转正确
</acceptance_criteria>
```

---

## TASK-ACCT-005: 账户状态管理 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>ad_account</module>
  <task_id>TASK-ACCT-005</task_id>
  <prerequisites>TASK-ACCT-004 已完成</prerequisites>
  <sot>STATE_MACHINE.md v2.7 §ad_account</sot>
</context>

<task>实现账户启用/暂停/关闭状态管理 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/services/ad_account_service.py | activate(), suspend(), close() |
  | backend/routers/ad_accounts.py | POST activate/suspend/close |
  | backend/tests/test_ad_account_api.py | 5 个状态管理测试 |
</deliverables>

<constraints>
  <rule>状态: active, suspended, closed</rule>
  <rule>closed 是终态，不可回退</rule>
  <rule>暂停账户可重新激活</rule>
  <rule>仅 account_manager/admin 可操作</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 终态回退 | STATE_402 | 400 | 已关闭账户不可操作 |
  | 非法转换 | STATE_400 | 400 | 状态转换非法 |
</error_handling>

<acceptance_criteria>
  □ 启用/暂停/关闭 API 可用
  □ closed 是终态
  □ 状态流转正确
</acceptance_criteria>
```

---

## TASK-ACCT-006: 账户余额查询 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>ad_account</module>
  <task_id>TASK-ACCT-006</task_id>
  <prerequisites>TASK-ACCT-002 已完成</prerequisites>
  <sot>LEDGER_SOT.md v1.2</sot>
</context>

<task>实现 GET /api/v1/ad-accounts/{id}/balance 余额查询 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/ad_account.py | BalanceResponse |
  | backend/services/ad_account_service.py | get_balance() |
  | backend/routers/ad_accounts.py | GET /api/v1/ad-accounts/{id}/balance |
  | backend/tests/test_ad_account_api.py | 3 个余额测试 |
</deliverables>

<constraints>
  <rule>余额 = 充值总额 - 消耗总额（从账本计算）</rule>
  <rule>返回: balance, total_topup, total_spend</rule>
  <rule>禁止直接修改 balance 字段</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 账户不存在 | BIZ_002 | 404 | 账户不存在 |
</error_handling>

<examples>
  <example name="查询余额">
    <request>GET /api/v1/ad-accounts/1/balance</request>
    <response>{"code": 0, "data": {"balance": 5000, "total_topup": 10000, "total_spend": 5000}}</response>
  </example>
</examples>

<acceptance_criteria>
  □ 余额从账本计算，非直接读取
  □ 返回余额、充值总额、消耗总额
</acceptance_criteria>
```

---

# M6 日报模块 (RPT)

> 优先级: P0 | Phase: Phase 1 (简化) + Phase 2 (完整) | 任务数: 9

## Phase 说明

```
Phase 1 状态机（3 状态，当前使用）:
  raw_submitted → trend_ok → final_confirmed

Phase 2 状态机（8 状态，未来启用）:
  raw_submitted → trend_pending → trend_ok/trend_flagged
  → trend_resolved → final_pending → final_confirmed → final_locked
```

## TASK-RPT-001: 日报列表 API (Phase 1)

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>daily_report</module>
  <task_id>TASK-RPT-001</task_id>
  <prerequisites>账户模块已完成</prerequisites>
  <sot>DATA_SCHEMA.md v5.6 §daily_reports, STATE_MACHINE.md v2.7</sot>
  <phase>Phase 1</phase>
</context>

<task>实现 GET /api/v1/daily-reports 日报列表 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/daily_report.py | DailyReportResponse, DailyReportListResponse |
  | backend/services/daily_report_service.py | list_daily_reports() |
  | backend/routers/daily_reports.py | GET /api/v1/daily-reports |
  | backend/tests/test_daily_report_api.py | 5 个测试用例 |
</deliverables>

<constraints>
  <rule>Phase 1 状态仅 3 个: raw_submitted, trend_ok, final_confirmed</rule>
  <rule>支持筛选: ad_account_id, report_date, status, pitcher_id</rule>
  <rule>pitcher 仅查看自己的日报</rule>
  <rule>project_owner 查看项目内所有日报</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 未认证 | AUTH_401 | 401 | 未认证 |
</error_handling>

<examples>
  <example name="正常列表">
    <request>GET /api/v1/daily-reports?report_date=2025-01-15</request>
    <response>{"code": 0, "data": {"items": [...], "total": 50}}</response>
  </example>
</examples>

<acceptance_criteria>
  □ GET /api/v1/daily-reports 返回日报列表
  □ Phase 1 状态仅 3 个
  □ 数据权限隔离生效
</acceptance_criteria>
```

---

## TASK-RPT-002: 提交日报 API (Phase 1)

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>daily_report</module>
  <task_id>TASK-RPT-002</task_id>
  <prerequisites>TASK-RPT-001 已完成</prerequisites>
  <sot>BR-RPT-001/002, STATE_MACHINE.md v2.7</sot>
  <phase>Phase 1</phase>
</context>

<task>实现 POST /api/v1/daily-reports 提交日报 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/daily_report.py | DailyReportCreate |
  | backend/services/daily_report_service.py | create_daily_report() |
  | backend/routers/daily_reports.py | POST /api/v1/daily-reports |
  | backend/tests/test_daily_report_api.py | 6 个提交测试 |
</deliverables>

<constraints>
  <rule>仅 pitcher 可提交</rule>
  <rule>只能提交已分配账户的日报</rule>
  <rule>同一账户同一日期只能提交一次</rule>
  <rule>初始状态: raw_submitted</rule>
  <rule>必填字段: ad_account_id, report_date, spend, conversions</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 非分配账户 | AUTH_403 | 403 | 无权限提交此账户日报 |
  | 重复提交 | BIZ_001 | 400 | 该日期已提交日报 |
  | 非 pitcher | AUTH_403 | 403 | 仅投手可提交日报 |
</error_handling>

<examples>
  <example name="正常提交">
    <request>POST /api/v1/daily-reports {"ad_account_id": 1, "report_date": "2025-01-15", "spend": 1000, "conversions": 50}</request>
    <response>{"code": 0, "data": {"id": 100, "status": "raw_submitted", ...}}</response>
  </example>
</examples>

<acceptance_criteria>
  □ POST /api/v1/daily-reports 提交日报
  □ 初始状态 raw_submitted
  □ 同一账户同一日期不可重复提交
</acceptance_criteria>
```

---

## TASK-RPT-003: 确认日报 API (Phase 1)

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>daily_report</module>
  <task_id>TASK-RPT-003</task_id>
  <prerequisites>TASK-RPT-002 已完成</prerequisites>
  <sot>BR-RPT-003, STATE_MACHINE.md v2.7</sot>
  <phase>Phase 1</phase>
</context>

<task>实现 POST /api/v1/daily-reports/{id}/confirm 确认日报 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/services/daily_report_service.py | confirm_trend(), confirm_final() |
  | backend/routers/daily_reports.py | POST confirm-trend, confirm-final |
  | backend/tests/test_daily_report_api.py | 5 个确认测试 |
</deliverables>

<constraints>
  <rule>Phase 1 状态流转: raw_submitted → trend_ok → final_confirmed</rule>
  <rule>confirm-trend: 仅 project_owner 可执行</rule>
  <rule>confirm-final: 仅 project_owner 可执行</rule>
  <rule>职责分离: 提交者不能是确认者</rule>
  <rule>Phase 1 原则: 只提示不阻断，异常只高亮显示</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 状态非法 | STATE_400 | 400 | 状态转换非法 |
  | 职责分离 | BIZ_001 | 400 | 违反职责分离原则 |
  | 无权限 | AUTH_403 | 403 | 仅项目负责人可确认 |
</error_handling>

<examples>
  <example name="确认趋势">
    <request>POST /api/v1/daily-reports/100/confirm-trend</request>
    <response>{"code": 0, "data": {"id": 100, "status": "trend_ok"}}</response>
  </example>
</examples>

<acceptance_criteria>
  □ confirm-trend 和 confirm-final API 可用
  □ 状态流转正确
  □ 职责分离生效
</acceptance_criteria>
```

---

## TASK-RPT-007: 日报统计 API (Phase 1)

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>daily_report</module>
  <task_id>TASK-RPT-007</task_id>
  <prerequisites>TASK-RPT-001 已完成</prerequisites>
  <sot>PRD.md v2.2 §2</sot>
  <phase>Phase 1</phase>
</context>

<task>实现 GET /api/v1/daily-reports/stats 日报统计 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/daily_report.py | DailyReportStatsResponse |
  | backend/services/daily_report_service.py | get_stats() |
  | backend/routers/daily_reports.py | GET /api/v1/daily-reports/stats |
  | backend/tests/test_daily_report_api.py | 3 个统计测试 |
</deliverables>

<constraints>
  <rule>统计指标: 总消耗、总进粉、平均 CPL、日报数量</rule>
  <rule>支持日期范围、项目、投手筛选</rule>
  <rule>CPL = spend / conversions（0 进粉时显示 N/A）</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 无数据 | - | 200 | 返回零值统计 |
</error_handling>

<examples>
  <example name="获取统计">
    <request>GET /api/v1/daily-reports/stats?start_date=2025-01-01&end_date=2025-01-31</request>
    <response>{"code": 0, "data": {"total_spend": 100000, "total_conversions": 2000, "avg_cpl": 50, "report_count": 300}}</response>
  </example>
</examples>

<acceptance_criteria>
  □ GET stats 返回统计数据
  □ 0 进粉时 CPL 显示 N/A
  □ 支持多维度筛选
</acceptance_criteria>
```

---

## TASK-RPT-004 ~ 006, 008 ~ 009 (Phase 2)

> Phase 2 任务在 Phase 1 稳定 2 个月后启动，此处仅列出任务清单：

| 任务 | 功能 | Phase |
|------|------|-------|
| TASK-RPT-004 | 趋势审核 API (8 状态机) | Phase 2 |
| TASK-RPT-005 | 异常标记 API | Phase 2 |
| TASK-RPT-006 | 异常解决 API | Phase 2 |
| TASK-RPT-008 | 日报锁定 API | Phase 2 |
| TASK-RPT-009 | 批量操作 API | Phase 2 |
# M7 充值模块 (FIN)

> 优先级: P1 | Phase: Phase 1 | 任务数: 7

## 充值状态机

```
draft → pending_review → approved → paid → completed
                      ↘ rejected
draft → cancelled
```

## TASK-FIN-001: 充值申请列表 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>topup</module>
  <task_id>TASK-FIN-001</task_id>
  <prerequisites>账户模块已完成</prerequisites>
  <sot>DATA_SCHEMA.md v5.6 §topup_requests, BR-FIN-001</sot>
</context>

<task>实现 GET /api/v1/topup-requests 充值申请列表 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/topup.py | TopupRequestResponse, TopupRequestListResponse |
  | backend/services/topup_service.py | list_topup_requests() |
  | backend/routers/topup.py | GET /api/v1/topup-requests |
  | backend/tests/test_topup_api.py | 5 个测试用例 |
</deliverables>

<constraints>
  <rule>返回字段: id, ad_account_id, amount, status, created_by, created_at</rule>
  <rule>支持筛选: ad_account_id, status, created_by</rule>
  <rule>pitcher 仅查看自己创建的申请</rule>
  <rule>finance 查看所有待审批申请</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 未认证 | AUTH_401 | 401 | 未认证 |
</error_handling>

<examples>
  <example name="正常列表">
    <request>GET /api/v1/topup-requests?status=pending_review</request>
    <response>{"code": 0, "data": {"items": [...], "total": 10}}</response>
  </example>
</examples>

<acceptance_criteria>
  □ GET /api/v1/topup-requests 返回充值申请列表
  □ 支持状态筛选
  □ 数据权限隔离生效
</acceptance_criteria>
```

---

## TASK-FIN-002: 创建充值申请 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>topup</module>
  <task_id>TASK-FIN-002</task_id>
  <prerequisites>TASK-FIN-001 已完成</prerequisites>
  <sot>BR-FIN-002/003, STATE_MACHINE.md §topup</sot>
</context>

<task>实现 POST /api/v1/topup-requests 创建充值申请 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/topup.py | TopupRequestCreate |
  | backend/services/topup_service.py | create_topup_request() |
  | backend/routers/topup.py | POST /api/v1/topup-requests |
  | backend/tests/test_topup_api.py | 5 个创建测试 |
</deliverables>

<constraints>
  <rule>pitcher/account_manager 可创建</rule>
  <rule>必须关联账户</rule>
  <rule>金额必须 > 0</rule>
  <rule>初始状态: draft 或 pending_review</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 金额非法 | BIZ_100 | 400 | 金额必须大于 0 |
  | 账户不存在 | BIZ_002 | 404 | 账户不存在 |
</error_handling>

<examples>
  <example name="正常创建">
    <request>POST /api/v1/topup-requests {"ad_account_id": 1, "amount": 5000}</request>
    <response>{"code": 0, "data": {"id": 50, "status": "pending_review", ...}}</response>
  </example>
</examples>

<acceptance_criteria>
  □ POST /api/v1/topup-requests 创建充值申请
  □ 金额验证
  □ 关联账户验证
</acceptance_criteria>
```

---

## TASK-FIN-003: 提交充值申请 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>topup</module>
  <task_id>TASK-FIN-003</task_id>
  <prerequisites>TASK-FIN-002 已完成</prerequisites>
  <sot>STATE_MACHINE.md §topup</sot>
</context>

<task>实现 POST /api/v1/topup-requests/{id}/submit 提交充值申请 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/services/topup_service.py | submit_topup_request() |
  | backend/routers/topup.py | POST /api/v1/topup-requests/{id}/submit |
  | backend/tests/test_topup_api.py | 3 个提交测试 |
</deliverables>

<constraints>
  <rule>仅创建者可提交</rule>
  <rule>状态流转: draft → pending_review</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 非 draft 状态 | STATE_400 | 400 | 状态转换非法 |
  | 非创建者 | AUTH_403 | 403 | 仅创建者可提交 |
</error_handling>

<acceptance_criteria>
  □ 提交 API 可用
  □ 状态流转正确
</acceptance_criteria>
```

---

## TASK-FIN-004: 审批充值申请 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>topup</module>
  <task_id>TASK-FIN-004</task_id>
  <prerequisites>TASK-FIN-003 已完成</prerequisites>
  <sot>BR-FIN-004, STATE_MACHINE.md §topup</sot>
</context>

<task>实现 POST /api/v1/topup-requests/{id}/approve 和 /reject 审批 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/services/topup_service.py | approve_topup(), reject_topup() |
  | backend/routers/topup.py | POST approve, reject |
  | backend/tests/test_topup_api.py | 5 个审批测试 |
</deliverables>

<constraints>
  <rule>仅 finance/admin 可审批</rule>
  <rule>状态流转: pending_review → approved/rejected</rule>
  <rule>职责分离: 申请者不能是审批者</rule>
  <rule>rejected 需填写拒绝原因</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 职责分离 | BIZ_001 | 400 | 违反职责分离原则 |
  | 状态非法 | STATE_400 | 400 | 状态转换非法 |
  | 拒绝无原因 | VAL_001 | 400 | 拒绝原因不能为空 |
</error_handling>

<examples>
  <example name="审批通过">
    <request>POST /api/v1/topup-requests/50/approve</request>
    <response>{"code": 0, "data": {"id": 50, "status": "approved"}}</response>
  </example>
  <example name="审批拒绝">
    <request>POST /api/v1/topup-requests/50/reject {"reason": "金额过大"}</request>
    <response>{"code": 0, "data": {"id": 50, "status": "rejected"}}</response>
  </example>
</examples>

<acceptance_criteria>
  □ approve 和 reject API 可用
  □ 职责分离生效
  □ rejected 需填写原因
</acceptance_criteria>
```

---

## TASK-FIN-005: 确认付款 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>topup</module>
  <task_id>TASK-FIN-005</task_id>
  <prerequisites>TASK-FIN-004 已完成</prerequisites>
  <sot>STATE_MACHINE.md §topup</sot>
</context>

<task>实现 POST /api/v1/topup-requests/{id}/pay 确认付款 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/services/topup_service.py | confirm_payment() |
  | backend/routers/topup.py | POST /api/v1/topup-requests/{id}/pay |
  | backend/tests/test_topup_api.py | 3 个付款测试 |
</deliverables>

<constraints>
  <rule>仅 finance 可确认付款</rule>
  <rule>状态流转: approved → paid</rule>
  <rule>需上传付款凭证（可选）</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 非 approved 状态 | STATE_400 | 400 | 状态转换非法 |
</error_handling>

<acceptance_criteria>
  □ 确认付款 API 可用
  □ 状态流转正确
</acceptance_criteria>
```

---

## TASK-FIN-006: 确认到账 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>topup</module>
  <task_id>TASK-FIN-006</task_id>
  <prerequisites>TASK-FIN-005 已完成</prerequisites>
  <sot>BR-FIN-005, STATE_MACHINE.md §topup, LEDGER_SOT.md v1.2</sot>
</context>

<task>实现 POST /api/v1/topup-requests/{id}/complete 确认到账 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/services/topup_service.py | confirm_arrival() |
  | backend/routers/topup.py | POST /api/v1/topup-requests/{id}/complete |
  | backend/tests/test_topup_api.py | 4 个到账测试 |
</deliverables>

<constraints>
  <rule>finance/account_manager 可确认到账</rule>
  <rule>状态流转: paid → completed</rule>
  <rule>到账后写入账本（ledger_entries）</rule>
  <rule>账本类型: topup</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 非 paid 状态 | STATE_400 | 400 | 状态转换非法 |
</error_handling>

<examples>
  <example name="确认到账">
    <request>POST /api/v1/topup-requests/50/complete {"actual_amount": 5000}</request>
    <response>{"code": 0, "data": {"id": 50, "status": "completed"}}</response>
  </example>
</examples>

<acceptance_criteria>
  □ 确认到账 API 可用
  □ 到账后写入账本
  □ 状态变为 completed
</acceptance_criteria>
```

---

## TASK-FIN-007: 取消充值申请 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>topup</module>
  <task_id>TASK-FIN-007</task_id>
  <prerequisites>TASK-FIN-002 已完成</prerequisites>
  <sot>STATE_MACHINE.md §topup</sot>
</context>

<task>实现 POST /api/v1/topup-requests/{id}/cancel 取消充值申请 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/services/topup_service.py | cancel_topup_request() |
  | backend/routers/topup.py | POST /api/v1/topup-requests/{id}/cancel |
  | backend/tests/test_topup_api.py | 3 个取消测试 |
</deliverables>

<constraints>
  <rule>仅创建者可取消</rule>
  <rule>仅 draft/pending_review 状态可取消</rule>
  <rule>状态流转: draft/pending_review → cancelled</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 非创建者 | AUTH_403 | 403 | 仅创建者可取消 |
  | 已审批 | STATE_400 | 400 | 已审批申请不可取消 |
</error_handling>

<acceptance_criteria>
  □ 取消 API 可用
  □ 仅 draft/pending_review 可取消
</acceptance_criteria>
```

---

# M8 账本模块 (LEDGER)

> 优先级: P2 | Phase: Phase 1 | 任务数: 4

## TASK-LEDGER-001: 账本流水列表 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>ledger</module>
  <task_id>TASK-LEDGER-001</task_id>
  <prerequisites>充值模块、日报模块已完成</prerequisites>
  <sot>LEDGER_SOT.md v1.2, DATA_SCHEMA.md v5.6 §ledger_entries</sot>
</context>

<task>实现 GET /api/v1/ledger-entries 账本流水列表 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/ledger.py | LedgerEntryResponse, LedgerEntryListResponse |
  | backend/services/ledger_service.py | list_ledger_entries() |
  | backend/routers/ledger.py | GET /api/v1/ledger-entries |
  | backend/tests/test_ledger_api.py | 5 个测试用例 |
</deliverables>

<constraints>
  <rule>返回字段: id, ad_account_id, entry_type, amount, balance_after, created_at</rule>
  <rule>entry_type: topup, spend, adjustment, reversal</rule>
  <rule>支持筛选: ad_account_id, entry_type, date_range</rule>
  <rule>按时间倒序排列</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 未认证 | AUTH_401 | 401 | 未认证 |
</error_handling>

<examples>
  <example name="正常列表">
    <request>GET /api/v1/ledger-entries?ad_account_id=1&entry_type=topup</request>
    <response>{"code": 0, "data": {"items": [...], "total": 20}}</response>
  </example>
</examples>

<acceptance_criteria>
  □ GET /api/v1/ledger-entries 返回流水列表
  □ 支持多维度筛选
  □ 时间倒序排列
</acceptance_criteria>
```

---

## TASK-LEDGER-002: 写入账本 Service

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>ledger</module>
  <task_id>TASK-LEDGER-002</task_id>
  <prerequisites>TASK-LEDGER-001 已完成</prerequisites>
  <sot>LEDGER_SOT.md v1.2 §写入规则</sot>
</context>

<task>实现账本写入 Service（内部调用，非 API）</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/services/ledger_service.py | create_entry(), create_topup_entry(), create_spend_entry() |
  | backend/tests/test_ledger_service.py | 6 个写入测试 |
</deliverables>

<constraints>
  <rule>账本只增不改（append-only）</rule>
  <rule>每条记录计算 balance_after</rule>
  <rule>必须关联 source_type 和 source_id（溯源）</rule>
  <rule>金额精度: 2 位小数</rule>
  <rule>禁止直接修改 ad_account.balance 字段</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 余额不足 | BIZ_101 | 400 | 余额不足 |
  | 金额非法 | BIZ_100 | 400 | 金额必须大于 0 |
</error_handling>

<examples>
  <example name="充值入账">
    create_topup_entry(ad_account_id=1, amount=5000, source_id=50)
    → LedgerEntry(entry_type="topup", amount=5000, balance_after=5000)
  </example>
  <example name="消耗记账">
    create_spend_entry(ad_account_id=1, amount=1000, source_id=100)
    → LedgerEntry(entry_type="spend", amount=-1000, balance_after=4000)
  </example>
</examples>

<acceptance_criteria>
  □ 账本写入 Service 可用
  □ 账本只增不改
  □ 每条记录有溯源信息
</acceptance_criteria>
```

---

## TASK-LEDGER-003: 红冲 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>ledger</module>
  <task_id>TASK-LEDGER-003</task_id>
  <prerequisites>TASK-LEDGER-002 已完成</prerequisites>
  <sot>LEDGER_SOT.md v1.2 §红冲规则, BR-LEDGER-003</sot>
</context>

<task>实现 POST /api/v1/ledger-entries/{id}/reverse 红冲 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/services/ledger_service.py | reverse_entry() |
  | backend/routers/ledger.py | POST /api/v1/ledger-entries/{id}/reverse |
  | backend/tests/test_ledger_api.py | 4 个红冲测试 |
</deliverables>

<constraints>
  <rule>仅 admin 可执行红冲</rule>
  <rule>红冲必须填写原因</rule>
  <rule>红冲生成反向记录（entry_type: reversal）</rule>
  <rule>原记录标记 is_reversed=True</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 已红冲 | BIZ_001 | 400 | 该记录已被红冲 |
  | 无原因 | BIZ_402 | 400 | 红冲必须填写原因 |
  | 无权限 | AUTH_403 | 403 | 仅管理员可红冲 |
</error_handling>

<examples>
  <example name="正常红冲">
    <request>POST /api/v1/ledger-entries/100/reverse {"reason": "录入错误"}</request>
    <response>{"code": 0, "data": {"original_id": 100, "reversal_id": 101}}</response>
  </example>
</examples>

<acceptance_criteria>
  □ 红冲 API 可用
  □ 必须填写原因
  □ 生成反向记录
</acceptance_criteria>
```

---

## TASK-LEDGER-004: 账户余额计算 Service

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>ledger</module>
  <task_id>TASK-LEDGER-004</task_id>
  <prerequisites>TASK-LEDGER-002 已完成</prerequisites>
  <sot>LEDGER_SOT.md v1.2</sot>
</context>

<task>实现余额计算 Service</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/services/ledger_service.py | calculate_balance(), get_balance_at() |
  | backend/tests/test_ledger_service.py | 4 个余额测试 |
</deliverables>

<constraints>
  <rule>余额 = SUM(amount) WHERE ad_account_id = ? AND is_reversed = false</rule>
  <rule>支持查询历史余额（指定时间点）</rule>
  <rule>缓存优化: 使用最近 balance_after 快速计算</rule>
</constraints>

<examples>
  <example name="计算当前余额">
    calculate_balance(ad_account_id=1) → 5000.00
  </example>
  <example name="查询历史余额">
    get_balance_at(ad_account_id=1, at="2025-01-15") → 3000.00
  </example>
</examples>

<acceptance_criteria>
  □ 余额计算准确
  □ 支持历史余额查询
  □ 排除已红冲记录
</acceptance_criteria>
```

---

# M9 对账模块 (RECON)

> 优先级: P2 | Phase: Phase 2 | 任务数: 4

## TASK-RECON-001 ~ 004 (Phase 2)

> Phase 2 任务清单：

| 任务 | 功能 | 说明 |
|------|------|------|
| TASK-RECON-001 | 对账批次列表 API | 列出对账批次 |
| TASK-RECON-002 | 创建对账批次 API | 上传平台账单，创建批次 |
| TASK-RECON-003 | 对账匹配 Service | 自动匹配日报与账单 |
| TASK-RECON-004 | 对账明细管理 API | 处理差异明细 |

> 详细提示词在 Phase 2 启动时补充。

---

# M10 利润模块 (PROFIT)

> 优先级: P2 | Phase: Phase 1 | 任务数: 4

## TASK-PROFIT-001: 项目利润报表 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>profit</module>
  <task_id>TASK-PROFIT-001</task_id>
  <prerequisites>日报模块、账本模块已完成</prerequisites>
  <sot>BR-PROFIT-001/002/004, PRD.md v2.2 附录B</sot>
</context>

<task>实现 GET /api/v1/profit/projects 项目利润报表 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/profit.py | ProjectProfitResponse, ProjectProfitListResponse |
  | backend/services/profit_service.py | get_project_profit_report() |
  | backend/routers/profit.py | GET /api/v1/profit/projects |
  | backend/tests/test_profit_api.py | 5 个测试用例 |
</deliverables>

<constraints>
  <rule>per_lead 模式: 收入 = conversions_final × unit_price</rule>
  <rule>fee_rate 模式: 收入 = ad_spend × service_rate</rule>
  <rule>毛利 = 收入 - 项目成本（ad_topup，含手续费）</rule>
  <rule>支持日期范围筛选</rule>
  <rule>仅 ceo/finance/project_owner 可查看</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 无权限 | AUTH_403 | 403 | 无权限查看利润报表 |
</error_handling>

<examples>
  <example name="获取项目利润">
    <request>GET /api/v1/profit/projects?start_date=2025-01-01&end_date=2025-01-31</request>
    <response>{"code": 0, "data": {"items": [{"project_id": 1, "revenue": 100000, "cost": 80000, "profit": 20000}]}}</response>
  </example>
</examples>

<acceptance_criteria>
  □ GET /api/v1/profit/projects 返回项目利润
  □ 收入公式正确（per_lead / fee_rate）
  □ 毛利 = 收入 - 成本
</acceptance_criteria>
```

---

## TASK-PROFIT-002: CPL 计算 Service

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>profit</module>
  <task_id>TASK-PROFIT-002</task_id>
  <prerequisites>日报模块已完成</prerequisites>
  <sot>BR-PROFIT-005/006, MASTER.md v4.6 §4.5.2</sot>
</context>

<task>实现 CPL 计算 Service</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/services/profit_service.py | calculate_cpl() |
  | backend/tests/test_profit_service.py | 5 个 CPL 测试 |
</deliverables>

<constraints>
  <rule>CPL = spend / conversions</rule>
  <rule>0 转化时显示 "N/A"</rule>
  <rule>进粉数 < 5 时标记"低量不稳定"</rule>
  <rule>冷启动期（7天）数据仅供观察</rule>
</constraints>

<examples>
  <example name="正常计算">
    calculate_cpl(spend=5000, conversions=100) → 50.00
  </example>
  <example name="零转化">
    calculate_cpl(spend=5000, conversions=0) → "N/A"
  </example>
  <example name="低量">
    calculate_cpl(spend=200, conversions=3) → {"cpl": 66.67, "flag": "低量不稳定"}
  </example>
</examples>

<acceptance_criteria>
  □ CPL 计算正确
  □ 0 转化返回 N/A
  □ 低量标记生效
</acceptance_criteria>
```

---

## TASK-PROFIT-003: 成本计算 Service

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>profit</module>
  <task_id>TASK-PROFIT-003</task_id>
  <prerequisites>账本模块已完成</prerequisites>
  <sot>BR-PROFIT-003, MASTER.md v4.6 §4.5.9, PRD.md v2.2 §2.2</sot>
</context>

<task>实现成本计算 Service</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/services/profit_service.py | calculate_cost() |
  | backend/tests/test_profit_service.py | 4 个成本测试 |
</deliverables>

<constraints>
  <rule>项目成本 = ad_topup（广告费充值，已含手续费）</rule>
  <rule>成本分类:
    - ad_topup: 广告费充值（归属项目）
    - ad_support: 广告配套（公司统一，不分摊）
    - overhead: 后勤支出（公司统一，不分摊）</rule>
  <rule>ad_support 和 overhead 不分摊到项目</rule>
</constraints>

<examples>
  <example name="项目成本">
    calculate_cost(project_id=1, start_date, end_date)
    → {"ad_topup": 80000}  # 仅 ad_topup
  </example>
</examples>

<acceptance_criteria>
  □ 项目成本 = ad_topup
  □ ad_support/overhead 不分摊到项目
</acceptance_criteria>
```

---

## TASK-PROFIT-004: 公司利润汇总 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>profit</module>
  <task_id>TASK-PROFIT-004</task_id>
  <prerequisites>TASK-PROFIT-001 已完成</prerequisites>
  <sot>MASTER.md v4.6 §4.5.10, PRD.md v2.2 附录B</sot>
</context>

<task>实现 GET /api/v1/profit/company 公司利润汇总 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/profit.py | CompanyProfitResponse |
  | backend/services/profit_service.py | get_company_profit_report() |
  | backend/routers/profit.py | GET /api/v1/profit/company |
  | backend/tests/test_profit_api.py | 3 个公司利润测试 |
</deliverables>

<constraints>
  <rule>公司利润 = 总收入 - 总支出</rule>
  <rule>总支出 = ad_topup + ad_support + overhead</rule>
  <rule>支持日期范围筛选</rule>
  <rule>仅 ceo/admin 可查看</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 无权限 | AUTH_403 | 403 | 仅老板可查看公司利润 |
</error_handling>

<examples>
  <example name="获取公司利润">
    <request>GET /api/v1/profit/company?start_date=2025-01-01&end_date=2025-01-31</request>
    <response>{"code": 0, "data": {"total_revenue": 500000, "total_expense": 400000, "profit": 100000}}</response>
  </example>
</examples>

<acceptance_criteria>
  □ GET /api/v1/profit/company 返回公司利润
  □ 总支出包含 ad_topup + ad_support + overhead
  □ 仅 ceo/admin 可查看
</acceptance_criteria>
```

---

# M11 周报模块 (WEEKLY)

> 优先级: P3 | Phase: Phase 1 (可选) + Phase 2 (必须) | 任务数: 3

## TASK-WEEKLY-001: 周报列表 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>weekly_report</module>
  <task_id>TASK-WEEKLY-001</task_id>
  <prerequisites>项目模块已完成</prerequisites>
  <sot>DATA_SCHEMA.md v5.6 §weekly_reports</sot>
</context>

<task>实现 GET /api/v1/weekly-reports 周报列表 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/weekly_report.py | WeeklyReportResponse, WeeklyReportListResponse |
  | backend/services/weekly_report_service.py | list_weekly_reports() |
  | backend/routers/weekly_reports.py | GET /api/v1/weekly-reports |
  | backend/tests/test_weekly_report_api.py | 4 个测试用例 |
</deliverables>

<constraints>
  <rule>返回字段: id, project_id, week_start_date, status, created_by</rule>
  <rule>支持筛选: project_id, week_start_date, created_by</rule>
</constraints>

<acceptance_criteria>
  □ GET /api/v1/weekly-reports 返回周报列表
  □ 支持多维度筛选
</acceptance_criteria>
```

---

## TASK-WEEKLY-002: 创建周报 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>weekly_report</module>
  <task_id>TASK-WEEKLY-002</task_id>
  <prerequisites>TASK-WEEKLY-001 已完成</prerequisites>
  <sot>DATA_SCHEMA.md v5.6 §weekly_reports</sot>
</context>

<task>实现 POST /api/v1/weekly-reports 创建周报 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/schemas/weekly_report.py | WeeklyReportCreate |
  | backend/services/weekly_report_service.py | create_weekly_report() |
  | backend/routers/weekly_reports.py | POST /api/v1/weekly-reports |
  | backend/tests/test_weekly_report_api.py | 4 个创建测试 |
</deliverables>

<constraints>
  <rule>必须指定 project_id, week_start_date</rule>
  <rule>包含: 周消耗、周进粉、问题、下周计划</rule>
  <rule>project_owner 可创建</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 周报已存在 | BIZ_001 | 400 | 该周周报已存在 |
</error_handling>

<acceptance_criteria>
  □ POST /api/v1/weekly-reports 创建周报
  □ 同一项目同一周不可重复创建
</acceptance_criteria>
```

---

## TASK-WEEKLY-003: 提交周报 API

```xml
<context>
  <project>AI 广告代投系统</project>
  <tech_stack>FastAPI + SQLAlchemy 2.x + Pydantic v2</tech_stack>
  <module>weekly_report</module>
  <task_id>TASK-WEEKLY-003</task_id>
  <prerequisites>TASK-WEEKLY-002 已完成</prerequisites>
  <sot>MASTER.md v4.6 附录C</sot>
</context>

<task>实现 POST /api/v1/weekly-reports/{id}/submit 提交周报 API</task>

<deliverables>
  | 文件 | 内容 |
  |------|------|
  | backend/services/weekly_report_service.py | submit_weekly_report() |
  | backend/routers/weekly_reports.py | POST /api/v1/weekly-reports/{id}/submit |
  | backend/tests/test_weekly_report_api.py | 3 个提交测试 |
</deliverables>

<constraints>
  <rule>Phase 1: 可选提交（不强制）</rule>
  <rule>Phase 2: 周五下班前必须提交（Feature Flag 控制）</rule>
  <rule>状态流转: draft → submitted</rule>
</constraints>

<error_handling>
  | 场景 | 错误码 | HTTP | 消息 |
  |------|--------|------|------|
  | 已提交 | STATE_400 | 400 | 周报已提交 |
</error_handling>

<acceptance_criteria>
  □ 提交 API 可用
  □ Phase 1 不强制
  □ Phase 2 强制（Feature Flag）
</acceptance_criteria>
```

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

## 附录 B：角色权限速查表

| 角色 | 中文名 | 职责 |
|------|--------|------|
| ceo | 老板 | 资金安全、公司盈亏、最终决策 |
| project_owner | 项目负责人 | 项目盈亏、日报审核、统计实际消耗 |
| finance | 财务 | 资金出入准确、数据真实、对账 |
| pitcher | 投手 | CPL 达标、日报准确、执行投放 |
| account_manager | 户管 | 账户分配、账户状态监控 |
| admin | 管理员 | 系统配置（不参与业务） |

## 附录 C：错误码速查表

| 错误码 | HTTP | 含义 |
|--------|------|------|
| AUTH_400 | 400 | 认证失败 |
| AUTH_401 | 401 | 未认证 |
| AUTH_403 | 403 | 无权限 |
| STATE_400 | 400 | 状态转换非法 |
| STATE_402 | 400 | 终态非法回退 |
| BIZ_001 | 400 | 无效的操作 |
| BIZ_002 | 404 | 资源不存在 |
| BIZ_100 | 400 | 金额非法 |
| BIZ_101 | 400 | 余额不足 |
| BIZ_402 | 400 | 红冲缺少原因 |
| VAL_001 | 400 | 参数校验失败 |

## 附录 D：Phase 1 日报状态（3 状态）

```python
PHASE1_DAILY_REPORT_STATUS = ["raw_submitted", "trend_ok", "final_confirmed"]
```

## 附录 E：响应格式

```json
// 成功响应
{
  "code": 0,
  "message": "success",
  "data": { ... }
}

// 错误响应
{
  "code": "ERROR_CODE",
  "message": "错误描述",
  "data": null
}

// 分页响应
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

---

**文档版本**: v2.0
**修订日期**: 2025-12-28
**任务总数**: 57 个（完整提示词覆盖）
**审核状态**: Claude 最佳实践优化版
