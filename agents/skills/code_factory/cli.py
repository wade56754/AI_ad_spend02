"""
CLI 命令行接口 v5.0

提供:
- 交互模式 (codefactory chat)
- 一次性生成 (codefactory gen)
- 项目配置 (codefactory init)
- 知识库管理 (codefactory kb)

基准文档: MASTER.md v4.6
版本: v5.0
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
import json


class CommandType(str, Enum):
    """命令类型"""
    CHAT = "chat"       # 交互模式
    GEN = "gen"         # 一次性生成
    INIT = "init"       # 初始化配置
    KB = "kb"           # 知识库管理
    CLARIFY = "clarify" # 需求澄清
    REVIEW = "review"   # 代码审查


@dataclass
class CLIContext:
    """CLI 上下文"""
    command: CommandType
    project_dir: Path
    verbose: bool = False
    args: dict = None
    
    def __post_init__(self):
        self.args = self.args or {}


class CodeFactoryCLI:
    """
    代码工厂 CLI
    
    使用方式:
    ```bash
    # 交互模式
    codefactory chat
    
    # 一次性生成
    codefactory gen "实现日报导出功能"
    
    # 初始化配置
    codefactory init
    
    # 知识库管理
    codefactory kb build
    codefactory kb search "日报状态机"
    
    # 需求澄清
    codefactory clarify "添加批量导出"
    
    # 代码审查
    codefactory review backend/services/report_service.py
    ```
    """
    
    VERSION = "5.0.0"
    BANNER = r"""
