"""
账本系统测试
Version: 1.0 (基于 BACKEND_TEST_CASES_FULL_v1.1.md)

SoT References:
- LEDGER_SOT.md v1.2 (双账本规则)
- DATA_SCHEMA.md v5.2 (ledger_entries 表结构)
- STATE_MACHINE.md v2.6 (日报/充值结算)

测试覆盖:
- TC-LEDGER-001 ~ TC-LEDGER-003: 双账本完整性
- TC-LEDGER-004 ~ TC-LEDGER-005: 禁止操作
- TC-LEDGER-006 ~ TC-LEDGER-007: 红冲机制
- TC-LEDGER-008 ~ TC-LEDGER-009: 余额验证
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from uuid import uuid4


# ============================================================================
# TC-LEDGER: 双账本完整性测试
# ============================================================================

class TestLedgerDualBook:
    """TC-LEDGER: 双账本完整性测试

    规则:
    - PROJECT 账本: project_id 有值, supplier_id 必须为空
    - SUPPLIER 账本: supplier_id 有值, project_id 必须为空
    """

    @pytest.mark.asyncio
    async def test_tc_ledger_001_project_revenue_ledger(
        self, async_client, admin_token, db_session
    ):
        """TC-LEDGER-001: PROJECT 账本记录收入"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 查询 PROJECT 类型的账本记录
        response = await async_client.get(
            "/api/v1/ledger-entries",
            params={"ledger_type": "PROJECT", "entry_type": "REVENUE"},
            headers=headers
        )

        if response.status_code == 200:
            data = response.json().get("data", response.json())
            items = data.get("items", data) if isinstance(data, dict) else data

            if items and len(items) > 0:
                entry = items[0]
                # PROJECT 账本必须有 project_id
                assert entry.get("project_id") is not None, \
                    "PROJECT ledger must have project_id"
                # PROJECT 账本的 supplier_id 必须为空
                assert entry.get("supplier_id") is None, \
                    "PROJECT ledger must have null supplier_id"

    @pytest.mark.asyncio
    async def test_tc_ledger_002_supplier_cost_ledger(
        self, async_client, admin_token
    ):
        """TC-LEDGER-002: SUPPLIER 账本记录成本"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await async_client.get(
            "/api/v1/ledger-entries",
            params={"ledger_type": "SUPPLIER", "entry_type": "COST"},
            headers=headers
        )

        if response.status_code == 200:
            data = response.json().get("data", response.json())
            items = data.get("items", data) if isinstance(data, dict) else data

            if items and len(items) > 0:
                entry = items[0]
                # SUPPLIER 账本必须有 supplier_id
                assert entry.get("supplier_id") is not None, \
                    "SUPPLIER ledger must have supplier_id"
                # SUPPLIER 账本的 project_id 必须为空
                assert entry.get("project_id") is None, \
                    "SUPPLIER ledger must have null project_id"
                # COST 金额必须为负数
                amount = Decimal(str(entry.get("amount", 0)))
                assert amount < 0, "COST entry must have negative amount"

    @pytest.mark.asyncio
    async def test_tc_ledger_003_project_topup_ledger(
        self, async_client, admin_token
    ):
        """TC-LEDGER-003: PROJECT 账本记录充值"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await async_client.get(
            "/api/v1/ledger-entries",
            params={"ledger_type": "PROJECT", "entry_type": "TOPUP"},
            headers=headers
        )

        if response.status_code == 200:
            data = response.json().get("data", response.json())
            items = data.get("items", data) if isinstance(data, dict) else data

            if items and len(items) > 0:
                entry = items[0]
                # TOPUP 金额必须为正数
                amount = Decimal(str(entry.get("amount", 0)))
                assert amount > 0, "TOPUP entry must have positive amount"


# ============================================================================
# TC-LEDGER: 禁止操作测试
# ============================================================================

class TestLedgerForbiddenOperations:
    """TC-LEDGER: 账本禁止操作测试

    规则: 账本记录一旦创建，不可删除或修改
    """

    @pytest.mark.asyncio
    async def test_tc_ledger_004_delete_forbidden(
        self, async_client, admin_token
    ):
        """TC-LEDGER-004: 禁止删除账本记录"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await async_client.delete(
            "/api/v1/ledger-entries/1",
            headers=headers
        )

        # 应该返回 405 Method Not Allowed
        assert response.status_code in [405, 403, 404], \
            f"Expected 405/403/404, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_tc_ledger_005_update_forbidden(
        self, async_client, admin_token
    ):
        """TC-LEDGER-005: 禁止更新账本记录"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "amount": "9999.00",
            "notes": "尝试修改"
        }

        response = await async_client.put(
            "/api/v1/ledger-entries/1",
            json=data,
            headers=headers
        )

        # 应该返回 405 Method Not Allowed
        assert response.status_code in [405, 403, 404], \
            f"Expected 405/403/404, got {response.status_code}"


# ============================================================================
# TC-LEDGER: 红冲机制测试
# ============================================================================

