#!/usr/bin/env python3
"""
检查数据库迁移是否可回滚

门禁规则：
- 每个migration必须有downgrade函数
- 或者在 migrations/EXEMPTIONS.md 中有豁免记录

用法:
    python scripts/check_migration.py
    python scripts/check_migration.py --strict  # 严格模式，不允许豁免
"""

import os
import re
import sys
from pathlib import Path


def find_migration_files(migrations_dir: str = "backend/alembic/versions") -> list[Path]:
    """查找所有迁移文件"""
    path = Path(migrations_dir)
    if not path.exists():
        # 尝试其他可能的路径
        alt_paths = [
            Path("alembic/versions"),
            Path("migrations/versions"),
            Path("backend/migrations/versions"),
        ]
        for alt in alt_paths:
            if alt.exists():
                path = alt
                break
        else:
            print(f"⚠️ 未找到迁移目录，已检查: {migrations_dir} 和备选路径")
            return []
    
    return list(path.glob("*.py"))


def check_downgrade(file_path: Path) -> tuple[bool, str]:
    """检查迁移文件是否有downgrade函数"""
    content = file_path.read_text(encoding="utf-8")
    
    # 检查是否有downgrade函数
    if "def downgrade(" not in content:
        return False, "缺少 downgrade() 函数"
    
    # 检查downgrade是否为空（只有pass）
    downgrade_match = re.search(
        r"def downgrade\(\)[^:]*:\s*\n((?:\s+.*\n)*)",
        content
    )
    if downgrade_match:
        body = downgrade_match.group(1).strip()
        if body == "pass" or body == "":
            return False, "downgrade() 函数为空"
    
    return True, "OK"


def load_exemptions(exemptions_file: str = "migrations/EXEMPTIONS.md") -> set[str]:
    """加载豁免列表"""
    path = Path(exemptions_file)
    if not path.exists():
        # 尝试其他可能的路径
        alt_paths = [
            Path("backend/alembic/EXEMPTIONS.md"),
            Path("docs/exemptions/migrations.md"),
        ]
        for alt in alt_paths:
            if alt.exists():
                path = alt
                break
        else:
            return set()
    
    content = path.read_text(encoding="utf-8")
    
    # 解析豁免的revision ID
    # 格式: - `abc123` - 原因
    exemptions = set()
    for match in re.finditer(r"`([a-f0-9]+)`", content):
        exemptions.add(match.group(1))
    
    return exemptions


def main():
    strict_mode = "--strict" in sys.argv
    
    print("=" * 60)
    print("  数据库迁移可回滚性检查")
    print("=" * 60)
    print()
    
    migration_files = find_migration_files()
    
    if not migration_files:
        print("✓ 无迁移文件需要检查")
        sys.exit(0)
    
    exemptions = set() if strict_mode else load_exemptions()
    if exemptions:
        print(f"已加载 {len(exemptions)} 个豁免记录")
        print()
    
    errors = []
    warnings = []
    passed = 0
    
    for file_path in sorted(migration_files):
        # 提取revision ID（文件名格式: abc123_description.py）
        revision = file_path.stem.split("_")[0]
        
        has_downgrade, message = check_downgrade(file_path)
        
        if has_downgrade:
            print(f"✓ {file_path.name}")
            passed += 1
        elif revision in exemptions:
            print(f"⚠ {file_path.name} - 已豁免")
            warnings.append(file_path.name)
        else:
            print(f"✗ {file_path.name} - {message}")
            errors.append((file_path.name, message))
    
    print()
    print("-" * 60)
    print(f"检查完成: {passed} 通过, {len(warnings)} 豁免, {len(errors)} 失败")
    print("-" * 60)
    
    if errors:
        print()
        print("❌ 以下迁移文件不可回滚:")
        for name, msg in errors:
            print(f"   - {name}: {msg}")
        print()
        print("解决方案:")
        print("  1. 添加 downgrade() 函数实现")
        print("  2. 或在 migrations/EXEMPTIONS.md 中添加豁免记录")
        print()
        sys.exit(1)
    
    print()
    print("✅ 所有迁移文件可回滚性检查通过")
    sys.exit(0)


if __name__ == "__main__":
    main()
