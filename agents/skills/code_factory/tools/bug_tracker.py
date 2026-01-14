"""
Bug Tracker - Bug 记录和追踪工具

提供结构化的 Bug 记录、查询和统计功能。

版本: v1.0
"""

import re
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class BugSeverity(str, Enum):
    """Bug 严重级别"""
    P0 = "P0"  # 阻塞性 - 系统不可用/数据丢失/安全漏洞
    P1 = "P1"  # 严重 - 核心功能异常/性能严重下降
    P2 = "P2"  # 一般 - 功能缺陷/非核心路径问题
    P3 = "P3"  # 轻微 - UI优化/文档错误


class BugStatus(str, Enum):
    """Bug 状态"""
    OPEN = "待修复"
    IN_PROGRESS = "修复中"
    FIXED = "已修复"
    VERIFIED = "已验证"
    CLOSED = "已关闭"


class BugModule(str, Enum):
    """Bug 所属模块"""
    BACKEND = "后端"
    FRONTEND = "前端"
    CODE_FACTORY = "代码工厂"
    INFRASTRUCTURE = "基础设施"
    FULL_STACK = "全栈"


@dataclass
class BugRecord:
    """Bug 记录"""
    id: str
    title: str
    severity: BugSeverity
    status: BugStatus
    module: BugModule
    description: str
    root_cause: str = ""
    fix_description: str = ""
    files_changed: List[str] = field(default_factory=list)
    reporter: str = "AI"
    fixer: str = "AI"
    created_at: str = ""
    fixed_at: str = ""
    verified_at: str = ""
    lessons_learned: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    def to_markdown(self) -> str:
        """生成 Markdown 格式的 Bug 记录"""
        files_list = "\n".join(f"| `{f}` | 修改 | - |" for f in self.files_changed) if self.files_changed else "| - | - | - |"
        
        return f"""# Bug: {self.title}

## 元数据

| 字段 | 值 |
|------|-----|
| **ID** | {self.id} |
| **日期** | {self.created_at.split()[0] if self.created_at else '-'} |
| **报告人** | {self.reporter} |
| **修复人** | {self.fixer} |
| **严重级别** | {self.severity.value} |
| **状态** | {self.status.value} |
| **影响范围** | {self.module.value} |

---

## 问题描述

### 现象
{self.description}

---

## 根因分析

### 根本原因
{self.root_cause if self.root_cause else '待分析'}

---

## 修复方案

### 方案描述
{self.fix_description if self.fix_description else '待修复'}

### 修改文件

| 文件 | 修改类型 | 说明 |
|------|---------|------|
{files_list}

---

## 经验教训

{self.lessons_learned if self.lessons_learned else '待总结'}

---

## 时间线

| 时间 | 事件 |
|------|------|
| {self.created_at} | 问题发现 |
| {self.fixed_at if self.fixed_at else '-'} | 修复完成 |
| {self.verified_at if self.verified_at else '-'} | 验证通过 |
"""


