"""
File System Tools - 文件系统工具

提供带安全检查的文件读写功能。
This is a copy from agents/tools/fs_tool.py for agent_platform independence.
"""

from pathlib import Path
from typing import Dict, Iterable, List, TypedDict
import logging

logger = logging.getLogger(__name__)


class WritePreview(TypedDict):
    """
    write_files dry-run mode preview structure.
    """
    files_to_write: int
    files_to_create: int
    files_to_update: int
    total_bytes: int
    paths: List[str]


def read_files(base_dir: Path, relative_paths: Iterable[str]) -> Dict[str, str]:
    """
    Read multiple files with path security checks.

    Args:
        base_dir: Base directory
        relative_paths: List of relative paths

    Returns:
        Dict mapping file path to file content.
        - Returns empty string if file doesn't exist
        - Returns error comment (starting with # ERROR) if read fails or path traversal detected

    Security:
        Uses Path.relative_to() to detect path traversal attacks
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
            logger.error(f"Failed to read '{rel}': {type(e).__name__}: {e}")
            result[rel] = f"# ERROR reading {rel}: {type(e).__name__}: {e}"
    return result


def write_files(
    base_dir: Path,
    changes: Dict[str, str],
    dry_run: bool = False,
) -> WritePreview:
    """
    Write multiple files with path security checks and optional dry-run mode.

    Args:
        base_dir: Base directory
        changes: Dict mapping file path to file content
        dry_run: Preview mode (default False)
            - True: Only return preview, don't write to disk
            - False: Execute actual write operations

    Returns:
        WritePreview structure containing:
            - files_to_write: Total number of files
            - files_to_create: Number of new files
            - files_to_update: Number of updated files
            - total_bytes: Total bytes
            - paths: List of affected paths

    Raises:
        OSError: Write failure (only when dry_run=False)
        ValueError: Path traversal detected

    Security:
        Uses Path.relative_to() to detect path traversal attacks
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

        # Calculate preview info
        preview["files_to_write"] += 1
        preview["total_bytes"] += len(content.encode("utf-8"))
        preview["paths"].append(rel)

        if p.exists():
            preview["files_to_update"] += 1
        else:
            preview["files_to_create"] += 1

        # Skip actual write in dry_run mode
        if dry_run:
            logger.debug(f"[DRY-RUN] Would write: {rel} ({len(content)} chars)")
            continue

        # Actual write
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


__all__ = [
    "read_files",
    "write_files",
    "WritePreview",
]
