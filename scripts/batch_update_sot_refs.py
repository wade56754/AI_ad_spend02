#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch_update_sot_refs.py - SoT 版本引用批量更新脚本

用途：
    从 SOT_VERSIONS.yaml 读取目标版本，批量更新指定目录下所有
    Markdown 文件的 SoT 版本引用。

使用示例：
    # 预览变更（不实际修改）
    python scripts/batch_update_sot_refs.py --dry-run

    # 更新默认目录
    python scripts/batch_update_sot_refs.py

    # 更新指定目录
    python scripts/batch_update_sot_refs.py --dir docs/10.module-specs

    # 仅更新指定 SoT 文档的引用
    python scripts/batch_update_sot_refs.py --doc API_SOT.md

    # 生成变更报告
    python scripts/batch_update_sot_refs.py --report changes.json

退出码：
    0 - 更新成功
    1 - 更新失败
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
from datetime import datetime
from pathlib import Path
from typing import Optional

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
class FileChange:
    """文件变更记录"""
    file_path: str
    changes: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "file": self.file_path,
            "change_count": len(self.changes),
            "changes": self.changes
        }


@dataclass
class UpdateResult:
    """更新结果"""
    files_scanned: int = 0
    files_modified: int = 0
    total_changes: int = 0
    file_changes: list[FileChange] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    dry_run: bool = False

    @property
    def is_success(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> dict:
        return {
            "success": self.is_success,
            "dry_run": self.dry_run,
            "timestamp": datetime.now().isoformat(),
            "files_scanned": self.files_scanned,
            "files_modified": self.files_modified,
            "total_changes": self.total_changes,
            "file_changes": [fc.to_dict() for fc in self.file_changes],
            "errors": self.errors
        }


# =============================================================================
# 核心更新逻辑
# =============================================================================

class SoTVersionUpdater:
    """SoT 版本更新器"""

    def __init__(self, config_path: Path):
        """
        初始化更新器

        Args:
            config_path: SOT_VERSIONS.yaml 文件路径
        """
        self.config_path = config_path
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
            key = doc_name.upper()  # 保留 .md 后缀
            self.sot_versions[key] = doc_info.get('version', '')

        # 加载排除目录
        scan_config = config.get('scan_directories', {})
        self.exclude_dirs = set(scan_config.get('exclude', []))

    def _create_pattern(self, doc_name: str) -> re.Pattern:
        """
        为指定文档创建匹配模式

        Args:
            doc_name: 文档名称（如 API_SOT.md）

        Returns:
            编译后的正则表达式
        """
        base_name = doc_name.replace('.md', '').replace('.MD', '')
        # 匹配 DOCUMENT.md v1.2 或 DOCUMENT.md v1.2.3
        pattern = rf'({re.escape(base_name)}\.md\s+v)(\d+\.\d+(?:\.\d+)?)'
        return re.compile(pattern, re.IGNORECASE)

    def update_file(
        self,
        file_path: Path,
        target_docs: Optional[list[str]] = None,
        dry_run: bool = False
    ) -> FileChange:
        """
        更新单个文件中的 SoT 版本引用

        Args:
            file_path: 要更新的文件路径
            target_docs: 要更新的 SoT 文档列表（None 表示全部）
            dry_run: 是否为预览模式

        Returns:
            文件变更记录
        """
        file_change = FileChange(file_path=str(file_path))

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                original_content = content
        except Exception as e:
            return file_change

        # 确定要更新的文档
        docs_to_update = target_docs if target_docs else list(self.sot_versions.keys())

        # 逐个文档进行替换
        for doc_name in docs_to_update:
            doc_key = doc_name.upper()
            if doc_key not in self.sot_versions:
                continue

            target_version = self.sot_versions[doc_key]
            # 提取版本号（去掉 v 前缀）
            version_num = target_version.lstrip('v')

            pattern = self._create_pattern(doc_name)

            def replace_version(match):
                old_version = match.group(2)
                if old_version != version_num:
                    file_change.changes.append({
                        "document": doc_name,
                        "old_version": f"v{old_version}",
                        "new_version": target_version,
                        "matched": match.group(0)
                    })
                    return f"{match.group(1)}{version_num}"
                return match.group(0)

            content = pattern.sub(replace_version, content)

        # 写入文件（如果有变更且不是 dry-run）
        if file_change.changes and not dry_run:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                file_change.changes = []  # 清空变更记录

        return file_change

    def update_directory(
        self,
        dir_path: Path,
        target_docs: Optional[list[str]] = None,
        dry_run: bool = False
    ) -> UpdateResult:
        """
        更新目录下所有 Markdown 文件

        Args:
            dir_path: 要更新的目录路径
            target_docs: 要更新的 SoT 文档列表（None 表示全部）
            dry_run: 是否为预览模式

        Returns:
            更新结果
        """
        result = UpdateResult(dry_run=dry_run)

        if not dir_path.exists():
            result.errors.append(f"目录不存在: {dir_path}")
            return result

        # 收集所有 Markdown 文件
        md_files = []
        for md_file in dir_path.rglob('*.md'):
            should_exclude = False
            for exclude_dir in self.exclude_dirs:
                if exclude_dir in str(md_file):
                    should_exclude = True
                    break

            if not should_exclude:
                md_files.append(md_file)

        result.files_scanned = len(md_files)

        # 更新每个文件
        for md_file in md_files:
            file_change = self.update_file(md_file, target_docs, dry_run)

            if file_change.changes:
                result.files_modified += 1
                result.total_changes += len(file_change.changes)
                result.file_changes.append(file_change)

        return result

    def format_report(self, result: UpdateResult, format_type: str = 'text') -> str:
        """
        格式化更新报告

        Args:
            result: 更新结果
            format_type: 输出格式 ('text' 或 'json')

        Returns:
            格式化后的报告字符串
        """
        if format_type == 'json':
            return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)

        # 文本格式报告
        lines = []
        lines.append("=" * 70)
        lines.append("SoT 版本引用批量更新报告")
        lines.append("=" * 70)
        lines.append("")

        if result.dry_run:
            lines.append("\033[33m[预览模式] 以下变更未实际应用\033[0m")
            lines.append("")

        lines.append(f"扫描文件数: {result.files_scanned}")
        lines.append(f"修改文件数: {result.files_modified}")
        lines.append(f"总变更数:   {result.total_changes}")
        lines.append("")

        if result.file_changes:
            lines.append("-" * 70)
            lines.append("变更详情:")
            lines.append("-" * 70)

            for fc in result.file_changes:
                lines.append(f"\n\033[36m{fc.file_path}\033[0m")
                for change in fc.changes:
                    lines.append(
                        f"  - {change['document']}: "
                        f"{change['old_version']} → {change['new_version']}"
                    )

        if result.errors:
            lines.append("-" * 70)
            lines.append("错误:")
            lines.append("-" * 70)
            for error in result.errors:
                lines.append(f"  - {error}")

        lines.append("")
        lines.append("=" * 70)

        if result.is_success:
            if result.dry_run:
                lines.append(f"\033[32m完成\033[0m - 预览 {result.total_changes} 处变更")
                lines.append("")
                lines.append("确认无误后，移除 --dry-run 参数以应用变更")
            else:
                lines.append(f"\033[32m完成\033[0m - 已更新 {result.total_changes} 处引用")
        else:
            lines.append(f"\033[31m失败\033[0m - 发生 {len(result.errors)} 个错误")

        lines.append("=" * 70)

        return "\n".join(lines)


