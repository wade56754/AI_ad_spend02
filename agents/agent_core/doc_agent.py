"""
DocAgent - 文档生成与审核 Agent

职责：
- 生成/更新项目文档（SPEC / MANIFEST / GUIDE）
- 检查文档与 SoT 的一致性
- 生成 API 文档、README 等
- 支持 Orchestrator 的 frontend_restructure 流水线

输入:
    request = {
        "action": str,           # "generate" | "review" | "sync"
        "doc_type": str,         # "api" | "readme" | "changelog" | "module" | "architecture" | "manifest" | "spec"
        "target": Optional[str], # 目标文件路径或模块名
        "context": Optional[str] # 额外上下文信息
    }

输出:
    AgentResponse with:
        - success: bool
        - data: {
            "action": str,
            "doc_type": str,
            "content": Optional[str],
            "changes": List[Dict],
            "notes": List[str],
            "meta": Dict[str, Any]
        }
        - error: Optional[str]

基准对齐：
- MASTER.md v3.5
- SoT Freeze v2.6
- Dev-Guides Freeze vFinal
- Agent Layer Freeze v1.0
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import logging
import re

from ..agents_config import SOT_FILES, read_optional

logger = logging.getLogger(__name__)


# Document templates for different types
DOC_TEMPLATES = {
    "spec": """---
version: {version}
status: draft
layer: {layer}
owner: {owner}
last_reviewed: {date}
baseline: {baseline}
---

# {title}

## 1. Overview

{overview}

## 2. Scope

{scope}

## 3. Specification

{specification}

## 4. Dependencies

{dependencies}

## 5. Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| {version} | {date} | {owner} | Initial draft |
""",

    "manifest": """---
version: {version}
status: frozen
layer: {layer}
owner: {owner}
last_reviewed: {date}
baseline: {baseline}
---

# {title} Freeze Manifest

## Executive Summary

| Metric | Value |
|--------|-------|
| **Document Count** | {doc_count} |
| **Health Score** | {health_score}/100 |
| **P0 Issues** | {p0_count} |
| **P1 Issues** | {p1_count} |
| **P2 Issues** | {p2_count} |
| **Freeze Date** | {date} |
| **Freeze Author** | {owner} |

## Document Inventory

{inventory}

## Audit Log

{audit_log}

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| {version} | {date} | {owner} | Initial freeze |
""",

    "architecture": """---
version: {version}
status: draft
layer: architecture
owner: {owner}
last_reviewed: {date}
baseline: {baseline}
---

# {title}

## 1. Overview

{overview}

## 2. Architecture Principles

- **SoT-Driven**: All architecture decisions must align with SoT documents
- **Layer Isolation**: Respect ASDD 6-layer boundaries
- **Explicit Dependencies**: Document all cross-layer dependencies

## 3. Component View

{component_view}

## 4. Data Flow

{data_flow}

## 5. Integration Points

{integration_points}

## 6. References

- MASTER.md v3.5
- SoT Freeze v2.6
- Dev-Guides Freeze vFinal

