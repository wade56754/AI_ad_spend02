"""
独立核心模块测试运行器
绕过 conftest.py 的依赖问题，直接测试重构后的核心模块
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_state_machine():
    """测试状态机模块"""
    print("\n" + "=" * 60)
    print("STATE MACHINE TESTS")
    print("=" * 60)

    from backend.core.state_machine import (
        DailyReportStatus, TopupStatus, TransferStatus,
        StateMachine, StateTransitionError,
        DAILY_REPORT_STATE_MACHINE, TOPUP_STATE_MACHINE, TRANSFER_STATE_MACHINE
    )

    passed = 0
    failed = 0

    # Test 1: Enum counts
    try:
        assert len(DailyReportStatus) == 8
        assert len(TopupStatus) == 7
        assert len(TransferStatus) == 5
        print("[PASS] Test 1: Enum counts correct")
        passed += 1
    except AssertionError as e:
        print(f"[FAIL] Test 1: {e}")
        failed += 1

    # Test 2: TOPUP transitions
    try:
        assert TOPUP_STATE_MACHINE.can_transition('draft', 'pending_review')
        assert TOPUP_STATE_MACHINE.can_transition('draft', 'cancelled')
        assert TOPUP_STATE_MACHINE.can_transition('pending_review', 'cancelled')
        assert not TOPUP_STATE_MACHINE.can_transition('completed', 'draft')
        print("[PASS] Test 2: TOPUP transitions correct")
        passed += 1
    except AssertionError as e:
        print(f"[FAIL] Test 2: {e}")
        failed += 1

    # Test 3: TRANSFER transitions
    try:
        assert TRANSFER_STATE_MACHINE.can_transition('draft', 'pending_approval')
        assert TRANSFER_STATE_MACHINE.can_transition('draft', 'rejected')
        assert TRANSFER_STATE_MACHINE.can_transition('pending_approval', 'approved')
        assert not TRANSFER_STATE_MACHINE.can_transition('completed', 'draft')
        print("[PASS] Test 3: TRANSFER transitions correct")
        passed += 1
    except AssertionError as e:
        print(f"[FAIL] Test 3: {e}")
        failed += 1

    # Test 4: Daily Report transitions
    try:
        assert DAILY_REPORT_STATE_MACHINE.can_transition('raw_submitted', 'trend_pending')
        assert DAILY_REPORT_STATE_MACHINE.can_transition('trend_pending', 'trend_ok')
        assert DAILY_REPORT_STATE_MACHINE.can_transition('trend_pending', 'trend_flagged')
        assert DAILY_REPORT_STATE_MACHINE.can_transition('final_confirmed', 'final_locked')
        print("[PASS] Test 4: DAILY_REPORT transitions correct")
        passed += 1
    except AssertionError as e:
        print(f"[FAIL] Test 4: {e}")
        failed += 1

    # Test 5: get_allowed_transitions
    try:
        allowed = TOPUP_STATE_MACHINE.get_allowed_transitions('pending_review')
        assert 'cancelled' in allowed
        assert 'rejected' in allowed
        print("[PASS] Test 5: get_allowed_transitions correct")
        passed += 1
    except AssertionError as e:
        print(f"[FAIL] Test 5: {e}")
        failed += 1

    # Test 6: transition() with entity
    try:
        class MockEntity:
            def __init__(self, status):
                self.status = status

        entity = MockEntity('draft')
        TOPUP_STATE_MACHINE.transition(entity, 'draft', 'pending_review', user_role='media_buyer')
        assert entity.status == 'pending_review'
        print("[PASS] Test 6: transition() updates entity status")
        passed += 1
    except Exception as e:
        print(f"[FAIL] Test 6: {e}")
        failed += 1

    # Test 7: StateTransitionError for invalid transition
    try:
        entity = MockEntity('completed')
        try:
            TOPUP_STATE_MACHINE.transition(entity, 'completed', 'draft', user_role='admin')
            print("[FAIL] Test 7: Should raise StateTransitionError")
            failed += 1
        except StateTransitionError:
            print("[PASS] Test 7: StateTransitionError raised for invalid transition")
            passed += 1
    except Exception as e:
        print(f"[FAIL] Test 7: {e}")
        failed += 1

    # Test 8: StateTransitionError for wrong role
    try:
        entity = MockEntity('draft')
        try:
            TOPUP_STATE_MACHINE.transition(entity, 'draft', 'pending_review', user_role='finance')
            print("[FAIL] Test 8: Should raise StateTransitionError for wrong role")
            failed += 1
        except StateTransitionError:
            print("[PASS] Test 8: StateTransitionError raised for wrong role")
            passed += 1
    except Exception as e:
        print(f"[FAIL] Test 8: {e}")
        failed += 1

    return passed, failed


def test_error_codes():
    """测试错误码模块"""
    print("\n" + "=" * 60)
    print("ERROR CODES TESTS")
    print("=" * 60)

    from backend.core.error_codes import ERROR_CODE_MAP, get_error_code

    passed = 0
    failed = 0

    # Test 1: ERROR_CODE_MAP count
    try:
        assert len(ERROR_CODE_MAP) >= 100
        print(f"[PASS] Test 1: ERROR_CODE_MAP has {len(ERROR_CODE_MAP)} entries")
        passed += 1
    except AssertionError as e:
        print(f"[FAIL] Test 1: {e}")
        failed += 1

    # Test 2: Sample error codes
    try:
        sample_codes = ['AUTH_001', 'BIZ_001', 'SYS_001', 'STATE_400', 'VALIDATION_001']
        for code in sample_codes:
            ec = get_error_code(code)
            assert ec is not None, f'{code} not found'
            assert ec.code == code
        print("[PASS] Test 2: Sample error codes found and match")
        passed += 1
    except AssertionError as e:
        print(f"[FAIL] Test 2: {e}")
        failed += 1

    # Test 3: Error code properties
    try:
        ec = get_error_code('STATE_400')
        assert hasattr(ec, 'code')
        assert hasattr(ec, 'status_code')
        assert hasattr(ec, 'message')
        assert ec.status_code == 400
        print("[PASS] Test 3: Error code has expected properties")
        passed += 1
    except AssertionError as e:
        print(f"[FAIL] Test 3: {e}")
        failed += 1

    # Test 4: Migrated codes exist
    try:
        migrated_codes = ['STATE_400', 'VALIDATION_001', 'VALIDATION_002', 'SYS_001']
        for code in migrated_codes:
            ec = get_error_code(code)
            assert ec is not None, f'Migrated code {code} not found'
        print("[PASS] Test 4: Migrated error codes exist")
        passed += 1
    except AssertionError as e:
        print(f"[FAIL] Test 4: {e}")
        failed += 1

    # Test 5: Category codes
    try:
        category_prefixes = ['AUTH_', 'BIZ_', 'SYS_', 'DB_', 'VALIDATION_', 'STATE_', 'TREND_', 'PROFIT_']
        for prefix in category_prefixes:
            matching = [k for k in ERROR_CODE_MAP.keys() if k.startswith(prefix)]
            assert len(matching) > 0, f'No codes for prefix {prefix}'
        print("[PASS] Test 5: All categories have error codes")
        passed += 1
    except AssertionError as e:
        print(f"[FAIL] Test 5: {e}")
        failed += 1

    # Test 6: to_dict method
    try:
        ec = get_error_code('AUTH_001')
        d = ec.to_dict()
        assert 'code' in d
        assert 'message' in d
        print("[PASS] Test 6: to_dict method works")
        passed += 1
    except Exception as e:
        print(f"[FAIL] Test 6: {e}")
        failed += 1

    return passed, failed


def test_response():
    """测试响应格式模块"""
    print("\n" + "=" * 60)
    print("RESPONSE MODULE TESTS")
    print("=" * 60)

    import json
    from datetime import datetime
    from backend.core.response import (
        success_response, error_response, paginated_response,
        StandardResponse, ResponseBuilder
    )

    passed = 0
    failed = 0

    # Test 1: success_response
    try:
        resp = success_response(data={'id': 1}, message='OK')
        body = json.loads(resp.body.decode())
        assert body['success'] == True
        assert body['data'] == {'id': 1}
        print("[PASS] Test 1: success_response works")
        passed += 1
    except Exception as e:
        print(f"[FAIL] Test 1: {e}")
        failed += 1

    # Test 2: error_response
    try:
        resp = error_response(code='BIZ_001', message='Error')
        body = json.loads(resp.body.decode())
        assert body['success'] == False
        assert body['error']['code'] == 'BIZ_001'
        print("[PASS] Test 2: error_response works")
        passed += 1
    except Exception as e:
        print(f"[FAIL] Test 2: {e}")
        failed += 1

    # Test 3: paginated_response
    try:
        resp = paginated_response(
            items=[{'id': 1}, {'id': 2}],
            total=10,
            page=1,
            page_size=2
        )
        body = json.loads(resp.body.decode())
        assert body['success'] == True
        assert len(body['data']) == 2
        assert body['meta']['pagination']['total'] == 10
        print("[PASS] Test 3: paginated_response works")
        passed += 1
    except Exception as e:
        print(f"[FAIL] Test 3: {e}")
        failed += 1

    # Test 4: ResponseBuilder.success
    try:
        resp = ResponseBuilder.success({'name': 'test'}, 'Created')
        body = json.loads(resp.body.decode())
        assert body['success'] == True
        print("[PASS] Test 4: ResponseBuilder.success works")
        passed += 1
    except Exception as e:
        print(f"[FAIL] Test 4: {e}")
        failed += 1

    # Test 5: Response envelope structure
    try:
        resp = success_response(data={'test': True})
        body = json.loads(resp.body.decode())
        assert 'success' in body
        assert 'data' in body
        assert 'timestamp' in body
        assert 'request_id' in body
        print("[PASS] Test 5: Response envelope structure correct")
        passed += 1
    except Exception as e:
        print(f"[FAIL] Test 5: {e}")
        failed += 1

    return passed, failed


def test_service_integration():
    """测试服务层状态机集成"""
    print("\n" + "=" * 60)
    print("SERVICE INTEGRATION TESTS")
    print("=" * 60)

    passed = 0
    failed = 0

    # Test 1: topup_service imports
    try:
        from backend.services.topup_service import TopupService
        assert hasattr(TopupService, '_validate_transition')
        print("[PASS] Test 1: topup_service imports with _validate_transition")
        passed += 1
    except Exception as e:
        print(f"[FAIL] Test 1: {e}")
        failed += 1

    # Test 2: transfer_service imports
    try:
        from backend.services.transfer_service import TransferService
        assert hasattr(TransferService, '_validate_transition')
        print("[PASS] Test 2: transfer_service imports with _validate_transition")
        passed += 1
    except Exception as e:
        print(f"[FAIL] Test 2: {e}")
        failed += 1

    # Test 3: daily_report_service imports
    try:
        from backend.services.daily_report_service import DailyReportService
        assert hasattr(DailyReportService, '_validate_transition')
        print("[PASS] Test 3: daily_report_service imports with _validate_transition")
        passed += 1
    except Exception as e:
        print(f"[FAIL] Test 3: {e}")
        failed += 1

    return passed, failed


def main():
    """运行所有测试"""
    print("=" * 60)
    print("BACKEND REFACTORING VERIFICATION TEST SUITE")
    print("=" * 60)
    print("Testing P0+P1 modules: state_machine, error_codes, response")
    print("Bypassing conftest.py dependencies (supabase/httpx)")

    total_passed = 0
    total_failed = 0

    # Run all test suites
    p, f = test_state_machine()
    total_passed += p
    total_failed += f

    p, f = test_error_codes()
    total_passed += p
    total_failed += f

    p, f = test_response()
    total_passed += p
    total_failed += f

    p, f = test_service_integration()
    total_passed += p
    total_failed += f

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    print(f"Success Rate: {total_passed/(total_passed+total_failed)*100:.1f}%")
    print("=" * 60)

    if total_failed == 0:
        print("\n[SUCCESS] ALL TESTS PASSED - Backend refactoring verified!")
        return 0
    else:
        print(f"\n[FAILED] {total_failed} TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
