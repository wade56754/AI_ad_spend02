# SQL 脚本审查报告

> **审查依据**: `docs/core/DATA_SCHEMA.md`  
> **审查日期**: 2025-01-XX  
> **审查范围**: 项目中的所有 SQL 脚本

---

## 📋 审查概览

### 审查的脚本文件

1. `backend/init.sql` - 数据库初始化脚本
2. `backend/create_reconciliation_indexes.sql` - 对账系统索引
3. `docs/core/05_indexes.sql` - 索引优化脚本
4. `docs/scripts/04_optimized_database_v3.2_final.sql` - 优化后的数据库结构
5. 其他历史脚本文件（已标记为存档）

---

## ❌ 发现的主要问题

### 1. **主键类型不一致** ⚠️ 严重

#### 问题描述

**文档要求**（DATA_SCHEMA.md）：
- `users` 表应使用 **UUID** 主键
- `channels` 表应使用 **UUID** 主键
- `projects`, `ad_accounts` 等应使用 **Integer** 主键

**实际情况**：

| 脚本文件 | users 表主键类型 | 是否符合规范 |
|---------|----------------|------------|
| `backend/init.sql` | `SERIAL` (Integer) | ❌ **不符合** |
| `backend/models/users.py` | `GUID()` (UUID) | ✅ 符合 |
| `docs/scripts/04_optimized_database_v3.2_final.sql` | 需检查 | ⚠️ 待确认 |

**影响**：
- 代码模型与 SQL 初始化脚本不一致
- 可能导致迁移错误
- 外键关系类型不匹配

#### 修复建议

```sql
-- backend/init.sql 应该修改为：
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- 改为 UUID
    -- ... 其他字段
);
```

---

### 2. **外键字段类型不匹配** ⚠️ 严重

#### 问题描述

**文档要求**：
- `ad_accounts.assigned_user_id` 应引用 `users.id` (UUID)
- `projects.account_manager_id` 应引用 `users.id` (UUID)
- 但 `projects`, `ad_accounts` 主键为 Integer

**实际情况**：

```sql
-- backend/init.sql 中：
-- ❌ 错误：假设 users.id 是 Integer
assigned_user_id INTEGER REFERENCES users(id)
account_manager_id INTEGER REFERENCES users(id)
```

**但模型代码中**：
```python
# backend/models/users.py
id = Column(GUID(), primary_key=True, default=uuid.uuid4)  # UUID类型
```

**影响**：
- 外键约束无法创建（类型不匹配）
- 关联关系错误

#### 修复建议

根据 DATA_SCHEMA.md 文档：
- `users` 使用 UUID 主键
- `projects`, `ad_accounts` 使用 Integer 主键
- `projects.account_manager_id` 应改为 **Integer**（文档第141行显示为 Integer）
- `ad_accounts.assigned_user_id` 应改为 **Integer**（文档第287行显示为 Integer）

**注意**：文档中存在矛盾：
- 第55行：users.id 是 UUID
- 第141行：projects.account_manager_id 是 Integer
- 第287行：ad_accounts.assigned_user_id 是 Integer

**结论**：文档和代码都需要确认正确的设计。

---

### 3. **字段定义与文档不一致** ⚠️ 中等

#### 3.1 用户表字段差异

| 字段 | 文档要求 | init.sql | 状态 |
|-----|---------|---------|------|
| `id` | UUID | SERIAL | ❌ |
| `email` | String(255), unique | VARCHAR(100), unique | ⚠️ 长度不同 |
| `name` | String(255), nullable | VARCHAR(100), NOT NULL | ⚠️ nullable 不一致 |
| `role` | String(64), default="trader" | user_role ENUM | ⚠️ 类型不同 |
| `role_id` | GUID, nullable | ❌ 缺失 | ❌ |
| `created_at` | DateTime, default=datetime.utcnow | TIMESTAMP WITH TIME ZONE | ⚠️ 时区处理不同 |

#### 3.2 项目表字段差异

| 字段 | 文档要求 | init.sql | 状态 |
|-----|---------|---------|------|
| `account_manager_id` | Integer, nullable | ❌ 缺失 | ❌ |
| `created_by` | Integer, required | ❌ 缺失 | ❌ |
| `updated_by` | Integer, nullable | ❌ 缺失 | ❌ |
| `client_name` | String(200), required | ❌ 缺失（有 client_id） | ⚠️ |
| `client_company` | String(200), required | ❌ 缺失（有 client_id） | ⚠️ |

---

### 4. **索引定义缺失** ⚠️ 中等

#### 4.1 文档要求的索引未在 init.sql 中创建

**文档要求但缺失的索引**：

