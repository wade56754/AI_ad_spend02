# BR-AUTH - 认证授权规则

> **文档版本**: v1.1
> **status**: active
> **owner**: wade
> **last_reviewed**: 2026-01-02
> **父文档**: BUSINESS_RULES.md v5.1
> **关联 SoT**: AUTH_SPEC.md v2.2, DATA_SCHEMA.md v5.7 §3.1.1
> **业务参考**: 见本文档（历史参考: BUSINESS_LOGIC_FRAMEWORK v2.1 已废弃）

---

## 互锁 SoT 引用

| SoT 文档 | 版本 | 引用章节 | 引用内容 |
|----------|------|----------|----------|
| BUSINESS_RULES.md | v5.0 | §4.1 | 规则索引定义 |
| AUTH_SPEC.md | v2.2 | §2-10 | 认证授权完整规范 |
| DATA_SCHEMA.md | v5.7 | §3.1.1 | users 表结构、角色枚举 |
| ERROR_CODES.md | v2.3 | §4.1, §4.2 | AUTH_*/BIZ_* 错误码 |
| MASTER.md | v4.8 | §2.4 | 角色定义（6 业务角色） |

---

## 规则总览

| 规则ID | 规则名称 | 优先级 | 测试状态 |
|--------|----------|--------|----------|
| BR-AUTH-001 | 登录必须验证 | P0 | ✅ |
| BR-AUTH-002 | Token 有效期 | P0 | ✅ |
| BR-AUTH-003 | 角色唯一性 | P0 | ✅ |
| BR-AUTH-004 | 权限继承禁止 | P0 | ✅ |
| BR-AUTH-005 | 密码强度 | P1 | 🟡 |
| BR-AUTH-006 | 职责分离 | P0 | ✅ |

---

## 规则详细定义

### BR-AUTH-001: 登录必须验证

#### 业务场景
所有业务 API 请求必须携带有效的 JWT Token，未经认证的请求一律拒绝。这是系统安全的第一道防线，确保只有合法用户才能访问系统资源。

#### 详细约束
- 📌 **强制**: 所有 `/api/v1/*` 请求必须在 Header 中携带 `Authorization: Bearer <token>`
- 📌 **强制**: Token 必须经过 Supabase Auth 签名验证
- ❌ **禁止**: 未携带 Token 的请求访问受保护资源
- ❌ **禁止**: 使用已过期或已撤销的 Token
- ✅ **允许**: `/api/v1/auth/login` 和 `/api/v1/auth/register` 不需要 Token

#### 前置条件
- 数据状态: 用户已注册且账户状态为 active
- 引用: AUTH_SPEC.md v2.1 §3.2

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 缺少 Authorization Header | `AUTH_400` | 401 | 未提供认证令牌 |
| Token 格式错误 | `AUTH_401` | 401 | 无效的认证令牌 |
| Token 签名验证失败 | `AUTH_401` | 401 | 无效的认证令牌 |
| Token 已过期 | `AUTH_402` | 401 | 令牌已过期 |
| Token 已被撤销 | `AUTH_003` | 401 | 令牌已被撤销 |

