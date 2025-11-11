# VS Code Supabase MCP 设置指南

## 1. 安装 VS Code 扩展

首先安装以下VS Code扩展：

### 必需扩展
- **Supabase** (Supabase官方扩展)
  - 扩展ID: `supabase.supabase`
  - 提供数据库浏览、查询、实时订阅等功能

### 可选扩展
- **PostgreSQL** (ms-ossdata.vscode-postgresql)
- **SQLTools** (mtxr.sqltools)

## 2. 连接到 Supabase 项目

### 方法1：使用连接字符串
1. 打开 VS Code
2. 按 `Ctrl+Shift+P` 打开命令面板
3. 输入 "PostgreSQL: Add Connection"
4. 选择使用连接字符串
5. 输入您的连接字符串：
   ```
   postgresql://postgres:xMw3Hx6suGGu2URV@db.jzmcoivxhiyidizncyaq.supabase.co:5432/postgres
   ```

### 方法2：使用Supabase CLI
1. 安装Supabase CLI：
   ```bash
   npm install -g supabase
   ```

2. 登录到Supabase：
   ```bash
   supabase login
   ```

3. 链接项目：
   ```bash
   supabase link --project-ref jzmcoivxhiyidizncyaq
   ```

## 3. 在VS Code中使用数据库

### 浏览数据库结构
- 安装扩展后，左侧会出现数据库图标
- 点击展开可以看到所有表
- 右键点击表可以查看数据、结构等

### 执行SQL查询
1. 按 `Ctrl+Shift+P`
2. 输入 "PostgreSQL: New Query"
3. 在新查询文件中编写SQL
4. 按 `F5` 或点击执行按钮运行

### 常用查询示例

```sql
-- 查看所有表
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public';

-- 查看用户
SELECT * FROM users WHERE role = 'admin';

-- 查看最近的审计日志
SELECT * FROM audit_logs
ORDER BY created_at DESC
LIMIT 10;

-- 创建新表
CREATE TABLE test_table (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 4. 实时功能

Supabase扩展支持实时订阅：
```sql
-- 创建实时订阅
SELECT * FROM your_table WHERE condition;
```

## 5. 代码生成

VS Code Supabase扩展可以自动生成类型定义：
1. 右键点击表
2. 选择 "Generate Types"
3. 选择目标语言（TypeScript、Python等）

## 6. 快捷键

- `Ctrl+Shift+P`: 打开命令面板
- `F5`: 执行SQL查询
- `Ctrl+/`: 注释/取消注释SQL

## 7. 故障排除

### 连接失败
- 检查密码是否正确
- 确保IP地址已加入白名单
- 验证项目ref是否正确

### 扩展未显示
- 重启VS Code
- 检查扩展是否正确安装
- 查看扩展输出日志

## 8. 替代方案：数据库客户端

如果VS Code扩展有问题，可以使用：
- **DBeaver** (免费跨平台)
- **TablePlus** (付费，界面优雅)
- **pgAdmin** (PostgreSQL官方工具)
- **Beekeeper Studio** (免费开源)

## 9. 项目连接信息

```
Host: db.jzmcoivxhiyidizncyaq.supabase.co
Port: 5432
Database: postgres
User: postgres
Password: xMw3Hx6suGGu2URV
```

## 10. 安全建议

1. 不要在代码中硬编码密码
2. 使用环境变量存储敏感信息
3. 定期更新密码
4. 限制连接IP地址

---

**提示**：您也可以使用我们之前创建的Python脚本（`scripts/database/`目录）来管理数据库。