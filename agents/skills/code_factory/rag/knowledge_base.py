"""
知识库管理器 v5.0 - 借鉴 Dify

功能:
- 管理多个文档索引
- 统一检索接口
- 支持多知识源

基准文档: MASTER.md v4.6
版本: v5.0
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable, Union
from enum import Enum
import json
import os

from .indexer import DocumentIndexer, IndexedDocument, IndexStats
from .retriever import DocumentRetriever, RetrievalResult, RetrievalContext, RetrievalMode


class KnowledgeSource(str, Enum):
    """知识源类型"""
    SOT = "sot"           # SoT 文档
    CODE = "code"         # 代码库
    HISTORY = "history"   # 历史对话
    CUSTOM = "custom"     # 自定义


@dataclass
class KnowledgeBaseConfig:
    """知识库配置"""
    # 路径配置
    project_dir: Path = field(default_factory=Path.cwd)
    sot_dir: Optional[Path] = None
    code_dirs: List[Path] = field(default_factory=list)
    history_dir: Optional[Path] = None
    
    # 索引配置
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    # 检索配置
    default_mode: RetrievalMode = RetrievalMode.KEYWORD
    top_k: int = 10
    
    # 持久化配置
    persist_dir: Optional[Path] = None
    
    def __post_init__(self):
        self.project_dir = Path(self.project_dir)
        
        if self.sot_dir is None:
            self.sot_dir = self.project_dir / "docs" / "sot"
        else:
            self.sot_dir = Path(self.sot_dir)
        
        if not self.code_dirs:
            self.code_dirs = [
                self.project_dir / "backend",
                self.project_dir / "frontend" / "src",
            ]
        else:
            self.code_dirs = [Path(d) for d in self.code_dirs]
        
        if self.history_dir is None:
            self.history_dir = self.project_dir / ".agents" / "history"
        else:
            self.history_dir = Path(self.history_dir)
        
        if self.persist_dir is None:
            self.persist_dir = self.project_dir / ".agents" / "knowledge"
        else:
            self.persist_dir = Path(self.persist_dir)


class KnowledgeBase:
    """
    知识库管理器
    
    整合多个知识源:
    - SoT 文档 (docs/sot/*.md)
    - 代码库 (backend/, frontend/src/)
    - 历史对话 (.agents/history/)
    
    使用方式:
    ```python
    # 创建知识库
    kb = KnowledgeBase(config)
    
    # 构建索引
    kb.build_index()
    
    # 搜索
    results = kb.search("日报状态机")
    
    # 获取增强上下文
    context = kb.get_context("如何实现日报导出")
    ```
    """
    
    VERSION = "5.0"
    
    def __init__(
        self,
        config: KnowledgeBaseConfig,
        embedding_fn: Optional[Callable[[str], List[float]]] = None,
    ):
        """初始化知识库
        
        Args:
            config: 知识库配置
            embedding_fn: 嵌入函数 (可选)
        """
        self.config = config
        self.embedding_fn = embedding_fn
        
        # 为每个知识源创建索引器
        self._indexers: Dict[KnowledgeSource, DocumentIndexer] = {}
        self._retrievers: Dict[KnowledgeSource, DocumentRetriever] = {}
        
        # 初始化索引器
        self._init_indexers()
        
        # 统计
        self._is_built = False
    
    def _init_indexers(self):
        """初始化索引器"""
        # SoT 索引器 (Markdown)
        self._indexers[KnowledgeSource.SOT] = DocumentIndexer(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            include_extensions=[".md"],
        )
        
        # 代码索引器
        self._indexers[KnowledgeSource.CODE] = DocumentIndexer(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            include_extensions=[".py", ".ts", ".tsx", ".js", ".jsx"],
        )
        
        # 历史索引器
        self._indexers[KnowledgeSource.HISTORY] = DocumentIndexer(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            include_extensions=[".md", ".json"],
        )
        
        # 创建检索器
        for source, indexer in self._indexers.items():
            self._retrievers[source] = DocumentRetriever(
                indexer=indexer,
                embedding_fn=self.embedding_fn,
                default_mode=self.config.default_mode,
                top_k=self.config.top_k,
            )
    
    def build_index(
        self,
        sources: Optional[List[KnowledgeSource]] = None,
        force_rebuild: bool = False,
    ) -> Dict[str, IndexStats]:
        """构建索引
        
        Args:
            sources: 要构建的知识源 (默认全部)
            force_rebuild: 是否强制重建
            
        Returns:
            各知识源的统计信息
        """
        if sources is None:
            sources = list(KnowledgeSource)
        
        stats = {}
        
        for source in sources:
            if force_rebuild and source in self._indexers:
                self._indexers[source].clear()
            
            if source == KnowledgeSource.SOT:
                if self.config.sot_dir and self.config.sot_dir.exists():
                    self._indexers[source].index_directory(self.config.sot_dir)
            
            elif source == KnowledgeSource.CODE:
                for code_dir in self.config.code_dirs:
                    if code_dir.exists():
                        self._indexers[source].index_directory(code_dir)
            
            elif source == KnowledgeSource.HISTORY:
                if self.config.history_dir and self.config.history_dir.exists():
                    self._indexers[source].index_directory(self.config.history_dir)
            
            stats[source.value] = self._indexers[source].get_stats().to_dict()
        
        self._is_built = True
        return stats
    
    def search(
        self,
        query: str,
        sources: Optional[List[KnowledgeSource]] = None,
        mode: Optional[RetrievalMode] = None,
        top_k: Optional[int] = None,
    ) -> List[RetrievalResult]:
        """搜索所有知识源
        
        Args:
            query: 查询字符串
            sources: 搜索的知识源 (默认全部)
            mode: 检索模式
            top_k: 返回数量
            
        Returns:
            RetrievalResult 列表
        """
        if not self._is_built:
            self.build_index()
        
        if sources is None:
            sources = list(KnowledgeSource)
        
        top_k = top_k or self.config.top_k
        
        # 从各知识源收集结果
        all_results = []
        
        for source in sources:
            if source in self._retrievers:
                results = self._retrievers[source].search(
                    query, 
                    mode=mode, 
                    top_k=top_k,
                )
                
                # 添加知识源标记
                for result in results:
                    result.chunk.metadata["knowledge_source"] = source.value
                
                all_results.extend(results)
        
        # 排序并限制数量
        all_results.sort(key=lambda r: r.score, reverse=True)
        return all_results[:top_k]
    
    def get_context(
        self,
        query: str,
        sources: Optional[List[KnowledgeSource]] = None,
        mode: Optional[RetrievalMode] = None,
        top_k: Optional[int] = None,
    ) -> RetrievalContext:
        """获取检索上下文
        
        Args:
            query: 查询字符串
            sources: 搜索的知识源
            mode: 检索模式
            top_k: 返回数量
            
        Returns:
            RetrievalContext
        """
        results = self.search(query, sources, mode, top_k)
        
        # 统计来源
        source_stats: Dict[str, int] = {}
        for result in results:
            path = result.chunk.metadata.get("path", "unknown")
            source_stats[path] = source_stats.get(path, 0) + 1
        
        return RetrievalContext(
            query=query,
            results=results,
            total_found=len(results),
            sources=source_stats,
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取知识库统计"""
        stats = {
            "version": self.VERSION,
            "is_built": self._is_built,
            "sources": {},
        }
        
        for source, indexer in self._indexers.items():
            stats["sources"][source.value] = indexer.get_stats().to_dict()
        
        return stats
    
    # =========================================================================
    # 便捷方法
    # =========================================================================
    
    def search_sot(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """搜索 SoT 文档"""
        return self.search(
            query,
            sources=[KnowledgeSource.SOT],
            top_k=top_k,
        )
    
    def search_code(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """搜索代码"""
        return self.search(
            query,
            sources=[KnowledgeSource.CODE],
            top_k=top_k,
        )
    
    def get_sot_context(self, query: str) -> str:
        """获取 SoT 相关上下文"""
        context = self.get_context(
            query,
            sources=[KnowledgeSource.SOT],
            top_k=5,
        )
        return context.to_prompt_context()
    
    def get_code_context(self, query: str) -> str:
        """获取代码相关上下文"""
        context = self.get_context(
            query,
            sources=[KnowledgeSource.CODE],
            top_k=5,
        )
        return context.to_prompt_context()
    
    # =========================================================================
    # 持久化
    # =========================================================================
    
    def save(self, path: Optional[Path] = None):
        """保存知识库状态"""
        save_dir = path or self.config.persist_dir
        if save_dir is None:
            return
        
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存元数据
        metadata = {
            "version": self.VERSION,
            "is_built": self._is_built,
            "config": {
                "chunk_size": self.config.chunk_size,
                "chunk_overlap": self.config.chunk_overlap,
            },
        }
        
        with open(save_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # 保存各知识源的文档列表
        for source, indexer in self._indexers.items():
            docs = indexer.get_all_documents()
            docs_data = [doc.to_dict() for doc in docs]
            
            with open(save_dir / f"{source.value}_docs.json", "w", encoding="utf-8") as f:
                json.dump(docs_data, f, indent=2, ensure_ascii=False)
    
    def clear(self):
        """清空知识库"""
        for indexer in self._indexers.values():
            indexer.clear()
        self._is_built = False


# ============================================================
# 便捷函数
# ============================================================

def create_knowledge_base(
    project_dir: Union[str, Path] = ".",
    sot_dir: Optional[Union[str, Path]] = None,
    code_dirs: Optional[List[Union[str, Path]]] = None,
    embedding_fn: Optional[Callable] = None,
) -> KnowledgeBase:
    """创建知识库
    
    Args:
        project_dir: 项目根目录
        sot_dir: SoT 文档目录
        code_dirs: 代码目录列表
        embedding_fn: 嵌入函数
        
    Returns:
        KnowledgeBase 实例
    """
    config = KnowledgeBaseConfig(
        project_dir=Path(project_dir),
        sot_dir=Path(sot_dir) if sot_dir else None,
        code_dirs=[Path(d) for d in code_dirs] if code_dirs else [],
    )
    
    return KnowledgeBase(config, embedding_fn)


# ============================================================
# 测试入口
# ============================================================

if __name__ == "__main__":
    import sys
    
    # 获取项目根目录
    project_dir = Path(__file__).parent.parent.parent.parent.parent
    
    print("=" * 60)
    print(f"知识库管理器 v{KnowledgeBase.VERSION}")
    print(f"项目目录: {project_dir}")
    print("=" * 60)
    
    # 创建知识库
    config = KnowledgeBaseConfig(project_dir=project_dir)
    kb = KnowledgeBase(config)
    
    # 构建索引
    print("\n构建索引...")
    stats = kb.build_index()
    
    print("\n索引统计:")
    for source, stat in stats.items():
        print(f"\n  {source}:")
        print(f"    文档数: {stat['total_documents']}")
        print(f"    块数: {stat['total_chunks']}")
        print(f"    字符数: {stat['total_chars']}")
    
    # 测试搜索
    print("\n" + "=" * 60)
    print("测试搜索: '日报状态机'")
    print("=" * 60)
    
    results = kb.search("日报状态机", top_k=3)
    for i, result in enumerate(results, 1):
        print(f"\n[{i}] 分数: {result.score:.2f}")
        print(f"    来源: {result.chunk.metadata.get('path', 'unknown')}")
        print(f"    内容: {result.chunk.content[:100]}...")

