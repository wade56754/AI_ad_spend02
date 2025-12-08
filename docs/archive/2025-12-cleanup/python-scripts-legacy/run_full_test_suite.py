#!/usr/bin/env python3
"""
Super Review Agent - 完整测试套件 v2.3
自动测试所有 4 个模式并生成详细报告
"""
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

# 测试配置
TEST_DOC = "docs/3.dev-guides/DDD_API_ARCHITECTURE.md"
CODEX_PROMPT = ".codex/prompts/doc-reviewer-codex.txt"
SKILL_NAME = "doc-fixer-claude"
OUTPUT_DIR = Path("tmp")

# 创建输出目录
OUTPUT_DIR.mkdir(exist_ok=True)

# 测试结果
results = []

def run_test(test_name, cmd, expected_output_file=None, timeout=120):
    """
    运行单个测试

    Args:
        test_name: 测试名称
        cmd: 命令列表
        expected_output_file: 预期的输出文件路径
        timeout: 超时时间（秒）

    Returns:
        dict: 测试结果
    """
    print(f"\n{'='*60}")
    print(f"测试: {test_name}")
    print(f"{'='*60}")
    print(f"命令: {' '.join(cmd)}")
    print("-" * 60)

    result = {
        "name": test_name,
        "success": False,
        "exit_code": None,
        "stdout": "",
        "stderr": "",
        "output_file_exists": False,
        "output_file_size": 0,
        "error_message": None
    }

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )

        result["exit_code"] = proc.returncode
        result["stdout"] = proc.stdout
        result["stderr"] = proc.stderr

        # 打印输出
        if proc.stdout:
            print("STDOUT:")
            print(proc.stdout[:500])  # 只显示前 500 字符
            if len(proc.stdout) > 500:
                print(f"... (还有 {len(proc.stdout) - 500} 字符)")

        if proc.stderr:
            print("\nSTDERR:")
            print(proc.stderr[:500])
            if len(proc.stderr) > 500:
                print(f"... (还有 {len(proc.stderr) - 500} 字符)")

        # 检查输出文件
        if expected_output_file:
            output_path = Path(expected_output_file)
            if output_path.exists():
                result["output_file_exists"] = True
                result["output_file_size"] = output_path.stat().st_size
                print(f"\n✓ 输出文件已生成: {expected_output_file} ({result['output_file_size']} bytes)")
            else:
                print(f"\n✗ 输出文件未生成: {expected_output_file}")

        # 判断测试是否成功
        if proc.returncode == 0:
            if expected_output_file:
                result["success"] = result["output_file_exists"] and result["output_file_size"] > 0
            else:
                # quick-check 模式：检查 stdout 是否有关键输出
                result["success"] = "Quick Check" in proc.stdout or "P0=" in proc.stdout
        else:
            result["error_message"] = f"Exit code: {proc.returncode}"

        # 打印结果
        if result["success"]:
            print(f"\n✅ 测试通过")
        else:
            print(f"\n❌ 测试失败: {result['error_message'] or '未满足预期条件'}")

    except subprocess.TimeoutExpired:
        result["error_message"] = f"超时 (>{timeout}s)"
        print(f"\n❌ 测试失败: 超时")

    except Exception as e:
        result["error_message"] = str(e)
        print(f"\n❌ 测试失败: {e}")

    return result

def main():
    print("=" * 60)
    print("Super Review Agent - 完整测试套件 v2.3")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    print("=" * 60)

    # 测试 1: review-only
    results.append(run_test(
        "Test 1: review-only 模式",
        [
            "python", "super_review_agent.py", "review-only",
            "--doc", TEST_DOC,
            "--codex-prompt", CODEX_PROMPT,
            "--output", "tmp/test_v3_review_only.md"
        ],
        expected_output_file="tmp/test_v3_review_only.md"
    ))

    # 测试 2: fix-once
    results.append(run_test(
        "Test 2: fix-once 模式",
        [
            "python", "super_review_agent.py", "fix-once",
            "--doc", TEST_DOC,
            "--codex-prompt", CODEX_PROMPT,
            "--skill-name", SKILL_NAME,
            "--output", "tmp/test_v3_fix_once.md"
        ],
        expected_output_file="tmp/test_v3_fix_once.md",
        timeout=300
    ))

    # 测试 3: auto-polish-loop
    results.append(run_test(
        "Test 3: auto-polish-loop 模式",
        [
            "python", "super_review_agent.py", "auto-polish-loop",
            "--doc", TEST_DOC,
            "--codex-prompt", CODEX_PROMPT,
            "--skill-name", SKILL_NAME,
            "--max-rounds", "2",
            "--output", "tmp/test_v3_polished.md"
        ],
        expected_output_file="tmp/test_v3_polished.md",
        timeout=600
    ))

    # 测试 4: quick-check
    results.append(run_test(
        "Test 4: quick-check 模式",
        [
            "python", "super_review_agent.py", "quick-check",
            "--doc", TEST_DOC,
            "--codex-prompt", CODEX_PROMPT
        ],
        expected_output_file=None  # quick-check 不生成文件
    ))

    # 生成测试报告
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(1 for r in results if r["success"])
    total = len(results)

    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{i}. {result['name']}: {status}")
        if result["exit_code"] is not None:
            print(f"   Exit Code: {result['exit_code']}")
        if result["output_file_exists"]:
            print(f"   Output File: {result['output_file_size']} bytes")
        if result["error_message"]:
            print(f"   Error: {result['error_message']}")

    print("\n" + "=" * 60)
    print(f"通过率: {passed}/{total} ({passed*100//total}%)")
    print("=" * 60)

    # 生成 Markdown 报告
    report_path = OUTPUT_DIR / f"TEST_REPORT_v3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# Super Review Agent - 测试报告 v2.3\n\n")
        f.write(f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**通过率**: {passed}/{total} ({passed*100//total}%)\n\n")
        f.write("## 测试结果\n\n")
        f.write("| 测试 | 状态 | Exit Code | 输出文件 | 备注 |\n")
        f.write("|------|------|-----------|---------|------|\n")

        for result in results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            exit_code = str(result["exit_code"]) if result["exit_code"] is not None else "N/A"
            output = f"{result['output_file_size']} bytes" if result["output_file_exists"] else "N/A"
            error = result["error_message"] or "-"
            f.write(f"| {result['name']} | {status} | {exit_code} | {output} | {error} |\n")

        f.write("\n## 详细日志\n\n")
        for i, result in enumerate(results, 1):
            f.write(f"### {result['name']}\n\n")
            f.write(f"**Exit Code**: {result['exit_code']}\n\n")
            if result["stdout"]:
                f.write("**STDOUT**:\n```\n")
                f.write(result["stdout"][:1000])
                if len(result["stdout"]) > 1000:
                    f.write(f"\n... (还有 {len(result['stdout']) - 1000} 字符)")
                f.write("\n```\n\n")
            if result["stderr"]:
                f.write("**STDERR**:\n```\n")
                f.write(result["stderr"][:1000])
                if len(result["stderr"]) > 1000:
                    f.write(f"\n... (还有 {len(result['stderr']) - 1000} 字符)")
                f.write("\n```\n\n")

    print(f"\n📄 详细报告已保存至: {report_path}")

    # 返回退出码
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()
