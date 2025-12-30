"""
项目配置解析器 v5.0 - 借鉴 cursorrules

支持 .codefactory.yaml 项目级配置，提供:
- 项目信息配置
- SoT 文档配置
- 代码风格规则
- 禁止行为定义
- 自定义 Preprompts

基准文档: MASTER.md v4.6
版本: v5.0
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import yaml
import re


@dataclass
class TechStackConfig:
    """技术栈配置"""
    backend: str = "FastAPI + SQLAlchemy 2.x + Pydantic v2"
    frontend: str = "Next.js 16 + TanStack Query v5 + shadcn/ui"
    database: str = "PostgreSQL (via Supabase)"
    auth: str = "Supabase Auth"
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "backend": self.backend,
            "frontend": self.frontend,
            "database": self.database,
            "auth": self.auth,
        }


@dataclass
class CodeStyleConfig:
    """代码风格配置"""
    python_formatter: str = "ruff"
    python_type_checker: str = "mypy"
    typescript_strict: bool = True
    max_line_length: int = 88
    indent_size: int = 4
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "python": {
                "formatter": self.python_formatter,
                "type_checker": self.python_type_checker,
                "max_line_length": self.max_line_length,
                "indent_size": self.indent_size,
            },
            "typescript": {
                "strict": self.typescript_strict,
            },
        }


@dataclass
class ForbiddenPattern:
    """禁止模式"""
    pattern: str
    reason: str
    severity: str = "error"  # "error" | "warning"
    
    def matches(self, code: str) -> bool:
        """检查代码是否匹配此模式"""
        return bool(re.search(self.pattern, code))
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "pattern": self.pattern,
            "reason": self.reason,
            "severity": self.severity,
        }


@dataclass 
class PrepromptOverride:
    """Preprompt 覆盖配置"""
    system: Optional[str] = None
    clarify: Optional[str] = None
    generate: Optional[str] = None
    improve: Optional[str] = None
    review: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Optional[str]]:
        return {
            "system": self.system,
            "clarify": self.clarify,
            "generate": self.generate,
            "improve": self.improve,
            "review": self.review,
        }


@dataclass
class ProjectConfig:
    """项目配置 - .codefactory.yaml 的 Python 表示"""
    
    # 基本信息
    version: str = "1.0"
    name: str = "AI 代码工厂项目"
    description: str = ""
    
    # 技术栈
    tech_stack: TechStackConfig = field(default_factory=TechStackConfig)
    
    # SoT 文档
    sot_docs: List[str] = field(default_factory=lambda: [
        "docs/sot/MASTER.md",
        "docs/sot/STATE_MACHINE.md",
        "docs/sot/DATA_SCHEMA.md",
        "docs/sot/API_SOT.md",
        "docs/sot/ERROR_CODES_SOT.md",
    ])
    
    # 代码风格
    code_style: CodeStyleConfig = field(default_factory=CodeStyleConfig)
    
    # 禁止模式
    forbidden: List[ForbiddenPattern] = field(default_factory=lambda: [
        ForbiddenPattern(
            pattern=r"os\.system",
            reason="使用 subprocess 代替",
        ),
        ForbiddenPattern(
            pattern=r"\.balance\s*=",
            reason="通过 ledger 修改余额",
        ),
        ForbiddenPattern(
            pattern=r"class Config:",
            reason="使用 model_config = ConfigDict() (Pydantic v2)",
        ),
        ForbiddenPattern(
            pattern=r"\.dict\(\)",
            reason="使用 .model_dump() (Pydantic v2)",
        ),
    ])
    
    # Preprompt 覆盖
    preprompts: PrepromptOverride = field(default_factory=PrepromptOverride)
    
    # 搜索配置
    search_include_dirs: List[str] = field(default_factory=lambda: [
        "backend/",
        "frontend/src/",
    ])
    search_exclude_dirs: List[str] = field(default_factory=lambda: [
        "node_modules/",
        "__pycache__/",
        ".git/",
        "dist/",
        "build/",
    ])
    
    # 输出配置
    output_dir: str = ".agents/output"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "project": {
                "name": self.name,
                "description": self.description,
                "tech_stack": self.tech_stack.to_dict(),
            },
            "rules": {
                "sot_docs": self.sot_docs,
                "code_style": self.code_style.to_dict(),
                "forbidden": [f.to_dict() for f in self.forbidden],
            },
            "preprompts": self.preprompts.to_dict(),
            "search": {
                "include_dirs": self.search_include_dirs,
                "exclude_dirs": self.search_exclude_dirs,
            },
            "output": {
                "dir": self.output_dir,
            },
        }
    
    def check_forbidden(self, code: str) -> List[Dict[str, str]]:
        """检查代码是否包含禁止模式
        
        Args:
            code: 代码内容
            
        Returns:
            匹配的禁止模式列表
        """
        violations = []
        for pattern in self.forbidden:
            if pattern.matches(code):
                violations.append(pattern.to_dict())
        return violations


class ProjectConfigLoader:
    """
    项目配置加载器
    
    加载优先级:
    1. .codefactory.yaml (项目根目录)
    2. .claude/codefactory.yaml
    3. 默认配置
    
    使用方式:
    ```python
    loader = ProjectConfigLoader(project_dir=Path("./my_project"))
    config = loader.load()
    
    # 检查禁止模式
    violations = config.check_forbidden(code)
    if violations:
        for v in violations:
            print(f"违规: {v['pattern']} - {v['reason']}")
    ```
    """
    
    CONFIG_FILENAMES = [
        ".codefactory.yaml",
        ".codefactory.yml",
        ".claude/codefactory.yaml",
        ".claude/codefactory.yml",
    ]
    
    def __init__(self, project_dir: Path):
        """初始化
        
        Args:
            project_dir: 项目根目录
        """
        self.project_dir = Path(project_dir)
        self._config: Optional[ProjectConfig] = None
    
    def load(self, force_reload: bool = False) -> ProjectConfig:
        """加载配置
        
        Args:
            force_reload: 是否强制重新加载
            
        Returns:
            ProjectConfig 实例
        """
        if self._config and not force_reload:
            return self._config
        
        # 查找配置文件
        config_path = self._find_config_file()
        
        if config_path:
            # 从文件加载
            self._config = self._load_from_file(config_path)
        else:
            # 使用默认配置
            self._config = ProjectConfig()
        
        return self._config
    
    def _find_config_file(self) -> Optional[Path]:
        """查找配置文件"""
        for filename in self.CONFIG_FILENAMES:
            path = self.project_dir / filename
            if path.exists():
                return path
        return None
    
    def _load_from_file(self, path: Path) -> ProjectConfig:
        """从文件加载配置
        
        Args:
            path: 配置文件路径
            
        Returns:
            ProjectConfig 实例
        """
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        
        return self._parse_config(data)
    
    def _parse_config(self, data: Dict[str, Any]) -> ProjectConfig:
        """解析配置数据
        
        Args:
            data: YAML 数据
            
        Returns:
            ProjectConfig 实例
        """
        config = ProjectConfig()
        
        # 版本
        config.version = data.get("version", config.version)
        
        # 项目信息
        project = data.get("project", {})
        config.name = project.get("name", config.name)
        config.description = project.get("description", config.description)
        
        # 技术栈
        tech_stack = project.get("tech_stack", {})
        if tech_stack:
            config.tech_stack = TechStackConfig(
                backend=tech_stack.get("backend", config.tech_stack.backend),
                frontend=tech_stack.get("frontend", config.tech_stack.frontend),
                database=tech_stack.get("database", config.tech_stack.database),
                auth=tech_stack.get("auth", config.tech_stack.auth),
            )
        
        # 规则
        rules = data.get("rules", {})
        
        # SoT 文档
        if "sot_docs" in rules:
            config.sot_docs = rules["sot_docs"]
        
        # 代码风格
        code_style = rules.get("code_style", {})
        if code_style:
            python_style = code_style.get("python", {})
            ts_style = code_style.get("typescript", {})
            config.code_style = CodeStyleConfig(
                python_formatter=python_style.get("formatter", config.code_style.python_formatter),
                python_type_checker=python_style.get("type_checker", config.code_style.python_type_checker),
                max_line_length=python_style.get("max_line_length", config.code_style.max_line_length),
                indent_size=python_style.get("indent_size", config.code_style.indent_size),
                typescript_strict=ts_style.get("strict", config.code_style.typescript_strict),
            )
        
        # 禁止模式
        forbidden = rules.get("forbidden", [])
        if forbidden:
            config.forbidden = []
            for item in forbidden:
                if isinstance(item, dict):
                    config.forbidden.append(ForbiddenPattern(
                        pattern=item.get("pattern", ""),
                        reason=item.get("reason", ""),
                        severity=item.get("severity", "error"),
                    ))
        
        # Preprompts
        preprompts = data.get("preprompts", {})
        if preprompts:
            config.preprompts = PrepromptOverride(
                system=preprompts.get("system"),
                clarify=preprompts.get("clarify"),
                generate=preprompts.get("generate"),
                improve=preprompts.get("improve"),
                review=preprompts.get("review"),
            )
        
        # 搜索配置
        search = data.get("search", {})
        if "include_dirs" in search:
            config.search_include_dirs = search["include_dirs"]
        if "exclude_dirs" in search:
            config.search_exclude_dirs = search["exclude_dirs"]
        
        # 输出配置
        output = data.get("output", {})
        if "dir" in output:
            config.output_dir = output["dir"]
        
        return config
    
    def save(self, config: ProjectConfig, path: Optional[Path] = None) -> Path:
        """保存配置到文件
        
        Args:
            config: 配置实例
            path: 保存路径，默认为 .codefactory.yaml
            
        Returns:
            保存的文件路径
        """
        if path is None:
            path = self.project_dir / ".codefactory.yaml"
        
        # 转换为 YAML 友好的格式
        data = config.to_dict()
        
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        return path
    
    def create_default(self) -> Path:
        """创建默认配置文件
        
        Returns:
            创建的文件路径
        """
        return self.save(ProjectConfig())


# ============================================================
# 便捷函数
# ============================================================

def load_project_config(project_dir: Union[str, Path] = ".") -> ProjectConfig:
    """快速加载项目配置
    
    Args:
        project_dir: 项目根目录
        
    Returns:
        ProjectConfig 实例
    """
    loader = ProjectConfigLoader(Path(project_dir))
    return loader.load()


def check_code_violations(
    code: str, 
    project_dir: Union[str, Path] = ".",
) -> List[Dict[str, str]]:
    """检查代码是否违反项目规则
    
    Args:
        code: 代码内容
        project_dir: 项目根目录
        
    Returns:
        违规列表
    """
    config = load_project_config(project_dir)
    return config.check_forbidden(code)


def create_default_config(project_dir: Union[str, Path] = ".") -> Path:
    """创建默认配置文件
    
    Args:
        project_dir: 项目根目录
        
    Returns:
        创建的文件路径
    """
    loader = ProjectConfigLoader(Path(project_dir))
    return loader.create_default()


# ============================================================
# 示例配置文件内容
# ============================================================

EXAMPLE_CONFIG = """# AI 代码工厂配置文件
# 基于 cursorrules 设计理念

