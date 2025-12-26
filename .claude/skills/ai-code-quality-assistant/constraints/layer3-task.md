# Layer 3: 任务约束（Task Constraints）

> **约束级别**: MAY（根据场景决定）
> **违反处理**: 提示但不强制，由用户决定
> **优先级**: 最低（低于 Layer 1 和 Layer 2）

---

## 概述

Layer 3 任务约束关注代码的文档完整性、扩展性和兼容性。这些约束是可选的，根据项目需求和场景决定是否应用。违反不会产生警告，仅作为改进建议。

### 3 大任务类别

1. **文档完整性** - docstring、README、使用示例
2. **扩展性** - 设计模式、配置分离、依赖注入
3. **兼容性** - 版本要求、跨平台处理、向后兼容

---

## 1. 文档完整性（Documentation Completeness）

### 规则定义

**建议**: 为复杂函数提供 docstring，为公共 API 提供使用示例，在 README 中说明项目结构
**目标**: 提高代码可理解性，降低新成员上手成本

### 检测规则

#### 1.1 函数 Docstring

**❌ 缺少 Docstring**:
```python
# Python
def calculate_compound_interest(principal, rate, years):
    return principal * (1 + rate) ** years

# 复杂逻辑但没有说明
def process_payment(order, payment_method, discount_code):
    # 50+ 行复杂逻辑
    pass
```

**✅ 提供 Docstring**:
```python
# Python
def calculate_compound_interest(principal: float, rate: float, years: int) -> float:
    """计算复利。

    Args:
        principal: 本金
        rate: 年利率（小数形式，如 0.05 表示 5%）
        years: 投资年限

    Returns:
        最终金额（本金 + 利息）

    Examples:
        >>> calculate_compound_interest(1000, 0.05, 10)
        1628.89

    Raises:
        ValueError: 如果 rate 或 years 为负数
    """
    if rate < 0 or years < 0:
        raise ValueError("Rate and years must be non-negative")
    return principal * (1 + rate) ** years
```

**JavaScript/TypeScript**:
```typescript
/**
 * 计算复利
 * @param principal - 本金
 * @param rate - 年利率（小数形式，如 0.05 表示 5%）
 * @param years - 投资年限
 * @returns 最终金额（本金 + 利息）
 * @throws {Error} 如果 rate 或 years 为负数
 * @example
 * calculateCompoundInterest(1000, 0.05, 10); // 1628.89
 */
function calculateCompoundInterest(
    principal: number,
    rate: number,
    years: number
): number {
    if (rate < 0 || years < 0) {
        throw new Error("Rate and years must be non-negative");
    }
    return principal * Math.pow(1 + rate, years);
}
```

#### 何时需要 Docstring

**必须提供** (复杂逻辑):
- 公共 API 函数
- 超过 20 行的函数
- 包含复杂算法的函数
- 有副作用的函数
- 参数 > 3 个的函数

**可选** (简单逻辑):
- 单行函数
- getter/setter
- 私有辅助函数
- 明显的业务逻辑

---

#### 1.2 README 文档

**❌ 缺少 README**:
```
project/
├── src/
└── tests/
# 没有 README.md
```

**✅ 提供完整 README**:
````markdown
# 项目名称

> 简短描述项目用途

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 运行

```bash
python main.py
```

## 项目结构

```
project/
├── src/
│   ├── models/      # 数据模型
│   ├── services/    # 业务逻辑
│   └── utils/       # 工具函数
└── tests/           # 测试文件
```

## 使用示例

```python
from src.services import UserService

service = UserService()
user = service.get_user(123)
print(user.name)
```

## 配置

创建 `.env` 文件：

```env
DATABASE_URL=postgresql://localhost/mydb
API_KEY=your-api-key
```

## 测试

```bash
pytest tests/
```

## 许可证

MIT
````

---

#### 1.3 使用示例

**❌ 缺少使用示例**:
```python
# 提供 API 但没有示例
class PaymentProcessor:
    def process(self, order, payment_method):
        pass
```

**✅ 提供使用示例**:
```python
class PaymentProcessor:
    """支付处理器。

    Examples:
        基本用法:
        >>> processor = PaymentProcessor(api_key="sk-123")
        >>> result = processor.process(
        ...     order=Order(total=100),
        ...     payment_method="credit_card"
        ... )
        >>> print(result.status)
        'success'

        处理失败:
        >>> try:
        ...     processor.process(order, "invalid_method")
        ... except ValueError as e:
        ...     print(e)
        'Invalid payment method'
    """
    def process(self, order, payment_method):
        pass
```

