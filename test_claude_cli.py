#!/usr/bin/env python3
"""测试 Claude CLI 是否可用"""
import subprocess
import sys

print("测试 Claude CLI...")
print("=" * 50)

try:
    # 测试 1: 检查 claude 命令是否存在
    result = subprocess.run(
        ["claude", "--version"],
        capture_output=True,
        text=True,
        timeout=5
    )
    print(f"✓ Claude CLI 找到")
    print(f"  Exit code: {result.returncode}")
    print(f"  Stdout: {result.stdout[:200]}")
    print(f"  Stderr: {result.stderr[:200]}")

except FileNotFoundError:
    print("❌ Claude CLI 未找到")
    print("请确保 Claude CLI 已安装并在 PATH 中")
    sys.exit(1)

except subprocess.TimeoutExpired:
    print("⚠️  Claude CLI 超时")
    sys.exit(1)

print("\n" + "=" * 50)

# 测试 2: 测试 claude -p 模式
print("\n测试 claude -p 模式...")
try:
    result = subprocess.run(
        ["claude", "-p", "--output-format", "text"],
        input="Hello, are you working?",
        capture_output=True,
        text=True,
        timeout=30
    )
    print(f"  Exit code: {result.returncode}")
    print(f"  Stdout length: {len(result.stdout)}")
    print(f"  Stdout preview: {result.stdout[:200]}")
    if result.stderr:
        print(f"  Stderr: {result.stderr[:200]}")

except Exception as e:
    print(f"❌ 测试失败: {e}")
    sys.exit(1)

print("\n✅ 所有测试完成")
