"""
提示词验证器 v5.0

整合 validate_prompt.py 的功能:
- 提示词格式验证
- 标签完整性检查
- 代码块配对检查

基准文档: MASTER.md v4.6
版本: v5.0
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import re

from .optimizer import RequiredTags, QualityScore, PromptOptimizer


@dataclass
class ValidationError:
    """验证错误"""
    code: str
    message: str
    severity: str  # "error" | "warning"
    line: Optional[int] = None


@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    suggestions: List[str]


class PromptValidator:
    """提示词验证器
    
    验证规则:
    1. 7 必需标签必须存在且闭合
    2. 代码块 ``` 必须成对
    3. 无空表格行
    4. 标签顺序建议
    """
    
    VERSION = "5.0"
    
    # 推荐的标签顺序
    RECOMMENDED_TAG_ORDER = [
        RequiredTags.ROLE,
        RequiredTags.GOAL,
        RequiredTags.INPUT,
        RequiredTags.OUTPUT_FORMAT,
        RequiredTags.CONSTRAINTS,
        RequiredTags.ERROR_HANDLING,
        RequiredTags.EXAMPLES,
    ]
    
    def __init__(self):
        self._optimizer = PromptOptimizer()
    
    def validate(self, prompt: str) -> ValidationResult:
        """验证提示词
        
        Args:
            prompt: 提示词文本
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        suggestions = []
        
        # 1. 检查必需标签
        tag_errors = self._check_required_tags(prompt)
        errors.extend(tag_errors)
        
        # 2. 检查代码块配对
        code_block_errors = self._check_code_blocks(prompt)
        errors.extend(code_block_errors)
        
        # 3. 检查空表格行
        table_errors = self._check_empty_table_rows(prompt)
        warnings.extend(table_errors)
        
        # 4. 检查标签顺序
        order_warnings = self._check_tag_order(prompt)
        warnings.extend(order_warnings)
        
        # 5. 检查内容质量
        quality_suggestions = self._check_content_quality(prompt)
        suggestions.extend(quality_suggestions)
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )
    
    def _check_required_tags(self, prompt: str) -> List[ValidationError]:
        """检查必需标签"""
        errors = []
        
        for tag in RequiredTags:
            open_tag = f"<{tag.value}>"
            close_tag = f"</{tag.value}>"
            
            has_open = open_tag.lower() in prompt.lower()
            has_close = close_tag.lower() in prompt.lower()
            
            if not has_open:
                errors.append(ValidationError(
                    code=f"TAG_MISSING_{tag.value.upper()}",
                    message=f"缺少必需标签 <{tag.value}>",
                    severity="error"
                ))
            elif not has_close:
                errors.append(ValidationError(
                    code=f"TAG_UNCLOSED_{tag.value.upper()}",
                    message=f"标签 <{tag.value}> 未闭合",
                    severity="error"
                ))
        
        return errors
    
    def _check_code_blocks(self, prompt: str) -> List[ValidationError]:
        """检查代码块配对"""
        errors = []
        
        backtick_count = prompt.count("```")
        if backtick_count % 2 != 0:
            errors.append(ValidationError(
                code="CODE_BLOCK_UNMATCHED",
                message=f"代码块 ``` 未配对 (共 {backtick_count} 个)",
                severity="error"
            ))
        
        return errors
    
    def _check_empty_table_rows(self, prompt: str) -> List[ValidationError]:
        """检查空表格行"""
        warnings = []
        
        # 匹配空表格行模式
        pattern = re.compile(r'\|\s*\|\s*\|')
        matches = pattern.finditer(prompt)
        
        for i, match in enumerate(matches):
            # 计算行号
            line_num = prompt[:match.start()].count('\n') + 1
            warnings.append(ValidationError(
                code="EMPTY_TABLE_ROW",
                message=f"第 {line_num} 行存在空表格行",
                severity="warning",
                line=line_num
            ))
        
        return warnings
    
    def _check_tag_order(self, prompt: str) -> List[ValidationError]:
        """检查标签顺序"""
        warnings = []
        
        # 获取标签出现位置
        positions = {}
        for tag in RequiredTags:
            match = re.search(rf"<{tag.value}>", prompt, re.IGNORECASE)
            if match:
                positions[tag] = match.start()
        
        # 检查顺序
        prev_pos = -1
        for tag in self.RECOMMENDED_TAG_ORDER:
            if tag in positions:
                if positions[tag] < prev_pos:
                    warnings.append(ValidationError(
                        code="TAG_ORDER",
                        message=f"建议将 <{tag.value}> 移到更前面",
                        severity="warning"
                    ))
                prev_pos = positions[tag]
        
        return warnings
    
    def _check_content_quality(self, prompt: str) -> List[str]:
        """检查内容质量，返回建议"""
        suggestions = []
        
        # 检查 goal 内容长度
        goal_match = re.search(
            r"<goal>(.*?)</goal>", 
            prompt, 
            re.IGNORECASE | re.DOTALL
        )
        if goal_match:
            goal_content = goal_match.group(1).strip()
            if len(goal_content) < 20:
                suggestions.append("建议在 <goal> 中添加更详细的任务描述")
        
        # 检查 examples 内容
        examples_match = re.search(
            r"<examples>(.*?)</examples>",
            prompt,
            re.IGNORECASE | re.DOTALL
        )
        if examples_match:
            examples_content = examples_match.group(1).strip()
            if len(examples_content) < 50:
                suggestions.append("建议在 <examples> 中添加完整的输入输出示例")
        
        # 检查 error_handling 内容
        error_match = re.search(
            r"<error_handling>(.*?)</error_handling>",
            prompt,
            re.IGNORECASE | re.DOTALL
        )
        if error_match:
            error_content = error_match.group(1).strip()
            if_count = error_content.lower().count("如果") + error_content.lower().count("if")
            if if_count < 3:
                suggestions.append("建议在 <error_handling> 中添加至少 3 种异常情况")
        
        return suggestions
    
    def quick_validate(self, prompt: str) -> Tuple[bool, List[str]]:
        """快速验证
        
        Returns:
            (是否有效, 错误消息列表)
        """
        result = self.validate(prompt)
        messages = [e.message for e in result.errors]
        return result.valid, messages
    
    def get_quality_score(self, prompt: str) -> QualityScore:
        """获取质量评分
        
        委托给 PromptOptimizer
        """
        return self._optimizer.evaluate_quality(prompt)


# ============================================================
# 便捷函数
# ============================================================

def quick_validate(prompt: str) -> Dict:
    """快速验证提示词
    
    Returns:
        {
            "valid": bool,
            "errors": List[str],
            "warnings": List[str]
        }
    """
    validator = PromptValidator()
    result = validator.validate(prompt)
    
    return {
        "valid": result.valid,
        "errors": [e.message for e in result.errors],
        "warnings": [e.message for e in result.warnings],
        "suggestions": result.suggestions,
    }

