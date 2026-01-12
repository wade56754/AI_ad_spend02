"""
路径工具函数

P1-1 fix: 统一路径计算方式，避免脆弱的 parent.parent.parent 链

版本: v1.0
"""

import os
from pathlib import Path
from typing import Optional


def get_project_root(start_path: Optional[Path] = None) -> Path:
    """
    获取项目根目录
    
    通过查找 .git 目录或项目标识文件来确定项目根目录
    
    Args:
        start_path: 起始路径，默认为当前文件所在目录
        
    Returns:
        项目根目录路径
        
    Raises:
        ValueError: 如果无法找到项目根目录
    """
    if start_path is None:
        # 默认从调用此函数的文件所在目录开始
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            caller_file = frame.f_back.f_code.co_filename
            start_path = Path(caller_file).parent
        else:
            start_path = Path.cwd()
    
    start_path = Path(start_path).resolve()
    current = start_path
    
    # 查找项目标识文件/目录
    project_markers = [
        '.git',
        '.claude',
        'pyproject.toml',
        'setup.py',
        'requirements.txt',
        'package.json',  # 前端项目
    ]
    
    # 向上查找，最多查找 10 层
    max_depth = 10
    depth = 0
    
    while depth < max_depth:
        # 检查是否有项目标识
        for marker in project_markers:
            marker_path = current / marker
            if marker_path.exists():
                return current
        
        # 检查是否到达文件系统根目录
        parent = current.parent
        if parent == current:
            break
        
        current = parent
        depth += 1
    
    # 如果找不到，尝试使用环境变量
    project_root_env = os.getenv('PROJECT_ROOT')
    if project_root_env:
        return Path(project_root_env).resolve()
    
    # 最后尝试：从当前工作目录向上查找
    cwd = Path.cwd()
    for marker in project_markers:
        marker_path = cwd / marker
        if marker_path.exists():
            return cwd
    
    # 如果都找不到，返回起始路径的父目录（向后兼容）
    return start_path.parent if start_path != Path('/') else start_path


def get_wshobson_agents_path(project_root: Optional[Path] = None) -> Path:
    """
    获取 wshobson/agents 仓库路径
    
    Args:
        project_root: 项目根目录，如果为 None 则自动查找
        
    Returns:
        wshobson/agents 仓库路径
    """
    if project_root is None:
        project_root = get_project_root()
    
    wshobson_path = project_root / "external" / "wshobson-agents"
    return wshobson_path