#### 代码引用
- Dependency: `backend/dependencies/auth.py`
- 方法: `get_current_user()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 正常携带 Token | 有效 Bearer Token | 成功 |
| T2 | 缺少 Header | 无 Authorization | `AUTH_400` |
| T3 | Token 格式错误 | Bearer abc123 | `AUTH_401` |
| T4 | Token 已过期 | 过期 Token | `AUTH_402` |
| T5 | Token 已撤销 | 登出后的 Token | `AUTH_003` |

---

### BR-AUTH-002: Token 有效期

#### 业务场景
Access Token 有效期控制在合理范围内，平衡安全性与用户体验。过长的有效期增加安全风险，过短则频繁要求用户重新认证。

#### 详细约束
- 📌 **强制**: Access Token 有效期默认 1 小时（3600 秒）
- 📌 **强制**: Access Token 有效期不得超过 24 小时
- 📌 **强制**: Refresh Token 有效期默认 30 天
- ✅ **允许**: 通过 Supabase Dashboard 配置 TTL
- ❌ **禁止**: 前端缓存 Token 超过有效期

#### Token TTL 配置
| Token 类型 | 默认 TTL | 最大 TTL | 配置位置 |
|-----------|---------|---------|----------|
| Access Token | 1 小时 | 24 小时 | Supabase Dashboard |
| Refresh Token | 30 天 | 365 天 | Supabase Dashboard |

#### 前置条件
- 数据状态: Token 已签发
- 引用: AUTH_SPEC.md v2.1 §3.3

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| Access Token 过期 | `AUTH_402` | 401 | 令牌已过期 |
| Refresh Token 过期 | `AUTH_402` | 401 | 令牌已过期 |
| Refresh Token 已使用 | `AUTH_003` | 401 | 令牌已被撤销 |

#### 代码引用
- Config: Supabase Dashboard → Authentication → Settings → JWT Settings
- Service: `backend/services/auth_service.py`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | Token 未过期 | exp > NOW() | 成功 |
| T2 | Token 刚好过期 | exp = NOW() | `AUTH_402` |
| T3 | Token 明显过期 | exp < NOW() - 1h | `AUTH_402` |
| T4 | Refresh Token 刷新 | 有效 Refresh Token | 新 Token |

---

### BR-AUTH-003: 角色唯一性

#### 业务场景
每个用户只能拥有一个角色，不支持多角色叠加。这简化了权限模型，避免权限冲突和管理复杂度。

#### 详细约束
- 📌 **强制**: `users.role` 字段只能是 6 个业务角色之一
- ❌ **禁止**: 一个用户同时拥有多个角色
- ❌ **禁止**: 使用角色数组或 JSONB 存储多角色
- ❌ **禁止**: 使用已废弃的 `supervisor` 角色
- ✅ **允许**: 角色变更（需 admin/ceo 操作 + 审计记录）

#### 业务层 6 角色
| 角色代码 | 业务名称 | 权限级别 | 技术层映射 |
|---------|---------|---------|-----------|
| `ceo` | 老板 | L6 (最高) | `admin` |
| `project_owner` | 项目负责人 | L5 | `is_project_owner=true` (业务属性) |
| `finance` | 财务 | L4 | `finance` |
| `pitcher` | 投手 | L3 | `media_buyer` |
| `account_manager` | 户管 | L2 | `account_manager` |
| `admin` | 管理员 | L1 | `admin` |

#### 前置条件
- 数据状态: 用户创建或角色变更时
- 引用: MASTER.md v4.8 §2.4, AUTH_SPEC.md v2.1 §2.2

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 使用无效角色 | `BIZ_001` | 400 | 无效的角色类型 |
| 使用已废弃角色 | `BIZ_001` | 400 | supervisor 角色已废弃 |
| 角色字段为空 | `VALIDATION_001` | 400 | 角色不能为空 |

#### 代码引用
- Model: `backend/models/user.py`
- Service: `backend/services/user_service.py`
- 方法: `create_user()`, `update_user_role()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 创建有效角色用户 | role=pitcher | 成功 |
| T2 | 使用无效角色 | role=superuser | `BIZ_001` |
| T3 | 使用已废弃角色 | role=supervisor | `BIZ_001` |
| T4 | 角色为空 | role=null | `VALIDATION_001` |

---

### BR-AUTH-004: 权限继承禁止

#### 业务场景
角色权限采用扁平化设计，不支持跨层级继承。每个角色拥有独立的权限集合，由权限矩阵明确定义，避免权限膨胀和越权风险。

#### 详细约束
- 📌 **强制**: 权限判断必须基于 `users.role` 字段
- ❌ **禁止**: 角色 A 自动继承角色 B 的权限
- ❌ **禁止**: 使用权限层级树结构
- ✅ **允许**: admin 拥有最高权限（非继承，而是独立定义）
- 📌 **强制**: 权限校验必须在 Service 层执行

#### 权限矩阵（摘要）
| 操作 | admin | finance | project_owner | account_manager | media_buyer |
|------|-------|---------|---------------|-----------------|-------------|
| 创建用户 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 审核日报 | ✅ | ❌ | ✅ | ❌ | ❌ |
| 审批充值 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 提交日报 | ✅ | ❌ | ❌ | ❌ | ✅ |

#### 前置条件
- 数据状态: API 请求时进行权限校验
- 引用: AUTH_SPEC.md v2.1 §5.2

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 角色无权限执行操作 | `AUTH_500` | 403 | 权限不足 |
| 尝试越权访问数据 | `AUTH_500` | 403 | 权限不足 |

#### 代码引用
- Dependency: `backend/dependencies/auth.py`
- 方法: `require_role()`, `check_permission()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | admin 创建用户 | role=admin | 成功 |
| T2 | pitcher 创建用户 | role=media_buyer | `AUTH_500` |
| T3 | finance 审核日报 | role=finance | `AUTH_500` |
| T4 | project_owner 审核日报 | is_project_owner=true | 成功 |

---

### BR-AUTH-005: 密码强度

#### 业务场景
用户密码必须满足最低安全要求，防止弱密码导致的账户被盗风险。密码强度规则由 Supabase Auth 强制执行。

#### 详细约束
- 📌 **强制**: 密码长度至少 8 位
- 📌 **强制**: 密码必须包含大写字母（A-Z）
- 📌 **强制**: 密码必须包含小写字母（a-z）
- 📌 **强制**: 密码必须包含数字（0-9）
- ✅ **允许**: 包含特殊字符（推荐但不强制）
- ❌ **禁止**: 使用常见弱密码（如 password123）

#### 密码规则
```regex
^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d!@#$%^&*]{8,}$
```

#### 前置条件
- 数据状态: 用户注册或密码修改时
- 引用: AUTH_SPEC.md v2.1 §6.1

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 密码长度不足 | `VALIDATION_001` | 400 | 密码长度至少 8 位 |
| 缺少大写字母 | `VALIDATION_001` | 400 | 密码必须包含大写字母 |
| 缺少小写字母 | `VALIDATION_001` | 400 | 密码必须包含小写字母 |
| 缺少数字 | `VALIDATION_001` | 400 | 密码必须包含数字 |

#### 代码引用
- Service: `backend/services/auth_service.py`
- 方法: `register()`, `change_password()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 合规密码 | Abc12345 | 成功 |
| T2 | 长度不足 | Abc123 | `VALIDATION_001` |
| T3 | 缺少大写 | abc12345 | `VALIDATION_001` |
| T4 | 缺少数字 | Abcdefgh | `VALIDATION_001` |

