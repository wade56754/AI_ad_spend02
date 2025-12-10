"""
趋势风控服务
Version: 1.0
Author: Claude协作开发

SoT References:
- STATE_MACHINE.md v2.6 第8.3节 (TF-001/002/003 风控规则)
- DATA_SCHEMA.md v5.2 (daily_reports 表结构)
- ERROR_CODES_SOT.md v2.1 (错误码)

实现三大风控规则的自动检测和标记：
- TF-001: 粉数骤降检查 (conversions_raw < 昨日最大值 × 0.5)
- TF-002: 粉数骤增检查 (conversions_raw > 昨日最大值 × 3)
- TF-003: 消耗异常检查 (raw_spend > 昨日 × 2)
"""

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from backend.models import DailyReport
from backend.models.base import DailyReportStatus

logger = logging.getLogger(__name__)


class TrendRiskRule(str, Enum):
    """趋势风控规则枚举 (STATE_MACHINE.md v2.6 第8.3节)"""
    TF_001 = "TF-001"  # 粉数骤降检查
    TF_002 = "TF-002"  # 粉数骤增检查
    TF_003 = "TF-003"  # 消耗异常检查


@dataclass
class TrendRiskCheckResult:
    """风控检查结果"""
    passed: bool  # True = 通过, False = 触发异常
    triggered_rules: List[TrendRiskRule]  # 触发的规则列表
    details: Dict[str, Any]  # 详细信息
    trend_flag_reason: Optional[str] = None  # 异常原因描述

    @property
    def should_flag(self) -> bool:
        """是否应该标记为 trend_flagged"""
        return not self.passed and len(self.triggered_rules) > 0


@dataclass
class TrendRiskThresholds:
    """风控阈值配置 (STATE_MACHINE.md v2.6 第8.3节)"""
    # TF-001: 粉数骤降阈值 (小于昨日的 50%)
    conversions_drop_threshold: float = 0.5
    # TF-002: 粉数骤增阈值 (大于昨日的 300%)
    conversions_spike_threshold: float = 3.0
    # TF-003: 消耗异常阈值 (大于昨日的 200%)
    spend_spike_threshold: float = 2.0


