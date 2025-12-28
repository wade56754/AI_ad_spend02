# Layer 2: 行为约束（Behavior Constraints）

> **约束级别**: SHOULD（强烈推荐）
> **违反处理**: 警告并提供修复建议，不强制阻断
> **优先级**: 中等（低于 Layer 1，高于 Layer 3）

---

## 概述

Layer 2 行为约束关注代码质量和可维护性，虽然违反不会立即拒绝代码，但强烈建议修复以提高代码质量、可维护性和长期稳定性。

### 4 大行为类别

1. **代码可读性** - 清晰命名、适当注释、良好结构
2. **错误处理** - try-catch、错误消息、日志记录
3. **性能意识** - 避免 N+1 查询、缓存、内存管理
4. **可测试性** - 依赖注入、单元测试、模块化

---

## 1. 代码可读性（Code Readability）

### 规则定义

**建议**: 使用清晰的命名、适当的注释、良好的代码结构
**目标**: 让代码易于理解和维护

### 检测规则

#### 1.1 变量命名

**❌ 不推荐模式**:
```python
# Python
a = 10  # 无意义的单字母变量
x = get_user()  # x 不表达含义
temp = calculate()  # temp 太通用
data = fetch()  # data 太模糊

# JavaScript/TypeScript
let x = 42;
const temp = getData();
var d = new Date();
```

**✅ 推荐做法**:
```python
# Python
user_count = 10
current_user = get_user()
total_amount = calculate()
order_list = fetch()

# JavaScript/TypeScript
let itemCount = 42;
const userData = getData();
const createdAt = new Date();
```

**命名规范**:
- **变量**: 名词，描述存储的内容（`user_count`, `totalAmount`）
- **函数**: 动词开头，描述操作（`get_user`, `calculateTotal`）
- **类**: 名词，首字母大写（`UserService`, `OrderManager`）
- **常量**: 全大写下划线分隔（`MAX_RETRIES`, `API_TIMEOUT`）
- **布尔值**: is/has/can 开头（`is_active`, `hasPermission`）

---

#### 1.2 函数命名

**❌ 不推荐模式**:
```python
# Python
def process(data):  # process 太模糊
    pass

def do_stuff(x, y):  # do_stuff 无意义
    pass

def func(a, b, c):  # func 完全无意义
    pass

# JavaScript/TypeScript
function handle(data) {}  // handle 太模糊
function doIt() {}  // doIt 无意义
```

**✅ 推荐做法**:
```python
# Python
def calculate_total_price(items):
    pass

def send_email_notification(user, message):
    pass

def validate_user_input(form_data):
    pass

# JavaScript/TypeScript
function calculateTotalPrice(items: Item[]): number {}
function sendEmailNotification(user: User, message: string): void {}
function validateUserInput(formData: FormData): boolean {}
```

---

#### 1.3 注释

**❌ 不推荐模式**:
```python
# 无用注释
x = x + 1  # 加 1

# 过时注释
# TODO: 修复这个 bug（已经修复但注释未删除）

# 注释代码（应该删除）
# old_function()
# deprecated_code()
```

**✅ 推荐做法**:
```python
# 解释"为什么"而非"是什么"
# 使用缓存避免重复计算斐波那契数列，显著提升性能
@lru_cache(maxsize=128)
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# 复杂逻辑的业务说明
# 根据业务规则，VIP 用户享受 20% 折扣，新用户享受 10% 折扣
if user.is_vip:
    discount = 0.20
elif user.is_new:
    discount = 0.10
else:
    discount = 0.0
```

---

#### 1.4 代码结构

**❌ 不推荐模式**:
```python
# 嵌套过深（> 3 层）
def process_order(order):
    if order.is_valid():
        if order.has_items():
            for item in order.items:
                if item.is_available():
                    if item.stock > 0:
                        # 处理逻辑
                        pass

# 函数过长（> 50 行）
def handle_request():
    # 100+ 行代码
    pass
```

