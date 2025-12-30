"""
验证模块 v4.5

功能:
- 来源追溯 (tracer.py)
- AST 代码分析 (ast_analyzer.py)
- SoT 合规验证
"""

from .tracer import SourceTracer, TraceResult, TraceItem
from .ast_analyzer import (
    PythonAstAnalyzer,
    TypeScriptAnalyzer,
    AstAnalysisResult,
    ExtractedValue,
    CodeLanguage,
    analyze_code,
    detect_language,
    validate_against_whitelist,
)

__all__ = [
    # 来源追溯
    "SourceTracer",
    "TraceResult",
    "TraceItem",
    # AST 分析
    "PythonAstAnalyzer",
    "TypeScriptAnalyzer",
    "AstAnalysisResult",
    "ExtractedValue",
    "CodeLanguage",
    "analyze_code",
    "detect_language",
    "validate_against_whitelist",
]
