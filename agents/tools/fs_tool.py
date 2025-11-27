from pathlib import Path
from typing import Dict, Iterable
import logging

logger = logging.getLogger(__name__)


def read_files(base_dir: Path, relative_paths: Iterable[str]) -> Dict[str, str]:
    """
    读取多个文件的内容，带路径安全检查。

    Args:
        base_dir: 基础目录
        relative_paths: 相对路径列表

    Returns:
        文件路径 -> 文件内容的字典
        - 文件不存在时返回空字符串
        - 读取失败或路径穿越时返回包含错误信息的注释（以 # ERROR 开头）

    Security:
        使用 Path.relative_to() 检测路径穿越攻击，阻止 "../../../" 等模式
    """
    result: Dict[str, str] = {}
    base_resolved = base_dir.resolve()

    for rel in relative_paths:
        try:
            p = (base_dir / rel).resolve()

            # Security check: ensure resolved path is within base_dir
            try:
                p.relative_to(base_resolved)
            except ValueError:
                logger.warning(f"Path traversal blocked: '{rel}' escapes base_dir")
                result[rel] = f"# ERROR: Path '{rel}' escapes base directory"
                continue

            if p.exists():
                result[rel] = p.read_text(encoding="utf-8")
            else:
                result[rel] = ""
        except (UnicodeDecodeError, PermissionError, OSError, ValueError) as e:
            # 读取失败时返回错误信息（作为注释，不影响后续处理）
            logger.error(f"Failed to read '{rel}': {type(e).__name__}: {e}")
            result[rel] = f"# ERROR reading {rel}: {type(e).__name__}: {e}"
    return result


def write_files(base_dir: Path, changes: Dict[str, str]) -> None:
    """
    写入多个文件，带路径安全检查。

    Args:
        base_dir: 基础目录
        changes: 文件路径 -> 文件内容的字典

    Raises:
        OSError: 写入失败时抛出异常
        ValueError: 路径穿越检测失败时抛出异常

    Security:
        使用 Path.relative_to() 检测路径穿越攻击，阻止 "../../../" 等模式
    """
    base_resolved = base_dir.resolve()

    for rel, content in changes.items():
        p = (base_dir / rel).resolve()

        # Security check: ensure resolved path is within base_dir
        try:
            p.relative_to(base_resolved)
        except ValueError as e:
            logger.error(f"Path traversal blocked in write: '{rel}'")
            raise ValueError(f"Path '{rel}' escapes base directory") from e

        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        logger.debug(f"File written: {rel} ({len(content)} chars)")
