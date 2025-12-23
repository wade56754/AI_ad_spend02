"""
PhaseConfig 单元测试

测试 Phase 1/2 配置系统的核心功能
"""

import os
import pytest
from unittest.mock import patch
from decimal import Decimal

from backend.core.phase_config import (
    Phase,
    PhaseConfig,
    get_phase_config,
    reset_phase_config,
    should_block_negative_balance,
    should_enforce_daily_report,
    should_lock_settlement,
    should_enforce_topup,
    log_phase_warning,
    phase2_only
)


class TestPhaseEnum:
    """Phase 枚举测试"""

    def test_phase_values(self):
        """测试 Phase 枚举值"""
        assert Phase.PHASE1.value == "phase1"
        assert Phase.PHASE2.value == "phase2"

    def test_phase_from_string(self):
        """测试从字符串创建 Phase"""
        assert Phase("phase1") == Phase.PHASE1
        assert Phase("phase2") == Phase.PHASE2


class TestPhaseConfig:
    """PhaseConfig 配置测试"""

    def setup_method(self):
        """每个测试前重置配置"""
        reset_phase_config()

    def teardown_method(self):
        """每个测试后清理环境变量"""
        reset_phase_config()
        for key in ["FACTORY_PHASE", "PHASE2_TOPUP_ENFORCEMENT",
                    "PHASE2_DAILY_REPORT_REQUIRED", "PHASE2_NEGATIVE_BALANCE_BLOCK",
                    "PHASE2_SETTLEMENT_LOCK"]:
            os.environ.pop(key, None)

    def test_default_config(self):
        """测试默认配置为 Phase 1"""
        config = PhaseConfig()
        assert config.phase == Phase.PHASE1
        assert config.topup_enforcement is False
        assert config.daily_report_required is False
        assert config.negative_balance_block is False
        assert config.settlement_lock is False

    def test_is_phase1_enabled(self):
        """测试 Phase 1 判断"""
        config = PhaseConfig(phase=Phase.PHASE1)
        assert config.is_phase1_enabled() is True
        assert config.is_phase2_enabled() is False

    def test_is_phase2_enabled(self):
        """测试 Phase 2 判断"""
        config = PhaseConfig(phase=Phase.PHASE2)
        assert config.is_phase1_enabled() is False
        assert config.is_phase2_enabled() is True

    def test_from_env_default(self):
        """测试从环境变量加载默认配置"""
        config = PhaseConfig.from_env()
        assert config.phase == Phase.PHASE1
        assert config.topup_enforcement is False

    def test_from_env_phase2(self):
        """测试从环境变量加载 Phase 2 配置"""
        os.environ["FACTORY_PHASE"] = "phase2"
        os.environ["PHASE2_TOPUP_ENFORCEMENT"] = "true"
        os.environ["PHASE2_NEGATIVE_BALANCE_BLOCK"] = "true"

        config = PhaseConfig.from_env()

        assert config.phase == Phase.PHASE2
        assert config.topup_enforcement is True
        assert config.negative_balance_block is True
        assert config.daily_report_required is False  # 默认 false

    def test_from_env_invalid_phase(self):
        """测试无效 Phase 值回退到默认"""
        os.environ["FACTORY_PHASE"] = "invalid"

        config = PhaseConfig.from_env()

        assert config.phase == Phase.PHASE1  # 回退到默认

    def test_get_enabled_features_phase1(self):
        """测试 Phase 1 无启用功能"""
        config = PhaseConfig(phase=Phase.PHASE1, topup_enforcement=True)
        features = config.get_enabled_features()
        assert features == []  # Phase 1 返回空列表

    def test_get_enabled_features_phase2(self):
        """测试 Phase 2 启用功能列表"""
        config = PhaseConfig(
            phase=Phase.PHASE2,
            topup_enforcement=True,
            negative_balance_block=True
        )
        features = config.get_enabled_features()

        assert "topup_enforcement" in features
        assert "negative_balance_block" in features
        assert "daily_report_required" not in features

    def test_str_representation(self):
        """测试字符串表示"""
        config = PhaseConfig(phase=Phase.PHASE1)
        result = str(config)
        assert "phase1" in result
        assert "PhaseConfig" in result


class TestGlobalConfig:
    """全局配置单例测试"""

    def setup_method(self):
        reset_phase_config()

    def teardown_method(self):
        reset_phase_config()
        os.environ.pop("FACTORY_PHASE", None)

    def test_get_phase_config_singleton(self):
        """测试全局配置单例"""
        config1 = get_phase_config()
        config2 = get_phase_config()
        assert config1 is config2

    def test_reset_phase_config(self):
        """测试重置全局配置"""
        config1 = get_phase_config()
        reset_phase_config()
        config2 = get_phase_config()
        # 重置后是新实例（但值相同）
        assert config1 is not config2