class BugTracker:
    """
    Bug 追踪器
    
    管理 Bug 记录的创建、更新、查询和统计
    """
    
    DEFAULT_BUG_DIR = Path("memory-bank/bug-fixes")
    
    def __init__(self, bug_dir: Optional[Path] = None):
        self.bug_dir = bug_dir or self.DEFAULT_BUG_DIR
        self.bug_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_bug_id(self) -> str:
        """生成 Bug ID"""
        today = datetime.now().strftime("%Y-%m%d")
        
        # 查找今天已有的 Bug 数量
        pattern = f"*{today.replace('-', '')}*.md"
        existing = list(self.bug_dir.glob(pattern))
        count = len(existing) + 1
        
        return f"BUG-{today}-{count:03d}"
    
    def record(
        self,
        title: str,
        description: str,
        severity: BugSeverity = BugSeverity.P2,
        module: BugModule = BugModule.BACKEND,
        reporter: str = "AI",
    ) -> BugRecord:
        """
        记录新 Bug
        
        Args:
            title: Bug 标题
            description: 问题描述
            severity: 严重级别
            module: 所属模块
            reporter: 报告人
            
        Returns:
            创建的 BugRecord
        """
        bug_id = self._generate_bug_id()
        
        bug = BugRecord(
            id=bug_id,
            title=title,
            description=description,
            severity=severity,
            status=BugStatus.OPEN,
            module=module,
            reporter=reporter,
        )
        
        # 保存到文件
        filename = f"{datetime.now().strftime('%Y-%m-%d')}-{self._slugify(title)}.md"
        filepath = self.bug_dir / filename
        filepath.write_text(bug.to_markdown(), encoding="utf-8")
        
        logger.info(f"Bug recorded: {bug_id} - {title}")
        self._update_index()
        
        return bug
    
    def update(
        self,
        bug_id: str,
        status: Optional[BugStatus] = None,
        root_cause: Optional[str] = None,
        fix_description: Optional[str] = None,
        files_changed: Optional[List[str]] = None,
        lessons_learned: Optional[str] = None,
        fixer: Optional[str] = None,
    ) -> bool:
        """
        更新 Bug 记录
        
        Args:
            bug_id: Bug ID
            status: 新状态
            root_cause: 根因分析
            fix_description: 修复描述
            files_changed: 修改的文件
            lessons_learned: 经验教训
            fixer: 修复人
            
        Returns:
            是否更新成功
        """
        bug_file = self._find_bug_file(bug_id)
        if not bug_file:
            logger.error(f"Bug not found: {bug_id}")
            return False
        
        bug = self._parse_bug_file(bug_file)
        if not bug:
            return False
        
        # 更新字段
        if status:
            bug.status = status
            if status == BugStatus.FIXED:
                bug.fixed_at = datetime.now().strftime("%Y-%m-%d %H:%M")
            elif status == BugStatus.VERIFIED:
                bug.verified_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if root_cause:
            bug.root_cause = root_cause
        if fix_description:
            bug.fix_description = fix_description
        if files_changed:
            bug.files_changed = files_changed
        if lessons_learned:
            bug.lessons_learned = lessons_learned
        if fixer:
            bug.fixer = fixer
        
        # 保存更新
        bug_file.write_text(bug.to_markdown(), encoding="utf-8")
        logger.info(f"Bug updated: {bug_id}")
        self._update_index()
        
        return True
    
    def list_bugs(
        self,
        status: Optional[BugStatus] = None,
        severity: Optional[BugSeverity] = None,
        module: Optional[BugModule] = None,
    ) -> List[Dict[str, Any]]:
        """
        列出 Bug
        
        Args:
            status: 按状态过滤
            severity: 按严重级别过滤
            module: 按模块过滤
            
        Returns:
            Bug 列表
        """
        bugs = []
        
        for bug_file in self.bug_dir.glob("*.md"):
            if bug_file.name in ("template.md", "index.md"):
                continue
            
            bug = self._parse_bug_file(bug_file)
            if not bug:
                continue
            
            # 应用过滤
            if status and bug.status != status:
                continue
            if severity and bug.severity != severity:
                continue
            if module and bug.module != module:
                continue
            
            bugs.append({
                "id": bug.id,
                "title": bug.title,
                "severity": bug.severity.value,
                "status": bug.status.value,
                "module": bug.module.value,
                "created_at": bug.created_at,
                "file": str(bug_file.name),
            })
        
        # 按严重级别和日期排序
        bugs.sort(key=lambda x: (x["severity"], x["created_at"]), reverse=True)
        
        return bugs
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计数据
        """
        bugs = self.list_bugs()
        
        stats = {
            "total": len(bugs),
            "by_severity": {s.value: 0 for s in BugSeverity},
            "by_status": {s.value: 0 for s in BugStatus},
            "by_module": {m.value: 0 for m in BugModule},
        }
        
        for bug in bugs:
            stats["by_severity"][bug["severity"]] += 1
            stats["by_status"][bug["status"]] += 1
            stats["by_module"][bug["module"]] += 1
        
        return stats
    
    def _find_bug_file(self, bug_id: str) -> Optional[Path]:
        """查找 Bug 文件"""
        for bug_file in self.bug_dir.glob("*.md"):
            if bug_file.name in ("template.md", "index.md"):
                continue
            content = bug_file.read_text(encoding="utf-8")
            if bug_id in content:
                return bug_file
        return None
    
    def _parse_bug_file(self, filepath: Path) -> Optional[BugRecord]:
        """解析 Bug 文件"""
        try:
            content = filepath.read_text(encoding="utf-8")
            
            # 提取基本信息
            id_match = re.search(r'\*\*ID\*\*\s*\|\s*(\S+)', content)
            title_match = re.search(r'^# Bug: (.+)$', content, re.MULTILINE)
            severity_match = re.search(r'\*\*严重级别\*\*\s*\|\s*(\S+)', content)
            status_match = re.search(r'\*\*状态\*\*\s*\|\s*(.+?)\s*\|', content)
            module_match = re.search(r'\*\*影响范围\*\*\s*\|\s*(.+?)\s*\|', content)
            date_match = re.search(r'\*\*日期\*\*\s*\|\s*(\S+)', content)
            
            if not all([id_match, title_match]):
                return None
            
            # 解析严重级别
            severity_str = severity_match.group(1) if severity_match else "P2"
            severity = BugSeverity(severity_str) if severity_str in [s.value for s in BugSeverity] else BugSeverity.P2
            
            # 解析状态
            status_str = status_match.group(1).strip() if status_match else "待修复"
            status = next((s for s in BugStatus if s.value == status_str), BugStatus.OPEN)
            
            # 解析模块
            module_str = module_match.group(1).strip() if module_match else "后端"
            module = next((m for m in BugModule if m.value == module_str), BugModule.BACKEND)
            
            return BugRecord(
                id=id_match.group(1),
                title=title_match.group(1),
                severity=severity,
                status=status,
                module=module,
                description="",  # 简化，不解析完整描述
                created_at=date_match.group(1) if date_match else "",
            )
        except Exception as e:
            logger.error(f"Failed to parse bug file {filepath}: {e}")
            return None
    
    def _update_index(self) -> None:
        """更新索引文件"""
        stats = self.get_statistics()
        bugs = self.list_bugs()
        
        # 按月分组
        bugs_by_month: Dict[str, List] = {}
        for bug in bugs:
            month = bug["created_at"][:7] if bug["created_at"] else "未知"
            if month not in bugs_by_month:
                bugs_by_month[month] = []
            bugs_by_month[month].append(bug)
        
        # 生成索引内容
        index_content = f"""# Bug 修复索引