**✅ 推荐做法**:
```python
# 提取函数，减少嵌套
def process_order(order):
    if not order.is_valid() or not order.has_items():
        return

    for item in order.items:
        process_item(item)

def process_item(item):
    if not item.is_available() or item.stock <= 0:
        return

    # 处理逻辑
    reserve_stock(item)
    update_inventory(item)

# 单一职责原则
def calculate_total_price(items):
    return sum(item.price * item.quantity for item in items)

def apply_discount(total, discount_rate):
    return total * (1 - discount_rate)

def calculate_final_price(items, discount_rate):
    total = calculate_total_price(items)
    return apply_discount(total, discount_rate)
```

### 风险等级

**Medium** - 代码可读性差可导致：
- 维护成本增加
- Bug 率上升
- 新成员上手困难
- 代码审查效率低

### 修复建议

1. **遵循语言规范** (PEP 8, ESLint, Prettier)
2. **提取复杂逻辑** - 单独函数
3. **减少嵌套** - Early return, 提取函数
4. **有意义的命名** - 自解释代码

---

## 2. 错误处理（Error Handling）

### 规则定义

**建议**: 使用 try-catch 处理异常，提供有意义的错误消息，记录日志
**目标**: 提高系统健壮性，便于问题排查

### 检测规则

#### 2.1 缺少错误处理

**❌ 不推荐模式**:
```python
# Python - 没有 try-except
def get_user(user_id):
    user = session.query(User).filter(User.id == user_id).first()
    return user.name  # 如果 user 为 None 会报错

# JavaScript/TypeScript - 没有 try-catch
async function fetchData() {
    const response = await fetch('/api/data');
    const data = await response.json();  // 如果请求失败会报错
    return data;
}
```

**✅ 推荐做法**:
```python
# Python - 使用 try-except
def get_user(user_id):
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(404, f"User {user_id} not found")
        return user.name
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(500, "Database error")

# JavaScript/TypeScript - 使用 try-catch
async function fetchData(): Promise<Data> {
    try {
        const response = await fetch('/api/data');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Failed to fetch data:', error);
        throw new Error('Failed to fetch data');
    }
}
```

---

#### 2.2 空 catch 块

**❌ 不推荐模式**:
```python
# Python
try:
    risky_operation()
except Exception:
    pass  # 吞掉异常，无法排查问题

# JavaScript/TypeScript
try {
    riskyOperation();
} catch (error) {
    // 空 catch 块，吞掉异常
}
```

**✅ 推荐做法**:
```python
# Python
try:
    risky_operation()
except ValueError as e:
    logger.warning(f"Invalid value: {e}")
    # 提供降级方案
    return default_value
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise  # 重新抛出异常

# JavaScript/TypeScript
try {
    riskyOperation();
} catch (error) {
    console.error('Operation failed:', error);
    // 提供降级方案或重新抛出
    return defaultValue;
}
```

---

#### 2.3 有意义的错误消息

**❌ 不推荐模式**:
```python
# Python
raise ValueError("Error")  # 消息太模糊
raise Exception("Invalid input")  # 缺少上下文

# JavaScript/TypeScript
throw new Error("Failed");  // 缺少详细信息
```

**✅ 推荐做法**:
```python
# Python
raise ValueError(f"Invalid email format: {email}. Expected format: user@example.com")
raise HTTPException(400, f"User {user_id} already exists")

# JavaScript/TypeScript
throw new Error(`Invalid email format: ${email}. Expected format: user@example.com`);
throw new ValidationError(`User ${userId} already exists`);
```

---

#### 2.4 日志记录

**❌ 不推荐模式**:
```python
# 没有日志
def process_payment(amount):
    charge = stripe.Charge.create(amount=amount)
    return charge

# 日志级别不当
logger.info(f"Critical error: {e}")  # 应该用 error 级别
```

