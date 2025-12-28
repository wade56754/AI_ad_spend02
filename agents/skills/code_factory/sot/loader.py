"""
SoT 动态加载器

基准文档: MASTER.md v4.6
版本: v4.2

功能:
- 从 SoT 文档动态加载角色、状态、字段白名单
- 支持版本校验
- 支持废弃角色映射
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Set, Optional, List
from datetime import datetime
import re

from .parser import SotParser


@dataclass
class LoadedSotData:
    """加载的 SoT 数据"""

    # 版本信息
    versions: Dict[str, str] = field(default_factory=dict)

    # 角色
    roles: Set[str] = field(default_factory=set)

    # 状态 (按表名分组)
    states: Dict[str, Set[str]] = field(default_factory=dict)

    # 错误码前缀
    error_codes: Set[str] = field(default_factory=set)

    # 字段定义 (按表名分组)
    fields: Dict[str, Set[str]] = field(default_factory=dict)

    # 废弃映射 (旧角色 -> 新角色)
    legacy_mapping: Dict[str, str] = field(default_factory=dict)

    # 加载时间
    loaded_at: datetime = field(default_factory=datetime.now)

    def is_valid_role(self, role: str) -> bool:
        """检查角色是否合法"""
        return role in self.roles

    def is_valid_state(self, state: str, table: Optional[str] = None) -> bool:
        """检查状态是否合法"""
        if table and table in self.states:
            return state in self.states[table]
        # 检查所有表
        return any(state in states for states in self.states.values())

    def map_legacy_role(self, role: str) -> Optional[str]:
        """映射废弃角色到新角色"""
        return self.legacy_mapping.get(role)


class SotLoader:
    """SoT 动态加载器"""

    # 期望的 SoT 文档版本
    EXPECTED_VERSIONS: Dict[str, str] = {
        "MASTER.md": "v4.6",
        "STATE_MACHINE.md": "v2.7",
        "DATA_SCHEMA.md": "v5.6",
    }

    def __init__(self, sot_dir: Path):
        """初始化加载器

        Args:
            sot_dir: SoT 文档目录 (docs/sot)
        """
        self.sot_dir = Path(sot_dir)
        self._parser = SotParser()
        self._cached_data: Optional[LoadedSotData] = None

    def load(self, force: bool = False) -> LoadedSotData:
        """加载 SoT 数据

        Args:
            force: 强制重新加载 (忽略缓存)

        Returns:
            LoadedSotData: 加载的数据
        """
        if self._cached_data and not force:
            return self._cached_data

        data = LoadedSotData()

        # 1. 加载版本信息
        for filename in self.EXPECTED_VERSIONS:
            path = self.sot_dir / filename
            if path.exists():
                data.versions[filename] = self._extract_version(path)

        # 2. 从 MASTER.md 加载角色
        master_path = self.sot_dir / "MASTER.md"
        if master_path.exists():
            data.roles = self._extract_roles(master_path)
            data.legacy_mapping = {"supervisor": "project_owner"}

        # 3. 从 STATE_MACHINE.md 加载状态
        sm_path = self.sot_dir / "STATE_MACHINE.md"
        if sm_path.exists():
            data.states["daily_report"] = self._extract_states(sm_path, "daily_report")
            data.states["topup_request"] = self._extract_states(sm_path, "topup")

        # 4. 从 ERROR_CODES_SOT.md 加载错误码
        error_path = self.sot_dir / "ERROR_CODES_SOT.md"
        if error_path.exists():
            data.error_codes = self._extract_error_codes(error_path)

        # 5. 从 DATA_SCHEMA.md 加载字段
        schema_path = self.sot_dir / "DATA_SCHEMA.md"
        if schema_path.exists():
            data.fields = self._extract_fields(schema_path)

        self._cached_data = data
        return data

    def _extract_version(self, path: Path) -> str:
        """从文件提取版本号"""
        try:
            content = path.read_text(encoding="utf-8")

            # 匹配多种版本格式
            patterns = [
                r"版本[：:]\s*v?([\d.]+)",
                r"\*\*版本\*\*[：:]\s*v?([\d.]+)",
                r"Version[：:]\s*v?([\d.]+)",
                r"^#.*v([\d.]+)",
            ]

            for pattern in patterns:
                if m := re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                    return f"v{m.group(1)}"

            return "unknown"
        except Exception:
            return "error"

    def _extract_roles(self, path: Path) -> Set[str]:
        """从 MASTER.md 提取角色"""
        try:
            content = path.read_text(encoding="utf-8")
            roles = set()

            # 匹配表格中的角色: | `ceo` | 或 | ceo |
            for m in re.finditer(r'\|\s*`?(\w+)`?\s*\|', content):
                name = m.group(1).lower()
                # 排除表头
                if name not in ("角色", "role", "说明", "description", "权限", "permission"):
                    roles.add(name)

            # 匹配列表中的角色: - `ceo` 或 - ceo:
            for m in re.finditer(r'^\s*[-*]\s*`?(\w+)`?[：:]', content, re.MULTILINE):
                name = m.group(1).lower()
                roles.add(name)

            return roles
        except Exception:
            return set()

    def _extract_states(self, path: Path, entity: str) -> Set[str]:
        """从 STATE_MACHINE.md 提取状态"""
        try:
            content = path.read_text(encoding="utf-8")
            states = set()

            # 匹配枚举定义: STATE = "value"
            for m in re.finditer(r'(\w+)\s*=\s*["\'](\w+)["\']', content):
                states.add(m.group(2))

            # 匹配状态表格: | raw_submitted |
            for m in re.finditer(r'\|\s*`?(\w+_\w+)`?\s*\|', content):
                state = m.group(1).lower()
                states.add(state)

            return states
        except Exception:
            return set()

    def _extract_error_codes(self, path: Path) -> Set[str]:
        """从 ERROR_CODES_SOT.md 提取错误码前缀"""
        try:
            content = path.read_text(encoding="utf-8")
            prefixes = set()

            # 匹配错误码: VAL-001, AUTH-002
            for m in re.finditer(r'([A-Z]+)-\d{3}', content):
                prefixes.add(m.group(1))

            return prefixes
        except Exception:
            return set()

    def _extract_fields(self, path: Path) -> Dict[str, Set[str]]:
        """从 DATA_SCHEMA.md 提取字段定义"""
        try:
            content = path.read_text(encoding="utf-8")
            fields: Dict[str, Set[str]] = {}

            current_table = None

            for line in content.split("\n"):
                # 匹配表名: ## daily_reports 或 ### `daily_reports`
                if m := re.match(r'^#{2,3}\s*`?(\w+)`?', line):
                    current_table = m.group(1).lower()
                    if current_table not in fields:
                        fields[current_table] = set()

                # 匹配字段: | id | 或 - `field_name`
                elif current_table:
                    if m := re.match(r'\|\s*`?(\w+)`?\s*\|', line):
                        field_name = m.group(1).lower()
                        if field_name not in ("字段", "field", "类型", "type", "说明"):
                            fields[current_table].add(field_name)

            return fields
        except Exception:
            return {}

    def verify_versions(self) -> List[str]:
        """验证 SoT 版本是否匹配

        Returns:
            List[str]: 不匹配的文件列表
        """
        data = self.load()
        mismatched = []

        for filename, expected in self.EXPECTED_VERSIONS.items():
            actual = data.versions.get(filename, "missing")
            if actual != expected:
                mismatched.append(f"{filename}: 期望 {expected}, 实际 {actual}")

        return mismatched

    def clear_cache(self):
        """清除缓存"""
        self._cached_data = None
