#!/usr/bin/env python
"""Phase 2 Health Check Script"""
import sys
import os

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

print("=== Phase 2 Health Check ===\n")

# Test 1: Import agent_platform.agents
print("1. Import test...")
try:
    from agent_platform.agents import (
        list_agents,
        list_mcp_safe_agents,
        is_agent_mcp_safe,
        create_agent,
    )
    print("   PASS: agent_platform.agents imported successfully")
except Exception as e:
    print(f"   FAIL: {e}")
    sys.exit(1)

# Test 2: List all agents
print("\n2. List all agents...")
try:
    all_agents = list_agents()
    names = [a.name for a in all_agents]
    print(f"   All agents ({len(all_agents)}): {names}")
except Exception as e:
    print(f"   FAIL: {e}")

# Test 3: List MCP safe agents
print("\n3. List MCP safe agents...")
try:
    safe_agents = list_mcp_safe_agents()
    safe_names = [a.name for a in safe_agents]
    print(f"   MCP safe agents ({len(safe_agents)}): {safe_names}")
except Exception as e:
    print(f"   FAIL: {e}")

# Test 4: Check mcp_safe status
print("\n4. mcp_safe status check...")
expected = {
    'test': True,
    'review': True,
    'doc': True,
    'fe': False,
    'be': False,
    'orch': False,
}
all_pass = True
for name, expected_val in expected.items():
    actual = is_agent_mcp_safe(name)
    status = "PASS" if actual == expected_val else "FAIL"
    if actual != expected_val:
        all_pass = False
    print(f"   {name}: {actual} (expected {expected_val}) - {status}")

# Test 5: Create agents
print("\n5. Agent creation test...")
for name in ['test', 'review', 'doc']:
    try:
        agent = create_agent(name)
        print(f"   {name}: PASS (name={agent.name}, version={agent.version})")
    except Exception as e:
        print(f"   {name}: FAIL ({e})")

print("\n=== Health Check Complete ===")
