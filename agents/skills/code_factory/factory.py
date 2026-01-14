"""
AI 代码工厂 v4.5 - 主编排器

整合 Anthropic autonomous-coding 模式与我们的 6 阶段流水线:

架构:
┌─────────────────────────────────────────────────────────────┐
│                    CodeFactory (主编排器)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Session 1: INITIALIZER                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 1. 解析需求 (PromptStructurer)                       │   │
│  │ 2. 搜索参考代码 (CodeSearcher)                       │   │
│  │ 3. 生成 task_list.json                               │   │
│  │ 4. 初始化项目结构 + Git                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Session 2+: FACTORY (循环)                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ SEARCH → SELECT → ADAPT → ASSEMBLE → VERIFY → CONFIRM │  │
│  │ (每个任务走完 6 阶段流水线，含幻觉抑制确认)            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

来源:
- Anthropic autonomous-coding (MIT License)
- MetaGPT 多角色协作模式
- Aider Repo Map 概念
- MASTER.md v4.6 AI 防幻觉原则

版本记录:
- v4.5 (2025-12-30): 统一版本号，增强搜索和验证功能
- v4.0 (2025-12-27): 对齐 MASTER.md v4.6，新增 Phase 6 CONFIRM
- v3.0 (2025-12-18): 集成 Anthropic autonomous-coding 架构
"""

import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime

from .task_list import TaskList, Task, TaskStatus, generate_api_tasks
from .security import SecurityValidator, SoTComplianceChecker, create_security_hook
from .session import SessionManager, SessionType, ProgressTracker

# v7.0: 使用 types 模块的数据类型，核心功能由 LightweightOrchestrator 处理
from .types import AdaptedFile, PhaseResult as TypedPhaseResult, PipelineResult
from .verifier import CodeVerifier, VerifyResult, VerifyDecision


@dataclass
class FactoryConfig:
    """工厂配置"""

    # 项目路径
    project_dir: Path

    # 搜索配置
    search_sources: Dict[str, bool] = field(
        default_factory=lambda: {
            "local_project": True,
            "code_library": True,
            "github": False,
        }
    )

    # 执行配置
    max_iterations: Optional[int] = None
    auto_continue: bool = True
    auto_fix_iterations: int = 3

    # 安全配置
    enable_security: bool = True
    enable_sot_check: bool = True

    # 输出配置
    output_mode: str = "files"  # files | diff | preview
    verbose: bool = True


@dataclass
class PhaseResult:
    """阶段结果"""

    phase: str
    success: bool
    data: Any = None
    error: str = None
    duration_ms: int = 0


@dataclass
class TaskResult:
    """任务结果"""

    task_id: str
    success: bool
    phases: List[PhaseResult] = field(default_factory=list)
    output_files: List[str] = field(default_factory=list)
    error: str = None


