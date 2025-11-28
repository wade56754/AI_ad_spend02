"""
claude_code_adapter.py

Claude Code CLI 适配器：通过 subprocess 调用 claude 命令行工具，
替代直接使用 Anthropic API，支持 Claude Max 订阅用户。

使用方式：
    from agents.tools.claude_code_adapter import call_claude_code

    result = call_claude_code(prompt, output_format="json")
"""

import subprocess
import json
import logging
import os
import re
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Claude Code CLI 配置
CLAUDE_CODE_CONFIG = {
    "command": "claude",  # Claude Code CLI 命令
    "timeout": 300,  # 超时时间（秒）
    "max_retries": 2,  # 最大重试次数
}


def _find_claude_cli() -> Optional[str]:
    """
    查找 claude CLI 可执行文件路径。

    Returns:
        claude CLI 路径，或 None（未找到）
    """
    # Windows: 尝试常见路径
    possible_paths = [
        "claude",  # 在 PATH 中
        "claude.exe",
        os.path.expanduser("~/.claude/claude.exe"),
        os.path.expanduser("~/AppData/Local/Programs/claude/claude.exe"),
    ]

    for path in possible_paths:
        try:
            result = subprocess.run(
                [path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                logger.debug(f"Found claude CLI at: {path}")
                return path
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            continue

    return None


def call_claude_code(
    prompt: str,
    output_format: str = "text",
    working_dir: Optional[Path] = None,
    timeout: Optional[int] = None,
) -> Dict[str, Any]:
    """
    通过 Claude Code CLI 调用 Claude 模型。

    Args:
        prompt: 发送给 Claude 的提示词
        output_format: 期望的输出格式 ("text" 或 "json")
        working_dir: 工作目录（默认当前目录）
        timeout: 超时时间（秒），默认使用配置值

    Returns:
        {
            "success": bool,
            "content": str,  # 原始响应内容
            "data": Any,     # 如果 output_format="json"，解析后的数据
            "error": Optional[str]
        }
    """
    claude_cli = _find_claude_cli()
    if not claude_cli:
        return {
            "success": False,
            "content": "",
            "data": None,
            "error": "Claude Code CLI 未找到。请确保已安装 Claude Code 并添加到 PATH。",
        }

    timeout = timeout or CLAUDE_CODE_CONFIG["timeout"]
    cwd = str(working_dir) if working_dir else None

    logger.info(f"Calling Claude Code CLI: timeout={timeout}s")
    logger.debug(f"Prompt length: {len(prompt)} chars")

    try:
        # 使用 -p 参数传递提示词（print mode，非交互）
        # Note: For very long prompts, consider using stdin instead
        cmd = [
            claude_cli,
            "-p", prompt,  # 直接传递提示词
            "--output-format", "text",  # 纯文本输出
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            encoding="utf-8",
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            logger.error(f"Claude CLI error (exit code {result.returncode}): {error_msg}")
            return {
                "success": False,
                "content": result.stdout,
                "data": None,
                "error": f"Claude CLI 返回错误 (exit {result.returncode}): {error_msg[:200]}",
            }

        content = result.stdout.strip()
        logger.debug(f"Claude response received: {len(content)} chars")

        # 解析 JSON（如果需要）
        data = None
        parse_error = None
        if output_format == "json":
            try:
                # 尝试从响应中提取 JSON
                data = _extract_json(content)
            except json.JSONDecodeError as e:
                parse_error = str(e)
                logger.warning(f"JSON parsing failed: {e}. Content preview: {content[:100]}...")
                # 不返回错误，保留原始内容供调用者处理

        return {
            "success": True,
            "content": content,
            "data": data,
            "error": None,
            "parse_warning": parse_error,  # 新增：JSON 解析警告
        }

    except subprocess.TimeoutExpired:
        logger.error(f"Claude CLI timeout after {timeout}s")
        return {
            "success": False,
            "content": "",
            "data": None,
            "error": f"Claude CLI 超时（{timeout}秒）。考虑增加 timeout 参数或简化 prompt。",
        }
    except FileNotFoundError:
        logger.error(f"Claude CLI not found at: {claude_cli}")
        return {
            "success": False,
            "content": "",
            "data": None,
            "error": f"Claude CLI 可执行文件未找到: {claude_cli}。请确保已正确安装。",
        }
    except Exception as e:
        logger.error(f"Claude CLI exception: {type(e).__name__}: {e}")
        return {
            "success": False,
            "content": "",
            "data": None,
            "error": f"Claude CLI 异常 ({type(e).__name__}): {str(e)[:200]}",
        }


def _extract_json(text: str) -> Any:
    """
    从文本中提取 JSON 数据。

    支持以下格式：
    1. 纯 JSON 文本
    2. Markdown 代码块中的 JSON (```json ... ```)
    3. 文本中间的 JSON 对象 {...}

    Args:
        text: 包含 JSON 的文本

    Returns:
        解析后的 Python 对象

    Raises:
        json.JSONDecodeError: 无法解析 JSON
    """
    text = text.strip()

    # 1. 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. 尝试提取 Markdown 代码块
    code_block_pattern = r"```(?:json)?\s*\n?([\s\S]*?)\n?```"
    matches = re.findall(code_block_pattern, text)
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue

    # 3. 尝试提取 {...} 或 [...]
    brace_pattern = r"(\{[\s\S]*\}|\[[\s\S]*\])"
    matches = re.findall(brace_pattern, text)
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue

    # 无法提取，抛出异常
    raise json.JSONDecodeError("No valid JSON found in text", text, 0)


def check_claude_code_available() -> Dict[str, Any]:
    """
    检查 Claude Code CLI 是否可用。

    Returns:
        {
            "available": bool,
            "path": Optional[str],  # CLI 路径
            "version": Optional[str],  # 版本信息
            "error": Optional[str]
        }
    """
    claude_cli = _find_claude_cli()
    if not claude_cli:
        return {
            "available": False,
            "path": None,
            "version": None,
            "error": "Claude Code CLI 未找到",
        }

    try:
        result = subprocess.run(
            [claude_cli, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        version = result.stdout.strip() if result.returncode == 0 else None

        return {
            "available": True,
            "path": claude_cli,
            "version": version,
            "error": None,
        }
    except Exception as e:
        return {
            "available": False,
            "path": claude_cli,
            "version": None,
            "error": str(e),
        }


# === 兼容层：模拟 Anthropic API 接口 ===


class ClaudeCodeClient:
    """
    模拟 Anthropic Client 的接口，内部使用 Claude Code CLI。

    用于替换现有代码中的 Anthropic() 调用：
        # 原来:
        client = Anthropic()
        resp = client.messages.create(...)

        # 改为:
        client = ClaudeCodeClient()
        resp = client.messages.create(...)
    """

    def __init__(self):
        self.messages = _MessagesAPI()


class _MessagesAPI:
    """模拟 client.messages 接口"""

    def create(
        self,
        model: str = "claude-3-5-sonnet",
        max_tokens: int = 8000,
        temperature: float = 0,
        messages: list = None,
        **kwargs,
    ) -> "_MockResponse":
        """
        模拟 Anthropic messages.create() 方法。

        P1-AG-002 增强：记录并传递 model/temperature 参数（用于日志和未来扩展）。
        注意：Claude Code CLI 当前版本不支持运行时切换模型，参数仅用于日志记录。

        Args:
            model: 模型名称（记录到日志，CLI 模式下使用用户默认模型）
            max_tokens: 最大 token 数（CLI 模式下由 Claude Code 控制）
            temperature: 温度参数（CLI 模式下暂不支持）
            messages: 消息列表
            **kwargs: 其他参数（system 等）
        """
        messages = messages or []

        # P1-AG-002: 记录请求参数（便于调试）
        logger.debug(
            f"ClaudeCodeClient.create: model={model}, max_tokens={max_tokens}, "
            f"temperature={temperature}, messages_count={len(messages)}"
        )

        # 提取用户消息内容
        prompt_parts = []

        # 处理 system 参数（如果提供）
        system_prompt = kwargs.get("system")
        if system_prompt:
            prompt_parts.append(f"[SYSTEM]\n{system_prompt}")

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if isinstance(content, list):
                # 处理多部分内容
                content = "\n".join(
                    part.get("text", "")
                    for part in content
                    if part.get("type") == "text"
                )
            prompt_parts.append(f"[{role.upper()}]\n{content}")

        prompt = "\n\n".join(prompt_parts)

        # 调用 Claude Code CLI
        # 注意：未来若 Claude CLI 支持 --model 参数，可在此处添加
        result = call_claude_code(prompt, output_format="text")

        if not result["success"]:
            raise RuntimeError(result["error"])

        return _MockResponse(result["content"])


class _MockResponse:
    """模拟 Anthropic API 响应对象"""

    def __init__(self, text: str):
        self.content = [_MockTextBlock(text)]


class _MockTextBlock:
    """模拟响应中的文本块"""

    def __init__(self, text: str):
        self.type = "text"
        self.text = text


# 导出
__all__ = [
    "call_claude_code",
    "check_claude_code_available",
    "ClaudeCodeClient",
    "CLAUDE_CODE_CONFIG",
    "_extract_json",  # Used by fe_dev_skill/be_dev_skill for fallback JSON parsing
]
