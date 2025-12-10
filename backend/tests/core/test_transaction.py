"""
事务管理系统测试模块
测试 backend/core/transaction.py 的事务管理功能
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.core.transaction import (
    TransactionManager,
    TransactionScope,
    BatchTransaction,
    transaction,
    nested_transaction,
    transactional,
    run_in_transaction,
    get_transaction_manager,
    is_in_transaction,
)


# ==================== Fixtures ====================

@pytest.fixture
def mock_session():
    """模拟数据库会话"""
    session = Mock(spec=Session)
    session.in_transaction.return_value = False
    session.begin = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.flush = Mock()
    session.add = Mock()
    session.add_all = Mock()
    return session


@pytest.fixture
def tx_manager(mock_session):
    """事务管理器 fixture"""
    return TransactionManager(mock_session)


@pytest.fixture
def mock_savepoint():
    """模拟保存点"""
    savepoint = Mock()
    savepoint.commit = Mock()
    savepoint.rollback = Mock()
    return savepoint


# ==================== TransactionManager 测试 ====================

@pytest.mark.unit
@pytest.mark.transaction
class TestTransactionManager:
    """测试事务管理器核心功能"""

    def test_transaction_manager_initialization(self, mock_session):
        """测试事务管理器初始化"""
        manager = TransactionManager(mock_session)
        assert manager.session == mock_session
        assert manager._savepoint is None

    def test_begin_transaction(self, tx_manager, mock_session):
        """测试开始事务"""
        mock_session.in_transaction.return_value = False
        result = tx_manager.begin()

        mock_session.begin.assert_called_once()
        assert result == tx_manager

    def test_begin_transaction_already_active(self, tx_manager, mock_session):
        """测试在已有事务时调用 begin"""
        mock_session.in_transaction.return_value = True
        result = tx_manager.begin()

        # 不应该再次调用 begin
        mock_session.begin.assert_not_called()
        assert result == tx_manager

    def test_commit_success(self, tx_manager, mock_session):
        """测试成功提交事务"""
        tx_manager.commit()
        mock_session.commit.assert_called_once()

    def test_commit_failure(self, tx_manager, mock_session):
        """测试提交事务失败"""
        mock_session.commit.side_effect = SQLAlchemyError("Commit failed")

        with pytest.raises(SQLAlchemyError):
            tx_manager.commit()

    def test_rollback_success(self, tx_manager, mock_session):
        """测试成功回滚事务"""
        tx_manager.rollback()
        mock_session.rollback.assert_called_once()

    def test_rollback_failure(self, tx_manager, mock_session):
        """测试回滚事务失败"""
        mock_session.rollback.side_effect = SQLAlchemyError("Rollback failed")

        with pytest.raises(SQLAlchemyError):
            tx_manager.rollback()

    def test_savepoint_with_name(self, tx_manager, mock_session, mock_savepoint):
        """测试创建命名保存点"""
        mock_session.begin_nested.return_value = mock_savepoint

        result = tx_manager.savepoint(name="checkpoint_1")

        mock_session.begin_nested.assert_called_once()
        assert tx_manager._savepoint == mock_savepoint
        assert result == mock_savepoint

    def test_savepoint_auto_name(self, tx_manager, mock_session, mock_savepoint):
        """测试创建自动命名保存点"""
        mock_session.begin_nested.return_value = mock_savepoint

        result = tx_manager.savepoint()

        mock_session.begin_nested.assert_called_once()
        assert tx_manager._savepoint == mock_savepoint

    def test_rollback_to_savepoint(self, tx_manager, mock_savepoint):
        """测试回滚到保存点"""
        tx_manager._savepoint = mock_savepoint

        tx_manager.rollback_to_savepoint()

        mock_savepoint.rollback.assert_called_once()

    def test_rollback_to_specific_savepoint(self, tx_manager, mock_savepoint):
        """测试回滚到指定保存点"""
        another_savepoint = Mock()
        another_savepoint.rollback = Mock()

        tx_manager.rollback_to_savepoint(savepoint=another_savepoint)

        another_savepoint.rollback.assert_called_once()


# ==================== 事务上下文管理器测试 ====================

@pytest.mark.unit
@pytest.mark.transaction
class TestTransactionContextManager:
    """测试 transaction 上下文管理器"""

    @patch('backend.core.transaction.get_db')
    def test_transaction_context_success(self, mock_get_db, mock_session):
        """测试事务上下文成功提交"""
        mock_get_db.return_value = iter([mock_session])
        mock_session.in_transaction.return_value = False

        with transaction(mock_session) as tx:
            assert isinstance(tx, TransactionManager)
            assert tx.session == mock_session

        mock_session.begin.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch('backend.core.transaction.get_db')
    def test_transaction_context_exception(self, mock_get_db, mock_session):
        """测试事务上下文异常回滚"""
        mock_get_db.return_value = iter([mock_session])
        mock_session.in_transaction.return_value = False

        with pytest.raises(ValueError):
            with transaction(mock_session) as tx:
                raise ValueError("Test error")

        mock_session.begin.assert_called_once()
        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()

    @patch('backend.core.transaction.get_db')
    def test_transaction_context_no_session(self, mock_get_db, mock_session):
        """测试没有提供 session 时使用依赖注入"""
        mock_get_db.return_value = iter([mock_session])
        mock_session.in_transaction.return_value = False

        with transaction() as tx:
            assert isinstance(tx, TransactionManager)

        mock_get_db.assert_called_once()


# ==================== 嵌套事务测试 ====================

@pytest.mark.unit
@pytest.mark.transaction
class TestNestedTransaction:
    """测试嵌套事务功能"""

    def test_nested_transaction_success(self, mock_session, mock_savepoint):
        """测试嵌套事务成功提交"""
        mock_session.begin_nested.return_value = mock_savepoint

        with nested_transaction(mock_session) as tx:
            assert isinstance(tx, TransactionManager)

        mock_session.begin_nested.assert_called_once()
        mock_savepoint.commit.assert_called_once()

    def test_nested_transaction_rollback(self, mock_session, mock_savepoint):
        """测试嵌套事务回滚"""
        mock_session.begin_nested.return_value = mock_savepoint

        with pytest.raises(RuntimeError):
            with nested_transaction(mock_session) as tx:
                raise RuntimeError("Nested transaction error")

        mock_savepoint.rollback.assert_called_once()
        mock_savepoint.commit.assert_not_called()


# ==================== TransactionScope 测试 ====================

@pytest.mark.unit
@pytest.mark.transaction
class TestTransactionScope:
    """测试事务作用域类"""

    def test_transaction_scope_auto_commit(self, mock_session):
        """测试事务作用域自动提交"""
        scope = TransactionScope(mock_session, auto_commit=True)

        with scope:
            pass

        mock_session.begin.assert_called_once()
        mock_session.commit.assert_called_once()
        assert scope._committed is True

    def test_transaction_scope_manual_commit(self, mock_session):
        """测试事务作用域手动提交"""
        scope = TransactionScope(mock_session, auto_commit=False)

        with scope:
            scope.commit()

        mock_session.begin.assert_called_once()
        mock_session.commit.assert_called_once()
        assert scope._committed is True

    def test_transaction_scope_exception_rollback(self, mock_session):
        """测试事务作用域异常回滚"""
        scope = TransactionScope(mock_session, auto_commit=True)

        with pytest.raises(ValueError):
            with scope:
                raise ValueError("Test error")

        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()
        assert scope._rolled_back is True

    def test_transaction_scope_manual_rollback(self, mock_session):
        """测试事务作用域手动回滚"""
        scope = TransactionScope(mock_session, auto_commit=False)

        with scope:
            scope.rollback()

        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()
        assert scope._rolled_back is True

    def test_transaction_scope_no_double_commit(self, mock_session):
        """测试不会重复提交"""
        scope = TransactionScope(mock_session, auto_commit=False)

        with scope:
            scope.commit()
            scope.commit()  # 第二次调用应该被忽略

        # 只应调用一次
        assert mock_session.commit.call_count == 1


# ==================== BatchTransaction 测试 ====================

@pytest.mark.unit
@pytest.mark.transaction
class TestBatchTransaction:
    """测试批量事务处理"""

    def test_batch_transaction_initialization(self, mock_session):
        """测试批量事务初始化"""
        batch = BatchTransaction(mock_session, batch_size=500)

        assert batch.session == mock_session
        assert batch.batch_size == 500
        assert batch.buffer == []

    def test_batch_add_within_limit(self, mock_session):
        """测试添加对象未达到批次大小"""
        batch = BatchTransaction(mock_session, batch_size=3)

        obj1 = Mock()
        obj2 = Mock()
        batch.add(obj1)
        batch.add(obj2)

        assert len(batch.buffer) == 2
        mock_session.add_all.assert_not_called()

    def test_batch_add_trigger_flush(self, mock_session):
        """测试添加对象触发自动刷新"""
        batch = BatchTransaction(mock_session, batch_size=2)

        obj1 = Mock()
        obj2 = Mock()
        batch.add(obj1)
        batch.add(obj2)  # 触发 flush

        mock_session.add_all.assert_called_once()
        mock_session.flush.assert_called_once()
        assert len(batch.buffer) == 0

    def test_batch_manual_flush(self, mock_session):
        """测试手动刷新批处理"""
        batch = BatchTransaction(mock_session, batch_size=100)

        batch.buffer = [Mock(), Mock(), Mock()]
        batch.flush()

        mock_session.add_all.assert_called_once()
        mock_session.flush.assert_called_once()
        assert len(batch.buffer) == 0

    def test_batch_commit(self, mock_session):
        """测试批量事务提交"""
        batch = BatchTransaction(mock_session, batch_size=100)
        batch.buffer = [Mock()]

        batch.commit()

        mock_session.add_all.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_batch_rollback(self, mock_session):
        """测试批量事务回滚"""
        batch = BatchTransaction(mock_session, batch_size=100)
        batch.buffer = [Mock(), Mock()]

        batch.rollback()

        assert len(batch.buffer) == 0
        mock_session.rollback.assert_called_once()

    def test_batch_context_manager_success(self, mock_session):
        """测试批量事务上下文管理器成功"""
        with BatchTransaction(mock_session, batch_size=10) as batch:
            batch.add(Mock())

        mock_session.begin.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_batch_context_manager_exception(self, mock_session):
        """测试批量事务上下文管理器异常"""
        with pytest.raises(RuntimeError):
            with BatchTransaction(mock_session, batch_size=10) as batch:
                batch.add(Mock())
                raise RuntimeError("Batch error")

        mock_session.rollback.assert_called_once()


# ==================== 工具函数测试 ====================

@pytest.mark.unit
@pytest.mark.transaction
class TestTransactionUtilities:
    """测试事务工具函数"""

    def test_get_transaction_manager(self, mock_session):
        """测试获取事务管理器"""
        manager = get_transaction_manager(mock_session)

        assert isinstance(manager, TransactionManager)
        assert manager.session == mock_session

    def test_is_in_transaction_true(self, mock_session):
        """测试检查在事务中"""
        mock_session.in_transaction.return_value = True

        result = is_in_transaction(mock_session)

        assert result is True
        mock_session.in_transaction.assert_called_once()

    def test_is_in_transaction_false(self, mock_session):
        """测试检查不在事务中"""
        mock_session.in_transaction.return_value = False

        result = is_in_transaction(mock_session)

        assert result is False

    @patch('backend.core.transaction.transaction')
    def test_run_in_transaction(self, mock_transaction_context, mock_session):
        """测试在事务中运行函数"""
        mock_func = Mock(return_value="test_result")
        mock_transaction_context.return_value.__enter__ = Mock()
        mock_transaction_context.return_value.__exit__ = Mock()

        result = run_in_transaction(mock_session, mock_func, "arg1", kwarg1="value1")

        mock_func.assert_called_once_with("arg1", kwarg1="value1")


# ==================== 集成测试 ====================

@pytest.mark.integration
@pytest.mark.transaction
class TestTransactionIntegration:
    """事务系统集成测试"""

    def test_transaction_workflow(self, mock_session, mock_savepoint):
        """测试完整事务工作流"""
        mock_session.in_transaction.return_value = False
        mock_session.begin_nested.return_value = mock_savepoint

        # 外层事务
        with transaction(mock_session) as tx1:
            # 创建保存点
            sp = tx1.savepoint("checkpoint")

            # 嵌套事务
            with nested_transaction(tx1.session) as tx2:
                pass

        # 验证调用序列
        mock_session.begin.assert_called()
        mock_session.commit.assert_called()

    def test_batch_processing_workflow(self, mock_session):
        """测试批量处理工作流"""
        items = [Mock() for _ in range(5)]

        with BatchTransaction(mock_session, batch_size=2) as batch:
            for item in items:
                batch.add(item)

        # batch_size=2, 5个对象应该触发2次 flush + 1次最终提交时的 flush
        assert mock_session.add_all.call_count >= 2
        mock_session.commit.assert_called_once()


# ==================== 边界情况测试 ====================

@pytest.mark.unit
@pytest.mark.transaction
class TestTransactionEdgeCases:
    """测试事务系统边界情况"""

    def test_empty_batch_flush(self, mock_session):
        """测试空批次刷新"""
        batch = BatchTransaction(mock_session, batch_size=10)
        batch.flush()  # 空缓冲区

        mock_session.add_all.assert_not_called()

    def test_transaction_scope_already_committed(self, mock_session):
        """测试已提交后再次提交"""
        scope = TransactionScope(mock_session, auto_commit=False)
        scope._committed = True

        scope.commit()  # 应该被忽略

        mock_session.commit.assert_not_called()

    def test_rollback_to_none_savepoint(self, tx_manager):
        """测试回滚到不存在的保存点"""
        # 不应该抛出异常
        tx_manager.rollback_to_savepoint(savepoint=None)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
