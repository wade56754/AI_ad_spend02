"""
code_adapter_skill.py - 代码适配 Skill

代码来源说明 (Code Sources):
================================================================================
本 Skill 的设计和实现借鉴了以下开源项目：

1. astx (MIT License)
   - GitHub: https://github.com/codemodsquad/astx
   - 借鉴内容:
     - 结构化搜索替换模式 (pattern → replacement)
     - 通配符匹配语法
     - AST 级别代码转换思路

2. refactor (MIT License)
   - GitHub: https://github.com/isidentical/refactor
   - 借鉴内容:
     - Python AST 重构框架设计
     - 契约式转换 (assert-based matching)
     - 规则化转换动作 (Rule + Replace)

3. ts-morph (MIT License)
   - GitHub: https://github.com/dsherret/ts-morph
   - 借鉴内容:
     - TypeScript AST 操作模式
     - 代码重构辅助方法设计
================================================================================

职责: 将参考代码适配为符合项目规范的代码
核心原则: 保留参考代码结构，只做必要修改，标注所有改动

基准对齐:
- CODE_FACTORY_REFERENCE_PROJECTS.md v1.0
- Agent Layer Freeze v1.0
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
import re

from .code_searcher_skill import SearchCandidate
from .code_selector_skill import AdaptationPlan

logger = logging.getLogger(__name__)


# ============================================================================
# 适配规则定义 (借鉴 astx 的 pattern → replacement 模式)
# ============================================================================

@dataclass
class AdaptationRule:
    """
    适配规则

    设计借鉴: astx 的结构化搜索替换
    """
    id: str
    pattern: str  # 正则表达式或字符串模式
    replacement: str
    context: str  # 说明
    layer: str  # "tech_stack" | "project_standard" | "sot_compliance"


# Pydantic v1 → v2 规则
PYDANTIC_V2_RULES = [
    AdaptationRule(
        id="PYDANTIC_CONFIG",
        pattern=r"class Config:",
        replacement="model_config = ConfigDict(",
        context="Pydantic v2 使用 model_config 替代 class Config",
        layer="tech_stack",
    ),
    AdaptationRule(
        id="PYDANTIC_VALIDATOR",
        pattern=r"@validator\(([^)]+)\)",
        replacement=r"@field_validator(\1)",
        context="Pydantic v2 使用 @field_validator 替代 @validator",
        layer="tech_stack",
    ),
    AdaptationRule(
        id="PYDANTIC_ROOT_VALIDATOR",
        pattern=r"@root_validator",
        replacement="@model_validator(mode='after')",
        context="Pydantic v2 使用 @model_validator 替代 @root_validator",
        layer="tech_stack",
    ),
    AdaptationRule(
        id="PYDANTIC_IMPORT_VALIDATOR",
        pattern=r"from pydantic import (.*)validator",
        replacement=r"from pydantic import \1field_validator",
        context="Pydantic v2 导入语句更新",
        layer="tech_stack",
    ),
]

# SQLAlchemy 1 → 2 规则
SQLALCHEMY_2_RULES = [
    AdaptationRule(
        id="SQLALCHEMY_QUERY",
        pattern=r"session\.query\((\w+)\)",
        replacement=r"session.execute(select(\1))",
        context="SQLAlchemy 2.x 推荐使用 select() 语法",
        layer="tech_stack",
    ),
    AdaptationRule(
        id="SQLALCHEMY_COLUMN",
        pattern=r"Column\(",
        replacement="mapped_column(",
        context="SQLAlchemy 2.x 使用 mapped_column",
        layer="tech_stack",
    ),
]

# 项目规范规则
PROJECT_STANDARD_RULES = [
    AdaptationRule(
        id="RESPONSE_DICT",
        pattern=r'return \{"([^"]+)":\s*([^}]+)\}',
        replacement=r'return StandardResponse(data=\2, message="\1")',
        context="使用项目标准响应格式",
        layer="project_standard",
    ),
]

# 所有规则
ALL_RULES = PYDANTIC_V2_RULES + SQLALCHEMY_2_RULES + PROJECT_STANDARD_RULES


# ============================================================================
# 数据类型定义
# ============================================================================

@dataclass
class Adaptation:
    """
    单个适配改动

    记录每个改动点的详细信息
    """
    line: int
    type: str  # "tech_stack" | "project_standard" | "sot_compliance" | "custom"
    original: str
    adapted: str
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "line": self.line,
            "type": self.type,
            "original": self.original,
            "adapted": self.adapted,
            "reason": self.reason,
        }


@dataclass
class SourceAttribution:
    """来源标注"""
    reference: str
    source: str
    adaptation_rate: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "reference": self.reference,
            "source": self.source,
            "adaptation_rate": self.adaptation_rate,
        }


@dataclass
class AdaptedFile:
    """适配后的文件"""
    file_path: str
    content: str
    adaptations: List[Adaptation] = field(default_factory=list)
    source_attribution: Optional[SourceAttribution] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "content": self.content,
            "adaptations": [a.to_dict() for a in self.adaptations],
            "source_attribution": self.source_attribution.to_dict() if self.source_attribution else None,
        }


# ============================================================================
# CodeAdapterSkill 主类
# ============================================================================

class CodeAdapterSkill:
    """
    代码适配 Skill

    架构设计借鉴:
    - astx: 结构化搜索替换模式
    - refactor: 规则化转换框架
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        初始化适配器

        Args:
            base_path: 项目根目录
        """
        self.base_path = base_path or self._detect_project_root()
        self.rules = ALL_RULES

        logger.info(f"CodeAdapterSkill initialized: {len(self.rules)} rules loaded")

    def adapt(
        self,
        reference: SearchCandidate,
        requirement: str,
        adaptation_plan: AdaptationPlan,
        custom_rules: Optional[Dict[str, str]] = None,
        preserve_comments: bool = True,
        add_type_hints: bool = True,
        target_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        适配参考代码

        Args:
            reference: 选中的参考代码
            requirement: 原始需求描述
            adaptation_plan: 适配方案
            custom_rules: 自定义适配规则
            preserve_comments: 保留原注释
            add_type_hints: 添加类型提示
            target_path: 目标文件路径

        Returns:
            适配结果
        """
        logger.info(
            f"Adaptation started: reference={reference.id}, "
            f"requirement='{requirement[:50]}...'"
        )

        try:
            # 1. 读取参考代码
            reference_code = self._read_reference_code(reference)

            if not reference_code:
                return {
                    "success": False,
                    "data": None,
                    "error": f"无法读取参考代码: {reference.path}",
                }

            # 2. 分层适配
            adapted_code = reference_code
            all_adaptations: List[Adaptation] = []

            # Layer 1: 技术栈适配 (借鉴 astx 的规则替换)
            adapted_code, adaptations = self._adapt_tech_stack(adapted_code)
            all_adaptations.extend(adaptations)

            # Layer 2: 项目规范适配
            adapted_code, adaptations = self._adapt_project_standards(adapted_code)
            all_adaptations.extend(adaptations)

            # Layer 3: 自定义规则
            if custom_rules:
                adapted_code, adaptations = self._apply_custom_rules(
                    adapted_code, custom_rules
                )
                all_adaptations.extend(adaptations)

            # Layer 4: 功能定制 (使用 LLM)
            adapted_code, adaptations = self._adapt_for_requirement(
                adapted_code, requirement, reference
            )
            all_adaptations.extend(adaptations)

            # 3. 添加来源标注
            adapted_code = self._add_source_attribution(
                adapted_code, reference, all_adaptations
            )

            # 4. 确定目标路径
            final_path = target_path or self._determine_target_path(
                reference, requirement
            )

            # 5. 计算适配率
            adaptation_rate = self._calculate_adaptation_rate(
                reference_code, adapted_code
            )

            # 6. 构建结果
            adapted_file = AdaptedFile(
                file_path=final_path,
                content=adapted_code,
                adaptations=all_adaptations,
                source_attribution=SourceAttribution(
                    reference=reference.path,
                    source=reference.source,
                    adaptation_rate=adaptation_rate,
                ),
            )

            # 统计
            summary = self._create_summary(all_adaptations)

            logger.info(
                f"Adaptation completed: {len(all_adaptations)} adaptations, "
                f"rate={adaptation_rate}"
            )

            return {
                "success": True,
                "data": {
                    "adapted_files": [adapted_file.to_dict()],
                    "summary": summary,
                },
                "error": None,
            }

        except Exception as e:
            logger.error(f"Adaptation failed: {e}", exc_info=True)
            return {
                "success": False,
                "data": None,
                "error": str(e),
            }

    # ========================================================================
    # Layer 1: 技术栈适配 (借鉴 astx 的规则替换模式)
    # ========================================================================

    def _adapt_tech_stack(self, code: str) -> Tuple[str, List[Adaptation]]:
        """
        技术栈适配

        借鉴: astx 的结构化搜索替换
        """
        adaptations = []

        for rule in self.rules:
            if rule.layer != "tech_stack":
                continue

            # 查找匹配
            matches = list(re.finditer(rule.pattern, code))

            for match in matches:
                original = match.group(0)
                adapted = re.sub(rule.pattern, rule.replacement, original)

                if original != adapted:
                    # 计算行号
                    line_num = code[:match.start()].count('\n') + 1

                    adaptations.append(Adaptation(
                        line=line_num,
                        type="tech_stack",
                        original=original,
                        adapted=adapted,
                        reason=f"{rule.id}: {rule.context}",
                    ))

            # 应用替换
            code = re.sub(rule.pattern, rule.replacement, code)

        return code, adaptations

    # ========================================================================
    # Layer 2: 项目规范适配
    # ========================================================================

    def _adapt_project_standards(self, code: str) -> Tuple[str, List[Adaptation]]:
        """项目规范适配"""
        adaptations = []

        # 检查是否需要添加项目标准导入
        standard_imports = [
            "from backend.core.response import StandardResponse",
            "from backend.core.error_codes import ErrorCode, AppException",
        ]

        # 如果代码中使用了这些类但没有导入，添加导入
        for import_line in standard_imports:
            class_name = import_line.split("import ")[-1].split(",")[0].strip()

            if class_name in code and import_line not in code:
                # 在文件开头添加导入
                code = import_line + "\n" + code
                adaptations.append(Adaptation(
                    line=1,
                    type="project_standard",
                    original="",
                    adapted=import_line,
                    reason="添加项目标准导入",
                ))

        # 应用项目规范规则
        for rule in self.rules:
            if rule.layer != "project_standard":
                continue

            matches = list(re.finditer(rule.pattern, code))

            for match in matches:
                original = match.group(0)
                adapted = re.sub(rule.pattern, rule.replacement, original)

                if original != adapted:
                    line_num = code[:match.start()].count('\n') + 1

                    adaptations.append(Adaptation(
                        line=line_num,
                        type="project_standard",
                        original=original,
                        adapted=adapted,
                        reason=rule.context,
                    ))

            code = re.sub(rule.pattern, rule.replacement, code)

        return code, adaptations

    # ========================================================================
    # Layer 3: 自定义规则
    # ========================================================================

    def _apply_custom_rules(
        self,
        code: str,
        custom_rules: Dict[str, str],
    ) -> Tuple[str, List[Adaptation]]:
        """应用自定义规则"""
        adaptations = []

        for pattern, replacement in custom_rules.items():
            if pattern in code:
                # 计算行号
                match = code.find(pattern)
                line_num = code[:match].count('\n') + 1

                adaptations.append(Adaptation(
                    line=line_num,
                    type="custom",
                    original=pattern,
                    adapted=replacement,
                    reason="自定义规则",
                ))

                code = code.replace(pattern, replacement)

        return code, adaptations

    # ========================================================================
    # Layer 4: 功能定制 (使用 LLM)
    # ========================================================================

    def _adapt_for_requirement(
        self,
        code: str,
        requirement: str,
        reference: SearchCandidate,
    ) -> Tuple[str, List[Adaptation]]:
        """
        使用 LLM 进行功能定制

        注意: 这里使用简化实现，生产环境应调用 LLM
        """
        adaptations = []

        # 如果有适配提示，添加到代码注释中
        if reference.adaptation_hint:
            hint_comment = f"# TODO: {reference.adaptation_hint}\n"

            if hint_comment not in code:
                # 找到第一个函数或类定义
                func_match = re.search(r'^(def |class )', code, re.MULTILINE)
                if func_match:
                    insert_pos = func_match.start()
                    code = code[:insert_pos] + hint_comment + code[insert_pos:]

                    adaptations.append(Adaptation(
                        line=code[:insert_pos].count('\n') + 1,
                        type="custom",
                        original="",
                        adapted=hint_comment.strip(),
                        reason="添加适配提示",
                    ))

        # 添加需求注释
        requirement_comment = f"# 需求: {requirement[:100]}...\n"

        if requirement_comment not in code and not code.startswith('"""'):
            code = requirement_comment + code
            adaptations.append(Adaptation(
                line=1,
                type="custom",
                original="",
                adapted=requirement_comment.strip(),
                reason="添加需求说明",
            ))

        return code, adaptations

    # ========================================================================
    # 来源标注
    # ========================================================================

    def _add_source_attribution(
        self,
        code: str,
        reference: SearchCandidate,
        adaptations: List[Adaptation],
    ) -> str:
        """
        添加来源标注

        借鉴: 代码溯源最佳实践
        """
        # 统计各类型适配数量
        type_counts = {}
        for a in adaptations:
            type_counts[a.type] = type_counts.get(a.type, 0) + 1

        changes_summary = ", ".join(
            f"{t} {c} 处" for t, c in type_counts.items()
        ) or "无修改"

        attribution = f'''"""
[ADAPTED FROM] {reference.source}: {reference.path}
[ADAPTATION]   基于参考代码适配，非从零生成
[CHANGES]      {changes_summary}

代码来源说明:
- 本文件基于开源参考代码适配生成
- 原始来源: {reference.source}
- 参考路径: {reference.path}
- 适配类型: 技术栈适配 + 项目规范适配 + 功能定制
"""

'''
        return attribution + code

    # ========================================================================
    # 辅助方法
    # ========================================================================

    def _read_reference_code(self, reference: SearchCandidate) -> str:
        """读取参考代码"""
        # 如果有代码片段直接返回
        if reference.snippet and len(reference.snippet) > 100:
            return reference.snippet

        # 尝试从本项目读取
        if reference.source == "local_project":
            file_path = self.base_path / reference.path
            if file_path.exists():
                try:
                    return file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception as e:
                    logger.warning(f"Failed to read {file_path}: {e}")

        # 返回片段或空
        return reference.snippet or ""

    def _determine_target_path(
        self,
        reference: SearchCandidate,
        requirement: str,
    ) -> str:
        """确定目标文件路径"""
        requirement_lower = requirement.lower()

        # 根据需求关键词推断路径
        if "export" in requirement_lower or "导出" in requirement_lower:
            return "backend/services/export_service.py"

        if "import" in requirement_lower or "导入" in requirement_lower:
            return "backend/services/import_service.py"

        if "router" in requirement_lower or "api" in requirement_lower:
            return "backend/routers/new_router.py"

        if "component" in requirement_lower or "组件" in requirement_lower:
            return "frontend/components/NewComponent.tsx"

        # 默认路径
        return "backend/services/new_service.py"

    def _calculate_adaptation_rate(self, original: str, adapted: str) -> str:
        """计算适配率 (保留了多少原代码)"""
        original_lines = set(original.strip().split('\n'))
        adapted_lines = set(adapted.strip().split('\n'))

        if not original_lines:
            return "0%"

        # 移除空行和注释行进行比较
        original_code_lines = {
            l.strip() for l in original_lines
            if l.strip() and not l.strip().startswith('#')
        }
        adapted_code_lines = {
            l.strip() for l in adapted_lines
            if l.strip() and not l.strip().startswith('#')
        }

        if not original_code_lines:
            return "100%"

        preserved = len(original_code_lines & adapted_code_lines)
        rate = preserved / len(original_code_lines) * 100

        return f"{rate:.0f}%"

    def _create_summary(self, adaptations: List[Adaptation]) -> Dict[str, Any]:
        """创建适配汇总"""
        by_type = {}
        for a in adaptations:
            by_type[a.type] = by_type.get(a.type, 0) + 1

        return {
            "total_adaptations": len(adaptations),
            "by_type": {
                "tech_stack": by_type.get("tech_stack", 0),
                "project_standard": by_type.get("project_standard", 0),
                "sot_compliance": by_type.get("sot_compliance", 0),
                "custom": by_type.get("custom", 0),
            },
        }

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

