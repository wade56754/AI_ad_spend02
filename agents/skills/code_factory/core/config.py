"""
工厂配置

基准文档: MASTER.md v4.6
版本: v4.2
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class FactoryConfig:
    """代码工厂配置"""

    # ========== 路径配置 ==========
    project_dir: Path = field(default_factory=lambda: Path.cwd())
    sot_dir: Optional[Path] = None
    output_dir: Optional[Path] = None
    task_file: Optional[Path] = None
    code_library_dir: Optional[Path] = None

    # ========== 搜索配置 ==========
    search_sources: Dict[str, bool] = field(default_factory=lambda: {
        "local_project": True,
        "code_library": True,
        "github": False,
    })
    search_include_dirs: List[str] = field(default_factory=lambda: [
        "backend",
        "frontend/src",
    ])
    search_exclude_dirs: List[str] = field(default_factory=lambda: [
        "__pycache__",
        "node_modules",
        ".git",
        "venv",
        ".venv",
    ])

    # ========== 执行配置 ==========
    max_iterations: Optional[int] = None  # None = 无限制
    auto_continue: bool = True
    auto_fix_iterations: int = 3

    # ========== 安全配置 ==========
    enable_security: bool = True
    enable_sot_check: bool = True

    # ========== 输出配置 ==========
    output_mode: str = "files"  # files | diff | preview
    verbose: bool = False

    def __post_init__(self):
        """初始化后处理"""
        # 确保 Path 类型
        self.project_dir = Path(self.project_dir)

        # 设置默认路径
        if self.sot_dir is None:
            self.sot_dir = self.project_dir / "docs" / "sot"
        else:
            self.sot_dir = Path(self.sot_dir)

        if self.output_dir is None:
            self.output_dir = self.project_dir / ".agents" / "code_factory"
        else:
            self.output_dir = Path(self.output_dir)

        if self.task_file is None:
            self.task_file = self.output_dir / "task_list.json"
        else:
            self.task_file = Path(self.task_file)

        if self.code_library_dir is None:
            self.code_library_dir = self.project_dir / "code-library"
        else:
            self.code_library_dir = Path(self.code_library_dir)

    @classmethod
    def from_project(cls, project_dir: Path) -> "FactoryConfig":
        """从项目目录创建配置"""
        return cls(project_dir=project_dir)

    def ensure_dirs(self):
        """确保必要目录存在"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.task_file.parent.mkdir(parents=True, exist_ok=True)
