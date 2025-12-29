"""
缓存失效策略模块

Phase 3 性能优化 (TASK-PERF-001)

功能:
- 统一的缓存失效接口
- 事件驱动的失效策略
- 级联失效规则

使用方式:
在 Router 层的写操作后调用对应的失效函数

Example:
```python
from backend.core.cache_invalidation import CacheInvalidator

# 项目创建后
await CacheInvalidator.on_project_change(project_id=new_project.id, action="create")

# 账户状态变更后
await CacheInvalidator.on_account_change(account_id=account.id, action="status_update")
```
"""

import logging
from typing import Optional, List

from backend.core.cache import cache_manager

logger = logging.getLogger(__name__)


class CacheInvalidator:
    """
    缓存失效管理器

    失效策略:
    1. 写操作后立即失效相关缓存
    2. 级联失效: 子实体变更影响父实体缓存
    3. 批量失效: 支持按模式批量删除

    失效规则:
    - 项目变更 → 失效项目缓存 + Dashboard 缓存
    - 账户变更 → 失效账户缓存 + 项目缓存 + Dashboard 缓存
    - 日报变更 → 失效日报缓存 + 账户缓存 + Dashboard 缓存
    - 充值变更 → 失效充值缓存 + 账户缓存 + Dashboard 缓存
    """

    @staticmethod
    async def on_project_change(
        project_id: Optional[int] = None, action: str = "update"
    ) -> int:
        """
        项目变更时失效缓存

        触发场景:
        - 项目创建/更新/删除
        - 项目状态变更
        - 项目成员变更
        - 项目费用变更

        Args:
            project_id: 项目 ID
            action: 操作类型 (create/update/delete/status_change)

        Returns:
            失效的缓存键数量
        """
        count = 0

        # 失效项目统计缓存 (所有用户)
        count += await cache_manager.delete_pattern("ai_ads:projects:statistics:*")

        # 失效项目列表缓存
        count += await cache_manager.delete_pattern("ai_ads:projects:list:*")

        # 失效单个项目详情缓存
        if project_id:
            count += await cache_manager.delete_pattern(
                f"ai_ads:projects:detail:{project_id}:*"
            )

        # 级联失效 Dashboard
        count += await cache_manager.delete_pattern("ai_ads:dashboard:*")

        logger.info(
            f"项目缓存失效: action={action}, project_id={project_id}, keys={count}"
        )
        return count

    @staticmethod
    async def on_account_change(
        account_id: Optional[int] = None,
        project_id: Optional[int] = None,
        action: str = "update",
    ) -> int:
        """
        账户变更时失效缓存

        触发场景:
        - 账户创建/更新/删除
        - 账户状态变更
        - 账户预算调整

        Args:
            account_id: 账户 ID
            project_id: 关联项目 ID
            action: 操作类型

        Returns:
            失效的缓存键数量
        """
        count = 0

        # 失效账户统计缓存
        count += await cache_manager.delete_pattern("ai_ads:accounts:statistics:*")

        # 失效账户列表缓存
        count += await cache_manager.delete_pattern("ai_ads:accounts:list:*")

        # 失效单个账户详情缓存
        if account_id:
            count += await cache_manager.delete_pattern(
                f"ai_ads:accounts:detail:{account_id}:*"
            )

        # 级联失效项目缓存 (账户变更影响项目统计)
        if project_id:
            count += await cache_manager.delete_pattern(
                f"ai_ads:projects:detail:{project_id}:*"
            )
        count += await cache_manager.delete_pattern("ai_ads:projects:statistics:*")

        # 级联失效 Dashboard
        count += await cache_manager.delete_pattern("ai_ads:dashboard:*")

        logger.info(
            f"账户缓存失效: action={action}, account_id={account_id}, keys={count}"
        )
        return count

    @staticmethod
    async def on_daily_report_change(
        report_id: Optional[int] = None,
        account_id: Optional[int] = None,
        report_date: Optional[str] = None,
        action: str = "update",
    ) -> int:
        """
        日报变更时失效缓存

        触发场景:
        - 日报创建/更新/删除
        - 日报状态流转

        Args:
            report_id: 日报 ID
            account_id: 账户 ID
            report_date: 日报日期
            action: 操作类型

        Returns:
            失效的缓存键数量
        """
        count = 0

        # 失效日报列表缓存
        count += await cache_manager.delete_pattern("ai_ads:daily_reports:list:*")

        # 失效单个日报缓存
        if report_id:
            count += await cache_manager.delete_pattern(
                f"ai_ads:daily_reports:detail:{report_id}:*"
            )

        # 级联失效账户缓存 (日报影响账户统计)
        if account_id:
            count += await cache_manager.delete_pattern(
                f"ai_ads:accounts:detail:{account_id}:*"
            )

        # 级联失效 Dashboard (日报是 Dashboard 核心数据源)
        count += await cache_manager.delete_pattern("ai_ads:dashboard:*")

        logger.info(
            f"日报缓存失效: action={action}, report_id={report_id}, keys={count}"
        )
        return count

    @staticmethod
    async def on_topup_change(
        topup_id: Optional[int] = None,
        account_id: Optional[int] = None,
        action: str = "update",
    ) -> int:
        """
        充值变更时失效缓存

        触发场景:
        - 充值创建/更新/删除
        - 充值状态变更

        Args:
            topup_id: 充值 ID
            account_id: 账户 ID
            action: 操作类型

        Returns:
            失效的缓存键数量
        """
        count = 0

        # 失效充值列表缓存
        count += await cache_manager.delete_pattern("ai_ads:topups:list:*")

        # 失效单个充值缓存
        if topup_id:
            count += await cache_manager.delete_pattern(
                f"ai_ads:topups:detail:{topup_id}:*"
            )

        # 级联失效账户缓存 (充值影响账户余额)
        if account_id:
            count += await cache_manager.delete_pattern(
                f"ai_ads:accounts:detail:{account_id}:*"
            )

        # 级联失效 Dashboard (资金数据)
        count += await cache_manager.delete_pattern("ai_ads:dashboard:*")

        logger.info(f"充值缓存失效: action={action}, topup_id={topup_id}, keys={count}")
        return count

    @staticmethod
    async def on_user_change(
        user_id: Optional[str] = None, action: str = "update"
    ) -> int:
        """
        用户变更时失效缓存

        触发场景:
        - 用户角色变更
        - 用户状态变更

        Args:
            user_id: 用户 ID
            action: 操作类型

        Returns:
            失效的缓存键数量
        """
        count = 0

        # 失效用户相关的所有缓存 (角色变更影响权限过滤)
        if user_id:
            count += await cache_manager.delete_pattern(f"ai_ads:*:{user_id}:*")

        logger.info(f"用户缓存失效: action={action}, user_id={user_id}, keys={count}")
        return count

    @staticmethod
    async def invalidate_all() -> int:
        """
        失效所有缓存

        触发场景:
        - 系统维护
        - 数据迁移
        - 紧急清理

        Returns:
            失效的缓存键数量
        """
        count = await cache_manager.delete_pattern("ai_ads:*")
        logger.warning(f"全量缓存失效: keys={count}")
        return count

    @staticmethod
    async def invalidate_dashboard_only() -> int:
        """
        仅失效 Dashboard 缓存

        触发场景:
        - Dashboard 数据刷新请求
        - 定时任务强制刷新

        Returns:
            失效的缓存键数量
        """
        count = await cache_manager.delete_pattern("ai_ads:dashboard:*")
        logger.info(f"Dashboard 缓存失效: keys={count}")
        return count


# 便捷函数导出
on_project_change = CacheInvalidator.on_project_change
on_account_change = CacheInvalidator.on_account_change
on_daily_report_change = CacheInvalidator.on_daily_report_change
on_topup_change = CacheInvalidator.on_topup_change
on_user_change = CacheInvalidator.on_user_change
invalidate_all = CacheInvalidator.invalidate_all
invalidate_dashboard_only = CacheInvalidator.invalidate_dashboard_only
