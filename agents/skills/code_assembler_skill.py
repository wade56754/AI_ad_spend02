"""
code_assembler_skill.py - 代码组装 Skill

代码来源说明 (Code Sources):
================================================================================
本 Skill 的设计和实现借鉴了以下开源项目：

1. Aider (Apache-2.0 License)
   - GitHub: https://github.com/paul-gauthier/aider
   - Stars: 22k+
   - 借鉴内容:
     - Repo Map 项目结构概览技术
     - 多文件协同编辑模式
     - Diff 格式输出
     - 上下文管理策略

2. Continue (Apache-2.0 License)
   - GitHub: https://github.com/continuedev/continue
   - Stars: 20k+
   - 借鉴内容:
     - Context Provider 系统设计
     - 工具调用机制

3. Copier (MIT License)
   - GitHub: https://github.com/copier-org/copier
   - Stars: 2k+
   - 借鉴内容:
     - 模板渲染系统
     - YAML 配置驱动生成
================================================================================

职责: 将适配后的代码组装成完整的功能模块
核心能力: 多文件组装 + 依赖管理 + 模板驱动

基准对齐:
- CODE_FACTORY_REFERENCE_PROJECTS.md v1.0
- Agent Layer Freeze v1.0
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import re

from .code_adapter_skill import AdaptedFile

logger = logging.getLogger(__name__)


# ============================================================================
# 数据类型定义
# ============================================================================

@dataclass
class AssembledFile:
    """
    组装后的文件

    借鉴: Aider 的多文件编辑输出格式
    """
    path: str
    content: str
    action: str  # "create" | "modify"
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "content": self.content,
            "action": self.action,
            "dependencies": self.dependencies,
        }


@dataclass
class RepoMap:
    """
    项目结构图

    借鉴: Aider 的 Repo Map 技术
    """
    affected_files: List[str] = field(default_factory=list)
    new_files: List[str] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, List[str]]:
        return {
            "affected_files": self.affected_files,
            "new_files": self.new_files,
            "modified_files": self.modified_files,
        }


@dataclass
class IntegrationGuide:
    """集成指南"""
    steps: List[str] = field(default_factory=list)
    imports_to_add: List[str] = field(default_factory=list)
    config_changes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, List[str]]:
        return {
            "steps": self.steps,
            "imports_to_add": self.imports_to_add,
            "config_changes": self.config_changes,
        }


@dataclass
class AssembledModule:
    """组装后的模块"""
    name: str
    files: List[AssembledFile] = field(default_factory=list)
    entry_points: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "files": [f.to_dict() for f in self.files],
            "entry_points": self.entry_points,
        }


# ============================================================================
# 模板定义 (借鉴 Copier 的模板系统)
# ============================================================================

BACKEND_SERVICE_TEMPLATE = '''"""
{feature_name} Service
[ASSEMBLED] 由 ai-ad-code-assembler 组装生成
[SOURCE] 基于参考代码适配组装

代码来源: 借鉴 Aider 的多文件协同编辑模式
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.response import StandardResponse


class {class_name}Service:
    """
    {feature_description}
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute(self, **kwargs) -> StandardResponse:
        """
        执行 {feature_name} 操作

        [ADAPTED] 此方法由适配代码填充
        """
        # TODO: 实现业务逻辑
        {adapted_logic}
        return StandardResponse(data={{}}, message="操作成功")
'''

BACKEND_ROUTER_TEMPLATE = '''"""
{feature_name} Router
[ASSEMBLED] 由 ai-ad-code-assembler 组装生成
[SOURCE] 基于参考代码适配组装

代码来源: 借鉴 Aider 的多文件协同编辑模式
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.deps import get_db
from backend.services.{feature_snake}_service import {class_name}Service
from backend.core.response import StandardResponse

router = APIRouter(prefix="/{feature_snake}", tags=["{feature_name}"])


@router.post("/", response_model=StandardResponse)
async def {feature_snake}_endpoint(
    db: AsyncSession = Depends(get_db),
):
    """
    {feature_description}
    """
    service = {class_name}Service(db)
    return await service.execute()
'''

FRONTEND_COMPONENT_TEMPLATE = '''/**
 * {feature_name} Component
 * [ASSEMBLED] 由 ai-ad-code-assembler 组装生成
 * [SOURCE] 基于参考代码适配组装
 *
 * 代码来源: 借鉴 Aider 的多文件协同编辑模式
 */
import React from 'react';

interface {class_name}Props {{
  // TODO: 定义 props
}}

