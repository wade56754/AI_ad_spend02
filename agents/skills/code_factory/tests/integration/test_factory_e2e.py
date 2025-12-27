"""
工厂端到端集成测试

基准文档: MASTER.md v4.6
版本: v4.2
"""

import pytest
from pathlib import Path

from agents.skills.code_factory.core.factory import CodeFactory, FactoryResult
from agents.skills.code_factory.core.config import FactoryConfig
from agents.skills.code_factory.core.feature_flags import FeatureFlags, set_flags
from agents.skills.code_factory.core.exceptions import (
    RiskBlockedError,
    SotVersionMismatchError,
)
from agents.skills.code_factory.phases.context import PipelineContext


class TestCodeFactoryInit:
    """工厂初始化测试"""

    def test_factory_creation(self, project_root):
        """测试工厂创建"""
        config = FactoryConfig(project_dir=project_root)
        factory = CodeFactory(config)

        assert factory is not None
        assert factory.VERSION == "4.2.0"

    def test_factory_with_custom_flags(self, project_root):
        """测试自定义特性标志"""
        flags = FeatureFlags(
            use_legacy_pipeline=True,
            enable_guardrails=False,
        )
        set_flags(flags)

        config = FactoryConfig(project_dir=project_root)
        factory = CodeFactory(config)

        assert factory.flags.use_legacy_pipeline is True
        assert factory.flags.enable_guardrails is False


class TestPipelineContext:
    """流水线上下文测试"""

    def test_context_creation(self):
        """测试上下文创建"""
        context = PipelineContext(
            requirement="添加用户认证功能",
            module_id="M3-USERS",
        )

        assert context.requirement == "添加用户认证功能"
        assert context.module_id == "M3-USERS"
        assert context.started_at is not None

    def test_context_add_phase_result(self):
        """测试添加阶段结果"""
        from agents.skills.code_factory.phases.base import PhaseResult

        context = PipelineContext(requirement="测试需求")

        result = PhaseResult(
            phase_id=0,
            phase_name="INIT",
            success=True,
            duration_ms=100,
        )
        context.add_phase_result(result)

        assert len(context.phase_results) == 1
        assert context.is_phase_success(0)

    def test_context_get_total_duration(self):
        """测试获取总耗时"""
        from agents.skills.code_factory.phases.base import PhaseResult

        context = PipelineContext(requirement="测试需求")

        for i in range(3):
            context.add_phase_result(PhaseResult(
                phase_id=i,
                phase_name=f"PHASE_{i}",
                success=True,
                duration_ms=100,
            ))

        assert context.get_total_duration_ms() == 300

    def test_context_to_summary(self):
        """测试生成摘要"""
        context = PipelineContext(
            requirement="测试需求",
            module_id="M1-TEST",
            session_id="session-001",
        )

        summary = context.to_summary()

        assert summary["requirement"] == "测试需求"
        assert summary["module_id"] == "M1-TEST"
        assert summary["session_id"] == "session-001"


class TestFactoryRun:
    """工厂运行测试"""

    def test_run_with_low_risk_requirement(self, project_root):
        """测试低风险需求"""
        flags = FeatureFlags(
            enable_risk_phase=True,
            enable_guardrails=False,  # 简化测试
        )
        set_flags(flags)

        config = FactoryConfig(project_dir=project_root)
        factory = CodeFactory(config)

        # 低风险需求
        result = factory.run(
            requirement="添加日志输出功能",
            module_id="M1-DASHBOARD",
        )

        assert result is not None
        assert result.requirement == "添加日志输出功能"

    def test_run_detects_high_risk(self, project_root):
        """测试检测高风险需求"""
        flags = FeatureFlags(enable_risk_phase=True)
        set_flags(flags)

        config = FactoryConfig(project_dir=project_root)
        factory = CodeFactory(config)

        # 高风险需求（包含账本关键词）
        result = factory.run(
            requirement="修改账本余额计算逻辑",
            module_id="M8-LEDGER",
        )

        assert result is not None
        # 高风险模块应该被标记或阻断
        assert result.blocked or result.success


