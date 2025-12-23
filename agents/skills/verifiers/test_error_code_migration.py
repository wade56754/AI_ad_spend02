"""
测试错误码迁移结果
"""

import sys
import io
from pathlib import Path

# 设置 stdout 编码为 utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def test_error_code_classes():
    """测试 ErrorCode 类"""
    print("=" * 60)
    print(" 测试 ErrorCode 类 ".center(60, "="))
    print("=" * 60)
    print()

    from backend.core.error_codes import (
        ErrorCode,
        AuthErrorCodes,
        BusinessErrorCodes,
        SystemErrorCodes,
        ValidationErrorCodes,
        StateErrorCodes,
        ERROR_CODE_MAP,
        get_error_code,
    )

    # 测试 ErrorCode 实例
    ec = AuthErrorCodes.INVALID_CREDENTIALS
    assert ec.code == "AUTH_001"
    assert ec.status_code == 401
    print(f"[PASS] AuthErrorCodes.INVALID_CREDENTIALS = {ec.code}")

    # 测试 ERROR_CODE_MAP
    ec2 = ERROR_CODE_MAP.get("BIZ_002")
    assert ec2 is not None
    assert ec2.code == "BIZ_002"
    print(f"[PASS] ERROR_CODE_MAP['BIZ_002'] = {ec2.code}")

    # 测试 get_error_code
    ec3 = get_error_code("VALIDATION_001")
    assert ec3.code == "VALIDATION_001"
    print(f"[PASS] get_error_code('VALIDATION_001') = {ec3.code}")

    # 测试未知错误码回退
    ec4 = get_error_code("UNKNOWN_999")
    assert ec4.code == "SYS_001"  # 默认回退到系统内部错误
    print(f"[PASS] get_error_code('UNKNOWN_999') fallback = {ec4.code}")

    print()
    print(f"总计 {len(ERROR_CODE_MAP)} 个标准错误码已定义")
    print()

    return True


def test_exception_classes():
    """测试异常类"""
    print("=" * 60)
    print(" 测试异常类 ".center(60, "="))
    print("=" * 60)
    print()

    # 直接导入异常基类 (绕过 FastAPI 依赖)
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "custom_exceptions",
        project_root / "backend" / "exceptions" / "custom_exceptions.py"
    )
    custom_exceptions = importlib.util.module_from_spec(spec)
    sys.modules["custom_exceptions"] = custom_exceptions
    spec.loader.exec_module(custom_exceptions)

    BaseCustomException = custom_exceptions.BaseCustomException
    BusinessLogicError = custom_exceptions.BusinessLogicError
    ResourceNotFoundError = custom_exceptions.ResourceNotFoundError
    PermissionDeniedError = custom_exceptions.PermissionDeniedError
    ValidationError = custom_exceptions.ValidationError
    StateTransitionError = custom_exceptions.StateTransitionError

    from backend.core.error_codes import BusinessErrorCodes, AuthErrorCodes

    # 测试默认错误码
    ex1 = ResourceNotFoundError()
    assert ex1.error_code == "BIZ_002"
    assert ex1.status_code == 404
    print(f"[PASS] ResourceNotFoundError 默认错误码 = {ex1.error_code}")

    ex2 = PermissionDeniedError()
    assert ex2.error_code == "AUTH_500"
    assert ex2.status_code == 403
    print(f"[PASS] PermissionDeniedError 默认错误码 = {ex2.error_code}")

    ex3 = ValidationError()
    assert ex3.error_code == "VALIDATION_001"
    assert ex3.status_code == 422
    print(f"[PASS] ValidationError 默认错误码 = {ex3.error_code}")

    ex4 = StateTransitionError()
    assert ex4.error_code == "STATE_400"
    assert ex4.status_code == 400
    print(f"[PASS] StateTransitionError 默认错误码 = {ex4.error_code}")

    # 测试使用 ErrorCode 对象
    ex5 = BusinessLogicError(error=BusinessErrorCodes.INSUFFICIENT_BALANCE)
    assert ex5.error_code == "BIZ_101"
    print(f"[PASS] BusinessLogicError(error=...) = {ex5.error_code}")

    # 测试自定义消息
    ex6 = ResourceNotFoundError(message="用户不存在")
    assert ex6.message == "用户不存在"
    assert ex6.error_code == "BIZ_002"
    print(f"[PASS] ResourceNotFoundError(message=...) = {ex6.message}")

    # 测试 to_dict
    ex7 = ValidationError(message="邮箱格式错误", details={"field": "email"})
    d = ex7.to_dict()
    assert d["code"] == "VALIDATION_001"
    assert d["message"] == "邮箱格式错误"
    assert d["details"]["field"] == "email"
    print(f"[PASS] to_dict() = {d}")

    print()
    return True


