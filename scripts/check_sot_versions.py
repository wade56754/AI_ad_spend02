#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_sot_versions.py - SoT 版本一致性检查脚本

用途：
    扫描指定目录下的 Markdown 文件，检测 SoT 版本引用是否与
    SOT_VERSIONS.yaml 中定义的版本一致。

使用示例：
    # 检查默认目录
    python scripts/check_sot_versions.py

    # 检查指定目录
    python scripts/check_sot_versions.py --dir docs/10.module-specs

    # 输出 JSON 格式报告
    python scripts/check_sot_versions.py --format json

    # CI 模式（不输出颜色）
    python scripts/check_sot_versions.py --ci

退出码：
    0 - 所有版本引用一致
    1 - 发现版本不一致
    2 - 配置文件或参数错误

作者：AI 广告代投系统开发团队
版本：1.0.0
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# 尝试导入 PyYAML，如果不存在则提供安装提示
try:
    import yaml
except ImportError:
    print("错误: 需要安装 PyYAML 库")
    print("请运行: pip install pyyaml")
    sys.exit(2)


# =============================================================================
# 数据结构
# =============================================================================

@dataclass
class VersionMismatch:
    """版本不匹配记录"""
    file_path: str
    line_number: int
    sot_document: str
    expected_version: str
    actual_version: str
    line_content: str

    def to_dict(self) -> dict:
        return {
            "file": self.file_path,
            "line": self.line_number,
            "document": self.sot_document,
            "expected": self.expected_version,
            "actual": self.actual_version,
            "content": self.line_content.strip()
        }


@dataclass
class CheckResult:
    """检查结果"""
    total_files: int = 0
    files_checked: int = 0
    references_found: int = 0
    mismatches: list[VersionMismatch] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def is_success(self) -> bool:
        return len(self.mismatches) == 0 and len(self.errors) == 0

    def to_dict(self) -> dict:
        return {
            "success": self.is_success,
            "total_files": self.total_files,
            "files_checked": self.files_checked,
            "references_found": self.references_found,
            "mismatch_count": len(self.mismatches),
            "mismatches": [m.to_dict() for m in self.mismatches],
            "errors": self.errors
        }


# =============================================================================
# 核心检查逻辑
# =============================================================================