---

### BR-AUTH-006: 职责分离

#### 业务场景
关键业务流程必须遵循职责分离（SOD）原则，防止内部欺诈和数据篡改。日报提交者不能审核自己的日报，充值申请者不能审批自己的充值。

#### 详细约束
- 📌 **强制**: 日报提交者 ≠ 日报审核者
- 📌 **强制**: 充值申请者 ≠ 充值审批者
- 📌 **强制**: 对账提交者 ≠ 对账确认者
- ✅ **允许**: admin 可绕过 SOD（必须填写原因 + 审计记录）
- ❌ **禁止**: 非 admin 角色绕过 SOD

#### SOD 规则矩阵
| 业务流程 | 提交角色 | 审核/审批角色 | SOD 规则 |
|---------|---------|--------------|----------|
| 日报审核 | pitcher | project_owner | 提交者 ≠ 审核者 |
| 充值审批 | pitcher | finance | 申请者 ≠ 审批者 |
| 对账确认 | project_owner | finance | 提交者 ≠ 确认者 |

#### 前置条件
- 数据状态: 审核/审批操作时
- 引用: AUTH_SPEC.md v2.1 §5.1.2, BUSINESS_RULES.md v4.8 BR-FIN-002

#### 错误码映射
| 违反场景 | 错误码 | HTTP | 错误消息 |
|----------|--------|------|----------|
| 审核自己提交的日报 | `BIZ_001` | 400 | 不能审核自己提交的日报（职责分离） |
| 审批自己申请的充值 | `BIZ_001` | 400 | 不能审批自己申请的充值（职责分离） |
| admin 绕过 SOD 缺少原因 | `VALIDATION_001` | 400 | 必须填写详细原因（至少 10 字符） |

#### 代码引用
- Service: `backend/services/daily_report_service.py`
- 方法: `approve_report()`, `admin_force_approve()`

#### Test Intent
| ID | 测试场景 | 输入 | 预期结果 |
|----|----------|------|----------|
| T1 | 他人审核日报 | 审核者 ≠ 提交者 | 成功 |
| T2 | 自我审核日报 | 审核者 = 提交者 | `BIZ_001` |
| T3 | admin 强制审核有原因 | admin + reason | 成功 + 审计 |
| T4 | admin 强制审核无原因 | admin + 空 reason | `VALIDATION_001` |

---

## 规则依赖关系

```
BR-AUTH-001 (登录必须验证)
    ↓
BR-AUTH-002 (Token 有效期)
    ↓
BR-AUTH-003 (角色唯一性) ←── BR-AUTH-004 (权限继承禁止)
    ↓
BR-AUTH-005 (密码强度)
    ↓
BR-AUTH-006 (职责分离)
```

---

## Auth 状态机

### Token 状态流转

```
┌─────────┐      过期       ┌─────────┐
│  active │ ──────────────→ │ expired │
│ (有效)  │                 │ (终态)  │
└────┬────┘                 └─────────┘
     │
     │ 登出/禁用/强制下线
     ↓
┌─────────────┐
│ invalidated │
│   (终态)    │
└─────────────┘
```

### 状态流转白名单

| 当前状态 | 目标状态 | 触发事件 | 操作者 |
|----------|----------|----------|--------|
| - | `active` | 登录成功 | 用户 |
| `active` | `active` | 刷新 Token | 用户 |
| `active` | `expired` | Token 自然过期 | system |
| `active` | `invalidated` | 用户登出 | 用户 |
| `active` | `invalidated` | 账户禁用 | admin |
| `active` | `invalidated` | 强制下线 | admin |

---

## 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2025-12-27 | 初始版本，对齐 BUSINESS_RULES.md v4.8；所有错误码对齐 ERROR_CODES.md v2.2；角色对齐 MASTER.md v4.8（6 业务角色） |

---

**文档性质**: 业务规则子模块
**执行级别**: 强制执行
**父文档**: BUSINESS_RULES.md v4.6
**关联 SoT**: AUTH_SPEC.md v2.1, DATA_SCHEMA.md v5.6 §3.1.1
**版本**: v1.0
