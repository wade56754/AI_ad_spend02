# cli.py - AI_ad_spend02 Agents CLI
#
# 支持两种 LLM 后端：
# 1. Anthropic API（需要 ANTHROPIC_API_KEY 环境变量）
# 2. Claude Code CLI（支持 Claude Max 订阅用户）

import argparse
import json
import sys
from pathlib import Path

from .agents_config import create_agent, list_agents, check_llm_available, get_llm_backend


def cmd_status() -> None:
    """检查 LLM 服务状态"""
    print("=" * 50)
    print("AI_ad_spend02 Agents - LLM 状态检测")
    print("=" * 50)

    result = check_llm_available()

    print(f"\n后端类型: {result['backend']}")
    print(f"状态: {'✅ 可用' if result['available'] else '❌ 不可用'}")
    print(f"信息: {result['message']}")

    if result['details']:
        print(f"详情: {json.dumps(result['details'], indent=2, ensure_ascii=False)}")

    print("\n可用 Agents:")
    for key, info in list_agents().items():
        print(f"  - {key}: {info['description']}")

    if not result['available']:
        print("\n" + "=" * 50)
        print("解决方案:")
        if result['backend'] == 'anthropic_api':
            print("  设置环境变量: set ANTHROPIC_API_KEY=sk-ant-xxx")
        else:
            print("  1. 确保已安装 Claude Code CLI")
            print("  2. 运行 'claude --version' 确认安装成功")
            print("  3. 将 claude 添加到系统 PATH")
        print("=" * 50)


def cmd_run(args: argparse.Namespace) -> None:
    """运行指定 Agent"""
    # 检查 LLM 可用性
    llm_status = check_llm_available()
    if not llm_status['available']:
        print(f"❌ LLM 服务不可用: {llm_status['message']}")
        print("运行 'python -m agents.cli status' 查看详情")
        sys.exit(1)

    print(f"使用 LLM 后端: {llm_status['backend']}")

    base_path = Path(args.base_path).resolve() if args.base_path else None

    agent = create_agent(
        args.agent,
        base_path=base_path,
        supabase_project_id=args.supabase_project_id,
    )

    # 构建请求：对于 orchestrator，action 就是 flow 名称
    if args.agent == "orch":
        request = {
            "flow": args.action,  # frontend_restructure, backend_only, etc.
            "task": args.task if hasattr(args, "task") and args.task else args.action,
            "auto_write": getattr(args, "auto_write", False),
        }
    else:
        request = {
            "action": args.action,
            "task": args.action,  # 兼容旧接口
            "target_files": args.files.split(",") if args.files else [],
        }

    print(f"\n启动 Agent: {args.agent}")
    print(f"任务: {args.action}")
    print("-" * 50)

    result = agent.handle_request(request)

    # 格式化输出
    if isinstance(result, dict):
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI_ad_spend02 Agents CLI - 支持 Anthropic API 和 Claude Code CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # status 命令
    status_parser = subparsers.add_parser("status", help="检查 LLM 服务状态")

    # run 命令（默认）
    run_parser = subparsers.add_parser("run", help="运行 Agent")
    run_parser.add_argument(
        "agent",
        choices=list(list_agents().keys()),
        help="Agent 名称: fe / be / test / orch"
    )
    run_parser.add_argument(
        "--action", "-a",
        type=str,
        required=True,
        help=(
            "任务描述或 flow 名称。\n"
            "  fe/be: 任务描述，如 '实现 projects CRUD API'\n"
            "  orch: flow 名称 (backend_only|frontend_only|full_pipeline|frontend_restructure)"
        )
    )
    run_parser.add_argument(
        "--task", "-t",
        type=str,
        default=None,
        help="任务描述（仅 orch Agent 用，可选）"
    )
    run_parser.add_argument(
        "--files", "-f",
        type=str,
        default="",
        help="目标文件列表，逗号分隔"
    )
    run_parser.add_argument(
        "--base-path",
        type=str,
        default=None,
        help="项目根路径（可选）"
    )
    run_parser.add_argument(
        "--supabase-project-id",
        type=str,
        default=None,
        help="Supabase 项目 ID（仅 test Agent 用）"
    )
    run_parser.add_argument(
        "--auto-write",
        action="store_true",
        default=False,
        help="（仅 orch Agent）自动将生成的文件写入磁盘。默认 False（dry-run 模式，只返回变更预览）"
    )

    # 示例用法
    # Fix: P2-08 - 添加 doc 和 review Agent 示例
    run_parser.epilog = """
示例用法:
  # 前端代码生成
  python -m agents.cli run fe --action "实现项目列表页面"

  # 后端代码生成
  python -m agents.cli run be --action "实现 projects CRUD API"

  # 文档生成 (doc Agent)
  python -m agents.cli run doc --action generate --files "docs/api/README.md"

  # 文档审核 (doc Agent)
  python -m agents.cli run doc --action review --files "docs/2.sot/API_SOT.md"

  # 代码审核 (review Agent)
  python -m agents.cli run review --action review --files "backend/routers/daily_reports.py"

  # SC-ORCH 前端重构流水线（dry-run 模式，默认）
  python -m agents.cli run orch --action frontend_restructure --task "重构前端结构"

  # SC-ORCH 前端重构流水线（auto-write 模式，写入文件）
  python -m agents.cli run orch --action frontend_restructure --task "重构前端结构" --auto-write

  # 完整流水线
  python -m agents.cli run orch --action full_pipeline
"""

    # 兼容旧命令格式：python -m agents.cli be --action "..."
    # 如果第一个参数是 agent 名称，则使用旧格式
    args = parser.parse_args()

    if args.command == "status":
        cmd_status()
    elif args.command == "run":
        cmd_run(args)
    elif args.command is None:
        # 尝试旧格式兼容
        old_parser = argparse.ArgumentParser(description="AI_ad_spend02 Agents CLI (legacy)")
        old_parser.add_argument("agent", choices=list(list_agents().keys()), nargs="?")
        old_parser.add_argument("--action", "-a", type=str, default=None)
        old_parser.add_argument("--files", "-f", type=str, default="")
        old_parser.add_argument("--base-path", type=str, default=None)
        old_parser.add_argument("--supabase-project-id", type=str, default=None)

        old_args = old_parser.parse_args()

        if old_args.agent and old_args.action:
            # 旧格式：python -m agents.cli be --action "..."
            old_args.command = "run"
            cmd_run(old_args)
        else:
            parser.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

