#!/usr/bin/env python3
"""
接口代码生成工具
根据模板快速生成标准化的接口代码
"""

import os
import sys
from pathlib import Path
from typing import Dict, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class InterfaceGenerator:
    def __init__(self):
        self.templates_dir = project_root / "templates" / "interfaces"
        self.backend_dir = project_root / "backend"

    def generate_crud_interface(self, module_name: str, model_name: str, fields: List[Dict]):
        """
        生成完整的CRUD接口代码

        Args:
            module_name: 模块名称 (如: projects, users)
            model_name: 模型名称 (如: Project, User)
            fields: 字段列表 [{name: str, type: str, required: bool, description: str}]
        """
        print(f"🔨 生成 {module_name} 模块接口代码...")

        # 生成schemas
        self._generate_schemas(module_name, model_name, fields)

        # 生成routes
        self._generate_routes(module_name, model_name, fields)

        # 生成service
        self._generate_service(module_name, model_name, fields)

        # 生成测试
        self._generate_tests(module_name, model_name, fields)

        print(f"✅ {module_name} 模块接口代码生成完成")

    def _generate_schemas(self, module_name: str, model_name: str, fields: List[Dict]):
        """生成Pydantic模型"""
        schema_file = self.backend_dir / "schemas" / f"{module_name}.py"

        # 构建字段定义
        create_fields = []
        update_fields = []

        for field in fields:
            field_name = field["name"]
            field_type = field["type"]
            field_required = field["required"]
            field_desc = field.get("description", "")

            # 基础类型映射
            type_mapping = {
                "string": "str",
                "integer": "int",
                "float": "float",
                "boolean": "bool",
                "datetime": "datetime",
                "uuid": "UUID",
                "email": "EmailStr"
            }

            py_type = type_mapping.get(field_type, field_type)

            # Create字段
            create_field = f'    {field_name}: {py_type}'
            if not field_required:
                create_field += ' = None'
            create_field += f'  # {field_desc}'
            create_fields.append(create_field)

            # Update字段 (都设为可选)
            update_field = f'    {field_name}: Optional[{py_type}] = None  # {field_desc}'
            update_fields.append(update_field)

        # 生成schema文件内容
        content = f'''"""
{module_name.title()} 相关的Pydantic模型
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, validator

class {model_name}Base(BaseModel):
    """{model_name} 基础模型"""
{chr(10).join(create_fields)}

class {model_name}Create({model_name}Base):
    """创建{model_name}的请求模型"""
    pass

class {model_name}Update(BaseModel):
    """更新{model_name}的请求模型"""
{chr(10).join(update_fields)}

class {model_name}Response({model_name}Base):
    """{model_name}响应模型"""
    id: UUID = Field(..., description="唯一标识")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[UUID] = Field(None, description="创建者ID")
    updated_by: Optional[UUID] = Field(None, description="更新者ID")

    class Config:
        from_attributes = True

class {model_name}List(BaseModel):
    """{model_name}列表响应模型"""
    items: List[{model_name}Response]
    pagination: dict
'''

        # 确保目录存在
        schema_file.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        with open(schema_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"📝 生成schemas文件: {schema_file}")

    def _generate_routes(self, module_name: str, model_name: str, fields: List[Dict]):
        """生成路由文件"""
        route_file = self.backend_dir / "routers" / f"{module_name}.py"

        content = f'''"""
{module_name.title()} 相关路由
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.response import success_response, error_response, paginated_response
from backend.core.security import AuthenticatedUser, get_current_user, require_role
from backend.schemas.{module_name} import {model_name}Create, {model_name}Update, {model_name}Response
from backend.services.{module_name}_service import {model_name}Service

router = APIRouter(prefix="/{module_name}", tags=["{module_name}"])

# 权限装饰器示例 - 根据实际需求调整
{module_name}_list_roles = ["admin", "manager", "data_clerk"]
{module_name}_create_roles = ["admin", "manager"]
{module_name}_update_roles = ["admin", "manager"]
{module_name}_delete_roles = ["admin"]

@router.get("/", response_model=dict)
async def list_{module_name}(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: AuthenticatedUser = Depends(require_role({module_name}_list_roles)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    获取{module_name}列表

    支持分页和搜索功能。
    """
    try:
        service = {model_name}Service(db)
        result = await service.list_{module_name}(
            page=page,
            page_size=page_size,
            search=search,
            current_user=current_user
        )
        return paginated_response(
            data=result["items"],
            page=page,
            page_size=page_size,
            total=result["total"],
            message="获取{module_name}列表成功"
        )
    except Exception as e:
        return error_response(
            message=f"获取{module_name}列表失败: {{str(e)}}",
            code="SYS_INTERNAL_ERROR"
        )

@router.get("/{{item_id}}", response_model=dict)
async def get_{module_name}(
    item_id: UUID,
    current_user: AuthenticatedUser = Depends(require_role({module_name}_list_roles)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    获取{module_name}详情
    """
    try:
        service = {model_name}Service(db)
        item = await service.get_{module_name}_by_id(item_id, current_user)
        if not item:
            return error_response(
                message="{model_name}不存在",
                code="BIZ_{module_name.upper()}_NOT_FOUND",
                status_code=404
            )
        return success_response(
            data=item,
            message="获取{module_name}详情成功"
        )
    except Exception as e:
        return error_response(
            message=f"获取{module_name}详情失败: {{str(e)}}",
            code="SYS_INTERNAL_ERROR"
        )

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_{module_name}(
    item_data: {model_name}Create,
    current_user: AuthenticatedUser = Depends(require_role({module_name}_create_roles)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    创建{module_name}
    """
    try:
        service = {model_name}Service(db)
        item = await service.create_{module_name}(item_data, current_user)
        return success_response(
            data=item,
            message="创建{module_name}成功",
            status_code=201
        )
    except Exception as e:
        return error_response(
            message=f"创建{module_name}失败: {{str(e)}}",
            code="SYS_INTERNAL_ERROR"
        )

@router.put("/{{item_id}}", response_model=dict)
async def update_{module_name}(
    item_id: UUID,
    item_data: {model_name}Update,
    current_user: AuthenticatedUser = Depends(require_role({module_name}_update_roles)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    更新{module_name}
    """
    try:
        service = {model_name}Service(db)
        item = await service.update_{module_name}(item_id, item_data, current_user)
        if not item:
            return error_response(
                message="{model_name}不存在",
                code="BIZ_{module_name.upper()}_NOT_FOUND",
                status_code=404
            )
        return success_response(
            data=item,
            message="更新{module_name}成功"
        )
    except Exception as e:
        return error_response(
            message=f"更新{module_name}失败: {{str(e)}}",
            code="SYS_INTERNAL_ERROR"
        )

@router.delete("/{{item_id}}", response_model=dict)
async def delete_{module_name}(
    item_id: UUID,
    current_user: AuthenticatedUser = Depends(require_role({module_name}_delete_roles)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    删除{module_name}
    """
    try:
        service = {model_name}Service(db)
        success = await service.delete_{module_name}(item_id, current_user)
        if not success:
            return error_response(
                message="{model_name}不存在",
                code="BIZ_{module_name.upper()}_NOT_FOUND",
                status_code=404
            )
        return success_response(
            message="删除{module_name}成功"
        )
    except Exception as e:
        return error_response(
            message=f"删除{module_name}失败: {{str(e)}}",
            code="SYS_INTERNAL_ERROR"
        )
'''

        # 确保目录存在
        route_file.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        with open(route_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"🛣️ 生成routes文件: {route_file}")

    def _generate_service(self, module_name: str, model_name: str, fields: List[Dict]):
        """生成服务层文件"""
        service_file = self.backend_dir / "services" / f"{module_name}_service.py"

        content = f'''"""
{module_name.title()} 业务服务层
"""

from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.models.{module_name} import {model_name}
from backend.schemas.{module_name} import {model_name}Create, {model_name}Update
from backend.core.exceptions import BusinessLogicException

class {model_name}Service:
    """{model_name}服务类"""

    def __init__(self, db: Session):
        self.db = db

    async def list_{module_name}(
        self,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        current_user: Any = None
    ) -> Dict[str, Any]:
        """获取{module_name}列表"""
        query = self.db.query({model_name})

        # 应用权限过滤
        query = self._apply_permissions(query, current_user)

        # 搜索过滤
        if search:
            # 根据实际字段调整搜索逻辑
            query = query.filter(
                {model_name}.name.ilike(f"%{{search}}%")
            )

        # 计算总数
        total = query.count()

        # 分页查询
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        # 转换为响应格式
        items_data = []
        for item in items:
            items_data.append({{
                "id": str(item.id),
                "name": item.name,
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat()
            }})

        return {{
            "items": items_data,
            "total": total
        }}

    async def get_{module_name}_by_id(
        self,
        item_id: UUID,
        current_user: Any = None
    ) -> Optional[Dict[str, Any]]:
        """根据ID获取{module_name}"""
        query = self.db.query({model_name}).filter({model_name}.id == item_id)

        # 应用权限过滤
        query = self._apply_permissions(query, current_user)

        item = query.first()
        if not item:
            return None

        return {{
            "id": str(item.id),
            "name": item.name,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat()
        }}

    async def create_{module_name}(
        self,
        item_data: {model_name}Create,
        current_user: Any = None
    ) -> Dict[str, Any]:
        """创建{module_name}"""
        # 检查业务规则
        await self._validate_create_data(item_data)

        # 创建记录
        item = {model_name}(**item_data.dict())
        item.created_by = current_user.id if current_user else None

        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        return {{
            "id": str(item.id),
            "name": item.name,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat()
        }}

    async def update_{module_name}(
        self,
        item_id: UUID,
        item_data: {model_name}Update,
        current_user: Any = None
    ) -> Optional[Dict[str, Any]]:
        """更新{module_name}"""
        item = self.db.query({model_name}).filter({model_name}.id == item_id).first()
        if not item:
            return None

        # 检查权限
        if not self._can_update(item, current_user):
            raise BusinessLogicException("无权限更新此{module_name}")

        # 更新字段
        update_data = item_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)

        item.updated_by = current_user.id if current_user else None

        self.db.commit()
        self.db.refresh(item)

        return {{
            "id": str(item.id),
            "name": item.name,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat()
        }}

    async def delete_{module_name}(
        self,
        item_id: UUID,
        current_user: Any = None
    ) -> bool:
        """删除{module_name}"""
        item = self.db.query({model_name}).filter({model_name}.id == item_id).first()
        if not item:
            return False

        # 检查权限
        if not self._can_delete(item, current_user):
            raise BusinessLogicException("无权限删除此{module_name}")

        self.db.delete(item)
        self.db.commit()

        return True

    def _apply_permissions(self, query, current_user: Any = None):
        """应用权限过滤"""
        # 根据用户角色实现权限过滤逻辑
        if current_user:
            if current_user.role == "admin":
                # 管理员可以查看所有
                pass
            elif current_user.role == "manager":
                # 项目经理只能查看自己的数据
                # query = query.filter({model_name}.manager_id == current_user.id)
                pass
            else:
                # 其他角色需要特殊权限处理
                # query = query.filter({model_name}.created_by == current_user.id)
                pass

        return query

    def _can_update(self, item, current_user: Any = None) -> bool:
        """检查是否可以更新"""
        if not current_user:
            return False

        # 管理员可以更新所有
        if current_user.role == "admin":
            return True

        # 创建者可以更新自己的
        if item.created_by == current_user.id:
            return True

        # 项目经理可以更新自己负责的
        # if current_user.role == "manager" and item.manager_id == current_user.id:
        #     return True

        return False

    def _can_delete(self, item, current_user: Any = None) -> bool:
        """检查是否可以删除"""
        # 删除权限通常更严格
        if not current_user:
            return False

        # 只有管理员可以删除
        return current_user.role == "admin"

    async def _validate_create_data(self, item_data: {model_name}Create):
        """验证创建数据"""
        # 检查业务规则
        # 示例：检查名称是否重复
        existing = self.db.query({model_name}).filter(
            {model_name}.name == item_data.name
        ).first()

        if existing:
            raise BusinessLogicException(f"{module_name.title()}名称已存在")
'''

        # 确保目录存在
        service_file.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        with open(service_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"⚙️ 生成service文件: {service_file}")

    def _generate_tests(self, module_name: str, model_name: str, fields: List[Dict]):
        """生成测试文件"""
        test_file = project_root / "tests" / "test_{module_name}.py"

        content = f'''"""
{module_name.title()} 接口测试
"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime

from app.main import app
from app.core.auth import create_access_token
from app.models.user import User

client = TestClient(app)

class Test{model_name}API:
    """{model_name} API测试类"""

    @pytest.fixture
    def auth_headers(self):
        """获取认证头"""
        user = User(
            id=uuid4(),
            email="test@example.com",
            full_name="测试用户",
            role="admin"
        )
        token = create_access_token(data={{"sub": str(user.id)}})
        return {{"Authorization": f"Bearer {{token}}"}}

    def test_list_{module_name}(self, auth_headers):
        """测试获取{module_name}列表"""
        response = client.get("/api/v1/{module_name}/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "pagination" in data["data"]

    def test_create_{module_name}(self, auth_headers):
        """测试创建{module_name}"""
        {module_name}_data = {{
            "name": "测试{module_name}",
            # 根据实际字段添加测试数据
        }}

        response = client.post(
            "/api/v1/{module_name}/",
            json={module_name}_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "测试{module_name}"

    def test_get_{module_name}_not_found(self, auth_headers):
        """测试获取不存在的{module_name}"""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/{module_name}/{{fake_id}}", headers=auth_headers)

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "不存在" in data["message"]

    def test_update_{module_name}(self, auth_headers):
        """测试更新{module_name}"""
        # 先创建一个{module_name}
        {module_name}_data = {{
            "name": "原始{module_name}"
        }}

        create_response = client.post(
            "/api/v1/{module_name}/",
            json={module_name}_data,
            headers=auth_headers
        )

        item_id = create_response.json()["data"]["id"]

        # 更新{module_name}
        update_data = {{
            "name": "更新后的{module_name}"
        }}

        response = client.put(
            f"/api/v1/{module_name}/{{item_id}}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "更新后的{module_name}"

    def test_delete_{module_name}(self, auth_headers):
        """测试删除{module_name}"""
        # 先创建一个{module_name}
        {module_name}_data = {{
            "name": "待删除{module_name}"
        }}

        create_response = client.post(
            "/api/v1/{module_name}/",
            json={module_name}_data,
            headers=auth_headers
        )

        item_id = create_response.json()["data"]["id"]

        # 删除{module_name}
        response = client.delete(
            f"/api/v1/{module_name}/{{item_id}}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_unauthorized_access(self):
        """测试未授权访问"""
        response = client.get("/api/v1/{module_name}/")

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False

    def test_invalid_permissions(self):
        """测试权限不足"""
        # 创建非管理员用户token
        user = User(
            id=uuid4(),
            email="user@example.com",
            full_name="普通用户",
            role="user"
        )
        token = create_access_token(data={{"sub": str(user.id)}})
        headers = {{"Authorization": f"Bearer {{token}}"}}

        response = client.post(
            "/api/v1/{module_name}/",
            json={{"name": "测试"}},
            headers=headers
        )

        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert "权限" in data["message"]
'''

        # 确保目录存在
        test_file.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"🧪 生成test文件: {test_file}")


def main():
    """主函数 - 示例用法"""
    generator = InterfaceGenerator()

    # 示例：生成projects模块
    fields = [
        {"name": "name", "type": "string", "required": True, "description": "项目名称"},
        {"name": "code", "type": "string", "required": True, "description": "项目代码"},
        {"name": "description", "type": "string", "required": False, "description": "项目描述"},
        {"name": "client_name", "type": "string", "required": True, "description": "客户名称"},
        {"name": "budget", "type": "float", "required": False, "description": "项目预算"},
        {"name": "start_date", "type": "datetime", "required": False, "description": "开始日期"},
        {"name": "end_date", "type": "datetime", "required": False, "description": "结束日期"},
    ]

    generator.generate_crud_interface("projects", "Project", fields)


if __name__ == "__main__":
    main()