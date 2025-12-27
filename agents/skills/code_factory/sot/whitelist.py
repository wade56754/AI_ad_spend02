"""
动态白名单管理

基准文档: MASTER.md v4.6
版本: v4.2

功能:
- 管理角色、状态、错误码白名单
- 支持验证和建议
"""

from dataclasses import dataclass, field
from typing import Set, Dict, Optional, Tuple, List
from difflib import get_close_matches


@dataclass
class WhitelistEntry:
    """白名单条目"""
    value: str
    category: str
    deprecated: bool = False
    replacement: Optional[str] = None
    source: Optional[str] = None  # SoT 来源


class DynamicWhitelist:
    """动态白名单管理器"""

    def __init__(self):
        self._entries: Dict[str, Dict[str, WhitelistEntry]] = {
            "role": {},
            "state": {},
            "error_code": {},
            "field": {},
        }

    def register(
        self,
        category: str,
        value: str,
        deprecated: bool = False,
        replacement: Optional[str] = None,
        source: Optional[str] = None,
    ):
        """注册白名单条目

        Args:
            category: 类别 (role, state, error_code, field)
            value: 值
            deprecated: 是否已废弃
            replacement: 替换值 (如果废弃)
            source: SoT 来源
        """
        if category not in self._entries:
            self._entries[category] = {}

        self._entries[category][value] = WhitelistEntry(
            value=value,
            category=category,
            deprecated=deprecated,
            replacement=replacement,
            source=source,
        )

    def register_bulk(
        self,
        category: str,
        values: Set[str],
        source: Optional[str] = None,
    ):
        """批量注册

        Args:
            category: 类别
            values: 值集合
            source: SoT 来源
        """
        for value in values:
            self.register(category, value, source=source)

    def is_valid(self, category: str, value: str) -> bool:
        """检查值是否有效

        Args:
            category: 类别
            value: 值

        Returns:
            是否有效
        """
        if category not in self._entries:
            return False
        return value in self._entries[category]

    def validate(self, category: str, value: str) -> Tuple[bool, Optional[str]]:
        """验证值并返回建议

        Args:
            category: 类别
            value: 值

        Returns:
            (是否有效, 建议信息)
        """
        if category not in self._entries:
            return False, f"未知类别: {category}"

        entries = self._entries[category]

        if value in entries:
            entry = entries[value]
            if entry.deprecated:
                return True, f"警告: '{value}' 已废弃，建议使用 '{entry.replacement}'"
            return True, None

        # 查找相似值
        all_values = list(entries.keys())
        similar = get_close_matches(value, all_values, n=3, cutoff=0.6)

        if similar:
            suggestion = ", ".join(similar)
            return False, f"无效值 '{value}'。您是否想用: {suggestion}?"
        else:
            return False, f"无效值 '{value}'。有效值: {', '.join(sorted(all_values)[:10])}"

    def get_all(self, category: str) -> Set[str]:
        """获取类别下所有值

        Args:
            category: 类别

        Returns:
            值集合
        """
        if category not in self._entries:
            return set()
        return set(self._entries[category].keys())

    def get_active(self, category: str) -> Set[str]:
        """获取类别下所有未废弃的值

        Args:
            category: 类别

        Returns:
            值集合
        """
        if category not in self._entries:
            return set()
        return {
            k for k, v in self._entries[category].items()
            if not v.deprecated
        }

    def suggest(self, category: str, partial: str, limit: int = 5) -> List[str]:
        """根据部分输入建议值

        Args:
            category: 类别
            partial: 部分输入
            limit: 最大返回数

        Returns:
            建议列表
        """
        if category not in self._entries:
            return []

        all_values = list(self._entries[category].keys())

        # 前缀匹配
        prefix_matches = [v for v in all_values if v.startswith(partial.lower())]
        if prefix_matches:
            return prefix_matches[:limit]

        # 模糊匹配
        return get_close_matches(partial, all_values, n=limit, cutoff=0.4)

    def to_dict(self) -> Dict[str, List[str]]:
        """转换为字典

        Returns:
            {category: [values]}
        """
        return {
            cat: list(entries.keys())
            for cat, entries in self._entries.items()
        }

    @classmethod
    def from_sot_data(cls, sot_data) -> "DynamicWhitelist":
        """从 SoT 数据创建白名单

        Args:
            sot_data: LoadedSotData 实例

        Returns:
            DynamicWhitelist 实例
        """
        whitelist = cls()

        # 注册角色
        whitelist.register_bulk("role", sot_data.roles, source="MASTER.md")

        # 注册废弃角色
        for old, new in sot_data.legacy_mapping.items():
            whitelist.register(
                "role",
                old,
                deprecated=True,
                replacement=new,
                source="MASTER.md (deprecated)",
            )

        # 注册状态
        for table, states in sot_data.states.items():
            for state in states:
                whitelist.register("state", state, source=f"STATE_MACHINE.md#{table}")

        # 注册错误码
        whitelist.register_bulk("error_code", sot_data.error_codes, source="ERROR_CODES_SOT.md")

        # 注册字段
        for table, fields in sot_data.fields.items():
            for field_name in fields:
                whitelist.register("field", field_name, source=f"DATA_SCHEMA.md#{table}")

        return whitelist