class CodeFactory:
    """
    AI 代码工厂主编排器

    职责:
    1. 会话管理 (初始化/工厂/验证)
    2. 任务调度 (优先级排序)
    3. 6 阶段流水线编排 (含 CONFIRM 幻觉抑制)
    4. 安全验证
    5. 进度追踪

    版本记录:
    - v4.5 (2025-12-30): 统一版本号，增强搜索和验证功能
    - v4.0 (2025-12-27): 对齐 MASTER.md v4.6，新增 Phase 6 CONFIRM
    - v3.0 (2025-12-18): 集成 Anthropic autonomous-coding 架构
    """

    VERSION = "4.5"

    def __init__(self, config: FactoryConfig):
        self.config = config
        self.project_dir = Path(config.project_dir)

        # 核心组件
        self.task_list = TaskList(self.project_dir)
        self.session = SessionManager(self.project_dir)
        self.progress = ProgressTracker(self.session)

        # 安全组件
        self.security = (
            SecurityValidator(self.project_dir) if config.enable_security else None
        )
        self.sot_checker = SoTComplianceChecker() if config.enable_sot_check else None

        # 子 Skill 组件 (5 阶段流水线)
        self.searcher = CodeSearcher(
            project_root=self.project_dir,
            code_library_path=self.project_dir / "code-library",
            enable_github=config.search_sources.get("github", False),
        )
        self.selector = CodeSelector(project_root=self.project_dir)
        self.adapter = CodeAdapter(project_root=self.project_dir)
        self.assembler = CodeAssembler(project_root=self.project_dir)
        self.verifier = CodeVerifier(
            project_root=self.project_dir,
            auto_fix=config.auto_fix_iterations > 0,
            strict_mode=False,
        )

        # 阶段间数据传递 (每个任务独立)
        self._phase_data: Dict[str, Any] = {}

        # 阶段处理器 (可扩展)
        # 6 阶段流水线: SEARCH → SELECT → ADAPT → ASSEMBLE → VERIFY → CONFIRM
        self.phase_handlers: Dict[str, Callable] = {
            "search": self._phase_search,
            "select": self._phase_select,
            "adapt": self._phase_adapt,
            "assemble": self._phase_assemble,
            "verify": self._phase_verify,
            "confirm": self._phase_confirm,  # v4.0 新增: 幻觉抑制最终确认
        }

    # ============================================================
    # 主入口
    # ============================================================

    def run(self, requirement: str = None) -> Dict[str, Any]:
        """
        运行代码工厂

        Args:
            requirement: 需求描述 (仅初始化会话需要)

        Returns:
            执行结果
        """
        try:
            # 确定会话类型
            session_type = self.session.get_session_type()

            if session_type == SessionType.INITIALIZER:
                if not requirement:
                    return {"success": False, "error": "初始化会话需要提供 requirement"}
                return self._run_initializer(requirement)
            else:
                return self._run_factory()

        except KeyboardInterrupt:
            self.session.pause_session()
            return {"success": False, "error": "用户中断", "can_resume": True}

        except Exception as e:
            self.session.fail_session(str(e))
            return {"success": False, "error": str(e)}

    # ============================================================
    # 初始化会话
    # ============================================================

    def _run_initializer(self, requirement: str) -> Dict[str, Any]:
        """运行初始化会话"""
        self.session.start_session(SessionType.INITIALIZER)
        self.session.print_session_header()

        print(f"需求: {requirement}\n")

        # Step 1: 解析需求
        print(">>> Step 1: 解析需求")
        structured = self._parse_requirement(requirement)
        print(f"    任务类型: {structured.get('task_type', 'unknown')}")
        print(f"    范围: {structured.get('scope', 'fullstack')}")

        # Step 2: 搜索参考代码
        print("\n>>> Step 2: 搜索参考代码")
        search_results = self._initial_search(requirement)
        print(f"    找到 {len(search_results)} 个候选参考")
        if search_results and self.config.verbose:
            for i, result in enumerate(search_results[:3]):  # 显示前 3 个
                print(
                    f"      [{i+1}] {result['path']} (相关度: {result['relevance_score']:.0f})"
                )
                print(f"          来源: {result['source']} | {result['match_reason']}")

        # Step 3: 生成任务列表
        print("\n>>> Step 3: 生成任务列表")
        tasks = self._generate_tasks(requirement, search_results)
        self.task_list.add_tasks(tasks)
        print(f"    生成 {len(tasks)} 个任务")

        # Step 4: 初始化项目结构
        print("\n>>> Step 4: 初始化项目结构")
        self._init_project_structure()

        # Step 5: Git 初始化
        print("\n>>> Step 5: Git 初始化")
        self._git_init()

        # 完成初始化
        self.session.complete_session()
        print("\n✅ 初始化完成")
        print(f"   任务列表: {self.task_list.task_file}")
        print(f"   下一步: 运行相同命令开始执行任务")

        return {
            "success": True,
            "session_type": "initializer",
            "tasks_generated": len(tasks),
        }

    def _parse_requirement(self, requirement: str) -> Dict[str, Any]:
        """解析需求"""
        # 简单的关键词匹配
        scope = "fullstack"
        if "后端" in requirement or "api" in requirement.lower():
            scope = "backend"
        elif "前端" in requirement or "ui" in requirement.lower():
            scope = "frontend"

        task_type = "feature"
        if "重构" in requirement or "refactor" in requirement.lower():
            task_type = "refactor"
        elif "修复" in requirement or "fix" in requirement.lower():
            task_type = "bugfix"

        return {
            "requirement": requirement,
            "scope": scope,
            "task_type": task_type,
        }

    def _initial_search(self, requirement: str) -> List[Dict[str, Any]]:
        """初始搜索参考代码

        使用 CodeSearcher 从多个来源搜索相关代码:
        1. 本项目代码 (最高优先级)
        2. 代码资料库 (code-library)
        3. GitHub (可选)

        Returns:
            List[Dict[str, Any]]: 搜索候选结果列表
        """
        # 使用已初始化的 searcher
        search_result = self.searcher.search(
            requirement=requirement,
            sources=self.config.search_sources,
            max_candidates=10,  # 初始搜索多获取一些候选
        )

        if not search_result.success:
            print(f"    ⚠️ 搜索失败: {search_result.error}")
            return []

        # 转换为字典列表以便兼容
        results = []
        for candidate in search_result.candidates:
            results.append(
                {
                    "id": candidate.id,
                    "source": candidate.source,
                    "path": candidate.path,
                    "relevance_score": candidate.relevance_score,
                    "snippet": candidate.snippet,
                    "match_reason": candidate.match_reason,
                    "tech_stack_match": candidate.tech_stack_match,
                    "adaptation_hint": candidate.adaptation_hint,
                    "language": candidate.language,
                }
            )

        return results

    def _generate_tasks(self, requirement: str, search_results: List) -> List[Task]:
        """生成任务列表"""
        # 使用 generate_api_tasks 作为基础
        # 实际使用时会由 AI 生成更详细的任务

        structured = self._parse_requirement(requirement)
        return generate_api_tasks(requirement, structured["scope"])

    def _init_project_structure(self) -> None:
        """初始化项目结构"""
        # 确保必要目录存在
        dirs = [
            self.project_dir / "generated",
            self.project_dir / "generated" / "backend",
            self.project_dir / "generated" / "frontend",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def _git_init(self) -> None:
        """Git 初始化"""
        git_dir = self.project_dir / ".git"
        if not git_dir.exists():
            subprocess.run(["git", "init"], cwd=self.project_dir, capture_output=True)
            subprocess.run(
                ["git", "add", "task_list.json"],
                cwd=self.project_dir,
                capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m", "chore: initialize code factory"],
                cwd=self.project_dir,
                capture_output=True,
            )

    # ============================================================
    # 工厂会话
    # ============================================================

    def _run_factory(self) -> Dict[str, Any]:
        """运行工厂会话"""
        # 恢复或开始新会话
        if self.session.has_existing_session():
            self.session.resume_session()
        else:
            self.session.start_session(SessionType.FACTORY, self.config.max_iterations)

        self.session.print_session_header()
        self.session.update_progress(tasks_total=len(self.task_list.tasks))

        results = []

        while self.session.should_continue():
            # 获取下一个任务
            task = self.task_list.get_next_task()
            if not task:
                if self.task_list.is_all_completed():
                    print("\n🎉 所有任务已完成!")
                    break
                else:
                    print("\n⚠️ 没有可执行的任务")
                    break

            # 执行任务
            result = self._execute_task(task)
            results.append(result)

            if result.success:
                # Git 提交
                self._git_commit(task, result)
            else:
                # 处理失败
                if task.retry_count < 3:
                    self.task_list.retry_task(task.id)
                    print(f"    ⚠️ 任务失败，将重试 ({task.retry_count + 1}/3)")
                else:
                    print(f"    ❌ 任务失败次数过多，跳过")

            # 显示进度
            self.progress.show_summary()

            # 自动继续
            if self.config.auto_continue and self.session.should_continue():
                self.session.wait_for_continue()

        # 完成会话
        self.session.complete_session()

        return {
            "success": True,
            "session_type": "factory",
            "tasks_executed": len(results),
            "tasks_succeeded": sum(1 for r in results if r.success),
            "progress": self.task_list.get_progress(),
        }

    def _execute_task(self, task: Task) -> TaskResult:
        """执行单个任务 (6 阶段流水线)"""
        self.progress.start_task(task.id, task.description)
        self.task_list.start_task(task.id)

        result = TaskResult(task_id=task.id, success=True)

        # 执行 6 阶段 (v4.0: 新增 CONFIRM)
        phases = ["search", "select", "adapt", "assemble", "verify", "confirm"]

        for phase in phases:
            # 跳过已完成的阶段
            if getattr(task, f"{phase}_completed", False):
                continue

            self.progress.start_phase(phase)

            phase_result = self._execute_phase(phase, task)
            result.phases.append(phase_result)

            if phase_result.success:
                self.task_list.update_phase(task.id, phase)
                self.progress.complete_phase(phase, "ok")
            else:
                self.progress.complete_phase(phase, "failed")
                result.success = False
                result.error = phase_result.error
                self.task_list.fail_task(task.id, phase_result.error)
                break

        if result.success:
            self.task_list.complete_task(task.id, result.output_files)
            self.progress.complete_task(task.id, result.output_files)

        return result

    def _execute_phase(self, phase: str, task: Task) -> PhaseResult:
        """执行单个阶段"""
        handler = self.phase_handlers.get(phase)
        if not handler:
            return PhaseResult(
                phase=phase,
                success=False,
                error=f"未知阶段: {phase}",
            )

        start_time = datetime.now()

        try:
            data = handler(task)
            duration = (datetime.now() - start_time).total_seconds() * 1000

            return PhaseResult(
                phase=phase,
                success=True,
                data=data,
                duration_ms=int(duration),
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            return PhaseResult(
                phase=phase,
                success=False,
                error=str(e),
                duration_ms=int(duration),
            )

    # ============================================================
    # 5 阶段处理器 (集成子 Skill)
    # ============================================================

    def _phase_search(self, task: Task) -> Dict[str, Any]:
        """SEARCH 阶段: 搜索参考代码"""
        # 调用 CodeSearcher
        result: SearchResult = self.searcher.search(
            requirement=task.description,
            sources=self.config.search_sources,
            max_candidates=5,
        )

        if not result.success:
            raise Exception(result.error or "搜索失败")

        # 保存阶段数据供后续阶段使用
        self._phase_data[task.id] = {
            "candidates": result.candidates,
            "search_stats": {
                "total_searched": result.stats.total_searched,
                "local_matches": result.stats.local_matches,
                "library_matches": result.stats.library_matches,
            },
        }

        if self.config.verbose:
            print(f"       找到 {len(result.candidates)} 个候选参考")

        return self._phase_data[task.id]

    def _phase_select(self, task: Task) -> Dict[str, Any]:
        """SELECT 阶段: 选择最佳参考"""
        # 获取上一阶段数据
        phase_data = self._phase_data.get(task.id, {})
        candidates = phase_data.get("candidates", [])

        if not candidates:
            # 没有候选时，使用模板生成
            if self.config.verbose:
                print("       无候选参考，将使用模板生成")
            self._phase_data[task.id]["selected"] = None
            self._phase_data[task.id]["adaptation_plan"] = None
            return {"selected": None, "scores": {}, "use_template": True}

        # 调用 CodeSelector
        result: SelectionResult = self.selector.select(
            candidates=candidates,
            requirement=task.description,
        )

        if not result.success:
            raise Exception(result.error or "选型失败")

        # 保存选型结果
        self._phase_data[task.id]["selected"] = result.selected
        self._phase_data[task.id]["scores"] = result.scores
        self._phase_data[task.id]["adaptation_plan"] = result.adaptation_plan

        if self.config.verbose and result.selected:
            print(f"       选中: {result.selected.path} (得分: {result.scores.total:.1f})")

        return {
            "selected": result.selected.to_dict() if result.selected else None,
            "scores": {
                "tech_stack_match": result.scores.tech_stack_match,
                "feature_coverage": result.scores.feature_coverage,
                "adaptation_cost": result.scores.adaptation_cost,
                "code_quality": result.scores.code_quality,
                "total": result.scores.total,
            }
            if result.scores
            else {},
            "alternatives": result.alternatives,
        }

    def _phase_adapt(self, task: Task) -> Dict[str, Any]:
        """ADAPT 阶段: 适配参考代码"""
        phase_data = self._phase_data.get(task.id, {})
        selected = phase_data.get("selected")
        adaptation_plan = phase_data.get("adaptation_plan")

        if not selected:
            # 没有选中参考，跳过适配
            if self.config.verbose:
                print("       无需适配，直接组装")
            self._phase_data[task.id]["adapted_files"] = []
            return {"adapted_files": [], "skipped": True}

        # 调用 CodeAdapter
        result: AdaptResult = self.adapter.adapt(
            candidate=selected,
            adaptation_plan=adaptation_plan,
            requirement=task.description,
        )

        if not result.success:
            raise Exception(result.error or "适配失败")

        # 保存适配结果
        self._phase_data[task.id]["adapted_files"] = result.adapted_files

        if self.config.verbose:
            print(f"       适配 {len(result.adapted_files)} 个文件")
            if result.summary:
                print(f"       改动: {result.summary.total_adaptations} 处")

        return {
            "adapted_files": [af.to_dict() for af in result.adapted_files],
            "summary": {
                "total_adaptations": result.summary.total_adaptations,
                "by_type": result.summary.by_type,
            }
            if result.summary
            else {},
        }

    def _phase_assemble(self, task: Task) -> Dict[str, Any]:
        """ASSEMBLE 阶段: 组装完整模块"""
        phase_data = self._phase_data.get(task.id, {})
        adapted_files = phase_data.get("adapted_files", [])

        # 确定组装范围
        scope = "backend"
        if "前端" in task.description or "frontend" in task.description.lower():
            scope = "frontend"
        elif "fullstack" in task.description.lower():
            scope = "fullstack"

        # 调用 CodeAssembler
        result: AssembleResult = self.assembler.assemble(
            adapted_files=adapted_files,
            requirement=task.description,
            scope=scope,
            include_tests=True,
        )

        if not result.success:
            raise Exception(result.error or "组装失败")

        # 保存组装结果
        self._phase_data[task.id]["assembled_module"] = result.module
        self._phase_data[task.id]["repo_map"] = result.repo_map
        self._phase_data[task.id]["integration_guide"] = result.integration_guide

        # 收集输出文件路径
        output_files = [f.path for f in result.module.files] if result.module else []

        if self.config.verbose:
            print(f"       组装 {len(output_files)} 个文件")
            if result.repo_map:
                print(
                    f"       新建: {len(result.repo_map.new_files)} | 修改: {len(result.repo_map.modified_files)}"
                )

        return {
            "module": {
                "name": result.module.name,
                "files": [
                    {"path": f.path, "action": f.action} for f in result.module.files
                ],
                "entry_points": result.module.entry_points,
            }
            if result.module
            else None,
            "repo_map": {
                "new_files": result.repo_map.new_files,
                "modified_files": result.repo_map.modified_files,
            }
            if result.repo_map
            else {},
            "integration_guide": {
                "steps": result.integration_guide.steps,
                "imports_to_add": result.integration_guide.imports_to_add,
            }
            if result.integration_guide
            else {},
            "output_files": output_files,
        }

    def _phase_verify(self, task: Task) -> Dict[str, Any]:
        """VERIFY 阶段: 验证代码质量 (使用 5 层验证器)"""
        phase_data = self._phase_data.get(task.id, {})
        assembled_module = phase_data.get("assembled_module")

        if not assembled_module or not assembled_module.files:
            if self.config.verbose:
                print("       无文件需要验证")
            return {"verified_files": [], "all_passed": True, "decision": "approved"}

        # 转换为 AdaptedFile 格式供验证器使用
        adapted_files = [
            AdaptedFile(
                file_path=f.path,
                content=f.content,
                adaptations=[],
                source_attribution=None,
            )
            for f in assembled_module.files
        ]

        # 调用 CodeVerifier (集成 5 层验证)
        result: VerifyResult = self.verifier.verify(
            adapted_files=adapted_files,
            requirement=task.description,
        )

        # 处理验证结果
        verified_files = []
        all_issues = []

        for fr in result.file_results:
            verified_files.append(
                {
                    "path": fr.file_path,
                    "passed": fr.decision
                    in (VerifyDecision.APPROVED, VerifyDecision.FIX_APPLIED),
                    "decision": fr.decision.value,
                    "issues": [
                        {
                            "code": i.code,
                            "line": i.line,
                            "message": i.message,
                            "severity": i.severity,
                        }
                        for i in fr.issues
                    ],
                    "fixed": fr.decision == VerifyDecision.FIX_APPLIED,
                }
            )
            all_issues.extend(fr.issues)

        # 如果有修复，使用修复后的内容
        if result.decision == VerifyDecision.FIX_APPLIED:
            fixed_files = self.verifier.get_fixed_files(result)
            # 更新 assembled_module 中的文件内容
            for fixed in fixed_files:
                for f in assembled_module.files:
                    if f.path == fixed.file_path:
                        f.content = fixed.content
                        break

        if self.config.verbose:
            decision_emoji = {
                VerifyDecision.APPROVED: "✓",
                VerifyDecision.FIX_APPLIED: "🔧",
                VerifyDecision.REJECTED: "✗",
                VerifyDecision.MANUAL_REVIEW: "⚠️",
            }
            emoji = decision_emoji.get(result.decision, "?")
            print(
                f"       {emoji} {result.decision.value} "
                f"(错误: {result.summary.get('total_errors', 0)}, "
                f"警告: {result.summary.get('total_warnings', 0)}, "
                f"修复: {result.summary.get('total_fixes', 0)})"
            )

        # 写入文件 (如果验证通过且不是预览模式)
        if result.success and self.config.output_mode == "files":
            self._write_files(assembled_module.files)

        # 保存验证结果供后续使用
        self._phase_data[task.id]["verify_result"] = result

        return {
            "verified_files": verified_files,
            "all_passed": result.success,
            "decision": result.decision.value,
            "summary": result.summary,
            "issues": [
                {"code": i.code, "line": i.line, "message": i.message}
                for i in all_issues
            ],
        }

    def _phase_confirm(self, task: Task) -> Dict[str, Any]:
        """CONFIRM 阶段: 幻觉抑制最终确认 (v4.0 新增)

        基于 MASTER.md v4.6 §7 AI 防幻觉原则:
        1. 遍历生成的每个状态值 → 追溯到 STATE_MACHINE.md
        2. 遍历生成的每个角色值 → 追溯到 6 角色白名单
        3. 遍历生成的每个字段 → 追溯到 DATA_SCHEMA.md
        4. 遍历调用的每个 API → 确认在项目中存在
        5. 生成来源追溯报告

        任何追溯失败 → BLOCKING

        Returns:
            Dict with confirmation results and traceability report
        """
        from .sot_loader import get_sot_loader, BUSINESS_ROLES

        phase_data = self._phase_data.get(task.id, {})
        assembled_module = phase_data.get("assembled_module")

        if not assembled_module or not assembled_module.files:
            if self.config.verbose:
                print("       无文件需要确认")
            return {
                "confirmed": True,
                "files_checked": 0,
                "traceability_report": [],
            }

        # 获取 SoT 加载器
        sot_loader = get_sot_loader(self.project_dir)

        traceability_report = []
        all_confirmed = True
        blocking_issues = []

        for f in assembled_module.files:
            file_report = {
                "path": f.path,
                "checks": [],
                "confirmed": True,
            }

            content = f.content

            # 检查 1: 角色值追溯
            # 匹配类似 role="xxx" 或 role: "xxx" 或 UserRole.xxx 的模式
            import re

            role_patterns = [
                r'role\s*[=:]\s*["\'](\w+)["\']',
                r"UserRole\.(\w+)",
                r"role\s*==\s*[\"'](\w+)[\"']",
            ]
            for pattern in role_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    role = match.lower()
                    # 检查业务角色
                    is_valid_business = role in BUSINESS_ROLES
                    # 检查技术角色
                    is_valid_tech = sot_loader.is_valid_role(role, "tech")

                    if is_valid_business or is_valid_tech:
                        file_report["checks"].append(
                            {
                                "type": "role",
                                "value": role,
                                "valid": True,
                                "source": "MASTER.md v4.6 §2.4"
                                if is_valid_business
                                else "backend/models/enums.py",
                            }
                        )
                    else:
                        file_report["checks"].append(
                            {
                                "type": "role",
                                "value": role,
                                "valid": False,
                                "source": None,
                                "error": f"角色 '{role}' 不在 6 角色白名单中",
                            }
                        )
                        file_report["confirmed"] = False
                        all_confirmed = False
                        blocking_issues.append(f"[{f.path}] 无效角色: {role}")

            # 检查 2: 状态值追溯
            status_patterns = [
                r'status\s*[=:]\s*["\'](\w+)["\']',
                r"DailyReportStatus\.(\w+)",
                r"TopupRequestStatus\.(\w+)",
            ]
            for pattern in status_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    status = match.lower()
                    if sot_loader.is_valid_status(status):
                        file_report["checks"].append(
                            {
                                "type": "status",
                                "value": status,
                                "valid": True,
                                "source": "STATE_MACHINE.md",
                            }
                        )
                    else:
                        file_report["checks"].append(
                            {
                                "type": "status",
                                "value": status,
                                "valid": False,
                                "source": None,
                                "error": f"状态 '{status}' 不在状态机白名单中",
                            }
                        )
                        file_report["confirmed"] = False
                        all_confirmed = False
                        blocking_issues.append(f"[{f.path}] 无效状态: {status}")

            # 检查 3: SoT 标注检查
            sot_annotations = re.findall(r"#\s*SoT:\s*(\S+)", content)
            for annotation in sot_annotations:
                file_report["checks"].append(
                    {
                        "type": "sot_annotation",
                        "value": annotation,
                        "valid": True,
                        "source": annotation,
                    }
                )

            traceability_report.append(file_report)

        # 输出确认结果
        if self.config.verbose:
            if all_confirmed:
                print(f"       ✓ 幻觉抑制确认通过 ({len(assembled_module.files)} 文件)")
            else:
                print(f"       ✗ 幻觉抑制确认失败 ({len(blocking_issues)} 个问题)")
                for issue in blocking_issues[:3]:
                    print(f"         - {issue}")
                if len(blocking_issues) > 3:
                    print(f"         ... 还有 {len(blocking_issues) - 3} 个问题")

        # 如果有 BLOCKING 问题，抛出异常
        if not all_confirmed and self.sot_checker:
            raise Exception(
                f"CONFIRM 阶段失败: {len(blocking_issues)} 个幻觉问题\n"
                + "\n".join(blocking_issues)
            )

        return {
            "confirmed": all_confirmed,
            "files_checked": len(assembled_module.files),
            "traceability_report": traceability_report,
            "blocking_issues": blocking_issues,
        }

    def _write_files(self, files: List) -> None:
        """写入文件到磁盘"""
        for f in files:
            file_path = self.project_dir / f.path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f.content, encoding="utf-8")
            if self.config.verbose:
                print(f"       写入: {f.path}")

    # ============================================================
    # Git 操作
    # ============================================================

    def _git_commit(self, task: Task, result: TaskResult) -> None:
        """Git 提交"""
        if not result.output_files:
            return

        try:
            # 添加文件
            for f in result.output_files:
                subprocess.run(
                    ["git", "add", f],
                    cwd=self.project_dir,
                    capture_output=True,
                )

            # 提交
            message = f"feat({task.category}): {task.description}\n\n🤖 Generated by AI Code Factory v{self.VERSION}"
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.project_dir,
                capture_output=True,
            )

        except Exception as e:
            print(f"    ⚠️ Git 提交失败: {e}")


# ============================================================
# 便捷函数
# ============================================================


def create_factory(project_dir: str, **kwargs) -> CodeFactory:
    """创建代码工厂实例"""
    config = FactoryConfig(
        project_dir=Path(project_dir),
        **kwargs,
    )
    return CodeFactory(config)


def run_factory(project_dir: str, requirement: str = None, **kwargs) -> Dict[str, Any]:
    """运行代码工厂"""
    factory = create_factory(project_dir, **kwargs)
    return factory.run(requirement)
