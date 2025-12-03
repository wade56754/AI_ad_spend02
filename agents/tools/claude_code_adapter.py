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
import shutil
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


def _run_cli(
    cli_path: str,
    args: list[str],
    *,
    timeout: Optional[int] = None,
    cwd: Optional[str] = None,
    input: Optional[str] = None,
    capture_output: bool = True,
    text: bool = True,
) -> subprocess.CompletedProcess:
    """
    统一的 CLI 执行助手。

    使用列表形式的命令参数，shell=False，确保与 check_claude_code_available()
    使用完全相同的调用方式。

    Args:
        cli_path: 已解析的 CLI 绝对路径
        args: 命令参数列表（不包含 CLI 路径本身）
        timeout: 超时时间（秒）
        cwd: 工作目录
        input: 输入内容（传递给 stdin）
        capture_output: 是否捕获输出
        text: 是否以文本模式处理输出

    Returns:
        subprocess.CompletedProcess 对象

    Raises:
        FileNotFoundError: CLI 文件不存在
        subprocess.TimeoutExpired: 超时
        OSError: 其他执行错误
    """
    # 构建完整命令列表：cli_path + args
    cmd = [cli_path] + args

    # 记录执行的命令（不包含敏感内容如完整 prompt）
    logger.debug(f"Executing CLI command: {cmd[:3]}... (total {len(cmd)} args)")

    try:
        result = subprocess.run(
            cmd,
            input=input,
            capture_output=capture_output,
            text=text,
            timeout=timeout,
            cwd=cwd,
            encoding="utf-8",
            errors="replace",  # 防御性编码处理
            shell=False,  # 统一使用 shell=False，避免 Windows 上的路径问题
        )
        return result
    except (FileNotFoundError, OSError) as e:
        # Windows 上可能出现 WinError 206（文件名或扩展名太长）
        # 需要先检查是否是 WinError 206，因为它在 Windows 上可能被作为 FileNotFoundError 或 OSError 抛出
        error_code = None
        if hasattr(e, 'winerror'):
            error_code = e.winerror
        elif hasattr(e, 'errno') and os.name == 'nt':
            # Windows 上 errno 206 对应 WinError 206
            if e.errno == 206:
                error_code = 206
        
        if error_code == 206:
            logger.error(
                f"Claude CLI command too long (WinError 206). "
                f"CLI path: {cli_path}, Args count: {len(args)}"
            )
            raise RuntimeError(
                f"Claude CLI 命令过长（Windows 限制）。请简化 prompt 或使用 Anthropic API。"
            ) from e
        
        # 对于 FileNotFoundError（非 WinError 206），认为是文件不存在
        if isinstance(e, FileNotFoundError):
            logger.error(
                f"Claude CLI not found at: {cli_path}. "
                f"Command: {cmd[:3]}..., Error: {e}"
            )
            raise RuntimeError(
                f"Claude CLI 可执行文件未找到: {cli_path}。请确保已正确安装。"
            ) from e
        
        # 对于其他 OSError，转换为 RuntimeError 以保持一致性
        logger.error(f"Claude CLI OSError: {e}. Command: {cmd[:3]}...")
        raise RuntimeError(
            f"Claude CLI 执行失败: {e}"
        ) from e
    except subprocess.TimeoutExpired as e:
        logger.error(f"Claude CLI timeout after {timeout}s. Command: {cmd[:3]}...")
        raise


def _resolve_cli_path(cli_path: str) -> Optional[str]:
    """
    解析 CLI 可执行文件路径。

    支持两种模式：
    1. 绝对路径或显式文件路径（包含路径分隔符或显式后缀）：
       - 直接检查文件是否存在
    2. 命令名（如 "claude"）：
       - 使用 shutil.which 在 PATH 中查找

    Args:
        cli_path: CLI 路径或命令名

    Returns:
        解析后的绝对路径，或 None（未找到）
    """
    path_obj = Path(cli_path)

    # 判断是否为文件路径模式（绝对路径、包含路径分隔符、或显式后缀）
    is_file_path = (
        path_obj.is_absolute()
        or os.sep in cli_path
        or os.altsep in cli_path if os.altsep else False
        or cli_path.lower().endswith(('.exe', '.cmd', '.bat', '.ps1', '.sh'))
    )

    if is_file_path:
        # 文件路径模式：检查文件是否存在
        if path_obj.exists():
            resolved = str(path_obj.resolve())
            logger.debug(f"Resolved CLI path (file): {cli_path} -> {resolved}")
            return resolved
        else:
            logger.debug(f"CLI file path not found: {cli_path}")
            return None
    else:
        # 命令名模式：使用 shutil.which 在 PATH 中查找
        resolved = shutil.which(cli_path)
        if resolved:
            # 确保返回绝对路径
            resolved_path = Path(resolved).resolve()
            logger.debug(f"Resolved CLI path (command): {cli_path} -> {resolved_path}")
            return str(resolved_path)
        else:
            logger.debug(f"CLI command not found in PATH: {cli_path}")
            return None


