#!/usr/bin/env python
"""Quick test script to check MCP server import and initialization."""
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print(f"Python: {sys.version}")
print(f"Project root: {project_root}")

try:
    print("\n1. Testing agent_platform.mcp.server import...")
    os.environ["AGENT_PLATFORM_MODE"] = "mcp"
    from agent_platform.mcp import server
    print(f"   OK - REPO_ROOT: {server.REPO_ROOT}")

    print("\n2. Testing tool registry...")
    tools = server._registry.list_tools()
    print(f"   OK - Registered {len(tools)} tools:")
    for t in tools:
        print(f"      - {t['name']}")

    print("\n3. Testing agents.agents_config import...")
    from agents.agents_config import _AGENT_REGISTRY, SOT_FILES
    print(f"   OK - Registered {len(_AGENT_REGISTRY)} agents")
    print(f"   OK - SOT_FILES: {len(SOT_FILES)} files")

    print("\n✅ All imports successful! MCP server should work.")

except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
