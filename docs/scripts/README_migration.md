# 数据库迁移指南

## 问题分析

您的数据库中缺少 `username` 字段，这是因为现有的 `users` 表结构与我们的优化脚本不兼容。

## 解决方案

我已经创建了一个安全的迁移脚本 `02_safe_migration.sql`，它能够：

1. **智能检测**现有表结构
2. **安全添加**缺失的字段
3. **保留现有数据**
4. **创建新表**（如果不存在）
5. **自动处理**冲突

## 执行步骤

### 第1步：执行迁移脚本

1. 在Supabase SQL编辑器中打开新查询
2. 复制 `02_safe_migration.sql` 的全部内容
3. 粘贴并执行

### 第2步：验证结果

执行以下查询验证迁移是否成功：

```sql
-- 查看users表结构
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users' AND table_schema = 'public'
ORDER BY ordinal_position;

-- 查看所有表
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- 检查管理员用户
SELECT id, email, username, role, is_superuser
FROM users
WHERE role = 'admin' OR is_superuser = true;
```

### 第3步：测试登录

1. 使用管理员账号登录：
   - 邮箱: admin@aiad.com
   - 密码: admin123!@#

## 脚本特性

### 安全特性
- ✅ 使用 `IF NOT EXISTS` 避免重复创建
- ✅ 检查现有字段再添加
- ✅ 自动生成唯一的username（如果缺失）
- ✅ 保留所有现有数据

### 智能处理
- ✅ 检测现有管理员用户并更新
- ✅ 自动创建必要的索引
- ✅ 创建触发器和函数
- ✅ 提供详细的执行日志

## 常见问题

### Q: 如果已经有admin用户怎么办？
A: 脚本会自动检测并更新现有admin用户，保留其数据。

### Q: 如果某些字段已存在怎么办？
A: 脚本会跳过已存在的字段，继续创建缺失的。

### Q: 迁移失败怎么办？
A: 查看诊断结果，脚本会显示每一步的执行状态。

### Q: 需要手动做什么吗？
A: 不需要，脚本会自动处理所有必要的更改。

## 迁移后的操作

1. **验证数据完整性**
   ```sql
   -- 检查用户数据
   SELECT COUNT(*) as user_count FROM users;

   -- 检查是否有未设置username的用户
   SELECT COUNT(*) as missing_username FROM users WHERE username IS NULL;
   ```

2. **更新应用配置**
   确保您的应用使用正确的字段名。

3. **备份记录**
   记录迁移时间，以备将来参考。

## 注意事项

- 脚本执行时间取决于数据量
- 建议在低峰期执行
- 执行前请确保有数据库备份
- 如果有自定义字段，请提前告知

---

**如果仍有问题，请提供：**
1. 具体的错误信息
2. 现有的表结构
3. 需要保留的特殊字段