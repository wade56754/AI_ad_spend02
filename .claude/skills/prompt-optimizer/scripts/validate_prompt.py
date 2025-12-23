#!/usr/bin/env python3
"""
Prompt Structure Validator
Validates prompt structure, XML tags, and completeness.
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class ValidationIssue:
    severity: str  # P0, P1, P2
    category: str
    message: str
    line: Optional[int] = None


class PromptValidator:
    """Validates prompt structure and content."""
    
    # Required sections for different complexity levels
    MINIMUM_SECTIONS = ['role', 'goal', 'output_format']
    STANDARD_SECTIONS = MINIMUM_SECTIONS + ['input_format', 'constraints', 'examples']
    COMPLETE_SECTIONS = STANDARD_SECTIONS + ['process', 'checklist']
    
    # Domain-specific required sections
    DOMAIN_SECTIONS = {
        'api-testing': [
            'test_categories', 'fixtures', 'naming_convention',
            'assertion_requirements'
        ],
        'code-review': [
            'review_dimensions', 'severity_levels'
        ],
    }
    
    def __init__(self, content: str):
        self.content = content
        self.lines = content.split('\n')
        self.issues: List[ValidationIssue] = []
    
    def validate(self) -> List[ValidationIssue]:
        """Run all validations."""
        self._check_xml_closure()
        self._check_section_separation()
        self._check_code_blocks()
        self._check_tables()
        self._check_examples()
        self._check_required_sections()
        self._check_claude_specific()  # Claude-specific optimizations
        return self.issues
    
    def _check_xml_closure(self):
        """Verify all XML tags are properly closed."""
        # Find all opening tags
        open_pattern = r'<([a-zA-Z][a-zA-Z0-9_-]*)(?:\s[^>]*)?>'
        close_pattern = r'</([a-zA-Z][a-zA-Z0-9_-]*)>'
        
        open_tags = []
        
        for i, line in enumerate(self.lines, 1):
            # Find opening tags
            for match in re.finditer(open_pattern, line):
                tag_name = match.group(1).lower()
                # Skip self-closing and special tags
                if not line[match.end()-2:match.end()] == '/>':
                    open_tags.append((tag_name, i))
            
            # Find closing tags
            for match in re.finditer(close_pattern, line):
                tag_name = match.group(1).lower()
                if open_tags and open_tags[-1][0] == tag_name:
                    open_tags.pop()
                elif open_tags:
                    self.issues.append(ValidationIssue(
                        severity='P0',
                        category='XML Structure',
                        message=f'Mismatched closing tag </{tag_name}>, expected </{open_tags[-1][0]}>',
                        line=i
                    ))
        
        # Check for unclosed tags
        for tag_name, line_num in open_tags:
            self.issues.append(ValidationIssue(
                severity='P0',
                category='XML Structure',
                message=f'Unclosed tag <{tag_name}>',
                line=line_num
            ))
    
    def _check_section_separation(self):
        """Verify input_format and output_format are separate."""
        in_input = False
        in_output = False
        
        for i, line in enumerate(self.lines, 1):
            if '<input_format>' in line.lower() or '<input>' in line.lower():
                in_input = True
            if '</input_format>' in line.lower() or '</input>' in line.lower():
                in_input = False
            if '<output_format>' in line.lower() or '<output>' in line.lower():
                in_output = True
                if in_input:
                    self.issues.append(ValidationIssue(
                        severity='P0',
                        category='Section Separation',
                        message='output_format is nested inside input_format - these should be separate sections',
                        line=i
                    ))
            if '</output_format>' in line.lower() or '</output>' in line.lower():
                in_output = False
    
    def _check_code_blocks(self):
        """Verify code blocks have language identifiers."""
        in_code_block = False
        code_start_line = 0
        
        for i, line in enumerate(self.lines, 1):
            if line.strip().startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    code_start_line = i
                    # Check for language identifier
                    lang = line.strip()[3:].strip()
                    if not lang:
                        self.issues.append(ValidationIssue(
                            severity='P2',
                            category='Code Block',
                            message='Code block missing language identifier',
                            line=i
                        ))
                else:
                    in_code_block = False
        
        if in_code_block:
            self.issues.append(ValidationIssue(
                severity='P0',
                category='Code Block',
                message='Unclosed code block',
                line=code_start_line
            ))
    
    def _check_tables(self):
        """Verify table format is correct."""
        in_table = False
        expected_cols = 0
        table_start = 0
        
        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if stripped.startswith('|') and stripped.endswith('|'):
                cols = stripped.count('|') - 1
                if not in_table:
                    in_table = True
                    expected_cols = cols
                    table_start = i
                else:
                    if cols != expected_cols:
                        self.issues.append(ValidationIssue(
                            severity='P1',
                            category='Table Format',
                            message=f'Inconsistent column count: expected {expected_cols}, got {cols}',
                            line=i
                        ))
                # Check for empty cells
                if '|  |' in stripped or '| |' in stripped:
                    self.issues.append(ValidationIssue(
                        severity='P2',
                        category='Table Format',
                        message='Table has empty cells',
                        line=i
                    ))
            else:
                in_table = False
    
    def _check_examples(self):
        """Verify examples are present and sufficient."""
        example_patterns = [
            r'<example',
            r'## Example',
            r'### Example',
            r'示例',
            r'Example \d+:',
        ]
        
        example_count = 0
        for pattern in example_patterns:
            example_count += len(re.findall(pattern, self.content, re.IGNORECASE))
        
        if example_count < 2:
            self.issues.append(ValidationIssue(
                severity='P1',
                category='Examples',
                message=f'Insufficient examples: found {example_count}, minimum 2 required',
            ))
    
    def _check_required_sections(self):
        """Check for required sections based on complexity."""
        content_lower = self.content.lower()
        
        # Check minimum sections
        for section in self.MINIMUM_SECTIONS:
            patterns = [f'<{section}>', f'<{section.replace("_", "-")}>']
            if not any(p in content_lower for p in patterns):
                self.issues.append(ValidationIssue(
                    severity='P1',
                    category='Required Section',
                    message=f'Missing required section: <{section}>',
                ))
    
    def _check_claude_specific(self):
        """Check Claude-specific optimization opportunities."""
        content_lower = self.content.lower()
        
        # Check for aggressive language (Claude 4.x doesn't need it)
        aggressive_patterns = [
            (r'\bMUST\b', 'Aggressive "MUST" - Claude 4.x responds well to normal tone'),
            (r'\bCRITICAL\b', 'Aggressive "CRITICAL" - consider softer language'),
            (r'\bNEVER\b', 'Negative instruction "NEVER" - prefer positive framing'),
            (r'\bALWAYS\b', 'Aggressive "ALWAYS" - Claude 4.x follows instructions precisely'),
        ]
        
        for pattern, message in aggressive_patterns:
            if re.search(pattern, self.content):
                self.issues.append(ValidationIssue(
                    severity='P2',
                    category='Claude Optimization',
                    message=message,
                ))
        
        # Check for "think" sensitivity (Opus 4.5)
        think_patterns = [
            r'\bthink about\b',
            r'\bthink through\b', 
            r'\bthink carefully\b',
        ]
        for pattern in think_patterns:
            if re.search(pattern, content_lower):
                self.issues.append(ValidationIssue(
                    severity='P2',
                    category='Claude Optimization',
                    message='Contains "think" - consider "consider/evaluate" for Opus 4.5',
                ))
                break
        
        # Check for negative instructions
        negative_patterns = [
            r"don't use",
            r"do not use", 
            r"never use",
            r"avoid using",
        ]
        for pattern in negative_patterns:
            if re.search(pattern, content_lower):
                self.issues.append(ValidationIssue(
                    severity='P2',
                    category='Claude Optimization',
                    message='Negative instruction found - prefer positive framing for Claude',
                ))
                break
        
        # Check for motivation/context
        motivation_indicators = ['because', 'this is important', 'the reason', 'this matters']
        has_motivation = any(ind in content_lower for ind in motivation_indicators)
        if not has_motivation and len(self.content) > 500:
            self.issues.append(ValidationIssue(
                severity='P2',
                category='Claude Optimization',
                message='Consider adding motivation/context (why) for better Claude performance',
            ))
    
    def get_score(self) -> Tuple[int, dict]:
        """Calculate quality score based on issues."""
        base_score = 80
        
        deductions = {
            'P0': 15,
            'P1': 8,
            'P2': 3,
        }
        
        dimension_scores = {
            'XML Structure': 10,
            'Section Separation': 10,
            'Code Block': 10,
            'Table Format': 10,
            'Examples': 10,
            'Required Section': 10,
            'Claude Optimization': 10,  # New dimension
            'Completeness': 10,
        }
        
        for issue in self.issues:
            deduction = deductions.get(issue.severity, 5)
            base_score -= deduction
            if issue.category in dimension_scores:
                dimension_scores[issue.category] = max(0, dimension_scores[issue.category] - deduction)
        
        return max(0, base_score), dimension_scores
    
    def generate_report(self) -> str:
        """Generate validation report."""
        score, dimensions = self.get_score()
        
        report = []
        report.append("# Prompt Validation Report\n")
        report.append(f"## Score: {score}/80\n")
        
        # Dimension breakdown
        report.append("## Dimension Scores\n")
        report.append("| Dimension | Score |")
        report.append("|-----------|-------|")
        for dim, s in dimensions.items():
            report.append(f"| {dim} | {s}/10 |")
        report.append("")
        
        # Issues by severity
        if self.issues:
            report.append("## Issues Found\n")
            
            for severity in ['P0', 'P1', 'P2']:
                severity_issues = [i for i in self.issues if i.severity == severity]
                if severity_issues:
                    emoji = {'P0': '🔴', 'P1': '🟠', 'P2': '🟡'}[severity]
                    report.append(f"### {emoji} {severity} Issues\n")
                    for issue in severity_issues:
                        line_info = f" (line {issue.line})" if issue.line else ""
                        report.append(f"- **[{issue.category}]** {issue.message}{line_info}")
                    report.append("")
        else:
            report.append("## ✅ No Issues Found\n")
        
        return '\n'.join(report)


def main():
    if len(sys.argv) < 2:
        print("Usage: validate_prompt.py <prompt_file>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    content = file_path.read_text(encoding='utf-8')
    
    validator = PromptValidator(content)
    validator.validate()
    
    print(validator.generate_report())
    
    score, _ = validator.get_score()
    sys.exit(0 if score >= 60 else 1)


if __name__ == '__main__':
    main()
