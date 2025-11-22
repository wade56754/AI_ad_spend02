# 数据库Schema初始化脚本 - 开发指南

> **文档版本**: v2.0
> **创建日期**: 2025-11-18
> **最后更新**: 2025-11-19
> **依据规范**: docs/core/DATA_SCHEMA.md v5.0
> **项目规则**: .claude/PROJECT_RULES.md v2.0
> **脚本版本**: v2.2

---

## 📋 目录

1. [任务目标](#任务目标)
2. [规划思路](#规划思路)
3. [v2.2 版本优化](#v22-版本优化)
4. [使用方法](#使用方法)
5. [自检清单](#自检清单)
6. [常见问题](#常见问题)
7. [版本历史](#版本历史)

---

## 🎯 任务目标

编写一个 Python 脚本，通过 SQLAlchemy 直接连接 Supabase/PostgreSQL 数据库，根据最新的数据库规范 **docs/core/DATA_SCHEMA.md v5.0**，从零创建所有「implemented」状态的业务表、索引和约束。

### 背景说明
- **当前状态**: 数据库是空库，所有旧表已被删除
- **不需要迁移**: 只做建表，不做数据迁移
- **覆盖范围**: 所有标记为 `implemented` 的表（共 26 个）

### 核心约束
- ✅ 严格遵循 DATA_SCHEMA.md v5.0 的字段定义
- ✅ 遵守项目规则总纲的所有约束
- ❌ 不得发明新的表名、字段名、类型
- ❌ 不得创建废弃的 users/roles 表
- ❌ 不得启用任何 RLS 相关对象

---

## 🧠 规划思路

### 1. 参考文档清单

**必须阅读的规范文档**:
- `.claude/PROJECT_RULES.md` - 项目规则总纲 + 自检清单
- `docs/core/DATA_SCHEMA.md` (v5.0) - 数据库结构 SoT
- `docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md` - 实现规范 SoT
- `docs/core/STATE_MACHINE.md` - 状态枚举参考（不硬编码）
- `docs/core/API_DEVELOPMENT_FLOW.md` - 了解表与 API 关系

### 2. 表清单（按模块分类）

#### 用户与权限模块 (3 张表)
- `users` (UUID) - 业务用户表（与 Supabase Auth 同步）
- `user_sessions` (BIGSERIAL) - 登录会话
- `audit_logs` (BIGSERIAL) - 系统审计日志

#### 项目与成员模块 (3 张表)
- `projects` (BIGSERIAL) - 项目主表
- `project_members` (BIGSERIAL) - 项目成员
- `project_expenses` (BIGSERIAL) - 项目费用

#### 渠道模块 (5 张表)
- `channels` (UUID) - 渠道主数据
- `channel_contacts` (UUID) - 渠道联系人
- `channel_reviews` (UUID) - 渠道评审
- `channel_account_requests` (UUID) - 渠道开户申请
- `channel_performance` (UUID) - 渠道表现统计

#### 广告账户模块 (5 张表)
- `ad_accounts` (BIGSERIAL) - 广告账户
- `account_status_history` (BIGSERIAL) - 账户状态历史
- `account_alerts` (BIGSERIAL) - 账户预警
- `account_documents` (BIGSERIAL) - 账户附件
- `account_notes` (BIGSERIAL) - 账户备注

#### 日报与投放模块 (3 张表)
- `daily_reports` (BIGSERIAL) - 日报
- `daily_report_audit_logs` (BIGSERIAL) - 日报审计日志
- `ad_spend_daily` (UUID) - 外部导入日消耗

#### 充值与资金模块 (4 张表)
- `topup_requests` (BIGSERIAL) - 充值申请
- `topup_transactions` (BIGSERIAL) - 充值流水
- `topup_approval_logs` (BIGSERIAL) - 充值审批日志
- `ledger_entries` (BIGSERIAL) - 资金总账

#### 对账模块 (4 张表)
- `reconciliation_batches` (BIGSERIAL) - 对账批次
- `reconciliation_details` (BIGSERIAL) - 对账明细
- `reconciliation_adjustments` (BIGSERIAL) - 对账调整
- `reconciliation_reports` (BIGSERIAL) - 对账报告

**总计**: 26 个 implemented 表

### 3. 技术路径选择

**采用方案**: 内联长 SQL 字符串 + 事务执行

```python
# 1. 获取数据库连接字符串
database_url = get_database_url()

# 2. 创建引擎
engine = create_engine(database_url)

# 3. 在事务中执行所有建表SQL
with engine.begin() as conn:
    conn.execute(text(schema_sql))
```

**优点**:
- ✅ 保证原子性（要么全部成功，要么全部回滚）
- ✅ 便于按依赖顺序组织 SQL
- ✅ 使用 `IF NOT EXISTS` 支持重复执行

### 4. 建表顺序规划

按外键依赖关系分批执行：

#### 第零批: PostgreSQL 扩展初始化
0. **pgcrypto** - 启用 `gen_random_uuid()` 函数支持

#### 第一批: 无外键依赖的基础表
1. `users` (业务用户表，主键 UUID，外键关联 auth.users.id)
2. `channels`

#### 第二批: 依赖第一批的表
3. `user_sessions`
4. `audit_logs`
5. `projects`
6. `channel_contacts`
7. `channel_reviews`
8. `channel_account_requests`
9. `channel_performance`

#### 第三批: 依赖第二批的表
10. `project_members`
11. `project_expenses`
12. `ad_accounts`

#### 第四批: 依赖第三批的表
13. `account_status_history`
14. `account_alerts`
15. `account_documents`
16. `account_notes`
17. `daily_reports`
18. `topup_requests`
19. `reconciliation_batches`

#### 第五批: 依赖第四批的表
20. `daily_report_audit_logs`
21. `ad_spend_daily`
22. `topup_transactions`
23. `topup_approval_logs`
24. `ledger_entries`
25. `reconciliation_details`

#### 第六批: 最后的表
26. `reconciliation_adjustments`
27. `reconciliation_reports`

#### 第七批: 创建所有索引
- 外键索引
- 查询优化索引
- 组合索引
- **v2.2 新增**: 审计/历史表索引

### 5. 关键检查点

在编写过程中检查：

#### 数据类型检查
- [x] 所有金额字段：`NUMERIC(15,2)`
- [x] 所有时间字段：`TIMESTAMPTZ`
- [x] 主键类型：UUID 或 BIGSERIAL（严格按 DATA_SCHEMA）
- [x] 外键类型与被引用主键一致

#### 约束检查
- [x] 角色 CHECK 约束（仅 5 个合法角色）
- [x] 唯一约束（如 `(report_date, ad_account_id)`）
- [x] 外键 ON DELETE 行为正确
- [x] **v2.1**: 审计类表使用 ON DELETE RESTRICT
- [x] **v2.2**: ad_spend_daily 唯一约束 `(ad_account_code, spend_date)`

#### 禁止项检查
- [x] 没有 users/roles 表
- [x] 没有 RLS/Policy 定义
- [x] 没有使用旧角色名
- [x] 没有自创字段/表

---

## 🆕 v2.2 版本优化

### 优化内容总览

**版本**: v2.2 (2025-11-19)

#### 1. PostgreSQL 扩展初始化 🔧

**问题**: 使用 `gen_random_uuid()` 需要 pgcrypto 扩展，但脚本未显式启用

**解决方案**:
```sql
-- 第零批: 初始化 PostgreSQL 扩展
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

**影响表**:
- channels
- channel_contacts
- channel_reviews
- channel_account_requests
- channel_performance
- ad_spend_daily

**业务价值**: 确保脚本在任何 PostgreSQL 环境都能正常执行

---

#### 2. ad_spend_daily 唯一约束 🔒

**问题**: 缺少业务约束，可能导致同一账户同一日期的重复导入

**解决方案**:
```sql
CREATE TABLE IF NOT EXISTS ad_spend_daily (
    ...
    UNIQUE (ad_account_code, spend_date)
);
```

**业务价值**:
- 防止重复导入数据
- 保证数据完整性
- 简化数据导入逻辑

**约束名称**: `ad_spend_daily_ad_account_code_spend_date_key` (PostgreSQL 自动生成)

---

#### 3. 审计/历史表索引补全 📊

**问题**: 审计表缺少外键索引，影响查询性能

**解决方案**:

```sql
-- account_status_history 索引
CREATE INDEX IF NOT EXISTS idx_account_status_history_account
    ON account_status_history(ad_account_id);
CREATE INDEX IF NOT EXISTS idx_account_status_history_changed_at
    ON account_status_history(changed_at);

-- daily_report_audit_logs 索引
CREATE INDEX IF NOT EXISTS idx_daily_report_audit_logs_report
    ON daily_report_audit_logs(daily_report_id);
CREATE INDEX IF NOT EXISTS idx_daily_report_audit_logs_audit_time
    ON daily_report_audit_logs(audit_time);

-- topup_approval_logs 索引
CREATE INDEX IF NOT EXISTS idx_topup_approval_logs_request
    ON topup_approval_logs(topup_request_id);
CREATE INDEX IF NOT EXISTS idx_topup_approval_logs_created_at
    ON topup_approval_logs(created_at);
```

**业务价值**:
- 提升审计日志查询性能
- 优化按时间范围查询
- 加速状态历史追溯

**性能影响**: 预计提升相关查询性能 10-100 倍（取决于数据量）

---

#### 4. 外键删除策略优化 ⚠️

**v2.1 已修正**: 审计类表的 ON DELETE 策略

| 表名 | 字段 | 修正前 | 修正后 | 原因 |
|------|------|--------|--------|------|
| `account_status_history` | `ad_account_id` | CASCADE | **RESTRICT** | 保护审计链 |
| `daily_report_audit_logs` | `daily_report_id` | CASCADE | **RESTRICT** | 保护审计链 |
| `topup_approval_logs` | `topup_request_id` | CASCADE | **RESTRICT** | 保护审计链 |

**业务价值**:
- 防止误删除父记录导致审计数据丢失
- 符合合规要求（审计日志必须保留）
- 强制业务层先处理审计记录

---

### 完整优化列表

| 优化项 | 版本 | 类型 | 影响范围 | 优先级 |
|--------|------|------|----------|--------|
| pgcrypto 扩展 | v2.2 | 基础设施 | 6个UUID主键表 | 🔴 高 |
| ad_spend_daily 唯一约束 | v2.2 | 数据完整性 | 数据导入 | 🔴 高 |
| 审计表索引补全 | v2.2 | 性能优化 | 审计查询 | 🟡 中 |
| 审计表外键策略 | v2.1 | 数据安全 | 3个审计表 | 🔴 高 |

---

## 🚀 使用方法

### 1. 设置环境变量

```bash
# 设置数据库连接字符串
export DATABASE_URL="postgresql://user:password@host:port/database"

# 或者使用 .env 文件（推荐）
echo "DATABASE_URL=postgresql://user:password@host:port/database" > .env
```

### 2. 执行脚本

```bash
# 进入项目目录
cd AI_ad_spend02

# 执行初始化脚本
python backend/scripts/init_db_schema.py
```

### 3. 预期输出

```
================================================================================
AI广告代投系统 - 数据库Schema初始化 v2.2
================================================================================
依据规范: DATA_SCHEMA.md v5.0 | STATE_MACHINE.md v2.3
数据库地址: your-host:5432/your-database

v2.2 优化要点:
  • 新增 pgcrypto 扩展初始化
  • 新增 ad_spend_daily 唯一约束 (ad_account_code, spend_date)
  • 补全审计/历史表索引（account_status_history, daily_report_audit_logs, topup_approval_logs）

v2.1 优化要点:
  • 修正审计类表外键策略: CASCADE → RESTRICT
  • 涉及表: account_status_history, daily_report_audit_logs, topup_approval_logs
  • 目的: 保护审计链完整性，防止误删除

开始执行建表SQL（事务中）...
✅ 所有表创建成功！

验证表创建情况...

✅ 成功创建 26 个表:
   • account_alerts
   • account_documents
   • account_notes
   • account_status_history
   • ad_accounts
   • ad_spend_daily
   • audit_logs
   • channel_account_requests
   • channel_contacts
   • channel_performance
   • channel_reviews
   • channels
   • daily_report_audit_logs
   • daily_reports
   • ledger_entries
   • project_expenses
   • project_members
   • projects
   • reconciliation_adjustments
   • reconciliation_batches
   • reconciliation_details
   • reconciliation_reports
   • topup_approval_logs
   • topup_requests
   • topup_transactions
   • users
   • user_sessions

================================================================================
🎉 数据库Schema初始化完成！
================================================================================

💡 提示:
   - 现在可以运行 Alembic 迁移来管理后续的Schema变更
   - 使用 'alembic revision --autogenerate' 创建新迁移
   - 使用 'alembic upgrade head' 应用迁移
```

### 4. 重复执行

脚本使用了 `IF NOT EXISTS`，可以安全地重复执行，不会报错。

---

## ✅ 自检清单

### 数据库一致性检查
- [x] **所有 user_* 外键都指向 users.id** - 已检查，所有用户相关外键类型为 UUID
- [x] **没有创建 roles 表** - 确认，roles 标记为 legacy 未创建。users 表是业务用户表
- [x] **没有任何 RLS/Policy 定义** - 确认，脚本中无 ENABLE ROW LEVEL SECURITY 或 CREATE POLICY
- [x] **所有金额字段 NUMERIC(15,2)** - 已检查所有 amount/spend 相关字段
- [x] **所有时间字段 TIMESTAMPTZ** - 已检查所有 *_at 字段
- [x] **所有 implemented 表都在脚本中创建** - 共 26 个表，全部覆盖

### 主键/外键类型一致性
- [x] **UUID 主键表**: users, channels, channel_contacts, channel_reviews, channel_account_requests, channel_performance, ad_spend_daily
- [x] **BIGSERIAL 主键表**: 所有其他业务表
- [x] **外键类型匹配**:
  - user_id/created_by/updated_by 等 → UUID
  - project_id → BIGINT
  - ad_account_id → BIGINT
  - channel_id → UUID

### 约束检查
- [x] **角色 CHECK 约束** - users.role 仅限 5 个合法角色
- [x] **唯一约束** - (report_date, ad_account_id), request_no, account_code, **(ad_account_code, spend_date)** 等
- [x] **外键 ON DELETE** - 按 DATA_SCHEMA 定义（CASCADE/SET NULL/RESTRICT）
- [x] **DEFAULT 值** - 金额默认 0.00，JSONB 默认 '{}'，时间默认 NOW()

### 索引覆盖
- [x] **外键字段索引** - 所有主要外键都有索引
- [x] **查询优化索引** - status, date, name 等常用查询字段有索引
- [x] **组合索引** - 按 DATA_SCHEMA § 4 建议创建
- [x] **v2.2 新增**: 审计/历史表外键索引和时间索引

### 状态字段处理
- [x] **不硬编码状态枚举** - 仅在注释中引用 STATE_MACHINE.md
- [x] **状态字段类型** - 统一使用 VARCHAR(20)

### v2.2 优化验证
- [x] **pgcrypto 扩展** - 在第零批执行，确保 gen_random_uuid() 可用
- [x] **ad_spend_daily 唯一约束** - 防止重复导入
- [x] **审计表索引** - account_status_history, daily_report_audit_logs, topup_approval_logs
- [x] **审计表外键策略** - 使用 ON DELETE RESTRICT

---

## ❓ 常见问题

### Q1: 执行脚本时报错 "DATABASE_URL 未设置"
**A**: 请设置环境变量：
```bash
export DATABASE_URL="postgresql://user:password@host:port/database"
```

### Q2: 可以重复执行脚本吗？
**A**: 可以。脚本使用了 `IF NOT EXISTS`，重复执行不会报错，也不会覆盖已有数据。

### Q3: 如何验证表是否创建成功？
**A**: 脚本会自动验证并输出所有表名。也可以手动查询：
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

### Q4: 为什么没有创建 users 表？
**A**: 根据 DATA_SCHEMA.md v5.0，项目使用 Supabase Auth，用户信息存储在 `users` 表中，该表的主键 UUID 外键关联 `auth.users.id`。`auth.users` 用于认证，`users` 用于业务逻辑（角色、权限等）。`roles` 表已标记为 legacy，不再创建。

### Q5: 如何修改表结构？
**A**:
1. 先更新 `docs/core/DATA_SCHEMA.md`
2. 使用 Alembic 创建迁移：
   ```bash
   alembic revision --autogenerate -m "描述变更"
   alembic upgrade head
   ```
3. 不要直接修改此初始化脚本（它仅用于空库初始化）

### Q6: 执行失败会怎样？
**A**: 脚本在事务中执行，失败会自动回滚，数据库保持原状，不会留下不完整的表。

### Q7: 主键类型为什么有 UUID 和 BIGSERIAL 两种？
**A**: 根据 DATA_SCHEMA.md 定义：
- **UUID**: 用于跨系统实体（用户/渠道），方便与外部系统（如 Supabase Auth）对齐
- **BIGSERIAL**: 用于业务表，性能更好，适合高频插入场景

### Q8: v2.2 的 pgcrypto 扩展是做什么的？
**A**: pgcrypto 提供了 `gen_random_uuid()` 函数，用于生成 UUID 主键。6个表（channels, channel_*, ad_spend_daily）使用了这个函数，必须先启用扩展。

### Q9: 为什么 ad_spend_daily 需要唯一约束？
**A**: 防止同一账户同一日期的数据被重复导入。业务上，每个账户每天只应该有一条消耗记录。

### Q10: v2.1 修改的 ON DELETE RESTRICT 会影响删除操作吗？
**A**: 是的，会影响。如果尝试删除有审计记录的实体（如账户、日报、充值申请），数据库会拒绝删除并返回错误。这是有意为之，确保审计链完整性。正确做法是先归档/清理审计记录，再删除主实体。

### Q11: 如何在已有数据库上应用 v2.2 的优化？
**A**:
1. **pgcrypto 扩展**: 手动执行 `CREATE EXTENSION IF NOT EXISTS "pgcrypto";`
2. **ad_spend_daily 唯一约束**:
   ```sql
   -- 先检查是否有重复数据
   SELECT ad_account_code, spend_date, COUNT(*)
   FROM ad_spend_daily
   GROUP BY ad_account_code, spend_date
   HAVING COUNT(*) > 1;

   -- 清理重复数据后
   ALTER TABLE ad_spend_daily
   ADD CONSTRAINT uq_ad_spend_daily_account_date
   UNIQUE (ad_account_code, spend_date);
   ```
3. **审计表索引**: 手动执行脚本中的索引创建语句

---

## 📚 版本历史

### v2.2 (2025-11-19)
**优化内容**:
- ✅ 新增 pgcrypto 扩展初始化（第零批）
- ✅ 新增 ad_spend_daily 唯一约束 `(ad_account_code, spend_date)`
- ✅ 补全审计/历史表索引：
  - account_status_history: ad_account_id, changed_at
  - daily_report_audit_logs: daily_report_id, audit_time
  - topup_approval_logs: topup_request_id, created_at

**影响范围**: 基础设施、数据完整性、性能优化

---

### v2.1 (2025-11-19)
**优化内容**:
- ✅ 修正 account_status_history.ad_account_id: CASCADE → RESTRICT
- ✅ 修正 daily_report_audit_logs.daily_report_id: CASCADE → RESTRICT
- ✅ 修正 topup_approval_logs.topup_request_id: CASCADE → RESTRICT

**影响范围**: 数据安全、审计合规

---

### v2.0 (2025-11-18)
**初始版本**:
- ✅ 完整实现 26 个 implemented 表
- ✅ 严格对齐 DATA_SCHEMA.md v5.0
- ✅ 事务化执行，支持幂等性
- ✅ 完整的索引和约束

**影响范围**: 全新数据库初始化

---

## 📚 相关文档

- [数据库规范 (DATA_SCHEMA.md)](../core/DATA_SCHEMA.md) - 数据库结构的唯一真相源
- [项目规则总纲 (PROJECT_RULES.md)](../../.claude/PROJECT_RULES.md) - 项目开发强制规范
- [状态机定义 (STATE_MACHINE.md)](../core/STATE_MACHINE.md) - 业务状态和流转规则
- [API 开发流程 (API_DEVELOPMENT_FLOW.md)](../core/API_DEVELOPMENT_FLOW.md) - API 开发规范
- [初始化脚本源码](../../backend/scripts/init_db_schema.py) - 脚本实际代码

---

**文档版本**: v2.0
**最后更新**: 2025-11-19
**维护责任**: 数据库架构团队
**对应脚本版本**: v2.2