> 记录所有 Bug 修复，便于追踪和学习
> 自动生成于 {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

## 统计概览

| 指标 | 数量 |
|------|------|
| **总计** | {stats['total']} |
| **P0 (阻塞)** | {stats['by_severity']['P0']} |
| **P1 (严重)** | {stats['by_severity']['P1']} |
| **P2 (一般)** | {stats['by_severity']['P2']} |
| **P3 (轻微)** | {stats['by_severity']['P3']} |

---

## 按状态统计

| 状态 | 数量 |
|------|------|
| **待修复** | {stats['by_status']['待修复']} |
| **修复中** | {stats['by_status']['修复中']} |
| **已修复** | {stats['by_status']['已修复']} |
| **已验证** | {stats['by_status']['已验证']} |
| **已关闭** | {stats['by_status']['已关闭']} |

---

## Bug 列表

"""
        
        for month, month_bugs in sorted(bugs_by_month.items(), reverse=True):
            index_content += f"### {month}\n\n"
            index_content += "| ID | 日期 | 标题 | 级别 | 状态 | 模块 |\n"
            index_content += "|----|------|------|------|------|------|\n"
            
            for bug in month_bugs:
                index_content += f"| {bug['id']} | {bug['created_at'][:10]} | [{bug['title']}](./{bug['file']}) | {bug['severity']} | {bug['status']} | {bug['module']} |\n"
            
            index_content += "\n"
        
        if not bugs:
            index_content += "暂无 Bug 记录。\n\n"
        
        index_content += """---

## 快捷操作

```bash
# 记录新 Bug
python -m agents.skills.code_factory.tools.bug_tracker record

# 列出所有 Bug
python -m agents.skills.code_factory.tools.bug_tracker list

# 更新 Bug 状态
python -m agents.skills.code_factory.tools.bug_tracker update BUG-ID --status 已验证
```

---

## 相关文档

- [Bug 修复模板](./template.md)
- [历史修复汇总](../../docs/integration/BUG_FIXES_SUMMARY.md)

---

**最后更新**: """ + datetime.now().strftime("%Y-%m-%d %H:%M")
        
        index_file = self.bug_dir / "index.md"
        index_file.write_text(index_content, encoding="utf-8")
    
    def _slugify(self, text: str) -> str:
        """生成 URL 友好的文件名"""
        # 移除特殊字符，保留中文和英文
        slug = re.sub(r'[^\w\u4e00-\u9fff-]', '-', text)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')[:50]
        return slug or "bug"


# =============================================================================
# 命令行入口
# =============================================================================

def main():
    """命令行入口"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Bug Tracker - Bug 记录和追踪工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # record 命令
    record_parser = subparsers.add_parser("record", help="记录新 Bug")
    record_parser.add_argument("--title", "-t", required=True, help="Bug 标题")
    record_parser.add_argument("--description", "-d", required=True, help="问题描述")
    record_parser.add_argument("--severity", "-s", choices=["P0", "P1", "P2", "P3"], default="P2", help="严重级别")
    record_parser.add_argument("--module", "-m", choices=["backend", "frontend", "code_factory", "infrastructure", "full_stack"], default="backend", help="所属模块")
    
    # list 命令
    list_parser = subparsers.add_parser("list", help="列出 Bug")
    list_parser.add_argument("--status", choices=["open", "in_progress", "fixed", "verified", "closed"], help="按状态过滤")
    list_parser.add_argument("--severity", choices=["P0", "P1", "P2", "P3"], help="按严重级别过滤")
    
    # update 命令
    update_parser = subparsers.add_parser("update", help="更新 Bug")
    update_parser.add_argument("bug_id", help="Bug ID")
    update_parser.add_argument("--status", choices=["open", "in_progress", "fixed", "verified", "closed"], help="新状态")
    update_parser.add_argument("--root-cause", help="根因分析")
    update_parser.add_argument("--fix", help="修复描述")
    update_parser.add_argument("--lessons", help="经验教训")
    
    # stats 命令
    subparsers.add_parser("stats", help="显示统计信息")
    
    args = parser.parse_args()
    
    tracker = BugTracker()
    
    if args.command == "record":
        module_map = {
            "backend": BugModule.BACKEND,
            "frontend": BugModule.FRONTEND,
            "code_factory": BugModule.CODE_FACTORY,
            "infrastructure": BugModule.INFRASTRUCTURE,
            "full_stack": BugModule.FULL_STACK,
        }
        bug = tracker.record(
            title=args.title,
            description=args.description,
            severity=BugSeverity(args.severity),
            module=module_map[args.module],
        )
        print(f"[OK] Bug recorded: {bug.id}")
        
    elif args.command == "list":
        status_map = {
            "open": BugStatus.OPEN,
            "in_progress": BugStatus.IN_PROGRESS,
            "fixed": BugStatus.FIXED,
            "verified": BugStatus.VERIFIED,
            "closed": BugStatus.CLOSED,
        }
        status = status_map.get(args.status) if args.status else None
        severity = BugSeverity(args.severity) if args.severity else None
        
        bugs = tracker.list_bugs(status=status, severity=severity)
        
        if not bugs:
            print("No bugs found.")
        else:
            print(f"{'ID':<20} {'Severity':<8} {'Status':<10} {'Title'}")
            print("-" * 70)
            for bug in bugs:
                print(f"{bug['id']:<20} {bug['severity']:<8} {bug['status']:<10} {bug['title'][:30]}")
        
    elif args.command == "update":
        status_map = {
            "open": BugStatus.OPEN,
            "in_progress": BugStatus.IN_PROGRESS,
            "fixed": BugStatus.FIXED,
            "verified": BugStatus.VERIFIED,
            "closed": BugStatus.CLOSED,
        }
        status = status_map.get(args.status) if args.status else None
        
        success = tracker.update(
            bug_id=args.bug_id,
            status=status,
            root_cause=args.root_cause,
            fix_description=args.fix,
            lessons_learned=args.lessons,
        )
        
        if success:
            print(f"[OK] Bug updated: {args.bug_id}")
        else:
            print(f"[ERROR] Failed to update bug: {args.bug_id}")
            sys.exit(1)
        
    elif args.command == "stats":
        stats = tracker.get_statistics()
        print(f"\n=== Bug Statistics ===\n")
        print(f"Total: {stats['total']}")
        print(f"\nBy Severity:")
        for sev, count in stats['by_severity'].items():
            print(f"  {sev}: {count}")
        print(f"\nBy Status:")
        for status, count in stats['by_status'].items():
            print(f"  {status}: {count}")
        print()
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
