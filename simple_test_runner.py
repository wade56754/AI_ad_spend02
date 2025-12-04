import sys
import os

# Change to project directory
os.chdir(r"D:\git\1108\AI_ad_spend02")

# Add project to path
sys.path.insert(0, r"D:\git\1108\AI_ad_spend02")

print("=" * 80)
print("Running pytest tests...")
print("=" * 80)

import pytest

# Run pytest programmatically
exit_code = pytest.main([
    "agent_platform/tests/test_mcp_server.py",
    "agent_platform/tests/test_mcp_server_agents.py",
    "agent_platform/tests/test_skills_registry.py",
    "-v",
    "--tb=line"
])

print("=" * 80)
print(f"Tests completed with exit code: {exit_code}")
print("=" * 80)
