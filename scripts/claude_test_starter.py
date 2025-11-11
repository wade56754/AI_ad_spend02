#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Claude Code 测试快速启动脚本
运行: python scripts/claude_test_starter.py
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# 颜色输出
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_banner():
    """打印横幅"""
    print(f"""
{BLUE}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🤖 AI广告代投系统 - Claude Code 测试快速启动器            ║
║                                                              ║
║   使用说明:                                                  ║
║   1. 选择测试阶段                                             ║
║   2. Claude Code 会自动执行并提供实时反馈                     ║
║   3. 失败时会自动修复                                             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{RESET}
""")

def check_environment():
    """检查环境"""
    print(f"\n{YELLOW}🔍 检查测试环境...{RESET}")

    # 检查Python版本
    python_version = sys.version_info
    if python_version.major < 3 or python_version.minor < 8:
        print(f"{RED}❌ Python版本过低: {python_version.major}.{python_version.minor}")
        print(f"需要 Python 3.8+")
        return False
    print(f"✅ Python版本: {python_version.major}.{python_version.minor}")

    # 检查必要的文件
    required_files = [
        "run_tests.py",
        "requirements-test.txt",
        "tests/conftest.py"
    ]

    for file in required_files:
        if not Path(file).exists():
            print(f"{RED}❌ 缺少文件: {file}")
            return False
    print(f"✅ 测试文件检查通过")

    # 检查依赖
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pytest"],
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"{YELLOW}⚠️  pytest未安装，正在安装...{RESET}")
            subprocess.run([sys.executable, "-m", "pip", "install", "pytest"])
    except:
        pass

    return True

def run_test_stage(stage_name, command, description):
    """运行测试阶段"""
    print(f"\n{BLUE}🚀 执行阶段: {stage_name}{RESET}")
    print(f"📝 {description}")

    start_time = time.time()

    # Claude Code 会在这里提供实时反馈
    print(f"{YELLOW}🔄 正在执行: {command}{RESET}")

    try:
        # 使用 subprocess.run 以捕获输出
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )

        execution_time = time.time() - start_time

        if result.returncode == 0:
            print(f"{GREEN}✅ 测试通过！耗时: {execution_time:.1f}秒{RESET}")

            # 如果有输出，显示关键信息
            if result.stdout:
                lines = result.stdout.split('\n')[-10:]  # 最后10行
                for line in lines:
                    if 'passed' in line or 'OK' in line or '=' in line:
                        print(f"   {line}")

            return True
        else:
            print(f"{RED}❌ 测试失败！耗时: {execution_time:.1f}秒{RESET}")

            # 显示错误信息
            if result.stderr:
                print(f"{RED}错误信息:{RESET}")
                for line in result.stderr.split('\n')[-5:]:
                    if line.strip():
                        print(f"   {line}")

            print(f"\n{YELLOW}💡 请将以上错误信息发送给 Claude Code 进行修复{RESET}")
            return False

    except KeyboardInterrupt:
        print(f"\n{YELLOW}⏹️  测试被中断{RESET}")
        return False
    except Exception as e:
        print(f"{RED}❌ 执行错误: {str(e)}{RESET}")
        return False