# =============================================================================
# 命令行入口
# =============================================================================

def main() -> int:
    """主函数"""
    parser = argparse.ArgumentParser(
        description="批量更新 SoT 版本引用",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --dry-run                    # 预览变更
  %(prog)s                              # 更新默认目录
  %(prog)s --dir docs/10.module-specs   # 更新指定目录
  %(prog)s --doc API_SOT.md             # 仅更新指定文档的引用
  %(prog)s --report changes.json        # 生成 JSON 报告
        """
    )

    parser.add_argument(
        '--dir', '-d',
        type=Path,
        default=Path('docs'),
        help='要更新的目录 (默认: docs)'
    )

    parser.add_argument(
        '--config', '-c',
        type=Path,
        default=Path('docs/SOT_VERSIONS.yaml'),
        help='配置文件路径 (默认: docs/SOT_VERSIONS.yaml)'
    )

    parser.add_argument(
        '--doc',
        type=str,
        action='append',
        dest='docs',
        help='指定要更新的 SoT 文档（可多次使用）'
    )

    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='预览模式（不实际修改文件）'
    )

    parser.add_argument(
        '--report', '-r',
        type=Path,
        help='保存 JSON 格式报告到指定文件'
    )

    parser.add_argument(
        '--format', '-f',
        choices=['text', 'json'],
        default='text',
        help='输出格式 (默认: text)'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='静默模式（仅输出错误）'
    )

    args = parser.parse_args()

    try:
        # 创建更新器
        updater = SoTVersionUpdater(args.config)

        # 执行更新
        result = updater.update_directory(
            args.dir,
            target_docs=args.docs,
            dry_run=args.dry_run
        )

        # 输出报告
        if not args.quiet:
            report = updater.format_report(result, args.format)
            print(report)

        # 保存 JSON 报告
        if args.report:
            with open(args.report, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"\n报告已保存到: {args.report}")

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
