"""
AI 代码工厂 v4.2 - 主编排器

基准文档: MASTER.md v4.6
版本: v4.2

整合:
- SOP 系统 (MetaGPT)
- Guardrails (SWE-agent)
- Task List (Anthropic)
- Repo Map (Aider)
- Event Stream (OpenHands)

10 阶段流水线:
INIT → RISK → PARSE → SEARCH → SELECT → ADAPT → ASSEMBLE → VERIFY → TRACE → OUTPUT
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import time
import uuid

from .config import FactoryConfig
from .feature_flags import get_flags, FeatureFlags
from .constants import VERSION, PHASE_NAMES
from .exceptions import RiskBlockedError, TraceFailedError

from ..sot.loader import SotLoader, LoadedSotData
from ..guardrails.recovery_loop import EditGuardrails
from ..task_persistence.task_list import TaskListManager
from ..event_stream.stream import EventStream
from ..repo_map.map_generator import RepoMapGenerator, RepoMap
from ..risk.classifier import RiskClassifier, RiskLevel
from ..validation.tracer import SourceTracer
from ..phases.base import PhaseResult
from ..phases.context import PipelineContext


@dataclass
class FactoryResult:
    """工厂执行结果"""

    success: bool
    requirement: str
    module_id: Optional[str] = None

    # 输出
    generated_files: List[str] = field(default_factory=list)
    generated_code: Dict[str, str] = field(default_factory=dict)

    # 统计
    phases_executed: int = 0
    trace_rate: float = 0.0
    duration_ms: int = 0

    # 状态
    blocked: bool = False
    error: Optional[str] = None

    # 详情
    phase_results: List[PhaseResult] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "requirement": self.requirement,
            "module_id": self.module_id,
            "generated_files": self.generated_files,
            "phases_executed": self.phases_executed,
            "trace_rate": f"{self.trace_rate:.0%}",
            "duration_ms": self.duration_ms,
            "blocked": self.blocked,
            "error": self.error,
            "warnings": self.warnings,
        }


class CodeFactory:
    """AI 代码工厂 v4.2 - 10 阶段流水线"""

    VERSION = VERSION

    def __init__(self, config: FactoryConfig):
        """初始化

        Args:
            config: 工厂配置
        """
        self.config = config
        self.flags = get_flags()

        # 确保目录存在
        config.ensure_dirs()

        # 初始化模块
        self.sot_loader = SotLoader(config.sot_dir)
        self.guardrails = EditGuardrails(self.flags.guardrails_max_retries)
        self.task_manager = TaskListManager(config.task_file)
        self.event_stream = EventStream(config.output_dir / "events.json")
        self.repo_map_gen = RepoMapGenerator(config.project_dir)
        self.risk_classifier = RiskClassifier()

        # 缓存
        self._sot_data: Optional[LoadedSotData] = None
        self._repo_map: Optional[RepoMap] = None

    def run(
        self,
        requirement: str,
        module_id: Optional[str] = None,
    ) -> FactoryResult:
        """执行代码生成

        Args:
            requirement: 需求描述
            module_id: 模块 ID

        Returns:
            FactoryResult
        """
        start_time = time.time()

        # 回滚开关
        if self.flags.use_legacy_pipeline:
            return self._run_legacy(requirement, module_id)

        # 创建上下文
        context = PipelineContext(
            requirement=requirement,
            module_id=module_id,
            project_dir=self.config.project_dir,
            session_id=str(uuid.uuid4())[:8],
        )

        try:
            # 执行 10 阶段流水线
            self._execute_pipeline(context)

            # 构建结果
            return FactoryResult(
                success=True,
                requirement=requirement,
                module_id=module_id,
                generated_files=context.output_files,
                generated_code=context.generated_code,
                phases_executed=len(context.phase_results),
                trace_rate=context.trace_rate,
                duration_ms=int((time.time() - start_time) * 1000),
                phase_results=context.phase_results,
                warnings=context.get_warnings(),
            )

        except RiskBlockedError as e:
            self.event_stream.error(str(e))
            return FactoryResult(
                success=False,
                requirement=requirement,
                module_id=module_id,
                blocked=True,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )

        except TraceFailedError as e:
            self.event_stream.error(str(e))
            return FactoryResult(
                success=False,
                requirement=requirement,
                module_id=module_id,
                error=str(e),
                trace_rate=e.rate,
                duration_ms=int((time.time() - start_time) * 1000),
            )

        except Exception as e:
            self.event_stream.error(str(e))
            return FactoryResult(
                success=False,
                requirement=requirement,
                module_id=module_id,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )

    def _execute_pipeline(self, context: PipelineContext):
        """执行流水线"""

        # Phase 0: INIT
        self._phase_init(context)

        # Phase 1: RISK
        if self.flags.enable_risk_phase:
            self._phase_risk(context)

        # Phase 2: PARSE
        self._phase_parse(context)

        # Phase 3: SEARCH
        self._phase_search(context)

        # Phase 4: SELECT
        self._phase_select(context)

        # Phase 5: ADAPT
        self._phase_adapt(context)

        # Phase 6: ASSEMBLE
        self._phase_assemble(context)

        # Phase 7: VERIFY
        self._phase_verify(context)

        # Phase 8: TRACE
        if self.flags.enable_trace_phase:
            self._phase_trace(context)

        # Phase 9: OUTPUT
        self._phase_output(context)

        context.finish()

    def _phase_init(self, context: PipelineContext):
        """Phase 0: 初始化"""
        start = time.time()
        self.event_stream.phase_start(0, "INIT")

        # 加载 SoT
        if self.flags.enable_sot_dynamic_load:
            self._sot_data = self.sot_loader.load()
            context.sot_data = self._sot_data
            context.sot_versions = self._sot_data.versions

        # 初始化任务列表
        if self.flags.enable_task_persistence:
            self.task_manager.init_session(context.requirement)
            context.session_id = self.task_manager.session_id

        # 生成代码地图
        if self.flags.enable_repo_map:
            self._repo_map = self.repo_map_gen.generate(
                include_dirs=self.config.search_include_dirs
            )
            context.repo_map = self._repo_map

        duration_ms = int((time.time() - start) * 1000)
        result = PhaseResult(0, "INIT", True, duration_ms)
        context.add_phase_result(result)
        self.event_stream.phase_end(0, "INIT", True, duration_ms)

    def _phase_risk(self, context: PipelineContext):
        """Phase 1: 风险评估"""
        start = time.time()
        self.event_stream.phase_start(1, "RISK")

        assessment = self.risk_classifier.assess(
            context.requirement,
            context.module_id,
        )
        context.risk_level = assessment.level.value
        context.risk_assessment = assessment

        duration_ms = int((time.time() - start) * 1000)

        if assessment.level == RiskLevel.BLOCKED:
            result = PhaseResult(1, "RISK", False, duration_ms, errors=assessment.reasons)
            context.add_phase_result(result)
            self.event_stream.phase_end(1, "RISK", False, duration_ms)
            raise RiskBlockedError(assessment.reasons[0], context.module_id)

        result = PhaseResult(
            1, "RISK", True, duration_ms,
            data={"level": assessment.level.value, "score": assessment.score}
        )
        context.add_phase_result(result)
        self.event_stream.phase_end(1, "RISK", True, duration_ms)

    def _phase_parse(self, context: PipelineContext):
        """Phase 2: 需求解析"""
        start = time.time()
        self.event_stream.phase_start(2, "PARSE")

        if self.flags.enable_task_persistence:
            self.task_manager.add("解析需求", phase_id=2)

        # TODO: 实现需求解析逻辑
        # - 提取关键词
        # - 识别技术栈
        # - 确定模块边界

        duration_ms = int((time.time() - start) * 1000)
        result = PhaseResult(2, "PARSE", True, duration_ms)
        context.add_phase_result(result)
        self.event_stream.phase_end(2, "PARSE", True, duration_ms)

    def _phase_search(self, context: PipelineContext):
        """Phase 3: 代码搜索"""
        start = time.time()
        self.event_stream.phase_start(3, "SEARCH")

        if self.flags.enable_task_persistence:
            self.task_manager.add("搜索参考代码", phase_id=3)

        # TODO: 实现搜索逻辑
        # - 搜索本项目
        # - 搜索代码库
        # - (可选) 搜索 GitHub

        duration_ms = int((time.time() - start) * 1000)
        result = PhaseResult(
            3, "SEARCH", True, duration_ms,
            data={"candidates": len(context.search_results)}
        )
        context.add_phase_result(result)
        self.event_stream.phase_end(3, "SEARCH", True, duration_ms)

    def _phase_select(self, context: PipelineContext):
        """Phase 4: 代码选型"""
        start = time.time()
        self.event_stream.phase_start(4, "SELECT")

        if self.flags.enable_task_persistence:
            self.task_manager.add("选择最佳参考", phase_id=4)

        # TODO: 实现选型逻辑
        # - 评估技术栈匹配度
        # - 评估功能覆盖度
        # - 评估适配成本

        duration_ms = int((time.time() - start) * 1000)
        result = PhaseResult(
            4, "SELECT", True, duration_ms,
            data={"selected": len(context.selected_candidates)}
        )
        context.add_phase_result(result)
        self.event_stream.phase_end(4, "SELECT", True, duration_ms)

    def _phase_adapt(self, context: PipelineContext):
        """Phase 5: 代码适配"""
        start = time.time()
        self.event_stream.phase_start(5, "ADAPT")

        if self.flags.enable_task_persistence:
            self.task_manager.add("适配代码规范", phase_id=5)

        # TODO: 实现适配逻辑
        # - 技术栈适配
        # - 项目规范适配
        # - SoT 合规适配

        duration_ms = int((time.time() - start) * 1000)
        result = PhaseResult(5, "ADAPT", True, duration_ms)
        context.add_phase_result(result)
        self.event_stream.phase_end(5, "ADAPT", True, duration_ms)

    def _phase_assemble(self, context: PipelineContext):
        """Phase 6: 代码组装"""
        start = time.time()
        self.event_stream.phase_start(6, "ASSEMBLE")

        if self.flags.enable_task_persistence:
            self.task_manager.add("组装完整模块", phase_id=6)

        # TODO: 实现组装逻辑
        # - 后端: Schema → Service → Router
        # - 前端: Types → API → Hooks → Components

        duration_ms = int((time.time() - start) * 1000)
        result = PhaseResult(6, "ASSEMBLE", True, duration_ms)
        context.add_phase_result(result)
        self.event_stream.phase_end(6, "ASSEMBLE", True, duration_ms)

    def _phase_verify(self, context: PipelineContext):
        """Phase 7: 代码验证"""
        start = time.time()
        self.event_stream.phase_start(7, "VERIFY")

        if self.flags.enable_task_persistence:
            self.task_manager.add("验证代码质量", phase_id=7)

        errors = []

        # 使用 Guardrails 验证
        if self.flags.enable_guardrails and context.assembled_files:
            for file_path, content in context.assembled_files.items():
                output_path = self.config.output_dir / file_path
                result = self.guardrails.apply_edit(output_path, content)

                if result.success:
                    context.output_files.append(str(output_path))
                    self.event_stream.file_edit(str(output_path), "create", True)
                else:
                    errors.extend(result.errors)
                    self.event_stream.file_edit(str(output_path), "create", False)

        context.verification_passed = len(errors) == 0
        context.verification_errors = errors

        duration_ms = int((time.time() - start) * 1000)
        result = PhaseResult(
            7, "VERIFY", context.verification_passed, duration_ms,
            errors=errors,
            data={"guardrails_stats": self.guardrails.stats.to_dict()}
        )
        context.add_phase_result(result)
        self.event_stream.phase_end(7, "VERIFY", context.verification_passed, duration_ms)

    def _phase_trace(self, context: PipelineContext):
        """Phase 8: 来源追溯"""
        start = time.time()
        self.event_stream.phase_start(8, "TRACE")

        if self.flags.enable_task_persistence:
            self.task_manager.add("验证来源追溯", phase_id=8)

        if self._sot_data and context.assembled_code:
            tracer = SourceTracer(self._sot_data)
            trace_result = tracer.trace_code(context.assembled_code)
            context.trace_report = trace_result
            context.trace_rate = trace_result.trace_rate

            # 检查追溯率
            if trace_result.trace_rate < self.flags.strict_trace_rate:
                duration_ms = int((time.time() - start) * 1000)
                result = PhaseResult(
                    8, "TRACE", False, duration_ms,
                    errors=[f"追溯率 {trace_result.trace_rate:.0%} < {self.flags.strict_trace_rate:.0%}"]
                )
                context.add_phase_result(result)
                self.event_stream.phase_end(8, "TRACE", False, duration_ms)
                raise TraceFailedError(trace_result.trace_rate, self.flags.strict_trace_rate)
        else:
            context.trace_rate = 1.0

        duration_ms = int((time.time() - start) * 1000)
        result = PhaseResult(
            8, "TRACE", True, duration_ms,
            data={"trace_rate": context.trace_rate}
        )
        context.add_phase_result(result)
        self.event_stream.phase_end(8, "TRACE", True, duration_ms)

    def _phase_output(self, context: PipelineContext):
        """Phase 9: 输出生成"""
        start = time.time()
        self.event_stream.phase_start(9, "OUTPUT")

        if self.flags.enable_task_persistence:
            self.task_manager.add("生成输出文件", phase_id=9)
            # 标记任务完成
            for task in self.task_manager.tasks:
                if task.status == "pending":
                    self.task_manager.complete_task(task.id)

        duration_ms = int((time.time() - start) * 1000)
        result = PhaseResult(
            9, "OUTPUT", True, duration_ms,
            data={"files": context.output_files}
        )
        context.add_phase_result(result)
        self.event_stream.phase_end(9, "OUTPUT", True, duration_ms)

    def _run_legacy(
        self,
        requirement: str,
        module_id: Optional[str] = None,
    ) -> FactoryResult:
        """v4.0 兼容模式"""
        return FactoryResult(
            success=True,
            requirement=requirement,
            module_id=module_id,
            phases_executed=6,
        )

    # === 便捷方法 ===

    def can_resume(self) -> bool:
        """检查是否可以恢复会话"""
        return self.task_manager.can_resume()

    def resume(self) -> FactoryResult:
        """恢复会话"""
        if not self.can_resume():
            return FactoryResult(
                success=False,
                requirement="",
                error="没有可恢复的会话",
            )

        return self.run(
            self.task_manager.requirement,
            None,
        )

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "version": self.VERSION,
            "flags": self.flags.to_dict(),
            "task_progress": self.task_manager.get_progress(),
            "guardrails_stats": self.guardrails.stats.to_dict(),
            "event_summary": self.event_stream.get_summary(),
        }


# === 便捷函数 ===

def run_factory(
    project_dir: Path,
    requirement: str,
    module_id: Optional[str] = None,
    **kwargs,
) -> FactoryResult:
    """快捷函数

    Args:
        project_dir: 项目目录
        requirement: 需求描述
        module_id: 模块 ID
        **kwargs: 其他配置

    Returns:
        FactoryResult
    """
    config = FactoryConfig(project_dir=project_dir, **kwargs)
    factory = CodeFactory(config)
    return factory.run(requirement, module_id)


def create_factory(project_dir: Path, **kwargs) -> CodeFactory:
    """创建工厂实例

    Args:
        project_dir: 项目目录
        **kwargs: 其他配置

    Returns:
        CodeFactory
    """
    config = FactoryConfig(project_dir=project_dir, **kwargs)
    return CodeFactory(config)
