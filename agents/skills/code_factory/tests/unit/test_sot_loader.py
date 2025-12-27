"""
SoT 加载器单元测试

基准文档: MASTER.md v4.6
版本: v4.2
"""

import pytest
from pathlib import Path

from agents.skills.code_factory.sot.loader import SotLoader, LoadedSotData
from agents.skills.code_factory.sot.whitelist import DynamicWhitelist


class TestSotLoader:
    """SoT 加载器测试"""

    def test_loaded_sot_data_structure(self, sample_sot_data):
        """测试 LoadedSotData 结构"""
        assert "admin" in sample_sot_data.roles
        assert "pitcher" in sample_sot_data.roles
        assert len(sample_sot_data.roles) == 6

    def test_loaded_sot_data_has_states(self, sample_sot_data):
        """测试状态数据"""
        assert "daily_reports" in sample_sot_data.states
        assert "draft" in sample_sot_data.states["daily_reports"]

    def test_loaded_sot_data_has_error_codes(self, sample_sot_data):
        """测试错误码前缀"""
        assert "VAL" in sample_sot_data.error_codes
        assert "AUTH" in sample_sot_data.error_codes

    def test_legacy_mapping(self, sample_sot_data):
        """测试废弃映射"""
        assert sample_sot_data.legacy_mapping.get("supervisor") == "admin"

    def test_version_tracking(self, sample_sot_data):
        """测试版本追踪"""
        assert sample_sot_data.versions["MASTER.md"] == "v4.6"


class TestDynamicWhitelist:
    """动态白名单测试"""

    def test_create_whitelist(self):
        """测试创建白名单"""
        whitelist = DynamicWhitelist()
        assert whitelist is not None

    def test_register_and_validate(self):
        """测试注册和验证"""
        whitelist = DynamicWhitelist()
        whitelist.register("role", "admin")
        whitelist.register("role", "pitcher")

        assert whitelist.is_valid("role", "admin")
        assert whitelist.is_valid("role", "pitcher")
        assert not whitelist.is_valid("role", "unknown")

    def test_register_deprecated(self):
        """测试注册废弃值"""
        whitelist = DynamicWhitelist()
        whitelist.register("role", "admin")
        whitelist.register(
            "role",
            "supervisor",
            deprecated=True,
            replacement="admin",
        )

        is_valid, msg = whitelist.validate("role", "supervisor")
        assert is_valid  # 废弃值仍然有效
        assert "废弃" in msg or "deprecated" in msg.lower()

    def test_bulk_register(self):
        """测试批量注册"""
        whitelist = DynamicWhitelist()
        whitelist.register_bulk("role", {"admin", "pitcher", "finance"})

        assert whitelist.is_valid("role", "admin")
        assert whitelist.is_valid("role", "pitcher")
        assert whitelist.is_valid("role", "finance")

    def test_validate_with_suggestion(self):
        """测试验证并返回建议"""
        whitelist = DynamicWhitelist()
        whitelist.register("role", "admin")
        whitelist.register("role", "pitcher")
        whitelist.register("role", "finance")

        is_valid, msg = whitelist.validate("role", "admi")  # 拼写错误
        assert not is_valid
        assert msg is not None
        # 应该建议 "admin"

    def test_get_all(self):
        """测试获取所有值"""
        whitelist = DynamicWhitelist()
        whitelist.register_bulk("role", {"admin", "pitcher", "finance"})

        all_roles = whitelist.get_all("role")
        assert len(all_roles) == 3
        assert "admin" in all_roles

    def test_get_active(self):
        """测试获取未废弃的值"""
        whitelist = DynamicWhitelist()
        whitelist.register("role", "admin")
        whitelist.register("role", "supervisor", deprecated=True)

        active = whitelist.get_active("role")
        assert "admin" in active
        assert "supervisor" not in active

    def test_from_sot_data(self, sample_sot_data):
        """测试从 SoT 数据创建"""
        whitelist = DynamicWhitelist.from_sot_data(sample_sot_data)

        # 检查角色
        assert whitelist.is_valid("role", "admin")
        assert whitelist.is_valid("role", "pitcher")

        # 检查状态
        assert whitelist.is_valid("state", "draft")
        assert whitelist.is_valid("state", "submitted")

        # 检查错误码
        assert whitelist.is_valid("error_code", "VAL")
        assert whitelist.is_valid("error_code", "AUTH")

    def test_suggest(self):
        """测试建议功能"""
        whitelist = DynamicWhitelist()
        whitelist.register_bulk("role", {"admin", "administrator", "pitcher"})

        suggestions = whitelist.suggest("role", "adm")
        assert "admin" in suggestions or "administrator" in suggestions
