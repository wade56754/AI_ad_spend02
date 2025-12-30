"""
工厂端到端集成测试

基准文档: MASTER.md v4.6
版本: v4.5
"""

import pytest
from pathlib import Path

from agents.skills.code_factory.core.factory import (
    CodeFactory,
    FactoryResult,
    GenerationContext,
    VerifyResult,
    ConfirmResult,
)
from agents.skills.code_factory.core.config import FactoryConfig
from agents.skills.code_factory.core.feature_flags import FeatureFlags, set_flags
from agents.skills.code_factory.core.exceptions import (
    RiskBlockedError,
    SotVersionMismatchError,
)


class TestCodeFactoryInit:
    """工厂初始化测试"""

    def test_factory_creation(self, project_root):
        """测试工厂创建"""
        config = FactoryConfig(project_dir=project_root)
        factory = CodeFactory(config)

        assert factory is not None
        assert factory.VERSION == "4.5.0"

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


class TestGenerationContext:
    """生成上下文测试 (v4.3 新增)"""

    def test_context_creation(self):
        """测试上下文创建"""
        context = GenerationContext(
            requirement="添加用户认证功能",
            module_id="M3-USERS",
        )

        assert context.requirement == "添加用户认证功能"
        assert context.module_id == "M3-USERS"
        assert context.session_id == ""

    def test_context_with_session_id(self):
        """测试带会话ID的上下文"""
        context = GenerationContext(
            requirement="测试需求",
            module_id="M1-TEST",
            session_id="abc123",
        )

        assert context.session_id == "abc123"

    def test_context_to_prompt(self):
        """测试生成Prompt上下文"""
        context = GenerationContext(
            requirement="添加日志功能",
            module_id="M1-DASHBOARD",
            risk_level="low",
            sot_versions={"MASTER.md": "v4.6"},
        )

        prompt = context.to_prompt_context()

        assert "添加日志功能" in prompt
        assert "M1-DASHBOARD" in prompt
        assert "v4.6" in prompt

    def test_context_with_risk_warnings(self):
        """测试带风险警告的上下文"""
        context = GenerationContext(
            requirement="修改余额",
            risk_level="high",
            risk_warnings=["包含账本关键词"],
        )

        prompt = context.to_prompt_context()

        assert "high" in prompt
        assert "账本" in prompt


class TestFactoryRun:
    """工厂运行测试"""

    def test_run_with_low_risk_requirement(self, project_root):
        """测试低风险需求"""
        flags = FeatureFlags(
            enable_risk_phase=True,
            enable_guardrails=False,
            enable_sot_dynamic_load=False,
            enable_repo_map=False,
        )
        set_flags(flags)

        config = FactoryConfig(project_dir=project_root)
        factory = CodeFactory(config)

        result = factory.run(
            requirement="添加日志输出功能",
            module_id="M1-DASHBOARD",
        )

        assert result is not None
        assert result.requirement == "添加日志输出功能"
        assert result.success is True

    def test_run_detects_high_risk(self, project_root):
        """测试检测高风险需求"""
        flags = FeatureFlags(
            enable_risk_phase=True,
            enable_sot_dynamic_load=False,
            enable_repo_map=False,
        )
        set_flags(flags)

        config = FactoryConfig(project_dir=project_root)
        factory = CodeFactory(config)

        result = factory.run(
            requirement="修改账本余额计算逻辑",
            module_id="M8-LEDGER",
        )

        assert result is not None
        assert result.blocked or result.success

    def test_build_context(self, project_root):
        """测试构建上下文"""
        flags = FeatureFlags(
            enable_risk_phase=True,
            enable_sot_dynamic_load=False,
            enable_repo_map=False,
        )
        set_flags(flags)

        config = FactoryConfig(project_dir=project_root)
        factory = CodeFactory(config)

        context = factory.build_context(
            requirement="添加用户列表页面",
            module_id="M3-USERS",
        )

        assert context is not None
        assert context.requirement == "添加用户列表页面"
        assert context.module_id == "M3-USERS"


class TestVerifyResult:
    """验证结果测试 (v4.3 新增)"""

    def test_verify_result_success(self):
        """测试成功验证结果"""
        result = VerifyResult(
            success=True,
            trace_rate=1.0,
        )

        assert result.success is True
        assert result.trace_rate == 1.0
        assert len(result.errors) == 0

    def test_verify_result_with_errors(self):
        """测试带错误的验证结果"""
        result = VerifyResult(
            success=False,
            errors=["语法错误", "类型错误"],
            warnings=["未使用的导入"],
        )

        assert result.success is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 1


