"""
项目成员管理 API 单元测试

测试覆盖:
- CRUD 操作
- 权限验证
- 角色约束 (owner 唯一性)
- 转移负责人
- 批量操作

SoT Reference: MASTER.md v4.4 §2.4
"""

import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.models import User, Project
from backend.models.core.project_member import ProjectMember
from backend.schemas.project_member import (
    ProjectMemberRole,
    ProjectMemberCreateRequest,
    ProjectMemberUpdateRequest,
    TransferOwnershipRequest,
)
from backend.services.project_member_service import ProjectMemberService
from backend.exceptions.custom_exceptions import (
    ResourceNotFoundError,
    ResourceConflictError,
    PermissionDeniedError,
    BusinessLogicError,
)


# ==================== Fixtures ====================

@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_admin_user():
    """模拟管理员用户"""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "admin@example.com"
    user.role = MagicMock()
    user.role.value = "admin"
    return user


@pytest.fixture
def mock_owner_user():
    """模拟项目负责人用户"""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "owner@example.com"
    user.role = MagicMock()
    user.role.value = "media_buyer"
    return user


@pytest.fixture
def mock_member_user():
    """模拟普通成员用户"""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "member@example.com"
    user.role = MagicMock()
    user.role.value = "media_buyer"
    return user


@pytest.fixture
def mock_project():
    """模拟项目"""
    project = MagicMock(spec=Project)
    project.id = 1
    project.name = "Test Project"
    project.status = "active"
    return project


@pytest.fixture
def mock_project_member(mock_project, mock_member_user):
    """模拟项目成员"""
    member = MagicMock(spec=ProjectMember)
    member.id = 1
    member.project_id = mock_project.id
    member.user_id = mock_member_user.id
    member.role = "member"
    member.permissions = None
    member.notes = None
    member.created_at = datetime.now()
    member.updated_at = datetime.now()
    member.is_owner = False
    member.can_edit = True
    member.user = mock_member_user
    member.project = mock_project
    return member


@pytest.fixture
def service(mock_db):
    """创建服务实例"""
    return ProjectMemberService(mock_db)


# ==================== Service 单元测试 ====================

class TestProjectMemberService:
    """ProjectMemberService 单元测试"""

    def test_create_member_success(self, service, mock_db, mock_admin_user, mock_project, mock_member_user):
        """测试成功创建成员"""
        # 设置模拟
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_project,  # 项目存在
            mock_member_user,  # 用户存在
            None,  # 不是已有成员
            None,  # 没有现有 owner (如果添加为 owner)
        ]

        request = ProjectMemberCreateRequest(
            project_id=1,
            user_id=mock_member_user.id,
            role=ProjectMemberRole.MEMBER
        )

        # 执行
        with patch.object(service, '_check_management_permission'):
            member = service.create_member(request, mock_admin_user)

        # 验证
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_member_duplicate_error(self, service, mock_db, mock_admin_user, mock_project, mock_member_user, mock_project_member):
        """测试重复添加成员抛出错误"""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_project,  # 项目存在
            mock_member_user,  # 用户存在
            mock_project_member,  # 已是成员
        ]

        request = ProjectMemberCreateRequest(
            project_id=1,
            user_id=mock_member_user.id,
            role=ProjectMemberRole.MEMBER
        )

        with patch.object(service, '_check_management_permission'):
            with pytest.raises(ResourceConflictError) as exc_info:
                service.create_member(request, mock_admin_user)

        assert "已是项目成员" in str(exc_info.value)

    def test_create_owner_when_exists_error(self, service, mock_db, mock_admin_user, mock_project, mock_member_user, mock_project_member):
        """测试添加 owner 时已有 owner 抛出错误"""
        existing_owner = MagicMock(spec=ProjectMember)
        existing_owner.role = "owner"

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_project,  # 项目存在
            mock_member_user,  # 用户存在
            None,  # 不是已有成员
            existing_owner,  # 已有 owner
        ]

        request = ProjectMemberCreateRequest(
            project_id=1,
            user_id=mock_member_user.id,
            role=ProjectMemberRole.OWNER
        )

        with patch.object(service, '_check_management_permission'):
            with pytest.raises(ResourceConflictError) as exc_info:
                service.create_member(request, mock_admin_user)

        assert "已有负责人" in str(exc_info.value)

    def test_delete_owner_blocked(self, service, mock_db, mock_admin_user):
        """测试直接删除 owner 被阻止"""
        owner_member = MagicMock(spec=ProjectMember)
        owner_member.id = 1
        owner_member.project_id = 1
        owner_member.role = "owner"

        mock_db.query.return_value.filter.return_value.first.return_value = owner_member

        with patch.object(service, '_check_management_permission'):
            with pytest.raises(BusinessLogicError) as exc_info:
                service.delete_member(1, mock_admin_user)

        assert "不能直接删除" in str(exc_info.value)

    def test_transfer_ownership_success(self, service, mock_db, mock_admin_user, mock_owner_user, mock_member_user):
        """测试成功转移负责人"""
        current_owner = MagicMock(spec=ProjectMember)
        current_owner.id = 1
        current_owner.user_id = mock_owner_user.id
        current_owner.role = "owner"

        new_owner_member = MagicMock(spec=ProjectMember)
        new_owner_member.id = 2
        new_owner_member.user_id = mock_member_user.id
        new_owner_member.role = "member"

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            new_owner_member,  # 新负责人是成员
            current_owner,  # 当前负责人
        ]

        request = TransferOwnershipRequest(
            new_owner_user_id=mock_member_user.id,
            demote_current_to=ProjectMemberRole.MEMBER
        )

        with patch.object(service, '_check_management_permission'):
            result = service.transfer_ownership(1, request, mock_admin_user)

        # 验证角色变更
        assert current_owner.role == "member"
        assert new_owner_member.role == "owner"
        mock_db.commit.assert_called_once()

    def test_check_management_permission_admin(self, service, mock_db, mock_admin_user):
        """测试 admin 有管理权限"""
        # admin 应该通过
        service._check_management_permission(1, mock_admin_user)
        # 没有抛出异常即为通过

    def test_check_management_permission_owner(self, service, mock_db, mock_owner_user):
        """测试 owner 有管理权限"""
        mock_owner_user.role.value = "media_buyer"  # 非 admin

        owner_member = MagicMock(spec=ProjectMember)
        owner_member.role = "owner"
        mock_db.query.return_value.filter.return_value.first.return_value = owner_member

        # owner 应该通过
        service._check_management_permission(1, mock_owner_user)

    def test_check_management_permission_denied(self, service, mock_db, mock_member_user):
        """测试普通成员无管理权限"""
        mock_member_user.role.value = "media_buyer"  # 非 admin

        mock_db.query.return_value.filter.return_value.first.return_value = None  # 不是 owner

        with pytest.raises(PermissionDeniedError):
            service._check_management_permission(1, mock_member_user)