**JavaScript/TypeScript - 在 README 中提供示例**:
```typescript
/**
 * # PaymentProcessor
 *
 * Process payments using various payment methods.
 *
 * @example
 * Basic usage:
 * ```typescript
 * const processor = new PaymentProcessor({ apiKey: 'sk-123' });
 * const result = await processor.process({
 *     order: { total: 100 },
 *     paymentMethod: 'credit_card'
 * });
 * console.log(result.status); // 'success'
 * ```
 *
 * @example
 * Handling errors:
 * ```typescript
 * try {
 *     await processor.process(order, 'invalid_method');
 * } catch (error) {
 *     console.error(error.message); // 'Invalid payment method'
 * }
 * ```
 */
class PaymentProcessor {
    process(order, paymentMethod) {}
}
```

### 风险等级

**Low** - 文档缺失可导致：
- 新成员上手慢
- API 误用
- 维护成本增加
- 代码重复实现

### 修复建议

1. **为公共 API 提供 docstring** - 必须
2. **为复杂函数提供 docstring** - 强烈推荐
3. **提供 README** - 项目级必须
4. **提供使用示例** - 公共 API 强烈推荐

---

## 2. 扩展性（Extensibility）

### 规则定义

**建议**: 适度使用设计模式，配置与代码分离，支持依赖注入
**目标**: 提高代码可扩展性，便于未来修改和扩展

### 检测规则

#### 2.1 配置硬编码

**❌ 配置硬编码**:
```python
# Python
def send_email(to, subject, body):
    smtp_host = "smtp.gmail.com"  # 硬编码
    smtp_port = 587  # 硬编码
    max_retries = 3  # 硬编码

    # 发送邮件逻辑
    pass
```

**✅ 配置分离**:
```python
# config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    max_retries: int = 3

    class Config:
        env_file = ".env"

settings = Settings()

# email_service.py
from config import settings

def send_email(to, subject, body):
    smtp_host = settings.smtp_host
    smtp_port = settings.smtp_port
    max_retries = settings.max_retries

    # 发送邮件逻辑
    pass
```

**JavaScript/TypeScript**:
```typescript
// config.ts
export const config = {
    smtpHost: process.env.SMTP_HOST || 'smtp.gmail.com',
    smtpPort: parseInt(process.env.SMTP_PORT || '587'),
    maxRetries: parseInt(process.env.MAX_RETRIES || '3')
};

// email-service.ts
import { config } from './config';

function sendEmail(to: string, subject: string, body: string) {
    const { smtpHost, smtpPort, maxRetries } = config;
    // 发送邮件逻辑
}
```

---

#### 2.2 设计模式

**❌ 无设计模式（复杂场景）**:
```python
# 多种通知方式，没有统一抽象
def send_notification(user, message, method):
    if method == "email":
        # 发送邮件逻辑
        pass
    elif method == "sms":
        # 发送短信逻辑
        pass
    elif method == "push":
        # 发送推送逻辑
        pass
    # 添加新方式需要修改此函数
```

**✅ 使用策略模式**:
```python
# 策略模式 - 易于扩展
from abc import ABC, abstractmethod

class NotificationStrategy(ABC):
    @abstractmethod
    def send(self, user, message):
        pass

class EmailNotification(NotificationStrategy):
    def send(self, user, message):
        # 发送邮件逻辑
        pass

class SMSNotification(NotificationStrategy):
    def send(self, user, message):
        # 发送短信逻辑
        pass

class PushNotification(NotificationStrategy):
    def send(self, user, message):
        # 发送推送逻辑
        pass

class NotificationService:
    def __init__(self, strategy: NotificationStrategy):
        self.strategy = strategy

    def notify(self, user, message):
        self.strategy.send(user, message)

# 使用
service = NotificationService(EmailNotification())
service.notify(user, "Hello")

# 添加新方式只需实现新策略，无需修改现有代码
```

