#!/usr/bin/env python
"""Test runner that captures all output to a file"""
import sys
import os
from io import StringIO

# Change to project directory
os.chdir(r"D:\git\1108\AI_ad_spend02")
sys.path.insert(0, r"D:\git\1108\AI_ad_spend02")

# Redirect stdout and stderr
output_buffer = StringIO()
error_buffer = StringIO()

class TeeOutput:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            stream.write(data)
            stream.flush()

    def flush(self):
        for stream in self.streams:
            stream.flush()

# Save original streams
original_stdout = sys.stdout
original_stderr = sys.stderr

# Create file for output
output_file = open(r"D:\git\1108\AI_ad_spend02\test_results_final.txt", "w", encoding="utf-8")

# Redirect to both file and buffer
sys.stdout = TeeOutput(output_file, output_buffer)
sys.stderr = TeeOutput(output_file, error_buffer)

try:
    print("=" * 80)
    print("Starting pytest execution...")
    print("=" * 80)

    import pytest

    # Run pytest
    exit_code = pytest.main([
        "agent_platform/tests/test_mcp_server.py",
        "agent_platform/tests/test_mcp_server_agents.py",
        "agent_platform/tests/test_skills_registry.py",
        "-v",
        "--tb=line",
        "--no-header"
    ])

    print("=" * 80)
    print(f"Tests completed with exit code: {exit_code}")
    print("=" * 80)

except Exception as e:
    print(f"ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

finally:
    # Restore original streams
    sys.stdout = original_stdout
    sys.stderr = original_stderr
    output_file.close()

    print(f"Output written to: D:\\git\\1108\\AI_ad_spend02\\test_results_final.txt")
