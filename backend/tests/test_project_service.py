"""
项目管理服务层测试
Version: 1.0
Author: Claude协作开发
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from unittest.mock import Mock, patch

from models.project import Project, ProjectMember, ProjectExpense
from models.user import User
from schemas.project import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectMemberAssignRequest,
    ProjectExpenseRequest
)
from services.project_service import ProjectService
from exceptions.custom_exceptions import (
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError,
    BusinessLogicError
)


class TestProjectService:
    """项目管理服务测试类"""

    @pytest.fixture
    def project_service(self, db_session):
        """创建项目服务实例"""
        return ProjectService(db_session)

    @pytest.fixture
    def admin_user(self, db_session):
        """创建管理员用户"""
        user = User(
            id=1,
            email="admin@example.com",
            nickname="管理员",
            role="admin"
        )
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def account_manager(self, db_session):
        """创建账户管理员"""
        user = User(
            id=2,
            email="manager@example.com",
            nickname="账户经理",
            role="account_manager"
        )
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def sample_project(self, db_session, admin_user):
        """创建示例项目"""
        project = Project(
            name="测试项目",
            client_name="客户A",
            client_company="客户公司A",
            description="这是一个测试项目",
            status="planning",
            budget=Decimal("10000.00"),
            currency="USD",
            created_by=admin_user.id
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        return project

    class TestProjectCRUD:
        """项目CRUD操作测试"""

        def test_create_project_success(self, project_service, admin_user):
            """测试成功创建项目"""
            request = ProjectCreateRequest(
                name="新项目",
                client_name="客户B",
                client_company="客户公司B",
                description="新项目描述",
                budget=Decimal("20000.00"),
                currency="USD",
                start_date=date(2025, 1, 1),
                end_date=date(2025, 12, 31)
            )

            project = project_service.create_project(request, admin_user)

            assert project.name == "新项目"
            assert project.client_name == "客户B"
            assert project.budget == Decimal("20000.00")
            assert project.created_by == admin_user.id
            assert project.status == "planning"

        def test_create_project_duplicate_name(self, project_service, admin_user, sample_project):
            """测试创建重复项目名称"""
            request = ProjectCreateRequest(
                name=sample_project.name,  # 使用相同名称
                client_name="新客户",
                client_company="新公司"
            )

            with pytest.raises(ResourceConflictError):
                project_service.create_project(request, admin_user)

        def test_create_project_invalid_date_range(self, project_service, admin_user):
            """测试创建项目时日期范围无效"""
            request = ProjectCreateRequest(
                name="项目",
                client_name="客户",
                client_company="公司",
                start_date=date(2025, 12, 31),
                end_date=date(2025, 1, 1)  # 结束日期早于开始日期
            )

            with pytest.raises(BusinessLogicError):
                project_service.create_project(request, admin_user)

        def test_get_project_success(self, project_service, sample_project, admin_user):
            """测试成功获取项目"""
            project = project_service.get_project(sample_project.id, admin_user)
            assert project.id == sample_project.id
            assert project.name == sample_project.name

        def test_get_project_not_found(self, project_service, admin_user):
            """测试获取不存在的项目"""
            with pytest.raises(ResourceNotFoundError):
                project_service.get_project(99999, admin_user)

        def test_update_project_success(self, project_service, sample_project, admin_user):
            """测试成功更新项目"""
            request = ProjectUpdateRequest(
                name="更新后的项目名",
                status="active",
                budget=Decimal("15000.00")
            )

            project = project_service.update_project(sample_project.id, request, admin_user)
            assert project.name == "更新后的项目名"
            assert project.status == "active"
            assert project.budget == Decimal("15000.00")

        def test_update_project_status_invalid(self, project_service, sample_project, admin_user):
            """测试更新项目为无效状态"""
            request = ProjectUpdateRequest(status="invalid_status")

            with pytest.raises(BusinessLogicError):
                project_service.update_project(sample_project.id, request, admin_user)

        def test_delete_project_success(self, project_service, sample_project, admin_user):
            """测试成功删除项目"""
            project_service.delete_project(sample_project.id, admin_user)

            with pytest.raises(ResourceNotFoundError):
                project_service.get_project(sample_project.id, admin_user)

        def test_delete_project_with_expenses(self, project_service, sample_project, admin_user, db_session):
            """测试删除有费用的项目"""
            # 创建项目费用
            expense = ProjectExpense(
                project_id=sample_project.id,
                expense_type="media_spend",
                amount=Decimal("1000.00"),
                expense_date=date.today(),
                created_by=admin_user.id
            )
            db_session.add(expense)
            db_session.commit()

            with pytest.raises(BusinessLogicError, match="有关联的费用记录"):
                project_service.delete_project(sample_project.id, admin_user)

        def test_get_projects_with_pagination(self, project_service, admin_user, db_session):
            """测试分页获取项目列表"""
            # 创建多个项目
            for i in range(25):
                project = Project(
                    name=f"项目{i}",
                    client_name=f"客户{i}",
                    client_company=f"公司{i}",
                    created_by=admin_user.id
                )
                db_session.add(project)
            db_session.commit()

            projects, total = project_service.get_projects(
                current_user=admin_user,
                page=1,
                page_size=10
            )

            assert len(projects) == 10
            assert total == 25

        def test_get_projects_with_filters(self, project_service, admin_user, sample_project, db_session):
            """测试带过滤条件获取项目列表"""
            # 创建不同状态的项目
            active_project = Project(
                name="活跃项目",
                client_name="客户C",
                client_company="公司C",
                status="active",
                account_manager_id=2,
                created_by=admin_user.id
            )
            db_session.add(active_project)
            db_session.commit()

            # 按状态过滤
            projects, total = project_service.get_projects(
                current_user=admin_user,
                status="active"
            )
            assert len(projects) == 1
            assert projects[0].status == "active"

            # 按客户名称过滤
            projects, total = project_service.get_projects(
                current_user=admin_user,
                client_name="客户A"
            )
            assert len(projects) == 1
            assert projects[0].client_name == "客户A"

    class TestProjectMembers:
        """项目成员管理测试"""

        def test_assign_member_success(self, project_service, sample_project, admin_user, db_session):
            """测试成功分配项目成员"""
            # 创建媒体买家用户
            media_buyer = User(
                id=3,
                email="buyer@example.com",
                nickname="媒体买家",
                role="media_buyer"
            )
            db_session.add(media_buyer)
            db_session.commit()

            request = ProjectMemberAssignRequest(
                user_id=media_buyer.id,
                role="media_buyer"
            )

            member = project_service.assign_member(sample_project.id, request, admin_user)
            assert member.project_id == sample_project.id
            assert member.user_id == media_buyer.id
            assert member.role == "media_buyer"

        def test_assign_duplicate_member(self, project_service, sample_project, admin_user, db_session):
            """测试分配重复成员"""
            # 先添加一个成员
            member = ProjectMember(
                project_id=sample_project.id,
                user_id=admin_user.id,
                role="account_manager"
            )
            db_session.add(member)
            db_session.commit()

            request = ProjectMemberAssignRequest(
                user_id=admin_user.id,
                role="media_buyer"
            )

            with pytest.raises(ResourceConflictError):
                project_service.assign_member(sample_project.id, request, admin_user)

        def test_remove_member_success(self, project_service, sample_project, admin_user, db_session):
            """测试成功移除项目成员"""
            # 先添加成员
            member = ProjectMember(
                project_id=sample_project.id,
                user_id=admin_user.id,
                role="account_manager"
            )
            db_session.add(member)
            db_session.commit()

            project_service.remove_member(sample_project.id, admin_user.id, admin_user)

            # 验证成员已被移除
            members = project_service.get_project_members(sample_project.id, admin_user)
            assert len(members) == 0

        def test_get_project_members_success(self, project_service, sample_project, admin_user, db_session):
            """测试获取项目成员列表"""
            # 添加多个成员
            user1 = User(id=4, email="user1@example.com", nickname="用户1", role="media_buyer")
            user2 = User(id=5, email="user2@example.com", nickname="用户2", role="analyst")
            db_session.add_all([user1, user2])
            db_session.flush()

            member1 = ProjectMember(
                project_id=sample_project.id,
                user_id=user1.id,
                role="media_buyer"
            )
            member2 = ProjectMember(
                project_id=sample_project.id,
                user_id=user2.id,
                role="analyst"
            )
            db_session.add_all([member1, member2])
            db_session.commit()

            members = project_service.get_project_members(sample_project.id, admin_user)
            assert len(members) == 2

    class TestProjectExpenses:
        """项目费用管理测试"""

        def test_add_expense_success(self, project_service, sample_project, admin_user):
            """测试成功添加项目费用"""
            request = ProjectExpenseRequest(
                expense_type="media_spend",
                amount=Decimal("500.00"),
                description="Facebook广告费",
                expense_date=date.today()
            )

            expense = project_service.add_expense(sample_project.id, request, admin_user)
            assert expense.project_id == sample_project.id
            assert expense.expense_type == "media_spend"
            assert expense.amount == Decimal("500.00")

        def test_add_expense_invalid_type(self, project_service, sample_project, admin_user):
            """测试添加无效类型的费用"""
            request = ProjectExpenseRequest(
                expense_type="invalid_type",
                amount=Decimal("100.00"),
                expense_date=date.today()
            )

            with pytest.raises(BusinessLogicError):
                project_service.add_expense(sample_project.id, request, admin_user)

        def test_get_project_expenses_with_pagination(self, project_service, sample_project, admin_user, db_session):
            """测试分页获取项目费用"""
            # 创建多个费用记录
            for i in range(25):
                expense = ProjectExpense(
                    project_id=sample_project.id,
                    expense_type="media_spend",
                    amount=Decimal(f"{100 + i}.00"),
                    expense_date=date.today(),
                    created_by=admin_user.id
                )
                db_session.add(expense)
            db_session.commit()

            expenses, total = project_service.get_project_expenses(
                project_id=sample_project.id,
                current_user=admin_user,
                page=1,
                page_size=10
            )

            assert len(expenses) == 10
            assert total == 25

    class TestProjectStatistics:
        """项目统计测试"""

        def test_get_project_statistics(self, project_service, admin_user, db_session):
            """测试获取项目统计信息"""
            # 创建不同状态的项目
            for status, count in [("active", 5), ("paused", 3), ("completed", 2)]:
                for i in range(count):
                    project = Project(
                        name=f"项目_{status}_{i}",
                        client_name=f"客户_{status}_{i}",
                        client_company=f"公司_{status}_{i}",
                        status=status,
                        budget=Decimal("10000.00"),
                        created_by=admin_user.id
                    )
                    db_session.add(project)
            db_session.commit()

            stats = project_service.get_project_statistics(admin_user)

            assert stats.total_projects == 10
            assert stats.active_projects == 5
            assert stats.paused_projects == 3
            assert stats.completed_projects == 2
            assert stats.total_budget == Decimal("100000.00")
            assert stats.total_clients == 10
            assert stats.avg_project_value == Decimal("10000.00")

    class TestPermissionChecks:
        """权限检查测试"""

        def test_media_buyer_cannot_create_project(self, project_service):
            """测试媒体买家不能创建项目"""
            media_buyer = User(
                id=6,
                email="buyer2@example.com",
                nickname="媒体买家2",
                role="media_buyer"
            )

            request = ProjectCreateRequest(
                name="项目",
                client_name="客户",
                client_company="公司"
            )

            with pytest.raises(PermissionDeniedError):
                project_service.create_project(request, media_buyer)

        def test_account_manager_can_only_update_own_projects(
            self, project_service, sample_project, account_manager
        ):
            """测试账户管理员只能更新自己的项目"""
            # 项目不是由该账户管理员管理的
            assert sample_project.account_manager_id != account_manager.id

            request = ProjectUpdateRequest(name="更新的项目")

            with pytest.raises(PermissionDeniedError):
                project_service.update_project(sample_project.id, request, account_manager)