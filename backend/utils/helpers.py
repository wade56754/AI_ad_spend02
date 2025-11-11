"""
通用辅助函数
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from passlib.context import CryptContext
from pydantic import BaseModel

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """密码哈希

    Args:
        password: 明文密码

    Returns:
        哈希后的密码
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def generate_uuid() -> str:
    """生成UUID字符串"""
    import uuid
    return str(uuid.uuid4())


def to_snake_case(name: str) -> str:
    """转换为蛇形命名

    Args:
        name: 原始字符串

    Returns:
        蛇形命名字符串
    """
    # 处理驼峰命名
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.lower()


def to_camel_case(name: str) -> str:
    """转换为驼峰命名

    Args:
        name: 原始字符串

    Returns:
        驼峰命名字符串
    """
    parts = name.split('_')
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])


def deep_merge_dict(dict1: Dict, dict2: Dict) -> Dict:
    """深度合并字典

    Args:
        dict1: 第一个字典
        dict2: 第二个字典

    Returns:
        合并后的字典
    """
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dict(result[key], value)
        else:
            result[key] = value

    return result


def convert_datetime_to_iso(dt: datetime) -> str:
    """将datetime转换为ISO格式字符串

    Args:
        dt: datetime对象

    Returns:
        ISO格式字符串
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def convert_iso_to_datetime(iso_str: str) -> datetime:
    """将ISO格式字符串转换为datetime

    Args:
        iso_str: ISO格式字符串

    Returns:
        datetime对象
    """
    return datetime.fromisoformat(iso_str.replace('Z', '+00:00'))


def mask_sensitive_data(data: Union[str, Dict], mask_char: str = "*") -> Union[str, Dict]:
    """脱敏处理敏感数据

    Args:
        data: 要脱敏的数据
        mask_char: 脱敏字符

    Returns:
        脱敏后的数据
    """
    if isinstance(data, str):
        # 邮箱脱敏
        if '@' in data:
            local, domain = data.split('@', 1)
            if len(local) <= 2:
                masked_local = mask_char * len(local)
            else:
                masked_local = local[0] + mask_char * (len(local) - 2) + local[-1]
            return f"{masked_local}@{domain}"

        # 手机号脱敏
        if re.match(r'^\d{11}$', data):
            return data[:3] + mask_char * 5 + data[-3:]

        # 身份证脱敏
        if re.match(r'^\d{18}$', data):
            return data[:6] + mask_char * 8 + data[-4:]

        # 通用字符串脱敏
        if len(data) <= 4:
            return mask_char * len(data)
        return data[:2] + mask_char * (len(data) - 4) + data[-2:]

    elif isinstance(data, dict):
        masked_dict = {}
        for key, value in data.items():
            # 敏感字段直接脱敏
            if any(sensitive in key.lower() for sensitive in
                   ['password', 'token', 'secret', 'key', 'salt']):
                masked_dict[key] = mask_char * 8
            else:
                masked_dict[key] = mask_sensitive_data(value, mask_char)
        return masked_dict

    return data


def calculate_checksum(data: Any) -> str:
    """计算数据的校验和

    Args:
        data: 要计算的数据

    Returns:
        MD5校验和
    """
    if isinstance(data, (dict, list)):
        data = json.dumps(data, sort_keys=True, ensure_ascii=False)

    return hashlib.md5(str(data).encode('utf-8')).hexdigest()


def paginate_query(query, page: int, size: int):
    """分页查询通用函数

    Args:
        query: SQLAlchemy查询对象
        page: 页码
        size: 每页大小

    Returns:
        分页结果
    """
    # 计算偏移量
    offset = (page - 1) * size

    # 获取总数
    total = query.count()

    # 获取分页数据
    items = query.offset(offset).limit(size).all()

    # 计算总页数
    pages = (total + size - 1) // size

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1,
    }


def validate_email(email: str) -> bool:
    """验证邮箱格式

    Args:
        email: 邮箱地址

    Returns:
        是否有效
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """验证手机号格式（中国）

    Args:
        phone: 手机号

    Returns:
        是否有效
    """
    pattern = r'^1[3-9]\d{9}$'
    return re.match(pattern, phone) is not None


def format_currency(amount: float, currency: str = "CNY") -> str:
    """格式化货币

    Args:
        amount: 金额
        currency: 货币代码

    Returns:
        格式化后的字符串
    """
    if currency == "CNY":
        return f"¥{amount:,.2f}"
    elif currency == "USD":
        return f"${amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"


def calculate_age(birth_date: datetime) -> int:
    """计算年龄

    Args:
        birth_date: 出生日期

    Returns:
        年龄
    """
    today = datetime.now()
    age = today.year - birth_date.year

    # 检查是否已过生日
    if today.month < birth_date.month or \
       (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1

    return age


def generate_random_code(length: int = 6) -> str:
    """生成随机验证码

    Args:
        length: 验证码长度

    Returns:
        随机验证码
    """
    import random
    import string
    return ''.join(random.choices(string.digits, k=length))


def safe_get(data: Dict, path: str, default: Any = None) -> Any:
    """安全获取嵌套字典的值

    Args:
        data: 字典数据
        path: 路径，用点分隔
        default: 默认值

    Returns:
        获取到的值或默认值
    """
    keys = path.split('.')
    current = data

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default

    return current


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """将列表分块

    Args:
        lst: 列表
        chunk_size: 块大小

    Returns:
        分块后的列表
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


class Timer:
    """计时器上下文管理器"""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.duration = None

    def __enter__(self):
        self.start_time = datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        self.duration = self.end_time - self.start_time

    @property
    def elapsed_seconds(self) -> float:
        """获取经过的秒数"""
        if self.duration is None:
            self.duration = datetime.now() - self.start_time
        return self.duration.total_seconds()


def retry_on_exception(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 退避倍数
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            import asyncio

            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise last_exception

        return wrapper
    return decorator