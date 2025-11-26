from pathlib import Path
from typing import Dict, Iterable


def read_files(base_dir: Path, relative_paths: Iterable[str]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for rel in relative_paths:
        p = (base_dir / rel).resolve()
        if p.exists():
            result[rel] = p.read_text(encoding="utf-8")
        else:
            result[rel] = ""
    return result


def write_files(base_dir: Path, changes: Dict[str, str]) -> None:
    for rel, content in changes.items():
        p = (base_dir / rel).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
