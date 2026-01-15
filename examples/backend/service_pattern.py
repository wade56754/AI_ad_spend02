"""
Service 层标准模式 - AI 广告代投系统
Version: 1.0
SoT Reference: STATE_MACHINE.md v2.6, BUSINESS_RULES.md v3.2

本文件展示 Service 层的标准写法，供 AI 代码生成参考。

关键模式：
1. 注入 Session，使用事务上下文管理器
2. 业务规则校验引用 BUSINESS_RULES.md
3. 状态转换遵循 STATE_MACHINE.md
4. 日志记录关键操作
5. 禁止绕过账本系统 (DATA_SCHEMA.md v5.11 §3.4.4)
"""

import logging
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy import and_, or_, func, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError,
)
from backend.models import User
from backend.models.base import UserRole

logger = logging.getLogger(__name__)


class ExampleService:
    """
    示例服务类

    职责：
    - 业务逻辑处理
    - 数据访问协调
    - 状态机管理
    - 权限验证
    """

    def __init__(self, db: Session):
        self.db = db

    # === 事务管理 ===

    @contextmanager
    def transaction(self):
        """
        事务上下文管理器

        使用方式:
            with self.transaction():
                # 数据库操作
                self.db.add(entity)
        """
        try:
            yield
            self.db.commit()
            logger.debug("Transaction committed successfully")
        except Exception as e:
            logger.error(f"Transaction failed, rolling back: {str(e)}", exc_info=True)
            self.db.rollback()
            raise

    # === CRUD 操作 ===

    def list_examples(
        self,
        page: int,
        page_size: int,
        status: Optional[str] = None,
        current_user: Optional[User] = None,
    ) -> Tuple[List[Any], int]:
        """
        获取列表（带分页）

        Args:
            page: 页码
            page_size: 每页条数
            status: 状态筛选
            current_user: 当前用户

        Returns:
            (items, total): 数据列表和总数
        """
        from backend.models import Example  # 替换为实际模型

        query = self.db.query(Example)

        # 权限过滤 - 非管理员只能看自己的数据
        if current_user and current_user.role != UserRole.ADMIN:
            query = query.filter(Example.created_by == current_user.id)

        # 状态筛选
        if status:
            query = query.filter(Example.status == status)

        # 获取总数
        total = query.count()

        # 分页
        items = query.order_by(desc(Example.created_at)) \
                     .offset((page - 1) * page_size) \
                     .limit(page_size) \
                     .all()

        return items, total

    def get_by_id(self, item_id: int, current_user: User) -> Any:
        """
        根据 ID 获取实体

        Args:
            item_id: 实体 ID
            current_user: 当前用户

        Raises:
            ResourceNotFoundError: 资源不存在 (BIZ_002)
            PermissionDeniedError: 无权限访问 (AUTH_003)
        """
        from backend.models import Example

        item = self.db.query(Example).filter(Example.id == item_id).first()

        if not item:
            # ERROR_CODES_SOT v2.1: BIZ_002 = 资源未找到
            raise ResourceNotFoundError(
                f"资源 {item_id} 不存在",
                error_code="BIZ_002"
            )

        # 权限检查
        if not self._can_access(current_user, item):
            raise PermissionDeniedError("无权限访问该资源")

        return item

    def create(self, request: Any, current_user: User) -> Any:
        """
        创建实体

        业务规则:
        - BR-XXX-001: [描述具体业务规则]

        Args:
            request: 创建请求
            current_user: 当前用户

        Raises:
            BusinessLogicError: 业务规则校验失败
            ResourceConflictError: 资源已存在 (BIZ_003)
        """
        from backend.models import Example

        logger.info(f"Creating example by user {current_user.id}")

        # 业务规则校验 - BR-XXX-001
        self._validate_business_rules(request)

        # 唯一性检查
        existing = self.db.query(Example).filter(
            Example.unique_field == request.unique_field
        ).first()

        if existing:
            raise ResourceConflictError(
                f"资源已存在: {request.unique_field}",
                error_code="BIZ_003"
            )

        with self.transaction():
            entity = Example(
                # 字段映射
                field1=request.field1,
                field2=request.field2,
                # 系统字段
                created_by=current_user.id,
                status="draft",  # 初始状态
            )
            self.db.add(entity)
            self.db.flush()  # 获取 ID

            logger.info(f"Created example {entity.id}")
            return entity

    def update(self, item_id: int, request: Any, current_user: User) -> Any:
        """
        更新实体

        注意：
        - 仅允许更新特定状态下的记录
        - 遵循 STATE_MACHINE.md 状态约束
        """
        item = self.get_by_id(item_id, current_user)

        # 状态检查 - 仅 draft 状态可编辑
        if item.status not in ["draft", "pending"]:
            raise BusinessLogicError(
                f"当前状态 {item.status} 不允许编辑",
                error_code="BIZ_101"
            )

        with self.transaction():
            # 更新字段 (仅更新非空值)
            for field, value in request.model_dump(exclude_unset=True).items():
                if hasattr(item, field):
                    setattr(item, field, value)

            item.updated_at = datetime.utcnow()
            item.updated_by = current_user.id

            logger.info(f"Updated example {item_id} by user {current_user.id}")
            return item

    # === 状态机操作 ===

    def approve(self, item_id: int, current_user: User) -> Any:
        """
        审批操作 - 状态转换

        状态机 (STATE_MACHINE.md v2.6):
            pending_review → approved (管理员/财务审批)

        触发条件:
        - 用户角色: admin 或 finance
        - 当前状态: pending_review
        """
        item = self.get_by_id(item_id, current_user)

        # 状态转换校验
        allowed_transitions = {
            "pending_review": ["approved", "rejected"],
        }

        current_status = item.status
        target_status = "approved"

        if current_status not in allowed_transitions:
            raise BusinessLogicError(
                f"当前状态 {current_status} 不支持审批操作",
                error_code="BIZ_102"
            )

        if target_status not in allowed_transitions[current_status]:
            raise BusinessLogicError(
                f"无法从 {current_status} 转换到 {target_status}",
                error_code="BIZ_103"
            )

        with self.transaction():
            # 状态转换
            item.status = target_status
            item.approved_by = current_user.id
            item.approved_at = datetime.utcnow()

            # 创建审计日志
            self._create_audit_log(
                entity_type="example",
                entity_id=item.id,
                action="approve",
                old_status=current_status,
                new_status=target_status,
                user_id=current_user.id,
            )

            logger.info(
                f"Example {item_id} approved: {current_status} → {target_status} "
                f"by user {current_user.id}"
            )
            return item

    # === 账本操作 (DATA_SCHEMA.md v5.11 §3.4.4) ===

    def _record_ledger_entry(
        self,
        account_id: int,
        entry_type: str,
        amount: Decimal,
        reference_type: str,
        reference_id: int,
        description: str,
    ):
        """
        记录账本条目

        重要: 禁止直接修改 balance 字段！
        必须通过 ledger_entries 表记录所有资金变动。

        SoT: DATA_SCHEMA.md v5.11 §3.4.4
        """
        from backend.models.finance.ledger import LedgerEntry

        entry = LedgerEntry(
            account_id=account_id,
            entry_type=entry_type,  # credit/debit
            amount=amount,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
        )
        self.db.add(entry)
        logger.info(f"Ledger entry created: {entry_type} {amount} for account {account_id}")

    # === 私有方法 ===

    def _can_access(self, user: User, item: Any) -> bool:
        """权限检查"""
        if user.role == UserRole.ADMIN:
            return True
        return item.created_by == user.id

    def _validate_business_rules(self, request: Any):
        """
        业务规则校验

        引用 BUSINESS_RULES.md v3.2 中的规则编号
        """
        # BR-XXX-001: 示例规则
        pass

    def _create_audit_log(self, **kwargs):
        """创建审计日志"""
        from backend.models.audit import AuditLog

        log = AuditLog(**kwargs, created_at=datetime.utcnow())
        self.db.add(log)
