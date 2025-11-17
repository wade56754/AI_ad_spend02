"""
项目模板管理业务逻辑层
Version: 1.0
Author: Claude协作开发
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
import json

from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session

from exceptions.custom_exceptions import (
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError
)
from models.projects import ProjectTemplate
from models.users import User
from schemas.project_template import (
    ProjectTemplateCreateRequest,
    ProjectTemplateUpdateRequest
)
from services.project_service import ProjectService


class ProjectTemplateService:
    """项目模板服务类"""

    # 预定义的模板分类
    TEMPLATE_CATEGORIES = [
        {"value": "ecommerce", "label": "电商推广"},
        {"value": "education", "label": "教育培训"},
        {"value": "finance", "label": "金融服务"},
        {"value": "gaming", "label": "游戏应用"},
        {"value": "social", "label": "社交应用"},
        {"value": "tool", "label": "工具应用"},
        {"value": "brand", "label": "品牌推广"},
        {"value": "performance", "label": "效果营销"},
        {"value": "custom", "label": "自定义"}
    ]

    def __init__(self, db: Session):
        self.db = db
        self.project_service = ProjectService(db)

    def create_template(
        self,
        request: ProjectTemplateCreateRequest,
        current_user: User
    ) -> ProjectTemplate:
        """创建项目模板"""
        # 检查权限
        if current_user.role not in ["admin", "account_manager"]:
            raise PermissionDeniedError("无权限创建项目模板")

        # 检查模板名称是否已存在
        if self.db.query(ProjectTemplate).filter(
            ProjectTemplate.name == request.name
        ).first():
            raise ResourceConflictError(f"模板名称 '{request.name}' 已存在")

        # 创建模板
        template = ProjectTemplate(
            name=request.name,
            description=request.description,
            category=request.category or "custom",
            default_budget=request.default_budget,
            default_currency=request.default_currency,
            default_duration_days=request.default_duration_days,
            config=json.dumps({
                "account_types": request.account_types or [],
                "default_roles": request.default_roles or [],
                "checklist": request.checklist or [],
                "notes": request.notes or ""
            }, ensure_ascii=False),
            is_active=request.is_active,
            created_by=current_user.id
        )

        try:
            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)

            # 记录日志
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"项目模板创建成功: {template.id}", extra={
                "template_id": template.id,
                "template_name": template.name,
                "user_id": current_user.id,
                "action": "create_template"
            })

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建项目模板失败: {str(e)}")
            raise ResourceConflictError(f"创建模板失败: {str(e)}")

        return template

    def get_templates(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> tuple[List[ProjectTemplate], int]:
        """获取项目模板列表"""
        query = self.db.query(ProjectTemplate)

        # 应用筛选条件
        if category:
            query = query.filter(ProjectTemplate.category == category)
        if is_active is not None:
            query = query.filter(ProjectTemplate.is_active == is_active)

        # 统计总数
        total = query.count()

        # 分页查询
        templates = query.order_by(
            desc(ProjectTemplate.is_active),
            desc(ProjectTemplate.created_at)
        ).offset((page - 1) * page_size).limit(page_size).all()

        return templates, total

    def get_template(
        self,
        template_id: int,
        current_user: User
    ) -> ProjectTemplate:
        """获取项目模板详情"""
        template = self.db.query(ProjectTemplate).filter(
            ProjectTemplate.id == template_id
        ).first()

        if not template:
            raise ResourceNotFoundError(f"项目模板 {template_id} 不存在")

        # 检查权限（模板对投手可见）
        if current_user.role not in ["admin", "account_manager", "media_buyer"]:
            raise PermissionDeniedError("无权限查看项目模板")

        return template

    def update_template(
        self,
        template_id: int,
        request: ProjectTemplateUpdateRequest,
        current_user: User
    ) -> ProjectTemplate:
        """更新项目模板"""
        template = self.get_template(template_id, current_user)

        # 检查权限
        if current_user.role not in ["admin", "account_manager"]:
            raise PermissionDeniedError("无权限更新项目模板")

        # 检查模板名称是否重复
        if request.name and request.name != template.name:
            if self.db.query(ProjectTemplate).filter(
                and_(
                    ProjectTemplate.name == request.name,
                    ProjectTemplate.id != template_id
                )
            ).first():
                raise ResourceConflictError(f"模板名称 '{request.name}' 已存在")

        # 更新字段
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(template, field):
                setattr(template, field, value)

        template.updated_by = current_user.id
        template.updated_at = datetime.utcnow()

        self.db.commit()
        return template

    def delete_template(
        self,
        template_id: int,
        current_user: User
    ) -> bool:
        """删除项目模板"""
        if current_user.role != "admin":
            raise PermissionDeniedError("只有管理员可以删除项目模板")

        template = self.get_template(template_id, current_user)

        # 检查是否有项目使用该模板
        # TODO: 如果有项目关联，应该标记为不活跃而不是删除
        self.db.delete(template)
        self.db.commit()

        return True

    def apply_template(
        self,
        template_id: int,
        project_name: str,
        client_name: str,
        current_user: User
    ) -> Any:
        """应用项目模板创建项目"""
        template = self.get_template(template_id, current_user)

        # 检查权限
        if current_user.role not in ["admin", "account_manager"]:
            raise PermissionDeniedError("无权限基于模板创建项目")

        # 解析模板配置
        config = json.loads(template.config) if template.config else {}

        # 计算项目日期
        from datetime import timedelta
        start_date = date.today()
        end_date = start_date + timedelta(days=template.default_duration_days or 30)

        # 创建项目数据
        from schemas.project import ProjectCreateRequest
        project_request = ProjectCreateRequest(
            name=project_name,
            client_name=client_name,
            client_company="",  # 需要额外提供
            description=f"基于模板 '{template.name}' 创建的项目\n{template.description or ''}",
            budget=template.default_budget,
            currency=template.default_currency,
            start_date=start_date,
            end_date=end_date,
            account_manager_id=current_user.id if current_user.role == "account_manager" else None
        )

        # 使用项目服务创建项目
        project = self.project_service.create_project(project_request, current_user)

        # 应用模板的其他配置
        if "default_roles" in config:
            # TODO: 根据默认角色分配成员
            pass

        # 记录模板使用
        template.use_count = (template.use_count or 0) + 1
        template.last_used_at = datetime.utcnow()
        self.db.commit()

        return project

    def get_template_categories(self) -> List[Dict[str, str]]:
        """获取模板分类列表"""
        return self.TEMPLATE_CATEGORIES

    def get_popular_templates(self, limit: int = 5) -> List[ProjectTemplate]:
        """获取热门模板"""
        templates = self.db.query(ProjectTemplate).filter(
            ProjectTemplate.is_active == True
        ).order_by(
            desc(ProjectTemplate.use_count),
            desc(ProjectTemplate.created_at)
        ).limit(limit).all()

        return templates

    def get_template_statistics(self) -> Dict[str, Any]:
        """获取模板使用统计"""
        stats = self.db.query(ProjectTemplate).with_entities(
            func.count(ProjectTemplate.id).label('total_templates'),
            func.count(func.distinct(ProjectTemplate.category)).label('total_categories'),
            func.sum(ProjectTemplate.use_count).label('total_uses'),
            func.count(ProjectTemplate.id).filter(ProjectTemplate.is_active == True).label('active_templates')
        ).first()

        # 按分类统计
        category_stats = self.db.query(
            ProjectTemplate.category,
            func.count(ProjectTemplate.id).label('count'),
            func.sum(ProjectTemplate.use_count).label('uses')
        ).filter(
            ProjectTemplate.is_active == True
        ).group_by(ProjectTemplate.category).all()

        return {
            'total_templates': stats.total_templates or 0,
            'total_categories': stats.total_categories or 0,
            'total_uses': stats.total_uses or 0,
            'active_templates': stats.active_templates or 0,
            'category_distribution': [
                {
                    'category': stat.category,
                    'template_count': stat.count,
                    'total_uses': stat.uses or 0
                }
                for stat in category_stats
            ]
        }