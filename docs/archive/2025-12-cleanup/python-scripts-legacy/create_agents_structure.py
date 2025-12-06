#!/usr/bin/env python
"""
自动创建 agents 子项目目录结构的脚本

使用方法：
    在项目根目录（包含 backend/ frontend/ docs/ 的目录）运行：
        python create_agents_structure.py
"""

from pathlib import Path
import textwrap

PROJECT_ROOT = Path(__file__).resolve().parent
AGENTS_ROOT = PROJECT_ROOT / "agents"


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    print(f"[DIR]  {path.relative_to(PROJECT_ROOT)}")


def ensure_file(path: Path, content: str = ""):
    if path.exists():
        print(f"[SKIP] {path.relative_to(PROJECT_ROOT)} 已存在，跳过")
        return
    path.write_text(content.lstrip("\n"), encoding="utf-8")
    print(f"[FILE] {path.relative_to(PROJECT_ROOT)} 创建完成")


def main():
    print(f"项目根目录: {PROJECT_ROOT}")
    print("开始创建 agents 子项目结构...\n")

    # 1. 顶层目录
    ensure_dir(AGENTS_ROOT)

    # 2. 子目录
    tools_dir = AGENTS_ROOT / "tools"
    skills_dir = AGENTS_ROOT / "skills"
    agent_core_dir = AGENTS_ROOT / "agent_core"
    logs_dir = AGENTS_ROOT / "logs"

    for d in [tools_dir, skills_dir, agent_core_dir, logs_dir]:
        ensure_dir(d)

    # 3. pyproject.toml（最小依赖，后面你可以自己补充）
    pyproject = AGENTS_ROOT / "pyproject.toml"
    pyproject_content = textwrap.dedent(
        """
        [project]
        name = "ai_ad_spend_agents"
        version = "0.1.0"
        description = "Agents (FE/BE/Test) for AI_ad_spend system"
        requires-python = ">=3.10"

        dependencies = [
            "anthropic>=0.40.0",   # Claude API / Agent SDK
            "fastapi>=0.115.0",    # 如果你不需要 HTTP 服务，可以删掉
            "uvicorn[standard]>=0.30.0",
            "python-dotenv>=1.0.1"
        ]

        [tool.setuptools.packages.find]
        where = ["."]
        """
    )
    ensure_file(pyproject, pyproject_content)

    # 4. agents_config.py
    agents_config = AGENTS_ROOT / "agents_config.py"
    agents_config_content = textwrap.dedent(
        """
        from pathlib import Path

        # 项目根目录（假设脚本位于 AI_ad_spend02/agents/ 下）
        PROJECT_ROOT = Path(__file__).resolve().parents[1]

        DOCS_DIR = PROJECT_ROOT / "docs"
        BACKEND_DIR = PROJECT_ROOT / "backend"
        FRONTEND_DIR = PROJECT_ROOT / "frontend"
        DB_DIR = BACKEND_DIR / "db"

        # 单一事实来源文档路径（根据你项目里实际文件名再调）
        SOT_FILES = {
            "MASTER": DOCS_DIR / "1.overview" / "MASTER.md",
            "DATA_SCHEMA": DOCS_DIR / "2.sot" / "DATA_SCHEMA.md",
            "API_SOT": DOCS_DIR / "2.sot" / "API_SOT.md",
            "STATE_MACHINE": DOCS_DIR / "2.sot" / "STATE_MACHINE.md",
            "BUSINESS_RULES": DOCS_DIR / "2.sot" / "BUSINESS_RULES.md",
            "ERROR_CODES": DOCS_DIR / "2.sot" / "ERROR_CODES_SOT.md",
            "FRONTEND_RULES": DOCS_DIR / "3.dev-guides" / "FRONTEND_DEVELOPMENT_RULES.md",
            "UI_DESIGN_SYSTEM": DOCS_DIR / "3.dev-guides" / "UI_DESIGN_SYSTEM.md",
            "DB_TEST_CASES": DB_DIR / "TEST_CASES_v2.0.md",
            "DB_INVARIANTS_SQL": DB_DIR / "db_invariants_test_v2.sql",
            "INIT_SCHEMA_SQL": DB_DIR / "init_schema.sql",
        }
        """
    )
    ensure_file(agents_config, agents_config_content)

    # 5. tools
    ensure_file(tools_dir / "__init__.py", "'''工具层：文件读写、Supabase MCP 等封装。'''\n")

    fs_tool_content = textwrap.dedent(
        """
        '''文件系统工具，用于读取/写入代码文件等。'''

        from pathlib import Path
        from typing import Dict

        def read_files(base_dir: Path, relative_paths) -> Dict[str, str]:
            contents: Dict[str, str] = {}
            for rel in relative_paths:
                p = base_dir / rel
                contents[rel] = p.read_text(encoding="utf-8") if p.exists() else ""
            return contents

        def write_files(base_dir: Path, changes: Dict[str, str]) -> None:
            for rel, content in changes.items():
                p = base_dir / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
        """
    )
    ensure_file(tools_dir / "fs_tool.py", fs_tool_content)

    supabase_tool_content = textwrap.dedent(
        """
        '''Supabase 相关操作工具（占位，后面你可以接 MCP 或 psycopg2）。'''

        from typing import Any, Dict

        def run_sql(sql: str) -> Dict[str, Any]:
            # 在这里接入 Supabase MCP 或直接用数据库连接执行 SQL
            # 先留空实现，防止误调用破坏数据。
            raise NotImplementedError("Supabase SQL 执行尚未实现")
        """
    )
    ensure_file(tools_dir / "supabase_tool.py", supabase_tool_content)

    # 6. skills
    ensure_file(skills_dir / "__init__.py", "'''Skill 层：前端、后端、数据库测试等原子能力。'''\n")

    fe_skill_content = textwrap.dedent(
        """
        '''前端开发 Skill：读取 SOT + 前端代码，调用 Claude 生成/重构 TSX。'''

        from typing import List, Dict, Any
        from anthropic import Anthropic
        from pathlib import Path
        from agents_config import SOT_FILES, FRONTEND_DIR
        from tools.fs_tool import read_files, write_files

        client = Anthropic()

        def fe_dev_skill(task_description: str, target_files: List[str]) -> Dict[str, Any]:
            \"\"\"最小占位实现：目前只回显输入，后面你再接 Claude。\"\"\"
            files = read_files(FRONTEND_DIR, target_files)
            return {
                "task": task_description,
                "target_files": target_files,
                "preview_files": list(files.keys()),
                "notes": ["TODO: 调用 Claude 生成/重构前端代码"]
            }
        """
    )
    ensure_file(skills_dir / "fe_dev_skill.py", fe_skill_content)

    be_skill_content = textwrap.dedent(
        """
        '''后端开发 Skill：根据 SOT 文档生成/重构 FastAPI + Service 代码。'''

        from typing import List, Dict, Any
        from anthropic import Anthropic
        from pathlib import Path
        from agents_config import SOT_FILES, BACKEND_DIR
        from tools.fs_tool import read_files, write_files

        client = Anthropic()

        def be_dev_skill(task_description: str, target_files: List[str]) -> Dict[str, Any]:
            \"\"\"最小占位实现：目前只回显输入，后面你再接 Claude。\"\"\"
            files = read_files(BACKEND_DIR, target_files)
            return {
                "task": task_description,
                "target_files": target_files,
                "preview_files": list(files.keys()),
                "notes": ["TODO: 调用 Claude 生成/重构后端代码"]
            }
        """
    )
    ensure_file(skills_dir / "be_dev_skill.py", be_skill_content)

    db_skill_content = textwrap.dedent(
        """
        '''数据库不变量测试 Skill：调用 db_invariants_test_v2.sql 执行测试。'''

        from typing import Dict, Any
        from agents_config import SOT_FILES
        from tools.supabase_tool import run_sql

        def db_test_skill() -> Dict[str, Any]:
            sql = SOT_FILES["DB_INVARIANTS_SQL"].read_text(encoding="utf-8")
            # 这里后面接 run_sql(sql) 或分段执行
            return {
                "status": "TODO",
                "notes": ["TODO: 接入 Supabase MCP 或数据库连接执行 SQL 测试脚本"],
            }
        """
    )
    ensure_file(skills_dir / "db_test_skill.py", db_skill_content)

    # 7. agent_core
    ensure_file(agent_core_dir / "__init__.py", "'''Agent 层：组合多个 Skill，形成 FE/BE/Test 智能体。'''\n")

    fe_agent_content = textwrap.dedent(
        """
        '''前端开发 Agent：包装 fe_dev_skill。'''

        from typing import List, Any, Dict
        from skills.fe_dev_skill import fe_dev_skill

        class FEAgent:
            def run(self, task_description: str, target_files: List[str]) -> Dict[str, Any]:
                return fe_dev_skill(task_description, target_files)
        """
    )
    ensure_file(agent_core_dir / "fe_agent.py", fe_agent_content)

    be_agent_content = textwrap.dedent(
        """
        '''后端开发 Agent：包装 be_dev_skill。'''

        from typing import List, Any, Dict
        from skills.be_dev_skill import be_dev_skill

        class BEAgent:
            def run(self, task_description: str, target_files: List[str]) -> Dict[str, Any]:
                return be_dev_skill(task_description, target_files)
        """
    )
    ensure_file(agent_core_dir / "be_agent.py", be_agent_content)

    test_agent_content = textwrap.dedent(
        """
        '''测试 Agent：包装 db_test_skill。'''

        from typing import Any, Dict
        from skills.db_test_skill import db_test_skill

        class TestAgent:
            def run(self) -> Dict[str, Any]:
                return db_test_skill()
        """
    )
    ensure_file(agent_core_dir / "test_agent.py", test_agent_content)

    # 8. logs/.gitignore
    ensure_file(logs_dir / ".gitignore", "*\n!.gitignore\n")

    # 9. cli.py
    cli_content = textwrap.dedent(
        """
        '''简单命令行入口：手工调用 FE/BE/Test 三个 Agent。'''

        import argparse
        from agent_core.fe_agent import FEAgent
        from agent_core.be_agent import BEAgent
        from agent_core.test_agent import TestAgent

        def main():
            parser = argparse.ArgumentParser(description="AI_ad_spend Agents CLI")
            sub = parser.add_subparsers(dest="cmd", required=True)

            fe = sub.add_parser("fe", help="前端开发代理")
            fe.add_argument("--task", required=True, help="前端任务描述（中文即可）")
            fe.add_argument("--files", nargs="+", required=True, help="要修改的 frontend 相对路径")

            be = sub.add_parser("be", help="后端开发代理")
            be.add_argument("--task", required=True, help="后端任务描述（中文即可）")
            be.add_argument("--files", nargs="+", required=True, help="要修改的 backend 相对路径")

            dbt = sub.add_parser("dbtest", help="运行数据库不变量测试")

            args = parser.parse_args()

            if args.cmd == "fe":
                agent = FEAgent()
                res = agent.run(args.task, args.files)
                print(res)
            elif args.cmd == "be":
                agent = BEAgent()
                res = agent.run(args.task, args.files)
                print(res)
            elif args.cmd == "dbtest":
                agent = TestAgent()
                res = agent.run()
                print(res)

        if __name__ == "__main__":
            main()
        """
    )
    ensure_file(AGENTS_ROOT / "cli.py", cli_content)

    # 10. server.py 占位（以后你要做 HTTP 服务再填）
    server_content = textwrap.dedent(
        """
        '''Agent HTTP 服务入口（FastAPI 占位）。'''

        from fastapi import FastAPI
        from agent_core.fe_agent import FEAgent
        from agent_core.be_agent import BEAgent
        from agent_core.test_agent import TestAgent

        app = FastAPI(title="AI_ad_spend Agents Service")

        @app.post("/fe-agent/run")
        async def run_fe_agent(task: str, files: list[str]):
            return FEAgent().run(task, files)

        @app.post("/be-agent/run")
        async def run_be_agent(task: str, files: list[str]):
            return BEAgent().run(task, files)

        @app.post("/test-agent/db-invariants")
        async def run_db_test():
            return TestAgent().run()
        """
    )
    ensure_file(AGENTS_ROOT / "server.py", server_content)

    print("\n目录结构创建完成。可以继续根据需要细化各个 Skill 和 Agent 的逻辑。")


if __name__ == "__main__":
    main()
