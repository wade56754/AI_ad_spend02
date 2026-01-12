"""
技能系统单元测试

覆盖:
- SkillMetadata 验证逻辑
- Skill 加载逻辑
- SkillRegistry 注册/查询逻辑
- SkillLoader 发现/加载逻辑

运行: pytest tests/test_skill_system_unit.py -v
"""

import pytest
from pathlib import Path
import threading
import time


class TestSkillMetadata:
    """SkillMetadata 单元测试"""

    def test_valid_metadata_creation(self):
        """测试有效的元数据创建"""
        from agents.skills.skill_system.base import SkillMetadata
        
        metadata = SkillMetadata(
            id="test-skill",
            name="Test Skill",
            version="1.0",
            triggers=["test"],
            keywords=["demo"],
            category="domain"
        )
        
        assert metadata.id == "test-skill"
        assert metadata.name == "Test Skill"
        assert metadata.version == "1.0"
        assert metadata.category == "domain"

    def test_invalid_id_empty(self):
        """测试空 ID 验证"""
        from agents.skills.skill_system.base import SkillMetadata
        
        with pytest.raises(ValueError) as exc_info:
            SkillMetadata(id="", name="Test", version="1.0")
        
        assert "ID 不能为空" in str(exc_info.value)

    def test_invalid_id_format(self):
        """测试无效 ID 格式"""
        from agents.skills.skill_system.base import SkillMetadata
        
        # 以数字开头
        with pytest.raises(ValueError) as exc_info:
            SkillMetadata(id="123skill", name="Test", version="1.0")
        
        assert "ID 格式无效" in str(exc_info.value)
        
        # 包含特殊字符
        with pytest.raises(ValueError) as exc_info:
            SkillMetadata(id="skill@name", name="Test", version="1.0")
        
        assert "ID 格式无效" in str(exc_info.value)

    def test_valid_id_formats(self):
        """测试有效的 ID 格式"""
        from agents.skills.skill_system.base import SkillMetadata
        
        # 下划线
        m1 = SkillMetadata(id="skill_name", name="Test", version="1.0")
        assert m1.id == "skill_name"
        
        # 连字符
        m2 = SkillMetadata(id="skill-name", name="Test", version="1.0")
        assert m2.id == "skill-name"
        
        # 混合
        m3 = SkillMetadata(id="my_skill-v2", name="Test", version="1.0")
        assert m3.id == "my_skill-v2"

    def test_invalid_name_empty(self):
        """测试空名称验证"""
        from agents.skills.skill_system.base import SkillMetadata
        
        with pytest.raises(ValueError) as exc_info:
            SkillMetadata(id="test", name="", version="1.0")
        
        assert "名称不能为空" in str(exc_info.value)

    def test_invalid_version_format(self):
        """测试无效版本格式"""
        from agents.skills.skill_system.base import SkillMetadata
        
        with pytest.raises(ValueError) as exc_info:
            SkillMetadata(id="test", name="Test", version="v1.0")
        
        assert "版本格式无效" in str(exc_info.value)

    def test_valid_version_formats(self):
        """测试有效的版本格式"""
        from agents.skills.skill_system.base import SkillMetadata
        
        # x.y 格式
        m1 = SkillMetadata(id="test", name="Test", version="1.0")
        assert m1.version == "1.0"
        
        # x.y.z 格式
        m2 = SkillMetadata(id="test", name="Test", version="1.2.3")
        assert m2.version == "1.2.3"
        
        # 单个数字
        m3 = SkillMetadata(id="test", name="Test", version="1")
        assert m3.version == "1"

    def test_matches_with_triggers(self):
        """测试触发词匹配"""
        from agents.skills.skill_system.base import SkillMetadata
        
        metadata = SkillMetadata(
            id="test",
            name="Test",
            version="1.0",
            triggers=["daily report", "api"]
        )
        
        # 完整词匹配
        assert metadata.matches("create daily report")
        assert metadata.matches("use api here")
        
        # 不应该部分匹配
        assert not metadata.matches("dailyreport")  # 无空格

    def test_matches_with_keywords(self):
        """测试关键词匹配"""
        from agents.skills.skill_system.base import SkillMetadata
        
        metadata = SkillMetadata(
            id="test",
            name="Test",
            version="1.0",
            keywords=["spend", "conversions"]
        )
        
        assert metadata.matches("calculate spend")
        assert metadata.matches("check conversions")
        
        # 不匹配无关词
        assert not metadata.matches("random query")

    def test_to_dict(self):
        """测试转换为字典"""
        from agents.skills.skill_system.base import SkillMetadata
        
        metadata = SkillMetadata(
            id="test",
            name="Test",
            version="1.0",
            triggers=["a"],
            keywords=["b"],
            category="domain"
        )
        
        d = metadata.to_dict()
        
        assert d["id"] == "test"
        assert d["name"] == "Test"
        assert d["version"] == "1.0"
        assert d["triggers"] == ["a"]
        assert d["keywords"] == ["b"]
        assert d["category"] == "domain"


