"""
RLS 感知 Mixin - 确保 ORM 查询与 Supabase RLS 策略一致
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session, Query

# 延迟导入避免循环依赖
def get_user_role_enum():
    from backend.models.enums import UserRole
    return UserRole


class RLSAwareMixin:
    """RLS 感知 Mixin - 提供统一的权限过滤接口"""

    __rls_user_field__ = None  # 子类覆盖
    __rls_admin_roles__ = []  # 子类覆盖
    __rls_readonly_roles__ = []

    @classmethod
    def apply_rls_filter(cls, query: Query, current_user_id: UUID, current_user_role):
        """应用 RLS 过滤"""
        UserRole = get_user_role_enum()

        if current_user_role in cls.__rls_admin_roles__:
            return query

        if not cls.__rls_user_field__:
            raise ValueError(f"{cls.__name__} 未定义 __rls_user_field__")

        user_field = getattr(cls, cls.__rls_user_field__)
        return query.filter(user_field == current_user_id)

    @classmethod
    def get_for_user(cls, session: Session, current_user_id: UUID, current_user_role, filters: Optional[List] = None) -> Query:
        """获取用户可访问的记录"""
        query = session.query(cls)
        query = cls.apply_rls_filter(query, current_user_id, current_user_role)

        if filters:
            for filter_condition in filters:
                query = query.filter(filter_condition)

        return query

    def is_accessible_by(self, user_id: UUID, user_role) -> bool:
        """检查用户是否可访问此记录"""
        if user_role in self.__rls_admin_roles__:
            return True

        if not self.__rls_user_field__:
            return False

        user_field_value = getattr(self, self.__rls_user_field__)
        return user_field_value == user_id

    def is_modifiable_by(self, user_id: UUID, user_role) -> bool:
        """检查用户是否可修改此记录"""
        if user_role in self.__rls_readonly_roles__:
            return False
        return self.is_accessible_by(user_id, user_role)