**JavaScript/TypeScript**:
```typescript
interface NotificationStrategy {
    send(user: User, message: string): Promise<void>;
}

class EmailNotification implements NotificationStrategy {
    async send(user: User, message: string) {
        // 发送邮件逻辑
    }
}

class SMSNotification implements NotificationStrategy {
    async send(user: User, message: string) {
        // 发送短信逻辑
    }
}

class NotificationService {
    constructor(private strategy: NotificationStrategy) {}

    async notify(user: User, message: string) {
        await this.strategy.send(user, message);
    }
}

// 使用
const service = new NotificationService(new EmailNotification());
await service.notify(user, "Hello");
```

#### 常用设计模式

| 模式 | 适用场景 | 示例 |
|------|---------|------|
| 策略模式 | 多种算法/方式选择 | 支付方式、通知方式 |
| 工厂模式 | 对象创建复杂 | 创建不同类型的用户 |
| 单例模式 | 全局唯一实例 | 数据库连接池 |
| 装饰器模式 | 动态添加功能 | 缓存、日志、权限 |
| 观察者模式 | 事件通知 | 状态变化通知 |

---

#### 2.3 依赖注入

**❌ 硬编码依赖**:
```python
class OrderService:
    def create_order(self, order_data):
        # 硬编码依赖
        db = Database()
        email_service = EmailService()

        order = db.save(order_data)
        email_service.send(order.user, "Order created")
        return order
```

**✅ 依赖注入**:
```python
class OrderService:
    def __init__(self, db: Database, email_service: EmailService):
        self.db = db
        self.email_service = email_service

    def create_order(self, order_data):
        order = self.db.save(order_data)
        self.email_service.send(order.user, "Order created")
        return order

# 使用（手动注入）
db = Database()
email_service = EmailService()
order_service = OrderService(db, email_service)

# 使用（FastAPI 自动注入）
from fastapi import Depends

def get_db():
    return Database()

def get_email_service():
    return EmailService()

@app.post("/orders")
def create_order(
    order_data: OrderCreate,
    db: Database = Depends(get_db),
    email_service: EmailService = Depends(get_email_service)
):
    service = OrderService(db, email_service)
    return service.create_order(order_data)
```

### 风险等级

**Low** - 扩展性差可导致：
- 修改成本高
- 添加功能困难
- 代码重复
- 测试困难

### 修复建议

1. **配置分离** - 使用 .env 或配置文件
2. **设计模式** - 适度使用（避免过度设计）
3. **依赖注入** - 提高可测试性和灵活性
4. **SOLID 原则** - 单一职责、开闭原则

---

## 3. 兼容性（Compatibility）

### 规则定义

**建议**: 说明最低版本要求，处理跨平台差异，提供向后兼容性
**目标**: 确保代码在不同环境下正常运行

### 检测规则

#### 3.1 版本要求

**❌ 缺少版本说明**:
```python
# requirements.txt
fastapi
sqlalchemy
pydantic
# 没有指定版本
```

**✅ 明确版本要求**:
```python
# requirements.txt
fastapi>=0.100.0,<1.0.0
sqlalchemy>=2.0.0,<3.0.0
pydantic>=2.0.0,<3.0.0

# Python 版本要求（pyproject.toml）
[tool.poetry]
name = "my-project"
version = "1.0.0"
description = ""
python = "^3.10"  # 最低 Python 3.10

# package.json
{
  "engines": {
    "node": ">=18.0.0",
    "npm": ">=9.0.0"
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0"
  }
}
```

---

#### 3.2 跨平台处理

**❌ 平台相关代码**:
```python
# 硬编码路径分隔符（仅 Unix）
file_path = "/home/user/data.txt"

# 使用 Unix 特定命令
os.system("rm -rf /tmp/cache")

# JavaScript - 硬编码路径
const filePath = 'C:\\Users\\user\\data.txt';  // 仅 Windows
```

**✅ 跨平台兼容**:
```python
# Python - 使用 pathlib
from pathlib import Path

file_path = Path.home() / "data.txt"  # 跨平台
cache_dir = Path("/tmp") / "cache"  # 自动处理路径分隔符

# 使用跨平台 API
import shutil
shutil.rmtree(cache_dir)  # 代替 rm -rf

# JavaScript/TypeScript - 使用 path 模块
import path from 'path';
import os from 'os';

const filePath = path.join(os.homedir(), 'data.txt');  // 跨平台
const cacheDir = path.join(os.tmpdir(), 'cache');
```

---

#### 3.3 向后兼容

