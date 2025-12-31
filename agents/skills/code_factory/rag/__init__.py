"""
RAG 知识库模块 v5.0 - 借鉴 Dify

提供文档索引和语义检索能力:
- 索引 SoT 文档
- 索引代码库
- 语义搜索
- 上下文增强

基准文档: MASTER.md v4.6
版本: v5.0
"""

from .indexer import (
    DocumentIndexer,
    IndexedDocument,
    IndexStats,
)
from .retriever import (
    DocumentRetriever,
    RetrievalResult,
    RetrievalContext,
)
from .knowledge_base import (
    KnowledgeBase,
    KnowledgeBaseConfig,
    create_knowledge_base,
)

__all__ = [
    # 索引器
    "DocumentIndexer",
    "IndexedDocument",
    "IndexStats",
    
    # 检索器
    "DocumentRetriever",
    "RetrievalResult",
    "RetrievalContext",
    
    # 知识库
    "KnowledgeBase",
    "KnowledgeBaseConfig",
    "create_knowledge_base",
]


