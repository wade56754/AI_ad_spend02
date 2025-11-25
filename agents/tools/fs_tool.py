"""
文件系统工具（如果不用 MCP fs）
"""

from pathlib import Path
from typing import Optional


class FSTool:
    """文件系统操作工具"""
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        初始化文件系统工具
        
        Args:
            base_path: 基础路径，默认为项目根目录
        """
        if base_path is None:
            # 假设项目根目录是 agents 的父目录
            self.base_path = Path(__file__).parent.parent.parent
        else:
            self.base_path = Path(base_path)
    
    def read_file(self, file_path: str) -> str:
        """
        读取文件内容
        
        Args:
            file_path: 相对路径或绝对路径
            
        Returns:
            文件内容
        """
        path = self.base_path / file_path if not Path(file_path).is_absolute() else Path(file_path)
        return path.read_text(encoding='utf-8')
    
    def write_file(self, file_path: str, content: str) -> None:
        """
        写入文件内容
        
        Args:
            file_path: 相对路径或绝对路径
            content: 文件内容
        """
        path = self.base_path / file_path if not Path(file_path).is_absolute() else Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
    
    def file_exists(self, file_path: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_path: 相对路径或绝对路径
            
        Returns:
            文件是否存在
        """
        path = self.base_path / file_path if not Path(file_path).is_absolute() else Path(file_path)
        return path.exists()
    
    def list_dir(self, dir_path: str = '.') -> list[str]:
        """
        列出目录内容
        
        Args:
            dir_path: 相对路径或绝对路径
            
        Returns:
            文件/目录名列表
        """
        path = self.base_path / dir_path if not Path(dir_path).is_absolute() else Path(dir_path)
        if not path.exists():
            return []
        return [item.name for item in path.iterdir()]