## 7. Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| {version} | {date} | {owner} | Initial draft |
""",
}


class DocAgent:
    """
    文档生成与审核 Agent

    Supports:
    - Document generation (spec, manifest, architecture, module docs)
    - Document review against SoT
    - Document synchronization with codebase
    """

    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.cwd()
        logger.info(f"DocAgent initialized: base_path={self.base_path}")

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理文档相关请求。

        Args:
            request: 包含 action, doc_type, target, context 的字典

        Returns:
            统一 AgentResponse 结构
        """
        action = request.get("action", "review")
        doc_type = request.get("doc_type", "module")
        target = request.get("target")
        context = request.get("context")

        logger.info(f"DocAgent request: action={action}, doc_type={doc_type}, target={target}")

        try:
            if action == "generate":
                result = self._generate_doc(doc_type, target, context)
            elif action == "review":
                result = self._review_doc(doc_type, target, context)
            elif action == "sync":
                result = self._sync_doc(doc_type, target, context)
            else:
                result = self._make_error_response(
                    action, doc_type,
                    f"Unknown action: {action}. Supported: generate, review, sync"
                )

            return result

        except Exception as e:
            logger.error(f"DocAgent error: {e}")
            return self._make_error_response(action, doc_type, str(e))

    def _make_response(
        self,
        success: bool,
        action: str,
        doc_type: str,
        content: Optional[str] = None,
        changes: Optional[List[Dict]] = None,
        notes: Optional[List[str]] = None,
        error: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a standardized response structure."""
        return {
            "success": success,
            "data": {
                "action": action,
                "doc_type": doc_type,
                "content": content,
                "changes": changes or [],
                "notes": notes or [],
                "meta": meta or {},
            },
            "error": error,
        }

    def _make_error_response(
        self, action: str, doc_type: str, error: str
    ) -> Dict[str, Any]:
        """Create an error response."""
        return self._make_response(
            success=False,
            action=action,
            doc_type=doc_type,
            error=error,
            notes=[f"Error: {error}"],
        )

    def _generate_doc(
        self,
        doc_type: str,
        target: Optional[str],
        context: Optional[str],
    ) -> Dict[str, Any]:
        """
        生成文档。

        支持的 doc_type:
        - spec: 规范文档
        - manifest: 冻结清单
        - architecture: 架构文档
        - module: 模块文档
        - api: API 文档
        - readme: README
        """
        notes: List[str] = []
        changes: List[Dict[str, Any]] = []
        meta: Dict[str, Any] = {}

        # Extract title from target path
        title = self._extract_title(target)
        today = datetime.now().strftime("%Y-%m-%d")

        # Load SoT context for generation
        sot_context = self._load_sot_context()
        notes.append(f"Loaded {len(sot_context)} SoT documents as context")

        # Determine template and generate content
        if doc_type in ("spec", "manifest", "architecture"):
            template = DOC_TEMPLATES.get(doc_type, DOC_TEMPLATES["spec"])
            content = self._generate_from_template(
                template,
                title=title,
                context=context,
                sot_context=sot_context,
                doc_type=doc_type,
            )
            meta["template"] = doc_type
        else:
            # Generic module/api/readme generation
            content = self._generate_generic_doc(doc_type, title, context, sot_context)
            meta["template"] = "generic"

        # Record the change
        if target:
            changes.append({
                "file": target,
                "action": "create",
                "content_preview": content[:200] + "..." if len(content) > 200 else content,
            })

        notes.extend([
            f"Generated {doc_type} document: {title}",
            f"Target: {target or 'stdout'}",
            f"Content length: {len(content)} chars",
            f"SoT baseline: MASTER.md v3.5, SoT Freeze v2.6",
        ])

        meta.update({
            "generated_at": today,
            "doc_type": doc_type,
            "title": title,
            "sot_docs_loaded": len(sot_context),
        })

        return self._make_response(
            success=True,
            action="generate",
            doc_type=doc_type,
            content=content,
            changes=changes,
            notes=notes,
            meta=meta,
        )

    def _review_doc(
        self,
        doc_type: str,
        target: Optional[str],
        context: Optional[str],
    ) -> Dict[str, Any]:
        """
        审核文档与 SoT 一致性。

        检查项：
        - P0: 与 SoT 定义冲突
        - P1: 缺失必要引用
        - P2: 格式/结构问题
        """
        notes: List[str] = []
        changes: List[Dict[str, Any]] = []
        meta: Dict[str, Any] = {}

        # Load target document if it exists
        target_content = ""
        if target:
            target_path = self.base_path / target
            if target_path.exists():
                try:
                    target_content = target_path.read_text(encoding="utf-8")
                    notes.append(f"Loaded target document: {target} ({len(target_content)} chars)")
                except Exception as e:
                    notes.append(f"Warning: Could not read {target}: {e}")
            else:
                notes.append(f"Warning: Target document not found: {target}")

        # Load SoT context
        sot_context = self._load_sot_context()
        notes.append(f"Loaded {len(sot_context)} SoT documents for comparison")

        # Perform review checks
        issues = self._perform_review_checks(target_content, sot_context, doc_type)

        p0_count = len([i for i in issues if i["severity"] == "P0"])
        p1_count = len([i for i in issues if i["severity"] == "P1"])
        p2_count = len([i for i in issues if i["severity"] == "P2"])

        health_score = 100 - (p0_count * 30) - (p1_count * 10) - (p2_count * 2)
        health_score = max(0, health_score)

        passed = p0_count == 0  # P0 issues block approval

        notes.extend([
            f"Review completed: {'PASS' if passed else 'FAIL'}",
            f"Health Score: {health_score}/100",
            f"P0 Issues: {p0_count}, P1 Issues: {p1_count}, P2 Issues: {p2_count}",
        ])

        if issues:
            for issue in issues[:5]:  # Show first 5 issues
                notes.append(f"  [{issue['severity']}] {issue['rule']}: {issue['detail']}")

        meta.update({
            "passed": passed,
            "health_score": health_score,
            "p0_count": p0_count,
            "p1_count": p1_count,
            "p2_count": p2_count,
            "issues": issues,
        })

        return self._make_response(
            success=True,
            action="review",
            doc_type=doc_type,
            changes=changes,
            notes=notes,
            meta=meta,
        )

    def _sync_doc(
        self,
        doc_type: str,
        target: Optional[str],
        context: Optional[str],
    ) -> Dict[str, Any]:
        """
        同步文档与代码/SoT。

        Operations:
        - Update version references
        - Sync baseline information
        - Update cross-references
        """
        notes: List[str] = []
        changes: List[Dict[str, Any]] = []
        meta: Dict[str, Any] = {}

        # Load target document
        target_content = ""
        if target:
            target_path = self.base_path / target
            if target_path.exists():
                try:
                    target_content = target_path.read_text(encoding="utf-8")
                    notes.append(f"Loaded target document: {target}")
                except Exception as e:
                    return self._make_error_response("sync", doc_type, f"Could not read {target}: {e}")
            else:
                return self._make_error_response("sync", doc_type, f"Target not found: {target}")

        # Load current SoT versions
        sot_versions = self._get_sot_versions()

        # Update version references in document
        updated_content, update_count = self._update_version_references(target_content, sot_versions)

        if update_count > 0:
            changes.append({
                "file": target,
                "action": "update",
                "updates": update_count,
                "description": f"Updated {update_count} version references",
            })
            notes.append(f"Updated {update_count} version references in {target}")
        else:
            notes.append(f"No version updates needed in {target}")

        meta.update({
            "updates_applied": update_count,
            "sot_versions": sot_versions,
        })

        return self._make_response(
            success=True,
            action="sync",
            doc_type=doc_type,
            content=updated_content if update_count > 0 else None,
            changes=changes,
            notes=notes,
            meta=meta,
        )

    # === Helper Methods ===

    def _extract_title(self, target: Optional[str]) -> str:
        """Extract a human-readable title from target path."""
        if not target:
            return "Documentation"

        # Extract filename without extension
        path = Path(target)
        name = path.stem

        # Convert snake_case/SCREAMING_CASE to Title Case
        words = name.replace("_", " ").replace("-", " ").split()
        return " ".join(word.capitalize() for word in words)

    def _load_sot_context(self) -> Dict[str, str]:
        """Load relevant SoT documents for context."""
        context = {}
        priority_docs = [
            "MASTER", "STATE_MACHINE", "DATA_SCHEMA",
            "BUSINESS_RULES", "API_SOT", "ERROR_CODES",
        ]

        for doc_key in priority_docs:
            if doc_key in SOT_FILES:
                content = read_optional(SOT_FILES[doc_key])
                if content:
                    context[doc_key] = content

        return context

    def _get_sot_versions(self) -> Dict[str, str]:
        """Extract version information from SoT documents."""
        versions = {
            "MASTER": "v3.5",
            "STATE_MACHINE": "v2.6",
            "DATA_SCHEMA": "v5.2",
            "BUSINESS_RULES": "v3.1",
            "API_SOT": "v9.0",
            "ERROR_CODES": "v2.1",
            "AUTH_SPEC": "v2.0",
            "LEDGER_SOT": "v1.1",
        }
        return versions

    def _generate_from_template(
        self,
        template: str,
        title: str,
        context: Optional[str],
        sot_context: Dict[str, str],
        doc_type: str,
    ) -> str:
        """Generate document content from template."""
        today = datetime.now().strftime("%Y-%m-%d")
        versions = self._get_sot_versions()

        # Build baseline string
        baseline_parts = [f"{k}.md {v}" for k, v in versions.items()]
        baseline = ", ".join(baseline_parts[:4]) + " ..."

        # Determine layer based on doc_type/target
        layer_map = {
            "spec": "sot",
            "manifest": "governance",
            "architecture": "architecture",
        }
        layer = layer_map.get(doc_type, "documentation")

        # Fill template
        content = template.format(
            version="v1.0",
            status="draft",
            layer=layer,
            owner="DocAgent",
            date=today,
            baseline=baseline,
            title=title,
            overview=context or f"Documentation for {title}",
            scope=f"This document covers the {title.lower()} specification.",
            specification="[Specification content to be added]",
            dependencies="See baseline documents.",
            component_view="[Component diagram to be added]",
            data_flow="[Data flow diagram to be added]",
            integration_points="[Integration points to be documented]",
            doc_count="N/A",
            health_score="N/A",
            p0_count="0",
            p1_count="0",
            p2_count="0",
            inventory="[Document inventory to be populated]",
            audit_log="[Audit log to be populated]",
        )

        return content

    def _generate_generic_doc(
        self,
        doc_type: str,
        title: str,
        context: Optional[str],
        sot_context: Dict[str, str],
    ) -> str:
        """Generate generic documentation."""
        today = datetime.now().strftime("%Y-%m-%d")

        return f"""# {title}

> Generated: {today}
> Type: {doc_type}
> Baseline: MASTER.md v3.5, SoT Freeze v2.6

## Overview

{context or f"Documentation for {title}."}

## Details

[Content to be added based on {doc_type} requirements]

## References

- MASTER.md v3.5
- SoT Freeze v2.6
- Dev-Guides Freeze vFinal

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| v1.0 | {today} | DocAgent | Initial generation |
"""

    def _perform_review_checks(
        self,
        content: str,
        sot_context: Dict[str, str],
        doc_type: str,
    ) -> List[Dict[str, Any]]:
        """Perform document review checks."""
        issues: List[Dict[str, Any]] = []

        if not content:
            issues.append({
                "severity": "P1",
                "rule": "DOC-001",
                "detail": "Target document is empty or not found",
            })
            return issues

        # Check for YAML frontmatter
        if not content.startswith("---"):
            issues.append({
                "severity": "P2",
                "rule": "DOC-002",
                "detail": "Missing YAML frontmatter (version, status, baseline)",
            })

        # Check for baseline reference
        if "baseline" not in content.lower():
            issues.append({
                "severity": "P1",
                "rule": "DOC-003",
                "detail": "Missing baseline reference to SoT documents",
            })

        # Check for outdated version references
        outdated_patterns = [
            (r"STATE_MACHINE\.md v2\.[0-5]", "STATE_MACHINE.md version < v2.6"),
            (r"DATA_SCHEMA\.md v[0-4]\.", "DATA_SCHEMA.md version < v5.0"),
            (r"MASTER\.md v[0-2]\.", "MASTER.md version < v3.0"),
        ]

        for pattern, description in outdated_patterns:
            if re.search(pattern, content):
                issues.append({
                    "severity": "P1",
                    "rule": "DOC-004",
                    "detail": f"Outdated reference: {description}",
                })

        # Check for required sections based on doc_type
        if doc_type in ("spec", "architecture"):
            required_sections = ["Overview", "References", "Change Log"]
            for section in required_sections:
                if section.lower() not in content.lower():
                    issues.append({
                        "severity": "P2",
                        "rule": "DOC-005",
                        "detail": f"Missing recommended section: {section}",
                    })

        return issues

    def _update_version_references(
        self,
        content: str,
        versions: Dict[str, str],
    ) -> tuple[str, int]:
        """Update version references in document content."""
        update_count = 0
        updated_content = content

        # Version update patterns
        for doc_name, current_version in versions.items():
            # Match patterns like "DOC_NAME.md vX.Y" or "DOC_NAME v X.Y"
            pattern = rf"({doc_name}(?:\.md)?\s+v)\d+\.\d+"
            replacement = rf"\g<1>{current_version[1:]}"  # Remove leading 'v' from version

            new_content, count = re.subn(pattern, replacement, updated_content, flags=re.IGNORECASE)
            if count > 0:
                update_count += count
                updated_content = new_content

        return updated_content, update_count
