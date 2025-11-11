# AI广告代投系统数据库结构分析与优化建议

> **版本**: v2.2 Analysis
> **分析日期**: 2025-01-11
> **分析范围**: 完整数据库结构审查

## 🔍 设计缺陷分析

### 1. 主键设计问题

#### 🚨 问题：混合使用 SERIAL 和 UUID
- `users` 表使用 UUID 主键
- 但某些关联表仍可能使用 INTEGER
- 这会导致外键引用不一致

#### 💡 优化建议：
```sql
-- 统一使用 UUID 主键
-- 所有表都使用 UUID PRIMARY KEY DEFAULT uuid_generate_v4()
-- 确保外键类型一致（都是 UUID）
```

### 2. 密码安全过度设计

#### 🚨 问题：密码存储结构冗余
```sql
password_hash VARCHAR(255) NOT NULL,
password_salt VARCHAR(32) NOT NULL DEFAULT gen_salt('bf', 12),
password_iterations INTEGER NOT NULL DEFAULT 12,
```
- bcrypt 已经内置了 salt，不需要额外存储
- `password_iterations` 对于 bcrypt 是无意义的
- 增加了存储和验证复杂度

#### 💡 优化建议：
```sql
-- 简化密码存储（使用 bcrypt）
password_hash VARCHAR(255) NOT NULL,  -- bcrypt 包含了 salt 和 rounds
last_password_change TIMESTAMPTZ,         -- 记录密码修改时间
password_reset_token TEXT,                  -- 密码重置令牌
password_reset_expires TIMESTAMPTZ           -- 重置令牌过期时间
```

### 3. 状态机设计不完整

#### 🚨 问题：缺少状态转换触发器
- 虽然有验证函数，但没有自动触发器
- 状态转换完全依赖应用层，容易出错
- 没有状态历史记录

#### 💡 优化建议：
```sql
-- 添加状态历史表
CREATE TABLE status_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID NOT NULL,
    old_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    changed_by UUID NOT NULL REFERENCES users(id),
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reason TEXT,
    metadata JSONB DEFAULT '{}'
);

-- 添加状态转换触发器
CREATE OR REPLACE FUNCTION enforce_status_transitions()
RETURNS TRIGGER AS $$
BEGIN
    -- 在这里调用相应的状态验证函数
    -- 如果验证失败，抛出异常
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### 4. 审计日志设计问题

#### 🚨 问题：审计日志不完整
- 缺少批量操作的审计
- 没有 API 调用级别的审计
- `session_id` 可能无法正确关联

#### 💡 优化建议：
```sql
-- 增强审计日志表
CREATE TABLE audit_logs (
    -- ... 现有字段 ...

    -- 新增字段
    batch_id UUID,                          -- 批量操作ID
    api_endpoint TEXT,                     -- API端点
    request_method VARCHAR(10),             -- HTTP方法
    response_status INTEGER,                -- HTTP状态码
    affected_rows INTEGER DEFAULT 0,        -- 影响的行数
    duration_ms INTEGER,                    -- 执行时间
    session_data JSONB,                     -- 会话快照
    stack_trace TEXT,                       -- 错误堆栈（如果失败）

    -- 性能相关
    query_plan JSONB                        -- 查询计划
);
```

### 5. 缺少软删除支持

#### 🚨 问题：没有软删除机制
- 数据删除后无法恢复
- 历史数据丢失
- 审计追踪中断

#### 💡 优化建议：
```sql
-- 为所有主要表添加软删除字段
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMPTZ;
ALTER TABLE projects ADD COLUMN deleted_at TIMESTAMPTZ;
ALTER TABLE ad_accounts ADD COLUMN deleted_at TIMESTAMPTZ;
-- ... 其他表

-- 创建软删除策略
CREATE POLICY soft_delete_policy ON users
    FOR UPDATE
    TO authenticated_user
    USING (id = current_user_id() OR is_superuser = true)
    WITH CHECK (
        -- 只能软删除，不能硬删除
        (deleted_at IS NOT NULL AND old_data.deleted_at IS NULL) OR
        (deleted_at IS NULL AND old_data.deleted_at IS NULL)
    );
```

### 6. 缺少数据版本控制

#### 🚨 问题：没有数据变更版本
- 无法追踪数据变更历史
- 难以实现数据恢复
- 缺少变更审批流程

#### 💡 优化建议：
```sql
-- 数据变更版本表
CREATE TABLE data_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(50) NOT NULL,
    record_id UUID NOT NULL,
    version INTEGER NOT NULL,
    operation VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    old_data JSONB,
    new_data JSONB,
    changed_by UUID NOT NULL REFERENCES users(id),
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    is_approved BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}'
);
```

### 7. 外键约束不一致

#### 🚨 问题：可选外键使用不当
- `channel_id` 是 NOT NULL，但 `project_id` 是可选的
- 业务逻辑上，广告账户应该必须属于某个项目

#### 💡 优化建议：
```sql
-- 明确业务规则
ALTER TABLE ad_accounts
ADD CONSTRAINT ad_accounts_project_required
CHECK (project_id IS NOT NULL);

