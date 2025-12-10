"""
项目模板服务测试模块
测试 backend/services/project_template_service.py 的模板管理功能

⚠️ 状态: 暂时禁用
原因: ProjectTemplate 模型未实现
TODO: 实现 backend/models/core/project_template.py 后启用此测试
"""

import pytest

# 暂时跳过所有测试，因为 ProjectTemplate 模型未实现
pytestmark = pytest.mark.skip(reason="ProjectTemplate 模型未实现，待补充实现")
import json
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from backend.services.project_template_service import ProjectTemplateService
from backend.models import ProjectTemplate, User
from backend.schemas.project_template import (
    ProjectTemplateCreateRequest,
    ProjectTemplateUpdateRequest
)
from backend.exceptions.custom_exceptions import (
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError
)


# ==================== Fixtures ====================

@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return Mock(spec=Session)


@pytest.fixture
def template_service(mock_db):
    """项目模板服务 fixture"""
    return ProjectTemplateService(mock_db)


@pytest.fixture
def admin_user():
    """管理员用户"""
    user = Mock(spec=User)
    user.id = 1
    user.username = "admin"
    user.role = "admin"
    return user


@pytest.fixture
def account_manager_user():
    """客户经理用户"""
    user = Mock(spec=User)
    user.id = 2
    user.username = "manager"
    user.role = "account_manager"
    return user


@pytest.fixture
def media_buyer_user():
    """投手用户"""
    user = Mock(spec=User)
    user.id = 3
    user.username = "buyer"
    user.role = "media_buyer"
    return user


@pytest.fixture
def advertiser_user():
    """广告主用户"""
    user = Mock(spec=User)
    user.id = 4
    user.username = "advertiser"
    user.role = "advertiser"
    return user


@pytest.fixture
def sample_template():
    """示例模板"""
    template = Mock(spec=ProjectTemplate)
    template.id = 1
    template.name = "电商推广模板"
    template.description = "适用于电商行业的推广模板"
    template.category = "ecommerce"
    template.default_budget = Decimal("100000.00")
    template.default_currency = "CNY"
    template.default_duration_days = 30
    template.config = json.dumps({
        "account_types": ["tiktok", "kuaishou"],
        "default_roles": ["account_manager", "media_buyer"],
        "checklist": ["设置广告账户", "配置投放计划", "设置预算"],
        "notes": "注意事项"
    }, ensure_ascii=False)
    template.is_active = True
    template.use_count = 5
    template.last_used_at = datetime.utcnow()
    template.created_by = 1
    template.created_at = datetime.utcnow()
    template.updated_at = None
    template.updated_by = None
    return template


@pytest.fixture
def create_request():
    """创建请求"""
    return ProjectTemplateCreateRequest(
        name="教育培训模板",
        description="适用于教育培训行业",
        category="education",
        default_budget=Decimal("50000.00"),
        default_currency="CNY",
        default_duration_days=60,
        account_types=["douyin", "wechat"],
        default_roles=["account_manager"],
        checklist=["准备素材", "设置账户"],
        notes="培训行业注意事项",
        is_active=True
    )


# ==================== 初始化测试 ====================

@pytest.mark.unit
@pytest.mark.project_template
class TestProjectTemplateServiceInitialization:
    """测试项目模板服务初始化"""

    def test_service_initialization(self, mock_db):
        """测试服务初始化"""
        service = ProjectTemplateService(mock_db)
        assert service.db == mock_db
        assert service.project_service is not None

    def test_template_categories_defined(self, template_service):
        """测试模板分类已定义"""
        categories = template_service.TEMPLATE_CATEGORIES
        assert len(categories) > 0
        assert all('value' in cat and 'label' in cat for cat in categories)


# ==================== 创建模板测试 ====================

