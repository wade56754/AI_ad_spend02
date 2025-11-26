from typing import List, Dict, Any
from anthropic import Anthropic, APIStatusError
import json

from agents_config import SOT_FILES, FRONTEND_DIR, read_optional
from tools.fs_tool import read_files, write_files


client = Anthropic()  # 依赖环境变量 ANTHROPIC_API_KEY


def _build_fe_prompt(task: str, existing_files: Dict[str, str]) -> str:
    master = read_optional(SOT_FILES["MASTER"])
    api_sot = read_optional(SOT_FILES["API_SOT"])
    fe_rules = read_optional(SOT_FILES["FRONTEND_RULES"])
    ui_system = read_optional(SOT_FILES["UI_DESIGN_SYSTEM"])

    files_block = []
    for path, content in existing_files.items():
        files_block.append(f"<!-- FILE: {path} -->\n{content}")
    files_combined = "\n\n".join(files_block)

    return f"""
<SYSTEM>
你是一个严格遵守规范的“前端开发 Agent”，技术栈：
- Next.js 14+ / React + TypeScript
- Tailwind CSS
- shadcn/ui 组件库

你必须：
- 遵守项目的前端开发规范和 UI 设计系统
- 不随意创建新 API / 新数据库字段
- 尽量通过组合现有组件实现需求
- 输出**完整文件内容**，而不是补丁片段
</SYSTEM>

<CONTEXT>
<DOC MASTER>
{master}
</DOC>

<DOC API_SOT>
{api_sot}
</DOC>

<DOC FRONTEND_RULES>
{fe_rules}
</DOC>

<DOC UI_DESIGN_SYSTEM>
{ui_system}
</DOC>

<EXISTING_FRONTEND_FILES>
{files_combined}
</EXISTING_FRONTEND_FILES>
</CONTEXT>

<TASK>
{task}
</TASK>

<THINKING_CHAIN>
1. 粗略阅读需求和现有 TSX 文件结构。
2. 根据 FRONTEND_RULES 和 UI_DESIGN_SYSTEM 规划本次修改方案：
   - 需要修改/新增的组件列表
   - 重要状态/props 设计
   - 与后端 API 的交互方式（仅使用 API_SOT 中已有接口）。
3. 按规划生成新的 TSX/TS 文件完整内容。
4. 自检：
   - TypeScript 是否可能报错？
   - 是否违反前端规范或 UI 设计系统？
   - 有无明显逻辑漏洞或状态不同步问题？
</THINKING_CHAIN>

<OUTPUT_FORMAT>
只允许输出一段 JSON，不能包含多余说明文字。JSON 结构如下：

{{
  "changes": [
    {{
      "file": "app/dashboard/page.tsx",
      "content": "该文件的新完整内容"
    }}
  ],
  "notes": [
    "自检说明 1",
    "自检说明 2"
  ]
}}
</OUTPUT_FORMAT>
""".strip()


def fe_dev_skill(task: str, target_files: List[str]) -> Dict[str, Any]:
    existing = read_files(FRONTEND_DIR, target_files)
    prompt = _build_fe_prompt(task, existing)

    try:
        resp = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=8000,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
    except APIStatusError as e:
        return {"ok": False, "error": f"Anthropic API error: {e}"}

    # 兼容 text / json 两种返回
    text = "".join(
        block.text for msg in resp.content for block in (msg if isinstance(msg, list) else [msg])
        if getattr(block, "type", None) == "text"
    ) if hasattr(resp, "content") else str(resp)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"ok": False, "error": "模型返回内容不是合法 JSON", "raw": text}

    changes_spec = data.get("changes", [])
    changes: Dict[str, str] = {}
    for item in changes_spec:
        path = item.get("file")
        content = item.get("content")
        if isinstance(path, str) and isinstance(content, str):
            changes[path] = content

    if changes:
        write_files(FRONTEND_DIR, changes)

    return {
        "ok": True,
        "changes": list(changes.keys()),
        "notes": data.get("notes", []),
    }
