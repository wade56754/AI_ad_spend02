"""
代码搜索器 - SEARCH 阶段实现 v4.5

职责: 从多个来源搜索与需求相关的参考代码

搜索来源:
1. 本项目代码 (最高优先级)
2. 代码资料库 (code-library)
3. GitHub (可选，需网络)

搜索策略:
1. 关键词匹配 (中英文映射)
2. AST 分析 (函数/类名匹配)
3. 代码结构匹配 (装饰器、导入)

来源:
- code-graph-rag: 语义搜索架构
- Aider: Repo Map 概念

v4.5 更新:
- 增加 AST 级别的函数/类名搜索
- 增加装饰器模式匹配 (@router.*, @pytest.*)
- 改进相关度计算算法
"""

import re
import os
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum


class SearchSource(Enum):
    """搜索来源"""
    LOCAL_PROJECT = "local_project"
    CODE_LIBRARY = "code_library"
    GITHUB = "github"


@dataclass
class SearchCandidate:
    """搜索候选结果"""
    id: str
    source: str
    path: str
    relevance_score: float
    snippet: str
    match_reason: str
    tech_stack_match: float = 0.0
    adaptation_hint: str = ""
    full_content: str = ""
    language: str = ""

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
            "language": self.language,
        }


@dataclass
class SearchStats:
    """搜索统计"""
    total_searched: int = 0
    local_matches: int = 0
    library_matches: int = 0
    github_matches: int = 0
    search_time_ms: int = 0


@dataclass
class SearchResult:
    """搜索结果"""
    success: bool
    candidates: List[SearchCandidate] = field(default_factory=list)
    stats: SearchStats = field(default_factory=SearchStats)
    error: str = None


# 中英文关键词映射
KEYWORD_MAPPING = {
    "导出": ["export", "download", "excel"],
    "导入": ["import", "upload"],
    "分页": ["pagination", "page", "paginate"],
    "表格": ["table", "grid", "list", "data-table"],
    "表单": ["form", "input", "field"],
    "上传": ["upload", "file-upload"],
    "下载": ["download", "export"],
    "搜索": ["search", "query", "filter"],
    "筛选": ["filter", "select"],
    "排序": ["sort", "order"],
    "图表": ["chart", "graph", "visualization"],
    "认证": ["auth", "login", "jwt"],
    "权限": ["permission", "rbac", "role"],
    "日报": ["daily-report", "report", "daily"],
    "账本": ["ledger", "accounting"],
    "充值": ["topup", "recharge", "deposit"],
    "状态": ["status", "state", "workflow"],
    "列表": ["list", "index", "get_all"],
    "详情": ["detail", "get", "show"],
    "创建": ["create", "add", "new"],
    "更新": ["update", "edit", "modify"],
    "删除": ["delete", "remove"],
}


