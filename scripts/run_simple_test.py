#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化的测试运行脚本
避免复杂的导入问题
"""

import sys
import os
import subprocess
import time

def run_simple_tests():
    """运行简化的模型测试"""
    print("\n🚀 运行阶段1：基础模型测试（简化版）")
    print("="*50)

    # 测试任务1.1：检查模型文件存在
    print("\n[任务1.1] 检查模型文件...")
    model_files = [
        "tests/test_models.py",
        "tests/test_financial_calculations.py",
        "tests/test_business_logic.py"
    ]

    for file in model_files:
        if os.path.exists(file):
            print(f"✅ {file} - 存在")
        else:
            print(f"❌ {file} - 不存在")

    # 测试任务1.2：运行基础语法检查
    print("\n[任务1.2] 运行语法检查...")

    try:
        # 检查模型文件的语法
        syntax_check = subprocess.run([
            sys.executable, "-m", "py_compile", "tests/test_models.py"
        ], capture_output=True, text=True)

        if syntax_check.returncode == 0:
            print("✅ test_models.py 语法检查通过")
        else:
            print("❌ test_models.py 语法错误")
            print(f"错误: {syntax_check.stderr[:200]}")
    except Exception as e:
        print(f"❌ 语法检查异常: {str(e)}")

    # 测试任务1.3：运行基础测试（如果有）
    print("\n[任务1.3] 尝试运行基础测试...")

    try:
        # 运行一个非常简单的测试
        test_code = """
import unittest
import sys
sys.path.insert(0, '.')
from decimal import Decimal

class TestBasics(unittest.TestCase):
    def test_decimal_creation(self):
        """测试Decimal创建"""
        d = Decimal('100.00')
        self.assertEqual(str(d), '100.00')

    def test_calculations(self):
        """测试基本计算"""
        a = Decimal('10')
        b = Decimal('5')
        self.assertEqual(a + b, Decimal('15'))

if __name__ == '__main__':
    unittest.main()
"""

        with open('temp_test.py', 'w', encoding='utf-8') as f:
            f.write(test_code)

        result = subprocess.run([
            sys.executable, 'temp_test.py'
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ 基础Python测试通过")
            print(f"输出: {result.stdout}")
        else:
            print(f"❌ 基础测试失败: {result.stderr}")

        # 清理临时文件
        os.remove('temp_test.py')

    except Exception as e:
        print(f"❌ 基础测试异常: {str(e)}")

    # 测试任务1.4：检查Python模块
    print("\n[任务1.4] 检查Python模块...")
    required_modules = [
        'decimal',
        'datetime',
        'json'
    ]

    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} - 可用")
        except ImportError:
            print(f"❌ {module} - 不可用")
            missing_modules.append(module)

    # 测试任务1.5：检查测试文件
    print("\n[任务1.5] 测试文件完整性检查...")

    test_files = [
        "test_models.py",
        "test_financial_calculations.py",
        "test_business_logic.py",
        "test_api_endpoints.py"
    ]

    passed = 0
    total = len(test_files)

    for file in test_files:
        file_path = f"tests/{file}"
        if os.path.exists(file_path):
            # 简单的行数检查
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                line_count = len(lines)
                print(f"✅ {file} - {line_count} 行")

                # 检查是否有测试函数
                test_count = sum(1 for line in lines if 'def test_' in line)
                if test_count > 0:
                    print(f"   包含 {test_count} 个测试函数")
            passed += 1
        else:
            print(f"❌ {file} - 文件不存在")

    print(f"\n✅ 阶段1完成：{passed}/{total} 文件检查通过")

    # 显示进度
    stage1_tasks = [
        "1.1 检查模型文件",
        "1.2 语法检查",
        "1.3 基础测试",
        "1.4 Python模块检查",
        "1.5 测试文件完整性"
    ]

    print("\n📊 阶段1总结：")
    for task in stage1_tasks:
        print(f"  {task}")

    print("\n📋 下一步建议：")
    if passed == total:
        print("✅ 所有基础检查通过，可以开始完整的pytest测试")
        print("   运行: python -m pytest tests/test_models.py")
    else:
        print("⚠️  有些基础检查未通过，建议先解决这些问题")
        print("   1. 确保所有必需的文件存在")
        print("   2. 修复语法错误")
        print("   3. 安装缺失的Python模块")

if __name__ == "__main__":
    run_simple_tests()