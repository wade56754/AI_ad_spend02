"""
code_searcher_skill.py - 代码搜索 Skill

代码来源说明 (Code Sources):
================================================================================
本 Skill 的设计和实现借鉴了以下开源项目：

1. code-graph-rag (MIT License)
   - GitHub: https://github.com/vitali87/code-graph-rag
   - 借鉴内容:
     - Tree-sitter AST 解析多语言代码
     - UniXcoder 语义向量化概念
     - 知识图谱存储代码关系架构

2. code-rag (MIT License)
   - GitHub: https://github.com/rawveg/code-rag
   - 借鉴内容:
     - RAG (Retrieval-Augmented Generation) 检索架构
     - 向量相似度搜索模式

3. Aider (Apache-2.0 License)
   - GitHub: https://github.com/paul-gauthier/aider
   - 借鉴内容:
     - Repo Map 项目结构索引技术
     - 文件依赖关系分析方法
================================================================================

职责: 从多个来源搜索与需求相关的参考代码
优先级: GitHub 外部代码 > 代码资料库 > 本项目代码 (本项目代码由AI生成，可靠性较低)

基准对齐:
- CODE_FACTORY_REFERENCE_PROJECTS.md v1.0
- Agent Layer Freeze v1.0
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import re
import time
import yaml

logger = logging.getLogger(__name__)


# ============================================================================
# 数据类型定义
# ============================================================================

@dataclass
class SearchCandidate:
    """
    搜索候选结果

    设计参考: code-graph-rag 的检索结果结构
    """
    id: str
    source: str  # "local_project" | "code_library" | "github"
    path: str
    relevance_score: float  # 0-100
    snippet: str
    match_reason: str
    tech_stack_match: float  # 0-100
    adaptation_hint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "path": self.path,
            "relevance_score": self.relevance_score,
            "snippet": self.snippet,
            "match_reason": self.match_reason,
            "tech_stack_match": self.tech_stack_match,
            "adaptation_hint": self.adaptation_hint,
        }


@dataclass
class SearchStats:
    """搜索统计信息"""
    total_searched: int = 0
    local_matches: int = 0
    library_matches: int = 0
    github_matches: int = 0
    search_time_ms: float = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_searched": self.total_searched,
            "local_matches": self.local_matches,
            "library_matches": self.library_matches,
            "github_matches": self.github_matches,
            "search_time_ms": self.search_time_ms,
        }


# ============================================================================
# 关键词映射表 (中文 → 英文)
# ============================================================================

KEYWORD_MAPPING: Dict[str, List[str]] = {
    # 功能类
    "导出": ["export", "download", "xlsx"],
    "导入": ["import", "upload", "parse"],
    "分页": ["pagination", "page", "paginate", "paging"],
    "表格": ["table", "grid", "list", "data-table", "datagrid"],
    "表单": ["form", "input", "field", "formik"],
    "上传": ["upload", "file-upload", "multipart"],
    "下载": ["download", "export", "blob"],
    "搜索": ["search", "query", "filter", "find"],
    "筛选": ["filter", "select", "where"],
    "排序": ["sort", "order", "orderby"],
    "图表": ["chart", "graph", "visualization", "echarts"],
    # 认证/权限
    "认证": ["auth", "login", "jwt", "token"],
    "权限": ["permission", "rbac", "role", "access"],
    "登录": ["login", "signin", "authenticate"],
    # 业务领域
    "日报": ["daily-report", "report", "daily"],
    "账本": ["ledger", "accounting", "balance"],
    "充值": ["topup", "recharge", "deposit"],
    "项目": ["project", "campaign"],
    "供应商": ["supplier", "vendor"],
    # 技术术语
    "excel": ["excel", "xlsx", "openpyxl", "xlsxwriter"],
    "api": ["api", "endpoint", "router", "route"],
    "crud": ["crud", "create", "read", "update", "delete"],
    "状态机": ["state-machine", "fsm", "workflow", "transition"],
    "验证": ["validation", "validate", "validator"],
}


# ============================================================================
# CodeSearcherSkill 主类
# ============================================================================

class CodeSearcherSkill:
    """
    代码搜索 Skill

    架构设计借鉴:
    - code-graph-rag: 语义搜索 + AST 解析
    - Aider: Repo Map 项目结构索引
    """

    # 来源权重 (GitHub 外部代码优先，本项目代码由AI生成可靠性较低)
    SOURCE_WEIGHTS = {
        "github": 1.8,         # GitHub 可靠代码优先
        "code_library": 1.5,   # 已验证的参考代码
        "local_project": 0.8,  # 本项目AI生成代码，优先级最低
    }

    def __init__(self, base_path: Optional[Path] = None):
        """
        初始化搜索器

        Args:
            base_path: 项目根目录，默认自动检测
        """
        self.base_path = base_path or self._detect_project_root()
        self.code_library = self.base_path / "code-library"
        self.inventory = self._load_inventory()
        self.references = self._load_references()

        logger.info(f"CodeSearcherSkill initialized: base_path={self.base_path}")

    def search(
        self,
        requirement: str,
        sources: Optional[Dict[str, bool]] = None,
        max_candidates: int = 5,
        tech_stack_filter: Optional[Dict[str, str]] = None,
        search_mode: str = "hybrid",
    ) -> Dict[str, Any]:
        """
        搜索参考代码

        Args:
            requirement: 需求描述 (中英文均可)
            sources: 搜索来源配置
            max_candidates: 最大候选数
            tech_stack_filter: 技术栈过滤
            search_mode: 搜索模式 ("keyword" | "semantic" | "hybrid")

        Returns:
            {
                "success": bool,
                "data": {
                    "candidates": [...],
                    "search_stats": {...}
                },
                "error": Optional[str]
            }
        """
        start_time = time.time()

        # 默认搜索配置 (优先使用外部可靠代码)
        sources = sources or {
            "github": True,        # 默认启用 GitHub 搜索 (外部可靠代码优先)
            "code_library": True,  # 已验证的参考代码
            "local_project": True, # 本项目AI生成代码作为参考
        }

        logger.info(f"Search started: requirement='{requirement[:50]}...' sources={sources}")

        stats = SearchStats()
        candidates: List[SearchCandidate] = []

        try:
            # 1. 提取关键词
            keywords = self._extract_keywords(requirement)
            logger.debug(f"Extracted keywords: {keywords}")

            # 2. 搜索本项目
            if sources.get("local_project"):
                local_results = self._search_local_project(
                    requirement, keywords, tech_stack_filter
                )
                candidates.extend(local_results)
                stats.local_matches = len(local_results)

            # 3. 搜索代码资料库
            if sources.get("code_library"):
                library_results = self._search_code_library(
                    requirement, keywords, tech_stack_filter
                )
                candidates.extend(library_results)
                stats.library_matches = len(library_results)

            # 4. 搜索 GitHub (可选)
            if sources.get("github"):
                github_results = self._search_github(
                    requirement, keywords, tech_stack_filter
                )
                candidates.extend(github_results)
                stats.github_matches = len(github_results)

            # 5. 排序和过滤
            candidates = self._rank_candidates(candidates)
            candidates = candidates[:max_candidates]

            # 6. 统计信息
            stats.total_searched = (
                stats.local_matches +
                stats.library_matches +
                stats.github_matches
            )
            stats.search_time_ms = (time.time() - start_time) * 1000

            logger.info(
                f"Search completed: {len(candidates)} candidates, "
                f"{stats.search_time_ms:.2f}ms"
            )

            return {
                "success": True,
                "data": {
                    "candidates": [c.to_dict() for c in candidates],
                    "search_stats": stats.to_dict(),
                },
                "error": None,
            }

        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            return {
                "success": False,
                "data": None,
                "error": str(e),
            }

    # ========================================================================
    # 关键词提取
    # ========================================================================

    def _extract_keywords(self, requirement: str) -> List[str]:
        """
        从需求中提取关键词

        借鉴: code-graph-rag 的关键词提取策略
        """
        keywords = []
        requirement_lower = requirement.lower()

        # 1. 使用映射表提取
        for cn_word, en_words in KEYWORD_MAPPING.items():
            if cn_word in requirement_lower:
                keywords.extend(en_words)
                keywords.append(cn_word)

        # 2. 提取英文单词
        english_words = re.findall(r'[a-zA-Z]{3,}', requirement)
        keywords.extend([w.lower() for w in english_words])

        # 3. 去重
        return list(set(keywords))

    # ========================================================================
    # 本项目搜索
    # ========================================================================

    def _search_local_project(
        self,
        requirement: str,
        keywords: List[str],
        tech_stack_filter: Optional[Dict[str, str]] = None,
    ) -> List[SearchCandidate]:
        """
        搜索本项目代码

        借鉴: Aider 的 Repo Map 技术 - 从项目结构中搜索
        """
        candidates = []

        # 从 inventory 中搜索
        for category, features in self.inventory.get("features", {}).items():
            for item in features:
                if self._matches_keywords(item, keywords):
                    # 计算相关度
                    relevance = self._calculate_relevance(item, keywords)

                    # 过滤低相关度
                    if relevance < 40:
                        continue

                    # 获取代码片段
                    files = item.get("files", [])
                    snippet = self._get_code_snippet(files) if files else ""

                    candidates.append(SearchCandidate(
                        id=f"local-{category}-{item.get('name', 'unknown')}",
                        source="local_project",
                        path=files[0] if files else "",
                        relevance_score=relevance,
                        snippet=snippet[:500],  # 限制长度
                        match_reason=f"本项目已有类似功能: {item.get('name', '')}",
                        tech_stack_match=100,  # 本项目代码 100% 匹配
                        adaptation_hint=item.get("description"),
                    ))

        # 直接在代码目录中搜索 (简化实现)
        code_matches = self._grep_in_codebase(keywords)
        candidates.extend(code_matches)

        return candidates

    def _grep_in_codebase(
        self,
        keywords: List[str],
    ) -> List[SearchCandidate]:
        """
        在代码库中 grep 搜索关键词

        简化实现，生产环境应使用 Tree-sitter AST 解析
        """
        candidates = []

        # 搜索后端代码
        backend_dir = self.base_path / "backend"
        if backend_dir.exists():
            for py_file in backend_dir.rglob("*.py"):
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    matched_keywords = [
                        kw for kw in keywords
                        if kw.lower() in content.lower()
                    ]

                    if len(matched_keywords) >= 2:  # 至少匹配 2 个关键词
                        relevance = min(100, 40 + len(matched_keywords) * 15)

                        candidates.append(SearchCandidate(
                            id=f"local-grep-{py_file.stem}",
                            source="local_project",
                            path=str(py_file.relative_to(self.base_path)),
                            relevance_score=relevance,
                            snippet=self._extract_relevant_snippet(content, matched_keywords),
                            match_reason=f"关键词匹配: {', '.join(matched_keywords[:3])}",
                            tech_stack_match=100,
                            adaptation_hint=None,
                        ))
                except Exception as e:
                    logger.debug(f"Failed to read {py_file}: {e}")

        return candidates[:5]  # 限制结果数量

    # ========================================================================
    # 代码资料库搜索
    # ========================================================================

    def _search_code_library(
        self,
        requirement: str,
        keywords: List[str],
        tech_stack_filter: Optional[Dict[str, str]] = None,
    ) -> List[SearchCandidate]:
        """
        搜索代码资料库

        从 code-library/references 目录中搜索
        """
        candidates = []

        for ref in self.references:
            if self._matches_keywords(ref, keywords):
                relevance = self._calculate_relevance(ref, keywords)

                if relevance < 40:
                    continue

                # 检查技术栈兼容性
                tech_match = self._check_tech_stack_match(ref, tech_stack_filter)

                candidates.append(SearchCandidate(
                    id=ref.get("id", f"lib-{len(candidates)}"),
                    source="code_library",
                    path=ref.get("github", ref.get("code_path", "")),
                    relevance_score=relevance,
                    snippet="",  # 资料库只存索引，需要时再加载
                    match_reason=f"代码资料库参考: {ref.get('name', '')}",
                    tech_stack_match=tech_match,
                    adaptation_hint=ref.get("adaptation_notes"),
                ))

        return candidates

    # ========================================================================
    # GitHub 搜索
    # ========================================================================

    def _search_github(
        self,
        requirement: str,
        keywords: List[str],
        tech_stack_filter: Optional[Dict[str, str]] = None,
    ) -> List[SearchCandidate]:
        """
        搜索 GitHub 参考代码

        优先搜索已索引的可靠开源项目 (github-repos.yaml)
        这些项目经过人工筛选，代码质量有保证

        TODO: 实现 GitHub Code Search API 实时搜索
        """
        candidates = []

        # 从 github-repos.yaml 搜索已索引的可靠项目
        github_repos = self.code_library / "references" / "github-repos.yaml"
        if github_repos.exists():
            try:
                data = yaml.safe_load(github_repos.read_text(encoding="utf-8"))

                # 遍历所有类别
                for category, repos in data.items():
                    if not isinstance(repos, list):
                        continue

                    for repo in repos:
                        if self._matches_keywords(repo, keywords):
                            relevance = self._calculate_relevance(repo, keywords)

                            if relevance < 35:  # GitHub 代码阈值稍低，因为质量更可靠
                                continue

                            # 检查技术栈兼容性
                            tech_match = self._check_tech_stack_match(repo, tech_stack_filter)

                            # 检查优先级
                            priority_bonus = 0
                            if repo.get("priority") == "P0":
                                priority_bonus = 15
                            elif repo.get("priority") == "P1":
                                priority_bonus = 10

                            candidates.append(SearchCandidate(
                                id=repo.get("id", f"github-{len(candidates)}"),
                                source="github",
                                path=repo.get("github", ""),
                                relevance_score=relevance + priority_bonus,
                                snippet=self._format_github_snippet(repo),
                                match_reason=f"GitHub 可靠项目: {repo.get('name', '')} - {repo.get('description', '')[:50]}",
                                tech_stack_match=tech_match,
                                adaptation_hint=self._format_adaptation_hint(repo),
                            ))

            except Exception as e:
                logger.warning(f"Failed to search github-repos.yaml: {e}")

        # 也搜索 by-feature 目录下的 GitHub 参考
        by_feature_dir = self.code_library / "references" / "by-feature"
        if by_feature_dir.exists():
            for ref_file in by_feature_dir.glob("*.yaml"):
                try:
                    data = yaml.safe_load(ref_file.read_text(encoding="utf-8"))
                    github_refs = data.get("github_references", [])

                    for ref in github_refs:
                        if self._matches_keywords(ref, keywords):
                            relevance = self._calculate_relevance(ref, keywords)

                            if relevance < 35:
                                continue

                            candidates.append(SearchCandidate(
                                id=ref.get("id", f"github-feat-{len(candidates)}"),
                                source="github",
                                path=ref.get("github", ref.get("url", "")),
                                relevance_score=relevance,
                                snippet=ref.get("code_example", ""),
                                match_reason=f"GitHub 功能参考: {ref.get('name', '')}",
                                tech_stack_match=self._check_tech_stack_match(ref, tech_stack_filter),
                                adaptation_hint=ref.get("adaptation_notes"),
                            ))

                except Exception as e:
                    logger.debug(f"Failed to load {ref_file}: {e}")

        logger.info(f"GitHub search found {len(candidates)} candidates")
        return candidates

    def _format_github_snippet(self, repo: Dict[str, Any]) -> str:
        """格式化 GitHub 仓库代码片段"""
        lines = []

        # 优先使用 code_example (实际可复用的代码)
        code_example = repo.get("code_example", "")
        if code_example and code_example.strip():
            lines.append(f'"""')
            lines.append(f"代码来源: {repo.get('name', 'Unknown')}")
            lines.append(f"GitHub: {repo.get('github', '')}")
            lines.append(f"License: {repo.get('license', 'Unknown')}")
            lines.append(f'"""')
            lines.append("")
            lines.append(code_example.strip())
            return "\n".join(lines)

        # 如果没有 code_example，返回元数据
        lines.append(f"# {repo.get('name', 'Unknown')}")
        lines.append(f"# GitHub: {repo.get('github', '')}")
        lines.append(f"# License: {repo.get('license', 'Unknown')}")
        lines.append(f"# Stars: {repo.get('stars', 'N/A')}")
        lines.append("")
        lines.append(f"# Description: {repo.get('description', '')}")
        lines.append("")

        use_cases = repo.get("use_cases", [])
        if use_cases:
            lines.append("# Use Cases:")
            for uc in use_cases[:5]:
                lines.append(f"#   - {uc}")

        key_files = repo.get("key_files", [])
        if key_files:
            lines.append("")
            lines.append("# Key Files:")
            for kf in key_files[:5]:
                lines.append(f"#   - {kf}")

        return "\n".join(lines)

    def _format_adaptation_hint(self, repo: Dict[str, Any]) -> str:
        """格式化适配提示"""
        hints = []

        # 兼容性信息
        compat = repo.get("compatibility", {})
        if compat:
            if compat.get("python_version"):
                hints.append(f"Python {compat['python_version']}")
            if compat.get("node_version"):
                hints.append(f"Node {compat['node_version']}")
            if compat.get("relevant_for"):
                hints.append(f"适用于: {', '.join(compat['relevant_for'])}")

        # 关键文件
        key_files = repo.get("key_files", [])
        if key_files:
            hints.append(f"参考文件: {key_files[0]}")

        # 集成方式
        if repo.get("integration"):
            hints.append(f"集成: {repo['integration'].strip()[:50]}")

        return "; ".join(hints) if hints else None

    # ========================================================================
    # 排序和评分
    # ========================================================================

    def _rank_candidates(
        self,
        candidates: List[SearchCandidate],
    ) -> List[SearchCandidate]:
        """
        综合排序候选结果

        借鉴: code-graph-rag 的多维度评分
        """
        def score(c: SearchCandidate) -> float:
            # 来源权重
            source_weight = self.SOURCE_WEIGHTS.get(c.source, 1.0)

            # 综合得分
            total = (
                c.relevance_score * 0.4 * source_weight +
                c.tech_stack_match * 0.3 +
                (100 if c.adaptation_hint else 80) * 0.2 +  # 有适配提示加分
                (100 if c.snippet else 60) * 0.1  # 有代码片段加分
            )

            return total

        return sorted(candidates, key=score, reverse=True)

    def _calculate_relevance(
        self,
        item: Dict[str, Any],
        keywords: List[str],
    ) -> float:
        """计算相关度分数"""
        item_text = str(item).lower()
        matched = sum(1 for kw in keywords if kw.lower() in item_text)

        # 基础分 40，每匹配一个关键词 +15，最高 100
        return min(100, 40 + matched * 15)

    def _matches_keywords(
        self,
        item: Dict[str, Any],
        keywords: List[str],
    ) -> bool:
        """检查是否匹配关键词"""
        item_text = str(item).lower()
        return any(kw.lower() in item_text for kw in keywords)

    def _check_tech_stack_match(
        self,
        ref: Dict[str, Any],
        tech_stack_filter: Optional[Dict[str, str]] = None,
    ) -> float:
        """检查技术栈兼容性"""
        if not tech_stack_filter:
            return 80  # 无过滤时默认 80 分

        ref_tech = ref.get("tech_stack", [])
        if not ref_tech:
            return 70

        ref_tech_str = " ".join(ref_tech).lower()

        match_count = 0
        total_filters = len(tech_stack_filter)

        for key, value in tech_stack_filter.items():
            if value.lower() in ref_tech_str:
                match_count += 1

        return (match_count / total_filters) * 100 if total_filters > 0 else 80

    # ========================================================================
    # 辅助方法
    # ========================================================================

    def _get_code_snippet(
        self,
        files: List[str],
        max_lines: int = 30,
    ) -> str:
        """获取代码片段"""
        if not files:
            return ""

        file_path = self.base_path / files[0]
        if file_path.exists():
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                lines = content.split("\n")[:max_lines]
                return "\n".join(lines)
            except Exception as e:
                logger.debug(f"Failed to read {file_path}: {e}")

        return ""

    def _extract_relevant_snippet(
        self,
        content: str,
        keywords: List[str],
        context_lines: int = 5,
    ) -> str:
        """提取包含关键词的代码片段"""
        lines = content.split("\n")

        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(kw.lower() in line_lower for kw in keywords):
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                return "\n".join(lines[start:end])

        return "\n".join(lines[:10])  # 默认返回前 10 行

    def _detect_project_root(self) -> Path:
        """自动检测项目根目录"""
        # 从当前文件向上查找
        current = Path(__file__).resolve()

        for parent in current.parents:
            if (parent / "CLAUDE.md").exists() or (parent / ".claude").exists():
                return parent

        # 默认返回 AI_ad_spend02
        return Path("D:/project/AI_ad_spend02")

    def _load_inventory(self) -> Dict[str, Any]:
        """加载本项目功能清单"""
        inventory_file = self.code_library / "inventory" / "backend-features.yaml"

        if inventory_file.exists():
            try:
                return yaml.safe_load(inventory_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"Failed to load inventory: {e}")

        return {"features": {}}

    def _load_references(self) -> List[Dict[str, Any]]:
        """
        加载本地参考代码索引

        注意: 只加载 by-feature 目录下的本地参考代码
        GitHub 参考由 _search_github 单独处理，避免重复搜索
        """
        references = []
        refs_dir = self.code_library / "references" / "by-feature"

        if refs_dir.exists():
            for ref_file in refs_dir.glob("*.yaml"):
                try:
                    data = yaml.safe_load(ref_file.read_text(encoding="utf-8"))
                    # 只加载 local_references (本地参考代码)
                    # external_references 和 github 参考由 _search_github 处理
                    references.extend(data.get("local_references", []))
                    # 也支持直接的 references (向后兼容)
                    for ref in data.get("references", []):
                        # 只添加非 GitHub 的参考
                        if not ref.get("github") and not ref.get("source") == "github":
                            references.append(ref)
                except Exception as e:
                    logger.warning(f"Failed to load {ref_file}: {e}")

        # 注意: 不再加载 github-repos.yaml
        # GitHub 参考由 _search_github 单独处理，并正确格式化 code_example

        return references


# ============================================================================
# Skill 入口函数
# ============================================================================

def code_searcher_skill(
    requirement: str,
    sources: Optional[Dict[str, bool]] = None,
    max_candidates: int = 5,
    tech_stack_filter: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    代码搜索 Skill 入口函数

    代码来源: 借鉴 code-graph-rag + Aider 架构

    Args:
        requirement: 需求描述
        sources: 搜索来源配置
        max_candidates: 最大候选数
        tech_stack_filter: 技术栈过滤

    Returns:
        搜索结果
    """
    searcher = CodeSearcherSkill()
    return searcher.search(
        requirement=requirement,
        sources=sources,
        max_candidates=max_candidates,
        tech_stack_filter=tech_stack_filter,
    )


__all__ = [
    "CodeSearcherSkill",
    "SearchCandidate",
    "code_searcher_skill",
]