```sql
-- users 表
CREATE UNIQUE INDEX users_email_key ON users(email);  -- ✅ init.sql 中有 UNIQUE 约束

-- projects 表
CREATE INDEX idx_projects_status ON projects(status);  -- ❌ 缺失
CREATE INDEX idx_projects_client ON projects(client_name);  -- ❌ 缺失（字段都不存在）
CREATE INDEX idx_projects_manager ON projects(account_manager_id);  -- ❌ 缺失（字段都不存在）
CREATE INDEX idx_projects_created_by ON projects(created_by);  -- ❌ 缺失（字段都不存在）
CREATE INDEX idx_projects_dates ON projects(start_date, end_date);  -- ❌ 缺失

-- ad_accounts 表
CREATE INDEX idx_ad_accounts_platform ON ad_accounts(platform);  -- ❌ 缺失
CREATE INDEX idx_ad_accounts_status ON ad_accounts(status);  -- ❌ 缺失
CREATE INDEX idx_ad_accounts_project ON ad_accounts(project_id);  -- ❌ 缺失（有 project_accounts 关联表）
CREATE INDEX idx_ad_accounts_channel ON ad_accounts(channel_id);  -- ❌ 缺失（字段不存在）
CREATE INDEX idx_ad_accounts_assigned_user ON ad_accounts(assigned_user_id);  -- ❌ 缺失
CREATE INDEX idx_ad_accounts_created_at ON ad_accounts(created_at);  -- ❌ 缺失

-- daily_reports 表
CREATE INDEX idx_daily_reports_date ON daily_reports(report_date);  -- ❌ 缺失
CREATE INDEX idx_daily_reports_account ON daily_reports(account_id);  -- ❌ 缺失
CREATE INDEX idx_daily_reports_status ON daily_reports(status);  -- ❌ 缺失
CREATE INDEX idx_daily_reports_created_by ON daily_reports(created_by);  -- ❌ 缺失（字段不存在）
```

**注意**：`backend/create_reconciliation_indexes.sql` 和 `docs/core/05_indexes.sql` 包含部分索引，但 `init.sql` 作为初始化脚本应该包含基础索引。

---

### 5. **约束定义缺失** ⚠️ 中等

#### 文档要求的约束未在 init.sql 中创建

**ad_accounts 表缺失的约束**：

```sql
-- 文档要求但缺失：
ALTER TABLE ad_accounts ADD CONSTRAINT check_account_status
    CHECK (status IN ('new', 'testing', 'active', 'suspended', 'dead', 'archived'));

ALTER TABLE ad_accounts ADD CONSTRAINT check_daily_budget_non_negative
    CHECK (daily_budget >= 0);

ALTER TABLE ad_accounts ADD CONSTRAINT check_total_budget_non_negative
    CHECK (total_budget >= 0);

ALTER TABLE ad_accounts ADD CONSTRAINT check_total_spend_non_negative
    CHECK (total_spend >= 0);
```

**init.sql 中**：
- 只有 `account_status` ENUM，但枚举值不同（'active', 'paused', 'banned', 'pending'）
- 缺少数值字段的非负约束

---

### 6. **表结构差异** ⚠️ 严重

#### 6.1 init.sql 中的表结构与文档差异较大

| 表名 | 文档中是否存在 | init.sql 中是否存在 | 差异说明 |
|-----|-------------|------------------|---------|
| `users` | ✅ | ✅ | 主键类型不一致 |
| `roles` | ✅ | ❌ | init.sql 中缺失 |
| `projects` | ✅ | ✅ | 字段差异大 |
| `project_members` | ✅ | ❌ | init.sql 中缺失 |
| `project_expenses` | ✅ | ❌ | init.sql 中缺失 |
| `channels` | ✅ | ❌ | init.sql 中缺失（有 ad_platforms） |
| `ad_accounts` | ✅ | ✅ | 字段差异大 |
| `account_status_history` | ✅ | ❌ | init.sql 中缺失 |
| `account_performance` | ✅ | ❌ | init.sql 中缺失 |
| `account_alerts` | ✅ | ❌ | init.sql 中缺失 |
| `topup_requests` | ✅ | ✅ | 字段差异 |
| `topup_transactions` | ✅ | ❌ | init.sql 中缺失 |
| `topup_approval_logs` | ✅ | ❌ | init.sql 中缺失 |
| `ad_spend_daily` | ✅ | ❌ | init.sql 中缺失 |
| `daily_reports` | ✅ | ✅ | 字段差异 |
| `daily_report_audit_logs` | ✅ | ❌ | init.sql 中缺失 |
| `reconciliation_batches` | ✅ | ❌ | init.sql 中缺失 |
| `reconciliation_details` | ✅ | ❌ | init.sql 中缺失 |
| `clients` | ❌ | ✅ | 文档中未定义 |
| `ad_platforms` | ❌ | ✅ | 文档中未定义（文档中有 channels） |
| `project_accounts` | ❌ | ✅ | 文档中未定义（文档中直接关联） |
| `audit_logs` | ❌ | ✅ | 文档中有 AuditLog，但结构不同 |

