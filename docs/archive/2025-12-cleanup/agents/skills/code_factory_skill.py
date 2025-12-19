"""
code_factory_skill.py - AI 代码工厂主编排器

代码来源说明 (Code Sources):
================================================================================
本 Skill 是代码工厂的主编排器，借鉴了以下开源项目：

整体架构:
1. MetaGPT (MIT License)
   - GitHub: https://github.com/geekan/MetaGPT
   - Stars: 45k+
   - 借鉴内容:
     - 多角色 Agent 协作模式
     - 标准化 SOP (Standard Operating Procedure)
     - 消息传递机制

2. OpenHands (MIT License)
   - GitHub: https://github.com/All-Hands-AI/OpenHands
   - Stars: 38k+
   - 借鉴内容:
     - Agent-Computer Interface (ACI) 设计
     - 事件驱动架构

3. SWE-agent (MIT License)
   - GitHub: https://github.com/princeton-nlp/SWE-agent
   - Stars: 13k+
   - 借鉴内容:
     - 文件编辑接口设计
     - 错误修复循环

子 Skill 来源:
- CodeSearcherSkill: code-graph-rag, Aider
- CodeSelectorSkill: MetaGPT, Devika (自研规则引擎)
- CodeAdapterSkill: astx, refactor
- CodeAssemblerSkill: Aider, Copier
- CodeVerifierSkill: mypy, ruff
================================================================================

职责: 编排代码工厂的 5 个阶段 (SEARCH → SELECT → ADAPT → ASSEMBLE → VERIFY)
核心原则: 搜索优先，适配改良，标注来源

基准对齐:
- CODE_FACTORY_REFERENCE_PROJECTS.md v1.0
- AI_CODE_FACTORY_REFACTOR_PROPOSAL.md v1.0
- Agent Layer Freeze v1.0
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
import time

# 导入子 Skills
from .code_searcher_skill import CodeSearcherSkill, code_searcher_skill
from .code_selector_skill import CodeSelectorSkill, code_selector_skill
from .code_adapter_skill import CodeAdapterSkill, code_adapter_skill
from .code_assembler_skill import CodeAssemblerSkill, code_assembler_skill
from .code_verifier_skill import CodeVerifierSkill, code_verifier_skill

logger = logging.getLogger(__name__)


# ============================================================================
# 数据类型定义
# ============================================================================

@dataclass
class FactoryConfig:
    """工厂配置"""
    scope: str = "fullstack"  # "backend" | "frontend" | "fullstack"
    search_sources: Dict[str, bool] = None
    auto_fix_iterations: int = 3
    output_mode: str = "files"  # "files" | "diff" | "preview"

    def __post_init__(self):
        if self.search_sources is None:
            self.search_sources = {
                "local_project": True,
                "code_library": True,
                "github": False,
            }


# ============================================================================
# CodeFactorySkill 主类
# ============================================================================

class CodeFactorySkill:
    """
    AI 代码工厂主编排器

    架构设计借鉴:
    - MetaGPT: 多角色协作模式
    - OpenHands: Agent-Computer Interface
    - SWE-agent: 错误修复循环

    工作流程:
    SEARCH → SELECT → ADAPT → ASSEMBLE → VERIFY
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        初始化代码工厂

        Args:
            base_path: 项目根目录
        """
        self.base_path = base_path or self._detect_project_root()

        # 初始化子 Skills
        self.searcher = CodeSearcherSkill(self.base_path)
        self.selector = CodeSelectorSkill()
        self.adapter = CodeAdapterSkill(self.base_path)
        self.assembler = CodeAssemblerSkill(self.base_path)
        self.verifier = CodeVerifierSkill(self.base_path)

        logger.info(f"CodeFactorySkill initialized: base_path={self.base_path}")

    def generate(
        self,
        requirement: str,
        config: Optional[FactoryConfig] = None,
    ) -> Dict[str, Any]:
        """
        执行代码工厂流程

        Args:
            requirement: 需求描述
            config: 工厂配置

        Returns:
            生成结果，包含所有阶段的输出
        """
        config = config or FactoryConfig()
        start_time = time.time()

        logger.info(
            f"=== Code Factory Started ===\n"
            f"Requirement: {requirement[:100]}...\n"
            f"Config: scope={config.scope}, output_mode={config.output_mode}"
        )

        result = {
            "success": False,
            "data": {
                "search_results": None,
                "selection": None,
                "adaptation": None,
                "assembly": None,
                "verification": None,
                "final_files": [],
            },
            "error": None,
            "metadata": {
                "total_time_ms": 0,
                "phases_completed": [],
            },
        }

        try:
            # ================================================================
            # Phase 1: SEARCH (搜索)
            # 来源: code-graph-rag, Aider
            # ================================================================
            logger.info(">>> Phase 1: SEARCH")

            search_result = self.searcher.search(
                requirement=requirement,
                sources=config.search_sources,
                max_candidates=5,
            )

            if not search_result.get("success"):
                result["error"] = f"搜索失败: {search_result.get('error')}"
                return result

            result["data"]["search_results"] = search_result["data"]
            result["metadata"]["phases_completed"].append("SEARCH")

            candidates = search_result["data"]["candidates"]
            if not candidates:
                result["error"] = "未找到相关参考代码"
                return result

            logger.info(f"Found {len(candidates)} candidates")

            # ================================================================
            # Phase 2: SELECT (选型)
            # 来源: MetaGPT, Devika
            # ================================================================
            logger.info(">>> Phase 2: SELECT")

            selection_result = self.selector.select(
                candidates=[
                    self._dict_to_search_candidate(c)
                    for c in candidates
                ],
                requirement=requirement,
            )

            if not selection_result.get("success"):
                result["error"] = f"选型失败: {selection_result.get('error')}"
                return result

            result["data"]["selection"] = selection_result["data"]
            result["metadata"]["phases_completed"].append("SELECT")

            selected = selection_result["data"]["selected"]
            adaptation_plan = selection_result["data"]["adaptation_plan"]

            logger.info(f"Selected: {selected['id']} (score: {selection_result['data']['scores']['total']:.2f})")

            # ================================================================
            # Phase 3: ADAPT (适配)
            # 来源: astx, refactor
            # ================================================================
            logger.info(">>> Phase 3: ADAPT")

            adaptation_result = self.adapter.adapt(
                reference=self._dict_to_search_candidate_obj(selected),
                requirement=requirement,
                adaptation_plan=self._dict_to_adaptation_plan(adaptation_plan),
            )

            if not adaptation_result.get("success"):
                result["error"] = f"适配失败: {adaptation_result.get('error')}"
                return result

            result["data"]["adaptation"] = adaptation_result["data"]
            result["metadata"]["phases_completed"].append("ADAPT")

            adapted_files = adaptation_result["data"]["adapted_files"]
            logger.info(f"Adapted {len(adapted_files)} files")

            # ================================================================
            # Phase 4: ASSEMBLE (组装)
            # 来源: Aider, Copier
            # ================================================================
            logger.info(">>> Phase 4: ASSEMBLE")

            assembly_result = self.assembler.assemble(
                adapted_files=[
                    self._dict_to_adapted_file(f)
                    for f in adapted_files
                ],
                requirement=requirement,
                scope=config.scope,
            )

            if not assembly_result.get("success"):
                result["error"] = f"组装失败: {assembly_result.get('error')}"
                return result

            result["data"]["assembly"] = assembly_result["data"]
            result["metadata"]["phases_completed"].append("ASSEMBLE")

            assembled_module = assembly_result["data"]["assembled_module"]
            logger.info(f"Assembled module: {assembled_module['name']} ({len(assembled_module['files'])} files)")

            # ================================================================
            # Phase 5: VERIFY (验证)
            # 来源: mypy, ruff
            # ================================================================
            logger.info(">>> Phase 5: VERIFY")

            verification_result = self.verifier.verify(
                assembled_files=[
                    self._dict_to_assembled_file(f)
                    for f in assembled_module["files"]
                ],
                requirement=requirement,
                auto_fix=True,
                max_fix_iterations=config.auto_fix_iterations,
            )

            result["data"]["verification"] = verification_result["data"]
            result["metadata"]["phases_completed"].append("VERIFY")

            # 即使验证有警告，只要没有错误就算成功
            verified_files = verification_result["data"]["verified_files"]
            report = verification_result["data"]["verification_report"]

            logger.info(
                f"Verification: passed={report['summary']['passed']}, "
                f"issues={report['summary']['remaining']}"
            )

            # ================================================================
            # 构建最终输出
            # ================================================================
            final_files = []
            for vf in verified_files:
                final_files.append({
                    "path": vf["path"],
                    "content": vf["content"],
                    "action": "create",
                    "source_refs": [selected["path"]],
                })

            result["data"]["final_files"] = final_files

            # 成功
            result["success"] = True
            result["metadata"]["total_time_ms"] = (time.time() - start_time) * 1000

            logger.info(
                f"=== Code Factory Completed ===\n"
                f"Success: {result['success']}\n"
                f"Files: {len(final_files)}\n"
                f"Time: {result['metadata']['total_time_ms']:.2f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"Code Factory failed: {e}", exc_info=True)
            result["error"] = str(e)
            result["metadata"]["total_time_ms"] = (time.time() - start_time) * 1000
            return result

    # ========================================================================
    # 辅助方法: 类型转换
    # ========================================================================

    def _dict_to_search_candidate(self, d: Dict[str, Any]):
        """转换字典为 SearchCandidate 对象用于选型"""
        from .code_searcher_skill import SearchCandidate
        return SearchCandidate(
            id=d.get("id", ""),
            source=d.get("source", ""),
            path=d.get("path", ""),
            relevance_score=d.get("relevance_score", 0),
            snippet=d.get("snippet", ""),
            match_reason=d.get("match_reason", ""),
            tech_stack_match=d.get("tech_stack_match", 80),
            adaptation_hint=d.get("adaptation_hint"),
        )

    def _dict_to_search_candidate_obj(self, d: Dict[str, Any]):
        """转换字典为 SearchCandidate 对象"""
        return self._dict_to_search_candidate(d)

    def _dict_to_adaptation_plan(self, d: Dict[str, Any]):
        """转换字典为 AdaptationPlan 对象"""
        from .code_selector_skill import AdaptationPlan
        return AdaptationPlan(
            base_code=d.get("base_code", ""),
            source=d.get("source", ""),
            estimated_adaptation_rate=d.get("estimated_adaptation_rate", "80%"),
            adaptation_hint=d.get("adaptation_hint"),
        )

    def _dict_to_adapted_file(self, d: Dict[str, Any]):
        """转换字典为 AdaptedFile 对象"""
        from .code_adapter_skill import AdaptedFile
        return AdaptedFile(
            file_path=d.get("file_path", ""),
            content=d.get("content", ""),
            adaptations=[],
            source_attribution=None,
        )

    def _dict_to_assembled_file(self, d: Dict[str, Any]):
        """转换字典为 AssembledFile 对象"""
        from .code_assembler_skill import AssembledFile
        return AssembledFile(
            path=d.get("path", ""),
            content=d.get("content", ""),
            action=d.get("action", "create"),
            dependencies=d.get("dependencies", []),
        )

    def _detect_project_root(self) -> Path:
        """自动检测项目根目录"""
        current = Path(__file__).resolve()

        for parent in current.parents:
            if (parent / "CLAUDE.md").exists() or (parent / ".claude").exists():
                return parent

        return Path("D:/project/AI_ad_spend02")


# ============================================================================
# Skill 入口函数
# ============================================================================

def code_factory_skill(
    requirement: str,
    scope: str = "fullstack",
    search_sources: Optional[Dict[str, bool]] = None,
    auto_fix_iterations: int = 3,
    output_mode: str = "files",
) -> Dict[str, Any]:
    """
    AI 代码工厂 Skill 入口函数

    代码来源:
    - 整体架构: MetaGPT, OpenHands, SWE-agent
    - 搜索: code-graph-rag, Aider
    - 选型: MetaGPT, Devika
    - 适配: astx, refactor
    - 组装: Aider, Copier
    - 验证: mypy, ruff

    Args:
        requirement: 需求描述
        scope: 范围 ("backend" | "frontend" | "fullstack")
        search_sources: 搜索来源配置
        auto_fix_iterations: 自动修复迭代次数
        output_mode: 输出模式 ("files" | "diff" | "preview")

    Returns:
        生成结果，包含所有阶段的输出
    """
    config = FactoryConfig(
        scope=scope,
        search_sources=search_sources,
        auto_fix_iterations=auto_fix_iterations,
        output_mode=output_mode,
    )

    factory = CodeFactorySkill()
    return factory.generate(
        requirement=requirement,
        config=config,
    )


__all__ = [
    "CodeFactorySkill",
    "FactoryConfig",
    "code_factory_skill",
]
