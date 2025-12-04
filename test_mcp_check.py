"""Quick MCP server health check"""
import sys
sys.path.insert(0, r"D:\git\1108\AI_ad_spend02")

output_file = r"D:\git\1108\AI_ad_spend02\mcp_check_result.txt"
lines = []

def log(msg):
    lines.append(msg)
    print(msg)

try:
    from agent_platform.mcp.server import _registry, handle_mcp_request, REPO_ROOT
    log(f"[OK] MCP server module imported")
    log(f"[OK] REPO_ROOT: {REPO_ROOT}")
    log(f"[OK] Registered tools: {list(_registry.tools.keys())}")

    # Test tools/list
    req = {"method": "tools/list", "id": 1}
    resp = handle_mcp_request(req)
    if resp and "result" in resp:
        tools = resp["result"].get("tools", [])
        log(f"[OK] tools/list returned {len(tools)} tools")
    else:
        log(f"[WARN] tools/list response: {resp}")

    # Test ap_list_agents
    from agent_platform.mcp.server import list_agents
    result = list_agents()
    if result.get("success"):
        log(f"[OK] ap_list_agents: {result.get('count')} agents registered")
    else:
        log(f"[FAIL] ap_list_agents error: {result.get('error')}")

    log("\n=== MCP Server Status: READY ===")

except Exception as e:
    log(f"[FAIL] Import error: {e}")
    import traceback
    lines.append(traceback.format_exc())
    log("\n=== MCP Server Status: NOT WORKING ===")

finally:
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
