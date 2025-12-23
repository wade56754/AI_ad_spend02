"""
代码组装器 - ASSEMBLE 阶段实现

职责: 将适配后的代码组装成完整的功能模块

组装模式:
1. 后端模块: Schema → Service → Router → Test
2. 前端模块: Types → API → Hooks → Components → Page
3. 全栈模块: Backend + Frontend

来源:
- Aider: Repo Map 技术
- Copier: 模板系统
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .adapter import AdaptedFile


@dataclass
class AssembledFile:
    """组装后的文件"""
    path: str
    content: str
    action: str  # create | modify
    dependencies: List[str] = field(default_factory=list)
    source_refs: List[str] = field(default_factory=list)


@dataclass
class RepoMap:
    """项目结构图 (借鉴 Aider)"""
    affected_files: List[str] = field(default_factory=list)
    new_files: List[str] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)


@dataclass
class IntegrationGuide:
    """集成指南"""
    steps: List[str] = field(default_factory=list)
    imports_to_add: List[str] = field(default_factory=list)
    config_changes: List[str] = field(default_factory=list)


@dataclass
class AssembledModule:
    """组装后的模块"""
    name: str
    files: List[AssembledFile] = field(default_factory=list)
    entry_points: Dict[str, str] = field(default_factory=dict)


@dataclass
class AssembleResult:
    """组装结果"""
    success: bool
    module: AssembledModule = None
    repo_map: RepoMap = None
    integration_guide: IntegrationGuide = None
    error: str = None


# ============================================================
# 代码模板
# ============================================================

BACKEND_SCHEMA_TEMPLATE = '''"""
{feature_name} Schema
[ASSEMBLED] 由 ai-ad-code-assembler 组装生成
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class {ClassName}Base(BaseModel):
    """基础模型"""
    model_config = ConfigDict(from_attributes=True)

    {fields}


class {ClassName}Create({ClassName}Base):
    """创建模型"""
    pass


class {ClassName}Update(BaseModel):
    """更新模型"""
    {update_fields}


class {ClassName}Response({ClassName}Base):
    """响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
'''

BACKEND_SERVICE_TEMPLATE = '''"""
{feature_name} Service
[ASSEMBLED] 由 ai-ad-code-assembler 组装生成
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.{model_file} import {ModelName}
from backend.schemas.{schema_file} import {ClassName}Create, {ClassName}Update
from backend.core.response import success_response
from backend.core.error_codes import BusinessError, ErrorCodes


class {ClassName}Service:
    """{feature_description}"""

    def __init__(self, db: Session):
        self.db = db

    def get_list(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[{ModelName}]:
        """获取列表"""
        stmt = select({ModelName}).offset(skip).limit(limit)
        result = self.db.execute(stmt)
        return result.scalars().all()

    def get_by_id(self, id: int) -> Optional[{ModelName}]:
        """根据 ID 获取"""
        stmt = select({ModelName}).where({ModelName}.id == id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def create(self, data: {ClassName}Create) -> {ModelName}:
        """创建"""
        db_obj = {ModelName}(**data.model_dump())
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, id: int, data: {ClassName}Update) -> Optional[{ModelName}]:
        """更新"""
        db_obj = self.get_by_id(id)
        if not db_obj:
            raise BusinessError(code=ErrorCodes.NOT_FOUND, message="记录不存在")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: int) -> bool:
        """删除"""
        db_obj = self.get_by_id(id)
        if not db_obj:
            raise BusinessError(code=ErrorCodes.NOT_FOUND, message="记录不存在")

        self.db.delete(db_obj)
        self.db.commit()
        return True
'''

BACKEND_ROUTER_TEMPLATE = '''"""
{feature_name} Router
[ASSEMBLED] 由 ai-ad-code-assembler 组装生成
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.deps import get_db
from backend.core.response import success_response
from backend.services.{service_file} import {ClassName}Service
from backend.schemas.{schema_file} import (
    {ClassName}Create,
    {ClassName}Update,
    {ClassName}Response,
)

router = APIRouter(prefix="/{feature_route}", tags=["{feature_name}"])


@router.get("/", response_model=List[{ClassName}Response])
def list_{feature_snake}(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """获取列表"""
    service = {ClassName}Service(db)
    items = service.get_list(skip=skip, limit=limit)
    return success_response(data=items)


@router.get("/{{id}}", response_model={ClassName}Response)
def get_{feature_snake}(
    id: int,
    db: Session = Depends(get_db),
):
    """获取详情"""
    service = {ClassName}Service(db)
    item = service.get_by_id(id)
    if not item:
        raise BusinessError(code=ErrorCodes.NOT_FOUND, message="记录不存在")
    return success_response(data=item)


@router.post("/", response_model={ClassName}Response)
def create_{feature_snake}(
    data: {ClassName}Create,
    db: Session = Depends(get_db),
):
    """创建"""
    service = {ClassName}Service(db)
    item = service.create(data)
    return success_response(data=item, message="创建成功")


@router.put("/{{id}}", response_model={ClassName}Response)
def update_{feature_snake}(
    id: int,
    data: {ClassName}Update,
    db: Session = Depends(get_db),
):
    """更新"""
    service = {ClassName}Service(db)
    item = service.update(id, data)
    return success_response(data=item, message="更新成功")


@router.delete("/{{id}}")
def delete_{feature_snake}(
    id: int,
    db: Session = Depends(get_db),
):
    """删除"""
    service = {ClassName}Service(db)
    service.delete(id)
    return success_response(message="删除成功")
'''

BACKEND_TEST_TEMPLATE = '''"""
{feature_name} Tests
[ASSEMBLED] 由 ai-ad-code-assembler 组装生成
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


