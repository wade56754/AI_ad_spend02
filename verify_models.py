"""验证 SQLAlchemy 模型层"""
import inspect
from backend.models import database_models

# 获取所有模型类
models = [
    obj for name, obj in inspect.getmembers(database_models)
    if inspect.isclass(obj) and hasattr(obj, '__tablename__')
]

print("="*70)
print(f"模型总数: {len(models)}")
print("="*70)

for i, model in enumerate(models, 1):
    print(f"{i:2}. {model.__tablename__:30} -> {model.__name__}")

print("="*70)

# 验证关键特性
print("\n验证关键模型特性:")
print("-"*70)

# User 模型
from backend.models.database_models import User
user_columns = [c.name for c in User.__table__.columns]
print(f"User 模型字段数: {len(user_columns)}")
print(f"User 字段: {', '.join(user_columns[:5])}...")

# AdAccount 模型
from backend.models.database_models import AdAccount
account_indexes = [idx.name for idx in AdAccount.__table__.indexes]
print(f"\nAdAccount 索引数: {len(account_indexes)}")
print(f"AdAccount 索引: {', '.join(account_indexes[:3])}...")

# AccountAlert 模型（验证 metadata 字段映射）
from backend.models.database_models import AccountAlert
alert_columns = {c.name: c.key for c in AccountAlert.__table__.columns}
print(f"\nAccountAlert 'metadata' 列映射: {alert_columns.get('metadata', 'NOT FOUND')}")

print("\n" + "="*70)
print("验证完成!")
