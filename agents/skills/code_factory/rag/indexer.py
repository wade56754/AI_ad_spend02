"""
文档索引器 v5.0

功能:
- 索引 Markdown 文档
- 索引 Python/TypeScript 代码
- 支持增量更新
- 文档分块

基准文档: MASTER.md v4.6
版本: v5.0
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Any, Iterator
from datetime import datetime
from enum import Enum
import hashlib
import re


class DocumentType(str, Enum):
    """文档类型"""
    MARKDOWN = "markdown"
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    YAML = "yaml"
    JSON = "json"
    OTHER = "other"


@dataclass
class DocumentChunk:
    """文档块"""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 位置信息
    start_line: int = 0
    end_line: int = 0
    
    # 嵌入向量 (延迟计算)
    embedding: Optional[List[float]] = None
    
    def __len__(self) -> int:
        return len(self.content)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "start_line": self.start_line,
            "end_line": self.end_line,
        }


@dataclass
class IndexedDocument:
    """已索引的文档"""
    id: str
    path: str
    doc_type: DocumentType
    chunks: List[DocumentChunk]
    
    # 元数据
    title: Optional[str] = None
    hash: str = ""
    indexed_at: str = ""
    
    # 统计
    total_chunks: int = 0
    total_chars: int = 0
    
    def __post_init__(self):
        if not self.indexed_at:
            self.indexed_at = datetime.now().isoformat()
        self.total_chunks = len(self.chunks)
        self.total_chars = sum(len(c) for c in self.chunks)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "path": self.path,
            "doc_type": self.doc_type.value,
            "title": self.title,
            "hash": self.hash,
            "indexed_at": self.indexed_at,
            "total_chunks": self.total_chunks,
            "total_chars": self.total_chars,
            "chunks": [c.to_dict() for c in self.chunks],
        }


@dataclass
class IndexStats:
    """索引统计"""
    total_documents: int = 0
    total_chunks: int = 0
    total_chars: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    last_updated: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_documents": self.total_documents,
            "total_chunks": self.total_chunks,
            "total_chars": self.total_chars,
            "by_type": self.by_type,
            "last_updated": self.last_updated,
        }


class DocumentIndexer:
    """
    文档索引器
    
    功能:
    - 递归扫描目录
    - 智能分块
    - 计算文档哈希
    - 支持增量更新
    
    使用方式:
    ```python
    indexer = DocumentIndexer(chunk_size=500, chunk_overlap=50)
    
    # 索引单个文件
    doc = indexer.index_file(Path("docs/sot/MASTER.md"))
    
    # 索引目录
    docs = indexer.index_directory(Path("docs/sot/"))
    
    # 获取统计
    stats = indexer.get_stats()
    ```
    """
    
    # 文件类型映射
    EXTENSION_MAP = {
        ".md": DocumentType.MARKDOWN,
        ".markdown": DocumentType.MARKDOWN,
        ".py": DocumentType.PYTHON,
        ".ts": DocumentType.TYPESCRIPT,
        ".tsx": DocumentType.TYPESCRIPT,
        ".js": DocumentType.JAVASCRIPT,
        ".jsx": DocumentType.JAVASCRIPT,
        ".yaml": DocumentType.YAML,
        ".yml": DocumentType.YAML,
        ".json": DocumentType.JSON,
    }
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        include_extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ):
        """初始化索引器
        
        Args:
            chunk_size: 块大小 (字符数)
            chunk_overlap: 块重叠 (字符数)
            include_extensions: 包含的文件扩展名
            exclude_patterns: 排除的路径模式
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.include_extensions = include_extensions or [".md", ".py", ".ts", ".tsx"]
        self.exclude_patterns = exclude_patterns or [
            "__pycache__",
            "node_modules",
            ".git",
            "venv",
            ".venv",
            "dist",
            "build",
        ]
        
        # 索引存储
        self._documents: Dict[str, IndexedDocument] = {}
    
    def index_file(self, path: Path) -> Optional[IndexedDocument]:
        """索引单个文件
        
        Args:
            path: 文件路径
            
        Returns:
            IndexedDocument 或 None
        """
        if not path.exists() or not path.is_file():
            return None
        
        # 检查扩展名
        if path.suffix not in self.include_extensions:
            return None
        
        # 读取内容
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            return None
        
        # 计算哈希
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        # 检查是否需要重新索引
        doc_id = str(path)
        if doc_id in self._documents:
            existing = self._documents[doc_id]
            if existing.hash == content_hash:
                return existing  # 无变化，返回缓存
        
        # 确定文档类型
        doc_type = self.EXTENSION_MAP.get(path.suffix, DocumentType.OTHER)
        
        # 分块
        chunks = self._chunk_document(content, doc_type, path)
        
        # 提取标题
        title = self._extract_title(content, doc_type)
        
        # 创建索引文档
        doc = IndexedDocument(
            id=doc_id,
            path=str(path),
            doc_type=doc_type,
            chunks=chunks,
            title=title,
            hash=content_hash,
        )
        
        # 存储
        self._documents[doc_id] = doc
        
        return doc
    
    def index_directory(
        self, 
        directory: Path,
        recursive: bool = True,
    ) -> List[IndexedDocument]:
        """索引目录
        
        Args:
            directory: 目录路径
            recursive: 是否递归
            
        Returns:
            IndexedDocument 列表
        """
        if not directory.exists() or not directory.is_dir():
            return []
        
        documents = []
        
        # 扫描文件
        pattern = "**/*" if recursive else "*"
        for path in directory.glob(pattern):
            # 检查排除模式
            if any(p in str(path) for p in self.exclude_patterns):
                continue
            
            # 索引文件
            doc = self.index_file(path)
            if doc:
                documents.append(doc)
        
        return documents
    
    def _chunk_document(
        self, 
        content: str, 
        doc_type: DocumentType,
        path: Path,
    ) -> List[DocumentChunk]:
        """分块文档
        
        Args:
            content: 文档内容
            doc_type: 文档类型
            path: 文件路径
            
        Returns:
            DocumentChunk 列表
        """
        if doc_type == DocumentType.MARKDOWN:
            return self._chunk_markdown(content, path)
        elif doc_type in (DocumentType.PYTHON, DocumentType.TYPESCRIPT, DocumentType.JAVASCRIPT):
            return self._chunk_code(content, path)
        else:
            return self._chunk_plain(content, path)
    
    def _chunk_markdown(self, content: str, path: Path) -> List[DocumentChunk]:
        """分块 Markdown 文档 (按标题分割)"""
        chunks = []
        lines = content.split("\n")
        
        current_chunk = []
        current_start = 0
        chunk_index = 0
        
        for i, line in enumerate(lines):
            # 检测标题
            if line.startswith("#") and current_chunk:
                # 保存当前块
                chunk_content = "\n".join(current_chunk)
                if chunk_content.strip():
                    chunks.append(DocumentChunk(
                        id=f"{path}#chunk-{chunk_index}",
                        content=chunk_content,
                        metadata={
                            "path": str(path),
                            "type": "markdown",
                        },
                        start_line=current_start,
                        end_line=i - 1,
                    ))
                    chunk_index += 1
                
                # 开始新块
                current_chunk = [line]
                current_start = i
            else:
                current_chunk.append(line)
        
        # 保存最后一块
        if current_chunk:
            chunk_content = "\n".join(current_chunk)
            if chunk_content.strip():
                chunks.append(DocumentChunk(
                    id=f"{path}#chunk-{chunk_index}",
                    content=chunk_content,
                    metadata={
                        "path": str(path),
                        "type": "markdown",
                    },
                    start_line=current_start,
                    end_line=len(lines) - 1,
                ))
        
        # 如果块太大，进一步分割
        final_chunks = []
        for chunk in chunks:
            if len(chunk.content) > self.chunk_size * 2:
                final_chunks.extend(self._split_large_chunk(chunk))
            else:
                final_chunks.append(chunk)
        
        return final_chunks
    
    def _chunk_code(self, content: str, path: Path) -> List[DocumentChunk]:
        """分块代码 (按函数/类分割)"""
        chunks = []
        lines = content.split("\n")
        
        # 简单的代码分块：按空行或类/函数定义分割
        current_chunk = []
        current_start = 0
        chunk_index = 0
        
        for i, line in enumerate(lines):
            # 检测函数/类定义
            is_definition = (
                line.strip().startswith("def ") or
                line.strip().startswith("class ") or
                line.strip().startswith("async def ") or
                line.strip().startswith("function ") or
                line.strip().startswith("export ") or
                line.strip().startswith("interface ") or
                line.strip().startswith("type ")
            )
            
            if is_definition and current_chunk and len("\n".join(current_chunk)) > 100:
                # 保存当前块
                chunk_content = "\n".join(current_chunk)
                if chunk_content.strip():
                    chunks.append(DocumentChunk(
                        id=f"{path}#chunk-{chunk_index}",
                        content=chunk_content,
                        metadata={
                            "path": str(path),
                            "type": "code",
                        },
                        start_line=current_start,
                        end_line=i - 1,
                    ))
                    chunk_index += 1
                
                # 开始新块
                current_chunk = [line]
                current_start = i
            else:
                current_chunk.append(line)
        
        # 保存最后一块
        if current_chunk:
            chunk_content = "\n".join(current_chunk)
            if chunk_content.strip():
                chunks.append(DocumentChunk(
                    id=f"{path}#chunk-{chunk_index}",
                    content=chunk_content,
                    metadata={
                        "path": str(path),
                        "type": "code",
                    },
                    start_line=current_start,
                    end_line=len(lines) - 1,
                ))
        
        return chunks
    
    def _chunk_plain(self, content: str, path: Path) -> List[DocumentChunk]:
        """分块普通文本 (按大小分割)"""
        chunks = []
        
        # 简单按大小分割
        start = 0
        chunk_index = 0
        
        while start < len(content):
            end = start + self.chunk_size
            
            # 尝试在空格处断开
            if end < len(content):
                space_pos = content.rfind(" ", start, end)
                if space_pos > start:
                    end = space_pos
            
            chunk_content = content[start:end].strip()
            if chunk_content:
                chunks.append(DocumentChunk(
                    id=f"{path}#chunk-{chunk_index}",
                    content=chunk_content,
                    metadata={
                        "path": str(path),
                        "type": "plain",
                    },
                ))
                chunk_index += 1
            
            start = end - self.chunk_overlap
            if start < 0:
                start = 0
            if end >= len(content):
                break
        
        return chunks
    
    def _split_large_chunk(self, chunk: DocumentChunk) -> List[DocumentChunk]:
        """分割大块"""
        chunks = []
        content = chunk.content
        
        start = 0
        chunk_index = 0
        
        while start < len(content):
            end = start + self.chunk_size
            
            if end < len(content):
                # 尝试在换行处断开
                newline_pos = content.rfind("\n", start, end)
                if newline_pos > start:
                    end = newline_pos
            
            sub_content = content[start:end].strip()
            if sub_content:
                chunks.append(DocumentChunk(
                    id=f"{chunk.id}-{chunk_index}",
                    content=sub_content,
                    metadata=chunk.metadata.copy(),
                ))
                chunk_index += 1
            
            start = end - self.chunk_overlap
            if start < 0:
                start = 0
            if end >= len(content):
                break
        
        return chunks
    
    def _extract_title(self, content: str, doc_type: DocumentType) -> Optional[str]:
        """提取文档标题"""
        if doc_type == DocumentType.MARKDOWN:
            # 查找第一个 # 标题
            for line in content.split("\n"):
                if line.startswith("# "):
                    return line[2:].strip()
        elif doc_type == DocumentType.PYTHON:
            # 查找模块 docstring
            match = re.search(r'^"""(.+?)"""', content, re.DOTALL)
            if match:
                first_line = match.group(1).split("\n")[0].strip()
                return first_line
        
        return None
    
    def get_document(self, doc_id: str) -> Optional[IndexedDocument]:
        """获取已索引的文档"""
        return self._documents.get(doc_id)
    
    def get_all_documents(self) -> List[IndexedDocument]:
        """获取所有已索引的文档"""
        return list(self._documents.values())
    
    def get_all_chunks(self) -> Iterator[DocumentChunk]:
        """获取所有文档块"""
        for doc in self._documents.values():
            yield from doc.chunks
    
    def get_stats(self) -> IndexStats:
        """获取索引统计"""
        stats = IndexStats()
        
        for doc in self._documents.values():
            stats.total_documents += 1
            stats.total_chunks += doc.total_chunks
            stats.total_chars += doc.total_chars
            
            doc_type = doc.doc_type.value
            stats.by_type[doc_type] = stats.by_type.get(doc_type, 0) + 1
        
        stats.last_updated = datetime.now().isoformat()
        
        return stats
    
    def clear(self):
        """清空索引"""
        self._documents.clear()


