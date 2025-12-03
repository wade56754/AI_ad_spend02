"""
Agent Platform MCP Server

Provides MCP (Model Context Protocol) tool interface for agent_platform.
In MCP mode, Claude is the only LLM, and agent_platform provides pure tools.

This server exposes agent_platform tools as MCP tools that Claude can invoke.

Phase 3.1: MCP tool mode support
Phase 3.2: Added path security (REPO_ROOT) and ap_run_pytest tool
Phase 3.3: P2-01 whitelist mode for pytest args, P2-02 ap_run_agent tool

Environment Variables:
    AGENT_PLATFORM_MODE: Set to "mcp" to enable MCP tool mode (auto-set by this module)
    AGENT_PLATFORM_REPO_ROOT: Override repository root path (optional, for testing)

Security:
    - All file operations are restricted to within REPO_ROOT
    - Path traversal attacks (../) are blocked
    - Only relative paths are accepted for file operations
    - Pytest extra_args filtered by whitelist (Phase 3.3)
"""

import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import re


# ============================================================================
# Pytest Extra Args Whitelist (Phase 3.3 P2-01)
# ============================================================================

# Whitelist of allowed pytest arguments for MCP tool
# Only these patterns are allowed to be passed via extra_args
# Format: exact match strings or prefix patterns (ending with '=')
PYTEST_ALLOWED_ARGS = {
    # Verbosity and output
    "-v", "-vv", "-q", "-s",
    "--verbose", "--quiet",
    # Traceback control
    "--tb=",  # prefix: --tb=short, --tb=long, --tb=no, etc.
    # Test selection (safe subset)
    "-k",  # keyword expression (next arg is the expression)
    "-x", "--exitfirst",  # stop on first failure
    "--maxfail=",  # prefix: --maxfail=3
    "--lf", "--last-failed",  # re-run failures
    "--ff", "--failed-first",
    # Output formatting
    "--no-header",
    "--color=",  # prefix: --color=yes, --color=no
    # Warnings
    "-W",  # warning filter (next arg is the filter)
    "--disable-warnings",
    # Parallel execution (if pytest-xdist installed)
    "-n",  # number of workers (next arg is count)
    # Durations
    "--durations=",  # prefix: --durations=10
    # Markers (already handled by 'markers' param, but allow here too)
    "-m",
}

# Arguments that take a value as the next argument (not =value style)
PYTEST_VALUE_ARGS = {"-k", "-W", "-n", "-m"}


def _validate_pytest_extra_args(extra_args: List[str]) -> Tuple[List[str], List[str]]:
    """
    Validate pytest extra_args against whitelist.

    Phase 3.3 P2-01: Whitelist mode for extra_args security.

    Args:
        extra_args: List of extra arguments to validate

    Returns:
        Tuple of (allowed_args, rejected_args)
    """
    allowed = []
    rejected = []
    skip_next = False

    for i, arg in enumerate(extra_args):
        if skip_next:
            # This arg is a value for a previous -k/-W/-n/-m style arg
            allowed.append(arg)
            skip_next = False
            continue

        # Check exact match
        if arg in PYTEST_ALLOWED_ARGS:
            allowed.append(arg)
            # Check if this arg expects a value as next argument
            if arg in PYTEST_VALUE_ARGS:
                skip_next = True
            continue

        # Check prefix match (for --tb=short style args)
        prefix_matched = False
        for pattern in PYTEST_ALLOWED_ARGS:
            if pattern.endswith("=") and arg.startswith(pattern):
                allowed.append(arg)
                prefix_matched = True
                break

        if not prefix_matched:
            rejected.append(arg)

    return allowed, rejected

# Set MCP mode before any agent_platform imports
os.environ["AGENT_PLATFORM_MODE"] = "mcp"

logger = logging.getLogger(__name__)


# ============================================================================
# REPO_ROOT Security Layer
# ============================================================================

