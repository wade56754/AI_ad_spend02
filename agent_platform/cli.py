"""
agent_platform CLI - Unified command-line interface for Agent Platform.

Phase 3.0C: Provides CLI entry point for OrchestratorAgent and other agents.

Usage:
    # Run orchestrator with be_then_test flow
    python -m agent_platform.cli orch --flow be_then_test --task "Implement API" --target-files routers/api.py

    # Run backend agent directly
    python -m agent_platform.cli run be --task "Generate service" --target-files services/foo.py

    # List available agents
    python -m agent_platform.cli list

    # Show agent info
    python -m agent_platform.cli info orch
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any, Dict, List, Optional

from agent_platform.core.protocol import AgentContext
from agent_platform.core.registry import create_agent, get_registry, list_agents

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for CLI output."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def print_json(data: Any, pretty: bool = True) -> None:
    """Print data as JSON to stdout."""
    if pretty:
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    else:
        print(json.dumps(data, ensure_ascii=False, default=str))


def cmd_list(args: argparse.Namespace) -> int:
    """List all registered agents."""
    # Ensure agents are registered
    _ensure_agents_registered()

    agents = list_agents()
    if not agents:
        print("No agents registered.")
        return 0

    print(f"Registered agents ({len(agents)}):")
    print("-" * 60)
    for meta in agents:
        tags_str = ", ".join(meta.tags) if meta.tags else "none"
        print(f"  {meta.name:12} v{meta.version:8} [{tags_str}]")
        print(f"    {meta.description}")
    print("-" * 60)
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    """Show detailed info for a specific agent."""
    _ensure_agents_registered()

    agent_name = args.agent
    registry = get_registry()
    meta = registry.get_agent_metadata(agent_name)

    if meta is None:
        print(f"Error: Agent '{agent_name}' not found.")
        print(f"Available agents: {[a.name for a in list_agents()]}")
        return 1

    print(f"Agent: {meta.name}")
    print(f"  Version:     {meta.version}")
    print(f"  Description: {meta.description}")
    print(f"  Tags:        {', '.join(meta.tags) if meta.tags else 'none'}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Run an agent with the given request."""
    _ensure_agents_registered()

    agent_name = args.agent
    task = args.task
    target_files = args.target_files or []

    # Build request dict
    request: Dict[str, Any] = {}
    if task:
        request["task"] = task
    if target_files:
        request["target_files"] = target_files

    # Parse extra JSON if provided
    if args.json:
        try:
            extra = json.loads(args.json)
            request.update(extra)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in --json argument: {e}")
            return 1

    # Create agent and context
    try:
        agent = create_agent(agent_name)
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    context = AgentContext()
    run_id = context.run_id

    if args.verbose:
        print(f"[run_id={run_id}] Running agent '{agent_name}' with request:")
        print_json(request)
        print("-" * 40)

    # Execute
    result = agent.handle_request(request, context)

    # Output result
    if args.output == "json":
        print_json(result, pretty=not args.compact)
    else:
        _print_human_result(result, agent_name, run_id)

    return 0 if result.get("success", False) else 1


def cmd_orch(args: argparse.Namespace) -> int:
    """Run OrchestratorAgent with specified flow."""
    _ensure_agents_registered()

    flow = args.flow
    task = args.task or ""
    target_files = args.target_files or []
    module = args.module

    # Build orchestrator request
    request: Dict[str, Any] = {
        "flow": flow,
        "task": task,
        "target_files": target_files,
    }

    if module:
        request["module"] = module

    # Mode-specific options
    if args.mode == "execute":
        request["auto_write"] = True
    elif args.mode == "dry-run":
        request["auto_write"] = False

    # Extra JSON params
    if args.json:
        try:
            extra = json.loads(args.json)
            request.update(extra)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in --json argument: {e}")
            return 1

    # Create orchestrator and context
    try:
        orch = create_agent("orch")
    except ValueError as e:
        print(f"Error: Cannot create orchestrator: {e}")
        return 1

    context = AgentContext()
    run_id = context.run_id

    if args.verbose:
        print(f"[run_id={run_id}] Running orchestrator flow '{flow}' with request:")
        print_json(request)
        print("-" * 40)

    # Execute
    result = orch.handle_request(request, context)

    # Output result
    if args.output == "json":
        print_json(result, pretty=not args.compact)
    else:
        _print_orch_result(result, flow, run_id)

    return 0 if result.get("success", False) else 1


def _print_human_result(result: Dict[str, Any], agent_name: str, run_id: str) -> None:
    """Print agent result in human-readable format."""
    success = result.get("success", False)
    error = result.get("error")
    data = result.get("data", {})

    status = "✓ SUCCESS" if success else "✗ FAILED"
    print(f"\n{status} [{agent_name}] run_id={run_id}")

    if error:
        print(f"  Error: {error}")

    if data:
        meta = data.get("meta", {})
        if meta:
            print(f"  Agent: {meta.get('agent', 'unknown')} v{meta.get('version', '?')}")

        # Show changes summary
        changes = data.get("changes", {})
        if changes:
            print(f"  Files generated: {len(changes)}")
            for path in list(changes.keys())[:5]:
                print(f"    - {path}")
            if len(changes) > 5:
                print(f"    ... and {len(changes) - 5} more")

        # Show notes
        notes = data.get("notes", [])
        if notes:
            print("  Notes:")
            for note in notes[:5]:
                print(f"    • {note}")


