#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
对账功能测试
测试自动对账算法、差异检测和处理流程
"""

import pytest
from decimal import Decimal, InvalidOperation
from datetime import date, datetime, timedelta
from typing import List, Dict, Tuple, Optional
import json

from tests.conftest import assert_decimal_equal, pytest_marks


@pytest.mark.integration
@pytest.mark.functional
class TestAutoReconciliation:
    """自动对账功能测试"""

    def test_perfect_match_reconciliation(self, db_session, test_project, test_topup):
        """测试完美匹配的对账"""
        # 创建对应的财务流水
        ledger_entry = {
            "topup_id": test_topup.id,
            "amount": test_topup.amount,
            "status": "pending",
            "transaction_date": date.today()
        }

        # 创建银行对账单记录
        bank_statement = {
            "transaction_id": "BANK_001",
            "amount": test_topup.amount,
            "date": date.today(),
            "description": f"充值-{test_topup.id}"
        }

        result = perform_auto_reconciliation(
            db_session,
            ledger_entries=[ledger_entry],
            bank_statements=[bank_statement]
        )

        assert result["matched_count"] == 1
        assert result["unmatched_ledger_count"] == 0
        assert result["unmatched_bank_count"] == 0
        assert result["discrepancies"] == []

    def test_partial_amount_match(self, db_session, test_project, test_topup):
        """测试部分金额匹配"""
        # 手续费情况：银行扣除了手续费
        ledger_amount = test_topup.amount  # 1000.00
        bank_amount = ledger_amount - Decimal("5.00")  # 995.00

        ledger_entry = {
            "topup_id": test_topup.id,
            "amount": ledger_amount,
            "status": "pending",
            "transaction_date": date.today()
        }

        bank_statement = {
            "transaction_id": "BANK_002",
            "amount": bank_amount,
            "date": date.today(),
            "fee": Decimal("5.00"),
            "description": f"充值-{test_topup.id}"
        }

        result = perform_auto_reconciliation(
            db_session,
            ledger_entries=[ledger_entry],
            bank_statements=[bank_statement],
            tolerance=Decimal("10.00")  # 10元容差
        )

        assert result["matched_count"] == 1
        assert len(result["discrepancies"]) == 1
        assert result["discrepancies"][0]["type"] == "fee_deducted"

    def test_date_mismatch_tolerance(self, db_session, test_topup):
        """测试日期差异容差"""
        yesterday = date.today() - timedelta(days=1)

        ledger_entry = {
            "topup_id": test_topup.id,
            "amount": test_topup.amount,
            "status": "pending",
            "transaction_date": yesterday
        }

        bank_statement = {
            "transaction_id": "BANK_003",
            "amount": test_topup.amount,
            "date": date.today(),
            "description": f"充值-{test_topup.id}"
        }

        result = perform_auto_reconciliation(
            db_session,
            ledger_entries=[ledger_entry],
            bank_statements=[bank_statement],
            date_tolerance_days=2  # 允许2天差异
        )

        assert result["matched_count"] == 1
        assert len(result["discrepancies"]) == 1
        assert result["discrepancies"][0]["type"] == "date_variance"

    def test_multiple_matches_one_transaction(self, db_session):
        """测试一对多匹配（一笔充值对应多笔银行交易）"""
        # 充值2000，分两次到账
        topup_data = {
            "id": "topup_split_001",
            "amount": Decimal("2000.00"),
            "status": "pending"
        }

        ledger_entry = {
            "topup_id": topup_data["id"],
            "amount": topup_data["amount"],
            "status": "pending"
        }

        bank_statements = [
            {
                "transaction_id": "BANK_004_1",
                "amount": Decimal("1000.00"),
                "date": date.today(),
                "description": f"充值-{topup_data['id']}-1"
            },
            {
                "transaction_id": "BANK_004_2",
                "amount": Decimal("1000.00"),
                "date": date.today(),
                "description": f"充值-{topup_data['id']}-2"
            }
        ]

        result = perform_auto_reconciliation(
            db_session,
            ledger_entries=[ledger_entry],
            bank_statements=bank_statements,
            allow_split_matching=True
        )

        assert result["matched_count"] == 1
        assert result["split_matches"] == 1

    def test_no_match_scenario(self, db_session, test_topup):
        """测试无匹配场景"""
        ledger_entry = {
            "topup_id": test_topup.id,
            "amount": Decimal("1000.00"),
            "status": "pending"
        }

        bank_statement = {
            "transaction_id": "BANK_005",
            "amount": Decimal("2000.00"),  # 金额不匹配
            "date": date.today(),
            "description": "其他交易"
        }

        result = perform_auto_reconciliation(
            db_session,
            ledger_entries=[ledger_entry],
            bank_statements=[bank_statement]
        )

        assert result["matched_count"] == 0
        assert result["unmatched_ledger_count"] == 1
        assert result["unmatched_bank_count"] == 1
        assert len(result["discrepancies"]) >= 1

    def test_tolerance_exceeded(self, db_session, test_topup):
        """测试超出容差范围"""
        ledger_amount = test_topup.amount
        bank_amount = ledger_amount - Decimal("100.00")  # 差异100元

        ledger_entry = {
            "topup_id": test_topup.id,
            "amount": ledger_amount,
            "status": "pending"
        }

        bank_statement = {
            "transaction_id": "BANK_006",
            "amount": bank_amount,
            "date": date.today(),
            "description": f"充值-{test_topup.id}"
        }

        result = perform_auto_reconciliation(
            db_session,
            ledger_entries=[ledger_entry],
            bank_statements=[bank_statement],
            tolerance=Decimal("10.00")  # 容差10元
        )

        assert result["matched_count"] == 0
        assert len(result["discrepancies"]) == 1
        assert result["discrepancies"][0]["type"] == "amount_variance_exceeded"


@pytest.mark.integration
@pytest.mark.functional
class TestDiscrepancyHandling:
    """差异处理测试"""

    def test_amount_variance_discrepancy(self, db_session):
        """测试金额差异处理"""
        discrepancy = {
            "type": "amount_variance",
            "ledger_amount": Decimal("1000.00"),
            "bank_amount": Decimal("995.00"),
            "variance": Decimal("5.00"),
            "variance_percentage": Decimal("0.5")
        }

        # 测试自动调整
        result = handle_discrepancy(
            discrepancy,
            action="auto_adjust",
            threshold=Decimal("1.0")  # 1%以下自动调整
        )

        assert result["action_taken"] == "adjusted"
        assert result["adjusted_amount"] == Decimal("995.00")
        assert result["status"] == "resolved"

    def test_fee_deduction_handling(self, db_session):
        """测试手续费扣除处理"""
        discrepancy = {
            "type": "fee_deducted",
            "ledger_amount": Decimal("1000.00"),
            "bank_amount": Decimal("997.00"),
            "fee_amount": Decimal("3.00"),
            "fee_type": "bank_processing_fee"
        }

        result = handle_discrepancy(
            discrepancy,
            action="record_fee",
            fee_account_id="fee_account_001"
        )

        assert result["action_taken"] == "fee_recorded"
        assert result["fee_amount"] == Decimal("3.00")
        assert result["net_matched_amount"] == Decimal("997.00")

    def test_manual_review_required(self, db_session):
        """测试需要人工审核的差异"""
        discrepancy = {
            "type": "amount_variance",
            "ledger_amount": Decimal("1000.00"),
            "bank_amount": Decimal("800.00"),
            "variance": Decimal("200.00"),
            "variance_percentage": Decimal("20.0")  # 20%差异
        }

        result = handle_discrepancy(
            discrepancy,
            action="manual_review",
            threshold=Decimal("5.0")  # 5%以上需要人工审核
        )

        assert result["action_taken"] == "escalated_to_review"
        assert result["review_priority"] == "high"
        assert result["assigned_to"] == "finance_team"

    def test_discrepancy_category_classification(self):
        """测试差异分类"""
        test_cases = [
            {
                "variance_percentage": 0.5,
                "expected_category": "minor"
            },
            {
                "variance_percentage": 2.0,
                "expected_category": "moderate"
            },
            {
                "variance_percentage": 10.0,
                "expected_category": "major"
            },
            {
                "variance_percentage": 50.0,
                "expected_category": "critical"
            }
        ]

        for case in test_cases:
            category = classify_discrepancy(case["variance_percentage"])
            assert category == case["expected_category"]


@pytest.mark.integration
@pytest.mark.functional
class TestReconciliationReports:
    """对账报表测试"""

    def test_daily_reconciliation_summary(self, db_session):
        """测试日对账汇总"""
        # 模拟一天的对账结果
        reconciliation_data = {
            "date": date.today(),
            "total_transactions": 100,
            "matched": 95,
            "unmatched": 5,
            "total_amount": Decimal("50000.00"),
            "matched_amount": Decimal("47500.00"),
            "discrepancies": [
                {
                    "type": "fee_deducted",
                    "count": 3,
                    "total_variance": Decimal("15.00")
                },
                {
                    "type": "amount_variance",
                    "count": 2,
                    "total_variance": Decimal("100.00")
                }
            ]
        }

        report = generate_daily_reconciliation_report(reconciliation_data)

        assert report["match_rate"] == 95.0  # 95%
        assert report["variance_rate"] == 0.23  # 115/50000 * 100
        assert report["status"] == "excellent"  # >95%匹配率

    def test_monthly_reconciliation_trend(self, db_session):
        """测试月度对账趋势"""
        monthly_data = [
            {"month": "2025-01", "match_rate": 98.5, "variance_rate": 0.15},
            {"month": "2025-02", "match_rate": 97.2, "variance_rate": 0.28},
            {"month": "2025-03", "match_rate": 99.1, "variance_rate": 0.09}
        ]

        trend_report = analyze_monthly_reconciliation_trend(monthly_data)

        assert trend_report["avg_match_rate"] == 98.27
        assert trend_report["match_rate_trend"] == "improving"
        assert trend_report["best_month"] == "2025-03"
        assert trend_report["worst_month"] == "2025-02"

    def test_discrepancy_detail_report(self, db_session):
        """测试差异详细报表"""
        discrepancies = [
            {
                "id": "disc_001",
                "topup_id": "topup_001",
                "ledger_amount": Decimal("1000.00"),
                "bank_amount": Decimal("995.00"),
                "variance": Decimal("5.00"),
                "type": "fee_deducted",
                "status": "resolved",
                "resolved_at": datetime.now(),
                "resolved_by": "auto_system"
            },
            {
                "id": "disc_002",
                "topup_id": "topup_002",
                "ledger_amount": Decimal("2000.00"),
                "bank_amount": None,
                "variance": Decimal("2000.00"),
                "type": "missing_bank_record",
                "status": "pending_review",
                "escalated_at": datetime.now(),
                "assigned_to": "finance_team"
            }
        ]

        report = generate_discrepancy_detail_report(discrepancies)

        assert report["total_discrepancies"] == 2
        assert report["resolved_count"] == 1
        assert report["pending_count"] == 1
        assert report["total_variance_amount"] == Decimal("2005.00")


@pytest.mark.integration
@pytest.mark.functional
class TestReconciliationWorkflow:
    """对账工作流测试"""

    def test_automatic_reconciliation_workflow(self, db_session):
        """测试自动对账工作流"""
        # 步骤1：获取未对账的记录
        pending_entries = get_pending_reconciliation_entries(db_session)
        assert len(pending_entries) > 0

        # 步骤2：获取银行对账单
        bank_statements = fetch_bank_statements(date.today() - timedelta(days=1))
        assert len(bank_statements) > 0

        # 步骤3：执行自动对账
        reconciliation_result = perform_auto_reconciliation(
            db_session,
            pending_entries,
            bank_statements
        )

        # 步骤4：处理差异
        for discrepancy in reconciliation_result["discrepancies"]:
            handle_result = handle_discrepancy(discrepancy, "auto_process")
            assert handle_result is not None

        # 步骤5：生成对账报告
        report = generate_reconciliation_report(reconciliation_result)
        assert report is not None

        # 验证工作流完成
        assert reconciliation_result["processed_count"] > 0

    def test_manual_override_workflow(self, db_session):
        """测试人工干预工作流"""
        # 创建需要人工审核的案例
        manual_case = {
            "entry_id": "manual_001",
            "amount": Decimal("10000.00"),
            "bank_records": [
                {"id": "bank_001", "amount": Decimal("8000.00")},
                {"id": "bank_002", "amount": Decimal("1500.00")}
            ],
            "total_bank_amount": Decimal("9500.00"),
            "variance": Decimal("500.00")
        }

        # 提交人工审核
        review_request = submit_for_manual_review(manual_case, reason="amount_variance_exceeds_threshold")

        assert review_request["status"] == "pending_review"
        assert review_request["assigned_to"] is not None

        # 模拟人工审核决定
        review_decision = {
            "request_id": review_request["id"],
            "decision": "adjust_ledger",
            "adjusted_amount": Decimal("9500.00"),
            "notes": "银行记录显示实际到账9500元，调整账面记录",
            "reviewer": "finance_manager_001"
        }

        # 执行人工审核决定
        result = execute_manual_decision(review_decision)

        assert result["success"] is True
        assert result["adjusted_amount"] == Decimal("9500.00")
        assert result["status"] == "resolved"

    def test_reconciliation_exception_handling(self, db_session):
        """测试对账异常处理"""
        # 测试数据完整性异常
        invalid_entry = {
            "id": None,  # 无效ID
            "amount": None,  # 无效金额
            "date": "invalid-date"  # 无效日期
        }

        with pytest.raises(ValidationError):
            validate_reconciliation_entry(invalid_entry)

        # 测试并发冲突
        entry_id = "concurrent_test_001"

        # 模拟并发更新
        session1 = db_session
        session2 = create_new_session()  # 创建新会话模拟并发

        # 会话1开始处理
        entry1 = session1.query(Ledger).filter(Ledger.id == entry_id).first()
        entry1.status = "processing"
        session1.commit()

        # 会话2尝试同时处理
        entry2 = session2.query(Ledger).filter(Ledger.id == entry_id).first()

        # 应该检测到并发冲突
        with pytest.raises(ConcurrentUpdateError):
            entry2.status = "matched"
            session2.commit()


@pytest.mark.integration
@pytest.mark.functional
class TestReconciliationPerformance:
    """对账性能测试"""

    @pytest.mark.slow
    def test_large_volume_reconciliation(self, db_session):
        """测试大批量对账性能"""
        # 创建10000条测试数据
        ledger_entries = []
        bank_statements = []

        for i in range(10000):
            ledger_entries.append({
                "id": f"ledger_{i}",
                "amount": Decimal("1000.00") + (i % 100),
                "date": date.today() - timedelta(days=i % 30),
                "status": "pending"
            })

            bank_statements.append({
                "id": f"bank_{i}",
                "amount": Decimal("1000.00") + (i % 100),
                "date": date.today() - timedelta(days=i % 30),
                "reference": f"ledger_{i}"
            })

        # 测量对账时间
        start_time = datetime.now()

        result = perform_auto_reconciliation(
            db_session,
            ledger_entries,
            bank_statements,
            batch_size=1000  # 批处理
        )

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # 性能断言
        assert result["matched_count"] == 10000
        assert processing_time < 120  # 2分钟内完成
        assert processing_time < 0.01 * 10000  # 每条记录少于0.01秒

    @pytest.mark.slow
    def test_concurrent_reconciliation(self, db_session):
        """测试并发对账性能"""
        import threading
        from queue import Queue

        results = Queue()

        def reconciliation_worker(batch_data):
            result = perform_auto_reconciliation(
                db_session,
                batch_data["ledger_entries"],
                batch_data["bank_statements"]
            )
            results.put(result)

        # 创建5个并发线程
        threads = []
        for i in range(5):
            batch_data = {
                "ledger_entries": [
                    {"id": f"concurrent_{i}_{j}", "amount": Decimal("1000.00")}
                    for j in range(1000)
                ],
                "bank_statements": [
                    {"id": f"bank_{i}_{j}", "amount": Decimal("1000.00")}
                    for j in range(1000)
                ]
            }

            thread = threading.Thread(target=reconciliation_worker, args=(batch_data,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 汇总结果
        total_matched = 0
        while not results.empty():
            result = results.get()
            total_matched += result["matched_count"]

        assert total_matched == 5000  # 5个线程 × 1000条记录


# 辅助函数和类（这些应该在实际的对账模块中实现）
def perform_auto_reconciliation(db_session, ledger_entries, bank_statements, **kwargs):
    """执行自动对账"""
    return {
        "matched_count": 0,
        "unmatched_ledger_count": 0,
        "unmatched_bank_count": 0,
        "discrepancies": [],
        "split_matches": 0,
        "processed_count": 0
    }

def handle_discrepancy(discrepancy, action, **kwargs):
    """处理对账差异"""
    return {
        "action_taken": "none",
        "status": "pending"
    }

def classify_discrepancy(variance_percentage):
    """分类差异严重程度"""
    if variance_percentage < 1:
        return "minor"
    elif variance_percentage < 5:
        return "moderate"
    elif variance_percentage < 20:
        return "major"
    else:
        return "critical"

def generate_daily_reconciliation_report(data):
    """生成日对账报表"""
    match_rate = (data["matched"] / data["total_transactions"]) * 100
    variance_rate = (sum(d["total_variance"] for d in data["discrepancies"]) / data["total_amount"]) * 100

    status = "excellent" if match_rate >= 95 else "good" if match_rate >= 90 else "needs_attention"

    return {
        "match_rate": match_rate,
        "variance_rate": variance_rate,
        "status": status
    }

def analyze_monthly_reconciliation_trend(monthly_data):
    """分析月度对账趋势"""
    avg_match_rate = sum(m["match_rate"] for m in monthly_data) / len(monthly_data)

    best_month = max(monthly_data, key=lambda x: x["match_rate"])["month"]
    worst_month = min(monthly_data, key=lambda x: x["match_rate"])["month"]

    # 简单的趋势判断
    if monthly_data[-1]["match_rate"] > monthly_data[0]["match_rate"]:
        trend = "improving"
    elif monthly_data[-1]["match_rate"] < monthly_data[0]["match_rate"]:
        trend = "declining"
    else:
        trend = "stable"

    return {
        "avg_match_rate": round(avg_match_rate, 2),
        "match_rate_trend": trend,
        "best_month": best_month,
        "worst_month": worst_month
    }

def generate_discrepancy_detail_report(discrepancies):
    """生成差异详细报表"""
    resolved = [d for d in discrepancies if d["status"] == "resolved"]
    pending = [d for d in discrepancies if d["status"] == "pending_review"]

    total_variance = sum(d["variance"] for d in discrepancies if d.get("variance"))

    return {
        "total_discrepancies": len(discrepancies),
        "resolved_count": len(resolved),
        "pending_count": len(pending),
        "total_variance_amount": total_variance
    }

def get_pending_reconciliation_entries(db_session):
    """获取待对账记录"""
    return []

def fetch_bank_statements(date):
    """获取银行对账单"""
    return []

def generate_reconciliation_report(result):
    """生成对账报告"""
    return {"summary": "test"}

def submit_for_manual_review(case, reason):
    """提交人工审核"""
    return {
        "id": "review_001",
        "status": "pending_review",
        "assigned_to": "finance_team"
    }

def execute_manual_decision(decision):
    """执行人工审核决定"""
    return {
        "success": True,
        "status": "resolved"
    }

class ValidationError(Exception):
    pass

class ConcurrentUpdateError(Exception):
    pass

def validate_reconciliation_entry(entry):
    """验证对账条目"""
    if entry.get("id") is None:
        raise ValidationError("Invalid entry ID")
    if entry.get("amount") is None:
        raise ValidationError("Invalid amount")
    return True

def create_new_session():
    """创建新的数据库会话"""
    return None