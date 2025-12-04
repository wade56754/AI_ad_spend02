#!/usr/bin/env python
"""Direct test runner that captures output reliably"""
import sys
import os

# Set up environment
os.chdir(r"D:\git\1108\AI_ad_spend02")
sys.path.insert(0, r"D:\git\1108\AI_ad_spend02")

# Import pytest
import pytest

# Create output file
output_file = r"D:\git\1108\AI_ad_spend02\test_run_output.txt"

# Run tests with output to file
with open(output_file, "w", encoding="utf-8") as f:
    # Redirect stdout to file
    old_stdout = sys.stdout
    sys.stdout = f

    # Print start marker
    print("=" * 80)
    print("PYTEST TEST EXECUTION")
    print("=" * 80)

    # Run pytest with arguments
    exit_code = pytest.main([
        "agent_platform/tests/test_mcp_server.py",
        "agent_platform/tests/test_mcp_server_agents.py",
        "agent_platform/tests/test_skills_registry.py",
        "-v",
        "--tb=line",
        "-s"  # Don't capture output
    ])

    # Print end marker
    print("=" * 80)
    print(f"EXIT CODE: {exit_code}")
    print("=" * 80)

    # Restore stdout
    sys.stdout = old_stdout

print(f"Test output written to: {output_file}")
print(f"Exit code: {exit_code}")
sys.exit(exit_code)