class TrendRiskControlService:
    """
    趋势风控服务类

    负责实现 STATE_MACHINE.md v2.6 第8.3节定义的三大风控规则：
    - TF-001: 粉数骤降检查
    - TF-002: 粉数骤增检查
    - TF-003: 消耗异常检查
    """

    def __init__(
        self,
        db: Session,
        thresholds: Optional[TrendRiskThresholds] = None
    ):
        self.db = db
        self.thresholds = thresholds or TrendRiskThresholds()

    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        try:
            yield
            self.db.commit()
            logger.debug("Transaction committed successfully")
        except Exception as e:
            logger.error(f"Transaction failed, rolling back: {str(e)}", exc_info=True)
            self.db.rollback()
            raise

    def check_trend_risk(
        self,
        report: DailyReport
    ) -> TrendRiskCheckResult:
        """
        执行趋势风控检查

        基于 STATE_MACHINE.md v2.6 第8.3节的规则定义

        Args:
            report: 待检查的日报对象

        Returns:
            TrendRiskCheckResult: 检查结果
        """
        logger.info(
            f"Checking trend risk for report: id={report.id}, "
            f"ad_account_id={report.ad_account_id}, date={report.report_date}"
        )

        # 获取昨日数据用于对比
        yesterday_data = self._get_yesterday_data(
            ad_account_id=report.ad_account_id,
            report_date=report.report_date
        )

        triggered_rules: List[TrendRiskRule] = []
        details: Dict[str, Any] = {
            "report_id": report.id,
            "report_date": str(report.report_date),
            "ad_account_id": report.ad_account_id,
            "conversions_raw": report.conversions_raw,
            "raw_spend": float(report.raw_spend or 0),
            "yesterday_data": None,
            "checks": {}
        }

        # 如果没有昨日数据，视为通过 (STATE_MACHINE.md: 如果昨日无数据，则不触发风控)
        if not yesterday_data:
            logger.info(
                f"No yesterday data for report {report.id}, skipping trend risk check"
            )
            details["yesterday_data"] = None
            details["skip_reason"] = "no_yesterday_data"
            return TrendRiskCheckResult(
                passed=True,
                triggered_rules=[],
                details=details,
                trend_flag_reason=None
            )

        details["yesterday_data"] = {
            "conversions_raw": yesterday_data.conversions_raw,
            "raw_spend": float(yesterday_data.raw_spend or 0)
        }

        # ====== TF-001: 粉数骤降检查 ======
        tf001_result = self._check_tf001(report, yesterday_data)
        details["checks"]["TF-001"] = tf001_result
        if tf001_result["triggered"]:
            triggered_rules.append(TrendRiskRule.TF_001)

        # ====== TF-002: 粉数骤增检查 ======
        tf002_result = self._check_tf002(report, yesterday_data)
        details["checks"]["TF-002"] = tf002_result
        if tf002_result["triggered"]:
            triggered_rules.append(TrendRiskRule.TF_002)

        # ====== TF-003: 消耗异常检查 ======
        tf003_result = self._check_tf003(report, yesterday_data)
        details["checks"]["TF-003"] = tf003_result
        if tf003_result["triggered"]:
            triggered_rules.append(TrendRiskRule.TF_003)

        # 构建结果
        passed = len(triggered_rules) == 0
        trend_flag_reason = None

        if not passed:
            # 构建异常原因描述
            reasons = []
            for rule in triggered_rules:
                check_detail = details["checks"].get(rule.value, {})
                reasons.append(f"{rule.value}: {check_detail.get('reason', 'unknown')}")
            trend_flag_reason = "; ".join(reasons)

        logger.info(
            f"Trend risk check completed for report {report.id}: "
            f"passed={passed}, triggered_rules={[r.value for r in triggered_rules]}"
        )

        return TrendRiskCheckResult(
            passed=passed,
            triggered_rules=triggered_rules,
            details=details,
            trend_flag_reason=trend_flag_reason
        )

    def _check_tf001(
        self,
        report: DailyReport,
        yesterday_data: DailyReport
    ) -> Dict[str, Any]:
        """
        TF-001: 粉数骤降检查

        规则: conversions_raw < 昨日最大值 × 0.5
        触发: 粉数下降超过 50%
        """
        current = report.conversions_raw or 0
        yesterday = yesterday_data.conversions_raw or 0

        # 计算阈值
        threshold = yesterday * self.thresholds.conversions_drop_threshold

        triggered = False
        reason = ""

        if yesterday > 0 and current < threshold:
            triggered = True
            drop_pct = ((yesterday - current) / yesterday) * 100
            reason = f"粉数骤降 {drop_pct:.1f}%"
            logger.warning(
                f"TF-001 triggered: report={report.id}, "
                f"current={current}, yesterday={yesterday}, drop={drop_pct:.1f}%"
            )
        else:
            reason = "粉数正常"

        return {
            "triggered": triggered,
            "current_value": current,
            "yesterday_value": yesterday,
            "threshold": threshold,
            "threshold_pct": self.thresholds.conversions_drop_threshold * 100,
            "reason": reason
        }

    def _check_tf002(
        self,
        report: DailyReport,
        yesterday_data: DailyReport
    ) -> Dict[str, Any]:
        """
        TF-002: 粉数骤增检查

        规则: conversions_raw > 昨日最大值 × 3
        触发: 粉数增长超过 300%
        """
        current = report.conversions_raw or 0
        yesterday = yesterday_data.conversions_raw or 0

        # 计算阈值
        threshold = yesterday * self.thresholds.conversions_spike_threshold

        triggered = False
        reason = ""

        if yesterday > 0 and current > threshold:
            triggered = True
            increase_pct = ((current - yesterday) / yesterday) * 100
            reason = f"粉数骤增 {increase_pct:.1f}%"
            logger.warning(
                f"TF-002 triggered: report={report.id}, "
                f"current={current}, yesterday={yesterday}, increase={increase_pct:.1f}%"
            )
        else:
            reason = "粉数增幅正常"

        return {
            "triggered": triggered,
            "current_value": current,
            "yesterday_value": yesterday,
            "threshold": threshold,
            "threshold_pct": self.thresholds.conversions_spike_threshold * 100,
            "reason": reason
        }

    def _check_tf003(
        self,
        report: DailyReport,
        yesterday_data: DailyReport
    ) -> Dict[str, Any]:
        """
        TF-003: 消耗异常检查

        规则: raw_spend > 昨日 × 2
        触发: 消耗增长超过 200%
        """
        current = float(report.raw_spend or 0)
        yesterday = float(yesterday_data.raw_spend or 0)

        # 计算阈值
        threshold = yesterday * self.thresholds.spend_spike_threshold

        triggered = False
        reason = ""

        if yesterday > 0 and current > threshold:
            triggered = True
            increase_pct = ((current - yesterday) / yesterday) * 100
            reason = f"消耗异常增长 {increase_pct:.1f}%"
            logger.warning(
                f"TF-003 triggered: report={report.id}, "
                f"current={current}, yesterday={yesterday}, increase={increase_pct:.1f}%"
            )
        else:
            reason = "消耗正常"

        return {
            "triggered": triggered,
            "current_value": current,
            "yesterday_value": yesterday,
            "threshold": threshold,
            "threshold_pct": self.thresholds.spend_spike_threshold * 100,
            "reason": reason
        }

    def _get_yesterday_data(
        self,
        ad_account_id: int,
        report_date: date
    ) -> Optional[DailyReport]:
        """
        获取昨日的日报数据

        Args:
            ad_account_id: 广告账户ID
            report_date: 当前日报日期

        Returns:
            Optional[DailyReport]: 昨日日报或 None
        """
        yesterday = report_date - timedelta(days=1)

        return self.db.query(DailyReport).filter(
            and_(
                DailyReport.ad_account_id == ad_account_id,
                DailyReport.report_date == yesterday
            )
        ).first()

    def execute_trend_check(
        self,
        report_id: int
    ) -> Tuple[DailyReport, TrendRiskCheckResult]:
        """
        执行趋势风控检查并更新日报状态

        状态流转 (STATE_MACHINE.md v2.6 第8章):
        - raw_submitted → trend_pending → trend_ok (通过)
        - raw_submitted → trend_pending → trend_flagged (触发)

        Args:
            report_id: 日报ID

        Returns:
            Tuple[DailyReport, TrendRiskCheckResult]: 更新后的日报和检查结果
        """
        logger.info(f"Executing trend check for report: {report_id}")

        # 获取日报
        report = self.db.query(DailyReport).filter(
            DailyReport.id == report_id
        ).first()

        if not report:
            raise ValueError(f"日报 {report_id} 不存在")

        # 验证状态 - 只能从 trend_pending 执行风控检查
        if report.status != DailyReportStatus.TREND_PENDING.value:
            raise ValueError(
                f"日报状态必须为 trend_pending，当前状态: {report.status}"
            )

        # 执行风控检查
        result = self.check_trend_risk(report)

        with self.transaction():
            if result.should_flag:
                # 触发异常 → trend_flagged
                report.status = DailyReportStatus.TREND_FLAGGED.value
                report.trend_flag = "flagged"
                report.trend_flag_reason = result.trend_flag_reason
                logger.info(
                    f"Report {report_id} flagged: {result.trend_flag_reason}"
                )
            else:
                # 通过 → trend_ok
                report.status = DailyReportStatus.TREND_OK.value
                report.trend_flag = "normal"
                logger.info(f"Report {report_id} passed trend check")

            report.version += 1

        return report, result

    def batch_execute_trend_check(
        self,
        report_ids: Optional[List[int]] = None,
        ad_account_id: Optional[int] = None,
        report_date: Optional[date] = None
    ) -> List[Tuple[int, bool, Optional[str]]]:
        """
        批量执行趋势风控检查

        Args:
            report_ids: 指定的日报ID列表 (可选)
            ad_account_id: 广告账户ID筛选 (可选)
            report_date: 报告日期筛选 (可选)

        Returns:
            List[Tuple[int, bool, str]]: [(report_id, passed, error_message), ...]
        """
        results: List[Tuple[int, bool, Optional[str]]] = []

        # 构建查询
        query = self.db.query(DailyReport).filter(
            DailyReport.status == DailyReportStatus.TREND_PENDING.value
        )

        if report_ids:
            query = query.filter(DailyReport.id.in_(report_ids))
        if ad_account_id:
            query = query.filter(DailyReport.ad_account_id == ad_account_id)
        if report_date:
            query = query.filter(DailyReport.report_date == report_date)

        reports = query.all()
        logger.info(f"Batch trend check: found {len(reports)} reports to check")

        for report in reports:
            try:
                _, check_result = self.execute_trend_check(report.id)
                results.append((report.id, check_result.passed, None))
            except Exception as e:
                logger.error(
                    f"Error checking report {report.id}: {str(e)}", exc_info=True
                )
                results.append((report.id, False, str(e)))

        return results

    def trigger_trend_check_for_new_report(
        self,
        report: DailyReport
    ) -> DailyReport:
        """
        为新提交的日报触发趋势检查

        状态流转: raw_submitted → trend_pending

        Args:
            report: 新提交的日报对象

        Returns:
            DailyReport: 更新后的日报对象
        """
        if report.status != DailyReportStatus.RAW_SUBMITTED.value:
            raise ValueError(
                f"只能从 raw_submitted 状态触发风控检查，当前状态: {report.status}"
            )

        with self.transaction():
            report.status = DailyReportStatus.TREND_PENDING.value
            report.version += 1
            logger.info(f"Report {report.id} transitioned to trend_pending")

        return report

    def get_pending_trend_check_count(self) -> int:
        """获取待风控检查的日报数量"""
        return self.db.query(func.count(DailyReport.id)).filter(
            DailyReport.status == DailyReportStatus.TREND_PENDING.value
        ).scalar() or 0

    def get_flagged_reports(
        self,
        ad_account_id: Optional[int] = None,
        report_date_start: Optional[date] = None,
        report_date_end: Optional[date] = None,
        limit: int = 100
    ) -> List[DailyReport]:
        """
        获取已标记异常的日报列表

        Args:
            ad_account_id: 广告账户ID筛选 (可选)
            report_date_start: 开始日期 (可选)
            report_date_end: 结束日期 (可选)
            limit: 返回数量限制

        Returns:
            List[DailyReport]: 异常日报列表
        """
        query = self.db.query(DailyReport).filter(
            DailyReport.status == DailyReportStatus.TREND_FLAGGED.value
        )

        if ad_account_id:
            query = query.filter(DailyReport.ad_account_id == ad_account_id)
        if report_date_start:
            query = query.filter(DailyReport.report_date >= report_date_start)
        if report_date_end:
            query = query.filter(DailyReport.report_date <= report_date_end)

        return query.order_by(DailyReport.report_date.desc()).limit(limit).all()
