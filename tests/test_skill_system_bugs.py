"""
技能系统 Bug 验证测试

验证 P0 和 P1 级别的 Bug 修复

运行: pytest tests/test_skill_system_bugs.py -v
"""

import pytest
from pathlib import Path


class TestP0Bugs:
    """P0 级别 Bug 测试"""

    def test_p0_1_empty_yaml_crash(self, tmp_path):
        """
        P0-1: 空 YAML 文件导致 NoneType 崩溃
        
        修复后: 应该抛出 ValueError 而不是 AttributeError
        """
        # 创建空的 skill.yaml
        skill_dir = tmp_path / "empty_skill"
        skill_dir.mkdir()
        skill_yaml = skill_dir / "skill.yaml"
        skill_yaml.write_text("")  # 空文件
        
        from agents.skills.skill_system.base import Skill
        skill = Skill(skill_dir)
        
        # 修复后应该抛出 ValueError，而不是 AttributeError
        with pytest.raises(ValueError) as exc_info:
            _ = skill.metadata  # 触发加载
        
        assert "为空或格式无效" in str(exc_info.value)

    def test_p0_2_abc_instantiation(self):
        """
        P0-2: ABC 基类直接实例化
        
        修复后: Skill 不再继承 ABC
        """
        from agents.skills.skill_system.base import Skill
        from abc import ABC
        
        # 检查 Skill 是否继承自 ABC
        is_abc_subclass = issubclass(Skill, ABC)
        
        # 修复后: Skill 不应该继承 ABC
        assert not is_abc_subclass, "Skill 不应该继承 ABC"

    def test_p0_3_import_error_handling(self):
        """
        P0-3: HallucinationGuard 延迟导入失败
        
        修复后: ImportError 应该被正确处理
        """
        from agents.skills.verifiers.source_tracing_verifier import HallucinationGuard
        guard = HallucinationGuard()
        
        # 检查是否有 spec_verifier (可能为 None 如果导入失败)
        has_spec_verifier = hasattr(guard, "spec_verifier")
        assert has_spec_verifier, "应该有 spec_verifier 属性"