def test_migration_mapping():
    """测试迁移映射"""
    print("=" * 60)
    print(" 测试迁移映射 ".center(60, "="))
    print("=" * 60)
    print()

    from backend.core.error_code_migration import (
        ERROR_CODE_MIGRATION_MAP,
        DEPRECATED_ERROR_CODES,
        migrate_error_code,
        is_standard_error_code,
    )

    # 测试迁移映射
    assert migrate_error_code("VAL_001") == "VALIDATION_001"
    print(f"[PASS] VAL_001 -> {migrate_error_code('VAL_001')}")

    assert migrate_error_code("STATE-001") == "STATE_400"
    print(f"[PASS] STATE-001 -> {migrate_error_code('STATE-001')}")

    assert migrate_error_code("BIZ_ERROR") == "BIZ_001"
    print(f"[PASS] BIZ_ERROR -> {migrate_error_code('BIZ_ERROR')}")

    assert migrate_error_code("INTERNAL_ERROR") == "SYS_001"
    print(f"[PASS] INTERNAL_ERROR -> {migrate_error_code('INTERNAL_ERROR')}")

    # 测试标准错误码检测
    assert is_standard_error_code("AUTH_001") is True
    assert is_standard_error_code("BIZ_002") is True
    assert is_standard_error_code("VALIDATION_001") is True
    assert is_standard_error_code("XXX_001") is False
    print(f"[PASS] is_standard_error_code() 检测正确")

    print()
    print(f"总计 {len(ERROR_CODE_MIGRATION_MAP)} 个迁移映射")
    print(f"总计 {len(DEPRECATED_ERROR_CODES)} 个废弃错误码")
    print()

    return True


def scan_remaining_issues():
    """扫描剩余问题"""
    print("=" * 60)
    print(" 扫描剩余非标准错误码 ".center(60, "="))
    print("=" * 60)
    print()

    import re

    backend_dir = project_root / "backend"

    # 非标准错误码模式 (排除标准码)
    # 标准: AUTH_xxx, BIZ_xxx, SYS_001-004, DB_xxx, VALIDATION_xxx,
    #       STATE_4xx, TREND_xxx, PROFIT_xxx
    non_standard_patterns = [
        r'"(VAL_\d+)"',           # 应该是 VALIDATION_xxx
        r'"(VAL-\d+)"',           # 连字符版本
        r'"(STATE_0\d+)"',        # 应该是 STATE_4xx
        r'"(STATE-0\d+)"',        # 连字符版本
        r'"(INTERNAL_\d+)"',      # 应该是 SYS_001
        r'"(INTERNAL_ERROR)"',
        r'"(BIZ_ERROR)"',         # 应该是 BIZ_xxx
        r'"(SEC_ERROR)"',         # 应该是 AUTH_xxx
        r'"(SYS_CONFIG)"',        # 应该是 SYS_001
        r'"(SYS_00[5-9])"',       # SYS只有001-004
        r'"(SYS_[1-9]\d+)"',      # SYS只有001-004
    ]

    found_issues = []

    for py_file in backend_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        # 跳过迁移映射文件和测试文件
        if "error_code_migration" in py_file.name:
            continue
        if "test_" in py_file.name or "_test" in py_file.name:
            continue

        try:
            content = py_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for pattern in non_standard_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                relative = py_file.relative_to(project_root)
                found_issues.append((str(relative), match))

    if found_issues:
        print(f"发现 {len(found_issues)} 个剩余问题:")
        for file_path, code in found_issues[:10]:
            print(f"  - {file_path}: {code}")
        if len(found_issues) > 10:
            print(f"  ... 还有 {len(found_issues) - 10} 个")
    else:
        print("[PASS] 没有发现剩余的非标准错误码!")

    print()
    return len(found_issues) == 0


if __name__ == "__main__":
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " 错误码迁移验证测试 ".center(58) + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    results = []

    results.append(("ErrorCode 类测试", test_error_code_classes()))
    results.append(("异常类测试", test_exception_classes()))
    results.append(("迁移映射测试", test_migration_mapping()))
    results.append(("剩余问题扫描", scan_remaining_issues()))

    print("=" * 60)
    print(" 测试结果汇总 ".center(60, "="))
    print("=" * 60)
    print()

    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("所有测试通过!")
    else:
        print("部分测试失败，请检查!")
