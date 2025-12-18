"""
验证器测试脚本

测试所有验证器是否能正常运行
"""

import sys
import io
from pathlib import Path

# 设置 stdout 编码为 utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.skills.verifiers import (
    EnhancedCodeVerifier,
    VerifyContext,
    VerifierConfig,
    HallucinationDetector,
    ASTVerifier,
    SpecComplianceVerifier,
    IntegrationVerifier,
    TestVerifier,
    quick_verify,
)


def test_basic_import():
    """测试基础导入"""
    print("=" * 60)
    print("测试 1: 基础导入")
    print("=" * 60)

    print("✓ EnhancedCodeVerifier 导入成功")
    print("✓ VerifyContext 导入成功")
    print("✓ VerifierConfig 导入成功")
    print("✓ 所有验证器导入成功")
    print()
    return True


def test_good_code():
    """测试正确的代码"""
    print("=" * 60)
    print("测试 2: 验证正确的代码")
    print("=" * 60)

    good_code = '''
"""用户服务模块"""

from typing import Optional, List
from datetime import datetime


class UserService:
    """用户服务类"""

    def __init__(self):
        self.users = {}

    def create_user(self, name: str, email: str) -> dict:
        """创建用户"""
        user_id = len(self.users) + 1
        user = {
            "id": user_id,
            "name": name,
            "email": email,
            "created_at": datetime.now().isoformat(),
        }
        self.users[user_id] = user
        return user

    def get_user(self, user_id: int) -> Optional[dict]:
        """获取用户"""
        return self.users.get(user_id)
'''

    context = VerifyContext(
        project_root=project_root,
        requirement="测试用户服务",
    )

    config = VerifierConfig(
        enable_hallucination=True,
        enable_ast=True,
        enable_spec=True,
        enable_integration=True,
        enable_test=False,  # 跳过测试验证
        auto_fix=False,
    )

    verifier = EnhancedCodeVerifier(context, config)
    result = verifier.verify_file("test_service.py", good_code)

    print(f"状态: {result.status.value}")
    print(f"问题数: {len(result.issues)}")

    if result.issues:
        print("发现的问题:")
        for issue in result.issues:
            print(f"  [{issue.code}] L{issue.line}: {issue.message}")
    else:
        print("✓ 无问题")

    print()
    return result.status.value in ("passed", "fixed")


def test_syntax_error():
    """测试语法错误检测"""
    print("=" * 60)
    print("测试 3: 检测语法错误")
    print("=" * 60)

    bad_code = '''
def broken_function(
    # 缺少闭合括号

class MissingColon
    pass
'''

    verifier = ASTVerifier()
    result = verifier.verify("test_bad.py", bad_code)

    print(f"通过: {result.passed}")
    print(f"问题数: {len(result.issues)}")

    for issue in result.issues:
        print(f"  [{issue.code}] L{issue.line}: {issue.message}")

    print()
    return not result.passed  # 应该失败


def test_hallucination_detection():
    """测试幻觉检测"""
    print("=" * 60)
    print("测试 4: 检测 AI 幻觉")
    print("=" * 60)

    hallucination_code = '''
from nonexistent_package import fake_function
from backend.services.fake_service import FakeClass

def my_function():
    result = fake_function()
    return result
'''

    context = VerifyContext(
        project_root=project_root,
        requirement="测试幻觉检测",
    )

    verifier = HallucinationDetector(context)
    result = verifier.verify("test_hallucination.py", hallucination_code)

    print(f"通过: {result.passed}")
    print(f"问题数: {len(result.issues)}")

    for issue in result.issues:
        print(f"  [{issue.code}] L{issue.line}: {issue.message}")

    print()
    return len(result.issues) > 0  # 应该检测到问题


