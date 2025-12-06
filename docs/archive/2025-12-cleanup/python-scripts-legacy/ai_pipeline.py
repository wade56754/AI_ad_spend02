#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI 文档 + 代码审查流水线脚本（v0.1）

功能：
1. 调用 doc-architect 子代理，生成文档审查报告
2. 调用 doc-fixer 子代理，根据报告自动修复文档
3. 使用 codex review 审查代码
4. （可选）调用 codex-loop 子代理，根据 codex 报告修复代码

注意：
- 这是一个“编排脚本”，不会自己理解业务，只是帮你串起 CLI / 子代理。
- 默认只运行一轮，你可以根据需要在 main() 里做多轮循环。
"""

import subprocess
import json
from pathlib import Path
from textwrap import dedent
from typing import List, Optional


# ========== 基础配置 ==========
PROJECT_ROOT = Path(__file__).resolve().parent

# Claude CLI 命令（如果你用的是 npx claude，可以改成 ["npx", "claude"]）
CLAUDE_CMD = ["claude", "chat"]

# Codex CLI 命令
CODEX_CMD = ["codex", "review"]

# 要参与“文档审查”的模块关键词（可按需调整）
DOC_SCOPE_MODULES = ["DailyReport", "Ledger"]

# 要参与“代码审查”的目录（git diff 会在这些目录里过滤）
CODE_DIR_PREFIXES = ["backend/", "frontend/"]


# ========== 工具函数 ==========

def run_cmd(cmd: List[str], input_text: Optional[str] = None) -> str:
    """运行外部命令，返回 stdout 文本（抛出异常算硬错误）。"""
    result = subprocess.run(
        cmd,
        input=input_text.encode("utf-8") if input_text else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    out = result.stdout.decode("utf-8", errors="ignore")
    err = result.stderr.decode("utf-8", errors="ignore")
    if err.strip():
        print(f"[WARN] {' '.join(cmd)} stderr:\n{err}\n")
    return out


def get_changed_code_files() -> List[str]:
    """
    用 git diff 找出当前 HEAD 相对上一版本改动过的代码文件。
    你也可以改成固定列表 / 手动传参。
    """
    try:
        diff_out = run_cmd(["git", "diff", "--name-only", "HEAD~1", "HEAD"])
    except Exception as e:
        print(f"[WARN] git diff 失败：{e}，将返回空列表")
        return []

    files = []
    for line in diff_out.splitlines():
        line = line.strip()
        if not line:
            continue
        if any(line.startswith(prefix) for prefix in CODE_DIR_PREFIXES):
            files.append(line)
    return files


# ========== 调用 Claude 子代理 ==========

def call_claude(prompt: str) -> str:
    """
    调用 Claude CLI，一次性对话。
    这里简单用 stdin 传入用户消息，你可以根据自己的 CLI 习惯调整参数。
    """
    full_prompt = prompt.strip() + "\n"
    out = run_cmd(CLAUDE_CMD, input_text=full_prompt)
    print("\n==== Claude 输出（截断前 2k 字） ====")
    print(out[:2000])
    print("=================================\n")
    return out


def run_doc_architect() -> str:
    """
    调用 doc-architect 子代理，让它对文档做一次完整审查。
    返回原始输出文本（包含 SoT 报告 + Dev-Ready 清单）。
    """
    prompt = dedent(f"""
    Use the doc-architect subagent to review the documentation.

    任务：
    - 读取 `.claude/skills/ai-ad-doc-architect/SKILL.md`
    - 重点审查与以下模块相关的文档：{", ".join(DOC_SCOPE_MODULES)}
    - 按 SKILL.md 的 Step 0~6.5 输出：
      - 《SoT 一致性审查报告》
      - 《开发文档优化清单（Dev-Ready）》

    要求：
    - 严格遵守仲裁链与问题分级规则；
    - 明确标出 P0 / P1 / Missing；
    - 输出中不要尝试修改文件，只做审查结论。
    """)
    return call_claude(prompt)


def run_doc_fixer(doc_architect_output: str) -> str:
    """
    调用 doc-fixer 子代理，根据 doc-architect 输出修复文档。
    """
    prompt = dedent(f"""
    Use the doc-fixer subagent to fix documentation issues.

    上一轮 doc-architect 的审查输出如下（请完整读取并解析）：

    --- DOC-ARCHITECT REPORT BEGIN ---
    {doc_architect_output}
    --- DOC-ARCHITECT REPORT END ---

    任务：
    - 按 doc-fixer.md 中的规则：
      - 只根据上述报告构建待修列表；
      - 优先修复 P0 和 Missing，每轮最多修 3 条；
      - 对对应文档做“最小必要修改”，保持 Markdown 结构安全；
      - 不修改上游 SoT，除非报告带有 [UPSTREAM_FIX_REQUIRED] 标签并通过二次验证。

    输出：
    - 《本轮修复摘要》
    - 《剩余待修简表》
    """)
    return call_claude(prompt)


# ========== 调用 Codex + 代码子代理 ==========

def run_codex_review(files: List[str]) -> Optional[dict]:
    """
    调用 codex review，返回解析后的 JSON。
    如果没有文件或 codex 失败，则返回 None。
    """
    if not files:
        print("[INFO] 没有检测到改动代码文件，跳过 Codex 审查。")
        return None

    cmd = CODEX_CMD + files + ["--format", "json"]
    print(f"[INFO] 运行 Codex 命令: {' '.join(cmd)}")
    try:
        out = run_cmd(cmd)
    except Exception as e:
        print(f"[ERROR] Codex 调用失败：{e}")
        return None

    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        # 有些 codex 实现会把 JSON 打包在 stdout 的一部分，这里做个简单兜底
        try:
            start = out.index("{")
            end = out.rindex("}") + 1
            data = json.loads(out[start:end])
        except Exception as e:
            print(f"[ERROR] 解析 Codex JSON 失败：{e}")
            return None

    return data


def run_codex_loop(codex_report: dict) -> str:
    """
    调用一个预期存在的 codex-loop 子代理（你可以稍后创建 .claude/agents/codex-loop.md），
    让 Claude 读取 codex JSON 并按 SoT 规则修复代码。

    这里不直接改代码逻辑，而是把 codex JSON 丢给子代理处理。
    """
    serialized = json.dumps(codex_report, ensure_ascii=False, indent=2)
    prompt = dedent(f"""
    Use the codex-loop subagent to review and fix code issues.

    这是 Codex 对当前代码的审查结果（JSON）：

    --- CODEX REPORT BEGIN ---
    {serialized}
    --- CODEX REPORT END ---

    任务：
    - 按严重程度识别 P0 / P1 / P2 问题；
    - 结合项目的 SoT 文档（MASTER_SPEC / STATE_MACHINE / DATA_SCHEMA / API_SOT）判断：
      - 哪些是“真问题”；
      - 哪些是 Codex 误报（与 SoT 冲突的建议必须拒绝）。
    - 对确认的 P0 / P1 问题：
      - 使用 Edit 工具对对应代码文件做“最小必要修改”；
      - 每轮最多修 3～5 条；
      - 修改前后自检片段，避免引入新问题。

    输出：
    - 《Codex 问题处理摘要》：修了哪些问题，哪些被判为误报，哪些留待后续处理。
    """)
    return call_claude(prompt)


# ========== 主流程 ==========

def main():
    print("========== [1] 文档审查：doc-architect ==========")
    doc_architect_output = run_doc_architect()

    print("========== [2] 文档修复：doc-fixer ==========")
    doc_fixer_output = run_doc_fixer(doc_architect_output)

    # 这里你可以简单用字符串判断是否还有 P0/Missing，决定要不要多轮循环
    if "P0：" in doc_fixer_output or "P0:" in doc_fixer_output:
        print("[INFO] 仍存在 P0 问题，建议再跑一轮 doc-architect + doc-fixer 循环（手动或扩展脚本）。")

    print("========== [3] 代码审查：Codex ==========")
    changed_files = get_changed_code_files()
    print(f"[INFO] 检测到改动代码文件：{changed_files}")
    codex_report = run_codex_review(changed_files)

    if codex_report:
        print("========== [4] 代码修复：codex-loop 子代理（预留） ==========")
        run_codex_loop(codex_report)
    else:
        print("[INFO] 无 Codex 报告，跳过 codex-loop。")

    print("✅ 流水线执行结束（本轮）")


if __name__ == "__main__":
    main()
