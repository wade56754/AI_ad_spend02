"""
Agent Platform MCP Server Package

Provides MCP (Model Context Protocol) tool interface for agent_platform.
In MCP mode, Claude is the only LLM, and agent_platform provides pure tools.

Environment Variables:
    AGENT_PLATFORM_MODE: Set to "mcp" to enable MCP tool mode
        - "cli" (default): Agents can call LLM APIs directly
        - "mcp": Pure tool mode, Claude is the only LLM

    AGENT_PLATFORM_REPO_ROOT: Override repository root path (optional)
        - Used for testing or when running from non-standard locations

Usage:
    # CLI mode (default) - agents can call LLM
    python -m agent_platform.cli run fe --task "Create button"

    # MCP mode - Claude is the LLM, agent_platform provides tools
    export AGENT_PLATFORM_MODE=mcp
    python -m agent_platform.mcp.server

Available MCP Tools:
    - ap_list_agents: List all available agents
    - ap_read_sot_file: Read a SoT document by key
    - ap_list_sot_files: List all SoT file keys
    - ap_read_file: Read a file from the repository (with path security)
    - ap_write_file: Write a file to the repository (with path security)
    - ap_run_pytest: Run pytest tests and return structured results

Phase 3.1: MCP tool mode support
Phase 3.2: Added path security and ap_run_pytest tool
"""

from .server import (
    create_mcp_server,
    MCPToolRegistry,
    REPO_ROOT,
    validate_path_security,
)

__all__ = [
    "create_mcp_server",
    "MCPToolRegistry",
    "REPO_ROOT",
    "validate_path_security",
]
