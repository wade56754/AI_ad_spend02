"""
ID生成器工具
Version: 1.0
Author: Claude协作开发
"""

from datetime import datetime


def generate_request_no(prefix: str) -> str:
    """生成申请单号"""
    """
    生成格式：PREFIX + YYYYMMDD + HHMMSS + 3位随机数
    例如：TOP20251112143045001
    """
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")

    # 使用微秒的后3位作为随机数
    random_suffix = str(now.microsecond)[-3:].zfill(3)

    return f"{prefix}{timestamp}{random_suffix}"


def generate_transaction_no() -> str:
    """生成交易流水号"""
    """
    生成格式：TXN + YYYYMMDD + HHMMSS + 3位随机数
    """
    return generate_request_no("TXN")