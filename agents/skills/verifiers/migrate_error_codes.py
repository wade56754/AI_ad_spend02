"""
批量迁移错误码脚本
Version: 1.0
Author: Claude协作开发

功能:
- 扫描后端代码中的非标准错误码
- 按照迁移映射表批量替换
- 生成迁移报告
"""

import sys
import io
import re
from pathlib import Path
from typing import List, Tuple, Dict, Set

# 设置 stdout 编码为 utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.core.error_code_migration import (
    ERROR_CODE_MIGRATION_MAP,
    DEPRECATED_ERROR_CODES,
    is_standard_error_code,
)


def find_error_codes_in_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    在文件中查找所有错误码

    Returns:
        列表 [(行号, 错误码, 整行内容), ...]
    """
    results = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # 尝试其他编码
        try:
            content = file_path.read_text(encoding="gbk")
        except UnicodeDecodeError:
            print(f"  [WARN] 无法读取文件 (编码问题): {file_path}")
            return results

    # 匹配错误码模式: "XXX_NNN" 或 'XXX_NNN' 或 "XXX-NNN"
    pattern = r'["\']([A-Z]+[_-]\d+|\w+_ERROR)["\']'

    for line_no, line in enumerate(content.split('\n'), 1):
        matches = re.findall(pattern, line)
        for match in matches:
            # 跳过明显非错误码的匹配 (如 ACC_001 是账户ID)
            if match.startswith("ACC_"):
                continue
            results.append((line_no, match, line.strip()))

    return results


def scan_non_standard_codes(directory: Path) -> Dict[str, List[Tuple[Path, int, str]]]:
    """
    扫描目录中所有非标准错误码

    Returns:
        字典 {错误码: [(文件路径, 行号, 整行内容), ...]}
    """
    non_standard: Dict[str, List[Tuple[Path, int, str]]] = {}

    # 扫描 Python 文件
    for py_file in directory.rglob("*.py"):
        # 跳过测试文件和迁移文件本身
        if "test" in py_file.name.lower() or "migration" in py_file.name.lower():
            continue
        # 跳过 __pycache__
        if "__pycache__" in str(py_file):
            continue

        codes = find_error_codes_in_file(py_file)
        for line_no, code, line in codes:
            # 检查是否为需要迁移的错误码
            if code in DEPRECATED_ERROR_CODES or code in ERROR_CODE_MIGRATION_MAP:
                if code not in non_standard:
                    non_standard[code] = []
                non_standard[code].append((py_file, line_no, line))

    return non_standard


def migrate_file(file_path: Path, dry_run: bool = True) -> Tuple[int, List[str]]:
    """
    迁移单个文件中的错误码

    Args:
        file_path: 文件路径
        dry_run: 是否仅预演 (不实际修改)

    Returns:
        (修复数量, 修复详情列表)
    """
    encoding = "utf-8"
    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            content = file_path.read_text(encoding="gbk")
            encoding = "gbk"
        except UnicodeDecodeError:
            return 0, []

    original_content = content
    fixes = []

    for old_code, new_code in ERROR_CODE_MIGRATION_MAP.items():
        if old_code == new_code:
            continue

        # 替换双引号格式
        pattern_double = f'"{old_code}"'
        replacement_double = f'"{new_code}"'
        if pattern_double in content:
            count = content.count(pattern_double)
            content = content.replace(pattern_double, replacement_double)
            fixes.append(f'  "{old_code}" → "{new_code}" ({count}处)')

        # 替换单引号格式
        pattern_single = f"'{old_code}'"
        replacement_single = f"'{new_code}'"
        if pattern_single in content:
            count = content.count(pattern_single)
            content = content.replace(pattern_single, replacement_single)
            fixes.append(f"  '{old_code}' → '{new_code}' ({count}处)")

    if content != original_content and not dry_run:
        file_path.write_text(content, encoding=encoding)

    return len(fixes), fixes


def run_migration(dry_run: bool = True) -> Dict[str, any]:
    """
    执行错误码迁移

    Args:
        dry_run: 是否仅预演

    Returns:
        迁移报告
    """
    backend_dir = project_root / "backend"

    print()
    print("=" * 70)
    print(f" 错误码迁移 {'(预演模式)' if dry_run else '(实际执行)'} ".center(70, "="))
    print("=" * 70)
    print()

    # 1. 扫描非标准错误码
    print("步骤 1: 扫描非标准错误码...")
    non_standard = scan_non_standard_codes(backend_dir)

    print(f"发现 {len(non_standard)} 种非标准错误码:")
    for code, locations in sorted(non_standard.items()):
        print(f"  - {code}: {len(locations)} 处")
    print()

    # 2. 执行迁移
    print(f"步骤 2: {'预演' if dry_run else '执行'}迁移...")
    total_files = 0
    total_fixes = 0
    file_fixes: Dict[str, List[str]] = {}

    for py_file in backend_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        # 跳过迁移脚本自身
        if "migrate_error_codes" in py_file.name:
            continue
        # 跳过 error_code_migration.py (映射表文件)
        if "error_code_migration" in py_file.name:
            continue
        # 跳过 error_codes.py (错误码定义文件)
        if py_file.name == "error_codes.py":
            continue

        fixes_count, fixes = migrate_file(py_file, dry_run)
        if fixes_count > 0:
            total_files += 1
            total_fixes += fixes_count
            relative_path = py_file.relative_to(project_root)
            file_fixes[str(relative_path)] = fixes

    print()
    print("-" * 70)
    print("迁移结果:")
    print("-" * 70)
    for file_path, fixes in sorted(file_fixes.items()):
        print(f"\n[{file_path}]")
        for fix in fixes:
            print(fix)

    print()
    print("=" * 70)
    print(f" 总计: {total_files} 个文件, {total_fixes} 处{'可修复' if dry_run else '已修复'} ".center(70, "="))
    print("=" * 70)

    return {
        "dry_run": dry_run,
        "non_standard_codes": len(non_standard),
        "files_affected": total_files,
        "total_fixes": total_fixes,
        "file_fixes": file_fixes,
    }


def generate_migration_report() -> str:
    """生成迁移报告 Markdown"""
    backend_dir = project_root / "backend"
    non_standard = scan_non_standard_codes(backend_dir)

    report = []
    report.append("# 错误码迁移报告")
    report.append("")
    report.append("## 扫描结果")
    report.append("")
    report.append(f"扫描目录: `backend/`")
    report.append(f"发现非标准错误码: {len(non_standard)} 种")
    report.append("")

    if non_standard:
        report.append("## 非标准错误码清单")
        report.append("")
        report.append("| 错误码 | 出现次数 | 建议迁移为 | 文件列表 |")
        report.append("|--------|----------|------------|----------|")

        for code, locations in sorted(non_standard.items()):
            new_code = ERROR_CODE_MIGRATION_MAP.get(code, "N/A")
            files = ", ".join(set(str(loc[0].relative_to(project_root)) for loc in locations[:3]))
            if len(locations) > 3:
                files += f" (+{len(locations) - 3} more)"
            report.append(f"| `{code}` | {len(locations)} | `{new_code}` | {files} |")

        report.append("")

    report.append("## 迁移映射表")
    report.append("")
    report.append("| 旧错误码 | 新标准错误码 | 说明 |")
    report.append("|----------|--------------|------|")
    for old, new in sorted(ERROR_CODE_MIGRATION_MAP.items()):
        if old != new:
            report.append(f"| `{old}` | `{new}` | - |")

    report.append("")
    report.append("## 执行迁移")
    report.append("")
    report.append("```bash")
    report.append("# 预演模式 (仅显示将要修改的内容)")
    report.append("python agents/skills/verifiers/migrate_error_codes.py --dry-run")
    report.append("")
    report.append("# 实际执行")
    report.append("python agents/skills/verifiers/migrate_error_codes.py --apply")
    report.append("```")

    return "\n".join(report)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="错误码迁移工具")
    parser.add_argument("--dry-run", action="store_true", help="仅预演，不实际修改文件")
    parser.add_argument("--apply", action="store_true", help="实际执行迁移")
    parser.add_argument("--report", action="store_true", help="生成迁移报告")

    args = parser.parse_args()

    if args.report:
        report = generate_migration_report()
        print(report)
    elif args.apply:
        run_migration(dry_run=False)
    else:
        # 默认预演模式
        run_migration(dry_run=True)