class Test{ClassName}:
    """测试 {feature_name}"""

    def test_list_{feature_snake}(self):
        """测试获取列表"""
        response = client.get("/{feature_route}/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_create_{feature_snake}(self):
        """测试创建"""
        payload = {create_payload}
        response = client.post("/{feature_route}/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_{feature_snake}(self):
        """测试获取详情"""
        response = client.get("/{feature_route}/1")
        # 可能返回 200 或 404
        assert response.status_code in [200, 404]

    def test_update_{feature_snake}(self):
        """测试更新"""
        payload = {update_payload}
        response = client.put("/{feature_route}/1", json=payload)
        # 可能返回 200 或 404
        assert response.status_code in [200, 404]

    def test_delete_{feature_snake}(self):
        """测试删除"""
        response = client.delete("/{feature_route}/1")
        # 可能返回 200 或 404
        assert response.status_code in [200, 404]
'''


class CodeAssembler:
    """
    代码组装器

    组装流程:
    1. 分析适配后的代码
    2. 生成缺失的模块文件
    3. 建立文件依赖关系
    4. 生成 Repo Map
    5. 生成集成指南
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)

    def assemble(
        self,
        adapted_files: List[AdaptedFile],
        requirement: str,
        scope: str = "fullstack",
        include_tests: bool = True,
    ) -> AssembleResult:
        """
        执行组装

        Args:
            adapted_files: 适配后的文件列表
            requirement: 原始需求
            scope: 组装范围 (backend | frontend | fullstack)
            include_tests: 是否生成测试

        Returns:
            AssembleResult
        """
        # 提取特性信息
        feature_info = self._extract_feature_info(requirement, adapted_files)

        # 组装文件列表
        assembled_files = []

        # 添加适配后的文件
        for af in adapted_files:
            assembled_files.append(AssembledFile(
                path=af.file_path,
                content=af.content,
                action="create",
                source_refs=[af.source_attribution.reference] if af.source_attribution else [],
            ))

        # 后端组装
        if scope in ["backend", "fullstack"]:
            backend_files = self._assemble_backend(feature_info, adapted_files, include_tests)
            assembled_files.extend(backend_files)

        # 前端组装 (TODO)
        if scope in ["frontend", "fullstack"]:
            # frontend_files = self._assemble_frontend(feature_info, adapted_files)
            # assembled_files.extend(frontend_files)
            pass

        # 去重
        seen_paths = set()
        unique_files = []
        for f in assembled_files:
            if f.path not in seen_paths:
                seen_paths.add(f.path)
                unique_files.append(f)

        # 建立依赖关系
        self._establish_dependencies(unique_files)

        # 生成 Repo Map
        repo_map = self._generate_repo_map(unique_files)

        # 生成集成指南
        integration_guide = self._generate_integration_guide(unique_files, feature_info)

        # 构建模块
        module = AssembledModule(
            name=feature_info["feature_name"],
            files=unique_files,
            entry_points={
                "backend_router": f"backend/routers/{feature_info['feature_snake']}_router.py",
            },
        )

        return AssembleResult(
            success=True,
            module=module,
            repo_map=repo_map,
            integration_guide=integration_guide,
        )

    def _extract_feature_info(
        self,
        requirement: str,
        adapted_files: List[AdaptedFile],
    ) -> Dict[str, Any]:
        """提取特性信息"""
        # 从需求中提取关键词
        words = re.findall(r'[\u4e00-\u9fa5a-zA-Z]+', requirement)

        # 尝试提取名词作为特性名
        feature_name = "feature"
        for word in words:
            if len(word) > 2 and word not in ["添加", "实现", "功能", "支持"]:
                feature_name = word
                break

        # 转换命名格式
        feature_snake = re.sub(r'[A-Z]', lambda m: '_' + m.group(0).lower(), feature_name)
        feature_snake = feature_snake.strip('_').lower().replace(' ', '_')
        feature_pascal = ''.join(word.capitalize() for word in feature_snake.split('_'))

        return {
            "feature_name": feature_name,
            "feature_snake": feature_snake,
            "feature_pascal": feature_pascal,
            "feature_route": feature_snake.replace('_', '-'),
            "class_name": feature_pascal,
            "model_name": feature_pascal,
        }

    def _assemble_backend(
        self,
        feature_info: Dict[str, Any],
        adapted_files: List[AdaptedFile],
        include_tests: bool,
    ) -> List[AssembledFile]:
        """组装后端模块"""
        files = []

        # 检查已有文件类型
        has_schema = any("schema" in af.file_path.lower() for af in adapted_files)
        has_service = any("service" in af.file_path.lower() for af in adapted_files)
        has_router = any("router" in af.file_path.lower() for af in adapted_files)

        # 生成缺失的文件
        if not has_schema:
            schema_content = self._render_template(
                BACKEND_SCHEMA_TEMPLATE,
                feature_info,
                fields="name: str",
                update_fields="name: Optional[str] = None",
            )
            files.append(AssembledFile(
                path=f"backend/schemas/{feature_info['feature_snake']}_schema.py",
                content=schema_content,
                action="create",
                dependencies=[],
            ))

        if not has_service:
            service_content = self._render_template(
                BACKEND_SERVICE_TEMPLATE,
                feature_info,
                model_file=feature_info['feature_snake'],
                schema_file=f"{feature_info['feature_snake']}_schema",
                feature_description=f"{feature_info['feature_name']} 服务",
            )
            files.append(AssembledFile(
                path=f"backend/services/{feature_info['feature_snake']}_service.py",
                content=service_content,
                action="create",
                dependencies=[f"backend/schemas/{feature_info['feature_snake']}_schema.py"],
            ))

        if not has_router:
            router_content = self._render_template(
                BACKEND_ROUTER_TEMPLATE,
                feature_info,
                service_file=f"{feature_info['feature_snake']}_service",
                schema_file=f"{feature_info['feature_snake']}_schema",
            )
            files.append(AssembledFile(
                path=f"backend/routers/{feature_info['feature_snake']}_router.py",
                content=router_content,
                action="create",
                dependencies=[
                    f"backend/services/{feature_info['feature_snake']}_service.py",
                    f"backend/schemas/{feature_info['feature_snake']}_schema.py",
                ],
            ))

        # 生成测试
        if include_tests:
            test_content = self._render_template(
                BACKEND_TEST_TEMPLATE,
                feature_info,
                create_payload='{"name": "test"}',
                update_payload='{"name": "updated"}',
            )
            files.append(AssembledFile(
                path=f"backend/tests/test_{feature_info['feature_snake']}.py",
                content=test_content,
                action="create",
                dependencies=[f"backend/routers/{feature_info['feature_snake']}_router.py"],
            ))

        return files

    def _render_template(self, template: str, feature_info: Dict[str, Any], **kwargs) -> str:
        """渲染模板"""
        context = {
            **feature_info,
            "ClassName": feature_info["class_name"],
            "ModelName": feature_info["model_name"],
            **kwargs,
        }

        result = template
        for key, value in context.items():
            result = result.replace(f"{{{key}}}", str(value))

        return result

    def _establish_dependencies(self, files: List[AssembledFile]) -> None:
        """建立文件依赖关系"""
        path_to_file = {f.path: f for f in files}

        for f in files:
            # 分析导入语句
            imports = re.findall(r'from\s+(backend\.[^\s]+)\s+import', f.content)
            for imp in imports:
                # 转换为文件路径
                imp_path = imp.replace('.', '/') + '.py'
                if imp_path in path_to_file and imp_path not in f.dependencies:
                    f.dependencies.append(imp_path)

    def _generate_repo_map(self, files: List[AssembledFile]) -> RepoMap:
        """生成 Repo Map"""
        new_files = [f.path for f in files if f.action == "create"]
        modified_files = [f.path for f in files if f.action == "modify"]

        return RepoMap(
            affected_files=[f.path for f in files],
            new_files=new_files,
            modified_files=modified_files,
        )

    def _generate_integration_guide(
        self,
        files: List[AssembledFile],
        feature_info: Dict[str, Any],
    ) -> IntegrationGuide:
        """生成集成指南"""
        steps = [
            f"1. 创建 {len([f for f in files if f.action == 'create'])} 个新文件",
            f"2. 在 backend/routers/__init__.py 中注册路由",
            f"3. 运行 pytest 验证测试",
        ]

        imports_to_add = [
            f"from backend.routers.{feature_info['feature_snake']}_router import router as {feature_info['feature_snake']}_router",
        ]

        config_changes = [
            f"app.include_router({feature_info['feature_snake']}_router)",
        ]

        return IntegrationGuide(
            steps=steps,
            imports_to_add=imports_to_add,
            config_changes=config_changes,
        )