**✅ 推荐做法**:
```python
# 使用适当的日志级别
import logging
logger = logging.getLogger(__name__)

def process_payment(amount, user_id):
    logger.info(f"Processing payment: user={user_id}, amount={amount}")
    try:
        charge = stripe.Charge.create(amount=amount)
        logger.info(f"Payment successful: charge_id={charge.id}")
        return charge
    except stripe.error.CardError as e:
        logger.warning(f"Card declined: {e}")
        raise
    except Exception as e:
        logger.error(f"Payment failed: {e}", exc_info=True)
        raise
```

**日志级别**:
- **DEBUG**: 详细调试信息
- **INFO**: 正常操作信息
- **WARNING**: 警告，但不影响功能
- **ERROR**: 错误，功能受影响
- **CRITICAL**: 严重错误，系统不可用

### 风险等级

**High** - 错误处理不当可导致：
- 系统崩溃
- 数据丢失
- 问题难以排查
- 用户体验差

### 修复建议

1. **try-catch 包裹风险操作** - 数据库、网络、文件 I/O
2. **提供有意义的错误消息** - 包含上下文信息
3. **记录日志** - 使用适当的日志级别
4. **优雅降级** - 提供降级方案而非直接崩溃

---

## 3. 性能意识（Performance Awareness）

### 规则定义

**建议**: 避免 N+1 查询、使用缓存、注意内存泄漏
**目标**: 提高系统性能和响应速度

### 检测规则

#### 3.1 N+1 查询问题

**❌ 不推荐模式**:
```python
# Python - SQLAlchemy
users = session.query(User).all()
for user in users:
    print(user.orders)  # 每个 user 触发一次查询，总共 N+1 次

# JavaScript/TypeScript - Prisma
const users = await prisma.user.findMany();
for (const user of users) {
    const orders = await prisma.order.findMany({
        where: { userId: user.id }
    });  // N+1 查询
}
```

**✅ 推荐做法**:
```python
# Python - SQLAlchemy
from sqlalchemy.orm import joinedload

# 使用 joinedload 预加载关联数据
users = session.query(User).options(joinedload(User.orders)).all()
for user in users:
    print(user.orders)  # 不触发额外查询

# 或使用 selectinload（适用于一对多）
from sqlalchemy.orm import selectinload
users = session.query(User).options(selectinload(User.orders)).all()

# JavaScript/TypeScript - Prisma
const users = await prisma.user.findMany({
    include: {
        orders: true  // 预加载关联数据
    }
});
```

---

#### 3.2 缺少缓存

**❌ 不推荐模式**:
```python
# 每次都重新计算
def get_popular_products():
    # 复杂的聚合查询
    products = session.query(Product).join(Order).group_by(Product.id).all()
    return products

# 每次请求都调用
@app.get("/popular")
def popular_products():
    return get_popular_products()
```

**✅ 推荐做法**:
```python
# 使用缓存
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=128)
def get_popular_products_cached():
    products = session.query(Product).join(Order).group_by(Product.id).all()
    return products

# 使用 Redis 缓存
import redis
r = redis.Redis()

@app.get("/popular")
def popular_products():
    cache_key = "popular_products"
    cached = r.get(cache_key)

    if cached:
        return json.loads(cached)

    products = get_popular_products()
    r.setex(cache_key, 300, json.dumps(products))  # 缓存 5 分钟
    return products
```

---

#### 3.3 大数据集处理

**❌ 不推荐模式**:
```python
# 一次性加载所有数据到内存
all_users = session.query(User).all()  # 可能有数百万条
for user in all_users:
    process(user)

# JavaScript/TypeScript
const allOrders = await prisma.order.findMany();  // 数据量可能很大
```

**✅ 推荐做法**:
```python
# 使用分页或流式处理
page_size = 1000
offset = 0

while True:
    users = session.query(User).limit(page_size).offset(offset).all()
    if not users:
        break

    for user in users:
        process(user)

    offset += page_size

# 或使用 yield_per（流式处理）
for user in session.query(User).yield_per(1000):
    process(user)

# JavaScript/TypeScript - 使用游标分页
let cursor = null;
while (true) {
    const orders = await prisma.order.findMany({
        take: 1000,
        cursor: cursor ? { id: cursor } : undefined
    });

    if (orders.length === 0) break;

    orders.forEach(order => process(order));
    cursor = orders[orders.length - 1].id;
}
```