def interactive_menu():
    """交互式菜单"""
    test_stages = {
        "1": {
            "name": "阶段1: 基础模型测试",
            "command": "python run_tests.py --type unit --file tests/test_models.py",
            "description": "验证数据库模型和字段约束"
        },
        "2": {
            "name": "阶段2: 业务逻辑测试",
            "command": "python run_tests.py --file tests/test_financial_calculations.py",
            "description": "验证财务计算和业务规则"
        },
        "3": {
            "name": "阶段3: API接口测试",
            "command": "python run_tests.py --file tests/test_api_endpoints.py",
            "description": "验证REST API功能和权限"
        },
        "4": {
            "name": "阶段4: 集成测试",
            "command": "python run_tests.py --type integration",
            "description": "验证模块间协作"
        },
        "5": {
            "name": "阶段5: 数据导入测试",
            "command": "python run_tests.py --file tests/test_data_import.py",
            "description": "验证数据导入功能"
        },
        "6": {
            "name": "阶段6: 性能测试",
            "command": "python run_tests.py --type performance",
            "description": "验证系统性能指标"
        },
        "7": {
            "name": "阶段7: 安全测试",
            "command": "python run_tests.py --type security",
            "description": "验证安全防护机制"
        },
        "8": {
            "name": "运行所有测试",
            "command": "python run_tests.py --coverage",
            "description": "执行完整测试套件并生成覆盖率报告"
        },
        "9": {
            "name": "快速冒烟测试",
            "command": "python run_tests.py --file tests/test_smoke.py",
            "description": "快速验证核心功能"
        },
        "10": {
            "name": "修复失败的测试",
            "command": "python run_tests.py --lf",
            "description": "只运行上次失败的测试"
        }
    }

    while True:
        print(f"\n{BLUE}请选择要执行的测试阶段：{RESET}")
        for key, stage in test_stages.items():
            print(f"  {key}. {stage['name']}")
            print(f"     {stage['description']}")

        print(f"\n{YELLOW}0. 退出{RESET}")

        choice = input(f"\n{BLUE}请输入选项 (0-10): {RESET}").strip()

        if choice == "0":
            print(f"\n{GREEN}👋 测试结束，再见！{RESET}")
            break

        if choice in test_stages:
            stage = test_stages[choice]
            print(f"\n{YELLOW}提示：测试失败时，请复制错误信息发送给 Claude Code{RESET}")
            success = run_test_stage(
                stage['name'],
                stage['command'],
                stage['description']
            )

            if success:
                print(f"\n{GREEN}🎉 阶段完成！可以继续选择下一个阶段{RESET}")

                # 询问是否查看报告
                if choice in ["3", "8"]:
                    view_report = input("\n是否查看测试报告？(y/n): ").lower()
                    if view_report == 'y':
                        print(f"\n{YELLOW}请使用 Claude Code 打开:{RESET}")
                        print(f"  - 覆盖率报告: htmlcov/index.html")
                        print(f"  - 测试日志: tests.log")
            else:
                retry = input("\n是否重试此阶段？(y/n): ").lower()
                if retry != 'y':
                    continue
        else:
            print(f"{RED}无效选项，请重新选择{RESET}")

def main():
    """主函数"""
    print_banner()

    # 检查环境
    if not check_environment():
        print(f"\n{RED}❌ 环境检查失败，请先解决上述问题{RESET}")
        return

    # 询问运行模式
    print(f"\n{BLUE}选择运行模式：{RESET}")
    print(f"1. 交互式菜单 - 逐步执行测试")
    print(f"2. 快速模式 - 按顺序执行所有阶段")

    mode = input(f"\n请选择 (1/2): ").strip()

    if mode == "1":
        interactive_menu()
    elif mode == "2":
        print(f"\n{YELLOW}快速模式：按顺序执行所有测试阶段{RESET}")
        print(f"如果某个阶段失败，请记录错误并使用模式1单独执行\n")

        stages = [
            ("阶段1", "python run_tests.py --type unit --file tests/test_models.py"),
            ("阶段2", "python run_tests.py --file tests/test_financial_calculations.py"),
            ("阶段3", "python run_tests.py --file tests/test_api_endpoints.py"),
            ("阶段4", "python run_tests.py --type integration"),
            ("阶段5", "python run_tests.py --file tests/test_data_import.py"),
            ("阶段6", "python run_tests.py --type performance"),
            ("阶段7", "python run_tests.py --type security")
        ]

        for name, command in stages:
            success = run_test_stage(name, command, f"执行{name}")
            if not success:
                print(f"\n{RED}⚠️  {name} 失败，请使用模式1单独调试{RESET}")
                break
    else:
        print(f"{RED}无效选择{RESET}")

if __name__ == "__main__":
    main()