export function {class_name}({{ }}: {class_name}Props) {{
  return (
    <div className="{feature_kebab}">
      {{/* [ADAPTED] 组件内容由适配代码填充 */}}
      <h2>{feature_name}</h2>
      {adapted_jsx}
    </div>
  );
}}

export default {class_name};
'''


# ============================================================================
# CodeAssemblerSkill 主类
# ============================================================================

class CodeAssemblerSkill:
    """
    代码组装 Skill

    架构设计借鉴:
    - Aider: Repo Map + 多文件编辑
    - Copier: 模板渲染系统
    - Continue: Context Provider 设计
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        初始化组装器

        Args:
            base_path: 项目根目录
        """
        self.base_path = base_path or self._detect_project_root()

        logger.info(f"CodeAssemblerSkill initialized: base_path={self.base_path}")

    def assemble(
        self,
        adapted_files: List[AdaptedFile],
        requirement: str,
        scope: str = "fullstack",
        include_tests: bool = True,
        include_types: bool = True,
        output_format: str = "files",
    ) -> Dict[str, Any]:
        """
        组装代码模块

        Args:
            adapted_files: 适配后的文件列表
            requirement: 原始需求描述
            scope: 组装范围 ("backend" | "frontend" | "fullstack")
            include_tests: 是否生成测试
            include_types: 是否生成类型文件
            output_format: 输出格式 ("files" | "diff")

        Returns:
            组装结果
        """
        logger.info(
            f"Assembly started: {len(adapted_files)} files, "
            f"scope={scope}, requirement='{requirement[:50]}...'"
        )

        try:
            # 1. 提取特性信息
            feature_info = self._extract_feature_info(requirement)

            # 2. 生成 Repo Map (借鉴 Aider)
            repo_map = self._generate_repo_map(adapted_files, feature_info)

            # 3. 组装文件
            assembled_files: List[AssembledFile] = []

            # 处理已适配的文件
            for adapted in adapted_files:
                assembled = AssembledFile(
                    path=adapted.file_path,
                    content=adapted.content,
                    action="create",
                    dependencies=[],
                )
                assembled_files.append(assembled)

            # 根据 scope 生成补充文件
            if scope in ["backend", "fullstack"]:
                backend_files = self._generate_backend_files(
                    feature_info, adapted_files, include_tests
                )
                assembled_files.extend(backend_files)

            if scope in ["frontend", "fullstack"]:
                frontend_files = self._generate_frontend_files(
                    feature_info, adapted_files, include_types
                )
                assembled_files.extend(frontend_files)

            # 4. 去重和整理
            assembled_files = self._deduplicate_files(assembled_files)

            # 5. 生成集成指南
            integration_guide = self._generate_integration_guide(
                feature_info, assembled_files
            )

            # 6. 构建模块
            module = AssembledModule(
                name=feature_info["name"],
                files=assembled_files,
                entry_points={
                    "backend_router": f"backend/routers/{feature_info['snake']}_router.py",
                    "frontend_page": f"frontend/app/{feature_info['kebab']}/page.tsx",
                },
            )

            logger.info(
                f"Assembly completed: {len(assembled_files)} files, "
                f"module={module.name}"
            )

            return {
                "success": True,
                "data": {
                    "assembled_module": module.to_dict(),
                    "repo_map": repo_map.to_dict(),
                    "integration_guide": integration_guide.to_dict(),
                },
                "error": None,
            }

        except Exception as e:
            logger.error(f"Assembly failed: {e}", exc_info=True)
            return {
                "success": False,
                "data": None,
                "error": str(e),
            }

    # ========================================================================
    # 特性信息提取
    # ========================================================================

    def _extract_feature_info(self, requirement: str) -> Dict[str, str]:
        """从需求中提取特性信息"""
        # 简单提取，生产环境应使用 NLP
        requirement_lower = requirement.lower()

        # 尝试提取关键词
        keywords = ["导出", "export", "导入", "import", "上传", "upload"]
        feature_name = "NewFeature"

        for kw in keywords:
            if kw in requirement_lower:
                if kw in ["导出", "export"]:
                    feature_name = "Export"
                elif kw in ["导入", "import"]:
                    feature_name = "Import"
                elif kw in ["上传", "upload"]:
                    feature_name = "Upload"
                break

        return {
            "name": feature_name,
            "snake": self._to_snake_case(feature_name),
            "kebab": self._to_kebab_case(feature_name),
            "pascal": feature_name,
            "description": requirement[:100],
        }

    def _to_snake_case(self, name: str) -> str:
        """转换为 snake_case"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _to_kebab_case(self, name: str) -> str:
        """转换为 kebab-case"""
        return self._to_snake_case(name).replace('_', '-')

    # ========================================================================
    # Repo Map 生成 (借鉴 Aider)
    # ========================================================================

    def _generate_repo_map(
        self,
        adapted_files: List[AdaptedFile],
        feature_info: Dict[str, str],
    ) -> RepoMap:
        """
        生成项目结构图

        借鉴: Aider 的 Repo Map 技术
        """
        new_files = []
        modified_files = []

        for adapted in adapted_files:
            file_path = Path(self.base_path) / adapted.file_path

            if file_path.exists():
                modified_files.append(adapted.file_path)
            else:
                new_files.append(adapted.file_path)

        # 添加将要生成的文件
        snake = feature_info["snake"]
        kebab = feature_info["kebab"]

        potential_new_files = [
            f"backend/services/{snake}_service.py",
            f"backend/routers/{snake}_router.py",
            f"frontend/components/{feature_info['pascal']}/index.tsx",
            f"frontend/app/{kebab}/page.tsx",
        ]

        for pf in potential_new_files:
            if pf not in new_files:
                new_files.append(pf)

        return RepoMap(
            affected_files=new_files + modified_files,
            new_files=new_files,
            modified_files=modified_files,
        )

    # ========================================================================
    # 后端文件生成
    # ========================================================================

    def _generate_backend_files(
        self,
        feature_info: Dict[str, str],
        adapted_files: List[AdaptedFile],
        include_tests: bool,
    ) -> List[AssembledFile]:
        """生成后端补充文件"""
        files = []

        # 提取适配代码中的逻辑
        adapted_logic = self._extract_adapted_logic(adapted_files)

        # 服务文件
        service_content = BACKEND_SERVICE_TEMPLATE.format(
            feature_name=feature_info["name"],
            class_name=feature_info["pascal"],
            feature_description=feature_info["description"],
            adapted_logic=adapted_logic or "pass",
        )

        files.append(AssembledFile(
            path=f"backend/services/{feature_info['snake']}_service.py",
            content=service_content,
            action="create",
            dependencies=[],
        ))

        # 路由文件
        router_content = BACKEND_ROUTER_TEMPLATE.format(
            feature_name=feature_info["name"],
            feature_snake=feature_info["snake"],
            class_name=feature_info["pascal"],
            feature_description=feature_info["description"],
        )

        files.append(AssembledFile(
            path=f"backend/routers/{feature_info['snake']}_router.py",
            content=router_content,
            action="create",
            dependencies=[f"backend/services/{feature_info['snake']}_service.py"],
        ))

        # 测试文件
        if include_tests:
            test_content = self._generate_test_file(feature_info)
            files.append(AssembledFile(
                path=f"tests/test_{feature_info['snake']}.py",
                content=test_content,
                action="create",
                dependencies=[
                    f"backend/services/{feature_info['snake']}_service.py",
                    f"backend/routers/{feature_info['snake']}_router.py",
                ],
            ))

        return files

    # ========================================================================
    # 前端文件生成
    # ========================================================================

    def _generate_frontend_files(
        self,
        feature_info: Dict[str, str],
        adapted_files: List[AdaptedFile],
        include_types: bool,
    ) -> List[AssembledFile]:
        """生成前端补充文件"""
        files = []

        # 提取适配的 JSX
        adapted_jsx = self._extract_adapted_jsx(adapted_files)

        # 组件文件
        component_content = FRONTEND_COMPONENT_TEMPLATE.format(
            feature_name=feature_info["name"],
            class_name=feature_info["pascal"],
            feature_kebab=feature_info["kebab"],
            adapted_jsx=adapted_jsx or "<p>功能开发中...</p>",
        )

        files.append(AssembledFile(
            path=f"frontend/components/{feature_info['pascal']}/index.tsx",
            content=component_content,
            action="create",
            dependencies=[],
        ))

        # 类型文件
        if include_types:
            types_content = self._generate_types_file(feature_info)
            files.append(AssembledFile(
                path=f"frontend/types/{feature_info['snake']}.ts",
                content=types_content,
                action="create",
                dependencies=[],
            ))

        return files

    # ========================================================================
    # 辅助方法
    # ========================================================================

    def _extract_adapted_logic(self, adapted_files: List[AdaptedFile]) -> str:
        """从适配文件中提取业务逻辑"""
        for adapted in adapted_files:
            if ".py" in adapted.file_path:
                # 尝试提取函数体
                match = re.search(
                    r'async def \w+\([^)]*\):[^\n]*\n((?:\s+.*\n?)+)',
                    adapted.content
                )
                if match:
                    return match.group(1).strip()

        return "pass  # TODO: 实现业务逻辑"

    def _extract_adapted_jsx(self, adapted_files: List[AdaptedFile]) -> str:
        """从适配文件中提取 JSX"""
        for adapted in adapted_files:
            if ".tsx" in adapted.file_path or ".jsx" in adapted.file_path:
                # 尝试提取 return 语句中的 JSX
                match = re.search(
                    r'return\s*\(\s*([\s\S]*?)\s*\)\s*;',
                    adapted.content
                )
                if match:
                    return match.group(1).strip()

        return "<p>功能开发中...</p>"

    def _generate_test_file(self, feature_info: Dict[str, str]) -> str:
        """生成测试文件"""
        return f'''"""
Tests for {feature_info["name"]}
[ASSEMBLED] 由 ai-ad-code-assembler 组装生成
"""
import pytest
from httpx import AsyncClient

