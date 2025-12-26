# Layer 1: 安全约束（Security Constraints）

> **约束级别**: MUST（不可违反）
> **违反处理**: 立即拒绝，必须修复后才能继续
> **优先级**: 最高（高于 Layer 2 和 Layer 3）

---

## 概述

Layer 1 安全约束是最高优先级的约束，任何违反都必须立即修复。这些约束旨在防止常见的安全漏洞，保护系统免受攻击。

### 5 大安全类别

1. **SQL 注入** - 防止数据库查询注入攻击
2. **XSS 防护** - 防止跨站脚本攻击
3. **硬编码密钥** - 防止敏感信息泄露
4. **不安全加密** - 确保使用安全的加密算法
5. **命令注入** - 防止操作系统命令注入

---

## 1. SQL 注入（SQL Injection）

### 规则定义

**禁止**: 拼接用户输入到 SQL 字符串中
**要求**: 使用参数化查询或 ORM

### 检测规则

#### Python (SQLAlchemy / Raw SQL)

**❌ 禁止模式**:
```python
# 模式 1: f-string 拼接
query = f"SELECT * FROM users WHERE id = {user_id}"
session.execute(query)

# 模式 2: % 格式化
query = "SELECT * FROM users WHERE name = '%s'" % user_name
session.execute(query)

# 模式 3: + 拼接
query = "SELECT * FROM users WHERE email = '" + user_email + "'"
session.execute(query)

# 模式 4: .format() 拼接
query = "SELECT * FROM users WHERE id = {}".format(user_id)
session.execute(query)
```

**✅ 正确做法**:
```python
# 方法 1: SQLAlchemy ORM (推荐)
user = session.query(User).filter(User.id == user_id).first()

# 方法 2: SQLAlchemy Core 参数化
from sqlalchemy import text
stmt = text("SELECT * FROM users WHERE id = :user_id")
session.execute(stmt, {"user_id": user_id})

# 方法 3: 原生 SQL 参数化（使用 psycopg2）
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

#### JavaScript/TypeScript (Prisma / Raw SQL)

**❌ 禁止模式**:
```typescript
// 模式 1: 模板字符串拼接
const query = `SELECT * FROM users WHERE id = ${userId}`;
await prisma.$queryRawUnsafe(query);

// 模式 2: + 拼接
const query = "SELECT * FROM users WHERE name = '" + userName + "'";
await db.raw(query);
```

**✅ 正确做法**:
```typescript
// 方法 1: Prisma ORM (推荐)
const user = await prisma.user.findUnique({
  where: { id: userId }
});

// 方法 2: Prisma 参数化查询
const users = await prisma.$queryRaw`
  SELECT * FROM users WHERE id = ${userId}
`;

// 方法 3: Knex.js 参数化
const users = await knex('users')
  .where('id', userId)
  .select('*');
```

### 风险等级

**Critical** - SQL 注入可导致：
- 数据库完全泄露
- 数据篡改或删除
- 系统权限提升
- 后续攻击的跳板

### 修复建议

1. **使用 ORM** (SQLAlchemy, Prisma, Django ORM) - 推荐
2. **参数化查询** (text() with bind params, $queryRaw)
3. **输入验证** - 作为额外防护层（不能单独依赖）
4. **最小权限原则** - 数据库用户仅授予必要权限

---

## 2. XSS 防护（Cross-Site Scripting Protection）

### 规则定义

**禁止**: 未转义的用户输入直接插入 HTML
**要求**: 使用模板引擎自动转义或手动转义

### 检测规则

#### JavaScript/TypeScript (React / Vue / Vanilla JS)

**❌ 禁止模式**:
```javascript
// 模式 1: innerHTML 直接赋值
element.innerHTML = userInput;

// 模式 2: document.write
document.write("<div>" + userInput + "</div>");

// 模式 3: jQuery html()
$('#content').html(userInput);

// 模式 4: React dangerouslySetInnerHTML（未经消毒）
<div dangerouslySetInnerHTML={{__html: userInput}} />
```

**✅ 正确做法**:
```javascript
// 方法 1: textContent (推荐，自动转义)
element.textContent = userInput;

// 方法 2: React 默认转义
<div>{userInput}</div>