def _find_claude_cli() -> Optional[str]:
    """
    查找 claude CLI 可执行文件路径。

    优先使用 PATH 解析，然后尝试常见安装路径。

    Returns:
        claude CLI 绝对路径，或 None（未找到）
    """
    # 优先级 1: 环境变量指定的路径
    env_path = os.environ.get("CLAUDE_CLI_PATH")
    if env_path:
        resolved = _resolve_cli_path(env_path)
        if resolved:
            return resolved

    # 优先级 2: 命令名 "claude"（通过 PATH 解析）
    resolved = _resolve_cli_path("claude")
    if resolved:
        return resolved

    # 优先级 3: 尝试常见路径（Windows 特定）
    if os.name == "nt":  # Windows
        appdata = os.environ.get("APPDATA", "")
        localappdata = os.environ.get("LOCALAPPDATA", "")
        userprofile = os.environ.get("USERPROFILE", "")
        current_dir = os.getcwd()

        windows_paths = [
            os.path.join(appdata, "npm", "claude.cmd"),
            os.path.join(appdata, "npm", "claude"),
            os.path.join(userprofile, ".local", "bin", "claude.exe"),
            os.path.join(current_dir, "claude.bat"),
            os.path.expanduser("~/.claude/claude.exe"),
            os.path.join(localappdata, "Programs", "claude", "claude.exe"),
            os.path.join(localappdata, "Claude", "claude.exe"),
            "C:\\Program Files\\Claude\\claude.exe",
            "C:\\Program Files (x86)\\Claude\\claude.exe",
        ]

        for path in windows_paths:
            resolved = _resolve_cli_path(path)
            if resolved:
                return resolved
    else:
        # Unix-like 系统
        unix_paths = [
            os.path.expanduser("~/.local/bin/claude"),
            os.path.expanduser("~/.claude/claude"),
            "/usr/local/bin/claude",
            "/usr/bin/claude",
        ]

        for path in unix_paths:
            resolved = _resolve_cli_path(path)
            if resolved:
                return resolved

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

    # claude_cli 现在已经是解析后的绝对路径

    timeout = timeout or CLAUDE_CODE_CONFIG["timeout"]
    max_retries = max_retries if max_retries is not None else CLAUDE_CODE_CONFIG["max_retries"]
    retry_delay = CLAUDE_CODE_CONFIG["retry_delay"]
    retry_backoff = CLAUDE_CODE_CONFIG["retry_backoff"]
    cwd = str(working_dir) if working_dir else None

    logger.info(f"Calling Claude Code CLI: timeout={timeout}s, max_retries={max_retries}")
    logger.debug(f"Prompt length: {len(prompt)} chars")

    # 构建命令参数列表（统一使用列表形式，shell=False）
    cmd_args = [
        "-p", prompt,  # 直接传递提示词
        "--output-format", "text",  # 纯文本输出
    ]

    last_error: Optional[str] = None
    retries = 0

    for attempt in range(max_retries + 1):
        try:
            # 使用统一的 _run_cli() 方法
            result = _run_cli(
                cli_path=claude_cli,
                args=cmd_args,
                timeout=timeout,
                cwd=cwd,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                # 收集错误信息：优先 stderr，其次 stdout（某些 CLI 可能将错误输出到 stdout）
                error_msg = result.stderr.strip() if result.stderr else ""
                if not error_msg and result.stdout:
                    # 检查 stdout 是否包含错误信息
                    stdout_lines = result.stdout.strip().split('\n')
                    error_lines = [line for line in stdout_lines if any(keyword in line.lower() for keyword in ['error', '失败', '错误', 'failed', 'invalid', 'fix'])]
                    if error_lines:
                        error_msg = '\n'.join(error_lines)
                
                if not error_msg:
                    # 如果仍然没有错误信息，使用 stdout 的前几行作为错误信息
                    if result.stdout:
                        error_msg = result.stdout.strip().split('\n')[0][:200]
                    else:
                        error_msg = "Unknown error (no stderr or stdout output)"
                
                # 非零退出码，部分情况可重试（如临时网络问题）
                # 但大部分非零退出码是永久性错误，不重试
                logger.error(
                    f"Claude CLI error (exit code {result.returncode}): {error_msg[:500]}\n"
                    f"Stdout: {result.stdout[:200] if result.stdout else 'None'}\n"
                    f"Stderr: {result.stderr[:200] if result.stderr else 'None'}"
                )
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

        except RuntimeError as e:
            # 不可重试：CLI 不存在（_run_cli 已转换为 RuntimeError）
            error_msg = str(e)
            logger.error(f"Claude CLI execution failed: {error_msg}")
            return {
                "success": False,
                "content": "",
                "data": None,
                "error": error_msg,
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
    logger.debug(f"_extract_json: input text length={len(text)}, first 100 chars: {text[:100]}")

    # 1. 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. 尝试提取 Markdown 代码块（改进：支持多行和更灵活的匹配）
    # 匹配 ```json 或 ``` 开头的代码块，非贪婪匹配到第一个 ```
    code_block_pattern = r"```(?:json)?\s*\n([\s\S]*?)\n```"
    matches = re.findall(code_block_pattern, text, re.MULTILINE | re.DOTALL)
    logger.debug(f"_extract_json: pattern 1 found {len(matches)} matches")
    for i, match in enumerate(matches):
        try:
            cleaned = match.strip()
            if cleaned:
                logger.debug(f"_extract_json: trying to parse match {i+1}, length={len(cleaned)}")
                return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.debug(f"_extract_json: match {i+1} parse failed: {e}")
            continue
    
    # 2.1 尝试更宽松的代码块匹配（不要求换行）
    code_block_pattern_loose = r"```(?:json)?\s*([\s\S]*?)```"
    matches = re.findall(code_block_pattern_loose, text)
    logger.debug(f"_extract_json: pattern 2 (loose) found {len(matches)} matches")
    for i, match in enumerate(matches):
        try:
            cleaned = match.strip()
            if cleaned:
                logger.debug(f"_extract_json: trying to parse loose match {i+1}, length={len(cleaned)}")
                return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.debug(f"_extract_json: loose match {i+1} parse failed: {e}, first 200 chars: {cleaned[:200]}")
            continue

    # 2.2 如果代码块匹配失败，尝试直接查找代码块标记之间的内容
    # 查找第一个 ```json 或 ``` 到最后一个 ``` 之间的内容
    start_marker = text.find("```")
    if start_marker != -1:
        # 找到开始标记后的内容
        content_start = text.find("\n", start_marker)
        if content_start == -1:
            content_start = text.find("```", start_marker + 3)
            if content_start != -1:
                content_start += 3
        else:
            content_start += 1
        
        # 从后往前找最后一个 ```
        end_marker = text.rfind("```")
        if end_marker != -1 and end_marker > content_start:
            json_content = text[content_start:end_marker].strip()
            if json_content:
                try:
                    logger.debug(f"_extract_json: trying to parse content between markers, length={len(json_content)}")
                    return json.loads(json_content)
                except json.JSONDecodeError:
                    pass

    # 2.3 最简单的方法：直接查找第一个 { 和最后一个 }，尝试解析
    # 这样可以处理任何格式的 JSON，包括代码块中的
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_candidate = text[first_brace:last_brace+1]
        try:
            logger.debug(f"_extract_json: trying to parse from first {{ to last }}, length={len(json_candidate)}")
            parsed = json.loads(json_candidate)
            logger.info(f"_extract_json: Successfully parsed JSON using first-last brace method, length={len(json_candidate)}")
            return parsed
        except json.JSONDecodeError as e:
            logger.warning(f"_extract_json: first-last brace method failed: {e}")
            logger.warning(f"_extract_json: JSON candidate first 500 chars: {json_candidate[:500]}")
            logger.warning(f"_extract_json: JSON candidate last 500 chars: {json_candidate[-500:]}")
            # 尝试使用 raw_decode 来找到 JSON 的实际结束位置
            try:
                decoder = json.JSONDecoder()
                parsed, idx = decoder.raw_decode(text, first_brace)
                logger.info(f"_extract_json: Successfully parsed JSON using raw_decode, ended at position {idx}")
                return parsed
            except json.JSONDecodeError as e2:
                logger.warning(f"_extract_json: raw_decode also failed: {e2}")

    # 3. 尝试提取 {...} 或 [...]（改进：从第一个 { 或 [ 开始，匹配到对应的结束符）
    # 先尝试找到第一个 { 或 [
    first_brace = text.find('{')
    first_bracket = text.find('[')
    
    if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
        # 从第一个 { 开始提取
        brace_count = 0
        for i in range(first_brace, len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    try:
                        return json.loads(text[first_brace:i+1])
                    except json.JSONDecodeError:
                        break
    elif first_bracket != -1:
        # 从第一个 [ 开始提取
        bracket_count = 0
        for i in range(first_bracket, len(text)):
            if text[i] == '[':
                bracket_count += 1
            elif text[i] == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    try:
                        return json.loads(text[first_bracket:i+1])
                    except json.JSONDecodeError:
                        break

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
        # 使用统一的 _run_cli() 方法
        result = _run_cli(
            cli_path=claude_cli,
            args=["--version"],
            timeout=5,
            capture_output=True,
            text=True,
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
        self.model = "claude-code"
        # 添加 usage 属性以兼容 Anthropic API 响应格式
        self.usage = _MockUsage()


class _MockTextBlock:
    """模拟响应中的文本块"""

    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class _MockUsage:
    """模拟 Anthropic API 响应中的 usage 对象"""

    def __init__(self):
        # Claude Code CLI 不提供 token 使用信息，返回 0
        self.input_tokens = 0
        self.output_tokens = 0


# 导出
__all__ = [
    "call_claude_code",
    "check_claude_code_available",
    "ClaudeCodeClient",
    "CLAUDE_CODE_CONFIG",
    "_extract_json",  # Used by fe_dev_skill/be_dev_skill for fallback JSON parsing
]
