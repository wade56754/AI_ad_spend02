#!/usr/bin/env python
"""Manual test runner that executes tests and saves results"""
import sys
import os

# Setup
os.chdir(r"D:\git\1108\AI_ad_spend02")
sys.path.insert(0, r"D:\git\1108\AI_ad_spend02")

# Capture results
results = []
results.append("=" * 80)
results.append("PYTEST REGRESSION TEST REPORT")
results.append("=" * 80)
results.append("")

try:
    # Import and run pytest
    import pytest

    # Create a custom plugin to capture results
    class ResultCollector:
        def __init__(self):
            self.passed = []
            self.failed = []
            self.skipped = []

        def pytest_runtest_logreport(self, report):
            if report.when == "call":
                if report.passed:
                    self.passed.append(report.nodeid)
                elif report.failed:
                    self.failed.append({
                        "nodeid": report.nodeid,
                        "error": str(report.longrepr)
                    })
                elif report.skipped:
                    self.skipped.append(report.nodeid)

    collector = ResultCollector()

    # Run tests
    exit_code = pytest.main([
        "agent_platform/tests/test_mcp_server.py",
        "agent_platform/tests/test_mcp_server_agents.py",
        "agent_platform/tests/test_skills_registry.py",
        "-v",
        "--tb=short",
        "-p", "no:terminal",
        "--quiet"
    ], plugins=[collector])

    # Format results
    total = len(collector.passed) + len(collector.failed) + len(collector.skipped)
    results.append(f"Total tests: {total}")
    results.append(f"Passed: {len(collector.passed)}")
    results.append(f"Failed: {len(collector.failed)}")
    results.append(f"Skipped: {len(collector.skipped)}")
    results.append("")

    if collector.failed:
        results.append("FAILED TESTS:")
        results.append("-" * 80)
        for failure in collector.failed:
            results.append(f"\nTest: {failure['nodeid']}")
            results.append(f"Error: {failure['error'][:500]}")  # First 500 chars
            results.append("")

    if collector.passed:
        results.append("PASSED TESTS:")
        results.append("-" * 80)
        for test in collector.passed:
            results.append(f"  - {test}")
        results.append("")

    results.append("=" * 80)
    results.append(f"Exit code: {exit_code}")
    results.append("=" * 80)

except Exception as e:
    results.append(f"ERROR: {str(e)}")
    import traceback
    results.append(traceback.format_exc())

# Write results
output = "\n".join(results)
print(output)

# Try to save to file
try:
    with open("manual_test_results.txt", "w", encoding="utf-8") as f:
        f.write(output)
except Exception as e:
    print(f"Could not save to file: {e}")
