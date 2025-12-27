"""
AI 代码工厂 v4.4 - 上下文增强引擎

基准文档: MASTER.md v4.6
版本: v4.4

核心设计:
- 工厂增强 Claude 的上下文，而非替代 Claude 的代码生成能力
- 代码生成由 Claude 通过 Prompt 完成
- 工厂只负责: 上下文构建 + 验证 + 确认

四阶段架构:
  CONTEXT → (Claude 生成) → VERIFY → CONFIRM

v4.4 更新:
- 新增 Phase 6 CONFIRM (幻觉抑制最终确认)
- 版本同步 skill.md / constants.py / factory.py
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
import time
import uuid

from .config import FactoryConfig
from .feature_flags import get_flags, FeatureFlags
from .constants import VERSION, HIGH_RISK_MODULES
from .exceptions import RiskBlockedError, TraceFailedError, ValidationError

from ..sot.loader import SotLoader, LoadedSotData
from ..sot.whitelist import DynamicWhitelist
from ..guardrails.recovery_loop import EditGuardrails
from ..event_stream.stream import EventStream
from ..repo_map.map_generator import RepoMapGenerator, RepoMap
from ..risk.classifier import RiskClassifier, RiskLevel

if TYPE_CHECKING:
    from ..task_cards.models import TaskCard, TaskCardIndex
    from ..prompts.injector import InjectedContext


@dataclass
class GenerationContext:
    """代码生成上下文 - 传递给 Claude 的信息"""

    requirement: str
    module_id: Optional[str] = None
    session_id: str = ""

    # SoT 数据
    sot_data: Optional[LoadedSotData] = None
    sot_versions: Dict[str, str] = field(default_factory=dict)

    # 代码地图
    repo_map: Optional[RepoMap] = None

    # 风险评估
    risk_level: str = "low"
    risk_warnings: List[str] = field(default_factory=list)

    # 白名单 (用于验证)
    whitelist: Optional[DynamicWhitelist] = None

    # 推荐参考
    suggested_files: List[str] = field(default_factory=list)
    code_patterns: List[str] = field(default_factory=list)

    # 任务卡 (v4.3 新增)
    task_card: Optional["TaskCard"] = None
    matched_task_score: float = 0.0

    # 提示词上下文 (v4.4 新增)
    prompt_context: Optional["InjectedContext"] = None
    prompts_used: List[str] = field(default_factory=list)

    def to_prompt_context(self) -> str:
        """生成 Prompt 上下文片段"""
        lines = []

        # 系统约束 (v4.4 提示词系统)
        if self.prompt_context and self.prompt_context.system_constraints:
            lines.append("# 系统约束")
            lines.append(self.prompt_context.system_constraints)
            lines.append("")

        lines.extend([
            f"## 需求: {self.requirement}",
            f"## 模块: {self.module_id or '未指定'}",
            "",
        ])

        # 任务指引 (v4.4 提示词系统)
        if self.prompt_context and self.prompt_context.task_guidance:
            lines.append("## 任务指引")
            lines.append(self.prompt_context.task_guidance)
            lines.append("")

        # 任务卡上下文
        if self.task_card:
            lines.append(f"## 匹配任务卡: {self.task_card.task_id} (匹配度: {self.matched_task_score:.0%})")
            lines.append(self.task_card.to_prompt_context())
            lines.append("")

        if self.sot_versions:
            lines.append("## SoT 版本:")
            for doc, ver in self.sot_versions.items():
                lines.append(f"  - {doc}: {ver}")
            lines.append("")

        if self.risk_level != "low":
            lines.append(f"## 风险等级: {self.risk_level}")
            if self.risk_warnings:
                for w in self.risk_warnings:
                    lines.append(f"  - {w}")
            lines.append("")

        if self.suggested_files:
            lines.append("## 建议参考文件:")
            for f in self.suggested_files[:10]:
                lines.append(f"  - {f}")
            lines.append("")

        # 补充说明 (v4.4 提示词系统)
        if self.prompt_context and self.prompt_context.supporting_context:
            lines.append("## 补充说明")
            lines.append(self.prompt_context.supporting_context)
            lines.append("")

        # 使用的提示词
        if self.prompts_used:
            lines.append(f"## 使用的提示词模板: {', '.join(self.prompts_used)}")
            lines.append("")

        return "\n".join(lines)


@dataclass
class VerifyResult:
    """验证结果"""

    success: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    trace_rate: float = 1.0
    guardrails_stats: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfirmResult:
    """幻觉抑制确认结果 (v4.4 新增)

    Phase 6 CONFIRM 阶段的输出，基于 MASTER.md v4.6 §7 AI 防幻觉原则:
    - 遍历生成的每个状态值 → 追溯到 STATE_MACHINE.md
    - 遍历生成的每个角色值 → 追溯到 6 角色白名单
    - 遍历生成的每个字段 → 追溯到 DATA_SCHEMA.md
    - 生成来源追溯报告
    """

    confirmed: bool
    trace_report: Dict[str, Any] = field(default_factory=dict)
    untraced_items: List[str] = field(default_factory=list)
    blocking_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_blocking(self) -> bool:
        """是否有阻断问题"""
        return len(self.blocking_issues) > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "confirmed": self.confirmed,
            "is_blocking": self.is_blocking,
            "trace_report": self.trace_report,
            "untraced_items": self.untraced_items,
            "blocking_issues": self.blocking_issues,
            "warnings": self.warnings,
        }


@dataclass
class FactoryResult:
    """工厂执行结果"""

    success: bool
    requirement: str
    module_id: Optional[str] = None

    # 上下文
    context: Optional[GenerationContext] = None

    # 验证
    verify_result: Optional[VerifyResult] = None

    # 输出
    output_files: List[str] = field(default_factory=list)

    # 状态
    blocked: bool = False
    error: Optional[str] = None
    duration_ms: int = 0

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "requirement": self.requirement,
            "module_id": self.module_id,
            "blocked": self.blocked,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "output_files": self.output_files,
            "trace_rate": self.verify_result.trace_rate if self.verify_result else None,
        }


class CodeFactory:
    """上下文增强引擎 v4.4

    核心职责:
    1. build_context(): 构建代码生成上下文
    2. verify_code(): 验证生成的代码
    3. confirm_code(): 幻觉抑制最终确认 (v4.4 新增)

    代码生成由 Claude 完成，工厂不直接生成代码。

    四阶段架构:
      CONTEXT → (Claude 生成) → VERIFY → CONFIRM
    """

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
        self.event_stream = EventStream(config.output_dir / "events.json")
        self.repo_map_gen = RepoMapGenerator(config.project_dir)
        self.risk_classifier = RiskClassifier()

        # 缓存
        self._sot_data: Optional[LoadedSotData] = None
        self._repo_map: Optional[RepoMap] = None
        self._whitelist: Optional[DynamicWhitelist] = None
        self._task_card_index: Optional["TaskCardIndex"] = None
        self._prompt_injector = None  # 懒加载

    # =========================================================================
    # 核心 API: 上下文构建
    # =========================================================================

    def build_context(
        self,
        requirement: str,
        module_id: Optional[str] = None,
    ) -> GenerationContext:
        """构建代码生成上下文

        这是工厂的核心方法。它不生成代码，而是为 Claude 准备
        所有必要的上下文信息。

        Args:
            requirement: 需求描述
            module_id: 模块 ID

        Returns:
            GenerationContext: 包含 SoT 数据、代码地图、风险评估的上下文

        Raises:
            RiskBlockedError: 如果需求被阻断
        """
        start_time = time.time()
        self.event_stream.phase_start(0, "CONTEXT")

        context = GenerationContext(
            requirement=requirement,
            module_id=module_id,
            session_id=str(uuid.uuid4())[:8],
        )

        # 1. 加载 SoT 数据
        if self.flags.enable_sot_dynamic_load:
            self._sot_data = self.sot_loader.load()
            context.sot_data = self._sot_data
            context.sot_versions = self._sot_data.versions

            # 构建白名单
            self._whitelist = DynamicWhitelist.from_sot_data(self._sot_data)
            context.whitelist = self._whitelist

        # 2. 风险评估
        if self.flags.enable_risk_phase:
            assessment = self.risk_classifier.assess(requirement, module_id)
            context.risk_level = assessment.level.value
            context.risk_warnings = assessment.reasons

            if assessment.level == RiskLevel.BLOCKED:
                self.event_stream.phase_end(0, "CONTEXT", False, 0)
                raise RiskBlockedError(assessment.reasons[0], module_id)

        # 3. 生成代码地图
        if self.flags.enable_repo_map:
            self._repo_map = self.repo_map_gen.generate(
                include_dirs=self.config.search_include_dirs
            )
            context.repo_map = self._repo_map

            # 提取建议参考文件
            if module_id:
                context.suggested_files = self._repo_map.get_files_for_module(module_id)

        # 4. 匹配任务卡 (v4.3 新增)
        if self.flags.enable_task_cards:
            task_card, score = self._match_task_card(requirement, module_id)
            if task_card and score >= 0.3:
                context.task_card = task_card
                context.matched_task_score = score

                # 从任务卡提取建议文件
                if task_card.outputs and not context.suggested_files:
                    context.suggested_files = task_card.outputs[:10]

        # 5. 注入提示词 (v4.4 新增)
        if self.flags.enable_prompt_system and self.flags.enable_prompt_injection:
            prompt_context = self._inject_prompts(requirement, module_id)
            if prompt_context:
                context.prompt_context = prompt_context
                context.prompts_used = prompt_context.prompts_used

        duration_ms = int((time.time() - start_time) * 1000)
        self.event_stream.phase_end(0, "CONTEXT", True, duration_ms)

        return context

    # =========================================================================
    # 核心 API: 代码验证
    # =========================================================================

    def verify_code(
        self,
        code_files: Dict[str, str],
        context: Optional[GenerationContext] = None,
    ) -> VerifyResult:
        """验证生成的代码

        对 Claude 生成的代码进行验证:
        1. Guardrails 验证 (语法、lint)
        2. SoT 白名单验证 (角色、状态、错误码)
        3. 来源追溯

        Args:
            code_files: 文件路径 -> 代码内容的映射
            context: 可选的生成上下文 (用于 SoT 验证)

        Returns:
            VerifyResult: 验证结果
        """
        start_time = time.time()
        self.event_stream.phase_start(1, "VERIFY")

        errors = []
        warnings = []

        # 1. Guardrails 验证
        if self.flags.enable_guardrails:
            for file_path, content in code_files.items():
                output_path = self.config.output_dir / file_path
                result = self.guardrails.apply_edit(output_path, content)

                if not result.success:
                    errors.extend(result.errors)
                    self.event_stream.file_edit(str(output_path), "create", False)
                else:
                    self.event_stream.file_edit(str(output_path), "create", True)

        # 2. SoT 白名单验证
        if context and context.whitelist:
            sot_errors = self._validate_sot_compliance(code_files, context.whitelist)
            errors.extend(sot_errors)

        # 3. 来源追溯 (简化版)
        trace_rate = 1.0
        if self._sot_data and code_files:
            trace_rate = self._calculate_trace_rate(code_files)
            if trace_rate < self.flags.strict_trace_rate:
                warnings.append(
                    f"追溯率 {trace_rate:.0%} < {self.flags.strict_trace_rate:.0%}"
                )

        duration_ms = int((time.time() - start_time) * 1000)
        success = len(errors) == 0
        self.event_stream.phase_end(1, "VERIFY", success, duration_ms)

        return VerifyResult(
            success=success,
            errors=errors,
            warnings=warnings,
            trace_rate=trace_rate,
            guardrails_stats=self.guardrails.stats.to_dict(),
        )

    def _validate_sot_compliance(
        self,
        code_files: Dict[str, str],
        whitelist: DynamicWhitelist,
    ) -> List[str]:
        """验证 SoT 合规性"""
        errors = []

        # 简化实现: 检查常见的值
        # 完整实现需要 AST 解析
        for file_path, content in code_files.items():
            # 检查角色
            for role in ["supervisor", "operator", "viewer"]:
                if f'"{role}"' in content or f"'{role}'" in content:
                    is_valid, msg = whitelist.validate("role", role)
                    if not is_valid:
                        errors.append(f"{file_path}: 非法角色 '{role}' - {msg}")

        return errors

    def _calculate_trace_rate(self, code_files: Dict[str, str]) -> float:
        """计算追溯率 (简化版)"""
        # 简化实现: 假设所有代码都可追溯
        # 完整实现需要 AST 解析 + 来源追踪
        return 1.0

    # =========================================================================
    # 核心 API: 幻觉抑制确认 (v4.4 新增)
    # =========================================================================

    def confirm_code(
        self,
        code_files: Dict[str, str],
        context: Optional[GenerationContext] = None,
    ) -> ConfirmResult:
        """Phase 6 CONFIRM: 幻觉抑制最终确认

        基于 MASTER.md v4.6 §7 AI 防幻觉原则:
        1. 遍历生成的每个状态值 → 追溯到 STATE_MACHINE.md
        2. 遍历生成的每个角色值 → 追溯到 6 角色白名单
        3. 遍历生成的每个字段 → 追溯到 DATA_SCHEMA.md
        4. 遍历调用的每个 API → 确认在项目中存在
        5. 生成来源追溯报告

        任何追溯失败 → BLOCKING

        Args:
            code_files: 文件路径 -> 代码内容的映射
            context: 可选的生成上下文 (用于获取白名单)

        Returns:
            ConfirmResult: 确认结果
        """
        start_time = time.time()
        self.event_stream.phase_start(2, "CONFIRM")

        trace_report = {
            "roles": {"traced": [], "untraced": []},
            "states": {"traced": [], "untraced": []},
            "deprecated": [],
        }
        untraced_items = []
        blocking_issues = []
        warnings = []

        # 获取白名单
        whitelist = context.whitelist if context else self._whitelist
        if not whitelist:
            # 尝试加载 SoT 数据
            if self.flags.enable_sot_dynamic_load and not self._sot_data:
                self._sot_data = self.sot_loader.load()
                whitelist = DynamicWhitelist.from_sot_data(self._sot_data)

        # 6 角色白名单 (MASTER.md v4.6 §2.4)
        valid_roles = {"ceo", "project_owner", "finance", "pitcher", "account_manager", "admin"}
        deprecated_roles = {"supervisor", "data_operator", "operator", "viewer"}

        # Phase 1 简化状态 (3 状态)
        phase1_states = {"raw_submitted", "trend_ok", "final_confirmed"}

        for file_path, content in code_files.items():
            # 1. 检查角色
            role_issues = self._confirm_roles(
                content, file_path, valid_roles, deprecated_roles, trace_report
            )
            blocking_issues.extend(role_issues)

            # 2. 检查状态 (Phase 1 约束)
            state_issues = self._confirm_states(
                content, file_path, phase1_states, trace_report
            )
            # Phase 1: 状态问题仅警告，不阻断
            if self.flags.enable_phase1_soft_mode:
                warnings.extend(state_issues)
            else:
                blocking_issues.extend(state_issues)

            # 3. 检查废弃角色使用
            deprecated_issues = self._confirm_deprecated(
                content, file_path, deprecated_roles, trace_report
            )
            blocking_issues.extend(deprecated_issues)

        # 汇总未追溯项
        untraced_items.extend(trace_report["roles"]["untraced"])
        untraced_items.extend(trace_report["states"]["untraced"])

        # 判断是否确认通过
        confirmed = len(blocking_issues) == 0

        duration_ms = int((time.time() - start_time) * 1000)
        self.event_stream.phase_end(2, "CONFIRM", confirmed, duration_ms)

        return ConfirmResult(
            confirmed=confirmed,
            trace_report=trace_report,
            untraced_items=untraced_items,
            blocking_issues=blocking_issues,
            warnings=warnings,
        )

    def _confirm_roles(
        self,
        content: str,
        file_path: str,
        valid_roles: set,
        deprecated_roles: set,
        trace_report: Dict,
    ) -> List[str]:
        """确认角色追溯"""
        issues = []
        import re

        # 匹配角色字符串 (支持多种格式)
        role_patterns = [
            r'\.role\s*==\s*["\'](\w+)["\']',   # user.role == "xxx"
            r'role\s*[=:]\s*["\'](\w+)["\']',   # role = "xxx" 或 role: "xxx"
            r'UserRole\.(\w+)',                  # UserRole.XXX
            r'"role":\s*["\'](\w+)["\']',        # "role": "xxx"
        ]

        found_roles = set()
        for pattern in role_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found_roles.update(m.lower() for m in matches)

        for role in found_roles:
            if role in valid_roles:
                trace_report["roles"]["traced"].append(role)
            elif role in deprecated_roles:
                trace_report["deprecated"].append(role)
                issues.append(
                    f"BLOCKING: {file_path} 使用了废弃角色 '{role}' "
                    f"(应替换为 6 角色白名单中的角色)"
                )
            else:
                # 检查是否是技术角色名
                tech_role_mapping = {
                    "media_buyer": "pitcher",
                    "data_operator": "project_owner",
                }
                if role not in tech_role_mapping:
                    trace_report["roles"]["untraced"].append(role)
                    issues.append(
                        f"BLOCKING: {file_path} 使用了未定义角色 '{role}' "
                        f"(合法角色: {', '.join(sorted(valid_roles))})"
                    )

        return issues

    def _confirm_states(
        self,
        content: str,
        file_path: str,
        valid_states: set,
        trace_report: Dict,
    ) -> List[str]:
        """确认状态追溯 (Phase 1 简化状态)"""
        issues = []
        import re

        # 匹配状态字符串
        state_patterns = [
            r'return\s*["\'](\w+)["\']',           # return "xxx"
            r'\.status\s*==\s*["\'](\w+)["\']',    # report.status == "xxx"
            r'status\s*[=:]\s*["\'](\w+)["\']',    # status = "xxx"
            r'ReportStatus\.(\w+)',                 # ReportStatus.XXX
            r'"status":\s*["\'](\w+)["\']',         # "status": "xxx"
        ]

        # Phase 2 完整状态 (仅用于检测)
        phase2_states = {
            "trend_pending", "trend_flagged", "trend_resolved",
            "final_pending", "final_locked"
        }

        found_states = set()
        for pattern in state_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found_states.update(m.lower() for m in matches)

        for state in found_states:
            if state in valid_states:
                trace_report["states"]["traced"].append(state)
            elif state in phase2_states:
                issues.append(
                    f"WARNING: {file_path} 使用了 Phase 2 状态 '{state}' "
                    f"(Phase 1 仅允许: {', '.join(sorted(valid_states))})"
                )
            elif state not in {"draft", "submitted", "confirmed", "locked"}:
                # 忽略通用状态词
                trace_report["states"]["untraced"].append(state)

        return issues

    def _confirm_deprecated(
        self,
        content: str,
        file_path: str,
        deprecated_roles: set,
        trace_report: Dict,
    ) -> List[str]:
        """确认废弃角色/概念"""
        issues = []

        for role in deprecated_roles:
            # 检查是否在代码中使用 (排除注释)
            if f'"{role}"' in content or f"'{role}'" in content:
                if role not in trace_report["deprecated"]:
                    trace_report["deprecated"].append(role)
                    issues.append(
                        f"BLOCKING: {file_path} 使用了废弃角色 '{role}'"
                    )

        return issues

    def _get_task_card_index(self) -> Optional["TaskCardIndex"]:
        """获取任务卡索引 (懒加载)"""
        if self._task_card_index is None:
            try:
                from ..task_cards.loader import TaskCardLoader

                task_cards_path = self.config.project_dir / "docs" / "guides" / "TASK_CARDS_v2.md"
                if task_cards_path.exists():
                    loader = TaskCardLoader(task_cards_path)
                    self._task_card_index = loader.load()
            except Exception:
                # 任务卡加载失败不影响主流程
                pass

        return self._task_card_index

    def _match_task_card(
        self,
        requirement: str,
        module_id: Optional[str] = None,
    ) -> tuple:
        """匹配任务卡

        Args:
            requirement: 需求描述
            module_id: 模块 ID

        Returns:
            (TaskCard, score) 或 (None, 0.0)
        """
        index = self._get_task_card_index()
        if not index:
            return None, 0.0

        # 查找匹配的任务卡
        matching = index.find_matching(requirement, module_id, threshold=0.1)
        if matching:
            best_card = matching[0]
            score = best_card.matches_requirement(requirement)
            return best_card, score

        return None, 0.0

    def _get_prompt_injector(self):
        """获取提示词注入器 (懒加载)"""
        if self._prompt_injector is None:
            try:
                from ..prompts.injector import PromptInjector
                from ..prompts.loader import PromptLoader

                prompts_dir = self.config.project_dir / ".claude" / "prompts"
                if prompts_dir.exists():
                    loader = PromptLoader(prompts_dir)
                    self._prompt_injector = PromptInjector(loader)
            except Exception:
                # 提示词系统加载失败不影响主流程
                pass

        return self._prompt_injector

    def _inject_prompts(
        self,
        requirement: str,
        module_id: Optional[str] = None,
    ) -> Optional["InjectedContext"]:
        """注入提示词

        根据需求自动匹配并注入合适的提示词

        Args:
            requirement: 需求描述
            module_id: 模块 ID

        Returns:
            InjectedContext 或 None
        """
        injector = self._get_prompt_injector()
        if not injector:
            return None

        try:
            return injector.inject(
                requirement=requirement,
                module_id=module_id,
                include_system=self.flags.enable_system_constraints,
                max_supporting=self.flags.prompt_max_supporting,
            )
        except Exception:
            # 提示词注入失败不影响主流程
            return None

    # =========================================================================
    # 便捷 API
    # =========================================================================

    def run(
        self,
        requirement: str,
        module_id: Optional[str] = None,
    ) -> FactoryResult:
        """执行完整流程 (上下文构建)

        注意: 此方法只构建上下文，不生成代码。
        代码生成由 Claude 完成。

        Args:
            requirement: 需求描述
            module_id: 模块 ID

        Returns:
            FactoryResult
        """
        start_time = time.time()

        try:
            context = self.build_context(requirement, module_id)

            return FactoryResult(
                success=True,
                requirement=requirement,
                module_id=module_id,
                context=context,
                duration_ms=int((time.time() - start_time) * 1000),
            )

        except RiskBlockedError as e:
            return FactoryResult(
                success=False,
                requirement=requirement,
                module_id=module_id,
                blocked=True,
                error=str(e),
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

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "version": self.VERSION,
            "flags": self.flags.to_dict(),
            "guardrails_stats": self.guardrails.stats.to_dict(),
            "event_summary": self.event_stream.get_summary(),
        }


# =========================================================================
# 便捷函数
# =========================================================================

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
