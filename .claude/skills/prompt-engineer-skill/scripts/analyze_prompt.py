#!/usr/bin/env python3
"""
Prompt Analyzer - 分析提示词质量并给出改进建议

用法:
    python analyze_prompt.py <prompt_file.md>
    python analyze_prompt.py --text "你的提示词内容"
"""

import re
import sys
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Issue:
    category: str  # STRUCT, ROLE, EXAMPLE, AMBIG, SCOPE, CHAIN
    severity: str  # P0, P1, P2
    message: str
    suggestion: str

def analyze_structure(content: str) -> List[Issue]:
    """分析 XML 结构"""
    issues = []
    
    # 检查是否使用 XML 标签
    xml_tags = re.findall(r'<(\w+)>', content)
    if len(xml_tags) < 2:
        issues.append(Issue(
            category="STRUCT",
            severity="P1",
            message="缺少 XML 标签结构化",
            suggestion="使用 <task>, <context>, <rules>, <examples> 等标签组织提示词"
        ))
    
    # 检查标签闭合
    open_tags = re.findall(r'<(\w+)(?:\s[^>]*)?>(?!.*</\1>)', content, re.DOTALL)
    for tag in open_tags[:3]:  # 最多报告 3 个
        issues.append(Issue(
            category="STRUCT",
            severity="P0",
            message=f"标签 <{tag}> 未正确闭合",
            suggestion=f"添加 </{tag}> 闭合标签"
        ))
    
    # 检查嵌套深度
    max_depth = 0
    current_depth = 0
    for char in content:
        if char == '<':
            current_depth += 1
            max_depth = max(max_depth, current_depth)
        elif char == '>':
            current_depth = max(0, current_depth - 1)
    
    if max_depth > 5:
        issues.append(Issue(
            category="STRUCT",
            severity="P2",
            message=f"XML 嵌套过深（{max_depth} 层）",
            suggestion="保持嵌套在 3 层以内，过深的结构可以扁平化"
        ))
    
    return issues

def analyze_role(content: str) -> List[Issue]:
    """分析角色定义"""
    issues = []
    
    # 检查是否有角色定义
    has_system = bool(re.search(r'<system>|<s>|你是一位|You are a', content, re.IGNORECASE))
    
    if not has_system:
        issues.append(Issue(
            category="ROLE",
            severity="P1",
            message="缺少角色定义",
            suggestion="添加 <system> 标签定义专业角色，如：你是一位资深XX专家..."
        ))
    elif has_system:
        # 检查角色是否足够具体
        role_match = re.search(r'你是一[位个](.{2,50}?)[，。]', content)
        if role_match:
            role = role_match.group(1)
            if len(role) < 10:
                issues.append(Issue(
                    category="ROLE",
                    severity="P2",
                    message=f"角色定义过于简单：'{role}'",
                    suggestion="细化角色：添加专业领域、经验水平、工作风格"
                ))
    
    return issues

def analyze_examples(content: str) -> List[Issue]:
    """分析示例"""
    issues = []
    
    # 检查是否有示例
    example_patterns = [
        r'<example',
        r'示例[：:]',
        r'Example[：:]',
        r'输入[：:].*输出[：:]',
    ]
    
    example_count = 0
    for pattern in example_patterns:
        example_count += len(re.findall(pattern, content, re.IGNORECASE))
    
    if example_count == 0:
        issues.append(Issue(
            category="EXAMPLE",
            severity="P1",
            message="缺少示例（Few-shot examples）",
            suggestion="添加 3-5 个具体示例，包含输入和期望输出"
        ))
    elif example_count < 3:
        issues.append(Issue(
            category="EXAMPLE",
            severity="P2",
            message=f"示例数量不足（当前 {example_count} 个）",
            suggestion="建议提供至少 3 个多样化示例，包括边界情况"
        ))
    
    # 检查是否有负面示例
    has_bad_example = bool(re.search(r'type="bad"|错误示例|不好的|❌|Wrong|Bad example', content, re.IGNORECASE))
    if example_count > 0 and not has_bad_example:
        issues.append(Issue(
            category="EXAMPLE",
            severity="P2",
            message="缺少负面示例",
            suggestion="添加 type='bad' 的示例，说明什么是不期望的输出"
        ))
    
    return issues

def analyze_ambiguity(content: str) -> List[Issue]:
    """分析歧义"""
    issues = []
    
    # 检查模糊词汇
    vague_words = [
        (r'适当[的地]', '适当'),
        (r'合适[的地]', '合适'),
        (r'一些', '一些'),
        (r'可能', '可能'),
        (r'大概', '大概'),
        (r'差不多', '差不多'),
        (r'等等', '等等'),
    ]
    
    for pattern, word in vague_words:
        if re.search(pattern, content):
            issues.append(Issue(
                category="AMBIG",
                severity="P2",
                message=f"存在模糊词汇：'{word}'",
                suggestion=f"将 '{word}' 替换为具体的标准或数值"
            ))
            break  # 只报告一个，避免过多噪音
    
    # 检查是否有明确的判断标准
    has_criteria = bool(re.search(r'标准[：:]|条件[：:]|规则[：:]|criteria|rules', content, re.IGNORECASE))
    has_conditional = bool(re.search(r'如果|当.*时|若|if\s|when\s', content, re.IGNORECASE))
    
    if has_conditional and not has_criteria:
        issues.append(Issue(
            category="AMBIG",
            severity="P1",
            message="存在条件判断但缺少明确标准",
            suggestion="为条件判断添加具体的判断标准和阈值"
        ))
    
    return issues