def _get_repo_root() -> Path:
    """
    Get the repository root directory with security considerations.

    Priority:
        1. AGENT_PLATFORM_REPO_ROOT environment variable (for testing/override)
        2. Inferred from this file's location: mcp/ -> agent_platform/ -> repo root

    Returns:
        Resolved absolute path to repository root

    Note:
        The path is always resolved to an absolute path to prevent
        symlink-based attacks and ensure consistent path comparisons.
    """
    env_root = os.environ.get("AGENT_PLATFORM_REPO_ROOT")
    if env_root:
        root = Path(env_root).resolve()
        if root.is_dir():
            logger.info(f"Using REPO_ROOT from environment: {root}")
            return root
        else:
            logger.warning(
                f"AGENT_PLATFORM_REPO_ROOT '{env_root}' is not a valid directory, "
                f"falling back to inferred path"
            )

    # Infer from file location: server.py -> mcp/ -> agent_platform/ -> repo root
    inferred = Path(__file__).resolve().parent.parent.parent
    logger.debug(f"Using inferred REPO_ROOT: {inferred}")
    return inferred


# Global REPO_ROOT - initialized once at module load
REPO_ROOT = _get_repo_root()


def validate_path_security(relative_path: str) -> Path:
    """
    Validate and resolve a relative path within REPO_ROOT.

    Security checks:
        1. Path must be relative (no absolute paths)
        2. Resolved path must be within REPO_ROOT (no ../ escapes)
        3. Path cannot start with / or contain drive letters (Windows)
        4. Path cannot be a Windows UNC path (\\\\server\\share) (Phase 3.2)

    Args:
        relative_path: File path relative to REPO_ROOT

    Returns:
        Resolved absolute Path object

    Raises:
        ValueError: If path validation fails (security violation)
    """
    # Check 1: Reject absolute paths
    if os.path.isabs(relative_path):
        raise ValueError(
            f"Absolute paths are not allowed: '{relative_path}'. "
            f"Use paths relative to repository root."
        )

    # Check 2: Reject Windows drive letters
    if len(relative_path) >= 2 and relative_path[1] == ':':
        raise ValueError(
            f"Drive letter paths are not allowed: '{relative_path}'. "
            f"Use paths relative to repository root."
        )

    # Check 3 (Phase 3.2 P1-02): Reject Windows UNC paths
    if relative_path.startswith('\\\\') or relative_path.startswith('//'):
        raise ValueError(
            f"UNC paths are not allowed: '{relative_path}'. "
            f"Use paths relative to repository root."
        )

    # Check 4: Resolve and verify within REPO_ROOT
    full_path = (REPO_ROOT / relative_path).resolve()

    try:
        full_path.relative_to(REPO_ROOT)
    except ValueError:
        raise ValueError(
            f"Path escape detected: '{relative_path}' resolves outside repository root. "
            f"This may be a directory traversal attack."
        )

    return full_path


# ============================================================================
# MCP Tool Registry
# ============================================================================

@dataclass
class MCPTool:
    """MCP tool definition"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable[..., Dict[str, Any]]


@dataclass
class MCPToolRegistry:
    """Registry for MCP tools"""
    tools: Dict[str, MCPTool] = field(default_factory=dict)

    def register(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
    ) -> Callable:
        """
        Decorator to register an MCP tool.

        Args:
            name: Tool name (e.g., "ap_list_agents")
            description: Tool description for Claude
            input_schema: JSON Schema for input parameters

        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            self.tools[name] = MCPTool(
                name=name,
                description=description,
                input_schema=input_schema,
                handler=func,
            )
            return func
        return decorator

    def get_tool(self, name: str) -> Optional[MCPTool]:
        """Get a tool by name"""
        return self.tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools in MCP format"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
            }
            for tool in self.tools.values()
        ]


# Global tool registry
_registry = MCPToolRegistry()


# ============================================================================
# MCP Tool Definitions
# ============================================================================