---

#### 3.4 内存泄漏

**❌ 不推荐模式**:
```javascript
// JavaScript - 事件监听器未移除
function setupEventListener() {
    const button = document.getElementById('myButton');
    button.addEventListener('click', handleClick);
    // 组件销毁时未移除监听器，导致内存泄漏
}

// 全局变量累积
let globalCache = [];
function addToCache(item) {
    globalCache.push(item);  // 无限增长
}
```

**✅ 推荐做法**:
```javascript
// JavaScript - 清理事件监听器
function setupEventListener() {
    const button = document.getElementById('myButton');
    button.addEventListener('click', handleClick);

    // 组件销毁时清理
    return () => {
        button.removeEventListener('click', handleClick);
    };
}

// React - useEffect 清理
useEffect(() => {
    const button = document.getElementById('myButton');
    const handleClick = () => {};
    button.addEventListener('click', handleClick);

    return () => {
        button.removeEventListener('click', handleClick);
    };
}, []);

// 限制缓存大小
const MAX_CACHE_SIZE = 1000;
let globalCache = [];

function addToCache(item) {
    globalCache.push(item);
    if (globalCache.length > MAX_CACHE_SIZE) {
        globalCache.shift();  // 移除最旧的项
    }
}
```

### 风险等级

**Medium** - 性能问题可导致：
- 响应时间慢
- 服务器资源消耗高
- 用户体验差
- 成本增加

### 修复建议

1. **使用 ORM 预加载** - joinedload, selectinload, include
2. **缓存热点数据** - lru_cache, Redis
3. **分页/流式处理** - 避免一次性加载大数据集
4. **清理资源** - 事件监听器、定时器、连接

---

## 4. 可测试性（Testability）

### 规则定义

**建议**: 使用依赖注入、编写单元测试、模块化设计
**目标**: 提高代码可测试性，降低 Bug 率

### 检测规则

#### 4.1 硬编码依赖

**❌ 不推荐模式**:
```python
# 硬编码数据库连接
def get_user(user_id):
    session = SessionLocal()  # 硬编码依赖
    user = session.query(User).filter(User.id == user_id).first()
    return user

# JavaScript/TypeScript
class UserService {
    async getUser(userId: number) {
        const db = new Database();  // 硬编码依赖
        return db.users.find(userId);
    }
}
```

**✅ 推荐做法**:
```python
# 依赖注入
def get_user(user_id: int, session: Session = Depends(get_db)):
    user = session.query(User).filter(User.id == user_id).first()
    return user

# 测试时可以注入 Mock
def test_get_user():
    mock_session = MagicMock()
    user = get_user(1, session=mock_session)
    assert mock_session.query.called

# JavaScript/TypeScript
class UserService {
    constructor(private db: Database) {}  // 依赖注入

    async getUser(userId: number) {
        return this.db.users.find(userId);
    }
}

// 测试时可以注入 Mock
const mockDb = { users: { find: jest.fn() } };
const service = new UserService(mockDb);
```

---

#### 4.2 缺少单元测试

**❌ 不推荐模式**:
```python
# 复杂逻辑但没有测试
def calculate_discount(price, user_type, is_holiday):
    if user_type == "vip":
        discount = 0.20
    elif user_type == "new":
        discount = 0.10
    else:
        discount = 0.05

    if is_holiday:
        discount += 0.05

    return price * (1 - discount)
```

**✅ 推荐做法**:
```python
# 提供测试
def calculate_discount(price, user_type, is_holiday):
    if user_type == "vip":
        discount = 0.20
    elif user_type == "new":
        discount = 0.10
    else:
        discount = 0.05

    if is_holiday:
        discount += 0.05

    return price * (1 - discount)

# 单元测试
def test_calculate_discount_vip():
    assert calculate_discount(100, "vip", False) == 80

def test_calculate_discount_new():
    assert calculate_discount(100, "new", False) == 90

def test_calculate_discount_holiday():
    assert calculate_discount(100, "regular", True) == 90

def test_calculate_discount_vip_holiday():
    assert calculate_discount(100, "vip", True) == 75
```

