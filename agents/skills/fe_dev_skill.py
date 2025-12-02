from typing import List, Dict, Any
import json
import logging

from ..agents_config import SOT_FILES, FRONTEND_DIR, LLM_CONFIG, read_optional
from ..tools.fs_tool import read_files
from ..tools.validation import validate_task_and_files
from ..tools.types import SkillResult
# Phase 2: 使用 agent_platform.llm 统一入口
from agent_platform.llm import get_llm_client, extract_response_text
from ..tools.claude_code_adapter import _extract_json

logger = logging.getLogger(__name__)


def _build_fe_prompt(task: str, existing_files: Dict[str, str]) -> str:
    """
    Build frontend code generation prompt with SoT context.

    Structure:
        - SYSTEM: Role definition, tech stack (Next.js/React/Tailwind/shadcn)
        - CONTEXT: Loads MASTER, API_SOT, FRONTEND_RULES, UI_DESIGN_SYSTEM
        - EXISTING_FRONTEND_FILES: Current code to be modified
        - TASK: User's task description
        - THINKING_CHAIN: Step-by-step reasoning guide for LLM
        - OUTPUT_FORMAT: JSON schema with 'changes' and 'notes' fields

    Returns:
        Complete prompt string for Claude API
    """
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


def fe_dev_skill(task: str, target_files: List[str]) -> SkillResult:
    """
    前端开发 Skill：生成前端代码变更。

    Args:
        task: 任务描述
        target_files: 目标文件列表

    Returns:
        {
            "success": bool,
            "data": {
                "changes": Dict[str, str],  # 文件路径 -> 新内容
                "notes": List[str]
            },
            "error": Optional[str]
        }
    """
    # 参数校验（使用统一函数）
    validation_error = validate_task_and_files(task, target_files)
    if validation_error:
        logger.warning(f"FE Skill validation failed: {validation_error['error']}")
        return validation_error

    logger.info(f"FE Skill started: task='{task[:60]}...' files={len(target_files)}")

    # 读取现有文件
    existing = read_files(FRONTEND_DIR, target_files)
    prompt = _build_fe_prompt(task, existing)

    # Fix: P1-03 - 使用统一的 LLM 客户端
    try:
        client = get_llm_client()
        logger.debug(f"Calling LLM: model={LLM_CONFIG['model']}")
        resp = client.messages.create(
            model=LLM_CONFIG["model"],
            max_tokens=LLM_CONFIG["max_tokens"],
            temperature=LLM_CONFIG["temperature"],
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:
        logger.error(f"LLM API error: {e}")
        return {
            "success": False,
            "data": None,
            "error": f"LLM API error: {e}",
        }

    # Fix: P1-03 - 使用统一的响应提取函数
    text = extract_response_text(resp)
    logger.debug(f"API response received: {len(text)} chars")

    # 解析 JSON
    try:
        data = json.loads(text)
    except json.JSONDecodeError as parse_error:
        # Try to extract JSON from markdown code blocks or embedded JSON
        try:
            data = _extract_json(text)
        except json.JSONDecodeError:
            logger.error(f"JSON parsing failed: {parse_error}")
            return {
                "success": False,
                "data": None,
                "error": f"模型返回内容不是合法 JSON: {str(parse_error)[:100]}",
                "raw": text[:500],  # 保留前500字符便于调试
            }

    # 提取 changes
    changes_spec = data.get("changes", [])
    changes: Dict[str, str] = {}
    for item in changes_spec:
        path = item.get("file")
        content = item.get("content")
        if isinstance(path, str) and isinstance(content, str):
            changes[path] = content

    logger.info(f"FE Skill completed: {len(changes)} files generated")

    # 注意：不再自动写入文件，由 Agent 层决定是否写入
    return {
        "success": True,
        "data": {
            "changes": changes,  # 返回完整内容，而非文件名列表
            "notes": data.get("notes", []),
        },
        "error": None,
    }
