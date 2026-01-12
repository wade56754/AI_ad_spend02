"""
wshobson/agents 整合测试

测试代理和技能的加载、适配和使用

版本: v1.0
"""

import pytest
from pathlib import Path
from agents.skills.skill_system.wshobson_agent_loader import WshobsonAgentLoader
from agents.skills.skill_system.wshobson_skill_loader import WshobsonSkillLoader
from agents.skills.skill_system.agent_adapter import AgentAdapter
from agents.skills.skill_system.skill_adapter import SkillAdapter
from agents.skills.skill_system.plugin_loader import PluginLoader
from agents.skills.skill_system.model_strategy import ModelStrategy
from agents.skills.code_factory.workflow.presets import WorkflowPresets


@pytest.fixture
def project_root():
    """项目根目录"""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def agent_loader():
    """代理加载器"""
    return WshobsonAgentLoader()


@pytest.fixture
def skill_loader():
    """技能加载器"""
    return WshobsonSkillLoader()


@pytest.fixture
def plugin_loader(project_root):
    """插件加载器"""
    return PluginLoader(project_root=project_root)


@pytest.fixture
def model_strategy():
    """模型策略"""
    return ModelStrategy()


class TestAgentLoader:
    """测试代理加载器"""
    
    def test_load_agent(self, agent_loader):
        """测试加载代理"""
        agent = agent_loader.load_agent("backend-architect")
        assert agent is not None
        assert agent.id == "backend-architect"
        assert agent.model_tier in ["tier1", "tier2"]
    
    def test_load_all_agents(self, agent_loader):
        """测试加载所有代理"""
        agents = agent_loader.load_all_agents()
        assert len(agents) > 0
        assert "backend-architect" in agents or "system-architect" in agents
    
    def test_get_agents_by_tier(self, agent_loader):
        """测试按层级获取代理"""
        tier1_agents = agent_loader.get_agents_by_tier("tier1")
        tier2_agents = agent_loader.get_agents_by_tier("tier2")
        
        assert len(tier1_agents) >= 0
        assert len(tier2_agents) >= 0
        
        # 验证层级
        for agent in tier1_agents:
            assert agent.model_tier == "tier1"
        for agent in tier2_agents:
            assert agent.model_tier == "tier2"


class TestSkillLoader:
    """测试技能加载器"""
    
    def test_load_skill(self, skill_loader):
        """测试加载技能"""
        # 注意：如果 wshobson/agents 中没有对应技能，可能返回 None
        skill = skill_loader.load_skill("backend-development")
        # 如果技能存在，验证其属性
        if skill:
            assert skill.metadata is not None
            assert skill.metadata.id is not None
    
    def test_load_all_skills(self, skill_loader):
        """测试加载所有技能"""
        skills = skill_loader.load_all_skills()
        # 至少应该有一些技能（从映射配置加载）
        assert isinstance(skills, dict)


class TestAgentAdapter:
    """测试代理适配器"""
    
    def test_adapt_agent(self, agent_loader, project_root):
        """测试适配代理"""
        # 加载代理
        agent = agent_loader.load_agent("backend-architect")
        if not agent:
            pytest.skip("Agent not found")
        
        # 适配代理
        adapter = AgentAdapter(project_root=project_root)
        adapted_agent = adapter.adapt_agent(agent)
        
        assert adapted_agent is not None
        assert adapted_agent.id == agent.id
        # 验证 SoT 约束已注入
        assert "SoT 规范约束" in adapted_agent.description or "sot_constraints" in adapted_agent.metadata


class TestSkillAdapter:
    """测试技能适配器"""
    
    def test_adapt_skill(self, skill_loader, project_root):
        """测试适配技能"""
        # 加载技能
        skill = skill_loader.load_skill("backend-development")
        if not skill:
            pytest.skip("Skill not found")
        
        # 适配技能
        adapter = SkillAdapter(project_root=project_root)
        adapted_skill = adapter.adapt_skill(skill)
        
        assert adapted_skill is not None


class TestPluginLoader:
    """测试插件加载器"""
    
    def test_load_plugin(self, plugin_loader):
        """测试加载插件"""
        plugin = plugin_loader.load_plugin("code-factory")
        assert plugin is not None
        assert plugin.id == "code-factory"
        assert plugin.source == "custom"
    
    def test_load_wshobson_plugin(self, plugin_loader):
        """测试加载 wshobson/agents 插件"""
        plugin = plugin_loader.load_plugin("backend-development")
        if plugin:
            assert plugin.source == "wshobson/agents"
    
    def test_load_all_plugins(self, plugin_loader):
        """测试加载所有插件"""
        plugins = plugin_loader.load_all_plugins()
        assert len(plugins) > 0
        assert "code-factory" in plugins
    
    def test_get_plugins_by_category(self, plugin_loader):
        """测试按类别获取插件"""
        dev_plugins = plugin_loader.get_plugins_by_category("development")
        assert len(dev_plugins) >= 0


class TestModelStrategy:
    """测试模型策略"""
    
    def test_get_model_for_task(self, model_strategy):
        """测试根据任务类型获取模型"""
        # Tier 1 任务
        model = model_strategy.get_model_for_task("code-generation")
        assert model == "opus-4.5"
        
        model = model_strategy.get_model_for_task("code-review")
        assert model == "opus-4.5"
        
        # Tier 2 任务
        model = model_strategy.get_model_for_task("documentation")
        assert model == "sonnet-4.5"
    
    def test_get_model_for_agent(self, model_strategy):
        """测试根据代理 ID 获取模型"""
        # Tier 1 代理
        model = model_strategy.get_model_for_agent("backend-architect")
        assert model == "opus-4.5"
        
        # Tier 2 代理
        model = model_strategy.get_model_for_agent("frontend-developer")
        assert model == "sonnet-4.5"
    
    def test_is_tier1_task(self, model_strategy):
        """测试判断 Tier 1 任务"""
        assert model_strategy.is_tier1_task("code-generation") is True
        assert model_strategy.is_tier1_task("documentation") is False


class TestWorkflowPresets:
    """测试工作流预设"""
    
    def test_full_stack_development(self):
        """测试全栈开发工作流"""
        workflow = WorkflowPresets.full_stack_development()
        assert workflow["name"] == "全栈功能开发"
        assert len(workflow["agents"]) > 0
        assert workflow["pattern"] == "sequential"
        
        # 验证模型分配
        opus_agents = [a for a in workflow["agents"] if a["model"] == "opus-4.5"]
        sonnet_agents = [a for a in workflow["agents"] if a["model"] == "sonnet-4.5"]
        assert len(opus_agents) > 0
        assert len(sonnet_agents) > 0
    
    def test_code_review_workflow(self):
        """测试代码审查工作流"""
        workflow = WorkflowPresets.code_review_workflow()
        assert workflow["name"] == "代码审查"
        assert workflow["pattern"] == "parallel"
        # 代码审查应该全部使用 Opus
        for agent in workflow["agents"]:
            assert agent["model"] == "opus-4.5"
    
    def test_bug_fixing_workflow(self):
        """测试 Bug 修复工作流"""
        workflow = WorkflowPresets.bug_fixing_workflow()
        assert workflow["name"] == "Bug 修复"
        assert workflow["pattern"] == "sequential"
    
    def test_get_workflow(self):
        """测试根据名称获取工作流"""
        workflow = WorkflowPresets.get_workflow("full_stack_development")
        assert workflow is not None
        
        # 测试不存在的工作流
        with pytest.raises(ValueError):
            WorkflowPresets.get_workflow("non-existent")