class CodeSearcher:
    """
    代码搜索器

    搜索策略:
    1. 提取关键词 (中英文映射)
    2. 本项目搜索 (grep/glob)
    3. 代码资料库搜索 (inventory YAML)
    4. GitHub 搜索 (可选)
    """

    def __init__(
        self,
        project_root: Path,
        code_library_path: Path = None,
        enable_github: bool = False
    ):
        self.project_root = Path(project_root)
        self.code_library_path = code_library_path or self.project_root / "code-library"
        self.enable_github = enable_github

        # 搜索配置
        self.backend_dirs = ["backend/routers", "backend/services", "backend/schemas"]
        self.frontend_dirs = ["frontend/src"]
        self.exclude_patterns = ["__pycache__", "node_modules", ".git", "*.pyc"]

    def search(
        self,
        requirement: str,
        sources: Dict[str, bool] = None,
        max_candidates: int = 5,
        tech_stack_filter: Dict[str, str] = None,
    ) -> SearchResult:
        """
        执行搜索

        Args:
            requirement: 需求描述
            sources: 搜索来源配置
            max_candidates: 最大候选数
            tech_stack_filter: 技术栈过滤

        Returns:
            SearchResult
        """
        import time
        start_time = time.time()

        sources = sources or {
            "local_project": True,
            "code_library": True,
            "github": self.enable_github,
        }

        candidates = []
        stats = SearchStats()

        # Step 1: 提取关键词
        keywords = self._extract_keywords(requirement)

        # Step 2: 本项目搜索
        if sources.get("local_project", True):
            local_candidates = self._search_local_project(keywords, tech_stack_filter)
            candidates.extend(local_candidates)
            stats.local_matches = len(local_candidates)

        # Step 3: 代码资料库搜索
        if sources.get("code_library", True):
            library_candidates = self._search_code_library(keywords, tech_stack_filter)
            candidates.extend(library_candidates)
            stats.library_matches = len(library_candidates)

        # Step 4: GitHub 搜索 (TODO)
        if sources.get("github", False):
            # github_candidates = self._search_github(keywords, tech_stack_filter)
            # candidates.extend(github_candidates)
            # stats.github_matches = len(github_candidates)
            pass

        # Step 5: 排序和截断
        candidates = self._rank_candidates(candidates)[:max_candidates]

        stats.total_searched = stats.local_matches + stats.library_matches + stats.github_matches
        stats.search_time_ms = int((time.time() - start_time) * 1000)

        return SearchResult(
            success=True,
            candidates=candidates,
            stats=stats,
        )

    def _extract_keywords(self, requirement: str) -> List[str]:
        """提取关键词 (中英文映射)"""
        keywords = set()

        # 中文关键词映射
        for cn_word, en_words in KEYWORD_MAPPING.items():
            if cn_word in requirement:
                keywords.update(en_words)

        # 英文关键词直接提取
        en_words = re.findall(r'[a-zA-Z_]+', requirement.lower())
        keywords.update(en_words)

        # 过滤太短的词
        keywords = {k for k in keywords if len(k) > 2}

        return list(keywords)

    def _search_local_project(
        self,
        keywords: List[str],
        tech_stack_filter: Dict[str, str] = None,
    ) -> List[SearchCandidate]:
        """搜索本项目代码"""
        candidates = []

        # 确定搜索目录
        search_dirs = []
        language_filter = tech_stack_filter.get("language") if tech_stack_filter else None

        if not language_filter or language_filter == "python":
            search_dirs.extend(self.backend_dirs)
        if not language_filter or language_filter in ["typescript", "javascript"]:
            search_dirs.extend(self.frontend_dirs)

        # 搜索每个目录
        for search_dir in search_dirs:
            dir_path = self.project_root / search_dir
            if not dir_path.exists():
                continue

            for file_path in dir_path.rglob("*"):
                if not file_path.is_file():
                    continue
                if any(p in str(file_path) for p in self.exclude_patterns):
                    continue
                if file_path.suffix not in [".py", ".ts", ".tsx", ".js", ".jsx"]:
                    continue

                # 读取文件内容
                try:
                    content = file_path.read_text(encoding="utf-8")
                except Exception:
                    continue

                # 计算相关度 (传入文件路径以启用 AST 分析)
                score, matches = self._calculate_relevance(content, keywords, file_path)

                if score > 25:  # 相关度阈值 (v4.5 降低以捕获更多候选)
                    rel_path = file_path.relative_to(self.project_root)
                    snippet = self._extract_snippet(content, matches)

                    candidates.append(SearchCandidate(
                        id=f"local_{hash(str(rel_path))}",
                        source=SearchSource.LOCAL_PROJECT.value,
                        path=str(rel_path),
                        relevance_score=score,
                        snippet=snippet,
                        match_reason=f"匹配关键词: {', '.join(matches[:3])}",
                        tech_stack_match=95.0,  # 本项目代码高匹配度
                        adaptation_hint="本项目代码，几乎无需适配",
                        full_content=content,
                        language="python" if file_path.suffix == ".py" else "typescript",
                    ))

        return candidates

    def _search_code_library(
        self,
        keywords: List[str],
        tech_stack_filter: Dict[str, str] = None,
    ) -> List[SearchCandidate]:
        """搜索代码资料库"""
        candidates = []

        if not self.code_library_path.exists():
            return candidates

        # 搜索 inventory 目录
        inventory_dir = self.code_library_path / "inventory"
        if inventory_dir.exists():
            for yaml_file in inventory_dir.glob("*.yaml"):
                try:
                    import yaml
                    with open(yaml_file, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)

                    if not data:
                        continue

                    # 匹配 tags 和 features
                    entries = data if isinstance(data, list) else [data]
                    for entry in entries:
                        if not isinstance(entry, dict):
                            continue

                        tags = entry.get("tags", [])
                        features = entry.get("features", [])
                        all_terms = tags + features

                        matches = [k for k in keywords if any(k in t.lower() for t in all_terms)]

                        if matches:
                            score = min(100, len(matches) * 20 + 40)
                            candidates.append(SearchCandidate(
                                id=f"lib_{entry.get('id', hash(str(entry)))}",
                                source=SearchSource.CODE_LIBRARY.value,
                                path=entry.get("path", str(yaml_file)),
                                relevance_score=score,
                                snippet=entry.get("description", "")[:200],
                                match_reason=f"匹配特性: {', '.join(matches[:3])}",
                                tech_stack_match=85.0,  # 资料库已验证代码
                                adaptation_hint=entry.get("adaptation_hint", "需要技术栈适配"),
                                language=entry.get("language", "python"),
                            ))
                except Exception:
                    continue

        # 搜索 snippets 目录
        snippets_dir = self.code_library_path / "snippets"
        if snippets_dir.exists():
            for snippet_file in snippets_dir.rglob("*"):
                if not snippet_file.is_file():
                    continue
                if snippet_file.suffix not in [".py", ".ts", ".tsx"]:
                    continue

                try:
                    content = snippet_file.read_text(encoding="utf-8")
                    score, matches = self._calculate_relevance(content, keywords)

                    if score > 30:
                        rel_path = snippet_file.relative_to(self.code_library_path)
                        snippet = self._extract_snippet(content, matches)

                        candidates.append(SearchCandidate(
                            id=f"snippet_{hash(str(rel_path))}",
                            source=SearchSource.CODE_LIBRARY.value,
                            path=str(rel_path),
                            relevance_score=score,
                            snippet=snippet,
                            match_reason=f"代码片段匹配: {', '.join(matches[:3])}",
                            tech_stack_match=85.0,
                            adaptation_hint="代码片段参考",
                            full_content=content,
                            language="python" if snippet_file.suffix == ".py" else "typescript",
                        ))
                except Exception:
                    continue

        return candidates

    def _calculate_relevance(self, content: str, keywords: List[str], file_path: Path = None) -> Tuple[float, List[str]]:
        """计算相关度分数 (增强版 v4.5)

        使用多维度计算:
        1. 关键词频率匹配 (40%)
        2. 函数/类名匹配 (30%)
        3. 装饰器匹配 (15%)
        4. 导入匹配 (15%)

        Args:
            content: 文件内容
            keywords: 关键词列表
            file_path: 可选的文件路径 (用于 AST 分析)

        Returns:
            Tuple[float, List[str]]: (分数, 匹配的关键词列表)
        """
        content_lower = content.lower()
        matches = []
        score = 0

        # 1. 关键词频率匹配 (最高 40 分)
        keyword_score = 0
        for keyword in keywords:
            count = content_lower.count(keyword.lower())
            if count > 0:
                matches.append(keyword)
                keyword_score += 10 + min(count * 3, 15)
        keyword_score = min(40, keyword_score)

        # 2. 函数/类名匹配 (最高 30 分)
        ast_score = 0
        if file_path and file_path.suffix == ".py":
            ast_matches = self._extract_ast_matches(content, keywords)
            if ast_matches:
                matches.extend([f"def:{m}" for m in ast_matches[:3]])
                ast_score = min(30, len(ast_matches) * 10)

        # 3. 装饰器匹配 (最高 15 分)
        decorator_score = 0
        decorator_patterns = [
            (r'@router\.(get|post|put|delete|patch)', 15),  # FastAPI router
            (r'@app\.(get|post|put|delete|patch)', 15),     # FastAPI app
            (r'@pytest\.\w+', 10),                          # pytest
            (r'@dataclass', 8),                             # dataclass
            (r'@property', 5),                              # property
        ]
        for pattern, weight in decorator_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                decorator_score = max(decorator_score, weight)
                matches.append(f"decorator:{pattern}")
                break
        decorator_score = min(15, decorator_score)

        # 4. 导入匹配 (最高 15 分)
        import_score = 0
        import_patterns = [
            (r'from fastapi import', 10),
            (r'from sqlalchemy', 10),
            (r'from pydantic import', 8),
            (r'import React', 10),
            (r'from.*tanstack.*query', 10),
        ]
        for pattern, weight in import_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                import_score += weight
        import_score = min(15, import_score)

        # 总分
        score = keyword_score + ast_score + decorator_score + import_score

        return score, matches

    def _extract_ast_matches(self, content: str, keywords: List[str]) -> List[str]:
        """使用 AST 提取匹配的函数/类名

        Args:
            content: Python 源代码
            keywords: 关键词列表

        Returns:
            List[str]: 匹配的函数/类名
        """
        matches = []
        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                name = None
                if isinstance(node, ast.FunctionDef):
                    name = node.name
                elif isinstance(node, ast.AsyncFunctionDef):
                    name = node.name
                elif isinstance(node, ast.ClassDef):
                    name = node.name

                if name:
                    name_lower = name.lower()
                    # 检查函数/类名是否包含关键词
                    for keyword in keywords:
                        if keyword.lower() in name_lower:
                            matches.append(name)
                            break
                    # 检查函数/类名中的单词
                    name_parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', name)
                    for part in name_parts:
                        if part.lower() in [k.lower() for k in keywords]:
                            if name not in matches:
                                matches.append(name)
                            break

        except SyntaxError:
            # 文件语法错误，跳过 AST 分析
            pass
        except Exception:
            # 其他错误，跳过
            pass

        return matches

    def _extract_snippet(self, content: str, keywords: List[str], max_lines: int = 10) -> str:
        """提取代码片段"""
        lines = content.split("\n")

        # 找到包含关键词的行
        keyword_lines = []
        for i, line in enumerate(lines):
            if any(k.lower() in line.lower() for k in keywords):
                keyword_lines.append(i)

        if not keyword_lines:
            return "\n".join(lines[:max_lines])

        # 以第一个匹配行为中心，提取上下文
        center = keyword_lines[0]
        start = max(0, center - max_lines // 2)
        end = min(len(lines), start + max_lines)

        return "\n".join(lines[start:end])

    def _rank_candidates(self, candidates: List[SearchCandidate]) -> List[SearchCandidate]:
        """排序候选结果"""
        # 权重: 来源 > 相关度 > 技术栈匹配度
        def score_key(c: SearchCandidate) -> float:
            source_weight = {
                SearchSource.LOCAL_PROJECT.value: 1.5,
                SearchSource.CODE_LIBRARY.value: 1.2,
                SearchSource.GITHUB.value: 1.0,
            }.get(c.source, 1.0)

            return (
                c.relevance_score * 0.4 +
                c.tech_stack_match * 0.3 +
                source_weight * 20
            )

        return sorted(candidates, key=score_key, reverse=True)