@_registry.register(
    name="ap_list_agents",
    description="List all available agents in the agent platform",
    input_schema={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
def list_agents() -> Dict[str, Any]:
    """List all registered agents"""
    try:
        from agents.agents_config import _AGENT_REGISTRY

        agents = []
        for key, meta in _AGENT_REGISTRY.items():
            # Try to get agent instance for metadata
            try:
                agent = meta.factory()
                agents.append({
                    "key": key,
                    "name": agent.name,
                    "description": getattr(agent, "description", ""),
                })
            except Exception as e:
                # Fallback to AgentMeta metadata if agent creation fails
                agents.append({
                    "key": key,
                    "name": meta.name,
                    "description": meta.description or f"(unavailable: {e})",
                })

        return {
            "success": True,
            "agents": agents,
            "count": len(agents),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@_registry.register(
    name="ap_read_sot_file",
    description="Read a Source of Truth (SoT) document from the docs directory",
    input_schema={
        "type": "object",
        "properties": {
            "sot_key": {
                "type": "string",
                "description": "SoT file key (e.g., 'DATA_SCHEMA', 'STATE_MACHINE', 'API_SOT')",
            },
        },
        "required": ["sot_key"],
    },
)
def read_sot_file(sot_key: str) -> Dict[str, Any]:
    """Read a SoT file by key"""
    try:
        from agents.agents_config import SOT_FILES

        if sot_key not in SOT_FILES:
            return {
                "success": False,
                "error": f"Unknown SoT key: {sot_key}",
                "available_keys": list(SOT_FILES.keys()),
            }

        file_path = SOT_FILES[sot_key]

        # Use security-validated path resolution
        try:
            full_path = validate_path_security(str(file_path))
        except ValueError as e:
            return {
                "success": False,
                "error": f"Security validation failed: {e}",
            }

        if not full_path.exists():
            return {
                "success": False,
                "error": f"SoT file not found: {file_path}",
            }

        content = full_path.read_text(encoding="utf-8")

        return {
            "success": True,
            "key": sot_key,
            "path": str(file_path),
            "content": content,
            "size": len(content),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@_registry.register(
    name="ap_list_sot_files",
    description="List all available SoT (Source of Truth) document keys",
    input_schema={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
def list_sot_files() -> Dict[str, Any]:
    """List all SoT file keys"""
    try:
        from agents.agents_config import SOT_FILES

        return {
            "success": True,
            "sot_files": [
                {"key": key, "path": str(path)}
                for key, path in SOT_FILES.items()
            ],
            "count": len(SOT_FILES),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@_registry.register(
    name="ap_read_file",
    description=(
        "Read a file from the repository. "
        "Path must be relative to repository root (e.g., 'backend/main.py', 'docs/README.md'). "
        "Absolute paths and directory traversal (../) are not allowed."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "File path relative to repository root (e.g., 'backend/main.py')",
            },
        },
        "required": ["path"],
    },
)
def read_file(path: str) -> Dict[str, Any]:
    """Read a file from the repository with security validation"""
    try:
        # Security validation
        try:
            full_path = validate_path_security(path)
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "error_kind": "SECURITY_ERROR",
            }

        if not full_path.exists():
            return {
                "success": False,
                "error": f"File not found: {path}",
                "error_kind": "NOT_FOUND",
            }

        if not full_path.is_file():
            return {
                "success": False,
                "error": f"Path is not a file: {path}",
                "error_kind": "INVALID_PATH",
            }

        content = full_path.read_text(encoding="utf-8")

        return {
            "success": True,
            "path": path,
            "content": content,
            "size": len(content),
        }
    except UnicodeDecodeError as e:
        return {
            "success": False,
            "error": f"File is not valid UTF-8 text: {e}",
            "error_kind": "ENCODING_ERROR",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_kind": "UNKNOWN",
        }


@_registry.register(
    name="ap_write_file",
    description=(
        "Write content to a file in the repository. "
        "Path must be relative to repository root (e.g., 'backend/main.py'). "
        "Absolute paths and directory traversal (../) are not allowed. "
        "Parent directories will be created if they don't exist."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "File path relative to repository root (e.g., 'backend/main.py')",
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file",
            },
        },
        "required": ["path", "content"],
    },
)
def write_file(path: str, content: str) -> Dict[str, Any]:
    """Write content to a file with security validation"""
    try:
        # Security validation
        try:
            full_path = validate_path_security(path)
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "error_kind": "SECURITY_ERROR",
            }

        # Create parent directories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if this is a new file or update
        is_new = not full_path.exists()

        # Write the file
        full_path.write_text(content, encoding="utf-8")

        return {
            "success": True,
            "path": path,
            "size": len(content),
            "action": "created" if is_new else "updated",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_kind": "WRITE_ERROR",
        }


@_registry.register(
    name="ap_run_pytest",
    description=(
        "Run pytest tests and return structured results. "
        "Useful for verifying code changes don't break existing functionality. "
        "Returns test summary with pass/fail counts and failure details. "
        "Note: extra_args are filtered by whitelist for security (Phase 3.3)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "test_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "List of test paths relative to repository root "
                    "(e.g., ['tests/', 'agent_platform/tests/']). "
                    "Defaults to ['tests/'] if not specified."
                ),
            },
            "markers": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Pytest markers to filter tests (e.g., ['unit', 'not slow']). "
                    "Maps to pytest -m option."
                ),
            },
            "max_failures": {
                "type": "integer",
                "description": (
                    "Maximum number of failure details to return (default: 10). "
                    "Helps prevent overly large responses."
                ),
            },
            "extra_args": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Extra arguments to pass to pytest. "
                    "Only whitelisted args are allowed: -v, -q, -s, --tb=*, -k, -x, --maxfail=*, "
                    "--lf, --ff, --durations=*, etc. Unrecognized args will be rejected."
                ),
            },
        },
        "required": [],
    },
)
def run_pytest(
    test_paths: Optional[List[str]] = None,
    markers: Optional[List[str]] = None,
    max_failures: int = 10,
    extra_args: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Run pytest tests and return structured results.

    This tool runs pytest as a subprocess and parses the output to provide
    structured test results suitable for MCP responses.

    Phase 3.3 P2-01: extra_args now uses whitelist mode for security.
    """
    try:
        # Default test paths
        if not test_paths:
            test_paths = ["tests/"]

        # Validate test paths (security check)
        validated_paths = []
        for test_path in test_paths:
            try:
                full_path = validate_path_security(test_path)
                if full_path.exists():
                    validated_paths.append(str(full_path))
                else:
                    logger.warning(f"Test path does not exist: {test_path}")
            except ValueError as e:
                return {
                    "success": False,
                    "error": f"Invalid test path '{test_path}': {e}",
                    "error_kind": "SECURITY_ERROR",
                }

        if not validated_paths:
            return {
                "success": False,
                "error": "No valid test paths found",
                "error_kind": "NOT_FOUND",
            }

        # Build pytest command
        cmd = [sys.executable, "-m", "pytest", "--tb=short", "-q"]

        # Add markers if specified
        if markers:
            marker_expr = " and ".join(markers)
            cmd.extend(["-m", marker_expr])

        # Phase 3.3 P2-01: Whitelist mode for extra_args
        if extra_args:
            allowed_args, rejected_args = _validate_pytest_extra_args(extra_args)

            if rejected_args:
                return {
                    "success": False,
                    "error": (
                        f"Rejected pytest arguments not in whitelist: {rejected_args}. "
                        f"Allowed patterns: -v, -q, -s, --tb=*, -k <expr>, -x, --maxfail=*, "
                        f"--lf, --ff, --durations=*, -n <count>, -W <filter>, etc."
                    ),
                    "error_kind": "CONFIG_ERROR",
                    "rejected_args": rejected_args,
                    "allowed_args": allowed_args,
                }

            cmd.extend(allowed_args)

        # Add test paths
        cmd.extend(validated_paths)

        logger.info(f"Running pytest command: {' '.join(cmd)}")

        # Run pytest as subprocess
        result = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
        )

        # Parse output
        stdout = result.stdout
        stderr = result.stderr
        return_code = result.returncode

        # Truncate output if too long
        max_output_len = 10000
        if len(stdout) > max_output_len:
            stdout = stdout[:max_output_len] + "\n... (output truncated)"
        if len(stderr) > max_output_len:
            stderr = stderr[:max_output_len] + "\n... (output truncated)"

        # Parse test summary from output
        summary = _parse_pytest_summary(stdout)

        # Extract failure details (limited by max_failures)
        failures = _extract_pytest_failures(stdout, max_failures)

        return {
            "success": return_code == 0,
            "return_code": return_code,
            "summary": summary,
            "failures": failures,
            "stdout": stdout,
            "stderr": stderr if stderr else None,
            "test_paths": test_paths,
            "markers": markers,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Pytest execution timed out (5 minute limit)",
            "error_kind": "TIMEOUT",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_kind": "EXECUTION_ERROR",
        }


def _parse_pytest_summary(output: str) -> Dict[str, Any]:
    """
    Parse pytest summary line from output.

    Looks for patterns like:
    - "5 passed, 2 failed, 1 error in 1.23s"
    - "10 passed in 0.50s"
    """
    summary = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "duration": None,
    }

    # Look for the summary line
    patterns = [
        (r"(\d+) passed", "passed"),
        (r"(\d+) failed", "failed"),
        (r"(\d+) error", "errors"),
        (r"(\d+) skipped", "skipped"),
        (r"in ([\d.]+)s", "duration"),
    ]

    for line in output.split("\n"):
        line_lower = line.lower()
        if "passed" in line_lower or "failed" in line_lower or "error" in line_lower:
            for pattern, key in patterns:
                match = re.search(pattern, line)
                if match:
                    value = match.group(1)
                    if key == "duration":
                        summary[key] = float(value)
                    else:
                        summary[key] = int(value)

    summary["total"] = (
        summary["passed"] + summary["failed"] +
        summary["errors"] + summary["skipped"]
    )

    return summary


def _extract_pytest_failures(output: str, max_failures: int) -> List[Dict[str, str]]:
    """
    Extract failure details from pytest output.

    Returns list of dicts with 'test_name' and 'message' keys.
    """
    failures = []

    # Look for FAILED lines
    failed_pattern = re.compile(r"FAILED\s+(.+?)\s+-\s+(.+)")

    for line in output.split("\n"):
        if len(failures) >= max_failures:
            break
        match = failed_pattern.search(line)
        if match:
            failures.append({
                "test_name": match.group(1).strip(),
                "message": match.group(2).strip()[:200],  # Truncate long messages
            })

    # Also look for short test failure lines (pytest -q format)
    short_pattern = re.compile(r"^(\S+::\S+)\s+FAILED")

    for line in output.split("\n"):
        if len(failures) >= max_failures:
            break
        match = short_pattern.match(line)
        if match and not any(f["test_name"] == match.group(1) for f in failures):
            failures.append({
                "test_name": match.group(1),
                "message": "(see stdout for details)",
            })

    return failures


# ============================================================================
# ap_run_agent MCP Tool (Phase 3.3 P2-02)
# ============================================================================

@_registry.register(
    name="ap_run_agent",
    description=(
        "Run an agent from the agent platform. "
        "Available agents: fe (frontend), be (backend), test, orch (orchestrator), doc, review. "
        "The agent will process the payload and return structured results. "
        "Note: In MCP mode, agents cannot call LLM APIs directly."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "agent_name": {
                "type": "string",
                "description": (
                    "Agent name/key to run. Available: "
                    "'fe' (frontend), 'be' (backend), 'test', 'orch' (orchestrator), 'doc', 'review'"
                ),
                "enum": ["fe", "be", "test", "orch", "doc", "review"],
            },
            "payload": {
                "type": "object",
                "description": (
                    "Request payload to pass to agent.handle_request(). "
                    "Structure varies by agent type. Common fields: 'task', 'flow', 'files'."
                ),
            },
            "context": {
                "type": "object",
                "description": (
                    "Optional context dict for agent execution. "
                    "May include 'run_id', 'dry_run', etc."
                ),
            },
        },
        "required": ["agent_name", "payload"],
    },
)
def run_agent(
    agent_name: str,
    payload: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run an agent and return its response.

    Phase 3.3 P2-02: MCP tool for invoking agents.

    Note: In MCP mode, agents cannot call LLM APIs. The LLM guard in
    agent_platform.llm.base.LLMClient will raise LLMNotConfiguredError
    if any agent attempts to create an LLM client.
    """
    try:
        from agents.agents_config import create_agent, list_agents

        # Validate agent_name
        available_agents = list_agents()
        if agent_name.lower() not in available_agents:
            return {
                "success": False,
                "error": f"Unknown agent '{agent_name}'",
                "error_kind": "AGENT_NOT_FOUND",
                "available_agents": list(available_agents.keys()),
            }

        # Create agent instance
        try:
            agent = create_agent(agent_name)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create agent '{agent_name}': {e}",
                "error_kind": "AGENT_CREATION_ERROR",
            }

        # Verify agent has handle_request method
        if not hasattr(agent, "handle_request"):
            return {
                "success": False,
                "error": f"Agent '{agent_name}' does not implement handle_request()",
                "error_kind": "AGENT_PROTOCOL_ERROR",
            }

        # Execute agent
        try:
            # Note: In MCP mode, if the agent tries to call LLM,
            # it will get LLMNotConfiguredError from the LLM guard
            result = agent.handle_request(payload, context or {})
        except Exception as e:
            # Check if this is an LLM-related error (MCP mode guard)
            error_str = str(e)
            if "MCP" in error_str or "LLM" in error_str or "工具模式" in error_str:
                return {
                    "success": False,
                    "error": (
                        f"Agent '{agent_name}' attempted to call LLM in MCP mode. "
                        f"In MCP mode, Claude is the only LLM. "
                        f"Original error: {error_str[:200]}"
                    ),
                    "error_kind": "LLM_NOT_ALLOWED",
                    "agent_name": agent_name,
                }
            else:
                return {
                    "success": False,
                    "error": f"Agent execution failed: {error_str[:500]}",
                    "error_kind": "AGENT_EXECUTION_ERROR",
                    "agent_name": agent_name,
                }

        # Wrap and return result
        # The agent should return AgentResponse structure
        return {
            "success": result.get("success", False),
            "agent_name": agent_name,
            "agent_result": result,
            # Extract summary for convenience
            "summary": _extract_agent_summary(agent_name, result),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_kind": "UNKNOWN",
            "agent_name": agent_name,
        }


