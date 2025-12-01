# -*- coding: utf-8 -*-
"""
测试数据工厂函数

提供创建测试数据的工厂函数，确保测试数据符合 SoT 规范。

基准文档: AUTOMATION_TEST_SPEC_v1.4.md 第 3.2 节
SoT 依赖: DATA_SCHEMA.md v5.2, STATE_MACHINE.md v2.6
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import uuid4


def create_test_project(
    *,
    name: str = "测试项目",
    owner_id: Optional[str] = None,
    status: str = "active",
    **kwargs
) -> Dict[str, Any]:
    """
    创建测试项目数据

    Args:
        name: 项目名称
        owner_id: 所有者 ID（默认自动生成）
        status: 项目状态 (active/inactive/archived)
        **kwargs: 其他字段覆盖

    Returns:
        符合 DATA_SCHEMA.md projects 表结构的字典

    SoT Ref: DATA_SCHEMA.md v5.2 第 2.1 节
    """
    return {
        "id": str(uuid4()),
        "name": name,
        "owner_id": owner_id or str(uuid4()),
        "status": status,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        **kwargs
    }


def create_test_channel(
    *,
    name: str = "测试渠道",
    channel_type: str = "social",
    **kwargs
) -> Dict[str, Any]:
    """
    创建测试渠道数据

    Args:
        name: 渠道名称
        channel_type: 渠道类型 (social/search/display)
        **kwargs: 其他字段覆盖

    Returns:
        符合 DATA_SCHEMA.md channels 表结构的字典

    SoT Ref: DATA_SCHEMA.md v5.2 第 2.2 节
    """
    return {
        "id": str(uuid4()),
        "name": name,
        "channel_type": channel_type,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        **kwargs
    }


def create_test_ad_account(
    *,
    project_id: Optional[str] = None,
    channel_id: Optional[str] = None,
    account_name: str = "测试广告账户",
    platform_account_id: str = "ACC_001",
    balance: Decimal = Decimal("10000.00"),
    **kwargs
) -> Dict[str, Any]:
    """
    创建测试广告账户数据

    Args:
        project_id: 关联项目 ID
        channel_id: 关联渠道 ID
        account_name: 账户名称
        platform_account_id: 平台账户 ID
        balance: 账户余额
        **kwargs: 其他字段覆盖

    Returns:
        符合 DATA_SCHEMA.md ad_accounts 表结构的字典

    SoT Ref: DATA_SCHEMA.md v5.2 第 2.3 节
    """
    return {
        "id": str(uuid4()),
        "project_id": project_id or str(uuid4()),
        "channel_id": channel_id or str(uuid4()),
        "account_name": account_name,
        "platform_account_id": platform_account_id,
        "balance": balance,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        **kwargs
    }


def create_test_daily_report(
    *,
    ad_account_id: Optional[str] = None,
    report_date: Optional[date] = None,
    status: str = "raw_submitted",
    spend: Decimal = Decimal("100.00"),
    impressions: int = 1000,
    clicks: int = 50,
    conversions: int = 5,
    **kwargs
) -> Dict[str, Any]:
    """
    创建测试日报数据

    Args:
        ad_account_id: 关联广告账户 ID
        report_date: 报告日期（默认今天）
        status: 日报状态（默认 raw_submitted）
        spend: 消耗金额
        impressions: 展示次数
        clicks: 点击次数
        conversions: 转化次数
        **kwargs: 其他字段覆盖

    Returns:
        符合 DATA_SCHEMA.md daily_reports 表结构的字典

    SoT Ref:
        - DATA_SCHEMA.md v5.2 第 2.4 节
        - STATE_MACHINE.md v2.6 第 8 章 (DailyReport 8 状态机)

    状态枚举（8 状态机）:
        raw_submitted → trend_pending → trend_ok/trend_flagged
        → trend_resolved → final_pending → final_confirmed → final_locked
    """
    return {
        "id": str(uuid4()),
        "ad_account_id": ad_account_id or str(uuid4()),
        "report_date": report_date or date.today(),
        "status": status,
        "spend": spend,
        "impressions": impressions,
        "clicks": clicks,
        "conversions": conversions,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        **kwargs
    }


def create_test_topup_request(
    *,
    ad_account_id: Optional[str] = None,
    amount: Decimal = Decimal("1000.00"),
    status: str = "pending",
    requested_by: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    创建测试充值申请数据

    Args:
        ad_account_id: 关联广告账户 ID
        amount: 充值金额
        status: 申请状态（默认 pending）
        requested_by: 申请人 ID
        **kwargs: 其他字段覆盖

    Returns:
        符合 DATA_SCHEMA.md topup_requests 表结构的字典

    SoT Ref:
        - DATA_SCHEMA.md v5.2 第 2.5 节
        - STATE_MACHINE.md v2.6 第 9 章 (Topup 状态机)

    状态枚举:
        pending → approved/rejected → completed/cancelled
    """
    return {
        "id": str(uuid4()),
        "ad_account_id": ad_account_id or str(uuid4()),
        "amount": amount,
        "status": status,
        "requested_by": requested_by or str(uuid4()),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        **kwargs
    }
