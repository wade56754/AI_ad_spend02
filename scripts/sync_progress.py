#!/usr/bin/env python3
"""
Task Master → Memory Bank Progress Sync

从 Task Master 任务卡同步生成 progress.md 文档。
支持手动运行或通过 Claude Code Hook 自动触发。

用法:
    python scripts/sync_progress.py [--project-root PATH]

环境变量:
    PROJECT_ROOT: 项目根目录 (默认: 当前目录)
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 项目根目录
PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).parent.parent))
TASKMASTER_PATH = PROJECT_ROOT / ".taskmaster" / "tasks" / "tasks.json"
PROGRESS_PATH = PROJECT_ROOT / "memory-bank" / "progress.md"

# 状态映射
STATUS_EMOJI = {
    "done": "✅",
    "in-progress": "🔄",
    "pending": "⏳",
    "blocked": "🚫",
    "cancelled": "❌",
    "deferred": "⏸️",
    "review": "👀",
}

# 优先级映射
PRIORITY_EMOJI = {
    "high": "🔴",
    "medium": "🟡",
    "low": "🟢",
}

# 模块映射 (从 tags 提取)
MODULE_MAP = {
    "M0-基础设施": "M0 基础设施",
    "M1-项目管理": "M1 项目管理",
    "M2-日报管理": "M2 日报管理",
    "M3-账户管理": "M3 账户管理",
    "M4-充值管理": "M4 充值管理",
    "M5-财务管理": "M5 财务管理",
    "AUTH": "认证模块",
    "USER": "用户模块",
    "PROJECT": "项目模块",
    "ACCOUNT": "账户模块",
    "REPORT": "日报模块",
    "TOPUP": "充值模块",
}


def load_tasks() -> dict[str, Any]:
    """加载 Task Master 任务数据"""
    if not TASKMASTER_PATH.exists():
        print(f"❌ Task Master 文件不存在: {TASKMASTER_PATH}")
        sys.exit(1)

    with open(TASKMASTER_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def categorize_tasks(tasks: list[dict]) -> dict[str, list[dict]]:
    """按模块分类任务"""
    categories: dict[str, list[dict]] = {}

    for task in tasks:
        # 从 tags 中提取模块
        module = "其他"
        for tag in task.get("tags", []):
            if tag.startswith("M"):
                module = MODULE_MAP.get(tag, tag)
                break

        if module not in categories:
            categories[module] = []
        categories[module].append(task)

    return categories


def calculate_stats(tasks: list[dict]) -> dict[str, Any]:
    """计算任务统计"""
    total = len(tasks)
    done = sum(1 for t in tasks if t["status"] == "done")
    in_progress = sum(1 for t in tasks if t["status"] == "in-progress")
    pending = sum(1 for t in tasks if t["status"] == "pending")
    cancelled = sum(1 for t in tasks if t["status"] == "cancelled")

    active_total = total - cancelled
    completion_rate = (done / active_total * 100) if active_total > 0 else 0

    return {
        "total": total,
        "done": done,
        "in_progress": in_progress,
        "pending": pending,
        "cancelled": cancelled,
        "active_total": active_total,
        "completion_rate": completion_rate,
    }


def generate_progress_bar(percentage: float, width: int = 20) -> str:
    """生成进度条"""
    filled = int(width * percentage / 100)
    bar = "█" * filled + "░" * (width - filled)
    return bar


def format_task_row(task: dict) -> str:
    """格式化任务行"""
    status_emoji = STATUS_EMOJI.get(task["status"], "❓")
    priority_emoji = PRIORITY_EMOJI.get(task.get("priority", "medium"), "🟡")
    title = task["title"]

    # 提取任务卡 ID (如 TASK-AUTH-001)
    task_id = title.split(":")[0].strip() if ":" in title else f"TASK-{task['id']}"
    task_name = title.split(":", 1)[1].strip() if ":" in title else title

    return f"| {task_id} | {task_name} | {status_emoji} {task['status']} | {priority_emoji} |"


def generate_progress_md(data: dict[str, Any]) -> str:
    """生成 progress.md 内容"""
    tasks = data.get("master", {}).get("tasks", [])
    metadata = data.get("master", {}).get("metadata", {})

    stats = calculate_stats(tasks)
    categories = categorize_tasks(tasks)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 构建文档
    lines = [
        "# AI 广告代投管理系统 - 进度记录",
        "",
        f"> **最后更新**: {now}",
        f"> **数据来源**: Task Master MCP (自动同步)",
        "> **SoT 基准**: MASTER.md v4.8 / DATA_SCHEMA.md v5.7 / 6 角色白名单",
        "",
        "---",
        "",
        "## 1. 总体进度",
        "",
        "```",
        f"任务完成率: {generate_progress_bar(stats['completion_rate'])} {stats['completion_rate']:.1f}%",
        "",
        f"总任务数:   {stats['active_total']} (排除已取消)",
        f"已完成:     {stats['done']}",
        f"进行中:     {stats['in_progress']}",
        f"待开始:     {stats['pending']}",
        f"已取消:     {stats['cancelled']}",
        "```",
        "",
        "| 指标 | 数值 |",
        "|------|------|",
        f"| 总任务数 | {stats['total']} |",
        f"| 已完成 | {stats['done']} / {stats['active_total']} |",
        f"| 完成率 | {stats['completion_rate']:.1f}% |",
        "",
        "---",
        "",
        "## 2. 模块进度",
        "",
    ]

    # 按模块生成进度
    for module_name in sorted(categories.keys()):
        module_tasks = categories[module_name]
        module_stats = calculate_stats(module_tasks)

        lines.append(f"### {module_name}")
        lines.append("")
        lines.append(
            f"进度: {generate_progress_bar(module_stats['completion_rate'], 15)} {module_stats['completion_rate']:.0f}% ({module_stats['done']}/{module_stats['active_total']})"
        )
        lines.append("")
        lines.append("| 任务卡 | 描述 | 状态 | 优先级 |")
        lines.append("|--------|------|------|--------|")

        for task in sorted(module_tasks, key=lambda t: t["id"]):
            if task["status"] != "cancelled":
                lines.append(format_task_row(task))

        lines.append("")

    # 已完成任务
    done_tasks = [t for t in tasks if t["status"] == "done"]
    if done_tasks:
        lines.extend(
            [
                "---",
                "",
                "## 3. 已完成任务",
                "",
                "| 任务卡 | 描述 | 完成时间 |",
                "|--------|------|----------|",
            ]
        )

        for task in sorted(
            done_tasks, key=lambda t: t.get("updatedAt", ""), reverse=True
        ):
            title = task["title"]
            task_id = (
                title.split(":")[0].strip() if ":" in title else f"TASK-{task['id']}"
            )
            task_name = title.split(":", 1)[1].strip() if ":" in title else title
            updated = task.get("updatedAt", "N/A")
            if updated != "N/A":
                updated = updated.split("T")[0]
            lines.append(f"| {task_id} | {task_name} | {updated} |")

        lines.append("")

    # 进行中任务
    in_progress_tasks = [t for t in tasks if t["status"] == "in-progress"]
    if in_progress_tasks:
        lines.extend(
            [
                "---",
                "",
                "## 4. 当前进行中",
                "",
                "| 任务卡 | 描述 | 优先级 |",
                "|--------|------|--------|",
            ]
        )

        for task in in_progress_tasks:
            title = task["title"]
            task_id = (
                title.split(":")[0].strip() if ":" in title else f"TASK-{task['id']}"
            )
            task_name = title.split(":", 1)[1].strip() if ":" in title else title
            priority = PRIORITY_EMOJI.get(task.get("priority", "medium"), "🟡")
            lines.append(
                f"| {task_id} | {task_name} | {priority} {task.get('priority', 'medium')} |"
            )

        lines.append("")

    # 待办任务 (下一步)
    pending_high = [
        t for t in tasks if t["status"] == "pending" and t.get("priority") == "high"
    ][:5]
    if pending_high:
        lines.extend(
            [
                "---",
                "",
                "## 5. 下一步计划 (高优先级)",
                "",
                "| 任务卡 | 描述 | 依赖 |",
                "|--------|------|------|",
            ]
        )

        for task in pending_high:
            title = task["title"]
            task_id = (
                title.split(":")[0].strip() if ":" in title else f"TASK-{task['id']}"
            )
            task_name = title.split(":", 1)[1].strip() if ":" in title else title
            deps = ", ".join(task.get("dependencies", [])) or "-"
            lines.append(f"| {task_id} | {task_name} | {deps} |")

        lines.append("")

    # 元数据
    lines.extend(
        [
            "---",
            "",
            "## 6. 同步信息",
            "",
            "| 属性 | 值 |",
            "|------|------|",
            f"| 同步时间 | {now} |",
            f"| Task Master 版本 | {metadata.get('version', 'N/A')} |",
            f"| 最后修改 | {metadata.get('lastModified', 'N/A').split('T')[0] if metadata.get('lastModified') else 'N/A'} |",
            f"| 数据标签 | {', '.join(metadata.get('tags', ['master']))} |",
            "",
            "> 此文档由 `scripts/sync_progress.py` 自动生成",
            "> 运行 `/sync-progress` 或完成任务卡时自动更新",
            "",
        ]
    )

    return "\n".join(lines)


def sync_progress() -> None:
    """执行同步"""
    print("🔄 正在同步 Task Master → progress.md ...")

    # 加载任务
    data = load_tasks()

    # 生成 progress.md
    content = generate_progress_md(data)

    # 备份旧文件
    if PROGRESS_PATH.exists():
        backup_path = PROGRESS_PATH.with_suffix(".md.bak")
        PROGRESS_PATH.rename(backup_path)
        print(f"📦 已备份旧文件: {backup_path}")

    # 写入新文件
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    # 统计
    tasks = data.get("master", {}).get("tasks", [])
    stats = calculate_stats(tasks)

    print(f"✅ 同步完成!")
    print(f"   - 总任务: {stats['total']}")
    print(f"   - 已完成: {stats['done']} ({stats['completion_rate']:.1f}%)")
    print(f"   - 输出: {PROGRESS_PATH}")


def main():
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(description="同步 Task Master 到 progress.md")
    parser.add_argument("--project-root", type=Path, help="项目根目录")
    args = parser.parse_args()

    if args.project_root:
        global PROJECT_ROOT, TASKMASTER_PATH, PROGRESS_PATH
        PROJECT_ROOT = args.project_root
        TASKMASTER_PATH = PROJECT_ROOT / ".taskmaster" / "tasks" / "tasks.json"
        PROGRESS_PATH = PROJECT_ROOT / "memory-bank" / "progress.md"

    sync_progress()


if __name__ == "__main__":
    main()