╔═══════════════════════════════════════════════════════════════╗
║     _    ___    ____          _        _____            _     ║
║    / \  |_ _|  / ___|___   __| | ___  |  ___|_ _   ___ | |_   ║
║   / _ \  | |  | |   / _ \ / _` |/ _ \ | |_ / _` | / __|| __|  ║
║  / ___ \ | |  | |__| (_) | (_| |  __/ |  _| (_| || (__ | |_   ║
║ /_/   \_|___|  \____\___/ \__,_|\___| |_|  \__,_| \___| \__|  ║
║                                                               ║
║                 AI Code Factory v5.0                          ║
║                 智能代码生成助手                               ║
╚═══════════════════════════════════════════════════════════════╝
    """
    
    def __init__(self, project_dir: Path = None):
        """初始化 CLI
        
        Args:
            project_dir: 项目目录
        """
        self.project_dir = project_dir or Path.cwd()
        self._setup_parser()
    
    def _setup_parser(self):
        """设置参数解析器"""
        self.parser = argparse.ArgumentParser(
            prog="codefactory",
            description="AI Code Factory - 智能代码生成助手",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例:
  codefactory chat                    # 进入交互模式
  codefactory gen "实现日报导出"       # 一次性生成
  codefactory init                    # 初始化配置
  codefactory kb build                # 构建知识库
  codefactory clarify "添加功能"       # 需求澄清
  codefactory review path/to/file.py  # 代码审查
            """
        )
        
        self.parser.add_argument(
            "-v", "--version",
            action="version",
            version=f"%(prog)s {self.VERSION}",
        )
        
        self.parser.add_argument(
            "--verbose",
            action="store_true",
            help="详细输出",
        )
        
        self.parser.add_argument(
            "--project-dir",
            type=Path,
            default=self.project_dir,
            help="项目目录",
        )
        
        # 子命令
        subparsers = self.parser.add_subparsers(dest="command", help="可用命令")
        
        # chat 命令
        chat_parser = subparsers.add_parser("chat", help="交互模式")
        chat_parser.add_argument(
            "--model",
            default="claude-3-opus",
            help="使用的模型",
        )
        
        # gen 命令
        gen_parser = subparsers.add_parser("gen", help="一次性生成")
        gen_parser.add_argument(
            "requirement",
            type=str,
            help="需求描述",
        )
        gen_parser.add_argument(
            "--output",
            type=Path,
            help="输出目录",
        )
        gen_parser.add_argument(
            "--template",
            choices=["fastapi", "nextjs", "fullstack"],
            help="项目模板",
        )
        
        # init 命令
        init_parser = subparsers.add_parser("init", help="初始化配置")
        init_parser.add_argument(
            "--force",
            action="store_true",
            help="强制覆盖",
        )
        
        # kb 命令
        kb_parser = subparsers.add_parser("kb", help="知识库管理")
        kb_subparsers = kb_parser.add_subparsers(dest="kb_action", help="知识库操作")
        
        kb_build = kb_subparsers.add_parser("build", help="构建索引")
        kb_build.add_argument("--force", action="store_true", help="强制重建")
        
        kb_search = kb_subparsers.add_parser("search", help="搜索")
        kb_search.add_argument("query", type=str, help="搜索查询")
        kb_search.add_argument("--top-k", type=int, default=5, help="结果数量")
        
        kb_stats = kb_subparsers.add_parser("stats", help="统计信息")
        
        # clarify 命令
        clarify_parser = subparsers.add_parser("clarify", help="需求澄清")
        clarify_parser.add_argument(
            "requirement",
            type=str,
            help="需求描述",
        )
        clarify_parser.add_argument(
            "--interactive",
            action="store_true",
            help="交互式澄清",
        )
        
        # review 命令
        review_parser = subparsers.add_parser("review", help="代码审查")
        review_parser.add_argument(
            "files",
            type=str,
            nargs="+",
            help="要审查的文件",
        )
        review_parser.add_argument(
            "--output",
            type=Path,
            help="输出报告路径",
        )
    
    def run(self, args: List[str] = None) -> int:
        """运行 CLI
        
        Args:
            args: 命令行参数
            
        Returns:
            退出码
        """
        parsed = self.parser.parse_args(args)
        
        if not parsed.command:
            self._print_banner()
            self.parser.print_help()
            return 0
        
        # 创建上下文
        ctx = CLIContext(
            command=CommandType(parsed.command),
            project_dir=parsed.project_dir,
            verbose=parsed.verbose,
            args=vars(parsed),
        )
        
        # 路由到对应命令
        handlers = {
            CommandType.CHAT: self._cmd_chat,
            CommandType.GEN: self._cmd_gen,
            CommandType.INIT: self._cmd_init,
            CommandType.KB: self._cmd_kb,
            CommandType.CLARIFY: self._cmd_clarify,
            CommandType.REVIEW: self._cmd_review,
        }
        
        handler = handlers.get(ctx.command)
        if handler:
            return handler(ctx)
        
        return 1
    
    def _print_banner(self):
        """打印 Banner"""
        print(self.BANNER)
    
    def _print(self, msg: str, style: str = None):
        """打印消息"""
        if style == "success":
            print(f"✅ {msg}")
        elif style == "error":
            print(f"❌ {msg}")
        elif style == "warning":
            print(f"⚠️  {msg}")
        elif style == "info":
            print(f"ℹ️  {msg}")
        else:
            print(msg)
    
    # =========================================================================
    # 命令处理器
    # =========================================================================
    
    def _cmd_chat(self, ctx: CLIContext) -> int:
        """交互模式"""
        self._print_banner()
        self._print("进入交互模式 (输入 /exit 退出, /help 查看帮助)", "info")
        print()
        
        # 加载组件
        from .prompts import Preprompts, PrepromptType
        from .phases import ClarifyPhase, clarify_requirement
        from .rag import create_knowledge_base
        
        preprompts = Preprompts(ctx.project_dir)
        kb = create_knowledge_base(ctx.project_dir)
        
        # 构建知识库索引
        self._print("正在构建知识库索引...", "info")
        kb.build_index()
        self._print("知识库索引已就绪", "success")
        print()
        
        # 交互循环
        history = []
        
        while True:
            try:
                user_input = input("🤖 > ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                self._print("再见!", "info")
                break
            
            if not user_input:
                continue
            
            # 特殊命令
            if user_input.startswith("/"):
                cmd = user_input[1:].lower()
                
                if cmd == "exit" or cmd == "quit":
                    self._print("再见!", "info")
                    break
                
                elif cmd == "help":
                    self._print_chat_help()
                    continue
                
                elif cmd == "clear":
                    history.clear()
                    self._print("历史已清空", "info")
                    continue
                
                elif cmd.startswith("search "):
                    query = cmd[7:]
                    results = kb.search(query, top_k=3)
                    print("\n搜索结果:")
                    for i, r in enumerate(results, 1):
                        print(f"  [{i}] {r.chunk.metadata.get('path', '未知')} (相关度: {r.score:.2f})")
                        print(f"      {r.chunk.content[:100]}...")
                    print()
                    continue
                
                elif cmd == "history":
                    if not history:
                        self._print("暂无历史", "info")
                    else:
                        print("\n对话历史:")
                        for i, (role, msg) in enumerate(history[-10:], 1):
                            prefix = "用户" if role == "user" else "助手"
                            print(f"  [{i}] {prefix}: {msg[:50]}...")
                    print()
                    continue
                
                else:
                    self._print(f"未知命令: {cmd}", "warning")
                    continue
            
            # 添加到历史
            history.append(("user", user_input))
            
            # 检索相关上下文
            context = kb.get_context(user_input, top_k=3)
            
            # 生成响应
            print("\n📝 正在处理...")
            
            # 需求澄清
            clarify_result = clarify_requirement(user_input)
            
            if clarify_result.needs_interaction:
                print("\n❓ 需要澄清的问题:")
                for q in clarify_result.required_unanswered[:3]:
                    print(f"  • {q.question}")
            
            if clarify_result.clarified_requirement:
                print("\n📋 理解的需求:")
                cr = clarify_result.clarified_requirement
                print(f"  摘要: {cr.summary}")
                if cr.scope_included:
                    print(f"  包含: {', '.join(cr.scope_included)}")
                if cr.tables:
                    print(f"  数据表: {', '.join(cr.tables)}")
            
            # 相关文档
            if context.results:
                print("\n📚 相关文档:")
                for r in context.results[:2]:
                    print(f"  • {r.chunk.metadata.get('path', '未知')}")
            
            print()
            
            # 模拟响应
            response = f"收到需求: {user_input}\n\n我将帮助你实现这个功能。首先，让我检查一下相关的代码和文档..."
            print(f"💬 {response}")
            print()
            
            # 添加响应到历史
            history.append(("assistant", response))
        
        return 0
    
    def _print_chat_help(self):
        """打印交互模式帮助"""
        print("""
可用命令:
  /help           - 显示此帮助
  /exit, /quit    - 退出交互模式
  /clear          - 清空对话历史
  /search <query> - 搜索知识库
  /history        - 显示对话历史

提示:
  - 直接输入需求描述即可开始生成代码
  - 系统会自动检索相关文档和代码
  - 可以追问和修改生成的代码
        """)
    
    def _cmd_gen(self, ctx: CLIContext) -> int:
        """一次性生成"""
        requirement = ctx.args.get("requirement", "")
        
        self._print(f"需求: {requirement}", "info")
        print()
        
        # 需求澄清
        from .phases import clarify_requirement, auto_clarify
        
        self._print("正在分析需求...", "info")
        clarified = auto_clarify(requirement)
        
        print("\n📋 澄清后的需求:")
        print(clarified.to_prompt_context())
        
        # TODO: 实际的代码生成逻辑
        self._print("\n代码生成功能正在开发中...", "warning")
        
        return 0
    
    def _cmd_init(self, ctx: CLIContext) -> int:
        """初始化配置"""
        from .config import ProjectConfigLoader, EXAMPLE_CONFIG
        
        config_path = ctx.project_dir / ".codefactory.yaml"
        
        if config_path.exists() and not ctx.args.get("force"):
            self._print(f"配置文件已存在: {config_path}", "warning")
            self._print("使用 --force 覆盖", "info")
            return 1
        
        # 写入配置
        config_path.write_text(EXAMPLE_CONFIG, encoding="utf-8")
        
        self._print(f"已创建配置文件: {config_path}", "success")
        return 0
    
    def _cmd_kb(self, ctx: CLIContext) -> int:
        """知识库管理"""
        action = ctx.args.get("kb_action")
        
        if not action:
            self._print("请指定操作: build, search, stats", "error")
            return 1
        
        from .rag import create_knowledge_base
        
        kb = create_knowledge_base(ctx.project_dir)
        
        if action == "build":
            self._print("正在构建知识库索引...", "info")
            force = ctx.args.get("force", False)
            stats = kb.build_index(force_rebuild=force)
            
            print("\n索引统计:")
            for source, stat in stats.items():
                print(f"  {source}:")
                print(f"    文档数: {stat['total_documents']}")
                print(f"    块数: {stat['total_chunks']}")
            
            self._print("\n索引构建完成", "success")
        
        elif action == "search":
            query = ctx.args.get("query", "")
            top_k = ctx.args.get("top_k", 5)
            
            if not query:
                self._print("请提供搜索查询", "error")
                return 1
            
            # 先构建索引
            kb.build_index()
            
            results = kb.search(query, top_k=top_k)
            
            print(f"\n搜索: '{query}'")
            print(f"找到 {len(results)} 个结果:")
            
            for i, r in enumerate(results, 1):
                print(f"\n[{i}] 相关度: {r.score:.2f}")
                print(f"    来源: {r.chunk.metadata.get('path', '未知')}")
                print(f"    内容: {r.chunk.content[:150]}...")
        
        elif action == "stats":
            stats = kb.get_stats()
            print("\n知识库统计:")
            print(f"  版本: {stats['version']}")
            print(f"  已构建: {stats['is_built']}")
            
            for source, stat in stats['sources'].items():
                print(f"\n  {source}:")
                print(f"    文档数: {stat['total_documents']}")
                print(f"    块数: {stat['total_chunks']}")
        
        return 0
    
    def _cmd_clarify(self, ctx: CLIContext) -> int:
        """需求澄清"""
        requirement = ctx.args.get("requirement", "")
        interactive = ctx.args.get("interactive", False)
        
        from .phases import clarify_requirement, ClarifyPhase
        
        if interactive:
            # 交互式澄清
            def interaction_callback(questions):
                print("\n❓ 请回答以下问题:")
                for q in questions:
                    if q.importance == "required" and q.answer is None:
                        if q.options:
                            print(f"\n{q.question}")
                            for i, opt in enumerate(q.options, 1):
                                print(f"  {i}. {opt}")
                            answer = input("请选择 (输入数字): ").strip()
                            try:
                                idx = int(answer) - 1
                                if 0 <= idx < len(q.options):
                                    q.answer = q.options[idx]
                            except ValueError:
                                q.answer = answer
                        else:
                            q.answer = input(f"{q.question} ").strip()
                return questions
            
            phase = ClarifyPhase(interaction_callback=interaction_callback)
            result = phase.analyze(requirement)
            
            if result.needs_interaction:
                result.questions = interaction_callback(result.questions)
                result = phase.finalize(result)
        else:
            result = clarify_requirement(requirement)
        
        # 输出结果
        print("\n📋 澄清结果:")
        print(f"  清晰度: {result.clarity_level.value}")
        
        if result.clarified_requirement:
            print(result.clarified_requirement.to_prompt_context())
        
        if result.unanswered_questions:
            print("\n❓ 未回答的问题:")
            for q in result.unanswered_questions[:5]:
                importance = "必需" if q.importance == "required" else "可选"
                print(f"  • [{importance}] {q.question}")
        
        return 0
    
    def _cmd_review(self, ctx: CLIContext) -> int:
        """代码审查"""
        files = ctx.args.get("files", [])
        
        if not files:
            self._print("请指定要审查的文件", "error")
            return 1
        
        print(f"\n📝 审查文件: {', '.join(files)}")
        
        # TODO: 实际的代码审查逻辑
        for file_path in files:
            path = ctx.project_dir / file_path
            if not path.exists():
                self._print(f"文件不存在: {file_path}", "warning")
                continue
            
            content = path.read_text(encoding="utf-8")
            
            print(f"\n## {file_path}")
            print(f"  行数: {len(content.split(chr(10)))}")
            
            # 简单检查
            issues = []
            
            if "class Config:" in content:
                issues.append("使用了旧的 Pydantic v1 语法 (class Config)")
            
            if ".dict()" in content:
                issues.append("使用了旧的 .dict() 方法，应使用 .model_dump()")
            
            if "os.system" in content:
                issues.append("使用了 os.system，应使用 subprocess")
            
            if issues:
                print("  发现问题:")
                for issue in issues:
                    print(f"    ❌ {issue}")
            else:
                print("  ✅ 未发现明显问题")
        
        return 0


# ============================================================
# 入口
# ============================================================

def main(args: List[str] = None) -> int:
    """CLI 入口
    
    Args:
        args: 命令行参数
        
    Returns:
        退出码
    """
    cli = CodeFactoryCLI()
    return cli.run(args)


if __name__ == "__main__":
    sys.exit(main())