class TestConfirmResult:
    """确认结果测试 (v4.4 新增 - Phase 6 CONFIRM)"""

    def test_confirm_result_success(self):
        """测试成功确认结果"""
        result = ConfirmResult(
            confirmed=True,
            trace_report={"roles": {"traced": ["admin", "pitcher"], "untraced": []}},
        )

        assert result.confirmed is True
        assert result.is_blocking is False
        assert len(result.blocking_issues) == 0

    def test_confirm_result_with_blocking_issues(self):
        """测试带阻断问题的确认结果"""
        result = ConfirmResult(
            confirmed=False,
            blocking_issues=["使用了废弃角色 'supervisor'"],
            untraced_items=["supervisor"],
        )

        assert result.confirmed is False
        assert result.is_blocking is True
        assert len(result.blocking_issues) == 1

    def test_confirm_result_to_dict(self):
        """测试确认结果转字典"""
        result = ConfirmResult(
            confirmed=True,
            trace_report={"roles": {"traced": ["admin"], "untraced": []}},
            warnings=["使用了 Phase 2 状态"],
        )

        data = result.to_dict()
        assert data["confirmed"] is True
        assert data["is_blocking"] is False
        assert len(data["warnings"]) == 1


class TestConfirmCode:
    """确认代码测试 (v4.4 新增 - Phase 6 CONFIRM)"""

    def test_confirm_valid_roles(self, project_root):
        """测试确认有效角色"""
        flags = FeatureFlags(
            enable_sot_dynamic_load=False,
            enable_phase1_soft_mode=True,
        )
        set_flags(flags)

        config = FactoryConfig(project_dir=project_root)
        factory = CodeFactory(config)

        code_files = {
            "test.py": '''
def check_role(user):
    if user.role == "admin":
        return True
    if user.role == "pitcher":
        return True
    return False
'''
        }

        result = factory.confirm_code(code_files)

        assert result.confirmed is True
        assert "admin" in result.trace_report["roles"]["traced"]

    def test_confirm_deprecated_role_blocked(self, project_root):
        """测试废弃角色被阻断"""
        flags = FeatureFlags(
            enable_sot_dynamic_load=False,
            enable_phase1_soft_mode=True,
        )
        set_flags(flags)

        config = FactoryConfig(project_dir=project_root)
        factory = CodeFactory(config)

        code_files = {
            "test.py": '''
def check_role(user):
    if user.role == "supervisor":  # 废弃角色
        return True
    return False
'''
        }

        result = factory.confirm_code(code_files)

        assert result.confirmed is False
        assert result.is_blocking is True
        assert "supervisor" in result.trace_report["deprecated"]

    def test_confirm_phase1_states(self, project_root):
        """测试 Phase 1 状态确认"""
        flags = FeatureFlags(
            enable_sot_dynamic_load=False,
            enable_phase1_soft_mode=True,
        )
        set_flags(flags)

        config = FactoryConfig(project_dir=project_root)
        factory = CodeFactory(config)

        code_files = {
            "test.py": '''
def get_status():
    return "raw_submitted"  # Phase 1 有效状态
'''
        }

        result = factory.confirm_code(code_files)

        assert result.confirmed is True
        assert "raw_submitted" in result.trace_report["states"]["traced"]


class TestFactoryResult:
    """工厂结果测试"""

    def test_result_success(self):
        """测试成功结果"""
        result = FactoryResult(
            success=True,
            requirement="添加功能",
        )

        assert result.success is True
        assert result.requirement == "添加功能"

    def test_result_with_context(self):
        """测试带上下文的结果"""
        context = GenerationContext(
            requirement="添加功能",
            module_id="M1-TEST",
        )
        result = FactoryResult(
            success=True,
            requirement="添加功能",
            context=context,
        )

        assert result.context is not None
        assert result.context.module_id == "M1-TEST"

    def test_result_failure(self):
        """测试失败结果"""
        result = FactoryResult(
            success=False,
            requirement="添加功能",
            error="生成失败",
        )

        assert result.success is False
        assert result.error == "生成失败"

    def test_result_blocked(self):
        """测试阻断结果"""
        result = FactoryResult(
            success=False,
            requirement="修改账本",
            blocked=True,
            error="高风险模块",
        )

        assert result.blocked is True

    def test_result_to_dict(self):
        """测试结果转字典"""
        result = FactoryResult(
            success=True,
            requirement="添加功能",
            output_files=["a.py", "b.py"],
        )

        data = result.to_dict()

        assert data["success"] is True
        assert len(data["output_files"]) == 2


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

        assert assessment.level in [RiskLevel.HIGH, RiskLevel.BLOCKED]

    def test_classify_high_risk_keywords(self):
        """测试高风险关键词分类"""
        from agents.skills.code_factory.risk.classifier import RiskClassifier, RiskLevel

        classifier = RiskClassifier()
        assessment = classifier.assess(
            requirement="删除所有账本记录并重新计算对账",
        )

        assert assessment.level in [RiskLevel.HIGH, RiskLevel.BLOCKED]