class TestSkill:
    """Skill 单元测试"""

    def test_skill_creation(self, tmp_path):
        """测试技能创建"""
        skill_dir = self._create_skill_dir(tmp_path, "test-skill")
        
        from agents.skills.skill_system.base import Skill
        skill = Skill(skill_dir)
        
        assert skill.skill_path == skill_dir
        assert skill._metadata is None  # 未加载

    def test_metadata_lazy_loading(self, tmp_path):
        """测试元数据懒加载"""
        skill_dir = self._create_skill_dir(tmp_path, "test-skill")
        
        from agents.skills.skill_system.base import Skill
        skill = Skill(skill_dir)
        
        # 未访问前不加载
        assert skill._metadata is None
        assert 1 not in skill._loaded_layers
        
        # 访问后加载
        _ = skill.metadata
        assert skill._metadata is not None
        assert 1 in skill._loaded_layers

    def test_instructions_lazy_loading(self, tmp_path):
        """测试指令懒加载"""
        skill_dir = self._create_skill_dir(tmp_path, "test-skill", with_instructions=True)
        
        from agents.skills.skill_system.base import Skill
        skill = Skill(skill_dir)
        
        # 未访问前不加载
        assert skill._instructions is None
        
        # 访问后加载
        instructions = skill.instructions
        assert instructions == "# Test Instructions"
        assert 2 in skill._loaded_layers

    def test_resources_lazy_loading(self, tmp_path):
        """测试资源懒加载"""
        skill_dir = self._create_skill_dir(tmp_path, "test-skill", with_resources=True)
        
        from agents.skills.skill_system.base import Skill
        skill = Skill(skill_dir)
        
        # 未访问前不加载
        assert skill._resources is None
        
        # 访问后加载
        resources = skill.resources
        assert "example" in resources
        assert 3 in skill._loaded_layers

    def test_repr_no_io(self, tmp_path):
        """测试 __repr__ 不触发 I/O"""
        skill_dir = self._create_skill_dir(tmp_path, "test-skill")
        
        from agents.skills.skill_system.base import Skill
        skill = Skill(skill_dir)
        
        # 调用 repr 前
        layers_before = skill._loaded_layers.copy()
        
        # 调用 repr
        repr_str = repr(skill)
        
        # 不应该触发加载
        assert skill._loaded_layers == layers_before
        assert "test-skill" in repr_str

    def test_set_category(self, tmp_path):
        """测试设置 category"""
        skill_dir = self._create_skill_dir(tmp_path, "test-skill")
        
        from agents.skills.skill_system.base import Skill
        skill = Skill(skill_dir)
        
        skill.set_category("custom")
        assert skill.metadata.category == "custom"

    def test_token_estimate(self, tmp_path):
        """测试 Token 估算"""
        skill_dir = self._create_skill_dir(
            tmp_path, "test-skill", 
            with_instructions=True, 
            with_resources=True
        )
        
        from agents.skills.skill_system.base import Skill
        skill = Skill(skill_dir)
        
        # 触发加载
        _ = skill.instructions
        _ = skill.resources
        
        estimates = skill.get_token_estimate()
        
        assert "layer1_metadata" in estimates
        assert "layer2_instructions" in estimates
        assert "layer3_resources" in estimates
        assert estimates["layer1_metadata"] > 0

    @staticmethod
    def _create_skill_dir(
        tmp_path: Path, 
        skill_id: str,
        with_instructions: bool = False,
        with_resources: bool = False
    ) -> Path:
        """创建测试技能目录"""
        skill_dir = tmp_path / skill_id
        skill_dir.mkdir()
        
        # skill.yaml
        (skill_dir / "skill.yaml").write_text(f"""
id: {skill_id}
name: Test Skill
version: "1.0"
category: general
triggers:
  - test
""")
        
        if with_instructions:
            (skill_dir / "instructions.md").write_text("# Test Instructions")
        
        if with_resources:
            resources_dir = skill_dir / "resources"
            resources_dir.mkdir()
            (resources_dir / "example.md").write_text("# Example")
        
        return skill_dir