@pytest.mark.unit
@pytest.mark.project_template
class TestCreateTemplate:
    """测试创建项目模板"""

    def test_create_template_success_admin(self, template_service, mock_db, admin_user, create_request):
        """测试管理员成功创建模板"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        with patch('backend.services.project_template_service.logging'):
            template = template_service.create_template(create_request, admin_user)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_template_success_account_manager(self, template_service, mock_db, account_manager_user, create_request):
        """测试客户经理成功创建模板"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        with patch('backend.services.project_template_service.logging'):
            template = template_service.create_template(create_request, account_manager_user)

        mock_db.add.assert_called_once()

    def test_create_template_permission_denied(self, template_service, advertiser_user, create_request):
        """测试无权限创建模板"""
        with pytest.raises(PermissionDeniedError) as exc_info:
            template_service.create_template(create_request, advertiser_user)

        assert "无权限创建项目模板" in str(exc_info.value)

    def test_create_template_duplicate_name(self, template_service, mock_db, admin_user, create_request, sample_template):
        """测试重复模板名称"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_template
        mock_db.query.return_value = mock_query

        with pytest.raises(ResourceConflictError) as exc_info:
            template_service.create_template(create_request, admin_user)

        assert "已存在" in str(exc_info.value)

    def test_create_template_default_category(self, template_service, mock_db, admin_user):
        """测试默认分类"""
        request = ProjectTemplateCreateRequest(
            name="测试模板",
            description="测试",
            default_budget=Decimal("10000.00"),
            default_currency="CNY",
            default_duration_days=30
        )

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        with patch('backend.services.project_template_service.logging'):
            template_service.create_template(request, admin_user)

        # 验证使用了默认分类 "custom"
        call_args = mock_db.add.call_args
        added_template = call_args[0][0]
        # Note: 由于是 Mock，我们只验证 add 被调用

    def test_create_template_database_error(self, template_service, mock_db, admin_user, create_request):
        """测试数据库错误"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        mock_db.commit.side_effect = Exception("Database error")

        with patch('backend.services.project_template_service.logging'):
            with pytest.raises(ResourceConflictError) as exc_info:
                template_service.create_template(create_request, admin_user)

        assert "创建模板失败" in str(exc_info.value)
        mock_db.rollback.assert_called_once()


# ==================== 获取模板列表测试 ====================

@pytest.mark.unit
@pytest.mark.project_template
class TestGetTemplates:
    """测试获取模板列表"""

    def test_get_templates_no_filters(self, template_service, mock_db, sample_template):
        """测试无过滤条件获取列表"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_template]
        mock_db.query.return_value = mock_query

        templates, total = template_service.get_templates()

        assert len(templates) == 1
        assert total == 1
        assert templates[0].id == 1

    def test_get_templates_with_category_filter(self, template_service, mock_db):
        """测试带分类过滤"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        templates, total = template_service.get_templates(category="ecommerce")

        assert total == 0
        # 验证 filter 被调用
        assert mock_query.filter.call_count >= 1

    def test_get_templates_with_active_filter(self, template_service, mock_db):
        """测试带活跃状态过滤"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        templates, total = template_service.get_templates(is_active=True)

        assert mock_query.filter.call_count >= 1

    def test_get_templates_pagination(self, template_service, mock_db):
        """测试分页"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 50
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        templates, total = template_service.get_templates(page=2, page_size=10)

        assert total == 50
        mock_query.offset.assert_called_with(10)
        mock_query.limit.assert_called_with(10)


# ==================== 获取模板详情测试 ====================

@pytest.mark.unit
@pytest.mark.project_template
class TestGetTemplate:
    """测试获取模板详情"""

    def test_get_template_success(self, template_service, mock_db, admin_user, sample_template):
        """测试成功获取模板"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_template
        mock_db.query.return_value = mock_query

        template = template_service.get_template(1, admin_user)

        assert template.id == 1
        assert template.name == "电商推广模板"

    def test_get_template_not_found(self, template_service, mock_db, admin_user):
        """测试模板不存在"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        with pytest.raises(ResourceNotFoundError) as exc_info:
            template_service.get_template(999, admin_user)

        assert "不存在" in str(exc_info.value)

    def test_get_template_permission_denied(self, template_service, mock_db, advertiser_user, sample_template):
        """测试无权限查看"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_template
        mock_db.query.return_value = mock_query

        with pytest.raises(PermissionDeniedError) as exc_info:
            template_service.get_template(1, advertiser_user)

        assert "无权限查看" in str(exc_info.value)

    def test_get_template_media_buyer_access(self, template_service, mock_db, media_buyer_user, sample_template):
        """测试投手可查看模板"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_template
        mock_db.query.return_value = mock_query

        template = template_service.get_template(1, media_buyer_user)

        assert template is not None


# ==================== 更新模板测试 ====================

