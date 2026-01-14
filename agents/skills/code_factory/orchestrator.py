"""
AI 代码工厂 v7.0 - 轻量编排器

版本: v7.0
基准文档: MASTER.md v4.8

重构说明:
- 从 977 行的 factory.py 精简为 <200 行的轻量编排器
- 移除 stub 依赖，使用真实的阶段实现
- 集成 Superpowers 方法论技能
- 实现两阶段审查流程

架构:
┌─────────────────────────────────────────────────────────────┐
│                  LightweightOrchestrator                    │
├─────────────────────────────────────────────────────────────┤
│  CLARIFY → PLAN → IMPLEMENT (TDD) → REVIEW → CONFIRM        │
│                                                             │
│  - CLARIFY: 对接 superpowers:brainstorming                  │
│  - PLAN: 对接 superpowers:writing-plans                     │
│  - IMPLEMENT: 对接 superpowers:test-driven-development       │
│  - REVIEW: 两阶段审查 (规格 + 质量)                          │
│  - CONFIRM: 幻觉抑制确认                                    │
└─────────────────────────────────────────────────────────────┘
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable

from .types import (
    PhaseType,
    PhaseResult,
    PipelineResult,
    ExecutionContext,
    TaskSpec,
)
from .core.exceptions import CodeFactoryError, PhaseExecutionError

logger = logging.getLogger(__name__)


class LightweightOrchestrator:
    """
    轻量编排器 - AI 代码工厂核心
    
    职责:
    1. 协调 5 个阶段的执行
    2. 管理阶段间数据传递
    3. 处理错误和恢复
    
    设计原则:
    - 单一职责：只负责编排，不包含业务逻辑
    - 开放封闭：阶段实现可插拔
    - 依赖倒置：依赖抽象阶段接口
    """
    
    VERSION = "7.0.0"
    
    def __init__(
        self,
        context: ExecutionContext,
        phase_handlers: Optional[Dict[PhaseType, Callable]] = None,
    ):
        """
        初始化编排器
        
        Args:
            context: 执行上下文
            phase_handlers: 阶段处理器映射 (可选，用于自定义)
        """
        self.context = context
        self._phase_data: Dict[str, Any] = {}
        
        # 注册阶段处理器
        self._handlers: Dict[PhaseType, Callable] = phase_handlers or {}
        if not self._handlers:
            self._register_default_handlers()
    
    def _register_default_handlers(self) -> None:
        """注册默认阶段处理器"""
        # 延迟导入，避免循环依赖
        from .phases.clarify import ClarifyPhase
        from .phases.plan import PlanPhase
        from .phases.implement import ImplementPhase
        from .phases.review import ReviewPhase
        from .phases.confirm import ConfirmPhase
        
        self._handlers = {
            PhaseType.CLARIFY: ClarifyPhase(self.context).execute,
            PhaseType.PLAN: PlanPhase(self.context).execute,
            PhaseType.IMPLEMENT: ImplementPhase(self.context).execute,
            PhaseType.REVIEW: ReviewPhase(self.context).execute,
            PhaseType.CONFIRM: ConfirmPhase(self.context).execute,
        }
    
    def execute(self, requirement: str) -> PipelineResult:
        """
        执行完整流水线
        
        Args:
            requirement: 需求描述
            
        Returns:
            PipelineResult: 流水线执行结果
        """
        logger.info(f"开始执行流水线 v{self.VERSION}")
        logger.info(f"需求: {requirement[:100]}...")
        
        result = PipelineResult(success=True)
        phases = [
            PhaseType.CLARIFY,
            PhaseType.PLAN,
            PhaseType.IMPLEMENT,
            PhaseType.REVIEW,
            PhaseType.CONFIRM,
        ]
        
        for phase in phases:
            phase_result = self._execute_phase(phase, requirement)
            result.phases.append(phase_result)
            
            if not phase_result.success:
                result.success = False
                result.error = phase_result.error
                logger.error(f"阶段 {phase.value} 失败: {phase_result.error}")
                break
            
            # 传递阶段数据
            self._phase_data[phase.value] = phase_result.data
            logger.info(f"阶段 {phase.value} 完成")
        
        # 收集输出文件
        if result.success:
            result.output_files = self._collect_output_files()
        
        return result
    
    def _execute_phase(self, phase: PhaseType, requirement: str) -> PhaseResult:
        """
        执行单个阶段
        
        Args:
            phase: 阶段类型
            requirement: 需求描述
            
        Returns:
            PhaseResult: 阶段执行结果
        """
        handler = self._handlers.get(phase)
        if not handler:
            return PhaseResult(
                phase=phase,
                success=False,
                error=f"未注册的阶段处理器: {phase.value}",
            )
        
        start_time = datetime.now()
        
        try:
            # 执行阶段
            data = handler(requirement, self._phase_data)
            duration = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return PhaseResult(
                phase=phase,
                success=True,
                data=data,
                duration_ms=duration,
            )
            
        except PhaseExecutionError as e:
            duration = int((datetime.now() - start_time).total_seconds() * 1000)
            return PhaseResult(
                phase=phase,
                success=False,
                error=str(e),
                duration_ms=duration,
            )
            
        except Exception as e:
            duration = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.exception(f"阶段 {phase.value} 执行异常")
            return PhaseResult(
                phase=phase,
                success=False,
                error=f"未预期的错误: {str(e)}",
                duration_ms=duration,
            )
    
    def _collect_output_files(self) -> List[str]:
        """收集所有输出文件"""
        files = []
        
        # 从实现阶段收集
        impl_data = self._phase_data.get(PhaseType.IMPLEMENT.value, {})
        if isinstance(impl_data, dict):
            files.extend(impl_data.get("output_files", []))
        
        return files
    
    def get_phase_data(self, phase: PhaseType) -> Any:
        """获取阶段数据"""
        return self._phase_data.get(phase.value)


# =============================================================================
# 便捷函数
# =============================================================================

def create_orchestrator(
    project_dir: str,
    requirement: str,
    workflow_type: str = "full_stack_development",
) -> LightweightOrchestrator:
    """
    创建编排器实例
    
    Args:
        project_dir: 项目目录
        requirement: 需求描述
        workflow_type: 工作流类型
        
    Returns:
        LightweightOrchestrator: 编排器实例
    """
    context = ExecutionContext(
        project_root=Path(project_dir),
        requirement=requirement,
        workflow_type=workflow_type,
    )
    return LightweightOrchestrator(context)


def run_pipeline(
    project_dir: str,
    requirement: str,
    workflow_type: str = "full_stack_development",
) -> Dict[str, Any]:
    """
    运行完整流水线
    
    Args:
        project_dir: 项目目录
        requirement: 需求描述
        workflow_type: 工作流类型
        
    Returns:
        执行结果字典
    """
    orchestrator = create_orchestrator(project_dir, requirement, workflow_type)
    result = orchestrator.execute(requirement)
    return result.to_dict()


__all__ = [
    "LightweightOrchestrator",
    "create_orchestrator",
    "run_pipeline",
]
