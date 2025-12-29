#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code 状态栏脚本 - AI 广告代投系统

显示：时间 | 模型 | 项目 | Git分支 | 上下文使用率 | 成本 | 监工状态
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Windows UTF-8
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ANSI 颜色
CYAN = '\033[36m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
RED = '\033[31m'
BLUE = '\033[34m'
MAGENTA = '\033[35m'
RESET = '\033[0m'
BOLD = '\033[1m'


def get_beijing_time() -> str:
    """获取北京时间 (UTC+8)"""
    beijing_tz = timezone(timedelta(hours=8))
    now = datetime.now(beijing_tz)

    # 星期映射
    weekdays = ['一', '二', '三', '四', '五', '六', '日']
    weekday = weekdays[now.weekday()]

    # 时段判断
    hour = now.hour
    if 5 <= hour < 9:
        period = "早"
    elif 9 <= hour < 12:
        period = "上午"
    elif 12 <= hour < 14:
        period = "中午"
    elif 14 <= hour < 18:
        period = "下午"
    elif 18 <= hour < 22:
        period = "晚"
    else:
        period = "深夜"

    return f"{now.month}/{now.day} 周{weekday} {period}{now.hour}:{now.minute:02d}"


def get_git_branch() -> str | None:
    """获取当前 Git 分支"""
    try:
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True,
            text=True,
            timeout=1,
            cwd=os.getcwd()
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_git_changes() -> int:
    """获取未提交的变更数"""
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=os.getcwd()
        )
        if result.returncode == 0:
            lines = [l for l in result.stdout.strip().split('\n') if l]
            return len(lines)
    except Exception:
        pass
    return 0


def get_supervisor_status() -> str:
    """获取监工系统状态"""
    data_dir = Path(__file__).parent / "data"

    # 检查进度文件
    progress_file = data_dir / "progress.json"
    if progress_file.exists():
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                overall = progress.get('overall_progress', 0)
                if overall > 0:
                    return f"{overall}%"
        except Exception:
            pass

    return "ready"


def format_context_usage(data: dict) -> str:
    """格式化上下文使用率"""
    ctx = data.get('context_window', {})
    usage = ctx.get('current_usage')
    total = ctx.get('context_window_size', 0)

    if not usage or total <= 0:
        return ""

    used = (
        usage.get('input_tokens', 0) +
        usage.get('output_tokens', 0) +
        usage.get('cache_creation_input_tokens', 0) +
        usage.get('cache_read_input_tokens', 0)
    )
    pct = (used * 100) // total

    # 颜色根据使用率
    if pct > 90:
        color = RED
    elif pct > 70:
        color = YELLOW
    else:
        color = GREEN

    return f"{color}ctx:{pct}%{RESET}"


def format_cost(data: dict) -> str:
    """格式化成本"""
    cost = data.get('cost', {})
    total_cost = cost.get('total_cost_usd', 0)

    if total_cost <= 0:
        return ""

    if total_cost > 1:
        color = RED
    elif total_cost > 0.5:
        color = YELLOW
    else:
        color = GREEN

    return f"{color}${total_cost:.3f}{RESET}"


def main():
    try:
        # 从 stdin 读取 JSON
        input_data = sys.stdin.read()
        data = json.loads(input_data) if input_data.strip() else {}

        # 模型
        model = data.get('model', {}).get('display_name', 'Claude')

        # 项目名
        cwd = data.get('workspace', {}).get('current_dir', os.getcwd())
        project = os.path.basename(cwd) or 'project'

        # Git 分支
        branch = get_git_branch()
        changes = get_git_changes()

        git_str = ""
        if branch:
            if changes > 0:
                git_str = f"{YELLOW}{branch}*{changes}{RESET}"
            else:
                git_str = f"{GREEN}{branch}{RESET}"

        # 上下文使用率
        ctx_str = format_context_usage(data)

        # 成本
        cost_str = format_cost(data)

        # 监工状态
        supervisor = get_supervisor_status()
        supervisor_str = f"{MAGENTA}SV:{supervisor}{RESET}"

        # 北京时间
        time_str = f"{BLUE}{get_beijing_time()}{RESET}"

        # 组装状态栏
        parts = [time_str, f"{CYAN}{BOLD}[{model}]{RESET}", project]

        if git_str:
            parts.append(git_str)
        if ctx_str:
            parts.append(ctx_str)
        if cost_str:
            parts.append(cost_str)
        parts.append(supervisor_str)

        status = " | ".join(parts)
        print(status)

    except Exception as e:
        # 出错时显示基础状态
        print(f"{CYAN}[AI广告代投]{RESET} Ready")


if __name__ == '__main__':
    main()
