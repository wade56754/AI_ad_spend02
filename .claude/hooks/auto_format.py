#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostToolUse Hook - 自动代码格式化
在 Write/Edit 后自动格式化代码文件

支持格式化：
- .py 文件 → black
- .ts/.tsx 文件 → prettier

格式化失败不阻断，静默继续
"""
import sys
import os
import json
import subprocess
import shutil
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


def run_black(file_path: str) -> bool:
    """运行 black 格式化 Python 文件"""
    try:
        # 优先使用 python -m black（更可靠，不依赖 PATH）
        result = subprocess.run(
            [sys.executable, "-m", "black", "--quiet", file_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except Exception:
        # black 未安装或执行失败，静默跳过
        return False


def run_prettier(file_path: str) -> bool:
    """运行 prettier 格式化 TypeScript 文件"""
    try:
        # 使用 npx prettier（如果本地没有安装会自动下载）
        result = subprocess.run(
            ["npx", "prettier", "--write", file_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except Exception:
        return False


def format_file(file_path: str) -> tuple[bool, str]:
    """
    根据文件类型自动格式化

    返回: (是否格式化, 格式化工具名称)
    """
    file_ext = Path(file_path).suffix

    # Python 文件
    if file_ext == ".py":
        success = run_black(file_path)
        return (success, "black")

    # TypeScript/TSX 文件
    elif file_ext in [".ts", ".tsx", ".js", ".jsx"]:
        success = run_prettier(file_path)
        return (success, "prettier")

    # 其他文件类型不处理
    return (False, None)


def main():
    """主格式化逻辑"""
    tool_name = os.environ.get("TOOL_NAME", "")
    tool_params_json = os.environ.get("TOOL_PARAMETERS_JSON", "{}")

    # 只处理 Write 和 Edit 工具
    if tool_name not in ["Write", "Edit"]:
        return 0

    try:
        params = json.loads(tool_params_json)
        file_path = params.get("file_path", "")

        if not file_path or not os.path.exists(file_path):
            return 0

        # 尝试格式化文件
        formatted, formatter = format_file(file_path)

        # 格式化成功时静默（不输出），失败也不影响流程
        # 这样可以保持输出简洁，格式化在后台默默完成

        return 0

    except Exception:
        # 任何错误都静默处理，不影响主流程
        return 0


if __name__ == "__main__":
    sys.exit(main())
