#!/usr/bin/env python
"""临时脚本：构建知识库索引"""

import sys
import os
import traceback

# 先写入文件表示脚本开始执行
project_dir = os.path.dirname(os.path.abspath(__file__))
result_path = os.path.join(project_dir, "kb_build_result.txt")

# 写入启动信息
with open(result_path, "w", encoding="utf-8") as f:
    f.write("Script started\n")
    f.write(f"Python version: {sys.version}\n")
    f.write(f"Project dir: {project_dir}\n")

try:
    # 设置路径
    sys.path.insert(0, project_dir)
    os.chdir(project_dir)

    output = []
    output.append("=" * 50)
    output.append("Knowledge Base Builder")
    output.append("=" * 50)

    # 更新进度
    with open(result_path, "a", encoding="utf-8") as f:
        f.write("Attempting import...\n")

    from agents.skills.code_factory import create_knowledge_base
    output.append("[OK] Import successful")

    with open(result_path, "a", encoding="utf-8") as f:
        f.write("Import successful\n")

    # 创建知识库
    kb = create_knowledge_base(".")
    output.append("[OK] Knowledge base created")

    with open(result_path, "a", encoding="utf-8") as f:
        f.write("KB created, building index...\n")

    # 构建索引
    stats = kb.build_index(force_rebuild=True)
    output.append("[OK] Index build completed!")

    # 输出统计
    output.append("")
    output.append("=" * 50)
    output.append("Index Statistics")
    output.append("=" * 50)

    for source, stat in stats.items():
        output.append(f"\n[{source.upper()}]")
        output.append(f"  Documents: {stat['total_documents']}")
        output.append(f"  Chunks: {stat['total_chunks']}")
        output.append(f"  Characters: {stat['total_chars']:,}")

    total_docs = sum(s['total_documents'] for s in stats.values())
    total_chunks = sum(s['total_chunks'] for s in stats.values())
    total_chars = sum(s['total_chars'] for s in stats.values())

    output.append("")
    output.append("=" * 50)
    output.append("TOTAL")
    output.append("=" * 50)
    output.append(f"  Documents: {total_docs}")
    output.append(f"  Chunks: {total_chunks}")
    output.append(f"  Characters: {total_chars:,}")
    output.append("")
    output.append("Done!")

    # 写入最终结果
    with open(result_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output))

except Exception as e:
    error_msg = f"[ERROR] {e}\n\n{traceback.format_exc()}"
    with open(result_path, "w", encoding="utf-8") as f:
        f.write(error_msg)