def _extract_agent_summary(agent_name: str, result: Dict[str, Any]) -> str:
    """
    Extract a brief summary from agent result for MCP response.

    This helps Claude quickly understand what the agent did.
    """
    if not result.get("success"):
        return f"Agent {agent_name} failed: {result.get('error', 'Unknown error')}"

    data = result.get("data", {})

    # Different summary formats for different agents
    if agent_name in ("fe", "be"):
        changes = data.get("changes", {})
        notes = data.get("notes", [])
        return (
            f"Agent {agent_name} completed. "
            f"Files changed: {len(changes)}. "
            f"Notes: {', '.join(notes[:3]) if notes else 'None'}"
        )
    elif agent_name == "test":
        executed = data.get("executed", False)
        return (
            f"TestAgent completed. "
            f"Tests executed: {executed}. "
            f"Prompt generated: {'Yes' if data.get('prompt') else 'No'}"
        )
    elif agent_name == "orch":
        flow = data.get("flow", "unknown")
        steps = data.get("steps", {})
        return (
            f"OrchestratorAgent completed flow '{flow}'. "
            f"Steps: {len(steps)}"
        )
    elif agent_name == "doc":
        action = data.get("action", "unknown")
        doc_type = data.get("doc_type", "")
        return f"DocAgent completed action '{action}' for {doc_type}"
    elif agent_name == "review":
        passed = data.get("passed", False)
        violations = len(data.get("violations", []))
        return (
            f"CodeReviewAgent completed. "
            f"Passed: {passed}. "
            f"Violations: {violations}"
        )
    else:
        return f"Agent {agent_name} completed successfully"


