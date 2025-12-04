"""Minimal MCP server test"""
import sys
import os

# Ensure AGENT_PLATFORM_MODE is set
os.environ["AGENT_PLATFORM_MODE"] = "mcp"

sys.path.insert(0, r"D:\git\1108\AI_ad_spend02")

result_lines = []

def log(msg):
    result_lines.append(msg)

# Step 1: Basic import
log("Step 1: Testing basic imports...")
try:
    from pathlib import Path
    log("  [OK] pathlib")
except Exception as e:
    log(f"  [FAIL] pathlib: {e}")

# Step 2: agent_platform.mcp.server direct import
log("\nStep 2: Testing agent_platform.mcp.server import...")
try:
    # This sets AGENT_PLATFORM_MODE before importing
    from agent_platform.mcp.server import _registry, REPO_ROOT
    log(f"  [OK] server module imported")
    log(f"  [OK] REPO_ROOT: {REPO_ROOT}")
    log(f"  [OK] Tools: {list(_registry.tools.keys())}")
except Exception as e:
    log(f"  [FAIL] {type(e).__name__}: {e}")
    import traceback
    log(traceback.format_exc())

# Step 3: Test handle_mcp_request
log("\nStep 3: Testing handle_mcp_request...")
try:
    from agent_platform.mcp.server import handle_mcp_request
    resp = handle_mcp_request({"method": "tools/list", "id": 1})
    if resp and "result" in resp:
        tools_count = len(resp["result"].get("tools", []))
        log(f"  [OK] tools/list returned {tools_count} tools")
    else:
        log(f"  [WARN] Unexpected response: {resp}")
except Exception as e:
    log(f"  [FAIL] {type(e).__name__}: {e}")

# Step 4: Test list_agents (this requires agents module)
log("\nStep 4: Testing list_agents...")
try:
    from agent_platform.mcp.server import list_agents
    result = list_agents()
    if result.get("success"):
        log(f"  [OK] {result.get('count')} agents available")
        for agent in result.get("agents", []):
            log(f"      - {agent['key']}: {agent['name']}")
    else:
        log(f"  [FAIL] {result.get('error')}")
except Exception as e:
    log(f"  [FAIL] {type(e).__name__}: {e}")
    import traceback
    log(traceback.format_exc())

# Final status
log("\n" + "=" * 50)
has_fail = any("[FAIL]" in line for line in result_lines)
if has_fail:
    log("=== MCP Server Status: HAS ISSUES ===")
else:
    log("=== MCP Server Status: READY ===")

# Write to file
output_path = r"D:\git\1108\AI_ad_spend02\mcp_test_result.txt"
with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(result_lines))

# Also print
for line in result_lines:
    print(line)