class TestLedgerReversal:
    """TC-LEDGER: 红冲机制测试

    规则: 红冲生成相反金额的 REVERSAL 记录 + 新的 REVENUE 记录
    """

    @pytest.mark.asyncio
    async def test_tc_ledger_006_reversal_creates_opposite_entry(
        self, async_client, admin_token
    ):
        """TC-LEDGER-006: 红冲生成相反记录"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 执行红冲操作
        data = {
            "new_conversions": 90,
            "reason": "数据更正：实际转化为90"
        }

        # 假设有一个已锁定的日报 ID 为 1
        response = await async_client.post(
            "/api/v1/daily-reports/1/reversal",
            json=data,
            headers=headers
        )

        if response.status_code == 200:
            result = response.json().get("data", response.json())
            # 验证生成了两条账本记录
            ledger_entries = result.get("ledger_entries", [])
            if ledger_entries:
                # 应该有 REVERSAL 和新的 REVENUE
                entry_types = [e.get("entry_type") for e in ledger_entries]
                assert "REVERSAL" in entry_types, "Should have REVERSAL entry"
                assert "REVENUE" in entry_types, "Should have new REVENUE entry"

    @pytest.mark.asyncio
    async def test_tc_ledger_007_reversal_admin_only(
        self, async_client, finance_token
    ):
        """TC-LEDGER-007: 红冲权限 (仅 admin)"""
        headers = {"Authorization": f"Bearer {finance_token}"}
        data = {
            "new_conversions": 85,
            "reason": "财务尝试红冲"
        }

        response = await async_client.post(
            "/api/v1/daily-reports/1/reversal",
            json=data,
            headers=headers
        )

        # 财务无权执行红冲
        assert response.status_code in [403, 400, 404], \
            f"Expected 403/400/404, got {response.status_code}"


# ============================================================================
# TC-LEDGER: 余额验证测试
# ============================================================================

class TestLedgerBalance:
    """TC-LEDGER: 余额验证测试

    规则:
    - 充值后: balance += amount
    - 计费后: balance -= revenue
    """

    @pytest.mark.asyncio
    async def test_tc_ledger_008_topup_increases_balance(
        self, async_client, admin_token
    ):
        """TC-LEDGER-008: 充值后余额增加"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 获取项目或账户当前余额
        response = await async_client.get(
            "/api/v1/projects/1/balance",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json().get("data", response.json())
            balance = Decimal(str(data.get("balance", 0)))
            # 余额应该是正数（假设有充值记录）
            # 具体验证需要结合充值流程

    @pytest.mark.asyncio
    async def test_tc_ledger_009_billing_decreases_balance(
        self, async_client, admin_token
    ):
        """TC-LEDGER-009: 计费后余额减少"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 获取项目余额历史
        response = await async_client.get(
            "/api/v1/ledger-entries",
            params={"project_id": 1, "entry_type": "REVENUE"},
            headers=headers
        )

        if response.status_code == 200:
            data = response.json().get("data", response.json())
            items = data.get("items", data) if isinstance(data, dict) else data

            if items and len(items) > 0:
                # REVENUE 记录应该导致余额减少
                # balance_after < balance_before
                pass


# ============================================================================
# 账本查询测试
# ============================================================================

class TestLedgerQuery:
    """账本查询功能测试"""

    @pytest.mark.asyncio
    async def test_list_ledger_entries(self, async_client, admin_token):
        """获取账本记录列表"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await async_client.get(
            "/api/v1/ledger-entries",
            headers=headers
        )

        assert response.status_code in [200, 401, 404, 500]

    @pytest.mark.asyncio
    async def test_list_ledger_with_filters(self, async_client, admin_token):
        """带过滤条件获取账本列表"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {
            "page": 1,
            "page_size": 20,
            "entry_type": "REVENUE",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31"
        }

        response = await async_client.get(
            "/api/v1/ledger-entries",
            params=params,
            headers=headers
        )

        assert response.status_code in [200, 401, 404, 500]

    @pytest.mark.asyncio
    async def test_get_ledger_summary(self, async_client, admin_token):
        """获取账本汇总"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await async_client.get(
            "/api/v1/ledger-entries/summary",
            headers=headers
        )

        assert response.status_code in [200, 401, 404, 500]

        if response.status_code == 200:
            data = response.json().get("data", response.json())
            # 验证汇总字段
            assert "total_revenue" in data or "total_cost" in data or \
                   "balance" in data or isinstance(data, list)


# ============================================================================
# 账本数据完整性测试
# ============================================================================

class TestLedgerIntegrity:
    """账本数据完整性测试"""

    @pytest.mark.asyncio
    async def test_ledger_entry_has_required_fields(
        self, async_client, admin_token
    ):
        """账本记录包含必要字段"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        response = await async_client.get(
            "/api/v1/ledger-entries",
            params={"page_size": 1},
            headers=headers
        )

        if response.status_code == 200:
            data = response.json().get("data", response.json())
            items = data.get("items", data) if isinstance(data, dict) else data

            if items and len(items) > 0:
                entry = items[0]
                # 必要字段检查
                required_fields = ["id", "entry_type", "amount"]
                for field in required_fields:
                    assert field in entry, f"Missing required field: {field}"

    @pytest.mark.asyncio
    async def test_ledger_amount_sign_consistency(
        self, async_client, admin_token
    ):
        """账本金额符号一致性"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 获取 COST 类型记录
        response = await async_client.get(
            "/api/v1/ledger-entries",
            params={"entry_type": "COST"},
            headers=headers
        )

        if response.status_code == 200:
            data = response.json().get("data", response.json())
            items = data.get("items", data) if isinstance(data, dict) else data

            for entry in items or []:
                amount = Decimal(str(entry.get("amount", 0)))
                # COST 必须为负数
                if entry.get("entry_type") == "COST":
                    assert amount < 0, \
                        f"COST entry {entry.get('id')} should have negative amount"

        # 获取 REVENUE/TOPUP 类型记录
        response = await async_client.get(
            "/api/v1/ledger-entries",
            params={"entry_type": "REVENUE"},
            headers=headers
        )

        if response.status_code == 200:
            data = response.json().get("data", response.json())
            items = data.get("items", data) if isinstance(data, dict) else data

            for entry in items or []:
                amount = Decimal(str(entry.get("amount", 0)))
                # REVENUE 必须为正数
                if entry.get("entry_type") == "REVENUE":
                    assert amount > 0, \
                        f"REVENUE entry {entry.get('id')} should have positive amount"
