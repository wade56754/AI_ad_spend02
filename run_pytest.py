import subprocess
import sys
import os

os.chdir(r"D:\git\1108\AI_ad_spend02")

try:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "agent_platform/tests/test_mcp_server.py",
            "agent_platform/tests/test_mcp_server_agents.py",
            "agent_platform/tests/test_skills_registry.py",
            "-v",
            "--tb=line"
        ],
        capture_output=True,
        text=True
    )

    output = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n\nReturn code: {result.returncode}\n"
    print(output)

    # Save to file with absolute path
    output_path = r"D:\git\1108\AI_ad_spend02\pytest_output.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"\nOutput saved to: {output_path}")

except Exception as e:
    error_msg = f"Error running pytest: {str(e)}\n"
    print(error_msg)
    with open(r"D:\git\1108\AI_ad_spend02\pytest_error.txt", "w", encoding="utf-8") as f:
        f.write(error_msg)
