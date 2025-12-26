# RLS_POLICIES_SOT.md · 行级安全策略唯一事实来源

> **版本**: v2.1 (规划版 - 当前未启用)
> **status**: planned
> **owner**: wade
> **last_reviewed**: 2025-11-27
> **发布日期**: 2025-11-22
> **文档类型**: Row Level Security (RLS) 策略的唯一真相源（SoT-RLS）
> **当前状态**: ⚠️ **规划中，当前版本未启用** - 仅应用层RBAC（Service + `@require_role`）
> **适用范围**: PostgreSQL + Supabase Auth (未来启用时)
> **规范级别**: 📘 规划参考（非强制执行）
> **维护团队**: 数据库安全架构团队

---

## 📋 目录

1. [文档定位与作用](#1-文档定位与作用)
2. [SoT仲裁规则](#2-sot仲裁规则)
3. [全局RLS设计原则](#3-全局rls设计原则)
4. [全局上下文函数SoT](#4-全局上下文函数sot)
5. [RLS核心模型](#5-rls核心模型角色×数据范围矩阵)
6. [表级策略结构模板](#6-表级策略结构模板)
7. [业务表RLS策略](#7-业务表rls策略)
8. [Ledger财务类表特殊规则](#8-ledger财务类表特殊规则)
9. [RLS测试用例SoT](#9-rls测试用例sot)
10. [性能要求](#10-性能要求)
11. [变更控制流程](#11-变更控制流程)
12. [版本历史](#12-版本历史)

---

## 1. 文档定位与作用

### 1.1 RLS_POLICIES_SOT的职责

**本文档是AI_AD_SYSTEM行级安全策略领域的规划文档**，负责定义：

- 📘 **RLS策略设计**: 所有业务表的行级访问控制策略（规划）
- 📘 **角色权限映射**: 5个角色的数据访问范围（admin/finance/data_operator/account_manager/media_buyer）
- 📘 **上下文函数**: 统一的JWT claims提取函数（`fn_current_user_id()`等）（规划）
- 📘 **安全基线**: Service层+RLS双重防护机制（规划）
- 📘 **测试规范**: RLS策略测试用例矩阵（规划）

⚠️ **当前版本实现状态**:
- ✅ **已实现**: 应用层RBAC（Service层 + `@require_role` 装饰器）
- ❌ **未实现**: 数据库层RLS（`ENABLE_RLS=false`）
- 📘 **规划中**: 本文档定义的RLS策略供未来启用时参考

### 1.2 在SoT体系中的位置

```
AI_AD_SYSTEM 文档体系
│
├─ DATA_SCHEMA.md v5.3        ← 表结构、字段定义的唯一来源
├─ AUTH_SPEC.md v2.0          ← 角色定义、权限控制的唯一来源
├─ BUSINESS_RULES.md v4.1     ← 业务规则的唯一来源
├─ STATE_MACHINE.md v2.7      ← 状态流转的唯一来源
├─ LEDGER_SOT.md v1.2         ← 账本业务逻辑的唯一来源
│
└─ RLS_POLICIES_SOT.md v2.1 (本文档) ← RLS策略的唯一来源
```

### 1.3 开发约束（当前版本）

⚠️ **当前版本（未启用RLS）开发规范**:

- ✅ **必须**使用应用层RBAC（Service层 + `@require_role` 装饰器）
- ✅ **必须**所有业务逻辑都经过Service层权限校验
- ❌ **禁止**直接绕过Service层访问数据库
- ❌ **禁止**在代码中硬编码角色权限逻辑
- 📘 **规划**未来启用RLS时，需先更新本文档，再执行SQL DDL
- 📘 **规划**启用RLS后，所有策略必须有对应的测试用例（第9章）

---

## 2. SoT仲裁规则

### 2.1 仲裁顺序（冲突优先级）

| 领域 | 唯一真相源 | 仲裁规则 | 示例 |
|-----|-----------|---------|------|
| **表结构/字段** | DATA_SCHEMA.md v5.3 | 字段名/类型/外键以DATA_SCHEMA为准 | `users.role` CHECK约束 |
| **角色定义** | AUTH_SPEC.md v2.0 | 5个角色定义以AUTH_SPEC为准 | `admin/finance/...` |
| **业务规则** | BUSINESS_RULES.md v4.1 | 权限/SOD规则以BUSINESS_RULES为准 | BR-FIN-002（职责分离） |
| **状态流转** | STATE_MACHINE.md v2.7 | 状态机逻辑以STATE_MACHINE为准 | 对账状态机、迁移状态机 |
| **RLS策略** | RLS_POLICIES_SOT.md v2.1 (本文档) | RLS策略设计以本文档为准 | `policy_users_select_self` |

### 2.2 冲突处理规则

- ✅ 如果DATA_SCHEMA与RLS_POLICIES字段定义冲突 → **以DATA_SCHEMA为准，修改RLS_POLICIES**
- ✅ 如果AUTH_SPEC与RLS_POLICIES角色定义冲突 → **以AUTH_SPEC为准，修改RLS_POLICIES**
- ✅ 如果BUSINESS_RULES与RLS_POLICIES业务规则冲突 → **以BUSINESS_RULES为准，修改RLS_POLICIES**

---

## 3. 全局RLS设计原则（规划）

⚠️ **本章节为规划内容，当前版本未启用**

### 3.1 FORCE ROW LEVEL SECURITY（规划）

**核心原则**: 未来启用时，所有业务表必须启用RLS，即使table owner也受RLS限制

```sql
-- 标准启用方式（所有业务表）（规划）
-- ALTER TABLE <table_name> ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE <table_name> FORCE ROW LEVEL SECURITY;
```

**当前状态**: `ENABLE_RLS=false`，仅应用层RBAC

**例外情况** (仅这些表不启用RLS):
- `user_sessions`: 由Supabase Auth管理
- `roles`: 历史兼容表（已废弃）

**启用状态统计**:
- **当前已启用**: 0张（RLS全局关闭）
- **规划启用**: 25张核心业务表（未来版本）
- **策略总数**: 85+

### 3.2 最小权限原则（Principle of Least Privilege）

**角色数据访问范围** (引用: AUTH_SPEC.md v2.0 第5.3节):

| 角色 | 数据访问范围 | 典型SQL过滤 |
|-----|-------------|-----------|
| `admin` | 全局无过滤 | `WHERE 1=1` |
| `finance` | 全局财务数据（充值/账本/对账） | `WHERE 1=1` |
| `data_operator` | 全局日报/账户/项目 | `WHERE 1=1` |
| `account_manager` | 仅管理的项目 | `WHERE account_manager_id = fn_current_user_id()` |
| `media_buyer` | 仅分配的账户/自己提交的日报 | `WHERE created_by = fn_current_user_id()` |

### 3.3 双重防护（Defense in Depth）

**设计理念**: Service层和RLS层分别承担不同职责

```
前端请求
    ↓
[Service层] ← 业务过滤（根据角色、业务逻辑）
    ↓
[RLS层]     ← 基线过滤（数据库级强制）
    ↓
数据库
```

**职责分工**:
- **Service层**: 复杂业务逻辑、跨表JOIN、SOD检查、审计日志
- **RLS层**: 最小权限基线、防止SQL注入、防止Service层bypass

### 3.4 统一函数封装原则

**强制约束**: 禁止在每个RLS策略中重复解析JWT

```sql
-- ✅ 正确：使用统一函数
CREATE POLICY policy_example
ON some_table FOR SELECT TO authenticated
USING (created_by = fn_current_user_id());

-- ❌ 错误：重复解析JWT
CREATE POLICY policy_example
ON some_table FOR SELECT TO authenticated
USING (created_by = auth.uid());  -- 可维护性差
```

### 3.5 策略命名规范

**标准格式**: `policy_{table}_{operation}_{scope}[_{condition}]`

**组成部分**:
1. **前缀**: 固定为 `policy_`
2. **表名**: 表名全称（如 `users`、`daily_reports`、`ledger_entries`）
3. **操作**: `select`、`insert`、`update`、`delete`
4. **范围**: `global`（全局）、`self`（本人）、`managed`（管理的）、角色缩写（`admin`、`finance`、`do`、`am`、`mb`）
5. **条件**（可选）: 特殊条件描述（如 `raw_only`、`supplier_only`）

**命名示例**:
- `policy_users_select_admin` - Admin查看所有用户
- `policy_users_select_self` - 用户查看自己
- `policy_projects_select_managed` - account_manager查看管理的项目
- `policy_daily_reports_update_mb_raw_only` - media_buyer仅可修改raw_submitted状态日报
- `policy_ledger_update_none` - 禁止任何UPDATE操作

**COMMENT规范**: 每个策略必须添加COMMENT

```sql
COMMENT ON POLICY policy_users_select_admin ON users IS
'允许admin角色查看所有用户（全局无过滤）';
```

---

## 4. 全局上下文函数SoT

### 4.1 函数列表（最小可维护集合）

**函数命名规范**: `fn_current_*`

| 函数名 | 返回类型 | 说明 | 数据源 |
|-------|---------|------|-------|
| `fn_current_user_id()` | UUID | 当前用户ID | `auth.uid()` |
| `fn_current_user_role()` | VARCHAR(20) | 当前用户业务角色 | JOIN `users.role` |
| `fn_is_admin()` | BOOLEAN | 当前用户是否为admin | `fn_current_user_role() = 'admin'` |
| `fn_is_finance()` | BOOLEAN | 当前用户是否为finance | `fn_current_user_role() = 'finance'` |

### 4.2 函数实现（SQL DDL）

```sql
-- 1. fn_current_user_id()
CREATE OR REPLACE FUNCTION fn_current_user_id()
RETURNS UUID AS $$
BEGIN
    RETURN auth.uid();  -- Supabase内置函数
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

COMMENT ON FUNCTION fn_current_user_id() IS
'获取当前登录用户的UUID（从Supabase JWT提取）';

-- 2. fn_current_user_role()
CREATE OR REPLACE FUNCTION fn_current_user_role()
RETURNS VARCHAR(20) AS $$
DECLARE
    user_role VARCHAR(20);
BEGIN
    SELECT role INTO user_role
    FROM users
    WHERE id = auth.uid();
    RETURN COALESCE(user_role, 'anonymous');
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

COMMENT ON FUNCTION fn_current_user_role() IS
'获取当前用户的业务角色（admin/finance/data_operator/account_manager/media_buyer）';

-- 3. fn_is_admin()
CREATE OR REPLACE FUNCTION fn_is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN fn_current_user_role() = 'admin';
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

COMMENT ON FUNCTION fn_is_admin() IS
'判断当前用户是否为系统管理员';

-- 4. fn_is_finance()
CREATE OR REPLACE FUNCTION fn_is_finance()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN fn_current_user_role() = 'finance';
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

COMMENT ON FUNCTION fn_is_finance() IS
'判断当前用户是否为财务';
```

### 4.3 性能优化说明

**STABLE属性**: PostgreSQL自动缓存函数结果，避免重复查询users表

---

## 5. RLS核心模型（角色×数据范围矩阵）

### 5.1 角色×数据范围总表

**引用**: AUTH_SPEC.md v2.0 第5.1节、SYSTEM_OVERVIEW.md v2.0 第6章

| 角色 | 数据范围描述 | 典型用例 |
|-----|------------|---------|
| **admin** | 全局无过滤（`WHERE 1=1`），可访问所有数据 | 运维&问题排查、数据修复 |
| **finance** | 全局账本/充值/对账可见，项目基本信息只读 | 充值审批（终审）、月度对账 |
| **data_operator** | 全局日报&趋势相关表读写，账本只读 | 审核日报、录入真实消耗 |
| **account_manager** | 仅访问自己管理的项目 | 创建项目、分配账户、发起充值 |
| **media_buyer** | 仅访问分配给自己的ad_accounts + 对应daily_reports | 提交日报、申请充值 |

### 5.2 角色×模块访问矩阵

| 模块/表 | admin | finance | data_operator | account_manager | media_buyer |
|--------|-------|---------|---------------|----------------|-------------|
| **users** | 读写全部 | 只读全部 | 只读全部 | 只读全部 | 只读自己 |
| **projects** | 读写全部 | 只读全部 | 只读全部 | 读写仅管理的 | 禁止访问 |
| **ad_accounts** | 读写全部 | 只读全部 | 读写全部 | 读写仅管理的项目下的 | 只读分配给自己的 |
| **daily_reports** | 读写全部 | 禁止访问 | 读写全部 | 只读仅管理的项目下的 | 读写仅自己创建的 |
| **topup_requests** | 读写全部 | 读写全部 | 读写全部（初审） | 读写仅管理的项目下的 | 读写仅自己申请的 |
| **ledger_entries** | 读写全部 | 读写全部 | 只读全部 | 禁止访问 | 禁止访问 |
| **reconciliation_batches** | 读写全部 | 读写全部 | 只读全部 | 禁止访问 | 禁止访问 |
| **audit_logs** | 读全部 | 禁止访问 | 禁止访问 | 禁止访问 | 禁止访问 |

---

## 6. 表级策略结构模板

### 6.1 统一模板结构

对每张表使用以下模板统一输出：

```
### 表名 (引用 DATA_SCHEMA.md)

#### 业务原则
- 1-2行业务原则描述（引用 BUSINESS_RULES.md）

#### 关键过滤字段
- 字段名1: 用途（引用 DATA_SCHEMA.md）
- 字段名2: 用途

#### 角色×操作矩阵

| 操作 | admin | finance | data_operator | account_manager | media_buyer |
|-----|-------|---------|---------------|----------------|-------------|
| SELECT | 条件 | 条件 | 条件 | 条件 | 条件 |
| INSERT | 条件 | 条件 | 条件 | 条件 | 条件 |
| UPDATE | 条件 | 条件 | 条件 | 条件 | 条件 |
| DELETE | 条件 | 条件 | 条件 | 条件 | 条件 |

#### RLS策略（精简版）

```sql
-- SELECT策略
CREATE POLICY policy_{table}_select_{scope}
ON {table} FOR SELECT TO authenticated
USING ({condition});

COMMENT ON POLICY policy_{table}_select_{scope} ON {table} IS '{说明}';

-- INSERT策略
CREATE POLICY policy_{table}_insert_{scope}
ON {table} FOR INSERT TO authenticated
WITH CHECK ({condition});

COMMENT ON POLICY policy_{table}_insert_{scope} ON {table} IS '{说明}';

-- UPDATE策略
CREATE POLICY policy_{table}_update_{scope}
ON {table} FOR UPDATE TO authenticated
USING ({condition})
WITH CHECK ({condition});

COMMENT ON POLICY policy_{table}_update_{scope} ON {table} IS '{说明}';
```

#### 必要索引（仅与RLS强相关）

```sql
CREATE INDEX IF NOT EXISTS idx_{table}_{field} ON {table}({field});
```
```

---

## 7. 业务表RLS策略

### 7.1 Table: users

#### 业务原则
- 用户可查看自己的完整信息，admin可查看所有用户
- 其他角色可查看所有用户的基本信息（敏感字段由Service层脱敏）

#### 关键过滤字段
- `id`: 用户主键UUID（引用 DATA_SCHEMA.md 3.1.1）
- `role`: 业务角色（5枚举固定值）

#### 角色×操作矩阵

| 操作 | admin | finance | data_operator | account_manager | media_buyer |
|-----|-------|---------|---------------|----------------|-------------|
| SELECT | 全局 | 全局（只读） | 全局（只读） | 全局（只读） | 仅自己 |
| INSERT | 允许 | 禁止 | 禁止 | 禁止 | 禁止 |
| UPDATE | 全局 | 仅自己 | 仅自己 | 仅自己 | 仅自己 |
| DELETE | 禁止 | 禁止 | 禁止 | 禁止 | 禁止 |

#### RLS策略

```sql
-- SELECT: admin全局查看
CREATE POLICY policy_users_select_admin
ON users FOR SELECT TO authenticated
USING (fn_is_admin());

COMMENT ON POLICY policy_users_select_admin ON users IS
'允许admin角色查看所有用户（全局无过滤）';

-- SELECT: 用户查看自己
CREATE POLICY policy_users_select_self
ON users FOR SELECT TO authenticated
USING (id = fn_current_user_id());

COMMENT ON POLICY policy_users_select_self ON users IS
'允许用户查看自己的完整信息';

-- SELECT: 所有人可查基本信息（列级过滤在Service层）
CREATE POLICY policy_users_select_basic
ON users FOR SELECT TO authenticated
USING (1=1);

COMMENT ON POLICY policy_users_select_basic ON users IS
'允许所有已认证用户查看基本用户信息（敏感字段由Service层脱敏）';

-- UPDATE: 用户修改自己
CREATE POLICY policy_users_update_self
ON users FOR UPDATE TO authenticated
USING (id = fn_current_user_id())
WITH CHECK (id = fn_current_user_id());

COMMENT ON POLICY policy_users_update_self ON users IS
'允许用户修改自己的信息';

-- UPDATE: admin修改所有用户
CREATE POLICY policy_users_update_admin
ON users FOR UPDATE TO authenticated
USING (fn_is_admin())
WITH CHECK (fn_is_admin());

COMMENT ON POLICY policy_users_update_admin ON users IS
'允许admin修改所有用户信息';

-- INSERT: 仅admin可创建用户
CREATE POLICY policy_users_insert_admin
ON users FOR INSERT TO authenticated
WITH CHECK (fn_is_admin());

COMMENT ON POLICY policy_users_insert_admin ON users IS
'仅允许admin创建新用户';
```

#### 必要索引

```sql
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
```

---

### 7.2 Table: projects

#### 业务原则
- account_manager仅可访问自己管理的项目（引用 BR-PROJ-001）
- admin/finance/data_operator可访问所有项目

#### 关键过滤字段
- `account_manager_id`: 项目管理者UUID（引用 DATA_SCHEMA.md 3.2.1）

#### 角色×操作矩阵

| 操作 | admin | finance | data_operator | account_manager | media_buyer |
|-----|-------|---------|---------------|----------------|-------------|
| SELECT | 全局 | 全局 | 全局 | 仅管理的 | 禁止 |
| INSERT | 允许 | 禁止 | 禁止 | 仅创建自己管理的 | 禁止 |
| UPDATE | 全局 | 禁止 | 禁止 | 仅管理的 | 禁止 |
| DELETE | 禁止 | 禁止 | 禁止 | 禁止 | 禁止 |

#### RLS策略

```sql
-- SELECT: 全局视野（admin/finance/data_operator）
CREATE POLICY policy_projects_select_global
ON projects FOR SELECT TO authenticated
USING (fn_current_user_role() IN ('admin', 'finance', 'data_operator'));

COMMENT ON POLICY policy_projects_select_global ON projects IS
'允许admin/finance/data_operator查看所有项目（全局视野）';

-- SELECT: account_manager仅查看管理的项目
CREATE POLICY policy_projects_select_managed
ON projects FOR SELECT TO authenticated
USING (account_manager_id = fn_current_user_id());

COMMENT ON POLICY policy_projects_select_managed ON projects IS
'允许account_manager查看自己管理的项目';

-- INSERT: account_manager创建自己管理的项目
CREATE POLICY policy_projects_insert_managed
ON projects FOR INSERT TO authenticated
WITH CHECK (
    fn_current_user_role() IN ('account_manager', 'admin')
    AND (account_manager_id = fn_current_user_id() OR fn_is_admin())
);

COMMENT ON POLICY policy_projects_insert_managed ON projects IS
'允许account_manager创建自己管理的项目，admin可创建任意项目';

-- UPDATE: 仅管理的项目可修改
CREATE POLICY policy_projects_update_managed
ON projects FOR UPDATE TO authenticated
USING (account_manager_id = fn_current_user_id() OR fn_is_admin())
WITH CHECK (account_manager_id = fn_current_user_id() OR fn_is_admin());

COMMENT ON POLICY policy_projects_update_managed ON projects IS
'允许account_manager修改自己管理的项目，admin可修改任意项目';
```

#### 必要索引

```sql
CREATE INDEX IF NOT EXISTS idx_projects_account_manager ON projects(account_manager_id);
```

---

### 7.3 Table: ad_accounts

#### 业务原则
- media_buyer仅可访问分配给自己的广告账户（引用 BR-ACCT-001）
- account_manager可访问自己管理的项目下的广告账户

#### 关键过滤字段
- `owner_id`: 账户负责人UUID（引用 DATA_SCHEMA.md 3.3.1）
- `project_id`: 关联项目UUID

#### 角色×操作矩阵

| 操作 | admin | finance | data_operator | account_manager | media_buyer |
|-----|-------|---------|---------------|----------------|-------------|
| SELECT | 全局 | 全局 | 全局 | 仅管理的项目下的 | 仅分配给自己的 |
| INSERT | 允许 | 禁止 | 允许 | 仅管理的项目下的 | 禁止 |
| UPDATE | 全局 | 禁止 | 全局 | 仅管理的项目下的 | 禁止 |
| DELETE | 禁止 | 禁止 | 禁止 | 禁止 | 禁止 |

#### RLS策略

```sql
-- SELECT: 全局视野
CREATE POLICY policy_ad_accounts_select_global
ON ad_accounts FOR SELECT TO authenticated
USING (fn_current_user_role() IN ('admin', 'finance', 'data_operator'));

COMMENT ON POLICY policy_ad_accounts_select_global ON ad_accounts IS
'允许admin/finance/data_operator查看所有广告账户';

-- SELECT: account_manager仅查看管理的项目下的账户
CREATE POLICY policy_ad_accounts_select_managed
ON ad_accounts FOR SELECT TO authenticated
USING (
    project_id IN (
        SELECT id FROM projects
        WHERE account_manager_id = fn_current_user_id()
    )
);

COMMENT ON POLICY policy_ad_accounts_select_managed ON ad_accounts IS
'允许account_manager查看自己管理的项目下的广告账户';

-- SELECT: media_buyer仅查看分配给自己的账户
CREATE POLICY policy_ad_accounts_select_self
ON ad_accounts FOR SELECT TO authenticated
USING (owner_id = fn_current_user_id());

COMMENT ON POLICY policy_ad_accounts_select_self ON ad_accounts IS
'允许media_buyer查看分配给自己的广告账户';

-- UPDATE: 根据角色过滤
CREATE POLICY policy_ad_accounts_update_managed
ON ad_accounts FOR UPDATE TO authenticated
USING (
    fn_current_user_role() IN ('admin', 'data_operator')
    OR (
        fn_current_user_role() = 'account_manager'
        AND project_id IN (
            SELECT id FROM projects
            WHERE account_manager_id = fn_current_user_id()
        )
    )
)
WITH CHECK (
    fn_current_user_role() IN ('admin', 'data_operator')
    OR (
        fn_current_user_role() = 'account_manager'
        AND project_id IN (
            SELECT id FROM projects
            WHERE account_manager_id = fn_current_user_id()
        )
    )
);

COMMENT ON POLICY policy_ad_accounts_update_managed ON ad_accounts IS
'允许admin/data_operator修改所有账户，account_manager仅可修改管理的项目下的账户';
```

#### 必要索引

```sql
CREATE INDEX IF NOT EXISTS idx_ad_accounts_project ON ad_accounts(project_id);
CREATE INDEX IF NOT EXISTS idx_ad_accounts_owner ON ad_accounts(owner_id);
```

---

### 7.4 Table: daily_reports

#### 业务原则
- media_buyer仅可访问自己创建的日报（引用 BR-RPT-001）
- data_operator/admin可访问所有日报
- finance禁止访问日报（职责分离）

#### 关键过滤字段
- `created_by`: 创建人UUID（引用 DATA_SCHEMA.md 3.3.2）
- `ad_account_id`: 关联广告账户UUID
- `status`: 日报状态（引用 STATE_MACHINE.md 第8章）

#### 角色×操作矩阵

| 操作 | admin | finance | data_operator | account_manager | media_buyer |
|-----|-------|---------|---------------|----------------|-------------|
| SELECT | 全局 | 禁止 | 全局 | 仅管理的项目下的 | 仅自己创建的 |
| INSERT | 允许 | 禁止 | 禁止 | 禁止 | 仅创建自己的 |
| UPDATE | 全局 | 禁止 | 全局 | 禁止 | 仅raw_submitted状态 |
| DELETE | 禁止 | 禁止 | 禁止 | 禁止 | 禁止 |

#### RLS策略

```sql
-- SELECT: 全局视野
CREATE POLICY policy_daily_reports_select_global
ON daily_reports FOR SELECT TO authenticated
USING (fn_current_user_role() IN ('admin', 'data_operator'));

COMMENT ON POLICY policy_daily_reports_select_global ON daily_reports IS
'允许admin/data_operator查看所有日报';

-- SELECT: account_manager仅查看管理的项目下的日报
CREATE POLICY policy_daily_reports_select_managed
ON daily_reports FOR SELECT TO authenticated
USING (
    ad_account_id IN (
        SELECT aa.id FROM ad_accounts aa
        JOIN projects p ON aa.project_id = p.id
        WHERE p.account_manager_id = fn_current_user_id()
    )
);

COMMENT ON POLICY policy_daily_reports_select_managed ON daily_reports IS
'允许account_manager查看自己管理的项目下的日报';

-- SELECT: media_buyer仅查看自己创建的日报
CREATE POLICY policy_daily_reports_select_self
ON daily_reports FOR SELECT TO authenticated
USING (created_by = fn_current_user_id());

COMMENT ON POLICY policy_daily_reports_select_self ON daily_reports IS
'允许media_buyer查看自己创建的日报';

-- INSERT: media_buyer创建日报
CREATE POLICY policy_daily_reports_insert_self
ON daily_reports FOR INSERT TO authenticated
WITH CHECK (
    created_by = fn_current_user_id()
    AND fn_current_user_role() = 'media_buyer'
);

COMMENT ON POLICY policy_daily_reports_insert_self ON daily_reports IS
'允许media_buyer创建日报（created_by必须为自己）';

-- UPDATE: media_buyer仅可修改raw_submitted状态
CREATE POLICY policy_daily_reports_update_mb_raw_only
ON daily_reports FOR UPDATE TO authenticated
USING (
    created_by = fn_current_user_id()
    AND status = 'raw_submitted'
)
WITH CHECK (
    created_by = fn_current_user_id()
    AND status = 'raw_submitted'
);

COMMENT ON POLICY policy_daily_reports_update_mb_raw_only ON daily_reports IS
'允许media_buyer修改自己创建的日报（仅限raw_submitted状态）';

-- UPDATE: data_operator/admin全局可修改
CREATE POLICY policy_daily_reports_update_global
ON daily_reports FOR UPDATE TO authenticated
USING (fn_current_user_role() IN ('admin', 'data_operator'))
WITH CHECK (fn_current_user_role() IN ('admin', 'data_operator'));

COMMENT ON POLICY policy_daily_reports_update_global ON daily_reports IS
'允许admin/data_operator修改所有日报（运营审核）';
```

#### 必要索引

```sql
CREATE INDEX IF NOT EXISTS idx_daily_reports_created_by ON daily_reports(created_by);
CREATE INDEX IF NOT EXISTS idx_daily_reports_account ON daily_reports(ad_account_id);
CREATE INDEX IF NOT EXISTS idx_daily_reports_status ON daily_reports(status);
```

---

### 7.5 Table: topup_requests

#### 业务原则
- media_buyer/account_manager可访问自己申请的充值（引用 BR-FIN-001）
- data_operator可访问所有充值（初审）
- finance可访问所有充值（终审）

#### 关键过滤字段
- `applicant_id`: 申请人UUID（引用 DATA_SCHEMA.md 3.4.1）
- `project_id`: 关联项目UUID

#### 角色×操作矩阵

| 操作 | admin | finance | data_operator | account_manager | media_buyer |
|-----|-------|---------|---------------|----------------|-------------|
| SELECT | 全局 | 全局 | 全局 | 仅管理的项目下的 | 仅自己申请的 |
| INSERT | 允许 | 禁止 | 禁止 | 允许 | 允许 |
| UPDATE | 全局 | 全局（终审） | 全局（初审） | 禁止 | 禁止 |
| DELETE | 禁止 | 禁止 | 禁止 | 禁止 | 禁止 |

#### RLS策略

```sql
-- SELECT: 全局视野
CREATE POLICY policy_topup_select_global
ON topup_requests FOR SELECT TO authenticated
USING (fn_current_user_role() IN ('admin', 'finance', 'data_operator'));

COMMENT ON POLICY policy_topup_select_global ON topup_requests IS
'允许admin/finance/data_operator查看所有充值申请';

-- SELECT: account_manager仅查看管理的项目下的充值
CREATE POLICY policy_topup_select_managed
ON topup_requests FOR SELECT TO authenticated
USING (
    project_id IN (
        SELECT id FROM projects
        WHERE account_manager_id = fn_current_user_id()
    )
);

COMMENT ON POLICY policy_topup_select_managed ON topup_requests IS
'允许account_manager查看自己管理的项目下的充值申请';

-- SELECT: media_buyer仅查看自己申请的充值
CREATE POLICY policy_topup_select_self
ON topup_requests FOR SELECT TO authenticated
USING (applicant_id = fn_current_user_id());

COMMENT ON POLICY policy_topup_select_self ON topup_requests IS
'允许media_buyer查看自己申请的充值';

-- INSERT: media_buyer/account_manager发起充值申请
CREATE POLICY policy_topup_insert_self
ON topup_requests FOR INSERT TO authenticated
WITH CHECK (
    applicant_id = fn_current_user_id()
    AND fn_current_user_role() IN ('media_buyer', 'account_manager')
);

COMMENT ON POLICY policy_topup_insert_self ON topup_requests IS
'允许media_buyer/account_manager发起充值申请';

-- UPDATE: data_operator初审
CREATE POLICY policy_topup_update_review
ON topup_requests FOR UPDATE TO authenticated
USING (fn_current_user_role() IN ('admin', 'data_operator'))
WITH CHECK (fn_current_user_role() IN ('admin', 'data_operator'));

COMMENT ON POLICY policy_topup_update_review ON topup_requests IS
'允许admin/data_operator修改充值申请（初审）';

-- UPDATE: finance终审
CREATE POLICY policy_topup_update_approve
ON topup_requests FOR UPDATE TO authenticated
USING (fn_current_user_role() IN ('admin', 'finance'))
WITH CHECK (fn_current_user_role() IN ('admin', 'finance'));

COMMENT ON POLICY policy_topup_update_approve ON topup_requests IS
'允许admin/finance修改充值申请（终审）';
```

#### 必要索引

```sql
CREATE INDEX IF NOT EXISTS idx_topup_requests_applicant ON topup_requests(applicant_id);
CREATE INDEX IF NOT EXISTS idx_topup_requests_project ON topup_requests(project_id);
CREATE INDEX IF NOT EXISTS idx_topup_requests_status ON topup_requests(status);
```

---

### 7.6 Table: audit_logs

#### 业务原则
- 完全禁止非admin访问（引用 BR-AUDIT-001）
- 禁止UPDATE/DELETE（确保审计完整性）

#### 角色×操作矩阵

| 操作 | admin | finance | data_operator | account_manager | media_buyer |
|-----|-------|---------|---------------|----------------|-------------|
| SELECT | 全局 | 禁止 | 禁止 | 禁止 | 禁止 |
| INSERT | 禁止（仅Service层） | 禁止 | 禁止 | 禁止 | 禁止 |
| UPDATE | 禁止 | 禁止 | 禁止 | 禁止 | 禁止 |
| DELETE | 禁止 | 禁止 | 禁止 | 禁止 | 禁止 |

#### RLS策略

```sql
-- SELECT: 仅admin可查询
CREATE POLICY policy_audit_logs_select_admin_only
ON audit_logs FOR SELECT TO authenticated
USING (fn_is_admin());

COMMENT ON POLICY policy_audit_logs_select_admin_only ON audit_logs IS
'仅允许admin查看审计日志';

-- INSERT: 禁止（仅由Service层INSERT）
CREATE POLICY policy_audit_logs_insert_none
ON audit_logs FOR INSERT TO authenticated
WITH CHECK (1=0);

COMMENT ON POLICY policy_audit_logs_insert_none ON audit_logs IS
'禁止通过SQL直接插入审计日志（必须通过Service层）';

-- UPDATE: 禁止
CREATE POLICY policy_audit_logs_update_none
ON audit_logs FOR UPDATE TO authenticated
USING (1=0);

COMMENT ON POLICY policy_audit_logs_update_none ON audit_logs IS
'禁止修改审计日志（确保完整性）';

-- DELETE: 禁止
CREATE POLICY policy_audit_logs_delete_none
ON audit_logs FOR DELETE TO authenticated
USING (1=0);

COMMENT ON POLICY policy_audit_logs_delete_none ON audit_logs IS
'禁止删除审计日志（确保完整性）';
```

---

## 8. Ledger财务类表特殊规则

### 8.1 双账本安全设计

**引用**: LEDGER_SOT.md v1.2、SYSTEM_OVERVIEW.md v2.0 第5章

#### PROJECT账本（项目收入账本）

**访问权限**:
- ✅ **finance/admin**: 全局可读写
- ✅ **account_manager**: 仅可读自己管理的项目账本
- ❌ **data_operator**: 禁止访问
- ❌ **media_buyer**: 禁止访问

#### SUPPLIER账本（供应商成本账本）

**访问权限**:
- ✅ **finance/admin**: 全局可读写
- ✅ **data_operator**: 仅可读（不可写）
- ❌ **account_manager**: 禁止访问
- ❌ **media_buyer**: 禁止访问

### 8.2 Table: ledger_entries

#### 业务原则
- 禁止UPDATE/DELETE，修正必须通过红冲机制（引用 LEDGER_SOT.md 4.3）
- finance全局可读写，data_operator仅可读SUPPLIER账本

#### 关键过滤字段
- `ledger_type`: 账本类型（PROJECT/SUPPLIER）（引用 DATA_SCHEMA.md 3.4.4）
- `project_id`: 关联项目UUID（仅PROJECT账本）
- `supplier_id`: 关联供应商ID（仅SUPPLIER账本）

#### 角色×操作矩阵

| 操作 | admin | finance | data_operator | account_manager | media_buyer |
|-----|-------|---------|---------------|----------------|-------------|
| SELECT | 全局 | 全局 | 仅SUPPLIER账本 | 仅管理的PROJECT账本 | 禁止 |
| INSERT | 允许 | 允许 | 禁止 | 禁止 | 禁止 |
| UPDATE | 禁止 | 禁止 | 禁止 | 禁止 | 禁止 |
| DELETE | 禁止 | 禁止 | 禁止 | 禁止 | 禁止 |

#### RLS策略

```sql
-- SELECT: finance/admin全局查看
CREATE POLICY policy_ledger_select_global
ON ledger_entries FOR SELECT TO authenticated
USING (fn_current_user_role() IN ('admin', 'finance'));

COMMENT ON POLICY policy_ledger_select_global ON ledger_entries IS
'允许admin/finance查看所有账本记录';

-- SELECT: data_operator仅可读SUPPLIER账本
CREATE POLICY policy_ledger_select_do_supplier_only
ON ledger_entries FOR SELECT TO authenticated
USING (
    fn_current_user_role() = 'data_operator'
    AND ledger_type = 'SUPPLIER'
);

COMMENT ON POLICY policy_ledger_select_do_supplier_only ON ledger_entries IS
'允许data_operator查看SUPPLIER账本（只读，不可查看PROJECT账本）';

-- SELECT: account_manager仅可读管理的PROJECT账本
CREATE POLICY policy_ledger_select_am_project_only
ON ledger_entries FOR SELECT TO authenticated
USING (
    fn_current_user_role() = 'account_manager'
    AND ledger_type = 'PROJECT'
    AND project_id IN (
        SELECT id FROM projects
        WHERE account_manager_id = fn_current_user_id()
    )
);

COMMENT ON POLICY policy_ledger_select_am_project_only ON ledger_entries IS
'允许account_manager查看管理的项目的PROJECT账本（只读）';

-- INSERT: 仅finance/admin可创建账本记录
CREATE POLICY policy_ledger_insert_finance
ON ledger_entries FOR INSERT TO authenticated
WITH CHECK (fn_current_user_role() IN ('admin', 'finance'));

COMMENT ON POLICY policy_ledger_insert_finance ON ledger_entries IS
'仅允许admin/finance创建账本记录';

-- UPDATE: 禁止（修正必须通过红冲）
CREATE POLICY policy_ledger_update_none
ON ledger_entries FOR UPDATE TO authenticated
USING (1=0);

COMMENT ON POLICY policy_ledger_update_none ON ledger_entries IS
'禁止UPDATE账本记录（修正必须通过红冲机制）';

-- DELETE: 禁止
CREATE POLICY policy_ledger_delete_none
ON ledger_entries FOR DELETE TO authenticated
USING (1=0);

COMMENT ON POLICY policy_ledger_delete_none ON ledger_entries IS
'禁止DELETE账本记录（确保审计完整性）';
```

#### 必要索引

```sql
CREATE INDEX IF NOT EXISTS idx_ledger_type ON ledger_entries(ledger_type);
CREATE INDEX IF NOT EXISTS idx_ledger_project ON ledger_entries(project_id);
CREATE INDEX IF NOT EXISTS idx_ledger_supplier ON ledger_entries(supplier_id);
```

---

## 9. RLS测试用例SoT

### 9.1 核心测试用例（12条）

| 测试ID | 角色 | 表 | 操作 | 期望结果 | 优先级 | 说明 |
|--------|------|-------|-----------|-----------------|-------|------|
| RLS-001 | media_buyer | daily_reports | SELECT | 仅看到created_by=自己的记录 | P0 | 基础隔离 |
| RLS-002 | media_buyer | daily_reports | SELECT | 看不到其他media_buyer的记录 | P0 | 横向隔离 |
| RLS-003 | account_manager | projects | SELECT | 仅看到account_manager_id=自己的项目 | P0 | 基础隔离 |
| RLS-004 | account_manager | daily_reports | SELECT | 看到所有管理项目下的日报 | P0 | 跨表JOIN过滤 |
| RLS-005 | data_operator | ledger_entries | SELECT | 看到所有SUPPLIER账本记录 | P0 | 账本隔离 |
| RLS-006 | data_operator | ledger_entries | INSERT | ❌ 禁止 | P0 | 仅finance可写 |
| RLS-007 | finance | topup_requests | SELECT | 看到所有充值记录 | P0 | 全局视野 |
| RLS-008 | admin | * | SELECT | 看到所有记录 | P0 | 全局无过滤 |
| RLS-009 | media_buyer | daily_reports | UPDATE | 仅raw_submitted状态可修改 | P0 | 状态保护 |
| RLS-010 | account_manager | users | SELECT (last_login_ip) | NULL（非本人） | P1 | Service层脱敏 |
| RLS-011 | data_operator | audit_logs | SELECT | ❌ 禁止访问 | P0 | 仅admin可查 |
| RLS-012 | finance | ledger_entries | UPDATE | ❌ 禁止 | P0 | 禁止UPDATE（红冲机制） |

### 9.2 测试执行方式

**方法1: 使用Supabase客户端模拟JWT**

```sql
-- 设置JWT claims（模拟media_buyer登录）
SET request.jwt.claims = '{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "role": "authenticated"
}'::json;

-- 查询daily_reports（应该只看到自己创建的）
SELECT * FROM daily_reports;
```

**方法2: 使用真实Supabase Auth登录**

```bash
# 使用JWT查询API（RLS自动生效）
curl https://your-project.supabase.co/rest/v1/daily_reports \
  -H "apikey: your-anon-key" \
  -H "Authorization: Bearer <access_token>"
```

---

## 10. 性能要求

### 10.1 必要索引（仅与RLS强相关）

**支持角色过滤的索引**:

```sql
-- 支持account_manager过滤
CREATE INDEX IF NOT EXISTS idx_projects_account_manager ON projects(account_manager_id);
CREATE INDEX IF NOT EXISTS idx_ad_accounts_project ON ad_accounts(project_id);

-- 支持media_buyer过滤
CREATE INDEX IF NOT EXISTS idx_ad_accounts_owner ON ad_accounts(owner_id);
CREATE INDEX IF NOT EXISTS idx_daily_reports_created_by ON daily_reports(created_by);
CREATE INDEX IF NOT EXISTS idx_topup_requests_applicant ON topup_requests(applicant_id);

-- 支持JOIN查询
CREATE INDEX IF NOT EXISTS idx_daily_reports_account ON daily_reports(ad_account_id);
CREATE INDEX IF NOT EXISTS idx_topup_requests_project ON topup_requests(project_id);

-- 支持Ledger过滤
CREATE INDEX IF NOT EXISTS idx_ledger_type ON ledger_entries(ledger_type);
CREATE INDEX IF NOT EXISTS idx_ledger_project ON ledger_entries(project_id);
CREATE INDEX IF NOT EXISTS idx_ledger_supplier ON ledger_entries(supplier_id);
```

### 10.2 性能优化策略

**上下文函数缓存**: 使用`STABLE`函数属性（PostgreSQL自动缓存）

```sql
-- ✅ 已优化：使用STABLE属性
CREATE OR REPLACE FUNCTION fn_current_user_role()
RETURNS VARCHAR(20) AS $$
DECLARE
    user_role VARCHAR(20);
BEGIN
    SELECT role INTO user_role
    FROM users
    WHERE id = auth.uid();
    RETURN COALESCE(user_role, 'anonymous');
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;  -- STABLE自动缓存
```

**性能指标**:
- account_manager查询100条日报: <100ms
- data_operator查询10000条日报: <500ms
- 并发100个media_buyer查询各自日报: TPS >200

---

## 11. 变更控制流程

### 11.1 RLS变更流程

**强制规则**: 所有RLS策略变更必须先更新本文档，再执行SQL DDL

**变更步骤**:
1. **Step 1**: 在本文档中添加/修改RLS策略定义
2. **Step 2**: 在对应章节添加COMMENT规范
3. **Step 3**: 在第9章添加测试用例
4. **Step 4**: 在第10章添加必要索引（如需要）
5. **Step 5**: 生成SQL DDL脚本
6. **Step 6**: 在开发环境测试验证
7. **Step 7**: 提交PR（包含文档更新+SQL脚本）
8. **Step 8**: PR Review通过后合并
9. **Step 9**: 在生产环境执行SQL DDL

### 11.2 禁止行为

- ❌ **禁止**在SQL中编写"临时策略"而不更新本文档
- ❌ **禁止**在生产环境直接执行DDL而不经过PR Review
- ❌ **禁止**修改RLS策略而不添加对应测试用例

---

## 12. 版本历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2025-01-22 | **初始版本**<br>- 定义12张核心表的RLS策略<br>- 建立上下文函数标准（fn_current_*）<br>- 创建测试矩阵（30+测试用例）<br>- 定义双账本RLS策略 | 数据库安全架构团队 |
| v1.1 | 2025-01-22 | **优化版**<br>- 新增"策略命名规范"章节<br>- 新增"全表RLS启用清单"章节<br>- 增强策略COMMENT注释示例 | 数据库安全架构团队 |
| v2.0 | 2025-01-22 | **正式上线版**<br>- 🔄 重构文档结构为SoT标准结构<br>- ✅ 统一"表级策略结构模板"<br>- ✅ 精简上下文函数到最小可维护集合<br>- ✅ 精简测试用例到12条核心用例<br>- ✅ 抽象全局RLS设计原则<br>- ✅ 建立变更控制流程<br>- ✅ 所有策略使用统一命名风格<br>- ✅ 保持所有业务规则和访问权限不变 | 数据库安全架构团队 |

---

**文档状态**: ✅ 正式上线版 - RLS策略完整定义（v2.0）
**维护责任**: 数据库安全架构团队
**下次审查**: 每季度或重大安全变更时
**反馈渠道**: 提交Issue或PR到 `./` 目录

---

**END OF DOCUMENT**
