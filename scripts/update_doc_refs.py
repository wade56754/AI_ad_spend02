#!/usr/bin/env python3
"""批量更新文档引用：docs/sot/ → docs/sot/"""

import os
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
SKIP_DIRS = {'archive', 'files', 'node_modules', '.git', '__pycache__', '.next'}

def should_process(path: Path) -> bool:
    """检查是否应该处理此文件"""
    parts = path.parts
    for skip in SKIP_DIRS:
        if skip in parts:
            return False
    return True

def update_file(filepath: Path) -> bool:
    """更新单个文件中的引用"""
    try:
        content = filepath.read_text(encoding='utf-8')
        original = content

        # 替换 docs/sot/ → docs/sot/
        content = re.sub(r'docs/2\.sot/', 'docs/sot/', content)

        # 替换 docs/sot/MASTER.md → docs/sot/MASTER.md
        content = re.sub(r'docs/1\.overview/MASTER\.md', 'docs/sot/MASTER.md', content)

        if content != original:
            filepath.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    updated = 0
    extensions = {'.md', '.py', '.ts', '.tsx', '.mdc'}

    for ext in extensions:
        for filepath in ROOT.rglob(f'*{ext}'):
            if should_process(filepath):
                if update_file(filepath):
                    print(f"Updated: {filepath.relative_to(ROOT)}")
                    updated += 1

    print(f"\n✓ 更新了 {updated} 个文件")

if __name__ == '__main__':
    main()