-- 添加业务约束
ALTER TABLE daily_reports
ADD CONSTRAINT daily_reports_future_check
CHECK (report_date <= CURRENT_DATE + INTERVAL '1 day'); -- 允许录入今天的数据
```

### 8. 缺少分区策略

#### 🚨 问题：大表没有分区
- `audit_logs` 会快速增长
- `daily_reports` 数据量会很大
- 查询性能会随时间下降

#### 💡 优化建议：
```sql
-- 创建分区表
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    -- ... 其他字段 ...
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- 创建月度分区
CREATE TABLE audit_logs_y2024m01 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- 自动分区管理
CREATE OR REPLACE FUNCTION create_monthly_partition(table_name TEXT, start_date DATE)
RETURNS TEXT AS $$
DECLARE
    partition_name TEXT;
    end_date DATE;
BEGIN
    partition_name := table_name || '_y' || to_char(start_date, 'YYYY') || 'm' || to_char(start_date, 'MM');
    end_date := start_date + INTERVAL '1 month';

    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
                    partition_name, table_name, start_date, end_date);

    RETURN partition_name;
END;
$$ LANGUAGE plpgsql;
```

### 9. 缺少业务规则约束

#### 🚨 问题：业务规则不够严格
- 预算检查不完整
- 没有余额检查
- 缺少业务流程约束

#### 💡 优化建议：
```sql
-- 业务规则函数
CREATE OR REPLACE FUNCTION check_account_balance()
RETURNS TRIGGER AS $$
DECLARE
    current_balance DECIMAL;
    daily_budget DECIMAL;
    monthly_spend DECIMAL;
BEGIN
    -- 获取当前余额
    SELECT balance INTO current_balance
    FROM ad_accounts WHERE id = NEW.id;

    -- 获取日预算
    SELECT COALESCE(daily_budget, 0) INTO daily_budget
    FROM ad_accounts WHERE id = NEW.id;

    -- 检查余额是否足够
    IF NEW.spent > current_balance THEN
        RAISE EXCEPTION '余额不足：当前余额 %，尝试支出 %',
                     current_balance, NEW.spent;
    END IF;

    -- 检查日预算
    IF daily_budget > 0 THEN
        SELECT COALESCE(SUM(spend), 0) INTO monthly_spend
        FROM daily_reports
        WHERE account_id = NEW.id
        AND report_date = CURRENT_DATE;

        IF monthly_spend + NEW.spend > daily_budget THEN
            RAISE EXCEPTION '超出日预算：预算 %，已花费 %，尝试添加 %',
                         daily_budget, monthly_spend, NEW.spend;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 应用触发器
CREATE TRIGGER check_account_balance_trigger
    BEFORE INSERT OR UPDATE ON daily_reports
    FOR EACH ROW EXECUTE FUNCTION check_account_balance();
```

### 10. 缺少性能监控表

#### 🚨 问题：没有性能监控机制
- 无法追踪慢查询
- 缺少性能基准数据
- 没有异常检测

#### 💡 优化建议：
```sql
-- 性能监控表
CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_hash VARCHAR(64) NOT NULL,
    query_type VARCHAR(50) NOT NULL,
    table_name VARCHAR(50),
    execution_time_ms INTEGER,
    rows_examined INTEGER,
    rows_returned INTEGER,
    cpu_time_ms INTEGER,
    io_time_ms INTEGER,
    index_scans INTEGER,
    heap_scans INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(query_hash, created_at)
);

-- 自动性能监控
CREATE OR REPLACE FUNCTION log_slow_queries()
RETURNS TRIGGER AS $$
BEGIN
    IF (EXTRACT(EPOCH FROM (clock_timestamp() - statement_timestamp())) * 1000) > 1000 THEN
        INSERT INTO performance_metrics (query_hash, query_type, execution_time_ms)
        VALUES (md5(current_query()), 'SELECT',
                (EXTRACT(EPOCH FROM (clock_timestamp() - statement_timestamp())) * 1000));
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
```

## 🎯 优化优先级

### 高优先级（立即修复）
1. **统一主键类型** - 使用 UUID
2. **简化密码存储** - 移除冗余字段
3. **添加软删除支持**
4. **完善外键约束**

### 中优先级（近期优化）
1. **实现状态转换触发器**
2. **添加审计日志增强**
3. **实现数据版本控制**
4. **添加业务规则约束**

### 低优先级（长期规划）
1. **实现表分区**
2. **添加性能监控**
3. **实现自动化测试**
4. **优化查询性能**

## 📊 总体评价

### 优点
- ✅ 使用了现代的 UUID 主键
- ✅ 实现了基本的 RLS 策略
- ✅ 有完善的索引设计
- ✅ 包含了状态机验证函数
- ✅ 密码安全考虑较好

### 需要改进
- 🔧 统一数据类型设计
- 🔧 完善业务规则约束
- 🔧 增强审计功能
- 🔧 添加性能监控
- 🔧 实现数据恢复机制

### 建议
1. 先修复高优先级问题
2. 逐步实施中优先级优化
3. 持续监控和优化
4. 定期进行代码审查

这个数据库结构整体设计良好，但在细节上还有不少优化空间。建议按照优先级逐步实施改进。