#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SessionStart Hook - 加载 SoT 文档上下文
检查 SoT 文档存在性，并将文档列表输出到 stdout（注入上下文）
"""
import sys
import os
import io
from pathlib import Path

# 在 Windows 上设置 UTF-8 输出编码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding="utf-8", errors="replace"
    )

# SoT 文档列表（按裁判链优先级排序）
SOT_DOCUMENTS = [
    {
        "path": "docs/1.overview/MASTER.md",
        "title": "架构宪法",
        "priority": 1,
        "description": "系统全局规则、角色定义、AI 防幻觉原则",
    },
    {
        "path": "docs/2.sot/DATA_SCHEMA.md",
        "title": "数据模型",
        "priority": 2,
        "description": "数据库模型、字段定义、外键关系",
    },
    {
        "path": "docs/2.sot/STATE_MACHINE.md",
        "title": "状态机",
        "priority": 3,
        "description": "日报 8 状态流转、状态转换规则",
    },
    {
        "path": "docs/2.sot/BUSINESS_RULES.md",
        "title": "业务规则",
        "priority": 4,
        "description": "业务逻辑、验证规则、计算公式",
    },
]


def check_file_exists(file_path: str) -> bool:
    """检查文件是否存在"""
    return Path(file_path).exists()


def get_file_size(file_path: str) -> str:
    """获取文件大小（KB）"""
    try:
        size_bytes = Path(file_path).stat().st_size
        size_kb = size_bytes / 1024
        return f"{size_kb:.1f} KB"
    except Exception:
        return "N/A"


def main():
    """主逻辑：检查并加载 SoT 文档"""

    print("=" * 80)
    print("📚 SoT 文档上下文加载")
    print("=" * 80)
    print()

    # 检查文档存在性
    existing_docs = []
    missing_docs = []

    for doc in SOT_DOCUMENTS:
        if check_file_exists(doc["path"]):
            existing_docs.append(doc)
        else:
            missing_docs.append(doc)

    # 输出已加载的文档列表
    if existing_docs:
        print(f"✅ 已加载 {len(existing_docs)} 个 SoT 文档:")
        print()

        for doc in existing_docs:
            size = get_file_size(doc["path"])
            print(f"  {doc['priority']}. [{doc['title']}] {doc['path']}")
            print(f"     {doc['description']}")
            print(f"     文件大小: {size}")
            print()

    # 警告缺失的文档
    if missing_docs:
        print(f"⚠️  缺失 {len(missing_docs)} 个 SoT 文档:")
        print()

        for doc in missing_docs:
            print(f"  ❌ [{doc['title']}] {doc['path']}")
            print(f"     {doc['description']}")
            print()

    # 输出裁判链优先级提醒
    print("=" * 80)
    print("⚖️  裁判链优先级规则")
    print("=" * 80)
    print()
    print("  当遇到冲突或歧义时，按以下优先级处理:")
    print()
    print("  1️⃣  MASTER.md > 2️⃣  DATA_SCHEMA.md > 3️⃣  STATE_MACHINE.md > 4️⃣  BUSINESS_RULES.md")
    print()
    print("  📖 开发前必读:")
    print("     → 所有开发必须基于 SoT 文档，禁止凭想象实现")
    print("     → 发现文档缺失或歧义，立即停止并询问")
    print("     → Phase 1: 仅记录、提示、高亮，禁止自动阻断")
    print()

    # 输出文档路径（供 Claude Code 注入上下文）
    print("=" * 80)
    print("📂 文档引用路径（可用 @docs 引用）")
    print("=" * 80)
    print()

    for doc in existing_docs:
        print(f"  @{doc['path']}")

    print()
    print("=" * 80)
    print("✅ SoT 上下文加载完成")
    print("=" * 80)
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
