from pathlib import Path
from typing import Dict, Iterable, List, TypedDict
import logging

logger = logging.getLogger(__name__)


class WritePreview(TypedDict):
    """
    write_files dry-run 模式返回的预览结构。

    Fix: P0-03 降级 P1 - 添加 dry-run 能力
    """
    files_to_write: int
    files_to_create: int
    files_to_update: int
    total_bytes: int
    paths: List[str]


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


def write_files(
    base_dir: Path,
    changes: Dict[str, str],
    dry_run: bool = False,
) -> WritePreview:
    """
    写入多个文件，带路径安全检查和可选 dry-run 模式。

    Fix: P0-03 降级 P1 - 添加 dry_run 参数支持预览模式

    Args:
        base_dir: 基础目录
        changes: 文件路径 -> 文件内容的字典
        dry_run: 预览模式（默认 False）
            - True: 仅返回预览结果，不写入磁盘
            - False: 执行实际写入操作

    Returns:
        WritePreview 结构，包含：
            - files_to_write: 总文件数
            - files_to_create: 新建文件数
            - files_to_update: 更新文件数
            - total_bytes: 总字节数
            - paths: 受影响的路径列表

    Raises:
        OSError: 写入失败时抛出异常（仅 dry_run=False）
        ValueError: 路径穿越检测失败时抛出异常

    Security:
        使用 Path.relative_to() 检测路径穿越攻击，阻止 "../../../" 等模式
        dry_run 模式下仍会执行安全检查，确保预览结果反映实际行为
    """
    base_resolved = base_dir.resolve()
    preview: WritePreview = {
        "files_to_write": 0,
        "files_to_create": 0,
        "files_to_update": 0,
        "total_bytes": 0,
        "paths": [],
    }

    for rel, content in changes.items():
        p = (base_dir / rel).resolve()

        # Security check: ensure resolved path is within base_dir
        try:
            p.relative_to(base_resolved)
        except ValueError as e:
            logger.error(f"Path traversal blocked in write: '{rel}'")
            raise ValueError(f"Path '{rel}' escapes base directory") from e

        # 统计预览信息
        preview["files_to_write"] += 1
        preview["total_bytes"] += len(content.encode("utf-8"))
        preview["paths"].append(rel)

        if p.exists():
            preview["files_to_update"] += 1
        else:
            preview["files_to_create"] += 1

        # dry_run 模式下不执行写入
        if dry_run:
            logger.debug(f"[DRY-RUN] Would write: {rel} ({len(content)} chars)")
            continue

        # 实际写入
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        logger.debug(f"File written: {rel} ({len(content)} chars)")

    if dry_run:
        logger.info(
            f"[DRY-RUN] Preview: {preview['files_to_write']} files "
            f"({preview['files_to_create']} create, {preview['files_to_update']} update), "
            f"{preview['total_bytes']} bytes total"
        )
    else:
        logger.info(f"Wrote {preview['files_to_write']} files ({preview['total_bytes']} bytes)")

    return preview
