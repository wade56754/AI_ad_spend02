"""
配置模块 v5.0

包含:
- ProjectConfig: 项目级配置 (.codefactory.yaml)
- ProjectConfigLoader: 配置加载器

基准文档: MASTER.md v4.6
版本: v5.0
"""

from .project_config import (
    ProjectConfig,
    ProjectConfigLoader,
    TechStackConfig,
    CodeStyleConfig,
    ForbiddenPattern,
    PrepromptOverride,
    load_project_config,
    check_code_violations,
    create_default_config,
    EXAMPLE_CONFIG,
)

__all__ = [
    # 配置类
    "ProjectConfig",
    "ProjectConfigLoader",
    "TechStackConfig",
    "CodeStyleConfig",
    "ForbiddenPattern",
    "PrepromptOverride",
    
    # 便捷函数
    "load_project_config",
    "check_code_violations",
    "create_default_config",
    
    # 示例
    "EXAMPLE_CONFIG",
]






