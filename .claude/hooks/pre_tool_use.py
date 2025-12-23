#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PreToolUse Hook - Write/Edit 工具使用前的代码检查
"""
import sys
import os
import json
import re
import io

# 在 Windows 上设置 UTF-8 输出编码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 合法角色列表（来自 MASTER.md v4.4 §2.4）
VALID_ROLES = {
    "ceo",
    "project_owner",
    "finance",
    "supervisor",
    "pitcher",
    "account_manager",
    "admin",
}

# Phase 2 功能关键词（禁止在 Phase 1 使用）
PHASE2_KEYWORDS = [
    r"auto[_-]?reject",
    r"auto[_-]?suspend",
    r"auto[_-]?freeze",
    r"auto[_-]?disable",
    r"auto[_-]?block",
    r"auto[_-]?penalty",
    r"forced[_-]?approval",
    r"mandatory[_-]?approval",
    r"自动拒绝",
    r"自动暂停",
    r"自动冻结",
    r"自动禁用",
    r"自动封禁",
    r"强制审批",
]


def check_phase2_features(content: str, file_path: str) -> list:
    """检测 Phase 2 功能"""
    violations = []

    for pattern in PHASE2_KEYWORDS:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            line_num = content[: match.start()].count("\n") + 1
            violations.append(
                f"  ⚠️  {file_path}:{line_num} - 检测到 Phase 2 功能关键词: '{match.group()}'"
            )

    return violations


def check_foreign_key_naming(content: str, file_path: str) -> list:
    """检测外键命名是否使用 _id 后缀"""
    violations = []

    # 检测 SQLAlchemy ForeignKey 定义
    fk_pattern = r"ForeignKey\(['\"]([^'\"]+)['\"]"
    matches = re.finditer(fk_pattern, content)

    for match in matches:
        fk_ref = match.group(1)
        line_num = content[: match.start()].count("\n") + 1

        # 检查当前行上下文，查找字段名
        lines = content.split("\n")
        if line_num <= len(lines):
            current_line = lines[line_num - 1]

            # 提取字段名（通常是 field_name = Column(...)）
            field_match = re.search(r"(\w+)\s*=\s*Column", current_line)
            if field_match:
                field_name = field_match.group(1)

                # 检查字段名是否以 _id 结尾
                if not field_name.endswith("_id"):
                    violations.append(
                        f"  ⚠️  {file_path}:{line_num} - 外键字段 '{field_name}' 缺少 _id 后缀 (引用: {fk_ref})"
                    )

    return violations


def check_invalid_roles(content: str, file_path: str) -> list:
    """检测是否引入未定义角色"""
    violations = []

    # 检测角色定义（Enum、List 等）
    role_patterns = [
        r'role["\']?\s*[:=]\s*["\'](\w+)["\']',  # role = "something" 或 role: "something"
        r'UserRole\.[A-Z_]+\s*=\s*["\'](\w+)["\']',  # UserRole.XXX = "something"
        r'roles?\s*=\s*\[[^\]]*["\'](\w+)["\'][^\]]*\]',  # roles = ["something", ...]
    ]

    for pattern in role_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            role_value = match.group(1).lower()

            if role_value not in VALID_ROLES and role_value not in [
                "user",
                "guest",
                "public",
            ]:  # 排除明显非业务角色
                line_num = content[: match.start()].count("\n") + 1
                violations.append(
                    f"  ⚠️  {file_path}:{line_num} - 检测到未定义角色: '{role_value}' (合法角色: {', '.join(sorted(VALID_ROLES))})"
                )

    return violations


def main():
    """主检查逻辑"""
    tool_name = os.environ.get("TOOL_NAME", "")
    tool_params_json = os.environ.get("TOOL_PARAMETERS_JSON", "{}")

    # 只检查 Write 和 Edit 工具
    if tool_name not in ["Write", "Edit"]:
        return 0

    try:
        params = json.loads(tool_params_json)
        file_path = params.get("file_path", "")
        content = params.get("content") or params.get("new_string", "")

        if not content:
            return 0

        # 只检查 Python 和 TypeScript 文件
        if not (file_path.endswith(".py") or file_path.endswith(".ts") or file_path.endswith(".tsx")):
            return 0

        all_violations = []

        # 执行各项检查
        all_violations.extend(check_phase2_features(content, file_path))
        all_violations.extend(check_foreign_key_naming(content, file_path))
        all_violations.extend(check_invalid_roles(content, file_path))

        # 输出检查结果
        if all_violations:
            print("=" * 80)
            print("❌ PreToolUse Hook - 检测到代码违规")
            print("=" * 80)
            print()

            for violation in all_violations:
                print(violation)

            print()
            print("📖 提醒：")
            print("  • Phase 1 禁止自动阻断/惩罚功能")
            print("  • 外键字段必须使用 _id 后缀（如：project_id, user_id）")
            print(f"  • 仅允许 7 个角色：{', '.join(sorted(VALID_ROLES))}")
            print()
            print("=" * 80)
            print("⚠️  请修复以上问题后重试")
            print("=" * 80)
            print()

            # 返回非零值会阻止工具执行
            return 1

        # 无违规，允许执行
        return 0

    except Exception as e:
        print(f"⚠️  PreToolUse Hook 执行出错: {e}", file=sys.stderr)
        # 出错时不阻止工具执行
        return 0


if __name__ == "__main__":
    sys.exit(main())
