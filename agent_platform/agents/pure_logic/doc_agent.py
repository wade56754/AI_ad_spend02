"""
DocAgentPure - MCP 安全的文档 Agent

Phase 2: 从 agents/agent_core/doc_agent.py 迁移

功能:
- 生成文档（spec, manifest, architecture）
- 审核文档与 SoT 一致性
- 同步文档版本引用

MCP 安全性:
- mcp_safe=True: 不调用 LLM
- 使用模板和规则生成/检查文档

基准对齐:
- AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md Phase 2
- Agent Layer Freeze v1.0
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import re

from agent_platform.core.protocol import AgentProtocol, AgentContext
from agent_platform.core.registry import register_agent

logger = logging.getLogger(__name__)


# Document templates
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
""",
}


class DocAgentPure(AgentProtocol):
    """
    MCP 安全的文档 Agent

    支持操作:
    - action="generate": 生成文档
    - action="review": 审核文档
    - action="sync": 同步版本引用
    """

    def __init__(self, base_path: Optional[Path] = None) -> None:
        self._base_path = base_path or Path.cwd()

    @property
    def name(self) -> str:
        return "doc"

    @property
    def description(self) -> str:
        return "文档生成与审核 Agent（MCP 安全）"

    @property
    def version(self) -> str:
        return "2.0.0"

    def handle_request(
        self,
        request: Dict[str, Any],
        context: Optional[AgentContext] = None,
    ) -> Dict[str, Any]:
        """
        处理文档请求。

        Args:
            request: {
                "action": "generate" | "review" | "sync",
                "doc_type": "spec" | "manifest" | "module" | ...,
                "target": Optional[str],
                "context": Optional[str]
            }
        """
        context_obj = context or AgentContext()
        run_id = context_obj.run_id

        action = request.get("action", "review")
        doc_type = request.get("doc_type", "module")
        target = request.get("target")
        ctx_info = request.get("context")

        logger.info(
            f"[run_id={run_id}] DocAgentPure: "
            f"action={action}, doc_type={doc_type}, target={target}"
        )

        try:
            if action == "generate":
                return self._generate_doc(doc_type, target, ctx_info, run_id)
            elif action == "review":
                return self._review_doc(doc_type, target, ctx_info, run_id)
            elif action == "sync":
                return self._sync_doc(doc_type, target, ctx_info, run_id)
            else:
                return self._make_error_response(
                    action, doc_type,
                    f"Unknown action: {action}. Use 'generate', 'review', or 'sync'."
                )
        except Exception as e:
            logger.error(f"[run_id={run_id}] DocAgentPure error: {e}")
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
        """Create standardized response"""
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
        return self._make_response(
            success=False, action=action, doc_type=doc_type, error=error
        )

    def _generate_doc(
        self,
        doc_type: str,
        target: Optional[str],
        ctx_info: Optional[str],
        run_id: str,
    ) -> Dict[str, Any]:
        """生成文档"""
        notes: List[str] = []
        changes: List[Dict[str, Any]] = []
        today = datetime.now().strftime("%Y-%m-%d")
        title = self._extract_title(target)

        # 获取 SoT 版本
        sot_versions = self._get_sot_versions()
        baseline = ", ".join(f"{k} {v}" for k, v in list(sot_versions.items())[:4])

        if doc_type in DOC_TEMPLATES:
            template = DOC_TEMPLATES[doc_type]
            content = template.format(
                version="v1.0",
                layer="documentation",
                owner="DocAgent",
                date=today,
                baseline=baseline,
                title=title,
                overview=ctx_info or f"Documentation for {title}",
                scope=f"This document covers {title.lower()}.",
                specification="[To be added]",
                dependencies="See baseline documents.",
                doc_count="N/A",
                health_score="N/A",
                p0_count="0",
                p1_count="0",
                p2_count="0",
                inventory="[To be populated]",
                audit_log="[To be populated]",
            )
        else:
            content = f"""# {title}

> Generated: {today}
> Type: {doc_type}
> Baseline: {baseline}

## Overview

{ctx_info or f"Documentation for {title}."}

## References

- MASTER.md v3.5
- SoT Freeze v2.6
"""

        if target:
            changes.append({
                "file": target,
                "action": "create",
                "content_preview": content[:200] + "...",
            })

        notes.extend([
            f"Generated {doc_type} document: {title}",
            f"Target: {target or 'stdout'}",
            f"Content length: {len(content)} chars",
        ])

        return self._make_response(
            success=True,
            action="generate",
            doc_type=doc_type,
            content=content,
            changes=changes,
            notes=notes,
            meta={"run_id": run_id, "agent": self.name, "title": title},
        )

    def _review_doc(
        self,
        doc_type: str,
        target: Optional[str],
        ctx_info: Optional[str],
        run_id: str,
    ) -> Dict[str, Any]:
        """审核文档"""
        notes: List[str] = []
        issues: List[Dict[str, Any]] = []

        # 加载目标文档
        content = ""
        if target:
            target_path = self._base_path / target
            if target_path.exists():
                try:
                    content = target_path.read_text(encoding="utf-8")
                    notes.append(f"Loaded: {target} ({len(content)} chars)")
                except Exception as e:
                    notes.append(f"Warning: Could not read {target}: {e}")
            else:
                notes.append(f"Warning: Not found: {target}")

        # 执行检查
        issues = self._perform_review_checks(content, doc_type)

        p0 = len([i for i in issues if i["severity"] == "P0"])
        p1 = len([i for i in issues if i["severity"] == "P1"])
        p2 = len([i for i in issues if i["severity"] == "P2"])

        health = max(0, 100 - p0 * 30 - p1 * 10 - p2 * 2)
        passed = p0 == 0

        notes.extend([
            f"Review: {'PASS' if passed else 'FAIL'}",
            f"Health: {health}/100",
            f"P0={p0}, P1={p1}, P2={p2}",
        ])

        return self._make_response(
            success=True,
            action="review",
            doc_type=doc_type,
            notes=notes,
            meta={
                "run_id": run_id,
                "agent": self.name,
                "passed": passed,
                "health_score": health,
                "issues": issues,
            },
        )

    def _sync_doc(
        self,
        doc_type: str,
        target: Optional[str],
        ctx_info: Optional[str],
        run_id: str,
    ) -> Dict[str, Any]:
        """同步文档版本引用"""
        notes: List[str] = []
        changes: List[Dict[str, Any]] = []

        if not target:
            return self._make_error_response("sync", doc_type, "Target required")

        target_path = self._base_path / target
        if not target_path.exists():
            return self._make_error_response("sync", doc_type, f"Not found: {target}")

        try:
            content = target_path.read_text(encoding="utf-8")
        except Exception as e:
            return self._make_error_response("sync", doc_type, f"Read error: {e}")

        sot_versions = self._get_sot_versions()
        updated, count = self._update_version_refs(content, sot_versions)

        if count > 0:
            changes.append({
                "file": target,
                "action": "update",
                "updates": count,
            })
            notes.append(f"Updated {count} version references")
        else:
            notes.append("No updates needed")

        return self._make_response(
            success=True,
            action="sync",
            doc_type=doc_type,
            content=updated if count > 0 else None,
            changes=changes,
            notes=notes,
            meta={"run_id": run_id, "agent": self.name, "updates": count},
        )

    # === Helper methods ===

    def _extract_title(self, target: Optional[str]) -> str:
        if not target:
            return "Documentation"
        name = Path(target).stem
        words = name.replace("_", " ").replace("-", " ").split()
        return " ".join(w.capitalize() for w in words)

    def _get_sot_versions(self) -> Dict[str, str]:
        """获取 SoT 文档版本（默认值）"""
        return {
            "MASTER.md": "v3.5",
            "STATE_MACHINE.md": "v2.6",
            "DATA_SCHEMA.md": "v5.2",
            "API_SOT.md": "v9.0",
        }

    def _perform_review_checks(
        self, content: str, doc_type: str
    ) -> List[Dict[str, Any]]:
        """执行文档检查"""
        issues: List[Dict[str, Any]] = []

        if not content:
            issues.append({
                "severity": "P1",
                "rule": "DOC-001",
                "detail": "Document is empty or not found",
            })
            return issues

        if not content.startswith("---"):
            issues.append({
                "severity": "P2",
                "rule": "DOC-002",
                "detail": "Missing YAML frontmatter",
            })

        if "baseline" not in content.lower():
            issues.append({
                "severity": "P1",
                "rule": "DOC-003",
                "detail": "Missing baseline reference",
            })

        return issues

    def _update_version_refs(
        self, content: str, versions: Dict[str, str]
    ) -> tuple[str, int]:
        """更新版本引用"""
        count = 0
        updated = content

        for doc_name, ver in versions.items():
            pattern = rf"({doc_name}\s+v)\d+\.\d+"
            new, n = re.subn(pattern, rf"\g<1>{ver[1:]}", updated, flags=re.I)
            if n > 0:
                count += n
                updated = new

        return updated, count


# ============================================================
# 自动注册到 Registry
# ============================================================

def _doc_agent_factory(base_path: Optional[Path] = None, **_: Any) -> DocAgentPure:
    return DocAgentPure(base_path=base_path)


register_agent(
    name="doc",
    factory=_doc_agent_factory,
    description="文档生成与审核 Agent（MCP 安全）",
    version="2.0.0",
    tags=["doc", "documentation", "mcp_safe", "pure_logic"],
    mcp_safe=True,
    override=True,
)
