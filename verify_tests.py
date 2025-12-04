#!/usr/bin/env python
"""Verify test execution by running pytest programmatically with detailed output"""
import sys
import os

# Setup
os.chdir(r"D:\git\1108\AI_ad_spend02")
sys.path.insert(0, r"D:\git\1108\AI_ad_spend02")

print("Starting test verification...")
print("=" * 80)

try:
    import pytest

    # Run tests and capture results
    exit_code = pytest.main([
        "agent_platform/tests/test_mcp_server.py",
        "agent_platform/tests/test_mcp_server_agents.py",
        "agent_platform/tests/test_skills_registry.py",
        "-v",
        "--tb=short",
        "-ra"  # Show summary of all outcomes
    ])

    print("=" * 80)
    print(f"\nFinal Exit Code: {exit_code}")

    if exit_code == 0:
        print("\n SUCCESS: All tests passed!")
    elif exit_code == 1:
        print("\n FAILURE: Some tests failed")
    elif exit_code == 2:
        print("\n ERROR: Test execution was interrupted")
    elif exit_code == 3:
        print("\n ERROR: Internal error")
    elif exit_code == 4:
        print("\n ERROR: pytest command line usage error")
    elif exit_code == 5:
        print("\n ERROR: No tests collected")

    print("=" * 80)
    sys.exit(exit_code)

except Exception as e:
    print(f"\nERROR during test execution: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(99)
