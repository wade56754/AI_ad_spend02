"""Quick test runner to check MCP server tests."""
import subprocess
import sys
import os

def main():
    os.chdir(r"D:\git\1108\AI_ad_spend02")

    result = subprocess.run(
        [
            r"D:\git\1108\AI_ad_spend02\.venv\Scripts\python.exe", "-m", "pytest",
            "agent_platform/tests/test_mcp_server.py",
            "agent_platform/tests/test_mcp_server_agents.py",
            "agent_platform/tests/test_skills_registry.py",
            "-v", "--tb=line"
        ],
        capture_output=True,
        text=True
    )

    output = f"""{"=" * 60}
PYTEST RESULTS
{"=" * 60}
{result.stdout}

STDERR:
{result.stderr}

Return code: {result.returncode}
"""

    print(output)

    # Write results to file with explicit path
    output_path = r"D:\git\1108\AI_ad_spend02\test_results_output.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"Results written to: {output_path}")

if __name__ == "__main__":
    main()
