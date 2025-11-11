#!/usr/bin/env python
"""
文档整理脚本
用于整理和归档过时的文档
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# 文档目录
DOCS_DIR = Path(__file__).parent
ARCHIVE_DIR = DOCS_DIR / "archive"

# 需要移动到归档的文档列表
TO_ARCHIVE = [
    # 根目录下的临时文档
    ("DATABASE_FIX_VALIDATION_REPORT.md", "数据库修复报告 - 已完成"),
    ("database_init.sql", "数据库初始化SQL - 已移动到scripts"),
    ("sample_queries.sql", "示例查询 - 已移动"),
    ("explore_database.py", "数据库探索脚本 - 已移动"),
    ("final_supabase_demo.py", "Supabase演示 - 已完成"),
    ("ai_ad_system_database.py", "旧版数据库脚本 - 已更新"),
]

# 需要更新的文档（更新内容）
TO_UPDATE = [
    "README.md",  # 需要更新指向新的文档索引
]

# 重复的文档（保留最新的）
DUPLICATES = {
    "DATA_SCHEMA.md": ["DATA_SCHEMA_v2_3.md"],  # v2_3是最新版本
}

def archive_document(file_path, reason):
    """归档文档"""
    source = DOCS_DIR / file_path
    if source.exists():
        # 创建归档子目录
        archive_subdir = ARCHIVE_DIR / datetime.now().strftime("%Y-%m")
        archive_subdir.mkdir(parents=True, exist_ok=True)

        # 移动文件
        dest = archive_subdir / source.name
        shutil.move(source, dest)

        # 创建说明文件
        readme = archive_subdir / f"{source.name}.README"
        with open(readme, 'w', encoding='utf-8') as f:
            f.write(f"# {source.name}\n\n")
            f.write(f"**归档原因**: {reason}\n")
            f.write(f"**归档日期**: {datetime.now().strftime('%Y-%m-%d')}\n")

        print(f"✓ 已归档: {file_path} -> {archive_subdir}")
    else:
        print(f"⚠ 文件不存在: {file_path}")

def create_readme():
    """创建归档目录的README"""
    readme = ARCHIVE_DIR / "README.md"
    if not readme.exists():
        with open(readme, 'w', encoding='utf-8') as f:
            f.write("# 文档归档\n\n")
            f.write("此目录包含项目的旧版本文档和已归档的文件。\n\n")
            f.write("## 目录结构\n\n")
            f.write("- 按年月组织的子目录（如 2025-01）\n")
            f.write("- 每个文件都有对应的 .README 说明归档原因\n\n")
            f.write("## 注意事项\n\n")
            f.write("- 归档文档仅供参考\n")
            f.write("- 如需最新信息，请查看主文档目录\n")

def main():
    print("="*50)
    print("文档整理工具")
    print("="*50)

    # 创建归档目录
    ARCHIVE_DIR.mkdir(exist_ok=True)

    # 1. 归档过时文档
    print("\n[1] 归档过时文档...")
    for file_path, reason in TO_ARCHIVE:
        archive_document(file_path, reason)

    # 2. 创建归档README
    print("\n[2] 创建归档说明...")
    create_readme()

    # 3. 清理临时文件
    print("\n[3] 清理临时文件...")
    temp_patterns = [
        "*.tmp",
        "*.log",
        "*~",
        ".DS_Store",
        "Thumbs.db"
    ]

    for pattern in temp_patterns:
        for file in DOCS_DIR.glob(pattern):
            if file.is_file():
                file.unlink()
                print(f"  - 删除临时文件: {file.name}")

    # 4. 统计文档
    print("\n[4] 文档统计...")
    doc_count = len(list(DOCS_DIR.glob("**/*.md")))
    print(f"  - Markdown文档: {doc_count} 个")
    print(f"  - 归档文档: {len(list(ARCHIVE_DIR.glob("**/*")))} 个")

    print("\n" + "="*50)
    print("文档整理完成！")
    print("="*50)

    # 5. 提供下一步建议
    print("\n建议后续操作：")
    print("1. 查看 docs/DOCUMENTATION_INDEX.md 了解文档结构")
    print("2. 更新需要维护的文档（标记为📝 待更新）")
    print("3. 删除不再需要的代码文件（如各种Python脚本）")

if __name__ == "__main__":
    main()