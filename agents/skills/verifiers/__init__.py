"""
代码验证器模块

增强版验证器套件，用于避免 AI 幻觉和确保代码质量

验证层:
1. HallucinationDetector - 幻觉检测 (API/函数存在性)
2. ASTVerifier - AST 语法验证
3. SpecComplianceVerifier - SoT 合规验证
4. IntegrationVerifier - 集成验证 (导入路径、依赖)
5. TestVerifier - 测试验证 (自动生成+运行测试)

借鉴开源项目:
- HallOumi: 幻觉检测理念
- tree-sitter: AST 解析
- mypy/ruff: 静态分析
- Qodo Cover: 测试生成

使用示例:
```python
from agents.skills.verifiers import (
    EnhancedCodeVerifier,
    VerifyContext,
    VerifierConfig,
    quick_verify,
)
from pathlib import Path

# 方式 1: 完整配置
context = VerifyContext(
    project_root=Path("/path/to/project"),
    requirement="实现用户注册 API",
)
verifier = EnhancedCodeVerifier(context)
result = verifier.verify_file("path/to/file.py", content)

# 方式 2: 快速验证
result = quick_verify("file.py", content, "/path/to/project")
```
"""

from .base import (
    VerifyResult,
    VerifyIssue,
    VerifiedFile,
    IssueSeverity,
    IssueCategory,
    VerifyStatus,
    VerifyContext,
    BaseVerifier,
    create_issue,
    merge_results,
)

from .hallucination_detector import HallucinationDetector
from .ast_verifier import ASTVerifier
from .spec_compliance_verifier import SpecComplianceVerifier
from .integration_verifier import IntegrationVerifier
from .test_verifier import TestVerifier
from .enhanced_verifier import (
    EnhancedCodeVerifier,
    VerifierConfig,
    create_verifier_from_project,
    quick_verify,
)
from .source_tracing_verifier import (
    SourceTracingVerifier,
    HallucinationGuard,
    verify_source_tracing,
    verify_hallucination_guard,
)

__all__ = [
    # 基础类型
    "VerifyResult",
    "VerifyIssue",
    "VerifiedFile",
    "IssueSeverity",
    "IssueCategory",
    "VerifyStatus",
    "VerifyContext",
    "BaseVerifier",
    "create_issue",
    "merge_results",
    # 验证器
    "HallucinationDetector",
    "ASTVerifier",
    "SpecComplianceVerifier",
    "IntegrationVerifier",
    "TestVerifier",
    # 增强版主验证器
    "EnhancedCodeVerifier",
    "VerifierConfig",
    # 便捷函数
    "create_verifier_from_project",
    "quick_verify",
    # 来源追溯验证器 (v1.0)
    "SourceTracingVerifier",
    "HallucinationGuard",
    "verify_source_tracing",
    "verify_hallucination_guard",
]
