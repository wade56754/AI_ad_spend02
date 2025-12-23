#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1 Guard Hook - Phase 1 原则守护
检测代码是否违反 Phase 1（照亮阶段）核心原则

违规行为：
1. 自动拒绝、自动暂停、自动冻结、强制阻断
2. raise Exception 处理预算超标（应该只提示）
3. 外键未使用 _id 后缀

Exit Code: 2 表示检测到违规
"""
import sys
import os
import json
import re
import io

# 在 Windows 上设置 UTF-8 输出编码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding="utf-8", errors="replace"
    )

# Phase 2 自动阻断行为模式（禁止在 Phase 1 使用）
PHASE2_AUTO_BLOCK_PATTERNS = [
    # 英文关键词
    (r"\bauto[_-]?reject", "自动拒绝"),
    (r"\bauto[_-]?suspend", "自动暂停"),
    (r"\bauto[_-]?freeze", "自动冻结"),
    (r"\bauto[_-]?disable", "自动禁用"),
    (r"\bauto[_-]?block", "自动阻断"),
    (r"\bauto[_-]?penalty", "自动惩罚"),
    (r"\bforced[_-]?approval", "强制审批"),
    (r"\bmandatory[_-]?approval", "强制审批"),
    (r"\bauto[_-]?decline", "自动拒绝"),
    (r"\bauto[_-]?terminate", "自动终止"),
    # 中文关键词
    (r"自动拒绝", "自动拒绝"),
    (r"自动暂停", "自动暂停"),
    (r"自动冻结", "自动冻结"),
    (r"自动禁用", "自动禁用"),
    (r"自动封禁", "自动封禁"),
    (r"自动阻断", "自动阻断"),
    (r"强制审批", "强制审批"),
    (r"强制阻断", "强制阻断"),
]

# 预算超标异常抛出模式（Phase 1 应该只提示，不抛异常）
BUDGET_EXCEPTION_PATTERNS = [
    (r"raise\s+.*Exception.*预算", "预算超标抛出异常"),
    (r"raise\s+.*Exception.*budget.*exceed", "预算超标抛出异常"),
    (r"raise\s+.*Exception.*余额不足", "余额不足抛出异常"),
    (r"raise\s+.*Exception.*insufficient.*balance", "余额不足抛出异常"),
    (r"raise\s+.*Exception.*超出预算", "预算超标抛出异常"),
    (r"raise\s+BusinessError.*预算", "预算超标业务异常"),
    (r"raise\s+BusinessError.*budget", "预算超标业务异常"),
]


class Violation:
    """违规记录"""

    def __init__(self, line_num, pattern_desc, matched_text, context_line):
        self.line_num = line_num
        self.pattern_desc = pattern_desc
        self.matched_text = matched_text
        self.context_line = context_line


def check_phase2_auto_blocks(content: str, file_path: str) -> list:
    """检测 Phase 2 自动阻断行为"""
    violations = []

    for pattern, desc in PHASE2_AUTO_BLOCK_PATTERNS:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            line_num = content[: match.start()].count("\n") + 1
            lines = content.split("\n")
            context_line = lines[line_num - 1].strip() if line_num <= len(lines) else ""

            violations.append(
                Violation(
                    line_num=line_num,
                    pattern_desc=f"检测到 Phase 2 功能: {desc}",
                    matched_text=match.group(),
                    context_line=context_line,
                )
            )

    return violations


def check_budget_exceptions(content: str, file_path: str) -> list:
    """检测预算超标异常抛出（Phase 1 应该只提示）"""
    violations = []

    for pattern, desc in BUDGET_EXCEPTION_PATTERNS:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            line_num = content[: match.start()].count("\n") + 1
            lines = content.split("\n")
            context_line = lines[line_num - 1].strip() if line_num <= len(lines) else ""

            violations.append(
                Violation(
                    line_num=line_num,
                    pattern_desc=f"Phase 1 禁止抛异常: {desc}",
                    matched_text=match.group(),
                    context_line=context_line,
                )
            )

    return violations


def check_foreign_key_naming(content: str, file_path: str) -> list:
    """检测外键命名是否使用 _id 后缀"""
    violations = []

    # 检测 SQLAlchemy ForeignKey 定义
    # 匹配模式：field_name = Column(..., ForeignKey(...), ...)
    fk_pattern = r'(\w+)\s*=\s*Column\([^)]*ForeignKey\(["\']([^"\']+)["\']\)'
    matches = re.finditer(fk_pattern, content)

    for match in matches:
        field_name = match.group(1)
        fk_ref = match.group(2)
        line_num = content[: match.start()].count("\n") + 1

        # 检查字段名是否以 _id 结尾
        if not field_name.endswith("_id"):
            lines = content.split("\n")
            context_line = lines[line_num - 1].strip() if line_num <= len(lines) else ""

            violations.append(
                Violation(
                    line_num=line_num,
                    pattern_desc=f"外键字段缺少 _id 后缀",
                    matched_text=f"{field_name} (引用: {fk_ref})",
                    context_line=context_line,
                )
            )

    return violations


def format_violations(violations: list, file_path: str) -> str:
    """格式化违规信息"""
    output = []
    output.append("=" * 80)
    output.append("❌ Phase 1 原则违规检测 - 发现违规代码")
    output.append("=" * 80)
    output.append("")
    output.append(f"文件: {file_path}")
    output.append("")

    for idx, v in enumerate(violations, 1):
        output.append(f"违规 #{idx}:")
        output.append(f"  位置: 第 {v.line_num} 行")
        output.append(f"  类型: {v.pattern_desc}")
        output.append(f"  匹配: {v.matched_text}")
        output.append(f"  代码: {v.context_line}")
        output.append("")

    output.append("=" * 80)
    output.append("📖 Phase 1 原则提醒:")
    output.append("  ✅ 允许: 记录事实、展示状态、提示异常、高亮警告")
    output.append("  ❌ 禁止: 自动拒绝、自动暂停、自动冻结、强制阻断")
    output.append("  ❌ 禁止: 预算超标抛异常（应该只是提示/高亮）")
    output.append("  ✅ 外键: 必须使用 _id 后缀（如 project_id, user_id）")
    output.append("")
    output.append("💡 修复建议:")
    output.append("  • 将自动阻断改为状态标记 + 前端高亮")
    output.append("  • 将 raise Exception 改为返回警告标志")
    output.append("  • 将外键字段重命名为 xxx_id 格式")
    output.append("=" * 80)
    output.append("")

    return "\n".join(output)


def main():
    """主检测逻辑"""
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

        # 只检查 Python 文件
        if not file_path.endswith(".py"):
            return 0

        # 执行各项检查
        all_violations = []

        all_violations.extend(check_phase2_auto_blocks(content, file_path))
        all_violations.extend(check_budget_exceptions(content, file_path))
        all_violations.extend(check_foreign_key_naming(content, file_path))

        # 如果有违规，输出到 stderr 并返回 exit code 2
        if all_violations:
            error_msg = format_violations(all_violations, file_path)
            print(error_msg, file=sys.stderr)
            return 2

        # 无违规，允许执行
        return 0

    except Exception as e:
        print(f"⚠️  Phase 1 Guard Hook 执行出错: {e}", file=sys.stderr)
        # 出错时不阻止工具执行
        return 0


if __name__ == "__main__":
    sys.exit(main())
