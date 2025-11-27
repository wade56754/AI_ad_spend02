# cli.py 示例片段

import argparse
from pathlib import Path

from .agents_config import create_agent, list_agents


def main() -> None:
    parser = argparse.ArgumentParser(description="AI_ad_spend02 Agents CLI")
    parser.add_argument("agent", choices=list_agents().keys(), help="Agent 名称: fe / be / test")
    parser.add_argument("--base-path", type=str, default=None, help="项目根路径（可选）")
    parser.add_argument("--supabase-project-id", type=str, default=None, help="Supabase 项目 ID（仅 test 用）")
    parser.add_argument("--action", type=str, default=None, help="具体动作，由对应 Agent 自行解析")
    # 这里可以继续加其他参数……

    args = parser.parse_args()

    base_path = Path(args.base_path).resolve() if args.base_path else None

    agent = create_agent(
        args.agent,
        base_path=base_path,
        supabase_project_id=args.supabase_project_id,
    )

    request = {
        "action": args.action,
        # 其他参数也可以放在这里传给 agent.handle_request
    }

    result = agent.handle_request(request)
    print(result)


if __name__ == "__main__":
    main()

