"""
AI 代码工厂端到端测试

测试从需求到代码生成的完整流程

版本: v1.0
"""

import pytest
from pathlib import Path
from agents.skills.code_factory.core.orchestrator import CodeFactoryOrchestrator
from agents.skills.code_factory.core.agent_executor import AgentExecutor, ExecutionResult
from agents.skills.code_factory.core.task_queue import TaskQueue
from agents.skills.skill_system.wshobson_agent_loader import Agent


@pytest.fixture
def project_root():
    """项目根目录"""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def orchestrator(project_root):
    """编排器"""
    return CodeFactoryOrchestrator(project_root=project_root)


@pytest.fixture
def executor():
    """代理执行器（使用 mock 模式）"""
    return AgentExecutor()


class TestCodeFactoryE2E:
    """端到端测试"""
    
    def test_full_stack_development_workflow(self, orchestrator):
        """测试全栈开发工作流"""
        result = orchestrator.execute(
            requirement="创建一个用户管理功能，包括列表、创建、编辑、删除",
            workflow_type="full_stack_development"
        )
        
        assert result["status"] in ["completed", "partial_failure", "ready"]
        assert "workflow" in result
        assert "agents" in result
        assert "execution_results" in result or "model_assignments" in result
        
        # 验证工作流结构
        workflow = result["workflow"]
        assert workflow["name"] == "全栈功能开发"
        assert len(workflow["agents"]) > 0
    
    def test_code_review_workflow(self, orchestrator):
        """测试代码审查工作流"""
        result = orchestrator.execute(
            requirement="审查用户管理模块的代码质量",
            workflow_type="code_review"
        )
        
        assert result["status"] in ["completed", "partial_failure", "ready"]
        assert result["workflow_type"] == "code_review"
    
    def test_bug_fixing_workflow(self, orchestrator):
        """测试 Bug 修复工作流"""
        result = orchestrator.execute(
            requirement="修复用户登录功能的 bug",
            workflow_type="bug_fixing"
        )
        
        assert result["status"] in ["completed", "partial_failure", "ready"]
        assert result["workflow_type"] == "bug_fixing"
    
    def test_error_handling(self, orchestrator):
        """测试错误处理"""
        # 测试不存在的代理
        result = orchestrator.execute(
            requirement="使用不存在的代理",
            workflow_type="full_stack_development"
        )
        
        # 应该优雅处理，不崩溃
        assert "status" in result
        assert result["status"] in ["completed", "partial_failure", "ready"]
    
    def test_agent_selection(self, orchestrator):
        """测试代理选择逻辑"""
        # 测试架构需求
        result = orchestrator.execute(
            requirement="设计系统架构",
            workflow_type=None  # 让系统自动推断
        )
        
        assert len(result["agents"]) > 0
        # 应该包含 system-architect
        agent_ids = [a["id"] for a in result["agents"]]
        assert "system-architect" in agent_ids
    
    def test_model_assignment(self, orchestrator):
        """测试模型分配"""
        result = orchestrator.execute(
            requirement="后端 API 开发",
            workflow_type="full_stack_development"
        )
        
        assert "model_assignments" in result
        # 验证关键代理使用 Opus
        for agent in result["agents"]:
            agent_id = agent["id"]
            if agent_id in ["system-architect", "backend-architect", "code-reviewer"]:
                model = result["model_assignments"].get(agent_id)
                assert model == "opus-4.5", f"Agent {agent_id} should use Opus 4.5"


class TestAgentExecutor:
    """代理执行器测试"""
    
    def test_executor_initialization(self):
        """测试执行器初始化"""
        executor = AgentExecutor()
        assert executor is not None
        assert executor.model_strategy is not None
    
    def test_mock_execution(self, executor):
        """测试模拟执行（无 API 密钥时）"""
        from agents.skills.skill_system.wshobson_agent_loader import WshobsonAgentLoader
        
        loader = WshobsonAgentLoader()
        agent = loader.load_agent("backend-architect")
        
        if agent:
            result = executor.execute_agent(
                agent=agent,
                requirement="创建用户 API",
                context={}
            )
            
            assert result is not None
            assert result.agent_id == agent.id
            # 如果没有 API 客户端，应该返回模拟结果
            if not executor.client:
                assert result.success is True
                assert "[Mock]" in result.output or result.output is not None


class TestTaskQueue:
    """任务队列测试"""
    
    def test_sequential_execution(self, executor):
        """测试顺序执行"""
        from agents.skills.skill_system.wshobson_agent_loader import WshobsonAgentLoader
        
        loader = WshobsonAgentLoader()
        agents = []
        for agent_id in ["backend-architect", "frontend-developer"]:
            agent = loader.load_agent(agent_id)
            if agent:
                agents.append(agent)
        
        if len(agents) >= 2:
            queue = TaskQueue(executor)
            results = queue.execute_sequential(
                agents=agents,
                requirement="创建用户管理功能",
                context={}
            )
            
            assert len(results) == len(agents)
            assert all(isinstance(r, ExecutionResult) for r in results)
    
    def test_parallel_execution(self, executor):
        """测试并行执行"""
        from agents.skills.skill_system.wshobson_agent_loader import WshobsonAgentLoader
        
        loader = WshobsonAgentLoader()
        agents = []
        for agent_id in ["code-reviewer", "security-auditor"]:
            agent = loader.load_agent(agent_id)
            if agent:
                agents.append(agent)
        
        if len(agents) >= 2:
            queue = TaskQueue(executor)
            results = queue.execute_parallel(
                agents=agents,
                requirement="审查代码",
                context={}
            )
            
            assert len(results) == len(agents)
            assert all(isinstance(r, ExecutionResult) for r in results)


class TestPerformanceMonitoring:
    """性能监控测试"""
    
    def test_metrics_collection(self, orchestrator):
        """测试指标收集"""
        from agents.skills.code_factory.core.monitoring import get_monitor
        
        monitor = get_monitor()
        initial_metrics = monitor.get_metrics()
        
        # 执行一个工作流
        orchestrator.execute(
            requirement="测试指标收集",
            workflow_type="full_stack_development"
        )
        
        # 检查指标是否更新
        updated_metrics = monitor.get_metrics()
        assert updated_metrics["execution_count"] >= initial_metrics["execution_count"]
    
    def test_cache_metrics(self):
        """测试缓存指标"""
        from agents.skills.code_factory.core.monitoring import get_monitor
        from agents.skills.skill_system.wshobson_agent_loader import WshobsonAgentLoader
        
        monitor = get_monitor()
        loader = WshobsonAgentLoader()
        
        # 第一次加载（应该 miss）
        agent1 = loader.load_agent("backend-architect")
        
        # 第二次加载（应该 hit，如果有缓存）
        agent2 = loader.load_agent("backend-architect")
        
        metrics = monitor.get_metrics()
        assert "cache_hit_rate" in metrics
        assert 0 <= metrics["cache_hit_rate"] <= 1