from backend.main import app


@pytest.mark.asyncio
async def test_{feature_info["snake"]}_endpoint():
    """测试 {feature_info["name"]} API"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/{feature_info["snake"]}/")
        assert response.status_code in [200, 201]
'''

    def _generate_types_file(self, feature_info: Dict[str, str]) -> str:
        """生成 TypeScript 类型文件"""
        return f'''/**
 * Types for {feature_info["name"]}
 * [ASSEMBLED] 由 ai-ad-code-assembler 组装生成
 */

export interface {feature_info["pascal"]}Request {{
  // TODO: 定义请求类型
}}

export interface {feature_info["pascal"]}Response {{
  success: boolean;
  data: unknown;
  message: string;
}}
'''

    def _generate_integration_guide(
        self,
        feature_info: Dict[str, str],
        files: List[AssembledFile],
    ) -> IntegrationGuide:
        """生成集成指南"""
        return IntegrationGuide(
            steps=[
                f"1. 将生成的文件复制到项目对应目录",
                f"2. 在 backend/routers/__init__.py 中注册路由",
                f"3. 在 frontend/app 目录中配置页面路由",
                f"4. 运行测试确保功能正常",
            ],
            imports_to_add=[
                f"from backend.routers.{feature_info['snake']}_router import router as {feature_info['snake']}_router",
            ],
            config_changes=[
                f"在 main.py 中添加: app.include_router({feature_info['snake']}_router)",
            ],
        )

    def _deduplicate_files(
        self,
        files: List[AssembledFile],
    ) -> List[AssembledFile]:
        """去重文件列表"""
        seen = set()
        result = []

        for f in files:
            if f.path not in seen:
                seen.add(f.path)
                result.append(f)

        return result

    def _detect_project_root(self) -> Path:
        """自动检测项目根目录"""
        current = Path(__file__).resolve()

        for parent in current.parents:
            if (parent / "CLAUDE.md").exists() or (parent / ".claude").exists():
                return parent

        return Path("D:/project/AI_ad_spend02")


# ============================================================================
# Skill 入口函数
# ============================================================================

def code_assembler_skill(
    adapted_files: List[Dict[str, Any]],
    requirement: str,
    scope: str = "fullstack",
    include_tests: bool = True,
    include_types: bool = True,
) -> Dict[str, Any]:
    """
    代码组装 Skill 入口函数

    代码来源: 借鉴 Aider + Copier 的多文件组装和模板系统

    Args:
        adapted_files: 适配后的文件列表 (字典格式)
        requirement: 原始需求描述
        scope: 组装范围
        include_tests: 是否生成测试
        include_types: 是否生成类型文件

    Returns:
        组装结果
    """
    # 转换为 AdaptedFile 对象
    files = [
        AdaptedFile(
            file_path=f.get("file_path", ""),
            content=f.get("content", ""),
            adaptations=[],
            source_attribution=None,
        )
        for f in adapted_files
    ]

    assembler = CodeAssemblerSkill()
    return assembler.assemble(
        adapted_files=files,
        requirement=requirement,
        scope=scope,
        include_tests=include_tests,
        include_types=include_types,
    )


__all__ = [
    "CodeAssemblerSkill",
    "AssembledFile",
    "AssembledModule",
    "code_assembler_skill",
]
