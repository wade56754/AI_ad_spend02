"""Simple import check for MCP server module."""

# First write a marker file to prove the script ran
with open(r"D:\git\1108\AI_ad_spend02\script_ran.txt", "w") as f:
    f.write("Script started\n")

try:
    from agent_platform.mcp.server import _registry, list_agents, run_agent
    with open(r"D:\git\1108\AI_ad_spend02\script_ran.txt", "a") as f:
        f.write("Imports successful\n")
        f.write(f"Registry tools: {list(_registry.tools.keys())}\n")

    # Test list_agents
    result = list_agents()
    with open(r"D:\git\1108\AI_ad_spend02\script_ran.txt", "a") as f:
        f.write(f"list_agents result: {result}\n")

    # Test run_agent on MCP-safe agent
    result2 = run_agent("review", {"action": "review", "changes": {}})
    with open(r"D:\git\1108\AI_ad_spend02\script_ran.txt", "a") as f:
        f.write(f"run_agent review result: {result2}\n")

    # Test run_agent on MCP-unsafe agent (should be blocked)
    result3 = run_agent("be", {"task": "test"})
    with open(r"D:\git\1108\AI_ad_spend02\script_ran.txt", "a") as f:
        f.write(f"run_agent be result: {result3}\n")

    with open(r"D:\git\1108\AI_ad_spend02\script_ran.txt", "a") as f:
        f.write("All tests completed successfully\n")

except Exception as e:
    with open(r"D:\git\1108\AI_ad_spend02\script_ran.txt", "a") as f:
        f.write(f"ERROR: {type(e).__name__}: {e}\n")