class TestHelperFunctions:
    """辅助函数测试"""

    def setup_method(self):
        reset_phase_config()

    def teardown_method(self):
        reset_phase_config()
        for key in ["FACTORY_PHASE", "PHASE2_NEGATIVE_BALANCE_BLOCK",
                    "PHASE2_DAILY_REPORT_REQUIRED", "PHASE2_SETTLEMENT_LOCK",
                    "PHASE2_TOPUP_ENFORCEMENT"]:
            os.environ.pop(key, None)

    def test_should_block_negative_balance_phase1(self):
        """Phase 1 不阻止负余额"""
        os.environ["FACTORY_PHASE"] = "phase1"
        reset_phase_config()
        assert should_block_negative_balance() is False

    def test_should_block_negative_balance_phase2_disabled(self):
        """Phase 2 但功能未启用"""
        os.environ["FACTORY_PHASE"] = "phase2"
        os.environ["PHASE2_NEGATIVE_BALANCE_BLOCK"] = "false"
        reset_phase_config()
        assert should_block_negative_balance() is False

    def test_should_block_negative_balance_phase2_enabled(self):
        """Phase 2 且功能启用"""
        os.environ["FACTORY_PHASE"] = "phase2"
        os.environ["PHASE2_NEGATIVE_BALANCE_BLOCK"] = "true"
        reset_phase_config()
        assert should_block_negative_balance() is True

    def test_should_enforce_daily_report(self):
        """测试日报强制检查"""
        os.environ["FACTORY_PHASE"] = "phase2"
        os.environ["PHASE2_DAILY_REPORT_REQUIRED"] = "true"
        reset_phase_config()
        assert should_enforce_daily_report() is True

    def test_should_lock_settlement(self):
        """测试结算锁定检查"""
        os.environ["FACTORY_PHASE"] = "phase2"
        os.environ["PHASE2_SETTLEMENT_LOCK"] = "true"
        reset_phase_config()
        assert should_lock_settlement() is True

    def test_should_enforce_topup(self):
        """测试充值强制检查"""
        os.environ["FACTORY_PHASE"] = "phase2"
        os.environ["PHASE2_TOPUP_ENFORCEMENT"] = "true"
        reset_phase_config()
        assert should_enforce_topup() is True


class TestPhase2OnlyDecorator:
    """@phase2_only 装饰器测试"""

    def setup_method(self):
        reset_phase_config()

    def teardown_method(self):
        reset_phase_config()
        os.environ.pop("FACTORY_PHASE", None)

    def test_phase2_only_in_phase1(self):
        """Phase 1 下跳过 Phase 2 专属功能"""
        os.environ["FACTORY_PHASE"] = "phase1"
        reset_phase_config()

        call_count = 0

        @phase2_only("test_feature")
        def phase2_function():
            nonlocal call_count
            call_count += 1
            return "executed"

        result = phase2_function()

        assert result is None  # Phase 1 下返回 None
        assert call_count == 0  # 函数未执行

    def test_phase2_only_in_phase2(self):
        """Phase 2 下执行 Phase 2 专属功能"""
        os.environ["FACTORY_PHASE"] = "phase2"
        reset_phase_config()

        call_count = 0

        @phase2_only("test_feature")
        def phase2_function():
            nonlocal call_count
            call_count += 1
            return "executed"

        result = phase2_function()

        assert result == "executed"
        assert call_count == 1

    def test_phase2_only_with_fallback(self):
        """Phase 1 下使用 fallback 函数"""
        os.environ["FACTORY_PHASE"] = "phase1"
        reset_phase_config()

        @phase2_only("test_feature", fallback=lambda: "fallback_result")
        def phase2_function():
            return "phase2_result"

        result = phase2_function()

        assert result == "fallback_result"


class TestLogPhaseWarning:
    """log_phase_warning 测试"""

    def setup_method(self):
        reset_phase_config()

    def teardown_method(self):
        reset_phase_config()
        os.environ.pop("FACTORY_PHASE", None)

    def test_log_phase_warning_phase1(self, caplog):
        """Phase 1 下记录警告"""
        os.environ["FACTORY_PHASE"] = "phase1"
        reset_phase_config()

        import logging
        with caplog.at_level(logging.WARNING):
            log_phase_warning(
                feature="test_feature",
                message="Test warning message",
                user_id=123
            )

        assert "Phase1 Warning" in caplog.text
        assert "test_feature" in caplog.text

    def test_log_phase_warning_phase2(self, caplog):
        """Phase 2 下记录错误"""
        os.environ["FACTORY_PHASE"] = "phase2"
        reset_phase_config()

        import logging
        with caplog.at_level(logging.ERROR):
            log_phase_warning(
                feature="test_feature",
                message="Test violation message",
                user_id=123
            )

        assert "Phase2 Violation" in caplog.text
        assert "test_feature" in caplog.text