def analyze_scope(content: str) -> List[Issue]:
    """分析范围定义"""
    issues = []
    
    # 检查是否有输入输出定义
    has_input = bool(re.search(r'<input|输入[：:]|Input[：:]', content, re.IGNORECASE))
    has_output = bool(re.search(r'<output|输出[：:]|Output[：:]|output_format', content, re.IGNORECASE))
    
    if not has_input:
        issues.append(Issue(
            category="SCOPE",
            severity="P2",
            message="缺少输入格式定义",
            suggestion="明确说明期望的输入格式、来源和验证规则"
        ))
    
    if not has_output:
        issues.append(Issue(
            category="SCOPE",
            severity="P1",
            message="缺少输出格式定义",
            suggestion="添加 <output_format> 标签明确期望的输出格式"
        ))
    
    # 检查是否有边界定义
    has_must = bool(re.search(r'必须|must|required|一定要', content, re.IGNORECASE))
    has_must_not = bool(re.search(r'禁止|不要|不能|不可|must not|never|don\'t', content, re.IGNORECASE))
    
    if not has_must and not has_must_not:
        issues.append(Issue(
            category="SCOPE",
            severity="P2",
            message="缺少边界约束",
            suggestion="添加 <must> 和 <must_not> 明确必须做和禁止做的事项"
        ))
    
    return issues

def analyze_complexity(content: str) -> List[Issue]:
    """分析复杂度"""
    issues = []
    
    # 估算任务步骤数
    step_indicators = len(re.findall(r'\d+[\.、)]|\bstep\b|步骤|第[一二三四五六七八九十]', content, re.IGNORECASE))
    
    # 估算 token 数（粗略）
    estimated_tokens = len(content) // 2  # 中文约 2 字符/token
    
    if step_indicators > 5 and '<chain' not in content.lower():
        issues.append(Issue(
            category="CHAIN",
            severity="P1",
            message=f"任务包含 {step_indicators}+ 个步骤，建议链式拆解",
            suggestion="将复杂任务拆分为多个链式提示词，每个步骤单独处理"
        ))
    
    if estimated_tokens > 3000:
        issues.append(Issue(
            category="CHAIN",
            severity="P2",
            message=f"提示词较长（约 {estimated_tokens} tokens）",
            suggestion="考虑将部分内容移至参考文档，按需加载"
        ))
    
    return issues

def calculate_score(issues: List[Issue]) -> int:
    """计算健康分数"""
    score = 100
    for issue in issues:
        if issue.severity == "P0":
            score -= 20
        elif issue.severity == "P1":
            score -= 10
        elif issue.severity == "P2":
            score -= 5
    return max(0, score)

def analyze_prompt(content: str) -> Tuple[List[Issue], int]:
    """完整分析提示词"""
    all_issues = []
    all_issues.extend(analyze_structure(content))
    all_issues.extend(analyze_role(content))
    all_issues.extend(analyze_examples(content))
    all_issues.extend(analyze_ambiguity(content))
    all_issues.extend(analyze_scope(content))
    all_issues.extend(analyze_complexity(content))
    
    score = calculate_score(all_issues)
    return all_issues, score

def format_report(issues: List[Issue], score: int) -> str:
    """格式化分析报告"""
    lines = []
    lines.append("=" * 60)
    lines.append("提示词质量分析报告")
    lines.append("=" * 60)
    lines.append(f"\n健康评分: {score}/100\n")
    
    # 按严重性分组
    p0 = [i for i in issues if i.severity == "P0"]
    p1 = [i for i in issues if i.severity == "P1"]
    p2 = [i for i in issues if i.severity == "P2"]
    
    lines.append(f"问题统计: P0={len(p0)}, P1={len(p1)}, P2={len(p2)}")
    lines.append("-" * 60)
    
    if p0:
        lines.append("\n🔴 P0 - 阻断性问题（必须修复）:")
        for i, issue in enumerate(p0, 1):
            lines.append(f"  {i}. [{issue.category}] {issue.message}")
            lines.append(f"     💡 {issue.suggestion}")
    
    if p1:
        lines.append("\n🟡 P1 - 重要问题（建议修复）:")
        for i, issue in enumerate(p1, 1):
            lines.append(f"  {i}. [{issue.category}] {issue.message}")
            lines.append(f"     💡 {issue.suggestion}")
    
    if p2:
        lines.append("\n🟢 P2 - 建议改进:")
        for i, issue in enumerate(p2, 1):
            lines.append(f"  {i}. [{issue.category}] {issue.message}")
            lines.append(f"     💡 {issue.suggestion}")
    
    if not issues:
        lines.append("\n✅ 未发现明显问题，提示词质量良好！")
    
    lines.append("\n" + "=" * 60)
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="分析提示词质量")
    parser.add_argument("file", nargs="?", help="提示词文件路径")
    parser.add_argument("--text", "-t", help="直接输入提示词文本")
    args = parser.parse_args()
    
    if args.text:
        content = args.text
    elif args.file:
        content = Path(args.file).read_text(encoding="utf-8")
    else:
        print("请提供提示词文件或使用 --text 参数")
        sys.exit(1)
    
    issues, score = analyze_prompt(content)
    report = format_report(issues, score)
    print(report)
    
    # 返回码：P0 问题返回 1
    sys.exit(1 if any(i.severity == "P0" for i in issues) else 0)

if __name__ == "__main__":
    main()