# ==================== Schema 测试 ====================

class TestProjectMemberSchemas:
    """Pydantic Schema 验证测试"""

    def test_create_request_valid(self):
        """测试有效创建请求"""
        request = ProjectMemberCreateRequest(
            project_id=1,
            user_id=uuid4(),
            role=ProjectMemberRole.MEMBER
        )
        assert request.role == ProjectMemberRole.MEMBER

    def test_create_request_role_from_string(self):
        """测试字符串角色转换"""
        request = ProjectMemberCreateRequest(
            project_id=1,
            user_id=uuid4(),
            role="viewer"  # type: ignore
        )
        assert request.role == ProjectMemberRole.VIEWER

    def test_transfer_request_invalid_demote_to_owner(self):
        """测试转移时不能降级为 owner"""
        with pytest.raises(ValueError) as exc_info:
            TransferOwnershipRequest(
                new_owner_user_id=uuid4(),
                demote_current_to=ProjectMemberRole.OWNER
            )
        assert "不能将当前负责人降级为 owner" in str(exc_info.value)

    def test_update_request_partial(self):
        """测试部分更新请求"""
        request = ProjectMemberUpdateRequest(
            role=ProjectMemberRole.VIEWER
        )
        assert request.role == ProjectMemberRole.VIEWER
        assert request.permissions is None
        assert request.notes is None


# ==================== API 端点测试 ====================

class TestProjectMembersAPI:
    """API 端点集成测试"""

    @pytest.fixture
    def client(self):
        """测试客户端"""
        return TestClient(app)

    def test_api_routes_registered(self, client):
        """测试 API 路由已注册"""
        # 获取 OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi = response.json()
        paths = openapi.get("paths", {})

        # 验证关键路由存在
        assert "/api/v1/project-members" in paths
        assert "/api/v1/project-members/{member_id}" in paths
        assert "/api/v1/projects/{project_id}/members" in paths
        assert "/api/v1/projects/{project_id}/transfer-owner" in paths
        assert "/api/v1/projects/{project_id}/owner" in paths
        assert "/api/v1/users/{user_id}/projects" in paths

    def test_create_member_requires_auth(self, client):
        """测试创建成员需要认证"""
        response = client.post(
            "/api/v1/project-members",
            json={
                "project_id": 1,
                "user_id": str(uuid4()),
                "role": "member"
            }
        )
        # 应返回 401 未认证
        assert response.status_code == 401

    def test_list_members_requires_auth(self, client):
        """测试列表需要认证"""
        response = client.get("/api/v1/projects/1/members")
        assert response.status_code == 401


# ==================== 角色枚举测试 ====================

class TestProjectMemberRole:
    """角色枚举测试"""

    def test_role_values(self):
        """测试角色值"""
        assert ProjectMemberRole.OWNER.value == "owner"
        assert ProjectMemberRole.MEMBER.value == "member"
        assert ProjectMemberRole.VIEWER.value == "viewer"

    def test_role_from_string(self):
        """测试从字符串创建角色"""
        assert ProjectMemberRole("owner") == ProjectMemberRole.OWNER
        assert ProjectMemberRole("member") == ProjectMemberRole.MEMBER
        assert ProjectMemberRole("viewer") == ProjectMemberRole.VIEWER

    def test_invalid_role(self):
        """测试无效角色抛出异常"""
        with pytest.raises(ValueError):
            ProjectMemberRole("invalid")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