---

#### 4.3 过度耦合

**❌ 不推荐模式**:
```python
# 单个函数做太多事情
def process_order(order_data):
    # 验证
    if not order_data.get("user_id"):
        raise ValueError("Missing user_id")

    # 计算价格
    total = sum(item["price"] * item["qty"] for item in order_data["items"])

    # 发送邮件
    send_email(order_data["user_id"], f"Total: {total}")

    # 保存数据库
    session.add(Order(**order_data))
    session.commit()
```

**✅ 推荐做法**:
```python
# 单一职责，模块化
def validate_order(order_data):
    if not order_data.get("user_id"):
        raise ValueError("Missing user_id")

def calculate_total(items):
    return sum(item["price"] * item["qty"] for item in items)

def save_order(order_data, session):
    order = Order(**order_data)
    session.add(order)
    session.commit()
    return order

def send_order_confirmation(user_id, total):
    send_email(user_id, f"Total: {total}")

def process_order(order_data, session):
    validate_order(order_data)
    total = calculate_total(order_data["items"])
    order = save_order(order_data, session)
    send_order_confirmation(order_data["user_id"], total)
    return order

# 每个函数可以单独测试
def test_validate_order():
    with pytest.raises(ValueError):
        validate_order({})

def test_calculate_total():
    items = [{"price": 10, "qty": 2}, {"price": 5, "qty": 3}]
    assert calculate_total(items) == 35
```

### 风险等级

**Medium** - 可测试性差可导致：
- Bug 率高
- 重构困难
- 维护成本高
- 缺乏信心修改代码

### 修复建议

1. **依赖注入** - 避免硬编码依赖
2. **单一职责** - 每个函数只做一件事
3. **编写单元测试** - 覆盖核心逻辑
4. **模块化设计** - 降低耦合度

---

## 违反处理流程

### 1. 检测到违反

当检测到 Layer 2 行为约束违反时：

```markdown
⚠️ **[Medium] 行为约束建议**

**类别**: 性能意识
**位置**: backend/services/order_service.py:58
**问题代码**:
```python
orders = session.query(Order).all()
for order in orders:
    print(order.items)  # N+1 查询
```

**问题描述**: 循环中触发额外查询，当数据量增大时会严重影响性能。

**修复建议**:
```python
from sqlalchemy.orm import selectinload

orders = session.query(Order).options(selectinload(Order.items)).all()
for order in orders:
    print(order.items)  # 不触发额外查询
```

**影响**: 中等（性能下降）
**建议修复**: 是
**允许忽略**: 是（非阻断性）
```

### 2. 警告但不阻断

- **生成代码**: 继续生成代码，但附带警告
- **记录问题**: 在报告中记录违反项
- **提供建议**: 给出具体的修复建议

### 3. 用户可选择忽略

用户可以选择忽略 Layer 2 警告：

```bash
# 忽略特定规则
/code-quality check --ignore=n-plus-one backend/services/order_service.py

# 忽略整个 Layer 2
/code-quality check --layer=1,3 backend/services/order_service.py
```

---

## 总结

### Layer 2 行为约束清单

| 行为类别 | 检查项 | 风险等级 | 是否阻断 |
|---------|--------|---------|---------|
| 代码可读性 | 命名、注释、结构 | Medium | 否 |
| 错误处理 | try-catch、日志、错误消息 | High | 否 |
| 性能意识 | N+1 查询、缓存、内存 | Medium | 否 |
| 可测试性 | 依赖注入、单元测试、模块化 | Medium | 否 |

### 成功标准

- ✅ 检测准确率 ≥ 90%
- ✅ 误报率 ≤ 10%
- ✅ 提供具体修复建议
- ✅ 允许用户选择性忽略

---

**版本**: v1.0
**最后更新**: 2025-12-22
**维护者**: wade
