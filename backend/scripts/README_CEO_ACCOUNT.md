# 创建 CEO 账号指南

## 问题诊断

如果遇到以下错误：
- ❌ 用户不存在
- ❌ 数据库表 'users' 不存在
- ❌ 密码错误

## 解决步骤

### 步骤 1: 检查数据库状态

```bash
cd backend
python -c "from backend.core.db import get_db; from sqlalchemy import inspect; db = next(get_db()); inspector = inspect(db.bind); print('数据库表:', inspector.get_table_names())"
```

### 步骤 2: 运行数据库迁移（如果表不存在）

```bash
cd backend
# 方法1: 使用 alembic（推荐）
alembic upgrade head

# 方法2: 如果 alembic 不可用，使用 Python 模块
python -m alembic upgrade head
```

### 步骤 3: 创建或重置 CEO 账号

```bash
# 从项目根目录运行
python backend/scripts/create_or_reset_ceo.py
```

或者自定义参数：

```bash
python backend/scripts/create_or_reset_ceo.py \
  --username boss \
  --email boss@example.com \
  --password YourPassword123 \
  --role admin
```

### 步骤 4: 验证账号

```bash
# 验证密码是否正确
python backend/scripts/reset_user_password.py --email ceo@example.com --password ceo123456
```

## 默认账号信息

创建成功后的默认账号：

```
用户名: ceo
邮箱: ceo@example.com
密码: ceo123456
角色: admin
```

## 常见问题

### Q1: 数据库表不存在

**解决方案**：
1. 确保已安装所有依赖：`pip install -r requirements.txt`
2. 运行数据库迁移：`alembic upgrade head`
3. 检查数据库连接配置（`.env` 文件中的 `DATABASE_URL`）

### Q2: 密码错误

**解决方案**：
1. 使用重置密码脚本：
   ```bash
   python backend/scripts/reset_user_password.py --email ceo@example.com --password ceo123456 --reset
   ```
2. 确保使用与登录验证一致的密码哈希方法（脚本已自动处理）

### Q3: 用户不存在

**解决方案**：
1. 使用智能创建脚本（会自动检测并创建）：
   ```bash
   python backend/scripts/create_or_reset_ceo.py
   ```

## 脚本说明

### create_or_reset_ceo.py（推荐）
- ✅ 自动检测用户是否存在
- ✅ 如果不存在则创建，如果存在则重置密码
- ✅ 自动检查数据库表是否存在

### reset_user_password.py
- ✅ 重置现有用户的密码
- ✅ 验证密码是否正确

### create_ceo_user_simple.py
- ✅ 直接创建新用户（如果已存在会失败）

## 登录信息

创建成功后，使用以下信息登录：

- **邮箱/用户名**: `ceo@example.com` 或 `ceo`
- **密码**: `ceo123456`
- **角色**: `admin`（可访问 CEO 驾驶舱）

## 注意事项

1. **数据库迁移**：首次使用前必须运行 `alembic upgrade head`
2. **密码安全**：生产环境请使用强密码
3. **角色权限**：`admin` 和 `ceo` 角色都可以访问 CEO 驾驶舱

