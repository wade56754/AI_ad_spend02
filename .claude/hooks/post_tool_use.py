#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostToolUse Hook - Write/Edit 工具使用后的代码格式化
"""
import sys
import os
import json
import subprocess
import shutil
import io

# 在 Windows 上设置 UTF-8 输出编码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def format_python_file(file_path: str) -> bool:
    """使用 black 格式化 Python 文件"""
    # 检查 black 是否安装
    if not shutil.which("black"):
        print(f"⚠️  black 未安装，跳过格式化: {file_path}")
        return False

    try:
        result = subprocess.run(
            ["black", "--quiet", file_path],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print(f"✅ black 格式化成功: {file_path}")
            return True
        else:
            print(f"⚠️  black 格式化失败: {file_path}")
            if result.stderr:
                print(f"   错误: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"⚠️  black 格式化超时: {file_path}")
        return False
    except Exception as e:
        print(f"⚠️  black 格式化出错: {e}")
        return False


def format_typescript_file(file_path: str) -> bool:
    """使用 prettier 格式化 TypeScript 文件"""
    # 检查 prettier 是否安装（支持 npx）
    has_prettier = shutil.which("prettier") or shutil.which("npx")

    if not has_prettier:
        print(f"⚠️  prettier 未安装，跳过格式化: {file_path}")
        return False

    try:
        # 优先使用本地 prettier，否则使用 npx
        cmd = ["prettier", "--write", file_path]
        if not shutil.which("prettier"):
            cmd = ["npx", "prettier", "--write", file_path]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.path.dirname(os.path.abspath(file_path)) or ".",
        )

        if result.returncode == 0:
            print(f"✅ prettier 格式化成功: {file_path}")
            return True
        else:
            print(f"⚠️  prettier 格式化失败: {file_path}")
            if result.stderr:
                print(f"   错误: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"⚠️  prettier 格式化超时: {file_path}")
        return False
    except Exception as e:
        print(f"⚠️  prettier 格式化出错: {e}")
        return False


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

        # 根据文件类型选择格式化工具
        if file_path.endswith(".py"):
            format_python_file(file_path)

        elif file_path.endswith((".ts", ".tsx", ".js", ".jsx")):
            format_typescript_file(file_path)

        # 其他文件类型不处理
        return 0

    except Exception as e:
        print(f"⚠️  PostToolUse Hook 执行出错: {e}", file=sys.stderr)
        # 出错时不影响主流程
        return 0


if __name__ == "__main__":
    sys.exit(main())
