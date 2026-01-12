"""
标准工作流预设

整合 wshobson/agents 模式的标准工作流定义

版本: v1.0
基准: wshobson/agents 工作流模式
"""

from typing import Dict, List, Any


class WorkflowPresets:
    """标准工作流预设（整合 wshobson/agents 模式）"""
    
    @staticmethod
    def full_stack_development() -> Dict[str, Any]:
        """
        全栈功能开发工作流
        
        使用 Opus 4.5 进行架构设计和代码生成，Sonnet 4.5 进行前端开发和测试
        """
        return {
            "name": "全栈功能开发",
            "description": "完整的前后端功能开发工作流",
            "agents": [
                {
                    "id": "system-architect",
                    "model": "opus-4.5",
                    "role": "系统架构设计"
                },
                {
                    "id": "backend-architect",
                    "model": "opus-4.5",
                    "role": "后端代码生成"
                },
                {
                    "id": "frontend-developer",
                    "model": "sonnet-4.5",
                    "role": "前端代码生成"
                },
                {
                    "id": "code-reviewer",
                    "model": "opus-4.5",
                    "role": "代码审查"
                },
                {
                    "id": "test-automator",
                    "model": "sonnet-4.5",
                    "role": "测试生成"
                }
            ],
            "pattern": "sequential",
            "estimated_tokens": {
                "opus": 50000,
                "sonnet": 30000
            }
        }
    
    @staticmethod
    def code_review_workflow() -> Dict[str, Any]:
        """
        代码审查工作流
        
        使用 Opus 4.5 进行代码审查、安全审计和性能分析
        """
        return {
            "name": "代码审查",
            "description": "多维度代码审查工作流",
            "agents": [
                {
                    "id": "code-reviewer",
                    "model": "opus-4.5",
                    "role": "代码质量审查"
                },
                {
                    "id": "security-auditor",
                    "model": "opus-4.5",
                    "role": "安全审计"
                },
                {
                    "id": "performance-engineer",
                    "model": "opus-4.5",
                    "role": "性能分析"
                }
            ],
            "pattern": "parallel",
            "estimated_tokens": {
                "opus": 40000,
                "sonnet": 0
            }
        }
    
    @staticmethod
    def bug_fixing_workflow() -> Dict[str, Any]:
        """
        Bug 修复工作流
        
        使用 Opus 4.5 进行调试和审查，Sonnet 4.5 进行测试生成
        """
        return {
            "name": "Bug 修复",
            "description": "Bug 定位、修复和验证工作流",
            "agents": [
                {
                    "id": "debugging-specialist",
                    "model": "opus-4.5",
                    "role": "Bug 定位和修复"
                },
                {
                    "id": "code-reviewer",
                    "model": "opus-4.5",
                    "role": "修复代码审查"
                },
                {
                    "id": "test-automator",
                    "model": "sonnet-4.5",
                    "role": "测试用例生成"
                }
            ],
            "pattern": "sequential",
            "estimated_tokens": {
                "opus": 30000,
                "sonnet": 10000
            }
        }
    
    @staticmethod
    def performance_optimization_workflow() -> Dict[str, Any]:
        """
        性能优化工作流
        
        使用 Opus 4.5 进行性能分析和优化
        """
        return {
            "name": "性能优化",
            "description": "性能分析和优化工作流",
            "agents": [
                {
                    "id": "performance-engineer",
                    "model": "opus-4.5",
                    "role": "性能分析"
                },
                {
                    "id": "backend-architect",
                    "model": "opus-4.5",
                    "role": "优化方案设计"
                },
                {
                    "id": "code-reviewer",
                    "model": "opus-4.5",
                    "role": "优化代码审查"
                }
            ],
            "pattern": "sequential",
            "estimated_tokens": {
                "opus": 40000,
                "sonnet": 0
            }
        }
    
    @staticmethod
    def system_architecture_workflow() -> Dict[str, Any]:
        """
        系统架构工作流
        
        使用 Opus 4.5 进行系统架构设计
        """
        return {
            "name": "系统架构",
            "description": "系统架构设计工作流",
            "agents": [
                {
                    "id": "system-architect",
                    "model": "opus-4.5",
                    "role": "系统架构设计"
                },
                {
                    "id": "database-architect",
                    "model": "opus-4.5",
                    "role": "数据库架构设计"
                },
                {
                    "id": "api-architect",
                    "model": "opus-4.5",
                    "role": "API 架构设计"
                }
            ],
            "pattern": "parallel",
            "estimated_tokens": {
                "opus": 50000,
                "sonnet": 0
            }
        }
    
    @staticmethod
    def get_workflow(name: str) -> Dict[str, Any]:
        """
        根据名称获取工作流
        
        Args:
            name: 工作流名称
            
        Returns:
            工作流定义
        """
        workflows = {
            "full_stack_development": WorkflowPresets.full_stack_development,
            "code_review": WorkflowPresets.code_review_workflow,
            "bug_fixing": WorkflowPresets.bug_fixing_workflow,
            "performance_optimization": WorkflowPresets.performance_optimization_workflow,
            "system_architecture": WorkflowPresets.system_architecture_workflow,
        }
        
        workflow_func = workflows.get(name)
        if workflow_func:
            return workflow_func()
        else:
            raise ValueError(f"Unknown workflow: {name}. Available: {list(workflows.keys())}")