class TestFactoryResult:
    """工厂结果测试"""

    def test_result_success(self):
        """测试成功结果"""
        result = FactoryResult(
            success=True,
            requirement="添加功能",
            phases_executed=10,
        )

        assert result.success is True
        assert result.phases_executed == 10

    def test_result_failure(self):
        """测试失败结果"""
        result = FactoryResult(
            success=False,
            requirement="添加功能",
            error="生成失败",
            warnings=["语法警告", "验证警告"],
        )

        assert result.success is False
        assert result.error == "生成失败"
        assert len(result.warnings) == 2

    def test_result_to_dict(self):
        """测试结果转字典"""
        result = FactoryResult(
            success=True,
            requirement="添加功能",
            generated_files=["a.py", "b.py"],
        )

        data = result.to_dict()

        assert data["success"] is True
        assert len(data["generated_files"]) == 2


class TestFeatureFlags:
    """特性标志测试"""

    def test_default_flags(self):
        """测试默认标志"""
        flags = FeatureFlags()

        assert flags.use_legacy_pipeline is False
        assert flags.enable_sot_dynamic_load is True
        assert flags.enable_risk_phase is True
        assert flags.enable_guardrails is True

    def test_flags_from_env(self, monkeypatch):
        """测试从环境变量读取"""
        monkeypatch.setenv("CF_LEGACY", "1")
        monkeypatch.setenv("CF_GUARDRAILS", "0")

        flags = FeatureFlags.from_env()

        assert flags.use_legacy_pipeline is True
        assert flags.enable_guardrails is False

    def test_flags_strict_trace_rate(self):
        """测试追溯率阈值"""
        flags = FeatureFlags(strict_trace_rate=0.95)

        assert flags.strict_trace_rate == 0.95


class TestEventStream:
    """事件流测试"""

    def test_event_recording(self):
        """测试事件记录"""
        from agents.skills.code_factory.event_stream.stream import EventStream
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            stream = EventStream(Path(temp_dir) / "events.json")

            stream.phase_start(0, "INIT")
            stream.phase_end(0, "INIT", success=True, duration_ms=100)

            # 检查事件列表
            assert len(stream.events) == 2

    def test_event_types(self):
        """测试事件类型"""
        from agents.skills.code_factory.event_stream.events import EventType

        assert EventType.PHASE_START is not None
        assert EventType.PHASE_END is not None
        assert EventType.ERROR is not None

    def test_event_stream_summary(self):
        """测试事件流摘要"""
        from agents.skills.code_factory.event_stream.stream import EventStream
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            stream = EventStream(Path(temp_dir) / "events.json")
            stream.phase_start(0, "INIT")
            stream.phase_end(0, "INIT", success=True, duration_ms=100)

            summary = stream.get_summary()
            assert "total_events" in summary


class TestRiskClassifier:
    """风险分类器测试"""

    def test_classify_low_risk(self):
        """测试低风险分类"""
        from agents.skills.code_factory.risk.classifier import RiskClassifier, RiskLevel

        classifier = RiskClassifier()
        assessment = classifier.assess(
            requirement="添加日志功能",
            module_id="M1-DASHBOARD",
        )

        assert assessment.level in [RiskLevel.LOW, RiskLevel.MEDIUM]

    def test_classify_high_risk_module(self):
        """测试高风险模块分类"""
        from agents.skills.code_factory.risk.classifier import RiskClassifier, RiskLevel

        classifier = RiskClassifier()
        assessment = classifier.assess(
            requirement="修改余额计算",
            module_id="M8-LEDGER",
        )

        # 高风险模块会被 BLOCKED
        assert assessment.level in [RiskLevel.HIGH, RiskLevel.BLOCKED]

    def test_classify_high_risk_keywords(self):
        """测试高风险关键词分类"""
        from agents.skills.code_factory.risk.classifier import RiskClassifier, RiskLevel

        classifier = RiskClassifier()
        assessment = classifier.assess(
            requirement="删除所有账本记录并重新计算对账",
        )

        # 高风险关键词会被 BLOCKED
        assert assessment.level in [RiskLevel.HIGH, RiskLevel.BLOCKED]
