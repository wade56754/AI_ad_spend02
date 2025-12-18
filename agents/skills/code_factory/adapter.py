"""
代码适配器 - ADAPT 阶段实现

职责: 将参考代码适配为符合项目规范的代码

适配层次:
1. 技术栈适配 (Pydantic v2, SQLAlchemy 2.x)
2. 项目规范适配 (响应格式, 错误码, 命名)
3. SoT 合规适配 (字段, 状态, 角色)
4. 功能定制适配

来源:
- astx: 结构化搜索替换
- refactor: 规则化转换
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from .searcher import SearchCandidate
from .selector import AdaptationPlan


@dataclass
class AdaptationRecord:
    """适配记录"""
    line: int
    type: str
    original: str
    adapted: str
    reason: str


@dataclass
class SourceAttribution:
    """来源标注"""
    reference: str
    source: str
    adaptation_rate: str


@dataclass
class AdaptedFile:
    """适配后的文件"""
    file_path: str
    content: str
    adaptations: List[AdaptationRecord] = field(default_factory=list)
    source_attribution: SourceAttribution = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "content": self.content,
            "adaptations": [
                {
                    "line": a.line,
                    "type": a.type,
                    "original": a.original,
                    "adapted": a.adapted,
                    "reason": a.reason,
                }
                for a in self.adaptations
            ],
            "source_attribution": {
                "reference": self.source_attribution.reference,
                "source": self.source_attribution.source,
                "adaptation_rate": self.source_attribution.adaptation_rate,
            } if self.source_attribution else None,
        }


@dataclass
class AdaptationSummary:
    """适配摘要"""
    total_adaptations: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)


@dataclass
class AdaptResult:
    """适配结果"""
    success: bool
    adapted_files: List[AdaptedFile] = field(default_factory=list)
    summary: AdaptationSummary = None
    error: str = None


# ============================================================
# 适配规则定义
# ============================================================

class AdaptationRule:
    """适配规则基类"""
    rule_id: str
    layer: str  # tech_stack, project_standard, sot_compliance, custom
    pattern: str
    replacement: str
    reason: str

    def __init__(self, rule_id: str, layer: str, pattern: str, replacement: str, reason: str):
        self.rule_id = rule_id
        self.layer = layer
        self.pattern = pattern
        self.replacement = replacement
        self.reason = reason

    def apply(self, content: str) -> Tuple[str, List[AdaptationRecord]]:
        """应用规则"""
        records = []
        new_content = content

        # 按行处理
        lines = content.split("\n")
        new_lines = []

        for i, line in enumerate(lines, 1):
            if re.search(self.pattern, line):
                new_line = re.sub(self.pattern, self.replacement, line)
                if new_line != line:
                    records.append(AdaptationRecord(
                        line=i,
                        type=self.layer,
                        original=line.strip(),
                        adapted=new_line.strip(),
                        reason=self.reason,
                    ))
                    new_lines.append(new_line)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        return "\n".join(new_lines), records


# 预定义适配规则
ADAPTATION_RULES = [
    # === 技术栈适配 (Pydantic v1 → v2) ===
    AdaptationRule(
        "PYDANTIC_CONFIG",
        "tech_stack",
        r"class Config:",
        "model_config = ConfigDict(",
        "Pydantic v2: class Config → model_config",
    ),
    AdaptationRule(
        "PYDANTIC_VALIDATOR",
        "tech_stack",
        r"@validator\((['\"])(\w+)['\"]\)",
        r"@field_validator(\1\2\1)",
        "Pydantic v2: @validator → @field_validator",
    ),
    AdaptationRule(
        "PYDANTIC_ROOT_VALIDATOR",
        "tech_stack",
        r"@root_validator",
        "@model_validator(mode='after')",
        "Pydantic v2: @root_validator → @model_validator",
    ),
    AdaptationRule(
        "PYDANTIC_DICT",
        "tech_stack",
        r"\.dict\(\)",
        ".model_dump()",
        "Pydantic v2: .dict() → .model_dump()",
    ),

    # === 技术栈适配 (SQLAlchemy 1 → 2) ===
    AdaptationRule(
        "SQLALCHEMY_QUERY",
        "tech_stack",
        r"session\.query\((\w+)\)",
        r"session.execute(select(\1))",
        "SQLAlchemy 2: session.query() → session.execute(select())",
    ),
    AdaptationRule(
        "SQLALCHEMY_COLUMN",
        "tech_stack",
        r"Column\(",
        "mapped_column(",
        "SQLAlchemy 2: Column → mapped_column",
    ),

    # === 项目规范适配 ===
    AdaptationRule(
        "RESPONSE_DICT",
        "project_standard",
        r"return \{\"success\": True,",
        "return success_response(data=",
        "项目规范: 使用 success_response()",
    ),
    AdaptationRule(
        "HTTP_EXCEPTION",
        "project_standard",
        r"raise HTTPException\(status_code=(\d+), detail=\"([^\"]+)\"\)",
        r'raise BusinessError(code="\2")',
        "项目规范: 使用 BusinessError",
    ),

    # === SoT 合规适配 ===
    AdaptationRule(
        "OLD_STATUS_DRAFT",
        "sot_compliance",
        r"['\"]draft['\"]",
        '"raw_submitted"',
        "SoT 合规: draft → raw_submitted (8状态机)",
    ),
    AdaptationRule(
        "OLD_STATUS_PENDING",
        "sot_compliance",
        r"status\s*=\s*['\"]pending['\"]",
        'status="trend_pending"',
        "SoT 合规: pending → trend_pending (8状态机)",
    ),
    AdaptationRule(
        "OLD_STATUS_APPROVED",
        "sot_compliance",
        r"['\"]approved['\"]",
        '"final_confirmed"',
        "SoT 合规: approved → final_confirmed (8状态机)",
    ),
    AdaptationRule(
        "OLD_ROLE_SUPER_ADMIN",
        "sot_compliance",
        r"['\"]super_admin['\"]",
        '"admin"',
        "SoT 合规: super_admin → admin",
    ),
    AdaptationRule(
        "OLD_ROLE_ACCOUNTANT",
        "sot_compliance",
        r"['\"]accountant['\"]",
        '"finance"',
        "SoT 合规: accountant → finance",
    ),
    AdaptationRule(
        "OLD_ROLE_OPERATOR",
        "sot_compliance",
        r"['\"]operator['\"]",
        '"data_operator"',
        "SoT 合规: operator → data_operator",
    ),
]


class CodeAdapter:
    """
    代码适配器

    适配流程:
    1. 应用技术栈规则
    2. 应用项目规范规则
    3. 应用 SoT 合规规则
    4. 添加来源标注
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.rules = ADAPTATION_RULES.copy()

    def adapt(
        self,
        candidate: SearchCandidate,
        adaptation_plan: AdaptationPlan,
        requirement: str,
        target_path: str = None,
        custom_rules: Dict[str, str] = None,
    ) -> AdaptResult:
        """
        执行适配

        Args:
            candidate: 选中的参考代码
            adaptation_plan: 适配方案
            requirement: 原始需求
            target_path: 目标文件路径
            custom_rules: 自定义规则

        Returns:
            AdaptResult
        """
        content = candidate.full_content if candidate.full_content else candidate.snippet

        if not content:
            return AdaptResult(
                success=False,
                error="没有可适配的代码内容",
            )

        # 添加自定义规则
        if custom_rules:
            for pattern, replacement in custom_rules.items():
                self.rules.append(AdaptationRule(
                    f"CUSTOM_{len(self.rules)}",
                    "custom",
                    pattern,
                    replacement,
                    f"自定义规则: {pattern} → {replacement}",
                ))

        # 执行适配
        all_records = []
        adapted_content = content

        for rule in self.rules:
            adapted_content, records = rule.apply(adapted_content)
            all_records.extend(records)

        # 添加来源标注头部
        adapted_content = self._add_source_header(
            adapted_content,
            candidate,
            adaptation_plan,
            all_records,
        )

        # 确定目标路径
        if not target_path:
            target_path = self._infer_target_path(candidate, requirement)

        # 构建结果
        source_attribution = SourceAttribution(
            reference=candidate.path,
            source=candidate.source,
            adaptation_rate=adaptation_plan.estimated_adaptation_rate,
        )

        adapted_file = AdaptedFile(
            file_path=target_path,
            content=adapted_content,
            adaptations=all_records,
            source_attribution=source_attribution,
        )

        # 统计
        summary = AdaptationSummary(
            total_adaptations=len(all_records),
            by_type={
                "tech_stack": sum(1 for r in all_records if r.type == "tech_stack"),
                "project_standard": sum(1 for r in all_records if r.type == "project_standard"),
                "sot_compliance": sum(1 for r in all_records if r.type == "sot_compliance"),
                "custom": sum(1 for r in all_records if r.type == "custom"),
            },
        )

        return AdaptResult(
            success=True,
            adapted_files=[adapted_file],
            summary=summary,
        )

    def _add_source_header(
        self,
        content: str,
        candidate: SearchCandidate,
        plan: AdaptationPlan,
        records: List[AdaptationRecord],
    ) -> str:
        """添加来源标注头部"""
        # 统计适配类型
        type_counts = {}
        for r in records:
            type_counts[r.type] = type_counts.get(r.type, 0) + 1

        changes_str = ", ".join(
            f"{t} {c}处" for t, c in type_counts.items()
        ) if type_counts else "无需适配"

        header = f'''"""
[ADAPTED FROM] {candidate.source}: {candidate.path}
[ADAPTATION]   基于参考代码适配，非从零生成
[CHANGES]      {changes_str}
[RATE]         {plan.estimated_adaptation_rate}
"""

'''
        return header + content

    def _infer_target_path(self, candidate: SearchCandidate, requirement: str) -> str:
        """推断目标文件路径"""
        # 从需求中提取功能名
        feature_words = re.findall(r'[\u4e00-\u9fa5a-zA-Z_]+', requirement)
        feature_name = "_".join(feature_words[:2]).lower() if feature_words else "feature"

        # 根据语言确定目录
        if candidate.language == "python":
            # 从原路径推断类型
            if "service" in candidate.path.lower():
                return f"backend/services/{feature_name}_service.py"
            elif "router" in candidate.path.lower():
                return f"backend/routers/{feature_name}_router.py"
            elif "schema" in candidate.path.lower():
                return f"backend/schemas/{feature_name}_schema.py"
            else:
                return f"backend/services/{feature_name}.py"
        else:
            # TypeScript/JavaScript
            if "hook" in candidate.path.lower():
                return f"frontend/src/hooks/use{feature_name.title().replace('_', '')}.ts"
            elif "component" in candidate.path.lower():
                return f"frontend/src/components/{feature_name.title().replace('_', '')}/index.tsx"
            elif "api" in candidate.path.lower():
                return f"frontend/src/api/{feature_name}Api.ts"
            else:
                return f"frontend/src/modules/{feature_name}/index.tsx"

    def add_inline_annotations(self, content: str, records: List[AdaptationRecord]) -> str:
        """添加行内标注"""
        lines = content.split("\n")

        # 按行号排序记录
        line_records = {}
        for r in records:
            if r.line not in line_records:
                line_records[r.line] = []
            line_records[r.line].append(r)

        # 添加标注
        new_lines = []
        for i, line in enumerate(lines, 1):
            if i in line_records:
                for r in line_records[i]:
                    comment = f"# [ADAPTED] {r.reason} | 原: {r.original[:50]}..."
                    new_lines.append(comment)
            new_lines.append(line)

        return "\n".join(new_lines)
