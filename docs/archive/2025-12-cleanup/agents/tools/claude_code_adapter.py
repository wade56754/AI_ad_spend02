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
import time
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Claude Code CLI 配置
# Fix: P2-10 - 增加默认超时时间，LLM 调用可能需要较长时间
# Fix: P1-02 - 添加重试机制配置
CLAUDE_CODE_CONFIG = {
    "command": "claude",  # Claude Code CLI 命令
    "timeout": 300,  # 默认超时时间（秒）- 5分钟
    "timeout_simple": 120,  # 简单请求超时（秒）- 2分钟
    "timeout_complex": 600,  # 复杂请求超时（秒）- 10分钟
    "max_retries": 2,  # 最大重试次数
    "retry_delay": 2.0,  # 重试初始延迟（秒）
    "retry_backoff": 2.0,  # 重试延迟倍数（指数退避）
}


# Fix: P1-02 - 可重试的错误类型
_RETRYABLE_ERRORS = (
    subprocess.TimeoutExpired,  # 超时
    OSError,  # 进程启动失败等
)


def _find_claude_cli() -> Optional[str]:
    """
    查找 claude CLI 可执行文件路径。

    Returns:
        claude CLI 路径，或 None（未找到）
    """
    # Windows: 尝试常见路径
    possible_paths = [
        "claude",  # 在 PATH 中（最高优先级）
        "claude.exe",
        "claude.cmd",  # npm 安装的 cmd 包装器
    ]
    
    # 添加 Windows 特定路径
    if os.name == "nt":  # Windows
        appdata = os.environ.get("APPDATA", "")
        localappdata = os.environ.get("LOCALAPPDATA", "")
        userprofile = os.environ.get("USERPROFILE", "")
        current_dir = os.getcwd()
        
        windows_paths = [
            # npm 全局安装路径（优先）
            os.path.join(appdata, "npm", "claude.cmd"),
            os.path.join(appdata, "npm", "claude"),
            # 用户本地 bin
            os.path.join(userprofile, ".local", "bin", "claude.exe"),
            # 项目目录下的批处理文件
            os.path.join(current_dir, "claude.bat"),
            # 常见安装路径
            os.path.expanduser("~/.claude/claude.exe"),
            os.path.join(localappdata, "Programs", "claude", "claude.exe"),
            os.path.join(localappdata, "Claude", "claude.exe"),
            # Program Files
            "C:\\Program Files\\Claude\\claude.exe",
            "C:\\Program Files (x86)\\Claude\\claude.exe",
        ]
        possible_paths.extend(windows_paths)
    else:
        # Unix-like 系统
        unix_paths = [
            os.path.expanduser("~/.local/bin/claude"),
            os.path.expanduser("~/.claude/claude"),
            "/usr/local/bin/claude",
            "/usr/bin/claude",
        ]
        possible_paths.extend(unix_paths)

    for path in possible_paths:
        try:
            # Windows 上，对于 .cmd 和 .bat 文件，可能需要使用 shell=True
            use_shell = os.name == "nt" and (
                path.endswith(".cmd") or 
                path.endswith(".bat") or 
                path.endswith(".exe")
            )
            
            result = subprocess.run(
                [path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                shell=use_shell,
            )
            if result.returncode == 0:
                logger.debug(f"Found claude CLI at: {path}")
                return path
        except (subprocess.SubprocessError, FileNotFoundError, OSError) as e:
            logger.debug(f"Failed to test path {path}: {e}")
            continue

    return None


def call_claude_code(
    prompt: str,
    output_format: str = "text",
    working_dir: Optional[Path] = None,
    timeout: Optional[int] = None,
    max_retries: Optional[int] = None,
) -> Dict[str, Any]:
    """
    通过 Claude Code CLI 调用 Claude 模型（带重试机制）。

    Fix: P1-02 - 添加重试机制，处理临时性错误

    Args:
        prompt: 发送给 Claude 的提示词
        output_format: 期望的输出格式 ("text" 或 "json")
        working_dir: 工作目录（默认当前目录）
        timeout: 超时时间（秒），默认使用配置值
        max_retries: 最大重试次数，默认使用配置值

    Returns:
        {
            "success": bool,
            "content": str,  # 原始响应内容
            "data": Any,     # 如果 output_format="json"，解析后的数据
            "error": Optional[str],
            "retries": int,  # 实际重试次数
        }
    """
    claude_cli = _find_claude_cli()
    if not claude_cli:
        return {
            "success": False,
            "content": "",
            "data": None,
            "error": "Claude Code CLI 未找到。请确保已安装 Claude Code 并添加到 PATH。",
            "retries": 0,
        }

    timeout = timeout or CLAUDE_CODE_CONFIG["timeout"]
    max_retries = max_retries if max_retries is not None else CLAUDE_CODE_CONFIG["max_retries"]
    retry_delay = CLAUDE_CODE_CONFIG["retry_delay"]
    retry_backoff = CLAUDE_CODE_CONFIG["retry_backoff"]
    cwd = str(working_dir) if working_dir else None

    logger.info(f"Calling Claude Code CLI: timeout={timeout}s, max_retries={max_retries}")
    logger.debug(f"Prompt length: {len(prompt)} chars")

    # Windows 上，对于 .cmd 和 .bat 文件，或者简单的命令名（需要 PATH 解析），使用 shell=True
    use_shell = False
    if os.name == "nt":  # Windows
        if claude_cli.endswith((".cmd", ".bat")):
            use_shell = True
        elif not os.path.isabs(claude_cli):
            if not os.path.exists(claude_cli):
                use_shell = True

    cmd = [
        claude_cli,
        "-p", prompt,  # 直接传递提示词
        "--output-format", "text",  # 纯文本输出
    ]

    last_error: Optional[str] = None
    retries = 0

    for attempt in range(max_retries + 1):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                encoding="utf-8",
                shell=use_shell,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                # 非零退出码，部分情况可重试（如临时网络问题）
                # 但大部分非零退出码是永久性错误，不重试
                logger.error(f"Claude CLI error (exit code {result.returncode}): {error_msg}")
                return {
                    "success": False,
                    "content": result.stdout,
                    "data": None,
                    "error": f"Claude CLI 返回错误 (exit {result.returncode}): {error_msg[:200]}",
                    "retries": retries,
                }

            content = result.stdout.strip()
            logger.debug(f"Claude response received: {len(content)} chars (attempt {attempt + 1})")

            # 解析 JSON（如果需要）
            data = None
            parse_error = None
            if output_format == "json":
                try:
                    data = _extract_json(content)
                except json.JSONDecodeError as e:
                    parse_error = str(e)
                    logger.warning(f"JSON parsing failed: {e}. Content preview: {content[:100]}...")

            return {
                "success": True,
                "content": content,
                "data": data,
                "error": None,
                "parse_warning": parse_error,
                "retries": retries,
            }

        except subprocess.TimeoutExpired:
            last_error = f"Claude CLI 超时（{timeout}秒）"
            retries = attempt
            if attempt < max_retries:
                delay = retry_delay * (retry_backoff ** attempt)
                logger.warning(
                    f"Claude CLI timeout (attempt {attempt + 1}/{max_retries + 1}), "
                    f"retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
            else:
                logger.error(f"Claude CLI timeout after {max_retries + 1} attempts")

        except FileNotFoundError:
            # 不可重试：CLI 不存在
            logger.error(f"Claude CLI not found at: {claude_cli}")
            return {
                "success": False,
                "content": "",
                "data": None,
                "error": f"Claude CLI 可执行文件未找到: {claude_cli}。请确保已正确安装。",
                "retries": retries,
            }

        except OSError as e:
            # 可重试：进程启动失败等
            last_error = f"Claude CLI OSError: {e}"
            retries = attempt
            if attempt < max_retries:
                delay = retry_delay * (retry_backoff ** attempt)
                logger.warning(
                    f"Claude CLI OSError (attempt {attempt + 1}/{max_retries + 1}): {e}, "
                    f"retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
            else:
                logger.error(f"Claude CLI OSError after {max_retries + 1} attempts: {e}")

        except Exception as e:
            # 其他异常：不重试
            logger.error(f"Claude CLI exception: {type(e).__name__}: {e}")
            return {
                "success": False,
                "content": "",
                "data": None,
                "error": f"Claude CLI 异常 ({type(e).__name__}): {str(e)[:200]}",
                "retries": retries,
            }

    # 所有重试都失败
    return {
        "success": False,
        "content": "",
        "data": None,
        "error": f"{last_error}。已重试 {max_retries} 次。考虑增加 timeout 参数或简化 prompt。",
        "retries": retries,
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