// 方法 3: DOMPurify 消毒 HTML（如果必须使用 HTML）
import DOMPurify from 'dompurify';
const clean = DOMPurify.sanitize(userInput);
element.innerHTML = clean;

// 方法 4: React 使用 DOMPurify
import DOMPurify from 'dompurify';
const clean = DOMPurify.sanitize(userInput);
<div dangerouslySetInnerHTML={{__html: clean}} />
```

#### Python (Jinja2 / FastAPI Templates)

**❌ 禁止模式**:
```python
# 模式 1: 关闭自动转义
{{ user_input | safe }}

# 模式 2: 手动拼接 HTML（未转义）
html = f"<div>{user_input}</div>"
```

**✅ 正确做法**:
```python
# 方法 1: Jinja2 自动转义（默认行为，推荐）
{{ user_input }}

# 方法 2: 手动转义（如果不用模板）
from markupsafe import escape
html = f"<div>{escape(user_input)}</div>"
```

### 风险等级

**High** - XSS 攻击可导致：
- 会话劫持（窃取 Cookie/Token）
- 钓鱼攻击（伪造表单）
- 恶意脚本执行
- 用户数据窃取

### 修复建议

1. **使用框架默认转义** (React, Vue, Jinja2) - 推荐
2. **textContent 替代 innerHTML** - 对于纯文本
3. **DOMPurify 消毒** - 对于必须支持 HTML 的场景
4. **CSP (Content Security Policy)** - 额外防护层

---

## 3. 硬编码密钥（Hardcoded Credentials）

### 规则定义

**禁止**: 在代码中硬编码密钥、密码、API Token
**要求**: 使用环境变量或密钥管理服务

### 检测规则

#### 通用检测模式

**❌ 禁止模式**:
```python
# Python
API_KEY = "sk-1234567890abcdef"
DATABASE_URL = "postgresql://user:password@localhost/db"
SECRET_KEY = "my-secret-key-12345"
JWT_SECRET = "super-secret-jwt-key"
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"

# JavaScript/TypeScript
const apiKey = "sk-1234567890abcdef";
const dbPassword = "my-database-password";
const githubToken = "ghp_1234567890abcdef";
```

**✅ 正确做法**:
```python
# Python - 使用环境变量
import os
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable not set")

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")

# JavaScript/TypeScript - 使用环境变量
const apiKey = process.env.API_KEY;
if (!apiKey) {
  throw new Error("API_KEY environment variable not set");
}

const dbPassword = process.env.DB_PASSWORD;
```

#### 特殊场景：公开密钥

**允许（但需注释说明）**:
```python
# ✅ 公开的 API 密钥（非敏感信息）
# QUALITY_ASSISTANT_IGNORE: public key
PUBLIC_API_KEY = "pk-1234567890"  # 公开的 Stripe 测试密钥

# ✅ 示例/测试密钥（带明确标注）
EXAMPLE_KEY = "example-key-for-documentation"  # 仅用于文档示例
```

### 检测正则表达式

```regex
# API 密钥模式
sk-[a-zA-Z0-9]{32,}
api[_-]?key\s*=\s*["'][^"']{8,}["']

# 密码模式
password\s*=\s*["'][^"']{6,}["']
pwd\s*=\s*["'][^"']{6,}["']

# AWS 密钥模式
AKIA[0-9A-Z]{16}

# GitHub Token 模式
ghp_[a-zA-Z0-9]{36}
```

### 风险等级

**Critical** - 硬编码密钥可导致：
- 完全的系统访问权限
- 数据泄露
- 财务损失（云服务滥用）
- 第三方服务滥用

### 修复建议

1. **使用环境变量** (.env 文件，不提交到 Git) - 推荐
2. **密钥管理服务** (AWS Secrets Manager, HashiCorp Vault)
3. **配置文件** (config.yaml，添加到 .gitignore)
4. **检查 Git 历史** - 如果已提交，需要轮换密钥

---

## 4. 不安全加密（Unsafe Encryption）

### 规则定义

**禁止**: 使用 MD5、SHA1 等弱加密算法哈希密码
**要求**: 使用 bcrypt、argon2、scrypt 等专用密码哈希算法

### 检测规则

#### Python

**❌ 禁止模式**:
```python
# 模式 1: MD5 哈希密码
import hashlib
password_hash = hashlib.md5(password.encode()).hexdigest()