class TestSkillRegistry:
    """SkillRegistry 单元测试"""

    def test_register_and_get(self, tmp_path):
        """测试注册和获取技能"""
        from agents.skills.skill_system.base import Skill, SkillRegistry
        
        skill_dir = TestSkill._create_skill_dir(tmp_path, "test-skill")
        skill = Skill(skill_dir)
        _ = skill.metadata  # 触发加载
        
        registry = SkillRegistry()
        registry.register(skill)
        
        # 获取
        retrieved = registry.get("test-skill")
        assert retrieved is skill

    def test_unregister(self, tmp_path):
        """测试注销技能"""
        from agents.skills.skill_system.base import Skill, SkillRegistry
        
        skill_dir = TestSkill._create_skill_dir(tmp_path, "test-skill")
        skill = Skill(skill_dir)
        _ = skill.metadata
        
        registry = SkillRegistry()
        registry.register(skill)
        
        # 注销
        result = registry.unregister("test-skill")
        assert result is True
        assert registry.get("test-skill") is None
        
        # 再次注销应该返回 False
        result = registry.unregister("test-skill")
        assert result is False

    def test_find_by_query(self, tmp_path):
        """测试按查询查找"""
        from agents.skills.skill_system.base import Skill, SkillRegistry
        
        skill_dir = TestSkill._create_skill_dir(tmp_path, "test-skill")
        skill = Skill(skill_dir)
        _ = skill.metadata
        
        registry = SkillRegistry()
        registry.register(skill)
        
        # 匹配
        results = registry.find_by_query("run test now")
        assert len(results) == 1
        assert results[0].metadata.id == "test-skill"
        
        # 不匹配
        results = registry.find_by_query("random query")
        assert len(results) == 0

    def test_find_by_category(self, tmp_path):
        """测试按类别查找"""
        from agents.skills.skill_system.base import Skill, SkillRegistry
        
        skill_dir = TestSkill._create_skill_dir(tmp_path, "test-skill")
        skill = Skill(skill_dir)
        _ = skill.metadata
        
        registry = SkillRegistry()
        registry.register(skill)
        
        # 查找
        results = registry.find_by_category("general")
        assert len(results) == 1
        
        # 不存在的类别
        results = registry.find_by_category("nonexistent")
        assert len(results) == 0

    def test_list_all(self, tmp_path):
        """测试列出所有技能"""
        from agents.skills.skill_system.base import Skill, SkillRegistry
        
        registry = SkillRegistry()
        
        # 注册多个技能
        for i in range(3):
            skill_dir = TestSkill._create_skill_dir(tmp_path, f"skill{i}")
            skill = Skill(skill_dir)
            _ = skill.metadata
            registry.register(skill)
        
        all_skills = registry.list_all()
        assert len(all_skills) == 3

    def test_thread_safety(self, tmp_path):
        """测试线程安全"""
        from agents.skills.skill_system.base import Skill, SkillRegistry
        
        # 预先创建所有技能目录
        skill_dirs = []
        for i in range(10):
            skill_dir = tmp_path / f"thread_skill{i}"
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "skill.yaml").write_text(f"""
id: skill{i}
name: Test Skill {i}
version: "1.0"
category: general
triggers:
  - test{i}
""")
            skill_dirs.append((skill_dir, f"skill{i}"))
        
        registry = SkillRegistry()
        errors = []
        
        def register_skill(skill_dir: Path, skill_id: str):
            try:
                skill = Skill(skill_dir)
                _ = skill.metadata
                registry.register(skill)
            except Exception as e:
                errors.append(e)
        
        # 并发注册
        threads = [
            threading.Thread(target=register_skill, args=(skill_dir, skill_id))
            for skill_dir, skill_id in skill_dirs
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # 无错误
        assert len(errors) == 0
        # 所有技能都注册成功
        assert len(registry) == 10

    def test_contains(self, tmp_path):
        """测试 in 操作符"""
        from agents.skills.skill_system.base import Skill, SkillRegistry
        
        skill_dir = TestSkill._create_skill_dir(tmp_path, "test-skill")
        skill = Skill(skill_dir)
        _ = skill.metadata
        
        registry = SkillRegistry()
        registry.register(skill)
        
        assert "test-skill" in registry
        assert "nonexistent" not in registry


class TestSkillLoader:
    """SkillLoader 单元测试"""

    def test_load_all(self, tmp_path):
        """测试加载所有技能"""
        from agents.skills.skill_system.loader import SkillLoader
        
        # 创建技能目录结构
        domain_dir = tmp_path / "domain_skills"
        domain_dir.mkdir()
        TestSkill._create_skill_dir(domain_dir, "skill1")
        TestSkill._create_skill_dir(domain_dir, "skill2")
        
        loader = SkillLoader(tmp_path)
        registry = loader.load_all()
        
        assert len(registry) == 2

    def test_load_skill(self, tmp_path):
        """测试加载单个技能"""
        from agents.skills.skill_system.loader import SkillLoader
        
        skill_dir = TestSkill._create_skill_dir(tmp_path, "single-skill")
        
        loader = SkillLoader(tmp_path)
        skill = loader.load_skill(skill_dir)
        
        assert skill is not None
        assert skill.metadata.id == "single-skill"

    def test_load_skill_error_handling(self, tmp_path):
        """测试加载失败的错误处理"""
        from agents.skills.skill_system.loader import SkillLoader
        
        # 创建无效的技能目录 (没有 skill.yaml)
        invalid_dir = tmp_path / "invalid"
        invalid_dir.mkdir()
        
        loader = SkillLoader(tmp_path)
        skill = loader.load_skill(invalid_dir)
        
        # 应该返回 None，而不是抛出异常
        assert skill is None

    def test_find_skill(self, tmp_path):
        """测试查找技能"""
        from agents.skills.skill_system.loader import SkillLoader
        
        domain_dir = tmp_path / "domain_skills"
        domain_dir.mkdir()
        TestSkill._create_skill_dir(domain_dir, "search-skill")
        
        loader = SkillLoader(tmp_path)
        loader.load_all()
        
        results = loader.find_skill("run test now")
        assert len(results) == 1

    def test_get_skill(self, tmp_path):
        """测试获取技能"""
        from agents.skills.skill_system.loader import SkillLoader
        
        domain_dir = tmp_path / "domain_skills"
        domain_dir.mkdir()
        TestSkill._create_skill_dir(domain_dir, "get-skill")
        
        loader = SkillLoader(tmp_path)
        loader.load_all()
        
        skill = loader.get_skill("get-skill")
        assert skill is not None
        assert skill.metadata.id == "get-skill"


class TestEdgeCases:
    """边界条件测试"""

    def test_empty_triggers_and_keywords(self):
        """测试空触发词和关键词"""
        from agents.skills.skill_system.base import SkillMetadata
        
        metadata = SkillMetadata(
            id="test",
            name="Test",
            version="1.0",
            triggers=[],
            keywords=[]
        )
        
        # 不应该匹配任何查询
        assert not metadata.matches("any query")

    def test_whitespace_handling(self):
        """测试空白字符处理"""
        from agents.skills.skill_system.base import SkillMetadata
        
        metadata = SkillMetadata(
            id="  test  ",  # 前后空格
            name="  Test Skill  ",
            version="1.0"
        )
        
        # 应该自动去除空格
        assert metadata.id == "test"
        assert metadata.name == "Test Skill"

    def test_missing_instructions_file(self, tmp_path):
        """测试缺少指令文件"""
        from agents.skills.skill_system.base import Skill
        
        skill_dir = TestSkill._create_skill_dir(tmp_path, "no-instructions")
        skill = Skill(skill_dir)
        
        # 应该返回空字符串，而不是抛出异常
        assert skill.instructions == ""

    def test_missing_resources_directory(self, tmp_path):
        """测试缺少资源目录"""
        from agents.skills.skill_system.base import Skill
        
        skill_dir = TestSkill._create_skill_dir(tmp_path, "no-resources")
        skill = Skill(skill_dir)
        
        # 应该返回空字典，而不是抛出异常
        assert skill.resources == {}

    def test_unicode_in_skill_files(self, tmp_path):
        """测试 Unicode 内容"""
        from agents.skills.skill_system.base import Skill
        
        skill_dir = tmp_path / "unicode-skill"
        skill_dir.mkdir()
        
        (skill_dir / "skill.yaml").write_text("""
id: unicode-skill
name: 中文技能名称
version: "1.0"
triggers:
  - 日报
  - 充值
""", encoding="utf-8")
        
        (skill_dir / "instructions.md").write_text("# 中文说明\n\n这是中文内容", encoding="utf-8")
        
        skill = Skill(skill_dir)
        
        assert skill.metadata.name == "中文技能名称"
        assert "中文说明" in skill.instructions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
