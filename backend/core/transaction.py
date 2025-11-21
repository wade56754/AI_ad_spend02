"""
事务管理模块
提供数据库事务管理和上下文管理器
"""
import logging
from contextlib import contextmanager
from typing import Any, Callable, Optional, TypeVar

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.core.db import get_db

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TransactionManager:
    """事务管理器"""

    def __init__(self, session: Session):
        self.session = session
        self._savepoint = None

    def begin(self):
        """开始事务"""
        if not self.session.in_transaction():
            self.session.begin()
        return self

    def commit(self):
        """提交事务"""
        try:
            self.session.commit()
            logger.debug("Transaction committed")
        except SQLAlchemyError as e:
            logger.error(f"Failed to commit transaction: {e}")
            raise

    def rollback(self):
        """回滚事务"""
        try:
            self.session.rollback()
            logger.debug("Transaction rolled back")
        except SQLAlchemyError as e:
            logger.error(f"Failed to rollback transaction: {e}")
            raise

    def savepoint(self, name: str = None):
        """创建保存点"""
        if name is None:
            name = f"sp_{id(self)}"
        self._savepoint = self.session.begin_nested()
        logger.debug(f"Savepoint created: {name}")
        return self._savepoint

    def rollback_to_savepoint(self, savepoint=None):
        """回滚到保存点"""
        if savepoint is None:
            savepoint = self._savepoint
        if savepoint:
            savepoint.rollback()
            logger.debug("Rollback to savepoint")


@contextmanager
def transaction(session: Optional[Session] = None):
    """事务上下文管理器

    Args:
        session: 数据库会话，如果为None则使用依赖注入的会话

    Usage:
        with transaction(db) as tx:
            # 数据库操作
            user = User(name="test")
            tx.add(user)
            # 自动提交或回滚
    """
    # 如果没有提供session，获取当前的session
    if session is None:
        # 在依赖注入上下文中使用
        session = next(get_db())

    tx_manager = TransactionManager(session)
    tx_manager.begin()

    try:
        yield tx_manager
        tx_manager.commit()
    except Exception as e:
        tx_manager.rollback()
        logger.error(f"Transaction failed, rolled back: {e}")
        raise


@contextmanager
def nested_transaction(session: Session):
    """嵌套事务上下文管理器（使用保存点）

    Args:
        session: 数据库会话

    Usage:
        with transaction(db) as tx1:
            # 外层事务
            with nested_transaction(tx1.session) as tx2:
                # 内层事务，可以独立回滚
    """
    savepoint = session.begin_nested()
    tx_manager = TransactionManager(session)
    tx_manager._savepoint = savepoint

    try:
        yield tx_manager
        savepoint.commit()
        logger.debug("Nested transaction committed")
    except Exception as e:
        savepoint.rollback()
        logger.debug(f"Nested transaction rolled back: {e}")
        raise


def transactional(func: Callable[..., T]) -> Callable[..., T]:
    """事务装饰器

    Args:
        func: 需要在事务中执行的函数

    Usage:
        @transactional
        def create_user(data: dict, db: Session):
            user = User(**data)
            db.add(user)
            return user
    """
    async def wrapper(*args, **kwargs) -> T:
        # 查找Session参数
        session = None
        for arg in args:
            if isinstance(arg, Session):
                session = arg
                break

        if session is None:
            session = kwargs.get('db')
            if session is None:
                # 尝试从依赖注入获取
                session = next(get_db())

        with transaction(session):
            return await func(*args, **kwargs)

    return wrapper


def run_in_transaction(
    session: Session,
    func: Callable,
    *args,
    **kwargs
) -> Any:
    """在事务中运行函数

    Args:
        session: 数据库会话
        func: 要执行的函数
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        函数执行结果
    """
    with transaction(session):
        return func(*args, **kwargs)


class TransactionScope:
    """事务作用域类"""

    def __init__(self, session: Session, auto_commit: bool = True):
        self.session = session
        self.auto_commit = auto_commit
        self._committed = False
        self._rolled_back = False

    def __enter__(self):
        self.session.begin()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # 发生异常，回滚
            self.session.rollback()
            self._rolled_back = True
            logger.error(f"Transaction rolled back due to {exc_type.__name__}: {exc_val}")
        elif not self._committed and self.auto_commit:
            # 没有异常且设置了自动提交
            self.session.commit()
            self._committed = True
            logger.debug("Transaction auto-committed")

    def commit(self):
        """手动提交"""
        if not self._committed and not self._rolled_back:
            self.session.commit()
            self._committed = True
            logger.debug("Transaction manually committed")

    def rollback(self):
        """手动回滚"""
        if not self._committed and not self._rolled_back:
            self.session.rollback()
            self._rolled_back = True
            logger.debug("Transaction manually rolled back")


class BatchTransaction:
    """批量事务处理器"""

    def __init__(self, session: Session, batch_size: int = 1000):
        self.session = session
        self.batch_size = batch_size
        self.buffer = []

    def add(self, obj: Any):
        """添加对象到批处理缓冲区"""
        self.buffer.append(obj)
        if len(self.buffer) >= self.batch_size:
            self.flush()

    def flush(self):
        """刷新缓冲区到数据库"""
        if self.buffer:
            self.session.add_all(self.buffer)
            self.session.flush()
            self.buffer.clear()
            logger.debug(f"Flushed {self.batch_size} items to database")

    def commit(self):
        """提交所有更改"""
        self.flush()
        self.session.commit()
        logger.debug("Batch transaction committed")

    def rollback(self):
        """回滚所有更改"""
        self.buffer.clear()
        self.session.rollback()
        logger.debug("Batch transaction rolled back")

    def __enter__(self):
        self.session.begin()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()


# 便捷函数
def get_transaction_manager(session: Session) -> TransactionManager:
    """获取事务管理器实例"""
    return TransactionManager(session)


def is_in_transaction(session: Session) -> bool:
    """检查是否在事务中"""
    return session.in_transaction()


# 示例使用
"""
# 1. 使用上下文管理器
with transaction(db) as tx:
    user = User(name="test")
    tx.session.add(user)
    # 自动提交

# 2. 使用装饰器
@transactional
async def create_user(data: dict, db: Session):
    user = User(**data)
    db.add(user)
    return user

# 3. 使用嵌套事务
with transaction(db) as tx1:
    # 创建用户
    user = User(name="test")
    tx1.session.add(user)

    with nested_transaction(tx1.session) as tx2:
        # 创建账户，失败不会影响用户创建
        account = Account(user_id=user.id)
        tx2.session.add(account)
        # 可以独立回滚

# 4. 批量处理
with BatchTransaction(db, batch_size=500) as batch:
    for data in large_dataset:
        user = User(**data)
        batch.add(user)
    # 自动提交所有批次
"""