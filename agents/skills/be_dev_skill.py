from typing import List, Dict, Any
from anthropic import Anthropic, APIStatusError
import json

from agents_config import SOT_FILES, BACKEND_DIR, read_optional
from tools.fs_tool import read_files, write_files


client = Anthropic()


def _build_be_prompt(task: str, existing_files: Dict[str, str]) -> str:
    master = read_optional(SOT_FILES["MASTER"])
    data_schema = read_optional(SOT_FILES["DATA_SCHEMA"])
    state_machine = read_optional(SOT_FILES["STATE_MACHINE"])
    business_rules = read_optional(SOT_FILES["BUSINESS_RULES"])
    api_sot = read_optional(SOT_FILES["API_SOT"])
    error_codes = read_optional(SOT_FILES["ERROR_CODES"])

    files_block = []
    for path, content in existing_files.items():
        files_block.append(f"<!-- FILE: {path} -->\n{content}")
    files_combined = "\n\n".join(files_block)

    return f"""
<SYSTEM>
你是“后端开发 Agent”，负责在现有 FastAPI + SQLAlchemy + Pydantic v2 项目中实现/重构接口和 Service。

必须遵守：
- DATA_SCHEMA / STATE_MACHINE / BUSINESS_RULES / API_SOT / ERROR_CODES 作为唯一事实来源
- 不自行发明新的枚举值、状态机、字段
- 统一 ErrorCode 枚举与错误响应结构
- 严格类型标注，避免 any、裸 dict

技术栈假设：
- FastAPI
- SQLAlchemy 2.x（声明式映射）
- Pydantic v2
</SYSTEM>

<CONTEXT>
<DOC MASTER>
{master}
</DOC>

<DOC DATA_SCHEMA>
{data_schema}
</DOC>

<DOC STATE_MACHINE>
{state_machine}
</DOC>

<DOC BUSINESS_RULES>
{business_rules}
</DOC>

<DOC API_SOT>
{api_sot}
</DOC>

<DOC ERROR_CODES>
{error_codes}
</DOC>

<EXISTING_BACKEND_FILES>
{files_combined}
</EXISTING_BACKEND_FILES>
</CONTEXT>

<TASK>
{task}
</TASK>

<THINKING_CHAIN>
1. 从 API_SOT 和 BUSINESS_RULES 中锁定本次要实现/修改的 API 和业务流程。
2. 检查 DATA_SCHEMA / STATE_MACHINE 是否有相关字段和状态机约束。
3. 规划具体改动：
   - Pydantic 模型
   - Service 层函数
   - Router 层路由和依赖
   - 错误码和校验逻辑
4. 生成完整代码文件内容。
5. 自检：
   - 类型是否自洽
   - 是否违背状态机和业务规则
   - 错误码是否统一且在 ERROR_CODES 中注册
</THINKING_CHAIN>

<OUTPUT_FORMAT>
只输出一段 JSON：

{{
  "changes": [
    {{
      "file": "app/routers/topup_router.py",
      "content": "新文件完整内容"
    }}
  ],
  "notes": [
    "你对本次改动的自检说明",
    "潜在风险提示"
  ]
}}
</OUTPUT_FORMAT>
""".strip()


def be_dev_skill(task: str, target_files: List[str]) -> Dict[str, Any]:
    existing = read_files(BACKEND_DIR, target_files)
    prompt = _build_be_prompt(task, existing)

    try:
        resp = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=8000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
    except APIStatusError as e:
        return {"ok": False, "error": f"Anthropic API error: {e}"}

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
        write_files(BACKEND_DIR, changes)

    return {
        "ok": True,
        "changes": list(changes.keys()),
        "notes": data.get("notes", []),
    }
