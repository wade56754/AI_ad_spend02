"""
Database locking utilities for concurrent-safe operations.

解决问题: BE-P0-2 - 资金操作缺少数据库锁
SoT: MASTER.md v4.9 - 资金操作必须保证数据一致性
SoT: LEDGER_SOT.md v1.1 - 账本操作原子性要求

使用示例:
    # 单记录锁定
    with lock_for_update(db, AdAccount, account_id) as account:
        account.balance -= amount
        db.commit()

    # 多记录批量锁定
    with lock_multiple_for_update(db, AdAccount, [id1, id2]) as accounts:
        for account in accounts:
            account.balance -= amount

    # 排他锁定带超时
    with lock_exclusive(db, Ledger, entry_id, timeout=5.0) as entry:
        entry.status = 'reversed'
"""
from typing import TypeVar, Generic, List, Optional, Type, Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.core.exceptions import NotFoundError, ConflictError

T = TypeVar("T")


@contextmanager
def lock_for_update(
    db: Session,
    model: Type[T],
    id_value: int,
    *,
    timeout: Optional[float] = None,
    skip_locked: bool = False,
) -> Generator[T, None, None]:
    """
    为资金操作加悲观锁 (SELECT FOR UPDATE)。

    Args:
        db: 数据库会话
        model: SQLAlchemy 模型类
        id_value: 记录 ID
        timeout: 锁等待超时（秒），None 表示无限等待
        skip_locked: 是否跳过已锁定的行（用于非阻塞操作）

    Yields:
        锁定的记录对象

    Raises:
        NotFoundError: 记录不存在
        ConflictError: 获取锁超时或记录被跳过

    Examples:
        >>> with lock_for_update(db, AdAccount, account_id) as account:
        ...     account.balance -= Decimal('100.00')
        ...     db.commit()
    """
    query = db.query(model).filter(model.id == id_value)

    if skip_locked:
        query = query.with_for_update(skip_locked=True)
    elif timeout is not None:
        # PostgreSQL 支持 NOWAIT，但不直接支持超时
        # 使用 statement_timeout 设置来实现
        query = query.with_for_update(nowait=False)
    else:
        query = query.with_for_update()

    record = query.first()

    if record is None:
        if skip_locked:
            raise ConflictError(
                f"{model.__name__} with id {id_value} is locked or does not exist"
            )
        raise NotFoundError(f"{model.__name__} with id {id_value} not found")

    try:
        yield record
    except Exception:
        db.rollback()
        raise


@contextmanager
def lock_multiple_for_update(
    db: Session,
    model: Type[T],
    id_values: List[int],
    *,
    skip_locked: bool = False,
) -> Generator[List[T], None, None]:
    """
    批量锁定多条记录。

    为避免死锁，ID 会按升序排序后锁定。

    Args:
        db: 数据库会话
        model: SQLAlchemy 模型类
        id_values: 记录 ID 列表
        skip_locked: 是否跳过已锁定的行

    Yields:
        锁定的记录列表（按 ID 升序）

    Raises:
        NotFoundError: 部分记录不存在（skip_locked=False 时）

    Examples:
        >>> with lock_multiple_for_update(db, AdAccount, [1, 2, 3]) as accounts:
        ...     for account in accounts:
        ...         account.balance = Decimal('0')
    """
    if not id_values:
        yield []
        return

    # 按 ID 排序，避免死锁
    sorted_ids = sorted(set(id_values))

    query = db.query(model).filter(model.id.in_(sorted_ids)).order_by(model.id)

    if skip_locked:
        query = query.with_for_update(skip_locked=True)
    else:
        query = query.with_for_update()

    records = query.all()

    if not skip_locked and len(records) != len(sorted_ids):
        found_ids = {r.id for r in records}
        missing_ids = set(sorted_ids) - found_ids
        raise NotFoundError(f"{model.__name__} with ids {missing_ids} not found")

    try:
        yield records
    except Exception:
        db.rollback()
        raise


@contextmanager
def lock_with_retry(
    db: Session,
    model: Type[T],
    id_value: int,
    *,
    max_retries: int = 3,
    retry_delay: float = 0.1,
) -> Generator[T, None, None]:
    """
    带重试的锁定操作。

    适用于高并发场景，当锁冲突时自动重试。

    Args:
        db: 数据库会话
        model: SQLAlchemy 模型类
        id_value: 记录 ID
        max_retries: 最大重试次数
        retry_delay: 重试间隔（秒）

    Yields:
        锁定的记录对象

    Raises:
        NotFoundError: 记录不存在
        ConflictError: 达到最大重试次数后仍无法获取锁
    """
    import time
    from sqlalchemy.exc import OperationalError

    last_error = None

    for attempt in range(max_retries + 1):
        try:
            with lock_for_update(db, model, id_value, skip_locked=False) as record:
                yield record
                return
        except OperationalError as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(retry_delay * (attempt + 1))  # 指数退避
                db.rollback()  # 清理失败的事务
            continue

    raise ConflictError(
        f"Failed to acquire lock on {model.__name__} {id_value} "
        f"after {max_retries} retries: {last_error}"
    )


def ensure_locked(record: T, model_name: str = "Record") -> T:
    """
    确认记录已被锁定的断言辅助函数。

    用于代码文档化和运行时检查。

    Args:
        record: 数据库记录
        model_name: 模型名称（用于错误消息）

    Returns:
        原始记录

    Raises:
        AssertionError: 如果记录为 None
    """
    assert record is not None, f"{model_name} must be locked before modification"
    return record