version: "1.0"

project:
  name: "AI 广告代投系统"
  description: "广告账户管理、日报审核、充值对账"
  tech_stack:
    backend: "FastAPI + SQLAlchemy 2.x + Pydantic v2"
    frontend: "Next.js 16 + TanStack Query v5 + shadcn/ui"
    database: "PostgreSQL (via Supabase)"
    auth: "Supabase Auth"

rules:
  sot_docs:
    - docs/sot/MASTER.md
    - docs/sot/STATE_MACHINE.md
    - docs/sot/DATA_SCHEMA.md
    - docs/sot/API_SOT.md
    - docs/sot/ERROR_CODES_SOT.md
  
  code_style:
    python:
      formatter: "ruff"
      type_checker: "mypy"
      max_line_length: 88
    typescript:
      strict: true
  
  forbidden:
    - pattern: "os\\.system"
      reason: "使用 subprocess 代替"
    - pattern: "\\.balance\\s*="
      reason: "通过 ledger 修改余额"
    - pattern: "class Config:"
      reason: "使用 model_config = ConfigDict() (Pydantic v2)"
    - pattern: "\\.dict\\(\\)"
      reason: "使用 .model_dump() (Pydantic v2)"

preprompts:
  system: |
    你是 AI 广告系统的编程助手。
    遵循 MASTER.md v4.6 的所有规范。
    处于 Phase 1 阶段，系统照亮而非问责。

search:
  include_dirs:
    - backend/
    - frontend/src/
  exclude_dirs:
    - node_modules/
    - __pycache__/
    - .git/

output:
  dir: .agents/output
"""


if __name__ == "__main__":
    print("=" * 60)
    print("项目配置加载器示例")
    print("=" * 60)
    
    # 显示示例配置
    print("\n示例配置文件 (.codefactory.yaml):")
    print("-" * 60)
    print(EXAMPLE_CONFIG)
    
    # 测试默认配置
    print("\n默认配置:")
    print("-" * 60)
    config = ProjectConfig()
    import json
    print(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))
    
    # 测试禁止模式检查
    print("\n禁止模式检查:")
    print("-" * 60)
    test_code = """
class MyModel(BaseModel):
    class Config:
        orm_mode = True
    
    def to_dict(self):
        return self.dict()
"""
    violations = config.check_forbidden(test_code)
    for v in violations:
        print(f"  ❌ {v['pattern']}: {v['reason']}")