# 模式 2: SHA1 哈希密码
password_hash = hashlib.sha1(password.encode()).hexdigest()

# 模式 3: SHA256 不加盐
password_hash = hashlib.sha256(password.encode()).hexdigest()
```

**✅ 正确做法**:
```python
# 方法 1: bcrypt (推荐)
import bcrypt

# 哈希密码
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# 验证密码
is_valid = bcrypt.checkpw(password.encode(), password_hash)

# 方法 2: argon2 (更安全，推荐用于高安全场景)
from argon2 import PasswordHasher
ph = PasswordHasher()

# 哈希密码
password_hash = ph.hash(password)

# 验证密码
try:
    ph.verify(password_hash, password)
    is_valid = True
except:
    is_valid = False
```

#### JavaScript/TypeScript

**❌ 禁止模式**:
```javascript
// 模式 1: crypto.createHash('md5')
const crypto = require('crypto');
const hash = crypto.createHash('md5').update(password).digest('hex');

// 模式 2: SHA1
const hash = crypto.createHash('sha1').update(password).digest('hex');
```

**✅ 正确做法**:
```javascript
// 方法 1: bcrypt (推荐)
const bcrypt = require('bcryptjs');

// 哈希密码
const hash = await bcrypt.hash(password, 10);

// 验证密码
const isValid = await bcrypt.compare(password, hash);

// 方法 2: argon2
const argon2 = require('argon2');

// 哈希密码
const hash = await argon2.hash(password);

// 验证密码
const isValid = await argon2.verify(hash, password);
```

### 允许的 MD5/SHA1 使用场景

**✅ 允许（非密码场景）**:
```python
# 文件完整性校验（MD5/SHA256 可用）
file_hash = hashlib.md5(file_content).hexdigest()

# Git commit hash（SHA1 可用）
commit_hash = hashlib.sha1(content.encode()).hexdigest()

# ETag 生成（MD5 可用）
etag = hashlib.md5(response_body.encode()).hexdigest()
```

### 风险等级

**Critical** - 不安全加密可导致：
- 密码被彩虹表破解
- 暴力破解成本极低
- 数据库泄露后所有密码被破解

### 修复建议

1. **bcrypt** - 适用于大多数场景（推荐）
2. **argon2** - 适用于高安全场景（推荐）
3. **scrypt** - 适用于特定合规要求
4. **轮换密钥** - 如果已使用 MD5/SHA1，需强制用户重置密码

---

## 5. 命令注入（Command Injection）

### 规则定义

**禁止**: 拼接用户输入到 shell 命令中
**要求**: 使用参数化 API 或白名单验证

### 检测规则

#### Python

**❌ 禁止模式**:
```python
# 模式 1: os.system 拼接
import os
os.system(f"rm {filename}")

# 模式 2: subprocess.run shell=True 拼接
import subprocess
subprocess.run(f"cat {filename}", shell=True)

# 模式 3: eval/exec 用户输入
eval(user_code)
exec(user_script)
```

**✅ 正确做法**:
```python
# 方法 1: subprocess 参数化（推荐）
import subprocess
subprocess.run(["rm", filename])

# 方法 2: 白名单验证
import re
if not re.match(r'^[a-zA-Z0-9_.-]+$', filename):
    raise ValueError("Invalid filename")
subprocess.run(["rm", filename])

# 方法 3: shlex.quote 转义（如果必须使用 shell）
import shlex
import subprocess
subprocess.run(f"rm {shlex.quote(filename)}", shell=True)

# 方法 4: 使用专用库替代命令
import os
os.remove(filename)  # 代替 rm 命令
```

#### JavaScript/TypeScript

**❌ 禁止模式**:
```javascript
// 模式 1: child_process.exec 拼接
const { exec } = require('child_process');
exec(`rm ${filename}`);

// 模式 2: child_process.spawn shell=true 拼接
const { spawn } = require('child_process');
spawn(`cat ${filename}`, { shell: true });

