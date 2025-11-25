#!/usr/bin/env python3
"""测试 quick-check 模式是否有输出"""
import subprocess
import sys

print("=" * 60)
print("测试 quick-check 模式输出")
print("=" * 60)

cmd = [
    "python", "super_review_agent.py", "quick-check",
    "--doc", "docs/3.dev-guides/DDD_API_ARCHITECTURE.md",
    "--codex-prompt", ".codex/prompts/doc-reviewer-codex.txt"
]

print(f"\n执行命令: {' '.join(cmd)}\n")
print("-" * 60)

result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    timeout=120
)

print("STDOUT:")
print(result.stdout if result.stdout else "(无输出)")
print("\nSTDERR:")
print(result.stderr if result.stderr else "(无错误)")
print(f"\nExit Code: {result.returncode}")

print("-" * 60)

if result.stdout and ("Quick Check" in result.stdout or "P0=" in result.stdout):
    print("\n✅ 测试通过：quick-check 有输出反馈")
    sys.exit(0)
elif result.returncode == 0:
    print("\n⚠️  测试警告：命令成功但无预期输出")
    sys.exit(1)
else:
    print("\n❌ 测试失败：命令执行失败")
    sys.exit(1)