def test_sot_compliance():
    """测试 SoT 合规检测"""
    print("=" * 60)
    print("测试 5: 检测 SoT 合规问题")
    print("=" * 60)

    non_compliant_code = '''
from enum import Enum

class DailyReportStatus(str, Enum):
    """日报状态 - 使用了错误的状态值"""
    DRAFT = "draft"              # 错误: 应该是 raw_submitted
    PENDING_REVIEW = "pending_review"  # 错误: 不在 8 状态中
    APPROVED = "approved"        # 错误: 不在 8 状态中


VALID_ROLES = [
    "super_admin",    # 错误: 应该是 admin
    "accountant",     # 错误: 应该是 finance
    "operator",       # 错误: 应该是 data_operator
]


def update_balance(account, amount):
    """直接修改余额 - 违反规则"""
    account.balance += amount    # 错误: 不应直接修改 balance
    account.balance = 100        # 错误: 不应直接修改 balance
'''

    context = VerifyContext(
        project_root=project_root,
        requirement="测试 SoT 合规",
    )

    verifier = SpecComplianceVerifier(context)
    result = verifier.verify("test_sot.py", non_compliant_code)

    print(f"通过: {result.passed}")
    print(f"问题数: {len(result.issues)}")

    for issue in result.issues:
        severity_icon = "❌" if issue.severity.value == "error" else "⚠️"
        print(f"  {severity_icon} [{issue.code}] L{issue.line}: {issue.message}")
        if issue.suggestion:
            print(f"      建议: {issue.suggestion}")

    print()
    return len(result.issues) > 0


def test_integration_verifier():
    """测试集成验证"""
    print("=" * 60)
    print("测试 6: 集成验证")
    print("=" * 60)

    code_with_imports = '''
import os
import sys
from typing import List, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.core.response import success_response


class UserCreate(BaseModel):
    name: str
    email: str


app = FastAPI()


@app.post("/users")
def create_user(user: UserCreate):
    return success_response(data={"id": 1})
'''

    context = VerifyContext(
        project_root=project_root,
        requirement="测试集成验证",
    )

    verifier = IntegrationVerifier(context)
    result = verifier.verify("test_integration.py", code_with_imports)

    print(f"通过: {result.passed}")
    print(f"问题数: {len(result.issues)}")
    print(f"统计: {result.metrics}")

    for issue in result.issues:
        severity_icon = "❌" if issue.severity.value == "error" else "⚠️"
        print(f"  {severity_icon} [{issue.code}] L{issue.line}: {issue.message}")

    print()
    return True


def test_quick_verify():
    """测试快速验证函数"""
    print("=" * 60)
    print("测试 7: 快速验证函数")
    print("=" * 60)

    simple_code = '''
def hello(name: str) -> str:
    """Say hello"""
    return f"Hello, {name}!"
'''

    result = quick_verify(
        file_path="simple.py",
        content=simple_code,
        project_root=str(project_root),
    )

    print(f"通过: {result['passed']}")
    print(f"状态: {result['status']}")
    print(f"问题数: {result['issues_count']}")
    print(f"错误: {result['errors']}")
    print(f"警告: {result['warnings']}")

    print()
    return result["passed"]


def test_report_generation():
    """测试报告生成"""
    print("=" * 60)
    print("测试 8: 报告生成")
    print("=" * 60)

    code1 = '''
def valid_function():
    return 42
'''

    code2 = '''
class DailyReportStatus:
    DRAFT = "draft"  # 不合规
'''

    context = VerifyContext(
        project_root=project_root,
        requirement="测试报告生成",
    )

    config = VerifierConfig(
        enable_test=False,
        auto_fix=False,
    )

    verifier = EnhancedCodeVerifier(context, config)

    results = verifier.verify_files([
        ("valid.py", code1),
        ("invalid.py", code2),
    ])

    # 生成文本报告
    text_report = verifier.generate_report(results, format="text")
    print("文本报告预览:")
    print("-" * 40)
    # 只打印前 20 行
    lines = text_report.split("\n")[:20]
    print("\n".join(lines))
    if len(text_report.split("\n")) > 20:
        print("... (更多内容省略)")
    print("-" * 40)

    print()
    return True


def run_all_tests():
    """运行所有测试"""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " 增强版代码验证器测试套件 ".center(58) + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    tests = [
        ("基础导入", test_basic_import),
        ("正确代码验证", test_good_code),
        ("语法错误检测", test_syntax_error),
        ("幻觉检测", test_hallucination_detection),
        ("SoT 合规检测", test_sot_compliance),
        ("集成验证", test_integration_verifier),
        ("快速验证函数", test_quick_verify),
        ("报告生成", test_report_generation),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed, None))
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            print()

    # 汇总
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed_count = 0
    for name, passed, error in results:
        if passed:
            print(f"  ✅ {name}")
            passed_count += 1
        else:
            print(f"  ❌ {name}" + (f" - {error}" if error else ""))

    print()
    print(f"通过: {passed_count}/{len(results)}")
    print()

    return passed_count == len(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