class TestP1Bugs:
    """P1 级别 Bug 测试"""

    def test_p1_1_substring_match_false_positive(self):
        """
        P1-1: 子串匹配导致误激活
        
        修复后: 使用词边界匹配，不会产生误报
        """
        from agents.skills.skill_system.base import SkillMetadata
        
        metadata = SkillMetadata(
            id="test",
            name="Test Skill",
            version="1.0",
            triggers=["api", "test"],
            keywords=["data"]
        )
        
        # 测试误匹配场景 - 修复后这些不应该匹配
        false_positives = [
            ("capitalism", "api"),     # 包含 "api" 但不是完整词
            ("contest", "test"),       # 包含 "test" 但不是完整词
            ("database", "data"),      # 包含 "data" 但不是完整词
        ]
        
        # 修复后: 这些都不应该匹配
        for query, _ in false_positives:
            assert not metadata.matches(query), f"'{query}' 不应该匹配"
        
        # 验证正确匹配仍然有效
        assert metadata.matches("use the api here"), "正确匹配失效 - 'api' 应该匹配"
        assert metadata.matches("run test now"), "正确匹配失效 - 'test' 应该匹配"
        assert metadata.matches("load data file"), "正确匹配失效 - 'data' 应该匹配"

    def test_p1_2_private_attribute_modification(self, tmp_path):
        """
        P1-2: 使用公开方法修改 category
        
        修复后: 应该使用 set_category() 方法
        """
        # 创建测试技能
        skill_dir = tmp_path / "test_skill"
        skill_dir.mkdir()
        skill_yaml = skill_dir / "skill.yaml"
        skill_yaml.write_text("""
id: test_skill
name: Test Skill
version: "1.0"
category: general
""")
        
        from agents.skills.skill_system.base import Skill
        
        skill = Skill(skill_dir)
        _ = skill.metadata  # 触发加载
        
        original_category = skill.metadata.category
        
        # 使用公开方法修改 category
        skill.set_category("domain")
        
        new_category = skill.metadata.category
        
        assert original_category == "general"
        assert new_category == "domain"

    def test_p1_3_resource_file_types(self, tmp_path):
        """
        P1-3: 只加载 .md 文件
        
        修复后: 应该加载多种类型的资源文件
        """
        # 创建测试技能和资源
        skill_dir = tmp_path / "resource_skill"
        skill_dir.mkdir()
        skill_yaml = skill_dir / "skill.yaml"
        skill_yaml.write_text("""
id: resource_skill
name: Resource Skill
version: "1.0"
""")
        
        resources_dir = skill_dir / "resources"
        resources_dir.mkdir()
        
        # 创建不同类型的资源文件
        (resources_dir / "readme.md").write_text("# Markdown")
        (resources_dir / "config.yaml").write_text("key: value")
        (resources_dir / "data.json").write_text('{"key": "value"}')
        (resources_dir / "example.py").write_text("print('hello')")
        
        from agents.skills.skill_system.base import Skill
        
        skill = Skill(skill_dir)
        resources = skill.resources
        
        # 修复后: 所有支持的文件类型都应该被加载
        assert "readme" in resources, "readme.md 应该被加载"
        assert "config" in resources, "config.yaml 应该被加载"
        assert "data" in resources, "data.json 应该被加载"
        assert "example" in resources, "example.py 应该被加载"

    def test_p1_4_annotation_after_code(self):
        """
        P1-4: _has_nearby_annotation 检查前后 5 行
        
        修复后: 注释在代码前后都应该被检测到
        """
        from agents.skills.verifiers.source_tracing_verifier import SourceTracingVerifier
        
        verifier = SourceTracingVerifier()
        
        # 测试代码：注释在代码之后
        code_with_annotation_after = """
class DailyReportStatus(str, Enum):
    PENDING = "pending"
# SoT: STATE_MACHINE.md#daily_report
"""
        
        # 测试代码：注释在代码之前
        code_with_annotation_before = """
# SoT: STATE_MACHINE.md#daily_report
class DailyReportStatus(str, Enum):
    PENDING = "pending"
"""
        
        result_after = verifier.verify("test.py", code_with_annotation_after)
        result_before = verifier.verify("test.py", code_with_annotation_before)
        
        # 修复后: 两种情况的 issues 数量应该相同
        assert len(result_after.issues) == len(result_before.issues), \
            "注释在代码前后应该有相同的检测结果"

    def test_p1_5_repr_triggers_io(self, tmp_path):
        """
        P1-5: __repr__ 触发 I/O 操作
        
        修复后: __repr__ 不应该触发文件加载
        """
        # 创建测试技能
        skill_dir = tmp_path / "repr_skill"
        skill_dir.mkdir()
        skill_yaml = skill_dir / "skill.yaml"
        skill_yaml.write_text("""
id: repr_skill
name: Repr Skill
version: "1.0"
""")
        
        from agents.skills.skill_system.base import Skill
        
        skill = Skill(skill_dir)
        
        # 检查初始状态
        initial_layers = skill._loaded_layers.copy()
        initial_metadata_loaded = skill._metadata is not None
        
        # 调用 __repr__
        repr_str = repr(skill)
        
        # 检查 __repr__ 后的状态
        after_layers = skill._loaded_layers.copy()
        after_metadata_loaded = skill._metadata is not None
        
        # 修复验证: __repr__ 不应该触发 I/O
        assert len(after_layers) == len(initial_layers), "__repr__ 不应该触发 I/O"
        assert initial_metadata_loaded == after_metadata_loaded, "__repr__ 不应该加载元数据"
        
        # 验证 repr 输出使用了目录名而不是触发加载
        assert "repr_skill" in repr_str, "repr 应该显示技能标识"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
