import argparse
import json

from agent_core.fe_agent import FEAgent
from agent_core.be_agent import BEAgent
from agent_core.test_agent import TestAgent


def main() -> None:
    parser = argparse.ArgumentParser(description="AI_ad_spend Agents CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    fe = sub.add_parser("fe", help="前端开发 Agent")
    fe.add_argument("--task", required=True, help="前端任务描述（中文）")
    fe.add_argument("--files", nargs="+", required=True, help="要修改的前端文件相对路径列表")

    be = sub.add_parser("be", help="后端开发 Agent")
    be.add_argument("--task", required=True, help="后端任务描述（中文）")
    be.add_argument("--files", nargs="+", required=True, help="要修改的后端文件相对路径列表")

    dbt = sub.add_parser("dbtest-prompt", help="生成数据库不变量测试的 Claude 提示词")

    args = parser.parse_args()

    if args.cmd == "fe":
        res = FEAgent().run(args.task, args.files)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.cmd == "be":
        res = BEAgent().run(args.task, args.files)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.cmd == "dbtest-prompt":
        res = TestAgent().build_prompt()
        if not res.get("ok"):
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            # 只打印 prompt，方便直接复制进 Claude
            print(res["prompt"])


if __name__ == "__main__":
    main()