def code_adapter_skill(
    reference: Dict[str, Any],
    requirement: str,
    adaptation_plan: Dict[str, Any],
    custom_rules: Optional[Dict[str, str]] = None,
    target_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    代码适配 Skill 入口函数

    代码来源: 借鉴 astx + refactor 的规则化转换框架

    Args:
        reference: 选中的参考代码 (字典格式)
        requirement: 原始需求描述
        adaptation_plan: 适配方案
        custom_rules: 自定义适配规则
        target_path: 目标文件路径

    Returns:
        适配结果
    """
    # 转换为 SearchCandidate
    search_candidate = SearchCandidate(
        id=reference.get("id", "unknown"),
        source=reference.get("source", "unknown"),
        path=reference.get("path", ""),
        relevance_score=reference.get("relevance_score", 0),
        snippet=reference.get("snippet", ""),
        match_reason=reference.get("match_reason", ""),
        tech_stack_match=reference.get("tech_stack_match", 80),
        adaptation_hint=reference.get("adaptation_hint"),
    )

    # 转换为 AdaptationPlan
    plan = AdaptationPlan(
        base_code=adaptation_plan.get("base_code", ""),
        source=adaptation_plan.get("source", ""),
        estimated_adaptation_rate=adaptation_plan.get("estimated_adaptation_rate", "80%"),
        adaptation_hint=adaptation_plan.get("adaptation_hint"),
    )

    adapter = CodeAdapterSkill()
    return adapter.adapt(
        reference=search_candidate,
        requirement=requirement,
        adaptation_plan=plan,
        custom_rules=custom_rules,
        target_path=target_path,
    )


__all__ = [
    "CodeAdapterSkill",
    "Adaptation",
    "AdaptedFile",
    "code_adapter_skill",
]
