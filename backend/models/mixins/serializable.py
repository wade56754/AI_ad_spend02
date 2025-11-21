"""
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