class SoTVersionChecker:
    """SoT 版本检查器"""

    # 匹配 SoT 版本引用的正则表达式模式
    PATTERNS = [
        # 模式 1: DOCUMENT.md v1.2.3
        re.compile(
            r'(?P<doc_name>MASTER|STATE_MACHINE|DATA_SCHEMA|LEDGER_SOT|'
            r'BUSINESS_RULES|API_SOT|ERROR_CODES_SOT|AUTH_SPEC|'
            r'BUSINESS_FLOW_MANAGEMENT|MVP_PHASE_DESIGN)\.md\s+'
            r'v(?P<version>\d+\.\d+(?:\.\d+)?)',
            re.IGNORECASE
        ),
        # 模式 2: 表格中 | DOCUMENT.md | v1.2 |
        re.compile(
            r'\|\s*(?P<doc_name>MASTER|STATE_MACHINE|DATA_SCHEMA|LEDGER_SOT|'
            r'BUSINESS_RULES|API_SOT|ERROR_CODES_SOT|AUTH_SPEC|'
            r'BUSINESS_FLOW_MANAGEMENT|MVP_PHASE_DESIGN)\.md\s*\|\s*'
            r'v(?P<version>\d+\.\d+(?:\.\d+)?)\s*\|',
            re.IGNORECASE
        ),
    ]

    def __init__(self, config_path: Path, ci_mode: bool = False):
        """
        初始化检查器

        Args:
            config_path: SOT_VERSIONS.yaml 文件路径
            ci_mode: 是否为 CI 模式（禁用颜色输出）
        """
        self.config_path = config_path
        self.ci_mode = ci_mode
        self.sot_versions: dict[str, str] = {}
        self.exclude_dirs: set[str] = set()
        self._load_config()

    def _load_config(self) -> None:
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 加载 SoT 版本
        sot_docs = config.get('sot_documents', {})
        for doc_name, doc_info in sot_docs.items():
            # 标准化文档名（去掉 .md 后缀用于匹配）
            key = doc_name.replace('.md', '').upper()
            self.sot_versions[key] = doc_info.get('version', '')

        # 加载排除目录
        scan_config = config.get('scan_directories', {})
        self.exclude_dirs = set(scan_config.get('exclude', []))

    def check_file(self, file_path: Path) -> list[VersionMismatch]:
        """
        检查单个文件中的 SoT 版本引用

        Args:
            file_path: 要检查的文件路径

        Returns:
            版本不匹配列表
        """
        mismatches = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            return mismatches  # 跳过无法读取的文件

        for line_num, line in enumerate(lines, start=1):
            for pattern in self.PATTERNS:
                for match in pattern.finditer(line):
                    doc_name = match.group('doc_name').upper()
                    actual_version = f"v{match.group('version')}"

                    expected_version = self.sot_versions.get(doc_name)
                    if expected_version and actual_version != expected_version:
                        mismatches.append(VersionMismatch(
                            file_path=str(file_path),
                            line_number=line_num,
                            sot_document=f"{doc_name}.md",
                            expected_version=expected_version,
                            actual_version=actual_version,
                            line_content=line
                        ))

        return mismatches

    def check_directory(self, dir_path: Path) -> CheckResult:
        """
        检查目录下所有 Markdown 文件

        Args:
            dir_path: 要检查的目录路径

        Returns:
            检查结果
        """
        result = CheckResult()

        if not dir_path.exists():
            result.errors.append(f"目录不存在: {dir_path}")
            return result

        # 收集所有 Markdown 文件
        md_files = []
        for md_file in dir_path.rglob('*.md'):
            # 检查是否在排除目录中
            should_exclude = False
            for exclude_dir in self.exclude_dirs:
                if exclude_dir in str(md_file):
                    should_exclude = True
                    break

            if not should_exclude:
                md_files.append(md_file)

        result.total_files = len(md_files)

        # 检查每个文件
        for md_file in md_files:
            result.files_checked += 1
            file_mismatches = self.check_file(md_file)
            result.references_found += len(file_mismatches) + sum(
                1 for pattern in self.PATTERNS
                for _ in pattern.finditer(md_file.read_text(encoding='utf-8', errors='ignore'))
            )
            result.mismatches.extend(file_mismatches)

        return result

    def format_report(self, result: CheckResult, format_type: str = 'text') -> str:
        """
        格式化检查报告

        Args:
            result: 检查结果
            format_type: 输出格式 ('text' 或 'json')

        Returns:
            格式化后的报告字符串
        """
        if format_type == 'json':
            return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)

        # 文本格式报告
        lines = []
        lines.append("=" * 70)
        lines.append("SoT 版本一致性检查报告")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"检查文件数: {result.files_checked}/{result.total_files}")
        lines.append(f"版本引用数: {result.references_found}")
        lines.append(f"不一致数量: {len(result.mismatches)}")
        lines.append("")

        if result.mismatches:
            lines.append("-" * 70)
            lines.append("版本不一致详情:")
            lines.append("-" * 70)

            for mismatch in result.mismatches:
                if self.ci_mode:
                    lines.append(f"\n文件: {mismatch.file_path}:{mismatch.line_number}")
                else:
                    lines.append(f"\n\033[33m文件:\033[0m {mismatch.file_path}:{mismatch.line_number}")

                lines.append(f"  文档: {mismatch.sot_document}")
                lines.append(f"  期望: {mismatch.expected_version}")
                lines.append(f"  实际: {mismatch.actual_version}")
                lines.append(f"  内容: {mismatch.line_content.strip()[:80]}...")

        if result.errors:
            lines.append("-" * 70)
            lines.append("错误:")
            lines.append("-" * 70)
            for error in result.errors:
                lines.append(f"  - {error}")

        lines.append("")
        lines.append("=" * 70)

        if result.is_success:
            status = "PASS" if self.ci_mode else "\033[32mPASS\033[0m"
            lines.append(f"状态: {status} - 所有 SoT 版本引用一致")
        else:
            status = "FAIL" if self.ci_mode else "\033[31mFAIL\033[0m"
            lines.append(f"状态: {status} - 发现 {len(result.mismatches)} 处版本不一致")
            lines.append("")
            lines.append("修复建议: 运行 scripts/batch_update_sot_refs.py 自动修复")

        lines.append("=" * 70)

        return "\n".join(lines)


# =============================================================================
# 命令行入口
# =============================================================================

def main() -> int:
    """主函数"""
    parser = argparse.ArgumentParser(
        description="检查 SoT 版本引用一致性",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                              # 检查默认目录
  %(prog)s --dir docs/10.module-specs   # 检查指定目录
  %(prog)s --format json                # 输出 JSON 格式
  %(prog)s --ci                         # CI 模式（无颜色）
        """
    )

    parser.add_argument(
        '--dir', '-d',
        type=Path,
        default=Path('docs'),
        help='要检查的目录 (默认: docs)'
    )

    parser.add_argument(
        '--config', '-c',
        type=Path,
        default=Path('docs/SOT_VERSIONS.yaml'),
        help='配置文件路径 (默认: docs/SOT_VERSIONS.yaml)'
    )

    parser.add_argument(
        '--format', '-f',
        choices=['text', 'json'],
        default='text',
        help='输出格式 (默认: text)'
    )

    parser.add_argument(
        '--ci',
        action='store_true',
        help='CI 模式（禁用颜色输出）'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='静默模式（仅输出错误）'
    )

    args = parser.parse_args()

    try:
        # 创建检查器
        checker = SoTVersionChecker(args.config, ci_mode=args.ci)

        # 执行检查
        result = checker.check_directory(args.dir)

        # 输出报告
        if not args.quiet or not result.is_success:
            report = checker.format_report(result, args.format)
            print(report)

        # 返回退出码
        return 0 if result.is_success else 1

    except FileNotFoundError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 2
    except yaml.YAMLError as e:
        print(f"配置文件解析错误: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"未知错误: {e}", file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