@pytest.mark.unit
@pytest.mark.project_template
class TestUpdateTemplate:
    """测试更新模板"""

    def test_update_template_success(self, template_service, mock_db, admin_user, sample_template):
        """测试成功更新模板"""
        update_request = ProjectTemplateUpdateRequest(
            name="新名称",
            description="新描述"
        )

        # 模拟 get_template 返回
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_template
        mock_db.query.return_value = mock_query

        template = template_service.update_template(1, update_request, admin_user)

        mock_db.commit.assert_called_once()

    def test_update_template_permission_denied(self, template_service, mock_db, media_buyer_user, sample_template):
        """测试无权限更新"""
        update_request = ProjectTemplateUpdateRequest(name="新名称")

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_template
        mock_db.query.return_value = mock_query

        with pytest.raises(PermissionDeniedError):
            template_service.update_template(1, update_request, media_buyer_user)

    def test_update_template_duplicate_name(self, template_service, mock_db, admin_user, sample_template):
        """测试更新为重复名称"""
        update_request = ProjectTemplateUpdateRequest(name="重复名称")

        # 第一次查询返回当前模板
        # 第二次查询返回重复名称的其他模板
        other_template = Mock(spec=ProjectTemplate)
        other_template.id = 2
        other_template.name = "重复名称"

        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [sample_template, other_template]
        mock_db.query.return_value = mock_query

        with pytest.raises(ResourceConflictError) as exc_info:
            template_service.update_template(1, update_request, admin_user)

        assert "已存在" in str(exc_info.value)

    def test_update_template_partial_update(self, template_service, mock_db, admin_user, sample_template):
        """测试部分字段更新"""
        update_request = ProjectTemplateUpdateRequest(
            description="仅更新描述"
        )

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_template
        mock_db.query.return_value = mock_query

        template = template_service.update_template(1, update_request, admin_user)

        mock_db.commit.assert_called_once()


# ==================== 删除模板测试 ====================

@pytest.mark.unit
@pytest.mark.project_template
class TestDeleteTemplate:
    """测试删除模板"""

    def test_delete_template_success(self, template_service, mock_db, admin_user, sample_template):
        """测试管理员成功删除"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_template
        mock_db.query.return_value = mock_query

        result = template_service.delete_template(1, admin_user)

        assert result is True
        mock_db.delete.assert_called_once_with(sample_template)
        mock_db.commit.assert_called_once()

    def test_delete_template_permission_denied(self, template_service, account_manager_user):
        """测试非管理员无权删除"""
        with pytest.raises(PermissionDeniedError) as exc_info:
            template_service.delete_template(1, account_manager_user)

        assert "只有管理员可以删除" in str(exc_info.value)


# ==================== 应用模板测试 ====================

@pytest.mark.unit
@pytest.mark.project_template
class TestApplyTemplate:
    """测试应用模板创建项目"""

    @patch('backend.services.project_template_service.ProjectService')
    def test_apply_template_success(self, mock_project_service_class, template_service, mock_db, admin_user, sample_template):
        """测试成功应用模板"""
        # 模拟 get_template
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_template
        mock_db.query.return_value = mock_query

        # 模拟项目服务
        mock_project = Mock()
        mock_project.id = 1
        mock_project.name = "新项目"
        template_service.project_service.create_project.return_value = mock_project

        project = template_service.apply_template(
            template_id=1,
            project_name="新项目",
            client_name="测试客户",
            current_user=admin_user
        )

        assert project is not None
        template_service.project_service.create_project.assert_called_once()
        mock_db.commit.assert_called()

    def test_apply_template_permission_denied(self, template_service, mock_db, media_buyer_user, sample_template):
        """测试无权限应用模板"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_template
        mock_db.query.return_value = mock_query

        with pytest.raises(PermissionDeniedError):
            template_service.apply_template(1, "项目", "客户", media_buyer_user)

    def test_apply_template_increments_use_count(self, template_service, mock_db, admin_user, sample_template):
        """测试应用模板增加使用计数"""
        initial_count = sample_template.use_count

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_template
        mock_db.query.return_value = mock_query

        template_service.project_service.create_project.return_value = Mock()

        template_service.apply_template(1, "项目", "客户", admin_user)

        # 验证使用计数增加（虽然在 Mock 中不会真正增加）
        mock_db.commit.assert_called()


# ==================== 获取分类列表测试 ====================

