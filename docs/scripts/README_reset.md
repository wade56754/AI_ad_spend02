# 数据库重置指南

## ⚠️ 重要警告

**此操作将永久删除所有现有数据！**
**请在执行前确保您已经备份了需要保留的数据！**

## 📋 重置步骤

### 第1步：备份现有数据（如果需要）

如果您有重要数据需要保留，请先备份：

```sql
-- 备份用户数据
SELECT * FROM users;

-- 备份项目数据
SELECT * FROM projects;

-- 备份其他重要表...
```

### 第2步：执行重置脚本

1. **登录Supabase控制台**
   - 访问 [supabase.com](https://supabase.com)
   - 选择您的项目：`jzmcoivxhiyidizncyaq`

2. **打开SQL编辑器**
   - 左侧菜单 → SQL Editor → New query

3. **复制并执行重置脚本**
   - 复制 `03_reset_database.sql` 的全部内容
   - 粘贴到SQL编辑器
   - 点击 **Run** 执行

### 第3步：验证重置结果

执行完成后，脚本会显示：
- 操作日志（每一步的执行状态）
- 新创建的表列表
- 默认管理员账号信息

### 第4步：测试登录

使用以下账号登录系统：
- **邮箱**: admin@aiad.com
- **密码**: admin123!@#
- **用户名**: admin

## 📊 重置后的数据库结构

### 核心表（11个）

1. **users** - 用户表
   - 完整的用户信息
   - 角色权限管理
   - 邮箱和用户名唯一索引

2. **user_profiles** - 用户配置扩展
   - 部门、职位等信息
   - 时区、语言偏好
   - 自定义设置

3. **sessions** - 会话管理
   - JWT会话存储
   - 过期时间管理

4. **projects** - 项目管理
   - 项目信息、预算
   - 客户信息
   - 状态管理

5. **channels** - 渠道管理
   - 广告渠道信息
   - 预算设置
   - 负责人管理

6. **ad_accounts** - 广告账户
   - 账户信息
   - 余额和消耗
   - 分配关系

7. **project_members** - 项目成员
   - 项目成员关系
   - 角色权限

8. **daily_reports** - 日报数据
   - 广告数据
   - 自动计算指标（CPM、CPC、CTR等）
   - 审核流程

9. **topups** - 充值记录
   - 充值申请流程
   - 多级审批

10. **reconciliations** - 对账记录
    - 财务对账
    - 金额核对

11. **audit_logs** - 审计日志
    - 操作记录
    - 数据追踪

### 特性

- ✅ **30+个索引** 优化查询性能
- ✅ **计算字段** 自动计算CPM、CPC、CTR等
- ✅ **触发器** 自动更新时间戳
- ✅ **约束** 保证数据完整性
- ✅ **视图** 简化复杂查询
- ✅ **安全函数** 密码加密验证

## 🔧 后续配置

### 1. 更新应用配置

在您的应用 `.env.local` 文件中：

```env
NEXT_PUBLIC_SUPABASE_URL=https://jzmcoivxhiyidizncyaq.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### 2. 配置RLS策略（可选）

如果需要行级安全，可以执行 `02_create_rls_policies.sql`

### 3. 创建初始数据

```sql
-- 创建测试项目
INSERT INTO projects (name, client_name, owner_id, created_by, updated_by)
SELECT '测试项目', '测试客户', id, id, id FROM users WHERE username = 'admin';

-- 创建测试渠道
INSERT INTO channels (name, platform, account_id, created_by, updated_by)
SELECT 'Facebook Ads', 'facebook', 'fb_001', id, id FROM users WHERE username = 'admin';

-- 创建测试账户
INSERT INTO ad_accounts (account_id, name, platform, channel_id, created_by, updated_by)
SELECT 'acc_001', '测试账户', 'facebook', c.id, u.id, u.id
FROM channels c, users u
WHERE c.platform = 'facebook' AND u.username = 'admin';
```

## 🚨 注意事项

1. **不可撤销**：一旦执行，数据无法恢复
2. **权限要求**：需要足够的数据库权限
3. **执行时间**：根据数据量，可能需要几分钟
4. **依赖关系**：脚本会自动处理表的删除顺序

## 📞 如果遇到问题

1. **权限错误**：确保使用service_role密钥
2. **超时错误**：可以分批执行脚本
3. **部分失败**：查看操作日志定位问题

---

**执行前请确认您已备份重要数据！**