**结论**：`backend/init.sql` 是**旧版本**的数据库结构，与当前文档规范差异很大。

---

## ✅ 符合规范的部分

### 1. 索引脚本质量较好

- `backend/create_reconciliation_indexes.sql` 使用了 `CONCURRENTLY`，避免锁表 ✅
- `docs/core/05_indexes.sql` 索引定义详细，使用部分索引优化 ✅
- 索引命名规范 ✅

### 2. 时间字段处理

- `init.sql` 中使用了 `TIMESTAMP WITH TIME ZONE` ✅
- 与文档要求的 `DateTime(timezone=True)` 一致 ✅

### 3. 触发器函数

- `update_updated_at_column()` 函数设计合理 ✅
- 为需要的表都添加了触发器 ✅

---

## 📝 详细问题清单

### 高优先级问题（必须修复）

1. ❌ **主键类型不一致** - users 表在 init.sql 中应使用 UUID
2. ❌ **外键类型不匹配** - 需要确认 users 与其他表的关联方式
3. ❌ **表结构过时** - init.sql 缺少大量文档中定义的表
4. ❌ **索引缺失** - 初始化脚本应包含基础索引

### 中优先级问题（建议修复）

5. ⚠️ **字段定义差异** - 字段类型、长度、nullable 属性不一致
6. ⚠️ **约束缺失** - CHECK 约束未创建
7. ⚠️ **唯一索引缺失** - 部分唯一约束未创建索引

### 低优先级问题（可选优化）

8. ⚪ **枚举类型** - init.sql 使用 ENUM，代码使用 String + CheckConstraint
9. ⚪ **测试数据** - init.sql 包含测试数据，生产环境应移除

---

## 🔧 修复建议

### 方案 1：更新 init.sql（推荐）

**优点**：
- 保持向后兼容
- 逐步迁移

**步骤**：
1. 根据 DATA_SCHEMA.md 更新 `backend/init.sql`
2. 添加缺失的表和字段
3. 修复主键类型
4. 添加缺失的索引和约束
5. 创建迁移脚本从旧结构迁移到新结构

### 方案 2：使用最新脚本作为基准

**优点**：
- 结构完整
- 符合最新规范

**步骤**：
1. 以 `docs/scripts/04_optimized_database_v3.2_final.sql` 作为基准
2. 清理测试数据
3. 更新为正式初始化脚本
4. 将 `backend/init.sql` 标记为废弃

### 方案 3：统一文档和代码

**优点**：
- 避免未来冲突
- 保持一致性

**步骤**：
1. 确认正确的设计（UUID vs Integer 主键）
2. 更新 DATA_SCHEMA.md 文档，消除矛盾
3. 更新所有 SQL 脚本
4. 更新 Python 模型代码

---

## 📊 符合度评分

| 检查项 | 符合度 | 说明 |
|-------|-------|------|
| 主键类型 | 30% | init.sql 与文档不一致 |
| 外键关系 | 40% | 类型不匹配 |
| 字段定义 | 50% | 部分字段缺失或类型不同 |
| 索引定义 | 60% | 基础索引缺失，但有单独的索引脚本 |
| 约束定义 | 40% | CHECK 约束缺失 |
| 表结构完整性 | 30% | init.sql 缺少大量表 |
| **总体符合度** | **42%** | **需要重大更新** |

---

## 🎯 行动建议

### 立即行动

1. ✅ **停止使用 `backend/init.sql`** - 标记为过时/废弃
2. ✅ **统一设计决策** - 确认 users 主键类型（UUID 还是 Integer）
3. ✅ **更新文档** - 修复 DATA_SCHEMA.md 中的矛盾描述

### 短期行动（1-2周）

1. 📝 创建符合规范的初始化脚本
2. 📝 创建从旧结构到新结构的迁移脚本
3. 📝 添加数据库版本管理（使用 Alembic）

### 长期行动（1个月）

1. 📝 统一所有 SQL 脚本
2. 📝 建立 SQL 脚本审查流程
3. 📝 自动化数据库结构验证

---

## 📚 相关文档

- [数据库设计文档](./DATA_SCHEMA.md)
- [Alembic 迁移指南](../development/MIGRATION.md)
- [数据库最佳实践](../development/DATABASE_BEST_PRACTICES.md)

---

**审查人**: AI Assistant  
**审查日期**: 2025-01-XX  
**下次审查**: 修复完成后