def _print_orch_result(result: Dict[str, Any], flow: str, run_id: str) -> None:
    """Print orchestrator result in human-readable format."""
    success = result.get("success", False)
    error = result.get("error")
    data = result.get("data", {})

    status = "✓ SUCCESS" if success else "✗ FAILED"
    print(f"\n{status} [orch/{flow}] run_id={run_id}")

    if error:
        print(f"  Error: {error}")

    if data:
        meta = data.get("meta", {})
        called_agents = meta.get("called_agents", [])
        if called_agents:
            print(f"  Agents called: {', '.join(called_agents)}")

        # Flow-specific summaries
        if flow == "be_then_test":
            be_result = data.get("backend_result", {})
            test_result = data.get("test_result", {})

            if be_result:
                be_status = "✓" if be_result.get("success") else "✗"
                files = be_result.get("files_generated", 0)
                print(f"  Backend:  {be_status} ({files} files)")

            if test_result:
                test_status = "✓" if test_result.get("success") else "✗"
                mode = test_result.get("mode", "?")
                executed = test_result.get("executed", False)
                exec_str = "executed" if executed else "prompt only"
                print(f"  Test:     {test_status} (mode={mode}, {exec_str})")

        # Show steps for other flows
        steps = data.get("steps", {})
        if steps and flow != "be_then_test":
            print(f"  Steps completed: {len(steps)}")

        # Show notes
        notes = data.get("notes", [])
        if notes:
            print("  Notes:")
            for note in notes[:5]:
                print(f"    • {note}")
            if len(notes) > 5:
                print(f"    ... and {len(notes) - 5} more")


def _ensure_agents_registered() -> None:
    """Ensure all business agents are registered."""
    from agents.plugin import register_all

    # Check if already registered
    registry = get_registry()
    if registry.count == 0:
        register_all()


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI."""
    parser = argparse.ArgumentParser(
        prog="agent_platform",
        description="AI_ad_spend02 Agent Platform CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all agents
  python -m agent_platform.cli list

  # Run orchestrator with be_then_test flow
  python -m agent_platform.cli orch --flow be_then_test \\
    --task "Implement finance_profit API" \\
    --module finance_profit \\
    --target-files backend/routers/finance_profit.py

  # Run backend agent directly
  python -m agent_platform.cli run be \\
    --task "Generate topup service" \\
    --target-files backend/services/topup_service.py

  # Output as JSON
  python -m agent_platform.cli orch --flow backend_only \\
    --task "Refactor auth" --output json
""",
    )

    # Global options
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "-o", "--output",
        choices=["human", "json"],
        default="human",
        help="Output format (default: human)",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Compact JSON output (no indentation)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # list command
    list_parser = subparsers.add_parser("list", help="List registered agents")
    list_parser.set_defaults(func=cmd_list)

    # info command
    info_parser = subparsers.add_parser("info", help="Show agent info")
    info_parser.add_argument("agent", help="Agent name")
    info_parser.set_defaults(func=cmd_info)

    # run command (generic agent runner)
    run_parser = subparsers.add_parser("run", help="Run an agent directly")
    run_parser.add_argument("agent", help="Agent name (be, fe, test, etc.)")
    run_parser.add_argument(
        "--task", "-t",
        help="Task description",
    )
    run_parser.add_argument(
        "--target-files", "-f",
        nargs="+",
        help="Target file paths",
    )
    run_parser.add_argument(
        "--json", "-j",
        help="Additional request params as JSON string",
    )
    run_parser.set_defaults(func=cmd_run)

    # orch command (orchestrator-specific)
    orch_parser = subparsers.add_parser("orch", help="Run OrchestratorAgent")
    orch_parser.add_argument(
        "--flow", "-F",
        required=True,
        choices=[
            "be_then_test",
            "backend_only",
            "frontend_only",
            "full_pipeline",
            "frontend_restructure",
            "gen_backend",
            "auto_fix",
        ],
        help="Orchestrator flow to execute",
    )
    orch_parser.add_argument(
        "--task", "-t",
        help="Task description",
    )
    orch_parser.add_argument(
        "--target-files", "-f",
        nargs="+",
        help="Target file paths",
    )
    orch_parser.add_argument(
        "--module", "-m",
        help="Module name (for scoped operations)",
    )
    orch_parser.add_argument(
        "--mode",
        choices=["dry-run", "execute"],
        default="dry-run",
        help="Execution mode (default: dry-run)",
    )
    orch_parser.add_argument(
        "--json", "-j",
        help="Additional request params as JSON string",
    )
    orch_parser.set_defaults(func=cmd_orch)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    setup_logging(args.verbose if hasattr(args, "verbose") else False)

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
