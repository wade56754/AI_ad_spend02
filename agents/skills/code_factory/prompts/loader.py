"""
提示词模板加载器 v5.0

功能:
- 从内置 templates/ 加载默认模板
- 支持 .claude/prompts/ 项目级覆盖
- 动态注入 SoT 版本

基准文档: MASTER.md v4.6
版本: v5.0
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, List, TYPE_CHECKING
import re

if TYPE_CHECKING:
    from ..sot.loader import SotLoader


@dataclass
class LoadedTemplate:
    """已加载的模板"""
    name: str
    content: str
    source: str  # "builtin" | "project"
    path: Path


class PromptLoader:
    """提示词模板加载器
    
    加载优先级:
    1. 项目级覆盖: .claude/prompts/{name}.md
    2. 内置模板: prompts/templates/{name}.md
    
    支持动态 SoT 版本注入:
    - ${MASTER_VERSION} → v4.6
    - ${STATE_MACHINE_VERSION} → v2.8
    """
    
    def __init__(
        self, 
        project_dir: Path, 
        sot_loader: Optional["SotLoader"] = None
    ):
        """初始化加载器
        
        Args:
            project_dir: 项目根目录
            sot_loader: SoT 加载器 (用于动态版本注入)
        """
        self.builtin_dir = Path(__file__).parent / "templates"
        self.project_dir = Path(project_dir) / ".claude" / "prompts"
        self.sot_loader = sot_loader
        
        # 缓存
        self._cache: Dict[str, LoadedTemplate] = {}
    
    def load(self, name: str, use_cache: bool = True) -> str:
        """加载模板
        
        Args:
            name: 模板名称 (不含 .md 后缀)
                  支持子目录: "task/refactor"
            use_cache: 是否使用缓存
            
        Returns:
            模板内容 (已注入 SoT 版本)
        """
        # 检查缓存
        if use_cache and name in self._cache:
            return self._cache[name].content
        
        # 加载模板
        template = self._load_template(name)
        if template is None:
            return ""
        
        # 注入 SoT 版本
        template.content = self._inject_sot_versions(template.content)
        
        # 缓存
        if use_cache:
            self._cache[name] = template
        
        return template.content
    
    def _load_template(self, name: str) -> Optional[LoadedTemplate]:
        """加载模板文件
        
        优先级: 项目级 > 内置
        """
        # 1. 尝试项目级覆盖
        project_path = self.project_dir / f"{name}.md"
        if project_path.exists():
            content = project_path.read_text(encoding="utf-8")
            return LoadedTemplate(
                name=name,
                content=content,
                source="project",
                path=project_path
            )
        
        # 2. 回退到内置模板
        builtin_path = self.builtin_dir / f"{name}.md"
        if builtin_path.exists():
            content = builtin_path.read_text(encoding="utf-8")
            return LoadedTemplate(
                name=name,
                content=content,
                source="builtin",
                path=builtin_path
            )
        
        return None
    
    def _inject_sot_versions(self, content: str) -> str:
        """注入 SoT 版本到模板
        
        替换占位符:
        - ${MASTER_VERSION} → v4.6
        - ${STATE_MACHINE_VERSION} → v2.8
        """
        if not self.sot_loader:
            # 无 SoT 加载器，使用默认版本
            return self._inject_default_versions(content)
        
        try:
            # 从 SoT 加载器获取版本
            sot_data = self.sot_loader.load()
            versions = sot_data.versions
            
            for doc, version in versions.items():
                # 文件名 -> 占位符名称
                # "MASTER.md" -> "MASTER"
                doc_key = doc.replace(".md", "").upper()
                placeholder = f"${{{doc_key}_VERSION}}"
                content = content.replace(placeholder, version)
            
            return content
        except Exception:
            # 加载失败，使用默认版本
            return self._inject_default_versions(content)
    
    def _inject_default_versions(self, content: str) -> str:
        """注入默认 SoT 版本 (回退方案)"""
        default_versions = {
            "MASTER": "v4.6",
            "STATE_MACHINE": "v2.8",
            "DATA_SCHEMA": "v5.6",
            "BUSINESS_RULES": "v4.7",
            "API_SOT": "v9.4",
            "ERROR_CODES": "v2.2",
            "AUTH_SPEC": "v2.1",
        }
        
        for doc_key, version in default_versions.items():
            placeholder = f"${{{doc_key}_VERSION}}"
            content = content.replace(placeholder, version)
        
        return content
    
    def list_templates(self, include_project: bool = True) -> List[str]:
        """列出所有可用模板
        
        Args:
            include_project: 是否包含项目级模板
            
        Returns:
            模板名称列表
        """
        templates = set()
        
        # 内置模板
        if self.builtin_dir.exists():
            for path in self.builtin_dir.rglob("*.md"):
                rel_path = path.relative_to(self.builtin_dir)
                name = str(rel_path).replace(".md", "").replace("\\", "/")
                templates.add(name)
        
        # 项目级模板
        if include_project and self.project_dir.exists():
            for path in self.project_dir.rglob("*.md"):
                rel_path = path.relative_to(self.project_dir)
                name = str(rel_path).replace(".md", "").replace("\\", "/")
                templates.add(name)
        
        return sorted(templates)
    
    def get_template_info(self, name: str) -> Optional[Dict]:
        """获取模板信息
        
        Args:
            name: 模板名称
            
        Returns:
            模板信息字典
        """
        template = self._load_template(name)
        if template is None:
            return None
        
        return {
            "name": template.name,
            "source": template.source,
            "path": str(template.path),
            "size": len(template.content),
        }
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
    
    def reload(self, name: str) -> str:
        """重新加载模板 (忽略缓存)"""
        if name in self._cache:
            del self._cache[name]
        return self.load(name, use_cache=True)

