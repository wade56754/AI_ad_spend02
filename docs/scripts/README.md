# 数据库优化脚本说明

## 概述

本目录包含了AI广告代投系统数据库优化的SQL脚本。这些脚本用于在Supabase中创建优化的数据库结构，包括表、索引、RLS策略、函数和触发器。

## 脚本列表

1. **01_optimize_database_schema.sql** - 主要的数据库结构脚本
   - 创建所有必要的表
   - 定义表结构和约束
   - 创建索引以优化查询性能
   - 创建触发器和函数
   - 插入初始数据

2. **02_create_rls_policies.sql** - RLS（行级安全）策略脚本
   - 启用表的RLS
   - 创建数据隔离策略
   - 定义基于角色的访问控制
   - 创建安全相关函数

3. **00_execute_database_optimization.sql** - 执行和验证脚本
   - 执行数据库优化
   - 验证执行结果
   - 提供后续操作指南

## 执行步骤

### 第一步：在Supabase中执行主脚本

1. 登录到您的Supabase项目
2. 进入SQL编辑器（SQL Editor）
3. 复制并执行 `01_optimize_database_schema.sql` 的内容
4. 等待脚本执行完成

### 第二步：执行RLS策略

1. 在同一个SQL编辑器中
2. 复制并执行 `02_create_rls_policies.sql` 的内容
3. 等待脚本执行完成

### 第三步：验证执行结果

1. 执行 `00_execute_database_optimization.sql` 的内容
2. 查看执行日志，确认所有组件都已正确创建
3. 记录默认管理员账号信息

## 重要提醒

### 备份数据
在执行这些脚本之前，请确保：
- 您已经备份了现有的数据库（如果有）
- 这是在开发或测试环境中执行
- 您有足够的权限执行DDL操作

### 默认账号
脚本会创建一个默认管理员账号：
- **邮箱**: admin@aiad.com
- **密码**: admin123!@#
- **角色**: admin

**重要**: 首次登录后请立即修改默认密码！

### 环境变量
执行完成后，需要在您的应用中配置以下环境变量：

```env
DATABASE_URL=your_supabase_database_url
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_KEY=your_supabase_service_key
JWT_SECRET=your_jwt_secret
```

## 数据库结构概览

### 核心表
- **users** - 用户表
- **user_profiles** - 用户配置扩展
- **sessions** - JWT会话管理
- **projects** - 项目管理
- **channels** - 渠道管理
- **ad_accounts** - 广告账户
- **project_members** - 项目成员关系
- **daily_reports** - 日报数据
- **topups** - 充值记录
- **reconciliations** - 对账记录
- **audit_logs** - 审计日志

### 安全特性
- 所有敏感数据表都启用了RLS
- 基于角色的数据访问控制
- 完整的审计日志记录
- 自动密码加密

### 性能优化
- 针对常用查询创建的索引
- 复合索引优化多条件查询
- 计算字段减少重复计算
- 分区准备（大表预留）

## 故障排除

### 如果脚本执行失败

1. 检查是否有权限错误
2. 确认Supabase项目有足够的资源
3. 查看错误日志定位具体问题
4. 可以分批执行SQL语句

### 如果RLS策略不生效

1. 确认RLS已启用
2. 检查JWT token是否正确设置
3. 验证用户角色是否正确传递
4. 查看查询计划确认策略被应用

### 如果性能问题

1. 运行 `ANALYZE` 更新统计信息
2. 检查查询是否使用了索引
3. 考虑调整数据库配置
4. 监控慢查询日志

## 联系支持

如果您在执行过程中遇到问题：
1. 查看Supabase文档
2. 检查脚本中的注释
3. 查看执行日志
4. 联系技术支持团队

---

**注意**: 这些脚本是为AI广告代投系统v2.1专门设计的，请确保在正确的环境中执行。