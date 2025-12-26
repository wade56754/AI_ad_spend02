# 测试文件：包含多个代码质量问题

import hashlib

# 问题 1: 硬编码 API 密钥（Layer 1 - Security）
API_KEY = "sk-1234567890abcdef"
DATABASE_PASSWORD = "my-secret-password"

# 问题 2: 使用 MD5 哈希密码（Layer 1 - Security）
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

# 问题 3: SQL 注入风险（Layer 1 - Security）
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    # 执行查询...
    return query

# 问题 4: 缺少错误处理（Layer 2 - Behavior）
def fetch_user_data(user_id):
    user = get_user(user_id)
    return user.name  # 如果 user 为 None 会报错

# 问题 5: 变量命名不清晰（Layer 2 - Behavior）
def process(x, y):
    a = x + y
    b = a * 2
    return b

# 问题 6: N+1 查询问题（Layer 2 - Behavior）
def get_all_orders():
    users = get_all_users()
    for user in users:
        orders = get_orders_by_user(user.id)  # 每个 user 触发一次查询
        print(orders)

# 问题 7: 缺少 docstring（Layer 3 - Task）
def calculate_total_price(items, discount_rate, tax_rate):
    # 复杂的价格计算逻辑
    subtotal = sum(item.price * item.quantity for item in items)
    discount = subtotal * discount_rate
    tax = (subtotal - discount) * tax_rate
    return subtotal - discount + tax

# 问题 8: 配置硬编码（Layer 3 - Task）
def send_email(to, subject, body):
    smtp_host = "smtp.gmail.com"  # 硬编码配置
    smtp_port = 587
    # 发送邮件逻辑...
    pass
