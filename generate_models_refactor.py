"""
Models 层自动重构生成脚本

运行此脚本将自动创建所有按照 SQLALCHEMY_OPTIMIZATION_GUIDE.md 规范的模型文件

使用方法:
    python generate_models_refactor.py

注意：
- 确保当前在项目根目录
- 会自动创建目录结构
- 会备份现有的 __init__.py
"""
import os
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent
MODELS_DIR = ROOT_DIR / "backend" / "models"

# 确保目录存在
for dir_name in ["mixins", "core", "accounts", "workflow", "finance", "audit"]:
    (MODELS_DIR / dir_name).mkdir(parents=True, exist_ok=True)


# ==================== Mixins ====================

# mixins/__init__.py
MIXINS_INIT = '''"""Mixins 模块"""
from .serializable import SerializableMixin
from .rls_aware import RLSAwareMixin

__all__ = ["SerializableMixin", "RLSAwareMixin"]
'''

# mixins/serializable.py
SERIALIZABLE_MIXIN = '''"""
序列化 Mixin - 将模型对象转换为字典
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class SerializableMixin:
    """
    序列化 Mixin - 将模型对象转换为字典

    使用方式:
        class MyModel(Base, SerializableMixin):
            __json_hidden__ = ['password']  # 隐藏字段
            __json_include_relationships__ = ['user', 'project']  # 包含关联
    """

    __json_hidden__ = []
    __json_include_relationships__ = []

    def to_dict(
        self,
        include_relationships: bool = False,
        exclude: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """转换为字典"""
        exclude = exclude or []
        exclude.extend(self.__json_hidden__)

        result = {}

        # 序列化列字段
        for column in self.__table__.columns:
            if column.name in exclude:
                continue
            value = getattr(self, column.name)
            result[column.name] = self._serialize_value(value)

        # 序列化关联对象
        if include_relationships:
            for rel_name in self.__json_include_relationships__:
                if rel_name in exclude:
                    continue
                rel_value = getattr(self, rel_name, None)
                if rel_value is None:
                    result[rel_name] = None
                elif isinstance(rel_value, list):
                    result[rel_name] = [
                        item.to_dict(include_relationships=False)
                        if hasattr(item, 'to_dict') else str(item)
                        for item in rel_value
                    ]
                else:
                    result[rel_name] = (
                        rel_value.to_dict(include_relationships=False)
                        if hasattr(rel_value, 'to_dict') else str(rel_value)
                    )

        return result

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """序列化单个值"""
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, UUID):
            return str(value)
        elif isinstance(value, bytes):
            return value.decode('utf-8', errors='ignore')
        return value

    @classmethod
    def from_dict(cls, data: Dict[str, Any], session=None):
        """从字典创建实例"""
        valid_columns = {col.name for col in cls.__table__.columns}
        filtered_data = {k: v for k, v in data.items() if k in valid_columns}
        return cls(**filtered_data)
'''

# mixins/rls_aware.py
RLS_AWARE_MIXIN = '''"""
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
'''


def write_file(path: Path, content: str):
    """写入文件"""
    path.write_text(content.strip(), encoding='utf-8')
    print(f"[OK] Created: {path.relative_to(ROOT_DIR)}")


def main():
    print("开始生成 Models 层重构文件...\n")

    # 创建 mixins 文件
    write_file(MODELS_DIR / "mixins" / "__init__.py", MIXINS_INIT)
    write_file(MODELS_DIR / "mixins" / "serializable.py", SERIALIZABLE_MIXIN)
    write_file(MODELS_DIR / "mixins" / "rls_aware.py", RLS_AWARE_MIXIN)

    # 创建空的 __init__.py
    for dir_name in ["core", "accounts", "workflow", "finance", "audit"]:
        write_file(MODELS_DIR / dir_name / "__init__.py", "# Models")

    print(f"\n✅ 完成！已创建基础文件结构")
    print("\n📋 接下来需要手动创建的文件：")
    print("  - core/user.py, core/channel.py, core/project.py")
    print("  - accounts/ad_account.py, accounts/account_request.py, accounts/account_history.py")
    print("  - workflow/daily_report.py, workflow/topup_request.py, workflow/ad_spend.py")
    print("  - finance/ledger.py, finance/reconciliation.py")
    print("  - audit/audit_log.py")
    print("  - events.py")
    print("  - 更新 __init__.py")
    print("\n💡 提示：由于每个模型文件较大，建议参考 SQLALCHEMY_OPTIMIZATION_GUIDE.md 逐个创建")


if __name__ == "__main__":
    main()
