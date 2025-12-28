#!/usr/bin/env python3
"""
检查CHANGELOG是否已更新

门禁规则：
- docs/sot/CHANGELOG.md 必须有新增条目
- 条目必须在 [Unreleased] 区域或对应版本下
- 条目应包含PR编号（可选但推荐）

用法:
    python scripts/check_changelog.py
    python scripts/check_changelog.py --base main  # 与main分支对比
"""

import subprocess
import sys
import re
from pathlib import Path


def get_changelog_path() -> Path:
    """获取CHANGELOG路径"""
    paths = [
        Path("docs/sot/CHANGELOG.md"),
        Path("CHANGELOG.md"),
        Path("docs/CHANGELOG.md"),
    ]
    for p in paths:
        if p.exists():
            return p
    return paths[0]  # 返回首选路径，即使不存在


def get_base_branch() -> str:
    """获取基准分支"""
    for arg in sys.argv:
        if arg.startswith("--base="):
            return arg.split("=")[1]
        if arg == "--base" and sys.argv.index(arg) + 1 < len(sys.argv):
            return sys.argv[sys.argv.index(arg) + 1]
    return "main"


def get_changelog_diff(changelog_path: Path, base_branch: str) -> str:
    """获取CHANGELOG的diff"""
    try:
        result = subprocess.run(
            ["git", "diff", f"{base_branch}...HEAD", "--", str(changelog_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        # 可能是新文件，尝试获取全部内容
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--", str(changelog_path)],
                capture_output=True,
                text=True,
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return ""


def check_changelog_updated(diff: str) -> tuple[bool, list[str]]:
    """检查CHANGELOG是否有新增内容"""
    if not diff:
        return False, ["无diff内容"]
    
    # 查找新增行（以+开头，但不是+++）
    added_lines = []
    for line in diff.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            content = line[1:].strip()
            if content and not content.startswith("#"):  # 忽略空行和标题行
                added_lines.append(content)
    
    return len(added_lines) > 0, added_lines


def check_format(changelog_path: Path) -> list[str]:
    """检查CHANGELOG格式"""
    if not changelog_path.exists():
        return ["CHANGELOG文件不存在"]
    
    content = changelog_path.read_text(encoding="utf-8")
    issues = []
    
    # 检查是否有 [Unreleased] 区域
    if "[Unreleased]" not in content:
        issues.append("缺少 [Unreleased] 区域")
    
    # 检查版本号格式 [x.x.x]
    version_pattern = r"\[(\d+\.\d+\.\d+)\]"
    if not re.search(version_pattern, content):
        issues.append("缺少版本号条目（格式: [x.x.x]）")
    
    return issues


def main():
    print("=" * 60)
    print("  CHANGELOG 更新检查")
    print("=" * 60)
    print()
    
    changelog_path = get_changelog_path()
    base_branch = get_base_branch()
    
    print(f"CHANGELOG路径: {changelog_path}")
    print(f"基准分支: {base_branch}")
    print()
    
    # 检查文件是否存在
    if not changelog_path.exists():
        print(f"❌ CHANGELOG文件不存在: {changelog_path}")
        print()
        print("解决方案:")
        print(f"  创建 {changelog_path} 文件")
        sys.exit(1)
    
    # 检查格式
    format_issues = check_format(changelog_path)
    if format_issues:
        print("⚠️ 格式问题:")
        for issue in format_issues:
            print(f"   - {issue}")
        print()
    
    # 检查是否有更新
    diff = get_changelog_diff(changelog_path, base_branch)
    updated, added_lines = check_changelog_updated(diff)
    
    if updated:
        print("✅ CHANGELOG已更新")
        print()
        print("新增条目预览:")
        for line in added_lines[:5]:  # 只显示前5行
            print(f"   + {line[:60]}{'...' if len(line) > 60 else ''}")
        if len(added_lines) > 5:
            print(f"   ... 还有 {len(added_lines) - 5} 行")
        print()
        
        # 检查是否包含PR编号（推荐但不强制）
        has_pr = any(re.search(r"#\d+", line) for line in added_lines)
        if not has_pr:
            print("💡 建议: 添加PR编号引用（如 #123）")
        
        sys.exit(0)
    else:
        print("❌ CHANGELOG未更新")
        print()
        print("解决方案:")
        print(f"  1. 编辑 {changelog_path}")
        print("  2. 在 [Unreleased] 区域添加变更说明")
        print("  3. 格式示例:")
        print()
        print("     ## [Unreleased]")
        print("     ### 新增")
        print("     - 功能描述 (#PR编号)")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
