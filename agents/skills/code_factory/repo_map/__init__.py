"""
代码地图模块 (Aider 风格)

功能:
- AST 解析提取函数/类签名
- 生成紧凑代码地图
- 支持上下文限制
"""

from .map_generator import RepoMapGenerator, RepoMap, FunctionSig, ClassDef

__all__ = [
    "RepoMapGenerator",
    "RepoMap",
    "FunctionSig",
    "ClassDef",
]
