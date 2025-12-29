"""
SoT 文档解析器

基准文档: MASTER.md v4.6
版本: v4.2

功能:
- 解析 Markdown 表格
- 提取结构化数据
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
import re


@dataclass
class TableRow:
    """表格行"""
    cells: List[str] = field(default_factory=list)

    def get(self, index: int, default: str = "") -> str:
        """获取指定列的值"""
        if 0 <= index < len(self.cells):
            return self.cells[index].strip()
        return default


@dataclass
class ParsedTable:
    """解析后的表格"""
    headers: List[str] = field(default_factory=list)
    rows: List[TableRow] = field(default_factory=list)

    def to_dicts(self) -> List[Dict[str, str]]:
        """转换为字典列表"""
        return [
            {h: row.get(i) for i, h in enumerate(self.headers)}
            for row in self.rows
        ]

    def get_column(self, header: str) -> List[str]:
        """获取指定列的所有值"""
        if header not in self.headers:
            return []
        idx = self.headers.index(header)
        return [row.get(idx) for row in self.rows]


class SotParser:
    """SoT 文档解析器"""

    def parse_file(self, path: Path) -> Dict[str, Any]:
        """解析文件

        Args:
            path: 文件路径

        Returns:
            解析结果
        """
        content = path.read_text(encoding="utf-8")
        return self.parse_content(content)

    def parse_content(self, content: str) -> Dict[str, Any]:
        """解析内容

        Args:
            content: Markdown 内容

        Returns:
            解析结果
        """
        result = {
            "version": self._extract_version(content),
            "title": self._extract_title(content),
            "sections": self._extract_sections(content),
            "tables": self._extract_tables(content),
        }
        return result

    def _extract_version(self, content: str) -> Optional[str]:
        """提取版本号"""
        patterns = [
            r"版本[：:]\s*v?([\d.]+)",
            r"\*\*版本\*\*[：:]\s*v?([\d.]+)",
            r"Version[：:]\s*v?([\d.]+)",
        ]

        for pattern in patterns:
            if m := re.search(pattern, content, re.IGNORECASE):
                return f"v{m.group(1)}"
        return None

    def _extract_title(self, content: str) -> Optional[str]:
        """提取标题"""
        if m := re.match(r'^#\s+(.+)$', content, re.MULTILINE):
            return m.group(1).strip()
        return None

    def _extract_sections(self, content: str) -> Dict[str, str]:
        """提取章节"""
        sections = {}
        current_section = None
        current_content = []

        for line in content.split("\n"):
            if m := re.match(r'^(#{2,3})\s+(.+)$', line):
                if current_section:
                    sections[current_section] = "\n".join(current_content)
                current_section = m.group(2).strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        if current_section:
            sections[current_section] = "\n".join(current_content)

        return sections

    def _extract_tables(self, content: str) -> List[ParsedTable]:
        """提取所有表格"""
        tables = []
        lines = content.split("\n")

        i = 0
        while i < len(lines):
            # 检测表格开始 (以 | 开头)
            if lines[i].strip().startswith("|") and "---" not in lines[i]:
                table = self._parse_table(lines, i)
                if table:
                    tables.append(table)
                    # 跳过已解析的行
                    i += len(table.rows) + 2  # header + separator + rows
                    continue
            i += 1

        return tables

    def _parse_table(self, lines: List[str], start: int) -> Optional[ParsedTable]:
        """解析单个表格"""
        if start >= len(lines):
            return None

        # 解析表头
        header_line = lines[start].strip()
        if not header_line.startswith("|"):
            return None

        headers = self._parse_row(header_line)
        if not headers:
            return None

        # 跳过分隔行
        if start + 1 >= len(lines):
            return None
        separator = lines[start + 1].strip()
        if "---" not in separator:
            return None

        # 解析数据行
        rows = []
        i = start + 2
        while i < len(lines):
            line = lines[i].strip()
            if not line.startswith("|"):
                break
            cells = self._parse_row(line)
            if cells:
                rows.append(TableRow(cells=cells))
            i += 1

        return ParsedTable(headers=headers, rows=rows)

    def _parse_row(self, line: str) -> List[str]:
        """解析表格行"""
        # 移除首尾的 |
        line = line.strip()
        if line.startswith("|"):
            line = line[1:]
        if line.endswith("|"):
            line = line[:-1]

        # 分割并清理
        cells = [cell.strip().strip("`") for cell in line.split("|")]
        return cells

    def extract_enum_values(self, content: str, enum_name: str) -> List[str]:
        """提取枚举值

        Args:
            content: 内容
            enum_name: 枚举名称

        Returns:
            枚举值列表
        """
        values = []

        # 匹配 Python 枚举定义
        pattern = rf'class\s+{enum_name}.*?(?=class|\Z)'
        if m := re.search(pattern, content, re.DOTALL):
            enum_content = m.group(0)
            for m2 in re.finditer(r'(\w+)\s*=\s*["\']([^"\']+)["\']', enum_content):
                values.append(m2.group(2))

        return values
