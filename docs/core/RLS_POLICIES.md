# AI_AD_SPEND 系统行级安全策略规范（RLS Policies）

**文档版本**：v1.3 🔒 规划文档（未启用）
**最后更新**：2025-11-20
**维护者**：Backend Team
**状态**：⚠️ **当前未启用 - 本文档描述的是规划目标策略**

---

## ⚠️ 重要声明

**当前 RLS 实施状态**：
- ❌ **数据库层 RLS 未启用**：PostgreSQL Row Level Security 功能关闭
- ✅ **应用层权限控制已启用**：通过 Service 层 + ORM Mixin 实现
- 📋 **本文档定位**：未来启用数据库 RLS 的规划蓝图和参考设计

**如需了解当前实际权限实现，请参考**：
- `docs/security/RLS_POLICIES.md` - 应用层权限实现说明（当前实现行为的 Implementation SoT）
- `backend/core/permissions.py` - RBAC 权限系统
- `backend/models/mixins/rls_aware.py` - ORM 层权限过滤

**SoT 层级说明**：
- 本文档（`docs/core/RLS_POLICIES.md`）是系统整体 SoT 的规划部分
- `docs/security/RLS_POLICIES.md` 描述当前实现行为
- 两者冲突时以本文档为权威，但当前实现以 security 文档为准

---

## 文档定位

本文档是 AI_AD_SPEND 系统 **行级安全（Row-Level Security, RLS）策略的规划设计文档（SoT）**。

**规划原则**（未来启用时适用）：
- ✅ 所有数据库 RLS 策略必须以本文档为准
- ✅ 所有角色权限判断必须先查本文档
- ✅ 禁止在代码中绕过 RLS（如 `SET ROLE`、`SECURITY DEFINER`）
- ✅ 任何 RLS 变更必须先更新本文档，再执行 SQL
- ❌ 禁止在生产环境临时禁用 RLS（`ALTER TABLE ... DISABLE ROW LEVEL SECURITY`）

**依赖文档**：
- `STATE_MACHINE.md` - 状态流转与角色权限
- `BUSINESS_RULES.md` - 业务规则与数据访问逻辑
- `DATA_SCHEMA.md` - 数据库表结构与外键关系
- `ERROR_CODES.md` - 权限错误码（AUTH_5xx）

---

## 目录

