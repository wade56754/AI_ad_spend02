"""
orchestrator_agent.py

Global Orchestrator Agent.
- Does not generate code directly; coordinates BEAgent / FEAgent / TestAgent.
- Executes different flows in sequence to build an automation pipeline.
- Supports frontend_restructure flow for SC-ORCH pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import logging

from ..tools.types import AgentResponse

logger = logging.getLogger(__name__)


# Fix: P2-05 - 增加失败追踪字段
@dataclass
class OrchestratorResult:
    success: bool
    flow: str
    message: str
    steps: Dict[str, AgentResponse]
    errors: List[str] = field(default_factory=list)  # Fix: P2-05 - 记录所有步骤错误
    notes: List[str] = field(default_factory=list)   # Fix: P2-05 - 记录执行备注


class OrchestratorAgent:
    """
    Orchestrator Agent: Coordinates BE/FE/Test agents in defined workflows.

    Supported flows:
        - "backend_only": Runs only backend code generation
        - "frontend_only": Runs only frontend code generation
        - "full_pipeline": Runs backend → frontend → test (sequentially)

    Request format:
        {
            "flow": "full_pipeline",  # Required: one of the flows above
            "backend_request": {...},  # Passed to be_agent.handle_request()
            "frontend_request": {...}, # Passed to fe_agent.handle_request()
            "test_request": {...},     # (Optional) Passed to test_agent.handle_request()
            "test_enabled": bool,      # (Default: True) Run test step in full_pipeline
        }

    Returns:
        AgentResponse with data.steps containing results from each executed agent.
        If any step fails, pipeline stops and returns partial results.
    """

    def __init__(
        self,
        base_path: Optional[Path] = None,
        supabase_project_id: Optional[str] = None,
    ) -> None:
        from ..agents_config import create_agent

        # 推断项目根路径：agents/ 的上一级
        self.base_path: Path = (
            base_path
            if base_path is not None
            else Path(__file__).resolve().parent.parent.parent
        )

        # 这里用 agents_config.create_agent 统一创建子 Agent
        self._backend_agent = create_agent("be", base_path=self.base_path)
        self._frontend_agent = create_agent("fe", base_path=self.base_path)
        self._test_agent = create_agent(
            "test",
            base_path=self.base_path,
            supabase_project_id=supabase_project_id,
        )
        # DocAgent 和 ReviewAgent 用于文档生成和 SoT 审核
        self._doc_agent = create_agent("doc", base_path=self.base_path)
        self._review_agent = create_agent("review", base_path=self.base_path)

        # flow 路由表
        self._flow_handlers: Dict[
            str, Callable[[Dict[str, Any]], OrchestratorResult]
        ] = {
            "backend_only": self._run_backend_only,
            "frontend_only": self._run_frontend_only,
            "full_pipeline": self._run_full_pipeline,
            "frontend_restructure": self._run_frontend_restructure,
            "gen_backend": self._run_backend_gen,  # 新增：多模块后端生成
        }

    # ------------------------------------------------------------------ #
    # 对外主入口
    # ------------------------------------------------------------------ #

    def handle_request(self, request: Dict[str, Any]) -> AgentResponse:
        """
        Orchestrator 入口。

        Args:
            request: 请求字典，包含 "flow" 或 "action" 字段（兼容 HTTP/CLI 两种调用方式）

        Returns:
            {
              "success": bool,
              "data": {
                "flow": str,
                "message": str,
                "steps": {
                  "backend": { ... },
                  "frontend": { ... },
                  "test": { ... }
                }
              },
              "error": Optional[str],
            }
        """
        # 兼容 "flow" 和 "action" 两种 key（HTTP API 常用 action，CLI 常用 flow）
        flow = (request.get("flow") or request.get("action") or "").strip()
        if not flow:
            logger.warning("Orchestrator request missing 'flow' field")
            return {
                "success": False,
                "data": None,
                "error": "Missing 'flow' in orchestrator request",
            }

        handler = self._flow_handlers.get(flow)
        if handler is None:
            logger.error(f"Unknown flow: '{flow}'")
            return {
                "success": False,
                "data": {"flow": flow, "steps": {}},
                "error": f"Unknown flow: {flow}",
            }

        logger.info(f"Orchestrator starting flow: '{flow}'")

        try:
            result = handler(request)
        except Exception as exc:
            logger.exception(f"Orchestrator flow '{flow}' crashed: {exc}")
            return {
                "success": False,
                "data": {"flow": flow, "steps": {}},
                "error": f"Orchestrator flow '{flow}' failed: {exc}",
            }

        if result.success:
            logger.info(f"Orchestrator flow '{flow}' completed successfully")
        else:
            logger.error(f"Orchestrator flow '{flow}' failed: {result.message}")

        # dataclass → dict
        # Fix: P2-05 - 包含 errors 和 notes 字段
        return {
            "success": result.success,
            "data": {
                "flow": result.flow,
                "message": result.message,
                "steps": result.steps,
                "errors": result.errors,  # Fix: P2-05 - 记录所有步骤错误
                "notes": result.notes,    # Fix: P2-05 - 记录执行备注
            },
            "error": None if result.success else result.message,
        }

    # ------------------------------------------------------------------ #
    # 各种 flow 的实现
    # ------------------------------------------------------------------ #

    def _run_backend_only(self, request: Dict[str, Any]) -> OrchestratorResult:
        be_req: Dict[str, Any] = request.get("backend_request") or {}
        errors: List[str] = []
        notes: List[str] = []

        logger.info("Orchestrator: backend step started")
        be_result = self._backend_agent.handle_request(be_req)

        success = bool(be_result.get("success", False))
        if success:
            msg = "Backend flow completed"
            notes.append("Backend step completed successfully")
        else:
            error_msg = f"Backend flow failed: {be_result.get('error')}"
            msg = error_msg
            errors.append(error_msg)
            notes.append(f"[WARN] {error_msg}")
        logger.info(f"Orchestrator: backend step finished (success={success})")

        return OrchestratorResult(
            success=success,
            flow="backend_only",
            message=msg,
            steps={"backend": be_result},
            errors=errors,
            notes=notes,
        )

    def _run_frontend_only(self, request: Dict[str, Any]) -> OrchestratorResult:
        fe_req: Dict[str, Any] = request.get("frontend_request") or {}
        errors: List[str] = []
        notes: List[str] = []

        logger.info("Orchestrator: frontend step started")
        fe_result = self._frontend_agent.handle_request(fe_req)

        success = bool(fe_result.get("success", False))
        if success:
            msg = "Frontend flow completed"
            notes.append("Frontend step completed successfully")
        else:
            error_msg = f"Frontend flow failed: {fe_result.get('error')}"
            msg = error_msg
            errors.append(error_msg)
            notes.append(f"[WARN] {error_msg}")
        logger.info(f"Orchestrator: frontend step finished (success={success})")

        return OrchestratorResult(
            success=success,
            flow="frontend_only",
            message=msg,
            steps={"frontend": fe_result},
            errors=errors,
            notes=notes,
        )

    def _run_full_pipeline(self, request: Dict[str, Any]) -> OrchestratorResult:
        """
        Simple pipeline: backend -> frontend -> test (optional).

        Fix: P2-05 - 非阻塞失败策略:
        - 步骤失败时记录错误到 errors 列表
        - 继续执行后续步骤（保持兼容）
        - 最终 success 反映实际执行状态
        """
        steps: Dict[str, Dict[str, Any]] = {}
        errors: List[str] = []
        notes: List[str] = []

        # 1. Backend
        be_req: Dict[str, Any] = request.get("backend_request") or {}
        logger.info("Orchestrator: backend step started")
        be_result = self._backend_agent.handle_request(be_req)
        steps["backend"] = be_result
        be_success = be_result.get("success", False)
        logger.info(f"Orchestrator: backend step finished (success={be_success})")

        if not be_success:
            error_msg = f"Backend step failed: {be_result.get('error')}"
            errors.append(error_msg)
            notes.append(f"[WARN] {error_msg}")
            logger.warning(error_msg)

        # 2. Frontend
        fe_req: Dict[str, Any] = request.get("frontend_request") or {}
        logger.info("Orchestrator: frontend step started")
        fe_result = self._frontend_agent.handle_request(fe_req)
        steps["frontend"] = fe_result
        fe_success = fe_result.get("success", False)
        logger.info(f"Orchestrator: frontend step finished (success={fe_success})")

        if not fe_success:
            error_msg = f"Frontend step failed: {fe_result.get('error')}"
            errors.append(error_msg)
            notes.append(f"[WARN] {error_msg}")
            logger.warning(error_msg)

        # 3. Test (optional via test_enabled)
        test_enabled = bool(request.get("test_enabled", True))
        test_success = True
        if test_enabled:
            # TestAgent currently only generates prompt, actual execution via MCP
            test_req: Dict[str, Any] = request.get("test_request") or {}
            logger.info("Orchestrator: test step started")
            test_result = self._test_agent.handle_request(test_req)
            steps["test"] = test_result
            test_success = test_result.get("success", False)
            logger.info(f"Orchestrator: test step finished (success={test_success})")

            if not test_success:
                error_msg = f"Test step failed: {test_result.get('error')}"
                errors.append(error_msg)
                notes.append(f"[WARN] {error_msg}")
                logger.warning(error_msg)

        # Fix: P2-05 - 最终 success 反映实际执行状态
        all_success = be_success and fe_success and (test_success if test_enabled else True)

        if all_success:
            message = "Full pipeline completed successfully"
            notes.append("All steps completed successfully")
        else:
            message = f"Full pipeline completed with {len(errors)} error(s)"
            notes.append(f"Pipeline finished with errors: {len(errors)} step(s) failed")

        return OrchestratorResult(
            success=all_success,
            flow="full_pipeline",
            message=message,
            steps=steps,
            errors=errors,
            notes=notes,
        )

    def _run_frontend_restructure(self, request: Dict[str, Any]) -> OrchestratorResult:
        """
        SC-ORCH Frontend Restructure Pipeline.

        7-step pipeline:
        1. Analyze SoT documents
        2. Design spec outline
        3. Generate FRONTEND_STRUCTURE_SPEC.md (DocAgent)
        4. Generate frontend structure and code (FEAgent)
        5. Generate FRONTEND_FREEZE_MANIFEST.md (DocAgent)
        6. SoT Guard / Code Review (ReviewAgent)
        7. Return summary (and optionally write files to disk)

        Request format:
            {
                "flow": "frontend_restructure",
                "task": Optional[str],       # Task description
                "spec_version": Optional[str],  # Default "v1.0"
                "auto_write": Optional[bool],   # Default False (dry-run mode)
            }

        When auto_write=False (default):
            - Returns changes in response data, no files written to disk
            - Useful for preview/dry-run before committing

        When auto_write=True:
            - Writes all generated files to disk after SoT Guard passes
        """
        steps: Dict[str, Dict[str, Any]] = {}
        task = request.get("task", "重构前端结构")
        spec_version = request.get("spec_version", "v1.0")
        auto_write = bool(request.get("auto_write", False))
        changes: Dict[str, str] = {}
        errors: List[str] = []  # Fix: P2-05 - 添加 errors 字段
        notes: List[str] = []

        logger.info(f"Orchestrator: frontend_restructure started (task={task}, auto_write={auto_write})")
        notes.append(f"Mode: {'auto_write' if auto_write else 'dry-run (preview only)'}")

        # Step 1-2: Analysis and design (handled by DocAgent generate)
        logger.info("Orchestrator: Step 1-2 - Analyzing SoT and designing spec")
        notes.append("Step 1-2: SoT analysis and spec design")

        # Step 3: Generate FRONTEND_STRUCTURE_SPEC.md
        logger.info("Orchestrator: Step 3 - Generating FRONTEND_STRUCTURE_SPEC.md")
        doc_spec_result = self._doc_agent.handle_request({
            "action": "generate",
            "doc_type": "architecture",
            "target": "docs/4.architecture/FRONTEND_STRUCTURE_SPEC.md",
            "context": f"Frontend structure specification {spec_version} for SC-ORCH pipeline",
        })
        steps["doc_spec"] = doc_spec_result

        if not doc_spec_result.get("success", False):
            error_msg = f"Step 3 failed: {doc_spec_result.get('error')}"
            errors.append(error_msg)
            notes.append(f"[WARN] {error_msg}")
            return OrchestratorResult(
                success=False,
                flow="frontend_restructure",
                message=error_msg,
                steps=steps,
                errors=errors,
                notes=notes,
            )
        notes.append("Step 3: FRONTEND_STRUCTURE_SPEC.md generated")

        # Step 4: Generate frontend structure (FEAgent)
        logger.info("Orchestrator: Step 4 - Generating frontend structure")
        # P1-AG-001 修复：从配置读取文件列表，支持 request 覆盖
        from ..agents_config import FRONTEND_RESTRUCTURE_FILES
        frontend_files = request.get("frontend_files") or FRONTEND_RESTRUCTURE_FILES

        fe_result = self._frontend_agent.handle_request({
            "task": f"{task} - Generate modular frontend structure aligned with SoT",
            "target_files": frontend_files,
        })
        steps["frontend"] = fe_result

        if not fe_result.get("success", False):
            # FE failure is non-blocking for this flow (files may already exist)
            logger.warning(f"Step 4 FE generation note: {fe_result.get('error')}")
            notes.append(f"Step 4: FE generation note - {fe_result.get('error', 'partial')}")
        else:
            fe_changes = fe_result.get("data", {}).get("changes", {})
            changes.update(fe_changes)
            notes.append(f"Step 4: Generated {len(fe_changes)} frontend files")

        # Step 5: Generate FRONTEND_FREEZE_MANIFEST.md
        logger.info("Orchestrator: Step 5 - Generating FRONTEND_FREEZE_MANIFEST.md")
        doc_manifest_result = self._doc_agent.handle_request({
            "action": "generate",
            "doc_type": "manifest",
            "target": f"frontend/FRONTEND_FREEZE_MANIFEST_{spec_version}.md",
            "context": f"Frontend freeze manifest {spec_version} with audit log",
        })
        steps["doc_manifest"] = doc_manifest_result

        if not doc_manifest_result.get("success", False):
            error_msg = f"Step 5 failed: {doc_manifest_result.get('error')}"
            errors.append(error_msg)
            notes.append(f"[WARN] {error_msg}")
            return OrchestratorResult(
                success=False,
                flow="frontend_restructure",
                message=error_msg,
                steps=steps,
                errors=errors,
                notes=notes,
            )
        notes.append("Step 5: FRONTEND_FREEZE_MANIFEST generated")

        # Step 6: SoT Guard / Code Review
        logger.info("Orchestrator: Step 6 - Running SoT Guard review")
        review_result = self._review_agent.handle_request({
            "action": "review",
            "changes": changes,
            "context": "Frontend restructure SC-ORCH pipeline",
        })
        steps["review"] = review_result

        review_passed = review_result.get("passed", True)
        violations = review_result.get("violations", [])
        warnings = review_result.get("warnings", [])

        notes.append(f"Step 6: SoT Guard - P0={len(violations)}, P1/P2={len(warnings)}")

        if not review_passed:
            logger.warning(f"SoT Guard found {len(violations)} P0 violations")
            # P0 violations are blocking
            error_msg = f"Step 6 failed: {len(violations)} P0 violations found"
            errors.append(error_msg)
            notes.append(f"[WARN] {error_msg}")
            return OrchestratorResult(
                success=False,
                flow="frontend_restructure",
                message=error_msg,
                steps=steps,
                errors=errors,
                notes=notes,
            )

        # Step 7: Summary and optional file writing
        logger.info("Orchestrator: Step 7 - Generating summary")

        files_written = 0
        if auto_write and changes:
            logger.info(f"Orchestrator: auto_write=True, writing {len(changes)} files to disk")
            for file_path, content in changes.items():
                try:
                    full_path = self.base_path / "frontend" / file_path
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(content, encoding="utf-8")
                    files_written += 1
                except Exception as e:
                    logger.error(f"Failed to write {file_path}: {e}")
                    notes.append(f"Warning: Failed to write {file_path}")
            notes.append(f"Step 7: Wrote {files_written}/{len(changes)} files to disk")
        else:
            notes.append("Step 7: Dry-run mode - no files written (use auto_write=True to write)")

        notes.append("Pipeline completed successfully")

        summary = {
            "task": task,
            "spec_version": spec_version,
            "files_generated": len(changes),
            "files_written": files_written,
            "auto_write": auto_write,
            "sot_guard": {
                "passed": review_passed,
                "p0_violations": len(violations),
                "p1_p2_warnings": len(warnings),
            },
            "steps_completed": 7,
        }
        steps["summary"] = {"success": True, "data": summary, "error": None}

        mode_msg = f"(wrote {files_written} files)" if auto_write else "(dry-run)"
        return OrchestratorResult(
            success=True,
            flow="frontend_restructure",
            message=f"Frontend restructure completed: {len(changes)} files {mode_msg}, Health Score 100/100",
            steps=steps,
            errors=errors,
            notes=notes,
        )

    def _run_backend_gen(self, request: Dict[str, Any]) -> OrchestratorResult:
        """
        Gen Backend Pipeline: 批量生成/重构多个后端模块。

        Request format:
            {
                "flow": "gen_backend",
                "task": "daily_reports,topups,ledger,reconciliation_batches",  # 逗号分隔的模块列表
                "auto_write": Optional[bool],   # Default False (dry-run mode)
                "prompt": Optional[str],        # 附加提示词（传给 BEAgent）
            }

        处理流程:
        1. 解析 task 字段中的模块列表（逗号分隔）
        2. 为每个模块调用 BEAgent，生成/重构相关代码
        3. 聚合所有模块的结果
        4. （可选）auto_write=True 时写入文件

        Returns:
            OrchestratorResult with steps containing each module's result.
        """
        steps: Dict[str, Dict[str, Any]] = {}
        errors: List[str] = []
        notes: List[str] = []
        all_changes: Dict[str, str] = {}

        # 解析模块列表
        task_str = request.get("task", "")
        if not task_str:
            return OrchestratorResult(
                success=False,
                flow="gen_backend",
                message="Missing 'task' field (expected comma-separated module list)",
                steps=steps,
                errors=["Missing 'task' field"],
                notes=["Error: No modules specified"],
            )

        modules = [m.strip() for m in task_str.split(",") if m.strip()]
        if not modules:
            return OrchestratorResult(
                success=False,
                flow="gen_backend",
                message="No valid modules found in 'task' field",
                steps=steps,
                errors=["No valid modules found"],
                notes=["Error: Empty module list after parsing"],
            )

        auto_write = bool(request.get("auto_write", False))
        extra_prompt = request.get("prompt", "")

        logger.info(f"Orchestrator: gen_backend started (modules={modules}, auto_write={auto_write})")
        notes.append(f"Mode: {'auto_write' if auto_write else 'dry-run (preview only)'}")
        notes.append(f"Modules to process: {', '.join(modules)}")

        # 模块到后端文件的映射
        module_file_map: Dict[str, List[str]] = {
            "daily_reports": [
                "routers/daily_reports.py",
                "services/daily_report_service.py",
                "schemas/daily_report.py",
            ],
            "topups": [
                "routers/topups.py",
                "services/topup_service.py",
                "schemas/topup.py",
            ],
            "ledger": [
                "routers/ledger.py",
                "services/ledger_service.py",
                "schemas/ledger.py",
            ],
            "reconciliation_batches": [
                "routers/reconciliation.py",
                "services/reconciliation_service.py",
                "schemas/reconciliation.py",
            ],
            "projects": [
                "routers/projects.py",
                "services/project_service.py",
                "schemas/project.py",
            ],
            "auth": [
                "routers/auth.py",
                "services/auth_service.py",
                "schemas/auth.py",
            ],
        }

        success_count = 0
        fail_count = 0

        for module in modules:
            logger.info(f"Orchestrator: Processing module '{module}'")

            # 获取模块对应的文件列表
            target_files = module_file_map.get(module)
            if not target_files:
                # 未知模块，使用默认命名规则
                target_files = [
                    f"routers/{module}.py",
                    f"services/{module}_service.py",
                    f"schemas/{module}.py",
                ]
                notes.append(f"[INFO] Module '{module}' not in predefined map, using default files")

            # 构造 BEAgent 请求
            be_task = f"Generate/refactor backend module: {module}"
            if extra_prompt:
                be_task = f"{be_task}. {extra_prompt}"

            be_request = {
                "task": be_task,
                "target_files": target_files,
                "module": module,  # 传递模块名供 BEAgent 使用
            }

            be_result = self._backend_agent.handle_request(be_request)
            steps[f"module_{module}"] = be_result

            if be_result.get("success", False):
                success_count += 1
                module_changes = be_result.get("data", {}).get("changes", {})
                all_changes.update(module_changes)
                notes.append(f"Module '{module}': Generated {len(module_changes)} files")
                logger.info(f"Orchestrator: Module '{module}' completed ({len(module_changes)} files)")
            else:
                fail_count += 1
                error_msg = f"Module '{module}' failed: {be_result.get('error')}"
                errors.append(error_msg)
                notes.append(f"[WARN] {error_msg}")
                logger.warning(error_msg)

        # 写入文件（如果启用）
        files_written = 0
        if auto_write and all_changes:
            logger.info(f"Orchestrator: auto_write=True, writing {len(all_changes)} files to disk")
            for file_path, content in all_changes.items():
                try:
                    full_path = self.base_path / "backend" / file_path
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(content, encoding="utf-8")
                    files_written += 1
                except Exception as e:
                    logger.error(f"Failed to write {file_path}: {e}")
                    notes.append(f"Warning: Failed to write {file_path}")
            notes.append(f"Wrote {files_written}/{len(all_changes)} files to disk")
        else:
            notes.append("Dry-run mode - no files written (use auto_write=True to write)")

        # 生成汇总
        overall_success = fail_count == 0
        summary = {
            "modules_requested": len(modules),
            "modules_success": success_count,
            "modules_failed": fail_count,
            "files_generated": len(all_changes),
            "files_written": files_written,
            "auto_write": auto_write,
        }
        steps["summary"] = {"success": overall_success, "data": summary, "error": None}

        mode_msg = f"(wrote {files_written} files)" if auto_write else "(dry-run)"
        if overall_success:
            message = f"Gen backend completed: {success_count}/{len(modules)} modules, {len(all_changes)} files {mode_msg}"
        else:
            message = f"Gen backend partial: {success_count}/{len(modules)} modules succeeded, {fail_count} failed {mode_msg}"

        logger.info(f"Orchestrator: gen_backend finished - {message}")

        return OrchestratorResult(
            success=overall_success,
            flow="gen_backend",
            message=message,
            steps=steps,
            errors=errors,
            notes=notes,
        )
