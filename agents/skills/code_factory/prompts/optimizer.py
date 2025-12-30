"""
提示词优化器 v5.0

整合 prompt-optimizer 的核心能力:
- 7 必需标签系统
- 8 维度质量评估

基准文档: MASTER.md v4.6
版本: v5.0
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import re


class RequiredTags(Enum):
    """7 必需标签 (来自 prompt-optimizer)"""
    ROLE = "role"
    GOAL = "goal"
    INPUT = "input"
    OUTPUT_FORMAT = "output_format"
    CONSTRAINTS = "constraints"
    ERROR_HANDLING = "error_handling"
    EXAMPLES = "examples"


class QualityDimension(Enum):
    """8 维度质量评估"""
    INTENT_CLARITY = "intent_clarity"           # 意图清晰度 15%
    STRUCTURE_COMPLETENESS = "structure"         # 结构完整性 15%
    SPECIFICITY = "specificity"                  # 具体性 15%
    OUTPUT_CONTROLLABILITY = "output_control"    # 输出可控性 15%
    EXAMPLE_EFFECTIVENESS = "examples"           # 示例有效性 10%
    CONSTRAINT_CLARITY = "constraints"           # 约束明确性 10%
    ERROR_HANDLING = "error_handling"            # 异常处理 10%
    TESTABILITY = "testability"                  # 可测试性 10%


# 各维度权重
DIMENSION_WEIGHTS = {
    QualityDimension.INTENT_CLARITY: 0.15,
    QualityDimension.STRUCTURE_COMPLETENESS: 0.15,
    QualityDimension.SPECIFICITY: 0.15,
    QualityDimension.OUTPUT_CONTROLLABILITY: 0.15,
    QualityDimension.EXAMPLE_EFFECTIVENESS: 0.10,
    QualityDimension.CONSTRAINT_CLARITY: 0.10,
    QualityDimension.ERROR_HANDLING: 0.10,
    QualityDimension.TESTABILITY: 0.10,
}


@dataclass
class TagValidationResult:
    """标签验证结果"""
    tag: RequiredTags
    present: bool
    closed: bool
    content_length: int = 0


@dataclass
class DimensionScore:
    """维度评分"""
    dimension: QualityDimension
    score: int  # 0-10
    weight: float
    weighted_score: float
    notes: str = ""


@dataclass
class QualityScore:
    """质量评分结果"""
    total_score: float  # 0-80
    rating: str  # 优秀/良好/及格/需改进
    rating_emoji: str  # 🟢/🟡/🟠/🔴
    dimension_scores: List[DimensionScore]
    tag_validation: List[TagValidationResult]
    p0_passed: bool  # P0 检查是否通过
    p0_failures: List[str]  # P0 失败项
    suggestions: List[str]  # 改进建议


class PromptOptimizer:
    """提示词优化器
    
    整合 prompt-optimizer 的核心能力:
    - validate_tags(): 验证 7 必需标签
    - evaluate_quality(): 8 维度质量评估
    - optimize(): 优化提示词结构
    """
    
    VERSION = "5.0"
    
    def __init__(self):
        self._tag_patterns = {
            tag: (re.compile(rf"<{tag.value}>", re.IGNORECASE),
                  re.compile(rf"</{tag.value}>", re.IGNORECASE))
            for tag in RequiredTags
        }
    
    def validate_tags(self, prompt: str) -> List[TagValidationResult]:
        """验证 7 必需标签
        
        Args:
            prompt: 提示词文本
            
        Returns:
            标签验证结果列表
        """
        results = []
        
        for tag in RequiredTags:
            open_pattern, close_pattern = self._tag_patterns[tag]
            
            open_match = open_pattern.search(prompt)
            close_match = close_pattern.search(prompt)
            
            present = open_match is not None
            closed = present and close_match is not None
            
            # 计算内容长度
            content_length = 0
            if present and closed:
                start = open_match.end()
                end = close_match.start()
                content_length = len(prompt[start:end].strip())
            
            results.append(TagValidationResult(
                tag=tag,
                present=present,
                closed=closed,
                content_length=content_length
            ))
        
        return results
    
    def get_missing_tags(self, prompt: str) -> List[str]:
        """获取缺失的标签
        
        Args:
            prompt: 提示词文本
            
        Returns:
            缺失的标签名称列表
        """
        results = self.validate_tags(prompt)
        missing = []
        
        for result in results:
            if not result.present or not result.closed:
                missing.append(result.tag.value)
        
        return missing
    
    def run_p0_checks(self, prompt: str) -> Tuple[bool, List[str]]:
        """运行 P0 检查
        
        P0 检查项:
        1-7: 7 个必需标签闭合
        8: ``` 数量为偶数
        9: 无空表格行
        
        Returns:
            (是否全部通过, 失败项列表)
        """
        failures = []
        
        # 1-7: 标签检查
        tag_results = self.validate_tags(prompt)
        for result in tag_results:
            if not result.present:
                failures.append(f"缺少 <{result.tag.value}> 标签")
            elif not result.closed:
                failures.append(f"<{result.tag.value}> 标签未闭合")
        
        # 8: 代码块配对
        backtick_count = prompt.count("```")
        if backtick_count % 2 != 0:
            failures.append(f"``` 数量为奇数 ({backtick_count})")
        
        # 9: 空表格行
        empty_row_pattern = re.compile(r'\|\s*\|\s*\|\s*\|')
        if empty_row_pattern.search(prompt):
            failures.append("存在空表格行")
        
        return len(failures) == 0, failures
    
    def evaluate_quality(self, prompt: str) -> QualityScore:
        """8 维度质量评估
        
        Args:
            prompt: 提示词文本
            
        Returns:
            质量评分结果
        """
        # 运行 P0 检查
        p0_passed, p0_failures = self.run_p0_checks(prompt)
        
        # 标签验证
        tag_validation = self.validate_tags(prompt)
        
        # 各维度评分
        dimension_scores = []
        
        # 1. 意图清晰度 (检查 goal 标签内容)
        intent_score = self._evaluate_intent_clarity(prompt, tag_validation)
        dimension_scores.append(intent_score)
        
        # 2. 结构完整性 (基于 P0 检查)
        structure_score = self._evaluate_structure(p0_passed, p0_failures)
        dimension_scores.append(structure_score)
        
        # 3. 具体性
        specificity_score = self._evaluate_specificity(prompt)
        dimension_scores.append(specificity_score)
        
        # 4. 输出可控性
        output_score = self._evaluate_output_controllability(prompt, tag_validation)
        dimension_scores.append(output_score)
        
        # 5. 示例有效性
        example_score = self._evaluate_examples(prompt, tag_validation)
        dimension_scores.append(example_score)
        
        # 6. 约束明确性
        constraint_score = self._evaluate_constraints(prompt, tag_validation)
        dimension_scores.append(constraint_score)
        
        # 7. 异常处理
        error_score = self._evaluate_error_handling(prompt, tag_validation)
        dimension_scores.append(error_score)
        
        # 8. 可测试性
        testability_score = self._evaluate_testability(prompt)
        dimension_scores.append(testability_score)
        
        # 计算总分
        total_score = sum(d.weighted_score for d in dimension_scores)
        
        # 确定评级
        if total_score >= 70:
            rating, emoji = "优秀", "🟢"
        elif total_score >= 60:
            rating, emoji = "良好", "🟡"
        elif total_score >= 50:
            rating, emoji = "及格", "🟠"
        else:
            rating, emoji = "需改进", "🔴"
        
        # 生成建议
        suggestions = self._generate_suggestions(dimension_scores, p0_failures)
        
        return QualityScore(
            total_score=total_score,
            rating=rating,
            rating_emoji=emoji,
            dimension_scores=dimension_scores,
            tag_validation=tag_validation,
            p0_passed=p0_passed,
            p0_failures=p0_failures,
            suggestions=suggestions,
        )
    
    def _evaluate_intent_clarity(
        self, 
        prompt: str, 
        tag_results: List[TagValidationResult]
    ) -> DimensionScore:
        """评估意图清晰度"""
        weight = DIMENSION_WEIGHTS[QualityDimension.INTENT_CLARITY]
        
        # 检查 goal 标签
        goal_result = next((r for r in tag_results if r.tag == RequiredTags.GOAL), None)
        
        if not goal_result or not goal_result.present:
            score = 2
            notes = "缺少 <goal> 标签"
        elif goal_result.content_length < 20:
            score = 4
            notes = "目标描述过短"
        elif goal_result.content_length < 50:
            score = 6
            notes = "目标描述基本清晰"
        elif goal_result.content_length < 100:
            score = 8
            notes = "目标描述清晰"
        else:
            score = 10
            notes = "目标描述完整清晰"
        
        return DimensionScore(
            dimension=QualityDimension.INTENT_CLARITY,
            score=score,
            weight=weight,
            weighted_score=score * weight * 10,
            notes=notes
        )
    
    def _evaluate_structure(
        self, 
        p0_passed: bool, 
        p0_failures: List[str]
    ) -> DimensionScore:
        """评估结构完整性"""
        weight = DIMENSION_WEIGHTS[QualityDimension.STRUCTURE_COMPLETENESS]
        
        if p0_passed:
            score = 10
            notes = "结构完整"
        elif len(p0_failures) == 1:
            score = 8
            notes = f"1 项未通过: {p0_failures[0]}"
        elif len(p0_failures) == 2:
            score = 6
            notes = f"2 项未通过"
        elif len(p0_failures) <= 4:
            score = 4
            notes = f"{len(p0_failures)} 项未通过"
        else:
            score = 2
            notes = "结构严重不完整"
        
        return DimensionScore(
            dimension=QualityDimension.STRUCTURE_COMPLETENESS,
            score=score,
            weight=weight,
            weighted_score=score * weight * 10,
            notes=notes
        )
    
    def _evaluate_specificity(self, prompt: str) -> DimensionScore:
        """评估具体性"""
        weight = DIMENSION_WEIGHTS[QualityDimension.SPECIFICITY]
        
        # 检查具体指标: 数字、具体名词
        has_numbers = bool(re.search(r'\d+', prompt))
        has_specific_words = any(word in prompt.lower() for word in [
            "必须", "至少", "最多", "恰好", "仅", "只能",
            "must", "at least", "at most", "exactly", "only"
        ])
        
        if has_numbers and has_specific_words:
            score = 10
            notes = "指令具体可执行"
        elif has_numbers or has_specific_words:
            score = 8
            notes = "大部分具体"
        else:
            score = 6
            notes = "部分模糊"
        
        return DimensionScore(
            dimension=QualityDimension.SPECIFICITY,
            score=score,
            weight=weight,
            weighted_score=score * weight * 10,
            notes=notes
        )
    
    def _evaluate_output_controllability(
        self, 
        prompt: str,
        tag_results: List[TagValidationResult]
    ) -> DimensionScore:
        """评估输出可控性"""
        weight = DIMENSION_WEIGHTS[QualityDimension.OUTPUT_CONTROLLABILITY]
        
        output_result = next(
            (r for r in tag_results if r.tag == RequiredTags.OUTPUT_FORMAT), 
            None
        )
        
        if not output_result or not output_result.present:
            score = 2
            notes = "缺少 <output_format> 标签"
        elif output_result.content_length < 50:
            score = 4
            notes = "输出格式定义过简"
        elif "```" in prompt and "|" in prompt:
            score = 10
            notes = "有完整模板和表格"
        elif "```" in prompt or "|" in prompt:
            score = 8
            notes = "有模板或表格"
        else:
            score = 6
            notes = "基本格式要求"
        
        return DimensionScore(
            dimension=QualityDimension.OUTPUT_CONTROLLABILITY,
            score=score,
            weight=weight,
            weighted_score=score * weight * 10,
            notes=notes
        )
    
    def _evaluate_examples(
        self,
        prompt: str,
        tag_results: List[TagValidationResult]
    ) -> DimensionScore:
        """评估示例有效性"""
        weight = DIMENSION_WEIGHTS[QualityDimension.EXAMPLE_EFFECTIVENESS]
        
        example_result = next(
            (r for r in tag_results if r.tag == RequiredTags.EXAMPLES),
            None
        )
        
        if not example_result or not example_result.present:
            score = 2
            notes = "无示例"
        elif example_result.content_length < 50:
            score = 4
            notes = "示例过短"
        elif example_result.content_length < 100:
            score = 6
            notes = "示例基本"
        elif "输入" in prompt and "输出" in prompt:
            score = 10
            notes = "完整输入输出示例"
        else:
            score = 8
            notes = "有示例"
        
        return DimensionScore(
            dimension=QualityDimension.EXAMPLE_EFFECTIVENESS,
            score=score,
            weight=weight,
            weighted_score=score * weight * 10,
            notes=notes
        )
    
    def _evaluate_constraints(
        self,
        prompt: str,
        tag_results: List[TagValidationResult]
    ) -> DimensionScore:
        """评估约束明确性"""
        weight = DIMENSION_WEIGHTS[QualityDimension.CONSTRAINT_CLARITY]
        
        constraint_result = next(
            (r for r in tag_results if r.tag == RequiredTags.CONSTRAINTS),
            None
        )
        
        if not constraint_result or not constraint_result.present:
            score = 2
            notes = "无约束"
        elif constraint_result.content_length < 30:
            score = 4
            notes = "约束过简"
        else:
            # 检查是否有多条约束
            constraint_count = prompt.count("- ") + prompt.count("1.")
            if constraint_count >= 3:
                score = 10
                notes = "约束完整"
            elif constraint_count >= 2:
                score = 8
                notes = "约束基本明确"
            else:
                score = 6
                notes = "约束较少"
        
        return DimensionScore(
            dimension=QualityDimension.CONSTRAINT_CLARITY,
            score=score,
            weight=weight,
            weighted_score=score * weight * 10,
            notes=notes
        )
    
    def _evaluate_error_handling(
        self,
        prompt: str,
        tag_results: List[TagValidationResult]
    ) -> DimensionScore:
        """评估异常处理"""
        weight = DIMENSION_WEIGHTS[QualityDimension.ERROR_HANDLING]
        
        error_result = next(
            (r for r in tag_results if r.tag == RequiredTags.ERROR_HANDLING),
            None
        )
        
        if not error_result or not error_result.present:
            score = 2
            notes = "未考虑异常"
        else:
            # 计算异常场景数量
            if_count = prompt.lower().count("如果") + prompt.lower().count("if ")
            if if_count >= 3:
                score = 10
                notes = f"≥3 种异常场景"
            elif if_count >= 2:
                score = 8
                notes = "2 种异常场景"
            elif if_count >= 1:
                score = 6
                notes = "1 种异常场景"
            else:
                score = 4
                notes = "提及但不具体"
        
        return DimensionScore(
            dimension=QualityDimension.ERROR_HANDLING,
            score=score,
            weight=weight,
            weighted_score=score * weight * 10,
            notes=notes
        )
    
    def _evaluate_testability(self, prompt: str) -> DimensionScore:
        """评估可测试性"""
        weight = DIMENSION_WEIGHTS[QualityDimension.TESTABILITY]
        
        # 检查是否有验证标准
        has_criteria = any(word in prompt.lower() for word in [
            "验证", "测试", "检查", "确保", "verify", "test", "check", "ensure"
        ])
        
        has_success_criteria = "通过" in prompt or "成功" in prompt or "pass" in prompt.lower()
        
        if has_criteria and has_success_criteria:
            score = 10
            notes = "有明确验证标准"
        elif has_criteria:
            score = 8
            notes = "有验证方式"
        else:
            score = 6
            notes = "可基本验证"
        
        return DimensionScore(
            dimension=QualityDimension.TESTABILITY,
            score=score,
            weight=weight,
            weighted_score=score * weight * 10,
            notes=notes
        )
    
    def _generate_suggestions(
        self, 
        scores: List[DimensionScore],
        p0_failures: List[str]
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # P0 问题优先
        for failure in p0_failures:
            suggestions.append(f"[P0] {failure}")
        
        # 低分维度建议
        for score in sorted(scores, key=lambda s: s.score):
            if score.score < 6:
                suggestions.append(f"[{score.dimension.value}] {score.notes}")
        
        return suggestions[:5]  # 最多 5 条建议
    
    def optimize(self, raw_prompt: str) -> str:
        """优化提示词
        
        将原始提示词转换为 7 标签结构
        
        Args:
            raw_prompt: 原始提示词
            
        Returns:
            优化后的提示词
        """
        # 如果已经有标签结构，返回原样
        if "<role>" in raw_prompt.lower() and "<goal>" in raw_prompt.lower():
            return raw_prompt
        
        # 构建基础模板
        template = f"""<role>
你是一位专业的 AI 编程助手。
- 核心能力：代码生成、代码审查、问题分析
- 知识背景：FastAPI, SQLAlchemy, Next.js, TypeScript
</role>

<goal>
{raw_prompt}
</goal>

<input>
- 需求描述：用户提供的需求
</input>

<output_format>
根据需求提供相应的代码或分析结果。
</output_format>

<constraints>
1. 遵循项目现有代码风格
2. 符合 SoT 规范
3. 保持代码简洁
</constraints>

<error_handling>
- 如果需求不明确：请求澄清
- 如果超出范围：说明限制
- 如果存在冲突：指出并询问
</error_handling>

<examples>
输入：添加用户登录功能
输出：提供完整的登录 API 和前端组件代码
</examples>"""
        
        return template


# ============================================================
# 便捷函数
# ============================================================

def validate_prompt(prompt: str) -> Dict:
    """验证提示词
    
    Returns:
        {
            "valid": bool,
            "missing_tags": List[str],
            "p0_passed": bool,
            "p0_failures": List[str]
        }
    """
    optimizer = PromptOptimizer()
    missing = optimizer.get_missing_tags(prompt)
    p0_passed, p0_failures = optimizer.run_p0_checks(prompt)
    
    return {
        "valid": len(missing) == 0 and p0_passed,
        "missing_tags": missing,
        "p0_passed": p0_passed,
        "p0_failures": p0_failures,
    }


def evaluate_prompt(prompt: str) -> Dict:
    """评估提示词质量
    
    Returns:
        质量评分字典
    """
    optimizer = PromptOptimizer()
    score = optimizer.evaluate_quality(prompt)
    
    return {
        "total_score": score.total_score,
        "rating": score.rating,
        "rating_emoji": score.rating_emoji,
        "p0_passed": score.p0_passed,
        "suggestions": score.suggestions,
        "dimensions": {
            d.dimension.value: {
                "score": d.score,
                "notes": d.notes
            }
            for d in score.dimension_scores
        }
    }

