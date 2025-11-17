import re
import os
from pathlib import Path
from typing import List, Dict


# 你项目的根路径（可以改成命令行参数，这里先写死）
PROJECT_ROOT = Path(r"D:\git\1108\AI_ad_spend02")
DOCS_ROOT = PROJECT_ROOT / "docs"
REPORT_PATH = DOCS_ROOT / "DOCS_AUDIT_REPORT.md"

# 允许的一级目录
ALLOWED_TOP_DIRS = {
    "core", "api", "modules", "dev", "deploy", "design", "scripts", "archive"
}

# 需要特别关注的关键词 / 模式
PATTERNS = {
    "old_roles": [
        r"\bmanager\b",          # 旧角色名
        r"\bdata_clerk\b",       # 旧角色名
    ],
    "old_nextjs": [
        r"Next\.js\s*13",
        r"Next\.js\s*15",
        r"Next\s*13",
        r"Next\s*15",
    ],
    "rls_enabled": [
        r"RLS\s*已启用",
        r"ENABLE\s+ROW\s+LEVEL\s+SECURITY",
        r"ALTER\s+TABLE.+ENABLE\s+ROW\s+LEVEL\s+SECURITY",
    ],
    "direct_fetch": [
        r"fetch\(\"http", r"fetch\('http",
        r"fetch\(\"/api", r"fetch\('/api",
    ],
    "wrong_data_schema_path": [
        r"docs/core/DATA_SCHEMA\.md"
    ],
    "supabase_direct": [
        r"supabase\.from\(",
        r"createClient\(",
    ],
}


def read_text(path: Path) -> str:
    try:
        with path.open("r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with path.open("r", encoding="gbk") as f:
                return f.read()
        except Exception:
            return ""


def find_pattern_hits(text: str, patterns: List[str]) -> List[str]:
    hits = []
    for p in patterns:
        for m in re.finditer(p, text, flags=re.IGNORECASE | re.MULTILINE):
            snippet = text[max(0, m.start() - 40): m.end() + 40]
            hits.append(snippet.replace("\n", " "))
            if len(hits) >= 5:
                # 每种模式最多展示 5 条示例，避免报告太长
                return hits
    return hits


def audit_docs() -> Dict:
    result = {
        "unclassified_files": [],
        "by_pattern": {k: [] for k in PATTERNS.keys()},
        "all_files": [],
    }

    if not DOCS_ROOT.exists():
        raise RuntimeError(f"docs 目录不存在：{DOCS_ROOT}")

    for path in DOCS_ROOT.rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(DOCS_ROOT)
        result["all_files"].append(str(rel))

        # 1）目录结构检查
        parts = rel.parts
        if len(parts) == 1:
            # docs 根目录下的散文件，除了 DOCUMENTATION_INDEX / README 之外都标记一下
            if parts[0] not in ("DOCUMENTATION_INDEX.md", "README.md"):
                result["unclassified_files"].append(str(rel))
        else:
            top = parts[0]
            if top not in ALLOWED_TOP_DIRS:
                result["unclassified_files"].append(str(rel))

        # 2）内容关键词扫描（只扫 Markdown / SQL / 文本）
        if path.suffix.lower() not in {".md", ".sql", ".txt"}:
            continue

        text = read_text(path)
        if not text:
            continue

        for key, pattern_list in PATTERNS.items():
            hits = find_pattern_hits(text, pattern_list)
            if hits:
                result["by_pattern"][key].append(
                    {
                        "file": str(rel),
                        "examples": hits,
                    }
                )

    return result


def generate_report(data: Dict):
    lines = []
    lines.append("# 文档审计报告 (docs 自动体检)")
    lines.append("")
    lines.append(f"- 项目根目录：`{PROJECT_ROOT}`")
    lines.append(f"- 扫描目录：`{DOCS_ROOT}`")
    lines.append(f"- 文档总数：{len(data['all_files'])}")
    lines.append("")

    # 一、未归类 / 可疑目录结构
    lines.append("## 一、未归类或可疑位置的文档")
    if not data["unclassified_files"]:
        lines.append("- ✅ 未发现可疑位置文档，目录结构基本符合预期。")
    else:
        lines.append("- ⚠️ 以下文件不在预期的 docs 子目录结构中（core/api/modules/dev/deploy/design/scripts/archive），需要人工决定：")
        lines.append("")
        for f in sorted(data["unclassified_files"]):
            lines.append(f"  - `{f}`")
    lines.append("")

    # 二、按关键词分类的风险点
    lines.append("## 二、关键风险关键词扫描结果")
    lines.append("")

    mapping_label = {
        "old_roles": "旧角色命名（manager / data_clerk 等）",
        "old_nextjs": "旧 Next.js 版本描述（13/15 等）",
        "rls_enabled": "RLS 已启用 / 强依赖 RLS 的描述",
        "direct_fetch": "前端直接 fetch() 调用示例（可能绕过 apiFetch）",
        "wrong_data_schema_path": "DATA_SCHEMA 路径错误引用（应为 docs/core/DATA_SCHEMA.md）",
        "supabase_direct": "前端/文档中直接操作 Supabase 客户端的示例",
    }

    for key, items in data["by_pattern"].items():
        label = mapping_label.get(key, key)
        lines.append(f"### {label}")
        if not items:
            lines.append(f"- ✅ 未发现可疑内容。")
            lines.append("")
            continue

        for item in items:
            lines.append(f"- 文件：`{item['file']}`")
            for ex in item["examples"]:
                lines.append(f"  - 示例：`{ex.strip()}`")
        lines.append("")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✅ 文档审计报告已生成：{REPORT_PATH}")


if __name__ == "__main__":
    data = audit_docs()
    generate_report(data)
