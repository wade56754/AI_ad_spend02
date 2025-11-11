# 数据库修复指南

> **版本**: v1.0
> **更新日期**: 2025-11-11
> **说明**: 本指南说明如何执行数据库设计修复脚本

---

## 📋 修复内容总览

本次修复解决了以下严重问题：

### ✅ 已修复的问题

1. **主键类型统一** - audit_logs表主键从BIGSERIAL改为UUID
2. **外键约束完善** - 添加了ON DELETE策略
3. **业务约束添加** - 日期逻辑、金额验证等CHECK约束
4. **余额更新优化** - 使用事务和锁确保一致性
5. **字段类型统一** - 统一金额字段精度为NUMERIC(15,2)
6. **枚举类型实现** - 提高类型安全性
7. **索引优化** - 添加关键复合索引和部分索引
8. **RLS策略优化** - 简化复杂查询，提高性能
9. **分区表实现** - 为大数据量表实现分区
10. **数据验证函数** - 完善数据完整性检查

---

## 🔧 执行步骤

### 步骤 1: 数据库备份

**⚠️ 重要：执行任何修改前必须备份数据库！**

```bash
# 备份当前数据库
pg_dump -h localhost -U postgres -d ad_spend_system \
    --format=custom \
    --compress=9 \
    --verbose \
    --file="backup_before_fix_$(date +%Y%m%d_%H%M%S).dump"

# 验证备份文件
pg_restore --list backup_before_fix_*.dump > /dev/null
```

### 步骤 2: 执行基础修复脚本

```bash
# 连接到数据库
psql -h localhost -U postgres -d ad_spend_system

# 执行基础修复脚本
\i scripts/fix_database_schema.sql

# 检查是否有错误
SELECT * FROM validate_data_integrity();
```

### 步骤 3: 执行RLS优化（可选）

```sql
-- 执行RLS优化脚本
\i scripts/optimize_rls_policies.sql

-- 测试权限
SELECT * FROM test_user_permissions('user_uuid', 'media_buyer');
```

### 步骤 4: 实现分区表（可选，用于大数据量）

```sql
-- 创建分区表结构
\i scripts/create_partitioned_tables.sql

-- 迁移数据（如果原表有数据）
SELECT migrate_to_partitioned_table();

-- 验证数据迁移
SELECT COUNT(*) FROM ad_spend_daily;
SELECT COUNT(*) FROM ad_spend_daily_backup;

-- 切换到分区表
SELECT backup_original_table();
```

### 步骤 5: 后续优化

```sql
-- 更新表统计信息
ANALYZE;

-- 重建索引（如果需要）
REINDEX DATABASE ad_spend_system;

-- 设置自动分区维护
SELECT maintain_partitions();
```

---

## 📊 验证检查

### 验证外键约束

```sql
-- 检查所有外键约束
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    tc.delete_rule
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
```

### 验证索引

```sql
-- 检查新增的索引
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('ad_accounts', 'topups', 'ad_spend_daily', 'projects')
ORDER BY tablename, indexname;
```

### 验证RLS策略

```sql
-- 检查RLS策略
SELECT * FROM rls_performance_stats;

-- 检查RLS审计
SELECT * FROM rls_audit_log ORDER BY timestamp DESC LIMIT 10;
```

### 验证分区表

```sql
-- 检查分区状态
SELECT * FROM partition_status;

-- 检查分区统计
SELECT * FROM partition_statistics;
```

---

## 🚨 注意事项

### 执行前检查

1. **确认数据库版本**: PostgreSQL 12+
2. **确认权限**: 需要superuser权限
3. **检查连接池**: 建议在维护窗口执行
4. **确认备份**: 必须有有效备份

### 可能的问题

1. **外键约束冲突**:
   - 如果现有数据违反新的外键约束，需要先清理数据
   - 解决方法：更新或删除无效数据

2. **CHECK约束冲突**:
   - 现有数据可能违反新的CHECK约束
   - 解决方法：使用`ALTER TABLE ... VALIDATE CONSTRAINT`逐步验证

3. **性能影响**:
   - 首次执行可能较慢
   - 建议在低峰期执行

### 回滚方案

如果需要回滚：

```bash
# 停止应用
sudo systemctl stop your-app

# 恢复备份
dropdb -h localhost -U postgres ad_spend_system
createdb -h localhost -U postgres ad_spend_system
pg_restore -h localhost -U postgres -d ad_spend_system backup_before_fix_*.dump

# 重启应用
sudo systemctl start your-app
```

---

## 📈 性能优化建议

### 查询优化

1. **使用分区查询**:
   ```sql
   -- 查询特定月份数据
   SELECT * FROM ad_spend_daily
   WHERE date >= '2025-01-01' AND date < '2025-02-01';
   ```

2. **利用索引**:
   ```sql
   -- 确保查询使用索引
   EXPLAIN SELECT * FROM ad_accounts
   WHERE project_id = 'uuid' AND status = 'active';
   ```

### 定期维护

```sql
-- 定期更新统计信息
ANALYZE;

-- 清理无用数据
VACUUM ad_spend_daily;

-- 重建索引（如果碎片化严重）
REINDEX INDEX CONCURRENTLY idx_ad_accounts_project_status;
```

---

## 📞 故障处理

### 常见错误

1. **权限错误**:
   ```
   ERROR: permission denied for relation ...
   ```
   解决：确保使用正确的用户执行

2. **约束错误**:
   ```
   ERROR: new row for relation "..." violates check constraint ...
   ```
   解决：检查数据并更新或删除冲突记录

3. **锁等待超时**:
   ```
   ERROR: canceling statement due to lock timeout
   ```
   解决：检查是否有长时间运行的事务

### 联系支持

如果遇到无法解决的问题：
1. 保存错误信息
2. 记录执行步骤
3. 联系数据库管理员

---

**文档版本**: v1.0
**最后更新**: 2025-11-11
**执行人**: 数据库管理员
**审核人**: 系统架构师