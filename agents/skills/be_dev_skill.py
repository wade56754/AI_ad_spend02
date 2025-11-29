from typing import List, Dict, Any
import json
import logging

from ..agents_config import SOT_FILES, BACKEND_DIR, LLM_CONFIG, read_optional
from ..tools.fs_tool import read_files
from ..tools.validation import validate_task_and_files
from ..tools.types import SkillResult
# Fix: P1-03 - 使用统一的 LLM 客户端模块，移除重复代码
from ..tools.llm_client import get_llm_client, extract_response_text
from ..tools.claude_code_adapter import _extract_json

logger = logging.getLogger(__name__)


def _build_be_prompt(task: str, existing_files: Dict[str, str]) -> str:
    """
    Build backend code generation prompt with SoT context.

    Structure:
        - SYSTEM: Role definition and tech stack constraints
        - CONTEXT: Loads 6 SoT documents (MASTER, DATA_SCHEMA, STATE_MACHINE, etc.)
        - EXISTING_BACKEND_FILES: Current code to be modified
        - TASK: User's task description
        - THINKING_CHAIN: Step-by-step reasoning guide for LLM
        - OUTPUT_FORMAT: JSON schema with 'changes' and 'notes' fields

    Returns:
        Complete prompt string for Claude API
    """
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


def be_dev_skill(task: str, target_files: List[str]) -> SkillResult:
    """
    后端开发 Skill：生成后端代码变更。

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
        logger.warning(f"BE Skill validation failed: {validation_error['error']}")
        return validation_error

    logger.info(f"BE Skill started: task='{task[:60]}...' files={len(target_files)}")

    # 读取现有文件
    existing = read_files(BACKEND_DIR, target_files)
    prompt = _build_be_prompt(task, existing)

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

    logger.info(f"BE Skill completed: {len(changes)} files generated")

    # 注意：不再自动写入文件，由 Agent 层决定是否写入
    return {
        "success": True,
        "data": {
            "changes": changes,  # 返回完整内容，而非文件名列表
            "notes": data.get("notes", []),
        },
        "error": None,
    }