1. [RLS 全局原则](#1-rls-全局原则)
2. [系统角色定义](#2-系统角色定义)
3. [JWT Claims 结构](#3-jwt-claims-结构)
4. [全局权限矩阵](#4-全局权限矩阵)
5. [核心表 RLS 策略](#5-核心表-rls-策略)
   - 5.1 [users - 用户表](#51-users---用户表)
   - 5.2 [projects - 项目表](#52-projects---项目表)
   - 5.3 [project_members - 项目成员表](#53-project_members---项目成员表)
   - 5.4 [channels - 渠道表](#54-channels---渠道表)
   - 5.5 [ad_accounts - 广告账户表](#55-ad_accounts---广告账户表)
   - 5.6 [daily_reports - 日报表](#56-daily_reports---日报表)
   - 5.7 [ad_spend_daily - 广告消耗表](#57-ad_spend_daily---广告消耗表)
   - 5.8 [topup_requests - 充值申请表](#58-topup_requests---充值申请表)
   - 5.9 [ledger_entries - 账本表](#59-ledger_entries---账本表)
   - 5.10 [reconciliation_batches - 对账批次表](#510-reconciliation_batches---对账批次表)
   - 5.11 [reconciliation_details - 对账明细表](#511-reconciliation_details---对账明细表)
   - 5.12 [account_status_history - 账户状态历史表](#512-account_status_history---账户状态历史表)
   - 5.13 [account_alerts - 账户预警表](#513-account_alerts---账户预警表)
   - 5.14 [audit_logs - 审计日志表](#514-audit_logs---审计日志表)
6. [RLS SQL 模板库](#6-rls-sql-模板库)
7. [RLS 变更流程](#7-rls-变更流程)
8. [RLS 测试与审计](#8-rls-测试与审计)
9. [常见问题与陷阱](#9-常见问题与陷阱)
10. [版本历史](#10-版本历史)

---

## 1. RLS 全局原则

**⚠️ 本节描述的是未来启用数据库 RLS 时应遵循的原则**
**当前数据库 RLS 未启用，以下策略仅作为规划参考**

### 1.1 Deny-by-Default 原则

所有表默认拒绝访问，必须显式授权。

```sql
-- ✅ 强制启用 RLS
ALTER TABLE <table_name> ENABLE ROW LEVEL SECURITY;
ALTER TABLE <table_name> FORCE ROW LEVEL SECURITY;
```

**实施要求**：
- 新表创建后立即启用 RLS
- 禁止使用 `CREATE POLICY ... TO PUBLIC`
- 策略必须显式定义 `USING` 和 `WITH CHECK` 子句

---

### 1.2 管理员不跳过 RLS

**安全原则**：即使是管理员也必须通过 RLS 策略访问数据，确保审计完整性。

```sql
-- ❌ 错误：管理员绕过 RLS
CREATE POLICY admin_bypass ON projects FOR ALL
USING (true);  -- 不安全：无审计记录

-- ✅ 正确：管理员受 RLS 约束（但可访问所有数据）
CREATE POLICY admin_full_access ON projects FOR SELECT
TO authenticated
USING (has_role('admin'));
```

**合规要求**：
- 防止权限提升攻击（Privilege Escalation）
- 所有访问必须经过 RLS 记录到审计日志
- 符合 SOC2 / ISO27001 审计标准

---

### 1.3 最小权限原则

**访问控制模型**：
- 用户只能访问**自己创建**或**被分配**的数据
- 跨项目访问必须通过 `project_members` 表验证成员关系
- 只读角色（finance）不得拥有 INSERT/UPDATE/DELETE 权限
- 审计数据（audit_logs）永久禁止修改和删除

---

### 1.4 策略命名规范

**命名模式**：`<table>_<operation>_<role>_<scope>`

```
示例：
✅ projects_select_admin_all           → 管理员查看所有项目
✅ daily_reports_insert_media_buyer    → 投手插入日报
✅ topup_requests_update_finance       → 财务审批充值申请
✅ audit_logs_deny_update              → 拒绝修改审计日志
```

---

### 1.5 安全最佳实践与已知陷阱

#### ✅ 必须遵守的安全规则

**1. 避免循环依赖（P0 - Critical）**

```sql
-- ❌ 错误：在 users 表策略中查询 users 表
USING ((SELECT role FROM users WHERE id = auth.uid()) = 'admin')

-- ✅ 正确：使用 JWT Claims 避免循环依赖
USING ((auth.jwt() ->> 'app_metadata')::jsonb ->> 'user_role' = 'admin')
```

**技术原因**：当 RLS 策略查询自身表时，会触发递归策略评估，可能导致死锁或性能急剧下降。

---

**2. RLS 无法实现字段级权限（P0 - Critical）**

```sql
-- ❌ 错误：尝试用 RLS 限制字段修改
WITH CHECK (
  status = (SELECT status FROM ad_accounts WHERE id = ad_accounts.id)
  -- ⚠️ 缺陷：子查询返回**更新后**的值，检查总是通过
)

-- ✅ 正确：在应用层或触发器实现
-- 方案 1：FastAPI 路由验证
if 'status' in update_data:
    if not has_permission('modify_status'):
        raise PermissionDenied()

-- 方案 2：PostgreSQL 触发器
CREATE TRIGGER check_field_changes
  BEFORE UPDATE ON ad_accounts
  FOR EACH ROW EXECUTE FUNCTION validate_field_modifications();
```

**技术原因**：PostgreSQL RLS 的 `WITH CHECK` 子句在行插入/更新**完成后**执行，此时新值已生效，无法实现列级约束。

---

**3. 防止策略重叠导致权限提升（P1 - High）**

```sql
-- ⚠️ 风险：多个 PERMISSIVE 策略使用 OR 逻辑组合
-- 可能导致 account_manager 绕过成员验证

-- ✅ 解决方案：使用 RESTRICTIVE 策略
CREATE POLICY projects_restrict_membership ON projects FOR UPDATE
AS RESTRICTIVE  -- 强制 AND 逻辑
USING (
  has_role('admin')
  OR has_role('data_operator')
  OR (has_role('account_manager') AND is_project_member(projects.id))
);
```

**技术原因**：PostgreSQL 对多个 PERMISSIVE 策略使用 `USING = P1 OR P2 OR ...`，若某个策略的 `WITH CHECK` 缺少约束，会导致未预期的授权。

---

**4. 审计日志不可变性（P1 - High）**

```sql
-- ✅ 正确：明确拒绝修改和删除审计日志
CREATE POLICY audit_logs_deny_update ON audit_logs FOR UPDATE
TO authenticated
USING (false);  -- 永远拒绝

CREATE POLICY audit_logs_deny_delete ON audit_logs FOR DELETE
TO authenticated
USING (false);  -- 永远拒绝
```

**合规要求**：SOC2 Type II 和 ISO27001 要求审计日志必须不可篡改，仅允许 INSERT 操作。

---

#### 🛡️ 部署前安全检查清单

- [ ] 所有表已启用 `ENABLE ROW LEVEL SECURITY` 和 `FORCE ROW LEVEL SECURITY`
- [ ] users 表策略使用 JWT Claims，无循环依赖
- [ ] audit_logs 表明确禁止 UPDATE/DELETE
- [ ] 无字段级权限控制策略（已移至应用层或触发器）
- [ ] 策略 USING 和 WITH CHECK 逻辑一致（特别是 UPDATE 操作）
- [ ] 敏感表（财务、审计）无 `USING (true)` 策略
- [ ] 运行策略审计脚本，检查覆盖率和过度宽松策略
- [ ] 验证 Helper 函数已部署且索引已创建

---

#### ⚠️ 已知风险缓解状态

| 风险 | 影响级别 | 缓解措施 | 状态 |
|------|---------|---------|------|
| users 表循环依赖 | P0 | 使用 JWT Claims | ✅ v1.1 已修复 |
| ad_accounts 字段级绕过 | P0 | 移至应用层控制 | ✅ v1.1 已修复 |
| 策略重叠权限提升 | P1 | RESTRICTIVE 策略 + 文档警告 | ✅ v1.1 已修复 |
| audit_logs 缺乏防篡改 | P1 | 明确 DENY UPDATE/DELETE | ✅ v1.1 已修复 |
| 代码重复维护困难 | P2 | Helper 函数库 | ✅ v1.2 已优化 |

---

## 2. 系统角色定义

根据 `backend/models/enums.py` 中的 `UserRole` 枚举：

| 角色 | 枚举值 | 英文名 | 职责 | 数据访问范围 |
|------|--------|--------|------|--------------|
| **管理员** | `admin` | Administrator | 系统全局管理，执行所有操作 | 所有数据（受 RLS 控制但范围最广） |
| **财务** | `finance` | Finance | 审核充值申请、查看财务数据 | 所有已批准的财务数据（只读） |
| **数据员** | `data_operator` | Data Operator | 审核日报、对账、数据校验 | 所有业务数据（可编辑） |
| **客户经理** | `account_manager` | Account Manager | 管理项目、分配账户、协调资源 | 管理的项目及其下所有数据 |
| **投手** | `media_buyer` | Media Buyer | 投放广告、提交日报、申请充值 | 分配给自己的账户及相关数据 |

**角色层级（权限从高到低）**：
```
admin > data_operator ≈ account_manager > finance > media_buyer
```

**特殊说明**：
- `data_operator` 和 `account_manager` 权限范围不同但等级相当
- `finance` 是只读角色，但拥有审批充值申请的特殊权限
- `media_buyer` 是数据生产者，权限范围最受限

---

## 3. JWT Claims 结构

Supabase Auth 提供的 JWT 必须包含以下 claims：

```json
{
  "sub": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",  // 用户 UUID
  "role": "authenticated",                         // Supabase 角色（固定）
  "app_metadata": {
    "user_role": "media_buyer"                     // 业务角色（必须同步）
  },
  "user_metadata": {
    "full_name": "张三",
    "department": "投放部"
  }
}
```

**RLS 策略中的访问方式**：

```sql
-- ✅ 获取当前用户 ID
auth.uid()

-- ✅ 获取业务角色（users 表策略必须使用此方式）
(auth.jwt() ->> 'app_metadata')::jsonb ->> 'user_role'

-- ⚠️ 安全警告：循环依赖风险
-- ❌ 错误：在 users 表策略中查询 users 表
(SELECT role FROM users WHERE id = auth.uid())

-- ✅ 完整示例：使用 JWT Claims
CREATE POLICY example_policy ON projects FOR SELECT
TO authenticated
USING (
  (auth.jwt() ->> 'app_metadata')::jsonb ->> 'user_role' = 'admin'
  OR created_by = auth.uid()
);
```

**关键字段映射**：

| JWT Claim | 数据库字段 | 说明 |
|-----------|-----------|------|
| `sub` | `users.id` | 用户主键（UUID） |
| `app_metadata.user_role` | `users.role` | 业务角色（必须保持同步） |
| `email` | `users.email` | 邮箱（Supabase Auth 管理） |

**同步要求**：在用户注册和角色变更时，必须同时更新：
1. `users.role` 数据库字段
2. Supabase Auth `app_metadata.user_role`

---

## 4. 全局权限矩阵

| 表名 | admin | data_operator | account_manager | finance | media_buyer |
|------|-------|---------------|-----------------|---------|-------------|
| **users** | ALL | SELECT | SELECT | SELECT | SELECT(self) |
| **projects** | ALL | ALL | ALL(managed) | SELECT | SELECT(assigned) |
| **project_members** | ALL | ALL | ALL(managed) | SELECT | SELECT(self) |
| **channels** | ALL | ALL | SELECT | SELECT | SELECT |
| **ad_accounts** | ALL | ALL | ALL(managed) | SELECT | SELECT(assigned) |
| **daily_reports** | ALL | ALL | SELECT | SELECT | ALL(assigned) |
| **ad_spend_daily** | ALL | INSERT/UPDATE | SELECT | SELECT | SELECT(assigned) |
| **topup_requests** | ALL | ALL | SELECT | REVIEW | ALL(own) |
| **ledger_entries** | ALL | INSERT/UPDATE | SELECT | SELECT | SELECT(assigned) |
| **reconciliation_batches** | ALL | ALL | SELECT | SELECT | - |
| **reconciliation_details** | ALL | ALL | SELECT | SELECT | - |
| **account_status_history** | ALL | INSERT | SELECT | SELECT | SELECT(assigned) |
| **account_alerts** | ALL | ALL | ALL(managed) | SELECT | SELECT(assigned) |
| **audit_logs** | SELECT | SELECT | SELECT | SELECT | - |

**图例**：
- `ALL` = SELECT + INSERT + UPDATE + DELETE
- `ALL(managed)` = 用户管理的项目范围内的所有操作
- `ALL(assigned)` = 分配给用户的账户范围内的所有操作
- `ALL(own)` = 用户自己创建的记录
- `SELECT` = 只读访问
- `REVIEW` = 特殊审批权限
- `-` = 无权限

---

## 5. 核心表 RLS 策略

### 5.1 users - 用户表

**表关键字段**：
- `id` (UUID, PK) - 用户 ID（对应 `auth.uid()`）
- `email` (VARCHAR) - 邮箱
- `role` (VARCHAR) - 业务角色
- `is_active` (BOOLEAN) - 是否激活

**角色访问规则**：

| 角色 | SELECT | INSERT | UPDATE | DELETE |
|------|--------|--------|--------|--------|
| admin | 所有用户 | ✅ | 所有用户 | 所有用户 |
| data_operator | 所有用户 | ❌ | ❌ | ❌ |
| account_manager | 所有用户 | ❌ | ❌ | ❌ |
| finance | 所有用户 | ❌ | ❌ | ❌ |
| media_buyer | 仅自己 | ❌ | 仅自己 | ❌ |

**RLS 策略**：

```sql
-- ==================== users 表 RLS 策略 ====================
-- ⚠️ 重要安全说明：
-- users 表策略必须使用 JWT Claims 避免循环依赖
-- 禁止在此处使用 (SELECT role FROM users WHERE id = auth.uid())

-- 策略 1: users_select_self
-- 业务理由：所有用户可查看自己的基本信息
CREATE POLICY users_select_self ON users
FOR SELECT
TO authenticated
USING (
  id = auth.uid()
);

-- 策略 2: users_select_all_staff
-- 业务理由：员工角色需查看其他用户信息以完成协作
-- 安全理由：使用 JWT Claims 避免循环依赖
CREATE POLICY users_select_all_staff ON users
FOR SELECT
TO authenticated
USING (
  (auth.jwt() ->> 'app_metadata')::jsonb ->> 'user_role'
  IN ('admin', 'data_operator', 'account_manager', 'finance')
);

-- 策略 3: users_update_self
-- 业务理由：用户可更新自己的资料
-- 安全理由：禁止修改自己的角色（role 必须保持不变）
CREATE POLICY users_update_self ON users
FOR UPDATE
TO authenticated
USING (
  id = auth.uid()
)
WITH CHECK (
  id = auth.uid()
  AND role = (auth.jwt() ->> 'app_metadata')::jsonb ->> 'user_role'
);

-- 策略 4: users_all_admin
-- 业务理由：管理员管理用户账户和权限
CREATE POLICY users_all_admin ON users
FOR ALL
TO authenticated
USING (
  (auth.jwt() ->> 'app_metadata')::jsonb ->> 'user_role' = 'admin'
)
WITH CHECK (
  (auth.jwt() ->> 'app_metadata')::jsonb ->> 'user_role' = 'admin'
);
```

**安全说明**：
- ✅ 已修复 P0 循环依赖风险：所有策略使用 JWT Claims
- ⚠️ 前提条件：Supabase Auth 必须正确设置 `app_metadata.user_role`
- 📋 同步要求：用户注册/角色变更时，确保 JWT Claims 与数据库一致

---

### 5.2 projects - 项目表

**表关键字段**：
- `id` (BIGINT, PK)
- `project_code` (VARCHAR, UNIQUE)
- `status` (VARCHAR) - 项目状态
- `created_by` (UUID, FK → users.id)

**角色访问规则**：

| 角色 | SELECT | INSERT | UPDATE | DELETE |
|------|--------|--------|--------|--------|
| admin | 所有项目 | ✅ | 所有项目 | 所有项目 |
| data_operator | 所有项目 | ✅ | 所有项目 | ❌ |
| account_manager | 管理的项目 | ✅ | 管理的项目 | ❌ |
| finance | 所有项目 | ❌ | ❌ | ❌ |
| media_buyer | 参与的项目 | ❌ | ❌ | ❌ |

**RLS 策略**：

```sql
-- ==================== projects 表 RLS 策略 ====================

-- 策略 1: projects_select_admin_data_operator_finance
-- 业务理由：管理员/数据员/财务需全局视野进行管理和分析
CREATE POLICY projects_select_admin_data_operator_finance ON projects
FOR SELECT
TO authenticated
USING (
  has_any_role(ARRAY['admin', 'data_operator', 'finance'])
);

-- 策略 2: projects_select_member
-- 业务理由：项目成员可查看参与的项目信息
CREATE POLICY projects_select_member ON projects
FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM project_members
    WHERE project_id = projects.id
      AND user_id = auth.uid()
  )
);

-- 策略 3: projects_insert_privileged_roles
-- 业务理由：创建项目需要管理权限
CREATE POLICY projects_insert_privileged_roles ON projects
FOR INSERT
TO authenticated
WITH CHECK (
  has_any_role(ARRAY['admin', 'data_operator', 'account_manager'])
);

-- 策略 4: projects_update_admin_data_operator
-- 业务理由：核心数据修改限制在管理员和数据员
CREATE POLICY projects_update_admin_data_operator ON projects
FOR UPDATE
TO authenticated
USING (
  has_any_role(ARRAY['admin', 'data_operator'])
)
WITH CHECK (
  has_any_role(ARRAY['admin', 'data_operator'])
);

-- 策略 5: projects_update_account_manager_managed
-- 业务理由：客户经理可管理自己的项目
-- 安全理由：必须验证 project_members 关系防止越权
CREATE POLICY projects_update_account_manager_managed ON projects
FOR UPDATE
TO authenticated
USING (
  has_role('account_manager')
  AND EXISTS (
    SELECT 1 FROM project_members
    WHERE project_id = projects.id
      AND user_id = auth.uid()
      AND role IN ('account_manager', 'project_owner')
  )
)
WITH CHECK (
  has_role('account_manager')
);

-- 策略 6: projects_delete_admin
-- 业务理由：项目删除是高危操作，仅管理员可执行
CREATE POLICY projects_delete_admin ON projects
FOR DELETE
TO authenticated
USING (
  has_role('admin')
);
```

---

### 5.3 project_members - 项目成员表

**表关键字段**：
- `id` (BIGINT, PK)
- `project_id` (BIGINT, FK → projects.id)
- `user_id` (UUID, FK → users.id)
- `role` (VARCHAR) - 成员角色（project_owner / member）

**角色访问规则**：

| 角色 | SELECT | INSERT | UPDATE | DELETE |
|------|--------|--------|--------|--------|
| admin | 所有成员 | ✅ | 所有成员 | 所有成员 |
| data_operator | 所有成员 | ✅ | 所有成员 | ✅ |
| account_manager | 管理的项目 | 管理的项目 | 管理的项目 | 管理的项目 |
| finance | 所有成员 | ❌ | ❌ | ❌ |
| media_buyer | 参与的项目 | ❌ | ❌ | ❌ |

**RLS 策略**：

```sql
-- ==================== project_members 表 RLS 策略 ====================

-- 策略 1: project_members_select_all_staff
-- 业务理由：员工角色需查看项目成员配置
CREATE POLICY project_members_select_all_staff ON project_members
FOR SELECT
TO authenticated
USING (
  has_any_role(ARRAY['admin', 'data_operator', 'finance'])
);

-- 策略 2: project_members_select_project_member
-- 业务理由：项目成员可查看同项目的其他成员
CREATE POLICY project_members_select_project_member ON project_members
FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM project_members pm2
    WHERE pm2.project_id = project_members.project_id
      AND pm2.user_id = auth.uid()
  )
);

-- 策略 3: project_members_insert_admin_data_operator
-- 业务理由：管理员和数据员配置项目成员
CREATE POLICY project_members_insert_admin_data_operator ON project_members
FOR INSERT
TO authenticated
WITH CHECK (
  has_any_role(ARRAY['admin', 'data_operator'])
);

-- 策略 4: project_members_insert_account_manager_managed
-- 业务理由：项目所有者可添加成员
-- 安全理由：必须验证 project_owner 角色防止普通成员越权
CREATE POLICY project_members_insert_account_manager_managed ON project_members
FOR INSERT
TO authenticated
WITH CHECK (
  has_role('account_manager')
  AND EXISTS (
    SELECT 1 FROM project_members pm
    WHERE pm.project_id = project_members.project_id
      AND pm.user_id = auth.uid()
      AND pm.role = 'project_owner'
  )
);

-- 策略 5: project_members_update_delete_admin_data_operator
-- 业务理由：管理员和数据员管理所有项目成员
CREATE POLICY project_members_update_delete_admin_data_operator ON project_members
FOR ALL
TO authenticated
USING (
  has_any_role(ARRAY['admin', 'data_operator'])
)
WITH CHECK (
  has_any_role(ARRAY['admin', 'data_operator'])
);

-- 策略 6: project_members_update_delete_account_manager_managed
-- 业务理由：项目所有者管理成员
CREATE POLICY project_members_update_delete_account_manager_managed ON project_members
FOR ALL
TO authenticated
USING (
  has_role('account_manager')
  AND EXISTS (
    SELECT 1 FROM project_members pm
    WHERE pm.project_id = project_members.project_id
      AND pm.user_id = auth.uid()
      AND pm.role = 'project_owner'
  )
)
WITH CHECK (
  has_role('account_manager')
);
```

---

### 5.4 channels - 渠道表

**表关键字段**：
- `id` (UUID, PK)
- `channel_name` (VARCHAR)
- `status` (VARCHAR) - active / inactive

**角色访问规则**：

| 角色 | SELECT | INSERT | UPDATE | DELETE |
|------|--------|--------|--------|--------|
| admin | 所有渠道 | ✅ | 所有渠道 | 所有渠道 |
| data_operator | 所有渠道 | ✅ | 所有渠道 | ❌ |
| account_manager | 所有渠道 | ❌ | ❌ | ❌ |
| finance | 所有渠道 | ❌ | ❌ | ❌ |
| media_buyer | 所有渠道 | ❌ | ❌ | ❌ |

**RLS 策略**：

```sql
-- ==================== channels 表 RLS 策略 ====================

-- 策略 1: channels_select_all
-- 业务理由：渠道是公共基础数据，所有用户可查看
CREATE POLICY channels_select_all ON channels
FOR SELECT
TO authenticated
USING (true);

-- 策略 2: channels_insert_update_admin_data_operator
-- 业务理由：渠道配置由管理员和数据员管理
CREATE POLICY channels_insert_update_admin_data_operator ON channels
FOR ALL
TO authenticated
USING (
  has_any_role(ARRAY['admin', 'data_operator'])
)
WITH CHECK (
  has_any_role(ARRAY['admin', 'data_operator'])
);

-- 策略 3: channels_delete_admin
-- 业务理由：删除渠道是高危操作，仅管理员可执行
CREATE POLICY channels_delete_admin ON channels
FOR DELETE
TO authenticated
USING (
  has_role('admin')
);
```

---

### 5.5 ad_accounts - 广告账户表

**表关键字段**：
- `id` (BIGINT, PK)
- `project_id` (BIGINT, FK → projects.id)
- `assigned_to` (UUID, FK → users.id) - 负责投手
- `status` (VARCHAR) - 账户状态
- `balance` (NUMERIC) - 账户余额

**角色访问规则**：

| 角色 | SELECT | INSERT | UPDATE | DELETE |
|------|--------|--------|--------|--------|
| admin | 所有账户 | ✅ | 所有账户 | 所有账户 |
| data_operator | 所有账户 | ✅ | 所有账户 | ❌ |
| account_manager | 管理的项目 | 管理的项目 | 管理的项目 | ❌ |
| finance | 所有账户 | ❌ | ❌ | ❌ |
| media_buyer | 分配给自己的 | ❌ | ❌ (应用层控制) | ❌ |

**说明**：
- 投手的字段级更新权限（如仅可更新 notes）无法通过 RLS 实现
- 已在应用层控制（见 `backend/routers/ad_accounts.py`）

**RLS 策略**：

```sql
-- ==================== ad_accounts 表 RLS 策略 ====================

-- 策略 1: ad_accounts_select_admin_data_operator_finance
-- 业务理由：管理员/数据员/财务需查看所有账户
CREATE POLICY ad_accounts_select_admin_data_operator_finance ON ad_accounts
FOR SELECT
TO authenticated
USING (
  has_any_role(ARRAY['admin', 'data_operator', 'finance'])
);

-- 策略 2: ad_accounts_select_account_manager_managed
-- 业务理由：客户经理查看管理的项目账户
CREATE POLICY ad_accounts_select_account_manager_managed ON ad_accounts
FOR SELECT
TO authenticated
USING (
  has_role('account_manager')
  AND EXISTS (
    SELECT 1 FROM project_members
    WHERE project_id = ad_accounts.project_id
      AND user_id = auth.uid()
  )
);

-- 策略 3: ad_accounts_select_media_buyer_assigned
-- 业务理由：投手查看分配给自己的账户
CREATE POLICY ad_accounts_select_media_buyer_assigned ON ad_accounts
FOR SELECT
TO authenticated
USING (
  assigned_to = auth.uid()
);

-- 策略 4: ad_accounts_insert_admin_data_operator
-- 业务理由：创建账户由管理员和数据员执行
CREATE POLICY ad_accounts_insert_admin_data_operator ON ad_accounts
FOR INSERT
TO authenticated
WITH CHECK (
  has_any_role(ARRAY['admin', 'data_operator'])
);

-- 策略 5: ad_accounts_insert_account_manager_managed
-- 业务理由：客户经理为管理的项目创建账户
CREATE POLICY ad_accounts_insert_account_manager_managed ON ad_accounts
FOR INSERT
TO authenticated
WITH CHECK (
  has_role('account_manager')
  AND EXISTS (
    SELECT 1 FROM project_members
    WHERE project_id = ad_accounts.project_id
      AND user_id = auth.uid()
  )
);

-- 策略 6: ad_accounts_update_admin_data_operator
-- 业务理由：管理员和数据员可修改所有字段
CREATE POLICY ad_accounts_update_admin_data_operator ON ad_accounts
FOR UPDATE
TO authenticated
USING (
  has_any_role(ARRAY['admin', 'data_operator'])
)
WITH CHECK (
  has_any_role(ARRAY['admin', 'data_operator'])
);

-- 策略 7: ad_accounts_update_account_manager_managed
-- 业务理由：客户经理修改管理的项目账户
CREATE POLICY ad_accounts_update_account_manager_managed ON ad_accounts
FOR UPDATE
TO authenticated
USING (
  has_role('account_manager')
  AND EXISTS (
    SELECT 1 FROM project_members
    WHERE project_id = ad_accounts.project_id
      AND user_id = auth.uid()
  )
)
WITH CHECK (
  has_role('account_manager')
);

-- ⚠️ 策略 8 已移除：字段级权限控制不能通过 RLS 实现（P0 安全修复）
--
-- 原策略问题：
-- - WITH CHECK 中的 (SELECT status FROM ad_accounts WHERE id = ad_accounts.id)
--   会返回**更新后**的值，导致检查总是通过，无法限制字段修改
-- - RLS 只能控制行级访问，无法控制列级权限
--
-- ✅ 正确的实现方式（3 选 1）：
--
-- 方案 1：数据库触发器（推荐）
-- CREATE TRIGGER prevent_field_modification
-- BEFORE UPDATE ON ad_accounts
-- FOR EACH ROW
-- EXECUTE FUNCTION check_media_buyer_field_restrictions();
--
-- 方案 2：应用层验证（当前方案）
-- if user_role == 'media_buyer':
--     if 'status' in update_data or 'balance' in update_data:
--         raise PermissionDenied("投手不能修改 status/balance 字段")
--
-- 方案 3：完全禁止投手 UPDATE 权限
-- 投手通过 API 提交变更请求，由数据员审核后更新
--
-- 📋 当前实施方案：应用层验证（见 backend/routers/ad_accounts.py）

-- 策略 9: ad_accounts_delete_admin
-- 业务理由：删除账户是高危操作，仅管理员可执行
CREATE POLICY ad_accounts_delete_admin ON ad_accounts
FOR DELETE
TO authenticated
USING (
  has_role('admin')
);
```

---

### 5.6 daily_reports - 日报表

**表关键字段**：
- `id` (BIGINT, PK)
- `ad_account_id` (BIGINT, FK → ad_accounts.id)
- `submitted_by` (UUID, FK → users.id) - 提交人
- `reviewed_by` (UUID, FK → users.id) - 审核人
- `status` (VARCHAR) - draft / pending / approved / rejected
- `report_date` (DATE)

**角色访问规则**：

| 角色 | SELECT | INSERT | UPDATE | DELETE |
|------|--------|--------|--------|--------|
| admin | 所有日报 | ✅ | 所有日报 | 所有日报 |
| data_operator | 所有日报 | ❌ | 所有日报（审核） | ❌ |
| account_manager | 管理的项目 | ❌ | ❌ | ❌ |
| finance | 已批准的 | ❌ | ❌ | ❌ |
| media_buyer | 自己的账户 | ✅ | 自己的（draft/rejected） | 自己的（draft） |

**RLS 策略**：

```sql
-- ==================== daily_reports 表 RLS 策略 ====================

-- 策略 1: daily_reports_select_admin_data_operator
-- 业务理由：管理员和数据员审核所有日报
CREATE POLICY daily_reports_select_admin_data_operator ON daily_reports
FOR SELECT
TO authenticated
USING (
  has_any_role(ARRAY['admin', 'data_operator'])
);

-- 策略 2: daily_reports_select_account_manager_managed
-- 业务理由：客户经理查看管理项目的日报
CREATE POLICY daily_reports_select_account_manager_managed ON daily_reports
FOR SELECT
TO authenticated
USING (
  has_role('account_manager')
  AND EXISTS (
    SELECT 1 FROM ad_accounts a
    JOIN project_members pm ON a.project_id = pm.project_id
    WHERE a.id = daily_reports.ad_account_id
      AND pm.user_id = auth.uid()
  )
);

-- 策略 3: daily_reports_select_finance_approved
-- 业务理由：财务仅查看已批准的日报进行财务核算
-- 安全理由：防止财务查看未审核的脏数据
CREATE POLICY daily_reports_select_finance_approved ON daily_reports
FOR SELECT
TO authenticated
USING (
  has_role('finance')
  AND status = 'approved'
);

-- 策略 4: daily_reports_select_media_buyer_own
-- 业务理由：投手查看自己提交的日报
CREATE POLICY daily_reports_select_media_buyer_own ON daily_reports
FOR SELECT
TO authenticated
USING (
  submitted_by = auth.uid()
);

-- 策略 5: daily_reports_insert_media_buyer
-- 业务理由：投手为分配的账户提交日报
-- 安全理由：验证账户归属防止投手跨账户提交日报
CREATE POLICY daily_reports_insert_media_buyer ON daily_reports
FOR INSERT
TO authenticated
WITH CHECK (
  has_role('media_buyer')
  AND submitted_by = auth.uid()
  AND EXISTS (
    SELECT 1 FROM ad_accounts
    WHERE id = daily_reports.ad_account_id
      AND assigned_to = auth.uid()
  )
);

-- 策略 6: daily_reports_update_admin
-- 业务理由：管理员可修改所有日报（错误修正）
CREATE POLICY daily_reports_update_admin ON daily_reports
FOR UPDATE
TO authenticated
USING (
  has_role('admin')
)
WITH CHECK (
  has_role('admin')
);

-- 策略 7: daily_reports_update_data_operator_review
-- 业务理由：数据员审核待审核的日报
-- 安全理由：仅允许从 pending 转为 approved/rejected
CREATE POLICY daily_reports_update_data_operator_review ON daily_reports
FOR UPDATE
TO authenticated
USING (
  has_role('data_operator')
  AND status = 'pending'
)
WITH CHECK (
  has_role('data_operator')
  AND status IN ('approved', 'rejected')
  AND reviewed_by = auth.uid()
);

-- 策略 8: daily_reports_update_media_buyer_draft_rejected
-- 业务理由：投手修改草稿和被拒绝的日报
-- 安全理由：仅允许修改自己的日报
CREATE POLICY daily_reports_update_media_buyer_draft_rejected ON daily_reports
FOR UPDATE
TO authenticated
USING (
  submitted_by = auth.uid()
  AND has_role('media_buyer')
  AND status IN ('draft', 'rejected')
)
WITH CHECK (
  submitted_by = auth.uid()
  AND status IN ('draft', 'pending')
);

-- 策略 9: daily_reports_delete_media_buyer_draft
-- 业务理由：投手删除草稿日报
CREATE POLICY daily_reports_delete_media_buyer_draft ON daily_reports
FOR DELETE
TO authenticated
USING (
  submitted_by = auth.uid()
  AND has_role('media_buyer')
  AND status = 'draft'
);

-- 策略 10: daily_reports_delete_admin
-- 业务理由：管理员清理错误数据
CREATE POLICY daily_reports_delete_admin ON daily_reports
FOR DELETE
TO authenticated
USING (
  has_role('admin')
);
```

---

### 5.7 ad_spend_daily - 广告消耗表

**表关键字段**：
- `id` (BIGINT, PK)
- `ad_account_id` (BIGINT, FK → ad_accounts.id)
- `data_date` (DATE) - 数据日期
- `spend` (NUMERIC) - 消耗金额
- `impressions` (INTEGER)
- `clicks` (INTEGER)

**角色访问规则**：

| 角色 | SELECT | INSERT | UPDATE | DELETE |
|------|--------|--------|--------|--------|
| admin | 所有数据 | ✅ | 所有数据 | 所有数据 |
| data_operator | 所有数据 | ✅ | 所有数据 | ❌ |
| account_manager | 管理的项目 | ❌ | ❌ | ❌ |
| finance | 所有数据 | ❌ | ❌ | ❌ |
| media_buyer | 自己的账户 | ❌ | ❌ | ❌ |

**RLS 策略**：

```sql
-- ==================== ad_spend_daily 表 RLS 策略 ====================

-- 策略 1: ad_spend_daily_select_admin_data_operator_finance
-- 业务理由：管理员/数据员/财务进行数据分析
CREATE POLICY ad_spend_daily_select_admin_data_operator_finance ON ad_spend_daily
FOR SELECT
TO authenticated
USING (
  has_any_role(ARRAY['admin', 'data_operator', 'finance'])
);

-- 策略 2: ad_spend_daily_select_account_manager_managed
-- 业务理由：客户经理查看管理项目的消耗数据
CREATE POLICY ad_spend_daily_select_account_manager_managed ON ad_spend_daily
FOR SELECT
TO authenticated
USING (
  has_role('account_manager')
  AND EXISTS (
    SELECT 1 FROM ad_accounts a
    JOIN project_members pm ON a.project_id = pm.project_id
    WHERE a.id = ad_spend_daily.ad_account_id
      AND pm.user_id = auth.uid()
  )
);

-- 策略 3: ad_spend_daily_select_media_buyer_assigned
-- 业务理由：投手查看自己账户的消耗数据
CREATE POLICY ad_spend_daily_select_media_buyer_assigned ON ad_spend_daily
FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM ad_accounts
    WHERE id = ad_spend_daily.ad_account_id
      AND assigned_to = auth.uid()
  )
);

-- 策略 4: ad_spend_daily_insert_update_admin_data_operator
-- 业务理由：消耗数据由管理员和数据员导入和校正
CREATE POLICY ad_spend_daily_insert_update_admin_data_operator ON ad_spend_daily
FOR ALL
TO authenticated
USING (
  has_any_role(ARRAY['admin', 'data_operator'])
)
WITH CHECK (
  has_any_role(ARRAY['admin', 'data_operator'])
);

-- 策略 5: ad_spend_daily_delete_admin
-- 业务理由：删除消耗数据是高危操作，仅管理员可执行
CREATE POLICY ad_spend_daily_delete_admin ON ad_spend_daily
FOR DELETE
TO authenticated
USING (
  has_role('admin')
);
```

---

### 5.8 topup_requests - 充值申请表

**表关键字段**：
- `id` (BIGINT, PK)
- `ad_account_id` (BIGINT, FK → ad_accounts.id)
- `requested_by` (UUID, FK → users.id) - 申请人
- `reviewed_by` (UUID, FK → users.id) - 数据员审核人
- `approved_by` (UUID, FK → users.id) - 财务批准人
- `amount` (NUMERIC) - 充值金额
- `status` (VARCHAR) - draft / pending_review / finance_approve / paid / completed / rejected / cancelled

**角色访问规则**：

| 角色 | SELECT | INSERT | UPDATE | DELETE |
|------|--------|--------|--------|--------|
| admin | 所有申请 | ✅ | 所有申请 | 所有申请 |
| data_operator | 所有申请 | ❌ | 审核操作 | ❌ |
| account_manager | 管理的项目 | ❌ | ❌ | ❌ |
| finance | 所有申请 | ❌ | 批准操作 | ❌ |
| media_buyer | 自己的申请 | ✅ | 自己的（draft） | 自己的（draft） |

**RLS 策略**：

```sql
-- ==================== topup_requests 表 RLS 策略 ====================

-- 策略 1: topup_requests_select_admin_data_operator_finance
-- 业务理由：管理员/数据员/财务查看所有充值申请
CREATE POLICY topup_requests_select_admin_data_operator_finance ON topup_requests
FOR SELECT
TO authenticated
USING (
  has_any_role(ARRAY['admin', 'data_operator', 'finance'])
);

-- 策略 2: topup_requests_select_account_manager_managed
-- 业务理由：客户经理查看管理项目的充值申请
CREATE POLICY topup_requests_select_account_manager_managed ON topup_requests
FOR SELECT
TO authenticated
USING (
  has_role('account_manager')
  AND EXISTS (
    SELECT 1 FROM ad_accounts a
    JOIN project_members pm ON a.project_id = pm.project_id
    WHERE a.id = topup_requests.ad_account_id
      AND pm.user_id = auth.uid()
  )
);

-- 策略 3: topup_requests_select_media_buyer_own
-- 业务理由：投手查看自己的充值申请
CREATE POLICY topup_requests_select_media_buyer_own ON topup_requests
FOR SELECT
TO authenticated
USING (
  requested_by = auth.uid()
);

-- 策略 4: topup_requests_insert_media_buyer
-- 业务理由：投手为分配的账户申请充值
-- 安全理由：验证账户归属防止投手跨账户申请充值
CREATE POLICY topup_requests_insert_media_buyer ON topup_requests
FOR INSERT
TO authenticated
WITH CHECK (
  has_role('media_buyer')
  AND requested_by = auth.uid()
  AND EXISTS (
    SELECT 1 FROM ad_accounts
    WHERE id = topup_requests.ad_account_id
      AND assigned_to = auth.uid()
  )
);

-- 策略 5: topup_requests_update_admin
-- 业务理由：管理员可修改所有充值申请（错误修正）
CREATE POLICY topup_requests_update_admin ON topup_requests
FOR UPDATE
TO authenticated
USING (
  has_role('admin')
)
WITH CHECK (
  has_role('admin')
);

-- 策略 6: topup_requests_update_data_operator_review
-- 业务理由：数据员审核充值申请
-- 安全理由：仅允许从 pending_review 转为 finance_approve/rejected
CREATE POLICY topup_requests_update_data_operator_review ON topup_requests
FOR UPDATE
TO authenticated
USING (
  has_role('data_operator')
  AND status = 'pending_review'
)
WITH CHECK (
  has_role('data_operator')
  AND status IN ('finance_approve', 'rejected')
  AND reviewed_by = auth.uid()
);

-- 策略 7: topup_requests_update_finance_approve
-- 业务理由：财务批准充值申请
-- 安全理由：仅允许从 finance_approve 转为 paid/rejected
CREATE POLICY topup_requests_update_finance_approve ON topup_requests
FOR UPDATE
TO authenticated
USING (
  has_role('finance')
  AND status = 'finance_approve'
)
WITH CHECK (
  has_role('finance')
  AND status IN ('paid', 'rejected')
  AND approved_by = auth.uid()
);

-- 策略 8: topup_requests_update_media_buyer_draft
-- 业务理由：投手修改草稿状态的充值申请
CREATE POLICY topup_requests_update_media_buyer_draft ON topup_requests
FOR UPDATE
TO authenticated
USING (
  requested_by = auth.uid()
  AND has_role('media_buyer')
  AND status = 'draft'
)
WITH CHECK (
  requested_by = auth.uid()
  AND status IN ('draft', 'pending_review')
);

-- 策略 9: topup_requests_delete_media_buyer_draft
-- 业务理由：投手删除草稿充值申请
CREATE POLICY topup_requests_delete_media_buyer_draft ON topup_requests
FOR DELETE
TO authenticated
USING (
  requested_by = auth.uid()
  AND has_role('media_buyer')
  AND status = 'draft'
);

-- 策略 10: topup_requests_delete_admin
-- 业务理由：管理员清理错误数据
CREATE POLICY topup_requests_delete_admin ON topup_requests
FOR DELETE
TO authenticated
USING (
  has_role('admin')
);
```

---

### 5.9 ledger_entries - 账本表

**表关键字段**：
- `id` (BIGINT, PK)
- `ad_account_id` (BIGINT, FK → ad_accounts.id)
- `entry_type` (VARCHAR) - topup_received / spend / adjustment
- `amount` (NUMERIC)
- `entry_date` (DATE)
- `created_by` (UUID, FK → users.id)

**角色访问规则**：

| 角色 | SELECT | INSERT | UPDATE | DELETE |
|------|--------|--------|--------|--------|
| admin | 所有记录 | ✅ | 所有记录 | 所有记录 |
| data_operator | 所有记录 | ✅ | ❌ | ❌ |
| account_manager | 管理的项目 | ❌ | ❌ | ❌ |
| finance | 所有记录 | ❌ | ❌ | ❌ |
| media_buyer | 自己的账户 | ❌ | ❌ | ❌ |

**RLS 策略**：

```sql
-- ==================== ledger_entries 表 RLS 策略 ====================

-- 策略 1: ledger_entries_select_admin_data_operator_finance
-- 业务理由：管理员/数据员/财务查看所有账本记录
CREATE POLICY ledger_entries_select_admin_data_operator_finance ON ledger_entries
FOR SELECT
TO authenticated
USING (
  has_any_role(ARRAY['admin', 'data_operator', 'finance'])
);

-- 策略 2: ledger_entries_select_account_manager_managed
-- 业务理由：客户经理查看管理项目的账本记录
CREATE POLICY ledger_entries_select_account_manager_managed ON ledger_entries
FOR SELECT
TO authenticated
USING (
  has_role('account_manager')
  AND EXISTS (
    SELECT 1 FROM ad_accounts a
    JOIN project_members pm ON a.project_id = pm.project_id
    WHERE a.id = ledger_entries.ad_account_id
      AND pm.user_id = auth.uid()
  )
);

-- 策略 3: ledger_entries_select_media_buyer_assigned
-- 业务理由：投手查看自己账户的账本记录
CREATE POLICY ledger_entries_select_media_buyer_assigned ON ledger_entries
FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM ad_accounts
    WHERE id = ledger_entries.ad_account_id
      AND assigned_to = auth.uid()
  )
);

-- 策略 4: ledger_entries_insert_admin_data_operator
-- 业务理由：账本记录由管理员和数据员创建
-- 安全理由：防止投手直接操作账本（仅通过充值申请间接创建）
CREATE POLICY ledger_entries_insert_admin_data_operator ON ledger_entries
FOR INSERT
TO authenticated
WITH CHECK (
  has_any_role(ARRAY['admin', 'data_operator'])
);

-- 策略 5: ledger_entries_update_delete_admin
-- 业务理由：修改和删除账本是高危操作，仅管理员可执行
CREATE POLICY ledger_entries_update_delete_admin ON ledger_entries
FOR ALL
TO authenticated
USING (
  has_role('admin')
)
WITH CHECK (
  has_role('admin')
);
```

---

### 5.10 reconciliation_batches - 对账批次表

**表关键字段**：
- `id` (BIGINT, PK)
- `batch_code` (VARCHAR, UNIQUE)
- `period_start` (DATE)
- `period_end` (DATE)
- `status` (VARCHAR) - draft / pending / reviewing / closed
- `created_by` (UUID, FK → users.id)
- `reviewed_by` (UUID, FK → users.id)

**角色访问规则**：

| 角色 | SELECT | INSERT | UPDATE | DELETE |
|------|--------|--------|--------|--------|
| admin | 所有批次 | ✅ | 所有批次 | 所有批次 |
| data_operator | 所有批次 | ✅ | 所有批次 | ❌ |
| account_manager | 所有批次 | ❌ | ❌ | ❌ |
| finance | 所有批次 | ❌ | ❌ | ❌ |
| media_buyer | 无权限 | ❌ | ❌ | ❌ |

**RLS 策略**：

```sql
-- ==================== reconciliation_batches 表 RLS 策略 ====================

-- 策略 1: reconciliation_batches_select_staff
-- 业务理由：所有员工可查看对账批次（透明化）
CREATE POLICY reconciliation_batches_select_staff ON reconciliation_batches
FOR SELECT
TO authenticated
USING (
  has_any_role(ARRAY['admin', 'data_operator', 'account_manager', 'finance'])
);

-- 策略 2: reconciliation_batches_insert_admin_data_operator
-- 业务理由：对账批次由管理员和数据员创建
CREATE POLICY reconciliation_batches_insert_admin_data_operator ON reconciliation_batches
FOR INSERT
TO authenticated
WITH CHECK (
  has_any_role(ARRAY['admin', 'data_operator'])
);

-- 策略 3: reconciliation_batches_update_admin_data_operator
-- 业务理由：对账批次由管理员和数据员管理
CREATE POLICY reconciliation_batches_update_admin_data_operator ON reconciliation_batches
FOR UPDATE
TO authenticated
USING (
  has_any_role(ARRAY['admin', 'data_operator'])
)
WITH CHECK (
  has_any_role(ARRAY['admin', 'data_operator'])
);

-- 策略 4: reconciliation_batches_delete_admin
-- 业务理由：删除对账批次是高危操作，仅管理员可执行
CREATE POLICY reconciliation_batches_delete_admin ON reconciliation_batches
FOR DELETE
TO authenticated
USING (
  has_role('admin')
);
```

---

### 5.11 reconciliation_details - 对账明细表

**表关键字段**：
- `id` (BIGINT, PK)
- `batch_id` (BIGINT, FK → reconciliation_batches.id)
- `ad_account_id` (BIGINT, FK → ad_accounts.id)
- `system_spend` (NUMERIC)
- `actual_spend` (NUMERIC)
- `discrepancy` (NUMERIC)
- `status` (VARCHAR) - pending / confirmed / adjusted

**角色访问规则**：

| 角色 | SELECT | INSERT | UPDATE | DELETE |
|------|--------|--------|--------|--------|
| admin | 所有明细 | ✅ | 所有明细 | 所有明细 |
| data_operator | 所有明细 | ✅ | 所有明细 | ❌ |
| account_manager | 所有明细 | ❌ | ❌ | ❌ |
| finance | 所有明细 | ❌ | ❌ | ❌ |
| media_buyer | 无权限 | ❌ | ❌ | ❌ |

**RLS 策略**：

```sql
-- ==================== reconciliation_details 表 RLS 策略 ====================

-- 策略 1: reconciliation_details_select_staff
-- 业务理由：所有员工可查看对账明细（透明化）
CREATE POLICY reconciliation_details_select_staff ON reconciliation_details
FOR SELECT
TO authenticated
USING (
  has_any_role(ARRAY['admin', 'data_operator', 'account_manager', 'finance'])
);

-- 策略 2: reconciliation_details_insert_admin_data_operator
-- 业务理由：对账明细由管理员和数据员创建
CREATE POLICY reconciliation_details_insert_admin_data_operator ON reconciliation_details
FOR INSERT
TO authenticated
WITH CHECK (
  has_any_role(ARRAY['admin', 'data_operator'])
);

-- 策略 3: reconciliation_details_update_admin_data_operator
-- 业务理由：对账明细由管理员和数据员管理
CREATE POLICY reconciliation_details_update_admin_data_operator ON reconciliation_details
FOR UPDATE
TO authenticated
USING (
  has_any_role(ARRAY['admin', 'data_operator'])
)
WITH CHECK (
  has_any_role(ARRAY['admin', 'data_operator'])
);

-- 策略 4: reconciliation_details_delete_admin
-- 业务理由：删除对账明细是高危操作，仅管理员可执行
CREATE POLICY reconciliation_details_delete_admin ON reconciliation_details
FOR DELETE
TO authenticated
USING (
  has_role('admin')
);
```

---

### 5.12 account_status_history - 账户状态历史表

**表关键字段**：
- `id` (BIGINT, PK)
- `ad_account_id` (BIGINT, FK → ad_accounts.id)
- `old_status` (VARCHAR)
- `new_status` (VARCHAR)
- `changed_by` (UUID, FK → users.id)
- `changed_at` (TIMESTAMPTZ)
- `reason` (TEXT)

**角色访问规则**：

| 角色 | SELECT | INSERT | UPDATE | DELETE |
|------|--------|--------|--------|--------|
| admin | 所有历史 | 系统自动 | ❌ | ❌ |
| data_operator | 所有历史 | 系统自动 | ❌ | ❌ |
| account_manager | 管理的项目 | ❌ | ❌ | ❌ |
| finance | 所有历史 | ❌ | ❌ | ❌ |
| media_buyer | 自己的账户 | ❌ | ❌ | ❌ |

**RLS 策略**：

```sql
-- ==================== account_status_history 表 RLS 策略 ====================

-- 策略 1: account_status_history_select_admin_data_operator_finance
-- 业务理由：管理员/数据员/财务查看所有状态历史
CREATE POLICY account_status_history_select_admin_data_operator_finance ON account_status_history
FOR SELECT
TO authenticated
USING (
  has_any_role(ARRAY['admin', 'data_operator', 'finance'])
);

-- 策略 2: account_status_history_select_account_manager_managed
-- 业务理由：客户经理查看管理项目的状态历史
CREATE POLICY account_status_history_select_account_manager_managed ON account_status_history
FOR SELECT
TO authenticated
USING (
  has_role('account_manager')
  AND EXISTS (
    SELECT 1 FROM ad_accounts a
    JOIN project_members pm ON a.project_id = pm.project_id
    WHERE a.id = account_status_history.ad_account_id
      AND pm.user_id = auth.uid()
  )
);

-- 策略 3: account_status_history_select_media_buyer_assigned
-- 业务理由：投手查看自己账户的状态历史
CREATE POLICY account_status_history_select_media_buyer_assigned ON account_status_history
FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM ad_accounts
    WHERE id = account_status_history.ad_account_id
      AND assigned_to = auth.uid()
  )
);

-- 策略 4: account_status_history_insert_system
-- 业务理由：状态历史通常由触发器自动记录
-- 安全理由：限制只有管理员和数据员可手动插入
CREATE POLICY account_status_history_insert_system ON account_status_history
FOR INSERT
TO authenticated
WITH CHECK (
  has_any_role(ARRAY['admin', 'data_operator'])
);
```

---

### 5.13 account_alerts - 账户预警表

**表关键字段**：
- `id` (BIGINT, PK)
- `ad_account_id` (BIGINT, FK → ad_accounts.id)
- `alert_type` (VARCHAR) - low_balance / high_spend / account_suspended
- `status` (VARCHAR) - open / ack / resolved
- `created_at` (TIMESTAMPTZ)
- `acknowledged_by` (UUID, FK → users.id)

**角色访问规则**：

| 角色 | SELECT | INSERT | UPDATE | DELETE |
|------|--------|--------|--------|--------|
| admin | 所有预警 | ✅ | 所有预警 | 所有预警 |
| data_operator | 所有预警 | ✅ | 所有预警 | ❌ |
| account_manager | 管理的项目 | ❌ | 管理的项目 | ❌ |
| finance | 所有预警 | ❌ | ❌ | ❌ |
| media_buyer | 自己的账户 | ❌ | 确认操作 | ❌ |

**RLS 策略**：

```sql
-- ==================== account_alerts 表 RLS 策略 ====================

-- 策略 1: account_alerts_select_admin_data_operator_finance
-- 业务理由：管理员/数据员/财务查看所有预警
CREATE POLICY account_alerts_select_admin_data_operator_finance ON account_alerts
FOR SELECT
TO authenticated
USING (
  has_any_role(ARRAY['admin', 'data_operator', 'finance'])
);

-- 策略 2: account_alerts_select_account_manager_managed
-- 业务理由：客户经理查看管理项目的预警
CREATE POLICY account_alerts_select_account_manager_managed ON account_alerts
FOR SELECT
TO authenticated
USING (
  has_role('account_manager')
  AND EXISTS (
    SELECT 1 FROM ad_accounts a
    JOIN project_members pm ON a.project_id = pm.project_id
    WHERE a.id = account_alerts.ad_account_id
      AND pm.user_id = auth.uid()
  )
);

-- 策略 3: account_alerts_select_media_buyer_assigned
-- 业务理由：投手查看自己账户的预警
CREATE POLICY account_alerts_select_media_buyer_assigned ON account_alerts
FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM ad_accounts
    WHERE id = account_alerts.ad_account_id
      AND assigned_to = auth.uid()
  )
);

-- 策略 4: account_alerts_insert_update_admin_data_operator
-- 业务理由：管理员和数据员管理预警
CREATE POLICY account_alerts_insert_update_admin_data_operator ON account_alerts
FOR ALL
TO authenticated
USING (
  has_any_role(ARRAY['admin', 'data_operator'])
)
WITH CHECK (
  has_any_role(ARRAY['admin', 'data_operator'])
);

-- 策略 5: account_alerts_update_account_manager_managed
-- 业务理由：客户经理处理管理项目的预警
CREATE POLICY account_alerts_update_account_manager_managed ON account_alerts
FOR UPDATE
TO authenticated
USING (
  has_role('account_manager')
  AND EXISTS (
    SELECT 1 FROM ad_accounts a
    JOIN project_members pm ON a.project_id = pm.project_id
    WHERE a.id = account_alerts.ad_account_id
      AND pm.user_id = auth.uid()
  )
)
WITH CHECK (
  has_role('account_manager')
  AND status IN ('ack', 'resolved')
);

-- 策略 6: account_alerts_update_media_buyer_acknowledge
-- 业务理由：投手确认自己账户的预警
-- 安全理由：仅允许从 open 转为 ack
CREATE POLICY account_alerts_update_media_buyer_acknowledge ON account_alerts
FOR UPDATE
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM ad_accounts
    WHERE id = account_alerts.ad_account_id
      AND assigned_to = auth.uid()
  )
  AND status = 'open'
)
WITH CHECK (
  status = 'ack'
  AND acknowledged_by = auth.uid()
);

-- 策略 7: account_alerts_delete_admin
-- 业务理由：删除预警是高危操作，仅管理员可执行
CREATE POLICY account_alerts_delete_admin ON account_alerts
FOR DELETE
TO authenticated
USING (
  has_role('admin')
);
```

---

### 5.14 audit_logs - 审计日志表

**表关键字段**：
- `id` (BIGINT, PK)
- `user_id` (UUID, FK → users.id)
- `action` (VARCHAR) - create / update / delete / login
- `table_name` (VARCHAR)
- `record_id` (BIGINT)
- `changes` (JSONB)
- `created_at` (TIMESTAMPTZ)

**角色访问规则**：

| 角色 | SELECT | INSERT | UPDATE | DELETE |
|------|--------|--------|--------|--------|
| admin | 所有日志 | 系统自动 | ❌ | ❌ |
| data_operator | 所有日志 | 系统自动 | ❌ | ❌ |
| account_manager | 管理的项目相关 | ❌ | ❌ | ❌ |
| finance | 财务相关日志 | ❌ | ❌ | ❌ |
| media_buyer | 无权限 | ❌ | ❌ | ❌ |

**RLS 策略**：

```sql
-- ==================== audit_logs 表 RLS 策略 ====================
-- ⚠️ 重要：审计日志是合规审计的关键数据，必须确保不可篡改

-- 策略 1: audit_logs_select_admin_data_operator
-- 业务理由：管理员和数据员查看所有审计日志
CREATE POLICY audit_logs_select_admin_data_operator ON audit_logs
FOR SELECT
TO authenticated
USING (
  has_any_role(ARRAY['admin', 'data_operator'])
);

-- 策略 2: audit_logs_select_account_manager_managed
-- 业务理由：客户经理查看管理项目相关的审计日志
CREATE POLICY audit_logs_select_account_manager_managed ON audit_logs
FOR SELECT
TO authenticated
USING (
  has_role('account_manager')
  AND table_name IN ('projects', 'project_members', 'ad_accounts', 'daily_reports')
);

-- 策略 3: audit_logs_select_finance_financial
-- 业务理由：财务查看财务相关的审计日志
CREATE POLICY audit_logs_select_finance_financial ON audit_logs
FOR SELECT
TO authenticated
USING (
  has_role('finance')
  AND table_name IN ('topup_requests', 'ledger_entries', 'reconciliation_batches')
);

-- 策略 4: audit_logs_insert_system
-- 业务理由：审计日志由应用层自动记录
-- 安全理由：限制只有管理员和数据员可手动插入
CREATE POLICY audit_logs_insert_system ON audit_logs
FOR INSERT
TO authenticated
WITH CHECK (
  has_any_role(ARRAY['admin', 'data_operator'])
  AND user_id = auth.uid()
);

-- ✅ 策略 5: audit_logs_deny_update（P1 安全修复：防篡改保护）
-- 合规理由：SOC2/ISO27001 要求审计日志不可修改
-- 技术理由：明确拒绝所有用户修改审计日志，确保日志完整性
CREATE POLICY audit_logs_deny_update ON audit_logs
FOR UPDATE
TO authenticated
USING (false);  -- 永远拒绝

-- ✅ 策略 6: audit_logs_deny_delete（P1 安全修复：防篡改保护）
-- 合规理由：SOC2/ISO27001 要求审计日志不可删除
-- 技术理由：明确拒绝所有用户删除审计日志，符合合规要求
CREATE POLICY audit_logs_deny_delete ON audit_logs
FOR DELETE
TO authenticated
USING (false);  -- 永远拒绝
```

**安全说明**：
- ✅ 已修复 P1 篡改风险：明确禁止 UPDATE/DELETE 操作
- 📋 合规要求：符合 SOC2/ISO27001 审计日志不可变性要求
- ⚠️ 数据清理：如需清理历史数据，必须由 DBA 手动执行 `ALTER TABLE ... DISABLE ROW LEVEL SECURITY` 后操作，并记录到独立的审计系统

---

## 6. RLS SQL 模板库

### 6.1 Helper 函数（减少代码重复）

**问题**：`(SELECT role FROM users WHERE id = auth.uid())` 在策略中重复使用，影响可维护性。

**解决方案**：创建 PostgreSQL 函数封装常用查询逻辑。

```sql
-- ==================== Helper 函数定义 ====================

-- Helper 函数 1: 获取当前用户角色
CREATE OR REPLACE FUNCTION get_current_user_role()
RETURNS TEXT
LANGUAGE SQL
STABLE
SECURITY DEFINER
AS $$
  SELECT role FROM users WHERE id = auth.uid();
$$;

-- Helper 函数 2: 检查用户是否有指定角色
CREATE OR REPLACE FUNCTION has_role(required_role TEXT)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
SECURITY DEFINER
AS $$
  SELECT EXISTS (
    SELECT 1 FROM users
    WHERE id = auth.uid()
      AND role = required_role
  );
$$;

-- Helper 函数 3: 检查用户是否有多个角色之一
CREATE OR REPLACE FUNCTION has_any_role(required_roles TEXT[])
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
SECURITY DEFINER
AS $$
  SELECT EXISTS (
    SELECT 1 FROM users
    WHERE id = auth.uid()
      AND role = ANY(required_roles)
  );
$$;

-- Helper 函数 4: 检查用户是否是项目成员
CREATE OR REPLACE FUNCTION is_project_member(p_project_id BIGINT)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
SECURITY DEFINER
AS $$
  SELECT EXISTS (
    SELECT 1 FROM project_members
    WHERE project_id = p_project_id
      AND user_id = auth.uid()
  );
$$;
```

**使用示例**：

```sql
-- ❌ 优化前：代码重复
CREATE POLICY projects_select_admin_data_operator ON projects
FOR SELECT
TO authenticated
USING (
  (SELECT role FROM users WHERE id = auth.uid()) IN ('admin', 'data_operator', 'finance')
);

-- ✅ 优化后：使用 helper 函数
CREATE POLICY projects_select_admin_data_operator ON projects
FOR SELECT
TO authenticated
USING (
  has_any_role(ARRAY['admin', 'data_operator', 'finance'])
);
```

**性能说明**：
- `STABLE` 函数会在同一语句中缓存结果，性能优于重复子查询
- `SECURITY DEFINER` 确保函数使用定义者权限执行
- 建议索引：`CREATE INDEX idx_users_id_role ON users(id, role);`

**⚠️ 注意**：
- Helper 函数适用于**非 users 表**的策略（避免循环依赖）
- users 表策略必须继续使用 JWT Claims
- 部署时需先创建函数，再创建引用这些函数的策略

---

### 6.2 启用 RLS 模板

```sql
-- 为新表启用 RLS
ALTER TABLE <table_name> ENABLE ROW LEVEL SECURITY;
ALTER TABLE <table_name> FORCE ROW LEVEL SECURITY;

-- 验证 RLS 状态
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

---

### 6.3 策略创建模板

```sql
-- SELECT 策略模板
CREATE POLICY <policy_name> ON <table_name>
FOR SELECT
TO authenticated
USING (
  <condition>
);

-- INSERT 策略模板
CREATE POLICY <policy_name> ON <table_name>
FOR INSERT
TO authenticated
WITH CHECK (
  <condition>
);

-- UPDATE 策略模板
CREATE POLICY <policy_name> ON <table_name>
FOR UPDATE
TO authenticated
USING (
  <using_condition>  -- 决定哪些行可以被更新
)
WITH CHECK (
  <check_condition>  -- 验证更新后的值是否合法
);

-- DELETE 策略模板
CREATE POLICY <policy_name> ON <table_name>
FOR DELETE
TO authenticated
USING (
  <condition>
);

-- ALL 策略模板
CREATE POLICY <policy_name> ON <table_name>
FOR ALL
TO authenticated
USING (
  <condition>
)
WITH CHECK (
  <condition>
);
```

---

### 6.4 常用条件模板

```sql
-- ✅ 使用 Helper 函数（推荐）
has_role('admin')
has_any_role(ARRAY['admin', 'data_operator'])
is_project_member(<table>.project_id)

-- ✅ 直接条件判断
created_by = auth.uid()
assigned_to = auth.uid()

-- ✅ 成员关系验证
EXISTS (
  SELECT 1 FROM project_members
  WHERE project_id = <table>.project_id
    AND user_id = auth.uid()
)

-- ✅ 账户归属验证
EXISTS (
  SELECT 1 FROM ad_accounts
  WHERE id = <table>.ad_account_id
    AND assigned_to = auth.uid()
)
```

---

### 6.5 策略管理命令

```sql
-- 查看表的所有策略
SELECT
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd,
  qual,
  with_check
FROM pg_policies
WHERE tablename = '<table_name>'
ORDER BY policyname;

-- 删除策略
DROP POLICY IF EXISTS <policy_name> ON <table_name>;

-- 禁用 RLS（⚠️ 生产环境禁止使用）
ALTER TABLE <table_name> DISABLE ROW LEVEL SECURITY;

-- 查看所有启用 RLS 的表
SELECT tablename
FROM pg_tables
WHERE schemaname = 'public'
  AND rowsecurity = true
ORDER BY tablename;
```

---

### 6.6 测试 RLS 模板

```sql
-- 模拟用户查询（Supabase）
SET request.jwt.claims TO '{"sub": "<user_uuid>", "role": "authenticated"}';

-- 测试查询
SELECT * FROM <table_name>;

-- 重置会话
RESET request.jwt.claims;
```

---

## 7. RLS 变更流程

### 7.1 变更流程图

```
需求评审
    ↓
更新 RLS_POLICIES.md（本文档）
    ↓
生成 Alembic 迁移文件
    ↓
Code Review
    ↓
在开发环境测试
    ↓
在测试环境验证
    ↓
审计委员会批准
    ↓
生产环境部署
    ↓
监控 + 审计日志
```

---

### 7.2 变更类型与审批权限

| 变更类型 | 审批级别 | 需要的审批人 | 回退风险 |
|---------|---------|------------|---------|
| **新增策略** | L1（低风险） | Tech Lead | 低 |
| **收紧权限** | L2（中风险） | Tech Lead + DBA | 中（可能影响业务） |
| **放松权限** | L3（高风险） | CTO + Security Team | 高（安全风险） |
| **删除策略** | L3（高风险） | CTO + Security Team | 高（数据泄露风险） |
| **修改角色定义** | L3（高风险） | CTO + Security Team | 极高（全局影响） |

---

### 7.3 变更检查清单

**变更前检查**：
- [ ] 更新本文档（RLS_POLICIES.md）
- [ ] 更新相关业务文档（BUSINESS_RULES.md / STATE_MACHINE.md）
- [ ] 创建 Alembic 迁移文件
- [ ] 编写迁移文件的 `upgrade()` 和 `downgrade()`
- [ ] 在迁移文件中添加详细注释
- [ ] 编写单元测试验证新策略
- [ ] 在开发环境执行迁移并测试

**变更后验证**：
- [ ] 验证所有角色的权限是否符合预期
- [ ] 检查审计日志是否正常记录
- [ ] 运行全量测试套件
- [ ] 性能测试（RLS 可能影响查询性能）
- [ ] 安全扫描（使用 `pg_policies` 视图检查）

**回滚准备**：
- [ ] 准备回滚 SQL 脚本
- [ ] 备份当前策略定义
- [ ] 明确回滚决策点（如何判断需要回滚）

---

### 7.4 紧急回滚流程

如果部署后发现问题：

```sql
-- 1. 立即禁用有问题的策略
DROP POLICY <problematic_policy> ON <table_name>;

-- 2. 恢复旧策略
<execute old policy SQL>

-- 3. 验证回滚
SELECT * FROM pg_policies WHERE tablename = '<table_name>';

-- 4. 通知团队并记录事件
```

---

## 8. RLS 测试与审计

### 8.1 单元测试模板

```python
# backend/tests/test_rls_policies.py

import pytest
from sqlalchemy import text
from backend.core.db import get_db

def test_media_buyer_can_only_see_own_daily_reports(db_session, test_user_media_buyer):
    """测试：投手只能查看自己提交的日报"""

    # 设置 JWT Claims
    db_session.execute(text(f"""
        SET request.jwt.claims TO '{{"sub": "{test_user_media_buyer.id}", "role": "authenticated"}}';
    """))

    # 查询日报
    result = db_session.execute(text("SELECT COUNT(*) FROM daily_reports;")).scalar()

    # 预期：只能看到自己的日报
    expected_count = db_session.execute(text(f"""
        SELECT COUNT(*) FROM daily_reports WHERE submitted_by = '{test_user_media_buyer.id}';
    """)).scalar()

    assert result == expected_count

def test_finance_cannot_insert_daily_reports(db_session, test_user_finance):
    """测试：财务不能插入日报"""

    db_session.execute(text(f"""
        SET request.jwt.claims TO '{{"sub": "{test_user_finance.id}", "role": "authenticated"}}';
    """))

    with pytest.raises(Exception):
        db_session.execute(text("""
            INSERT INTO daily_reports (ad_account_id, submitted_by, status, report_date)
            VALUES (1, '{test_user_finance.id}', 'draft', '2025-01-01');
        """))

def test_admin_can_access_all_data(db_session, test_user_admin):
    """测试：管理员可以访问所有数据"""

    db_session.execute(text(f"""
        SET request.jwt.claims TO '{{"sub": "{test_user_admin.id}", "role": "authenticated"}}';
    """))

    result = db_session.execute(text("SELECT COUNT(*) FROM projects;")).scalar()
    assert result > 0
```

---

### 8.2 CI 自动化测试

```yaml
# .github/workflows/rls_tests.yml

name: RLS Policies Test

on:
  pull_request:
    paths:
      - 'backend/alembic/versions/*.py'
      - 'docs/RLS_POLICIES.md'

jobs:
  test-rls:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Database
        run: docker-compose up -d postgres

      - name: Run Migrations
        run: |
          cd backend
          alembic upgrade head

      - name: Run RLS Tests
        run: |
          pytest backend/tests/test_rls_policies.py -v

      - name: Validate Policy Count
        run: |
          psql $DATABASE_URL -c "SELECT COUNT(*) FROM pg_policies WHERE schemaname = 'public';"
```

---

### 8.3 策略审计脚本

```sql
-- 检查所有表是否启用 RLS
SELECT
  tablename,
  CASE
    WHEN rowsecurity THEN '✅ 已启用'
    ELSE '❌ 未启用'
  END AS rls_status
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename NOT LIKE 'pg_%'
ORDER BY tablename;

-- 检查策略覆盖率
SELECT
  t.tablename,
  COUNT(p.policyname) AS policy_count,
  STRING_AGG(DISTINCT p.cmd::text, ', ') AS operations_covered
FROM pg_tables t
LEFT JOIN pg_policies p ON t.tablename = p.tablename
WHERE t.schemaname = 'public'
  AND t.tablename NOT LIKE 'pg_%'
GROUP BY t.tablename
ORDER BY policy_count ASC;

-- 检查过度宽松的策略
SELECT
  tablename,
  policyname,
  cmd,
  qual AS using_clause,
  with_check AS with_check_clause
FROM pg_policies
WHERE schemaname = 'public'
  AND (
    qual = 'true'  -- USING (true) 可能过于宽松
    OR with_check = 'true'
  )
ORDER BY tablename, policyname;
```

---

### 8.4 审计日志查询

```sql
-- 查询 RLS 策略变更历史
SELECT
  action,
  user_id,
  table_name,
  changes->>'policy_name' AS policy_changed,
  created_at
FROM audit_logs
WHERE action IN ('rls_policy_created', 'rls_policy_modified', 'rls_policy_dropped')
ORDER BY created_at DESC
LIMIT 100;

-- 查询权限拒绝事件
SELECT
  user_id,
  action,
  table_name,
  record_id,
  changes->>'error_code' AS error_code,
  created_at
FROM audit_logs
WHERE changes->>'error_code' LIKE 'AUTH_5%'
ORDER BY created_at DESC
LIMIT 50;

-- 按用户统计权限拒绝次数
SELECT
  u.email,
  u.role,
  COUNT(*) AS denial_count,
  MAX(a.created_at) AS last_denial
FROM audit_logs a
JOIN users u ON a.user_id = u.id
WHERE a.changes->>'error_code' LIKE 'AUTH_5%'
  AND a.created_at > NOW() - INTERVAL '7 days'
GROUP BY u.id, u.email, u.role
ORDER BY denial_count DESC
LIMIT 20;
```

---

## 9. 常见问题与陷阱

### 9.1 性能问题

**问题**：RLS 策略包含复杂子查询导致查询慢。

```sql
-- ❌ 性能差：每行都执行子查询
CREATE POLICY projects_select_member ON projects
FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM project_members
    WHERE project_id = projects.id
      AND user_id = auth.uid()
  )
);
```

**解决方案**：使用 IN 子查询或 CTE。

```sql
-- ✅ 性能好：使用 IN 子查询
CREATE POLICY projects_select_member_optimized ON projects
FOR SELECT
USING (
  project_id IN (
    SELECT project_id
    FROM project_members
    WHERE user_id = auth.uid()
  )
);
```

**性能优化建议**：
- 为关联字段添加索引
- 使用 Helper 函数缓存重复查询
- 避免在 RLS 策略中使用复杂 JOIN

---

### 9.2 策略重叠与权限提升风险

**问题**：多个 PERMISSIVE 策略使用 OR 逻辑组合，可能导致意外授权。

**安全风险示例**：

```sql
-- ⚠️ 风险：两个策略的 WITH CHECK 使用 OR 组合

-- 策略 1: admin/data_operator 可更新所有项目
CREATE POLICY projects_update_admin_data_operator ON projects
FOR UPDATE
USING (has_any_role(ARRAY['admin', 'data_operator']))
WITH CHECK (has_any_role(ARRAY['admin', 'data_operator']));

-- 策略 2: account_manager 可更新管理的项目
CREATE POLICY projects_update_account_manager_managed ON projects
FOR UPDATE
USING (
  has_role('account_manager')
  AND is_project_member(projects.id)
)
WITH CHECK (has_role('account_manager'));  -- ⚠️ 缺少成员验证！

-- 🚨 权限提升风险：
-- WITH CHECK = (策略1) OR (策略2)
-- account_manager 可以通过策略2更新任意项目（只要是 account_manager 角色）
```

**解决方案 1：使用 RESTRICTIVE 策略**

```sql
-- ✅ 正确：添加 RESTRICTIVE 策略强制 AND 逻辑
CREATE POLICY projects_restrictive_membership ON projects
FOR UPDATE
AS RESTRICTIVE
USING (
  has_role('admin')
  OR has_role('data_operator')
  OR (has_role('account_manager') AND is_project_member(projects.id))
);
```

**解决方案 2：合并策略**

```sql
-- ✅ 正确：合并为单个策略，逻辑清晰
DROP POLICY projects_update_admin_data_operator ON projects;
DROP POLICY projects_update_account_manager_managed ON projects;

CREATE POLICY projects_update_all_roles ON projects
FOR UPDATE
TO authenticated
USING (
  has_any_role(ARRAY['admin', 'data_operator'])
  OR (has_role('account_manager') AND is_project_member(projects.id))
)
WITH CHECK (
  has_any_role(ARRAY['admin', 'data_operator'])
  OR (has_role('account_manager') AND is_project_member(projects.id))
);
```

**策略组合规则**：

| 策略类型 | 组合逻辑 | 使用场景 |
|---------|---------|---------|
| **PERMISSIVE（默认）** | OR | 授予权限 |
| **RESTRICTIVE** | AND | 限制权限 |
| **混合使用** | `(P1 OR P2 OR ...) AND (R1 AND R2 AND ...)` | 灵活控制 |

---

### 9.3 调试技巧

```sql
-- 查看策略执行计划
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT * FROM projects WHERE id = 1;

-- 临时禁用 RLS 进行对比（仅开发环境）
SET row_security = OFF;
SELECT * FROM projects;
SET row_security = ON;

-- 查看策略评估顺序
SELECT * FROM pg_policy WHERE polrelid = 'projects'::regclass;
```

---

### 9.4 常见错误码

| 错误码 | 说明 | 原因 |
|-------|------|------|
| `42501` | insufficient_privilege | RLS 策略拒绝访问 |
| `42P01` | undefined_table | 表不存在或无权限查看 |
| `42883` | undefined_function | `auth.uid()` 未定义 |

---

## 10. 版本历史

| 版本 | 日期 | 变更内容 | 变更人 |
|------|------|---------|--------|
| v1.3 | 2025-11-20 | **⚠️ 文档定位调整**：<br>• 标记文档状态为"规划文档（未启用）"<br>• 增加"重要声明"章节说明当前数据库 RLS 未启用<br>• 明确 SoT 层级：本文档为规划级 SoT<br>• 指向 `docs/security/RLS_POLICIES.md` 作为当前实现说明<br>• 在"RLS 全局原则"章节开头增加规划性质警告<br>• 配合方案 A 执行计划（见 `docs/RLS_STRATEGY_EXEC_PLAN_A.md`） | Backend Team |
| v1.2 | 2025-11-20 | **🔧 生产优化版**：<br>• 全局替换角色判断逻辑为 Helper 函数<br>• 为所有关键策略添加业务/安全理由注释<br>• 优化 SQL 格式：统一对齐、缩进、命名<br>• 修复重复章节编号问题<br>• 改写安全警告为更严谨的技术文案<br>• 增强错误场景说明与缓解措施 | Backend Team |
| v1.1 | 2025-11-20 | **🔒 安全修复版**：<br>• [P0] 修复 users 表循环依赖（改用 JWT Claims）<br>• [P0] 移除 ad_accounts 字段级限制策略（改为应用层控制）<br>• [P1] 为 audit_logs 添加防篡改策略（明确拒绝 UPDATE/DELETE）<br>• [P1] 添加 RESTRICTIVE 策略示例防止权限提升<br>• [P2] 创建 Helper 函数库减少代码重复<br>• 新增 1.5 节安全最佳实践与检查清单<br>• 扩展 9.2 节策略重叠风险说明 | Backend Team |
| v1.0 | 2025-11-20 | 初始版本，定义所有核心表 RLS 策略 | Backend Team |

---

**文档维护规则**：
- ✅ 任何 RLS 策略变更必须先更新本文档
- ✅ 每次变更必须更新版本历史
- ✅ 每季度进行一次策略审计
- ✅ 发现文档与实际不符时，立即提交 Issue

**审计周期**：
- 日常审计：每次部署后自动运行策略审计脚本
- 月度审计：人工检查策略覆盖率和权限矩阵
- 季度审计：安全团队进行全面渗透测试

**紧急联系**：
- RLS 策略问题：Backend Team（backend@company.com）
- 安全事件：Security Team（security@company.com）
- DBA 支持：DBA Team（dba@company.com）

---

**文档结束**