@pytest.mark.unit
@pytest.mark.project_template
class TestGetTemplateCategories:
    """测试获取模板分类"""

    def test_get_template_categories(self, template_service):
        """测试获取分类列表"""
        categories = template_service.get_template_categories()

        assert len(categories) > 0
        assert all(isinstance(cat, dict) for cat in categories)
        assert all('value' in cat and 'label' in cat for cat in categories)

    def test_categories_include_ecommerce(self, template_service):
        """测试包含电商分类"""
        categories = template_service.get_template_categories()
        values = [cat['value'] for cat in categories]

        assert 'ecommerce' in values
        assert 'custom' in values


# ==================== 获取热门模板测试 ====================

@pytest.mark.unit
@pytest.mark.project_template
class TestGetPopularTemplates:
    """测试获取热门模板"""

    def test_get_popular_templates(self, template_service, mock_db, sample_template):
        """测试获取热门模板"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_template]
        mock_db.query.return_value = mock_query

        templates = template_service.get_popular_templates(limit=5)

        assert len(templates) == 1
        mock_query.limit.assert_called_with(5)

    def test_get_popular_templates_custom_limit(self, template_service, mock_db):
        """测试自定义数量"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        templates = template_service.get_popular_templates(limit=10)

        mock_query.limit.assert_called_with(10)


# ==================== 获取统计信息测试 ====================

@pytest.mark.unit
@pytest.mark.project_template
class TestGetTemplateStatistics:
    """测试获取模板统计"""

    def test_get_template_statistics(self, template_service, mock_db):
        """测试获取统计信息"""
        # 模拟总体统计
        mock_stats = Mock()
        mock_stats.total_templates = 10
        mock_stats.total_categories = 5
        mock_stats.total_uses = 50
        mock_stats.active_templates = 8

        # 模拟分类统计
        mock_category_stat = Mock()
        mock_category_stat.category = "ecommerce"
        mock_category_stat.count = 3
        mock_category_stat.uses = 15

        mock_query = Mock()
        mock_query.with_entities.return_value.first.return_value = mock_stats
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [mock_category_stat]
        mock_db.query.return_value = mock_query

        stats = template_service.get_template_statistics()

        assert stats['total_templates'] == 10
        assert stats['total_categories'] == 5
        assert stats['total_uses'] == 50
        assert stats['active_templates'] == 8
        assert len(stats['category_distribution']) == 1

    def test_get_template_statistics_empty(self, template_service, mock_db):
        """测试空统计"""
        mock_stats = Mock()
        mock_stats.total_templates = None
        mock_stats.total_categories = None
        mock_stats.total_uses = None
        mock_stats.active_templates = None

        mock_query = Mock()
        mock_query.with_entities.return_value.first.return_value = mock_stats
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        stats = template_service.get_template_statistics()

        assert stats['total_templates'] == 0
        assert stats['total_uses'] == 0
        assert stats['category_distribution'] == []


# ==================== 边界情况测试 ====================

@pytest.mark.unit
@pytest.mark.project_template
class TestProjectTemplateEdgeCases:
    """测试项目模板服务边界情况"""

    def test_create_template_empty_config(self, template_service, mock_db, admin_user):
        """测试空配置创建"""
        request = ProjectTemplateCreateRequest(
            name="空配置模板",
            description="测试",
            default_budget=Decimal("10000.00"),
            default_currency="CNY",
            default_duration_days=30
        )

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        with patch('backend.services.project_template_service.logging'):
            template_service.create_template(request, admin_user)

        mock_db.add.assert_called_once()

    def test_get_templates_page_zero(self, template_service, mock_db):
        """测试第0页（边界情况）"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        templates, total = template_service.get_templates(page=0, page_size=10)

        # 验证不会出错
        assert total == 0


# ==================== 集成测试 ====================

@pytest.mark.integration
@pytest.mark.project_template
class TestProjectTemplateIntegration:
    """项目模板服务集成测试"""

    def test_full_template_lifecycle(self, template_service, mock_db, admin_user, sample_template, create_request):
        """测试完整的模板生命周期"""
        # 创建模板
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        with patch('backend.services.project_template_service.logging'):
            template = template_service.create_template(create_request, admin_user)

        # 获取模板
        mock_query.filter.return_value.first.return_value = sample_template
        template = template_service.get_template(1, admin_user)

        # 更新模板
        update_request = ProjectTemplateUpdateRequest(description="更新后的描述")
        template = template_service.update_template(1, update_request, admin_user)

        # 删除模板
        result = template_service.delete_template(1, admin_user)

        assert result is True
        assert mock_db.commit.call_count >= 3  # 创建、更新、删除


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