**❌ 破坏性变更（无过渡期）**:
```python
# v1.0 - 旧版本
def get_user(user_id):
    return {"id": user_id, "name": "John"}

# v2.0 - 直接删除参数（破坏性变更）
def get_user():  # 删除 user_id 参数
    return {"id": 1, "name": "John"}
```

**✅ 提供向后兼容**:
```python
# v2.0 - 保留向后兼容
import warnings

def get_user(user_id=None):  # 参数变为可选
    if user_id is not None:
        warnings.warn(
            "user_id parameter is deprecated and will be removed in v3.0. "
            "Use get_user_by_id(user_id) instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return get_user_by_id(user_id)

    # 新逻辑
    return get_current_user()

def get_user_by_id(user_id):
    return {"id": user_id, "name": "John"}

# v3.0 - 移除已弃用参数
def get_user():
    return get_current_user()

def get_user_by_id(user_id):
    return {"id": user_id, "name": "John"}
```

**JavaScript/TypeScript**:
```typescript
/**
 * @deprecated Use getUserById(userId) instead. Will be removed in v3.0.
 */
function getUser(userId?: number): User {
    if (userId !== undefined) {
        console.warn(
            'getUser(userId) is deprecated. Use getUserById(userId) instead.'
        );
        return getUserById(userId);
    }
    return getCurrentUser();
}

function getUserById(userId: number): User {
    return { id: userId, name: 'John' };
}
```

### 风险等级

**Low** - 兼容性问题可导致：
- 部署失败
- 平台特定 Bug
- 用户升级困难
- 依赖冲突

### 修复建议

1. **明确版本要求** - requirements.txt, package.json
2. **使用跨平台 API** - pathlib, path 模块
3. **提供过渡期** - 弃用警告，至少 1-2 个版本
4. **文档说明** - CHANGELOG 中标注破坏性变更

---

## 违反处理流程

### 1. 检测到违反

当检测到 Layer 3 任务约束违反时：

```markdown
💡 **[Low] 任务约束建议**

**类别**: 文档完整性
**位置**: backend/services/payment_service.py:42
**问题**:
```python
def process_payment(order, payment_method, discount_code):
    # 50+ 行复杂逻辑，但没有 docstring
    pass
```

**改进建议**:
```python
def process_payment(order: Order, payment_method: str, discount_code: str = None) -> PaymentResult:
    """处理支付。

    Args:
        order: 订单对象
        payment_method: 支付方式（"credit_card", "paypal", "alipay"）
        discount_code: 优惠码（可选）

    Returns:
        PaymentResult 对象，包含支付状态和交易 ID

    Raises:
        ValueError: 如果 payment_method 不支持
        PaymentError: 如果支付失败

    Examples:
        >>> result = process_payment(order, "credit_card")
        >>> print(result.status)
        'success'
    """
    # 50+ 行复杂逻辑
    pass
```

**影响**: 低（文档缺失）
**建议修复**: 是（提高可维护性）
**允许忽略**: 是（不影响功能）
```

### 2. 提示但不警告

- **生成代码**: 继续生成代码，不产生警告
- **记录建议**: 在报告中记录改进建议
- **由用户决定**: 用户自行决定是否采纳

### 3. 完全可选

用户可以完全忽略 Layer 3 建议：

```bash
# 仅检查 Layer 1 和 Layer 2
/code-quality check --layer=1,2 backend/services/payment_service.py

# 或明确忽略 Layer 3
/code-quality check --skip-documentation backend/
```

---

## 总结

### Layer 3 任务约束清单

| 任务类别 | 检查项 | 风险等级 | 是否阻断 |
|---------|--------|---------|---------|
| 文档完整性 | docstring、README、示例 | Low | 否 |
| 扩展性 | 设计模式、配置分离、依赖注入 | Low | 否 |
| 兼容性 | 版本要求、跨平台、向后兼容 | Low | 否 |

### 适用场景

**应用 Layer 3** (推荐):
- 公共库/SDK 开发
- 长期维护的项目
- 团队协作项目
- 开源项目

**可忽略 Layer 3** (可接受):
- 原型开发
- 一次性脚本
- 内部工具（仅自己使用）
- 时间紧迫的项目

### 成功标准

- ✅ 提供改进建议
- ✅ 不产生警告或阻断
- ✅ 用户可完全忽略
- ✅ 根据项目类型自适应

---

**版本**: v1.0
**最后更新**: 2025-12-22
**维护者**: wade