// 模式 3: eval 用户输入
eval(userCode);
```

**✅ 正确做法**:
```javascript
// 方法 1: child_process.execFile 参数化（推荐）
const { execFile } = require('child_process');
execFile('rm', [filename]);

// 方法 2: child_process.spawn 参数化
const { spawn } = require('child_process');
spawn('rm', [filename]);

// 方法 3: 白名单验证
const path = require('path');
const fs = require('fs');

if (!/^[a-zA-Z0-9_.-]+$/.test(filename)) {
  throw new Error('Invalid filename');
}
fs.unlinkSync(filename);  // 使用 Node.js API 代替命令
```

### 风险等级

**Critical** - 命令注入可导致：
- 任意代码执行
- 服务器完全控制
- 数据泄露或破坏
- 横向移动攻击

### 修复建议

1. **使用参数化 API** (subprocess.run([]), execFile()) - 推荐
2. **白名单验证** - 严格限制允许的字符
3. **避免 shell=True** - 除非绝对必要
4. **使用专用库** - 用 os.remove() 代替 rm 命令

---

## 违反处理流程

### 1. 检测到违反

当检测到 Layer 1 安全约束违反时：

```markdown
❌ **[Critical] 安全约束违反**

**类型**: SQL 注入
**位置**: backend/services/user_service.py:42
**问题代码**:
```python
query = f"SELECT * FROM users WHERE id = {user_id}"
session.execute(query)
```

**风险等级**: Critical
**风险描述**: 用户可通过构造恶意 user_id 执行任意 SQL 命令，可能导致数据库完全泄露。

**修复建议**:
```python
# 使用 SQLAlchemy ORM（推荐）
user = session.query(User).filter(User.id == user_id).first()

# 或使用参数化查询
from sqlalchemy import text
stmt = text("SELECT * FROM users WHERE id = :user_id")
session.execute(stmt, {"user_id": user_id})
```

**必须修复**: 是
**允许忽略**: 否（Layer 1 约束不可违反）
```

### 2. 拒绝代码

- **立即停止**: 不生成包含安全漏洞的代码
- **强制修复**: 要求用户修复后再继续
- **记录日志**: 记录违反的类型和位置

### 3. 例外处理

**极少数情况下**，如果确实需要违反约束（如安全测试、教育目的），必须：

1. **明确标注**:
   ```python
   # SECURITY_WARNING: Intentional SQL injection for testing
   # DO NOT USE IN PRODUCTION
   query = f"SELECT * FROM users WHERE id = {user_id}"
   ```

2. **隔离环境**: 确保代码仅在测试环境运行
3. **文档说明**: 在代码和文档中明确说明原因

---

## 检测工具集成

### Python

**推荐工具**:
- **bandit** - 静态安全检查
- **safety** - 依赖漏洞扫描
- **pylint** - 代码质量检查（包含部分安全规则）

```bash
# 安装
pip install bandit safety pylint

# 运行检查
bandit -r backend/
safety check
pylint backend/
```

### JavaScript/TypeScript

**推荐工具**:
- **eslint-plugin-security** - ESLint 安全插件
- **npm audit** - 依赖漏洞扫描
- **snyk** - 综合安全扫描

```bash
# 安装
npm install --save-dev eslint-plugin-security

# 运行检查
npm audit
npx eslint --plugin security frontend/
```

---

## 总结

### Layer 1 安全约束清单

| 安全类别 | 禁止行为 | 要求行为 | 风险等级 |
|---------|---------|---------|---------|
| SQL 注入 | 拼接 SQL 字符串 | 参数化查询/ORM | Critical |
| XSS 防护 | 未转义 HTML 输出 | 自动转义/DOMPurify | High |
| 硬编码密钥 | 密钥/密码/token | 环境变量/密钥服务 | Critical |
| 不安全加密 | MD5/SHA1 哈希密码 | bcrypt/argon2 | Critical |
| 命令注入 | 拼接 shell 命令 | 参数化 API/白名单 | Critical |

### 成功标准

- ✅ 检测准确率 ≥ 95%
- ✅ 误报率 ≤ 5%
- ✅ 所有 Critical 问题必须修复
- ✅ 所有 High 问题强烈建议修复

---

**版本**: v1.0
**最后更新**: 2025-12-22
**维护者**: wade
