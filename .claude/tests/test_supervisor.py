#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监工系统集成测试

测试所有监工模块的功能。

运行测试:
    cd .claude && python -m pytest tests/test_supervisor.py -v

或者直接运行:
    python .claude/tests/test_supervisor.py
"""

import json
import sys
import tempfile
from datetime import datetime, date
from pathlib import Path
from typing import Generator

import pytest

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))

from lib.config import (
    Config,
    get_config,
    get_sot_versions,
    get_valid_roles,
    is_valid_role,
    is_valid_state,
    is_valid_state_transition,
    reload_config,
)
from lib.progress_tracker import (
    ProgressTracker,
    TaskStatus,
    Task,
    Module,
    get_tracker,
    reset_tracker,
)
from lib.compliance_checker import (
    ComplianceChecker,
    ViolationType,
    Severity,
    Violation,
    check_code,
    is_compliant,
)
from lib.risk_detector import (
    RiskDetector,
    RiskLevel,
    RiskType,
    Risk,
    detect_risks,
)
from lib.report_generator import (
    ReportGenerator,
    generate_daily_report,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def fresh_config() -> Config:
    """获取新加载的配置"""
    return reload_config()


@pytest.fixture
def tracker() -> ProgressTracker:
    """获取新的进度追踪器"""
    t = ProgressTracker()
    t.load_tasks()
    return t


@pytest.fixture
def checker() -> ComplianceChecker:
    """获取新的合规检查器"""
    return ComplianceChecker()


@pytest.fixture
def detector(tracker: ProgressTracker, checker: ComplianceChecker) -> RiskDetector:
    """获取新的风险检测器"""
    return RiskDetector(tracker=tracker, checker=checker)


@pytest.fixture
def generator(tracker: ProgressTracker) -> ReportGenerator:
    """获取新的报告生成器"""
    return ReportGenerator(tracker=tracker)


# =============================================================================
# 配置模块测试
# =============================================================================

class TestConfig:
    """配置模块测试"""

    def test_config_load(self, fresh_config: Config):
        """测试配置加载"""
        assert fresh_config is not None
        assert fresh_config.source in ["file", "default"]

    def test_sot_versions(self, fresh_config: Config):
        """测试 SoT 版本"""
        versions = fresh_config.sot_versions
        assert "MASTER.md" in versions
        assert "API_SOT.md" in versions
        assert "DATA_SCHEMA.md" in versions
        assert versions["MASTER.md"] == "v4.4"

    def test_valid_roles(self, fresh_config: Config):
        """测试有效角色"""
        roles = fresh_config.valid_roles
        assert len(roles) == 7
        assert "ceo" in roles
        assert "pitcher" in roles
        assert "admin" in roles
        # 确保旧角色不在列表中
        assert "operator" not in roles
        assert "manager" not in roles

    def test_is_valid_role(self):
        """测试角色验证函数"""
        assert is_valid_role("pitcher") is True
        assert is_valid_role("ceo") is True
        assert is_valid_role("operator") is False
        assert is_valid_role("unknown") is False

    def test_is_valid_state(self):
        """测试状态验证函数"""
        assert is_valid_state("raw_submitted") is True
        assert is_valid_state("final_locked") is True
        assert is_valid_state("draft") is False
        assert is_valid_state("approved") is False

    def test_state_transitions(self):
        """测试状态转换验证"""
        # 有效转换
        assert is_valid_state_transition("raw_submitted", "trend_pending") is True
        assert is_valid_state_transition("trend_pending", "trend_ok") is True
        assert is_valid_state_transition("final_confirmed", "final_locked") is True

        # 无效转换
        assert is_valid_state_transition("raw_submitted", "final_locked") is False
        assert is_valid_state_transition("final_locked", "raw_submitted") is False

    def test_forbidden_patterns(self, fresh_config: Config):
        """测试禁止模式"""
        patterns = fresh_config.forbidden_patterns
        assert len(patterns) > 0
        assert "direct_balance_modify" in patterns
        assert "auto_block" in patterns


# =============================================================================
# 进度追踪器测试
# =============================================================================

class TestProgressTracker:
    """进度追踪器测试"""

    def test_load_tasks(self, tracker: ProgressTracker):
        """测试任务加载"""
        assert tracker.is_loaded is True
        assert len(tracker.modules) == 11
        assert len(tracker.tasks) >= 20

    def test_module_structure(self, tracker: ProgressTracker):
        """测试模块结构"""
        assert "A1" in tracker.modules
        assert "B1" in tracker.modules
        assert "D1" in tracker.modules

        a1 = tracker.modules["A1"]
        assert a1.name == "运营驾驶舱"
        assert a1.task_count >= 2

    def test_task_status(self, tracker: ProgressTracker):
        """测试任务状态"""
        task = tracker.get_task("A1-001")
        assert task is not None
        assert task.status in TaskStatus

    def test_update_task(self, tracker: ProgressTracker):
        """测试任务更新"""
        task = tracker.update_task("A2-002", progress=50)
        assert task is not None
        assert task.progress == 50
        assert task.status == TaskStatus.IN_PROGRESS

    def test_complete_task(self, tracker: ProgressTracker):
        """测试任务完成"""
        task = tracker.complete_task("B3-001")
        assert task is not None
        assert task.progress == 100
        assert task.status == TaskStatus.COMPLETED

    def test_module_progress(self, tracker: ProgressTracker):
        """测试模块进度计算"""
        progress = tracker.get_module_progress("A1")
        assert 0 <= progress <= 100

    def test_overall_progress(self, tracker: ProgressTracker):
        """测试整体进度计算"""
        progress = tracker.get_overall_progress()
        assert 0 <= progress <= 100

    def test_tasks_by_status(self, tracker: ProgressTracker):
        """测试按状态筛选任务"""
        completed = tracker.get_tasks_by_status(TaskStatus.COMPLETED)
        assert isinstance(completed, list)

        in_progress = tracker.get_tasks_by_status("in_progress")
        assert isinstance(in_progress, list)


# =============================================================================
# 合规检查器测试
# =============================================================================

class TestComplianceChecker:
    """合规检查器测试"""

    def test_sot_version_outdated(self, checker: ComplianceChecker):
        """测试 SoT 版本过时检测"""
        content = """
        # 参考文档
        基于 DATA_SCHEMA.md v5.1 实现
        """
        result = checker.check_content("test.py", content)
        # 应该检测到版本不匹配
        version_violations = [
            v for v in result.violations
            if v.type == ViolationType.SOT_VERSION_MISMATCH
        ]
        assert len(version_violations) > 0

    def test_invalid_role_detection(self, checker: ComplianceChecker):
        """测试无效角色检测"""
        content = '''
        def check_permission(user):
            if user.role == "operator":
                return False
        '''
        result = checker.check_content("test.py", content)
        role_violations = [
            v for v in result.violations
            if v.type == ViolationType.INVALID_ROLE
        ]
        assert len(role_violations) > 0

    def test_valid_role_passes(self, checker: ComplianceChecker):
        """测试有效角色通过"""
        content = '''
        def check_permission(user):
            if user.role == "pitcher":
                return True
        '''
        result = checker.check_content("test.py", content)
        role_violations = [
            v for v in result.violations
            if v.type == ViolationType.INVALID_ROLE
        ]
        assert len(role_violations) == 0

    def test_phase2_violation(self, checker: ComplianceChecker):
        """测试 Phase 2 功能检测"""
        content = '''
        def process_report(report):
            if report.is_invalid:
                auto_reject(report)
        '''
        result = checker.check_content("test.py", content)
        phase2_violations = [
            v for v in result.violations
            if v.type == ViolationType.PHASE2_VIOLATION
        ]
        assert len(phase2_violations) > 0

    def test_balance_modification(self, checker: ComplianceChecker):
        """测试直接修改余额检测"""
        content = '''
        def deduct_spend(account, amount):
            account.balance -= amount
        '''
        result = checker.check_content("test.py", content)
        forbidden_violations = [
            v for v in result.violations
            if v.type == ViolationType.FORBIDDEN_PATTERN
        ]
        assert len(forbidden_violations) > 0

    def test_old_status_detection(self, checker: ComplianceChecker):
        """测试旧状态名检测"""
        content = '''
        def check_report(report):
            if report.status == "draft":
                return "pending"
        '''
        result = checker.check_content("test.py", content)
        # 应检测到使用旧状态名
        assert result.has_violations

    def test_compliant_code_passes(self, checker: ComplianceChecker):
        """测试合规代码通过"""
        content = '''
        def update_report_status(report, status):
            """更新日报状态（使用 8 状态机）"""
            if status == "raw_submitted":
                report.status = status
                create_ledger_entry(report)  # 通过账本记录
        '''
        result = checker.check_content("test.py", content)
        # 应该没有严重违规
        assert result.passed or len(checker.get_critical_violations()) == 0

    def test_check_code_function(self):
        """测试便捷检查函数"""
        violations = check_code('account.balance = 100', "test.py")
        assert len(violations) > 0

    def test_is_compliant_function(self):
        """测试合规检查函数"""
        assert is_compliant('def hello(): pass') is True
        assert is_compliant('account.balance -= 100') is False


# =============================================================================
# 风险检测器测试
# =============================================================================

class TestRiskDetector:
    """风险检测器测试"""

    def test_detect_all(self, detector: RiskDetector):
        """测试运行所有检测"""
        result = detector.detect_all()
        assert result is not None
        assert isinstance(result.risks, list)

    def test_blocked_task_detection(self, detector: RiskDetector):
        """测试阻塞任务检测"""
        # 设置一些阻塞任务
        detector.tracker.update_task("E1-001", status=TaskStatus.BLOCKED)
        detector.tracker.update_task("E1-002", status=TaskStatus.BLOCKED)
        detector.tracker.update_task("E1-003", status=TaskStatus.BLOCKED)

        detector.detect_all()
        blocked_risks = detector.get_risks_by_type(RiskType.BLOCKED_TASK)
        assert len(blocked_risks) > 0

    def test_progress_lag_detection(self, detector: RiskDetector):
        """测试进度落后检测"""
        detector.detect_all()
        lag_risks = detector.get_risks_by_type(RiskType.PROGRESS_LAG)
        # 根据任务定义，应该有一些落后的模块
        assert isinstance(lag_risks, list)

    def test_compliance_risk_detection(self, detector: RiskDetector):
        """测试合规风险检测"""
        # 添加一些违规
        detector.checker.check_content("bad.py", "account.balance -= 100")

        detector.detect_all()
        compliance_risks = detector.get_risks_by_type(RiskType.COMPLIANCE)
        assert len(compliance_risks) > 0

    def test_risk_levels(self, detector: RiskDetector):
        """测试风险级别"""
        detector.detect_all()

        for level in RiskLevel:
            risks = detector.get_risks_by_level(level)
            assert isinstance(risks, list)

    def test_risk_summary(self, detector: RiskDetector):
        """测试风险摘要"""
        detector.detect_all()
        summary = detector.get_summary()

        assert "total" in summary
        assert "by_level" in summary
        assert "by_type" in summary


# =============================================================================
# 报告生成器测试
# =============================================================================

class TestReportGenerator:
    """报告生成器测试"""

    def test_generate_daily(self, generator: ReportGenerator):
        """测试日报生成"""
        content = generator.generate_daily()

        assert "# 项目进度日报" in content
        assert "## 📊 进度概览" in content
        assert "## 📦 模块进度" in content
        assert "## 🚨 风险预警" in content

    def test_generate_weekly(self, generator: ReportGenerator):
        """测试周报生成"""
        content = generator.generate_weekly()

        assert "# 项目进度周报" in content
        assert "## 📊 进度概览" in content
        assert "## 🎯 本周完成" in content
        assert "## 📋 下周计划" in content

    def test_generate_session(self, generator: ReportGenerator):
        """测试会话报告生成"""
        session_data = {
            "session_id": "test-123",
            "start_time": "2025-01-01T10:00:00",
            "end_time": "2025-01-01T12:00:00",
            "duration": "2h",
            "files_modified": ["file1.py", "file2.ts"],
            "tools_used": {"Write": 5, "Edit": 3},
            "modules_touched": ["A1", "B1"],
            "overall_progress": 50,
        }
        content = generator.generate_session(session_data)

        assert "# 会话报告" in content
        assert "test-123" in content
        assert "file1.py" in content

    def test_save_report(self, generator: ReportGenerator, tmp_path: Path):
        """测试报告保存"""
        content = "# Test Report\n\nTest content"

        # 使用临时目录
        original_dir = generator._tracker  # 保存原始状态

        filepath = generator.save_report(content, "daily", "test-report.md")

        assert filepath.exists()
        assert filepath.name == "test-report.md"

        saved_content = filepath.read_text(encoding="utf-8")
        assert "Test Report" in saved_content

    def test_progress_bar(self, generator: ReportGenerator):
        """测试进度条生成"""
        bar = generator._create_progress_bar(50)
        assert "50%" in bar
        assert "█" in bar
        assert "░" in bar

    def test_module_progress_table(self, generator: ReportGenerator):
        """测试模块进度表格"""
        content = generator.generate_daily()

        # 检查表格结构
        assert "| 模块 | 名称 | 进度 | 完成/总计 | 状态 |" in content
        assert "| A1 |" in content


# =============================================================================
# 集成测试
# =============================================================================

class TestIntegration:
    """集成测试"""

    def test_full_workflow(self):
        """测试完整工作流"""
        # 1. 加载配置
        config = reload_config()
        assert config is not None

        # 2. 加载任务
        tracker = ProgressTracker()
        tracker.load_tasks()
        assert tracker.is_loaded

        # 3. 更新任务
        tracker.update_task("A2-001", progress=70)
        tracker.update_task("B2-001", status="in_progress", progress=50)

        # 4. 检查合规
        checker = ComplianceChecker()
        checker.check_content("test.py", 'if user.role == "pitcher": pass')

        # 5. 检测风险
        detector = RiskDetector(tracker=tracker, checker=checker)
        result = detector.detect_all()

        # 6. 生成报告
        generator = ReportGenerator(tracker=tracker, checker=checker, detector=detector)
        content = generator.generate_daily()

        # 验证
        assert "项目进度日报" in content
        assert tracker.get_task("A2-001").progress == 70

    def test_violation_to_risk_flow(self):
        """测试违规到风险的流转"""
        # 1. 检查违规代码
        checker = ComplianceChecker()
        checker.check_content("bad_code.py", """
        def process():
            account.balance -= 100
            auto_reject(report)
        """)

        # 2. 检测风险
        detector = RiskDetector(checker=checker)
        detector.detect_all()

        # 3. 验证风险被检测到
        compliance_risks = detector.get_risks_by_type(RiskType.COMPLIANCE)
        assert len(compliance_risks) > 0

        # 4. 验证报告包含风险
        generator = ReportGenerator(checker=checker, detector=detector)
        content = generator.generate_daily()
        assert "风险预警" in content


# =============================================================================
# 运行测试
# =============================================================================

if __name__ == "__main__":
    # 可以直接运行此文件进行测试
    pytest.main([__file__, "-v", "--tb=short"])