# ============================================================================
# MCP Server Implementation
# ============================================================================

def create_mcp_server() -> MCPToolRegistry:
    """
    Create and return the MCP tool registry.

    Returns:
        MCPToolRegistry with all registered tools
    """
    return _registry


def handle_mcp_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle an MCP request.

    Args:
        request: MCP request with "method" and "params"

    Returns:
        MCP response
    """
    method = request.get("method", "")
    params = request.get("params", {})
    request_id = request.get("id")

    if method == "tools/list":
        return {
            "id": request_id,
            "result": {
                "tools": _registry.list_tools(),
            },
        }

    elif method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})

        tool = _registry.get_tool(tool_name)
        if not tool:
            return {
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}",
                },
            }

        try:
            result = tool.handler(**tool_args)
            return {
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2),
                        }
                    ],
                },
            }
        except Exception as e:
            return {
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": str(e),
                },
            }

    else:
        return {
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Unknown method: {method}",
            },
        }


def run_stdio_server() -> None:
    """
    Run MCP server in stdio mode.

    Reads JSON-RPC requests from stdin, writes responses to stdout.
    """
    logger.info("Starting Agent Platform MCP Server (stdio mode)")
    logger.info(f"REPO_ROOT: {REPO_ROOT}")
    logger.info(f"Registered tools: {list(_registry.tools.keys())}")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
            response = handle_mcp_request(request)
            print(json.dumps(response), flush=True)
        except json.JSONDecodeError as e:
            error_response = {
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {e}",
                },
            }
            print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    run_stdio_server()
