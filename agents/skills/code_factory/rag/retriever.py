"""
文档检索器 v5.0

功能:
- 语义搜索
- 关键词搜索
- 混合检索
- 上下文增强

基准文档: MASTER.md v4.6
版本: v5.0
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
from enum import Enum
import re
from difflib import SequenceMatcher

from .indexer import DocumentIndexer, DocumentChunk, IndexedDocument


class RetrievalMode(str, Enum):
    """检索模式"""
    KEYWORD = "keyword"       # 关键词匹配
    SEMANTIC = "semantic"     # 语义搜索 (需要嵌入)
    HYBRID = "hybrid"         # 混合模式


@dataclass
class RetrievalResult:
    """检索结果"""
    chunk: DocumentChunk
    score: float
    match_type: str  # "keyword" | "semantic" | "hybrid"
    highlights: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk.id,
            "content": self.chunk.content,
            "score": self.score,
            "match_type": self.match_type,
            "highlights": self.highlights,
            "metadata": self.chunk.metadata,
        }


@dataclass
class RetrievalContext:
    """检索上下文 - 用于增强代码生成"""
    query: str
    results: List[RetrievalResult]
    total_found: int
    
    # 来源统计
    sources: Dict[str, int] = field(default_factory=dict)
    
    def to_prompt_context(self, max_chunks: int = 5) -> str:
        """生成提示词上下文
        
        Args:
            max_chunks: 最大块数
            
        Returns:
            提示词上下文字符串
        """
        if not self.results:
            return "## 相关文档\n\n未找到相关文档。"
        
        lines = ["## 相关文档", ""]
        
        for i, result in enumerate(self.results[:max_chunks], 1):
            path = result.chunk.metadata.get("path", "未知")
            lines.append(f"### [{i}] {path} (相关度: {result.score:.2f})")
            lines.append("")
            
            # 截取内容
            content = result.chunk.content
            if len(content) > 500:
                content = content[:500] + "..."
            
            lines.append("```")
            lines.append(content)
            lines.append("```")
            lines.append("")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "total_found": self.total_found,
            "sources": self.sources,
        }


class DocumentRetriever:
    """
    文档检索器
    
    支持多种检索模式:
    - 关键词匹配 (默认)
    - 语义搜索 (需要嵌入函数)
    - 混合模式
    
    使用方式:
    ```python
    # 创建检索器
    retriever = DocumentRetriever(indexer)
    
    # 关键词搜索
    results = retriever.search("日报状态机")
    
    # 获取增强上下文
    context = retriever.get_context("如何实现日报导出")
    prompt = context.to_prompt_context()
    ```
    """
    
    def __init__(
        self,
        indexer: DocumentIndexer,
        embedding_fn: Optional[Callable[[str], List[float]]] = None,
        default_mode: RetrievalMode = RetrievalMode.KEYWORD,
        top_k: int = 10,
    ):
        """初始化检索器
        
        Args:
            indexer: 文档索引器
            embedding_fn: 嵌入函数 (用于语义搜索)
            default_mode: 默认检索模式
            top_k: 返回结果数量
        """
        self.indexer = indexer
        self.embedding_fn = embedding_fn
        self.default_mode = default_mode
        self.top_k = top_k
    
    def search(
        self,
        query: str,
        mode: Optional[RetrievalMode] = None,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """搜索文档
        
        Args:
            query: 查询字符串
            mode: 检索模式
            top_k: 返回数量
            filters: 过滤条件
            
        Returns:
            RetrievalResult 列表
        """
        mode = mode or self.default_mode
        top_k = top_k or self.top_k
        
        if mode == RetrievalMode.KEYWORD:
            results = self._keyword_search(query, filters)
        elif mode == RetrievalMode.SEMANTIC:
            results = self._semantic_search(query, filters)
        else:  # HYBRID
            results = self._hybrid_search(query, filters)
        
        # 排序并限制数量
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]
    
    def get_context(
        self,
        query: str,
        mode: Optional[RetrievalMode] = None,
        top_k: Optional[int] = None,
    ) -> RetrievalContext:
        """获取检索上下文
        
        Args:
            query: 查询字符串
            mode: 检索模式
            top_k: 返回数量
            
        Returns:
            RetrievalContext
        """
        results = self.search(query, mode, top_k)
        
        # 统计来源
        sources: Dict[str, int] = {}
        for result in results:
            path = result.chunk.metadata.get("path", "unknown")
            sources[path] = sources.get(path, 0) + 1
        
        return RetrievalContext(
            query=query,
            results=results,
            total_found=len(results),
            sources=sources,
        )
    
    def _keyword_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """关键词搜索"""
        results = []
        
        # 提取关键词
        keywords = self._extract_keywords(query)
        
        # 遍历所有块
        for chunk in self.indexer.get_all_chunks():
            # 应用过滤器
            if filters and not self._apply_filters(chunk, filters):
                continue
            
            # 计算匹配分数
            score, highlights = self._calculate_keyword_score(chunk.content, keywords)
            
            if score > 0:
                results.append(RetrievalResult(
                    chunk=chunk,
                    score=score,
                    match_type="keyword",
                    highlights=highlights,
                ))
        
        return results
    
    def _semantic_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """语义搜索"""
        if not self.embedding_fn:
            # 回退到关键词搜索
            return self._keyword_search(query, filters)
        
        results = []
        
        # 计算查询嵌入
        query_embedding = self.embedding_fn(query)
        
        # 遍历所有块
        for chunk in self.indexer.get_all_chunks():
            # 应用过滤器
            if filters and not self._apply_filters(chunk, filters):
                continue
            
            # 计算块嵌入 (懒加载)
            if chunk.embedding is None:
                chunk.embedding = self.embedding_fn(chunk.content)
            
            # 计算相似度
            score = self._cosine_similarity(query_embedding, chunk.embedding)
            
            if score > 0.3:  # 阈值
                results.append(RetrievalResult(
                    chunk=chunk,
                    score=score,
                    match_type="semantic",
                ))
        
        return results
    
    def _hybrid_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """混合搜索"""
        # 获取两种结果
        keyword_results = self._keyword_search(query, filters)
        semantic_results = self._semantic_search(query, filters) if self.embedding_fn else []
        
        # 合并结果
        chunk_scores: Dict[str, float] = {}
        chunk_map: Dict[str, RetrievalResult] = {}
        
        # 关键词分数 (权重 0.4)
        for result in keyword_results:
            chunk_id = result.chunk.id
            chunk_scores[chunk_id] = result.score * 0.4
            chunk_map[chunk_id] = result
        
        # 语义分数 (权重 0.6)
        for result in semantic_results:
            chunk_id = result.chunk.id
            if chunk_id in chunk_scores:
                chunk_scores[chunk_id] += result.score * 0.6
            else:
                chunk_scores[chunk_id] = result.score * 0.6
                chunk_map[chunk_id] = result
        
        # 生成合并结果
        results = []
        for chunk_id, score in chunk_scores.items():
            result = chunk_map[chunk_id]
            results.append(RetrievalResult(
                chunk=result.chunk,
                score=score,
                match_type="hybrid",
                highlights=result.highlights,
            ))
        
        return results
    
    def _extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        # 简单分词
        words = re.findall(r'\b\w+\b', query.lower())
        
        # 过滤停用词
        stopwords = {
            "的", "是", "在", "和", "有", "了", "我", "你", "他",
            "the", "a", "an", "is", "are", "in", "on", "to", "for",
            "如何", "怎么", "什么", "哪些", "为什么",
        }
        
        return [w for w in words if w not in stopwords and len(w) > 1]
    
    def _calculate_keyword_score(
        self,
        content: str,
        keywords: List[str],
    ) -> tuple[float, List[str]]:
        """计算关键词匹配分数"""
        content_lower = content.lower()
        
        matches = 0
        highlights = []
        
        for keyword in keywords:
            if keyword in content_lower:
                matches += 1
                # 查找匹配位置
                start = content_lower.find(keyword)
                if start >= 0:
                    # 提取上下文
                    context_start = max(0, start - 20)
                    context_end = min(len(content), start + len(keyword) + 20)
                    highlight = content[context_start:context_end]
                    highlights.append(f"...{highlight}...")
        
        if not keywords:
            return 0.0, []
        
        # 分数 = 匹配数 / 关键词数
        score = matches / len(keywords)
        
        # 加入长度惩罚 (避免超长文档得分过高)
        length_penalty = min(1.0, 1000 / max(len(content), 1))
        score *= length_penalty
        
        return score, highlights
    
    def _apply_filters(
        self,
        chunk: DocumentChunk,
        filters: Dict[str, Any],
    ) -> bool:
        """应用过滤条件"""
        for key, value in filters.items():
            if key == "path":
                if value not in chunk.metadata.get("path", ""):
                    return False
            elif key == "type":
                if chunk.metadata.get("type") != value:
                    return False
            elif key in chunk.metadata:
                if chunk.metadata[key] != value:
                    return False
        return True
    
    def _cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float],
    ) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    # =========================================================================
    # 便捷方法
    # =========================================================================
    
    def search_sot(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """搜索 SoT 文档"""
        return self.search(
            query,
            filters={"type": "markdown"},
            top_k=top_k,
        )
    
    def search_code(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """搜索代码"""
        return self.search(
            query,
            filters={"type": "code"},
            top_k=top_k,
        )
    
    def find_similar(
        self,
        content: str,
        top_k: int = 5,
    ) -> List[RetrievalResult]:
        """查找相似内容"""
        return self.search(content, mode=RetrievalMode.KEYWORD, top_k=top_k)


