"""
Test script for Reconciliation Control API endpoints.

Tests the following endpoint groups:
1. Settlement Rules CRUD
2. Balance Snapshots CRUD + batch + verify
3. Reconciliation Issues CRUD + workflow actions
"""

import os
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def get_test_user_id():
    """Get a valid user ID for testing."""
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT id FROM users WHERE role IN ('admin', 'finance', 'ceo') LIMIT 1"
        ))
        row = result.fetchone()
        if row:
            return str(row[0])
    return None


def get_test_ad_account_id():
    """Get a valid ad account ID for testing."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id FROM ad_accounts LIMIT 1"))
        row = result.fetchone()
        if row:
            return row[0]
    return None


def test_settlement_rules():
    """Test Settlement Rules endpoints."""
    print("\n" + "="*60)
    print("Testing Settlement Rules API")
    print("="*60)

    from backend.services.reconciliation_control_service import SettlementRuleService
    from backend.schemas.reconciliation import SettlementRuleCreate, SettlementRuleUpdate, SettlementRuleType

    db = SessionLocal()
    user_id = get_test_user_id()

    if not user_id:
        print("ERROR: No test user found")
        return False

    try:
        from uuid import UUID
        service = SettlementRuleService(db)

        # 1. Create tiered rule
        print("\n1. Creating tiered settlement rule...")
        create_data = SettlementRuleCreate(
            name="Test Tiered Settlement Rule",
            rule_type=SettlementRuleType.TIERED,
            config={
                "tiers": [
                    {"min": 0, "max": 10000, "rate": 0.03},
                    {"min": 10000, "max": 50000, "rate": 0.025},
                    {"min": 50000, "max": None, "rate": 0.02}
                ]
            },
            effective_from=date.today()
        )
        rule = service.create(create_data, UUID(user_id))
        print(f"   Created: id={rule.id}, name={rule.name}, type={rule.rule_type}")
        rule_id = rule.id

        # 2. Get by ID
        print("\n2. Getting rule by ID...")
        fetched = service.get_by_id(rule_id)
        print(f"   Fetched: id={fetched.id}, name={fetched.name}")

        # 3. List rules
        print("\n3. Listing rules...")
        rules, total = service.list_rules(skip=0, limit=10)
        print(f"   Found {total} rules, returned {len(rules)}")

        # 4. Update rule
        print("\n4. Updating rule...")
        update_data = SettlementRuleUpdate(name="Updated Tiered Rule")
        updated = service.update(rule_id, update_data)
        print(f"   Updated name: {updated.name}")

        # 5. Soft delete
        print("\n5. Soft deleting rule...")
        deleted = service.delete(rule_id)
        print(f"   Deleted: {deleted}")

        # Verify effective_to is set
        final = service.get_by_id(rule_id)
        print(f"   effective_to: {final.effective_to}")

        # Clean up
        print("\n6. Cleaning up test rule...")
        db.execute(text(f"DELETE FROM settlement_rules WHERE id = {rule_id}"))
        db.commit()
        print("   Cleaned up")

        print("\n[PASS] Settlement Rules tests PASSED")
        return True

    except Exception as e:
        print(f"\n[FAIL] Settlement Rules tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


def test_balance_snapshots():
    """Test Balance Snapshots endpoints."""
    print("\n" + "="*60)
    print("Testing Balance Snapshots API")
    print("="*60)

    from backend.services.reconciliation_control_service import BalanceSnapshotService
    from backend.schemas.reconciliation import BalanceSnapshotCreate, BalanceSnapshotBatchCreate, BalanceSnapshotSource

    db = SessionLocal()
    user_id = get_test_user_id()
    ad_account_id = get_test_ad_account_id()

    if not user_id:
        print("ERROR: No test user found")
        return False
    if not ad_account_id:
        print("ERROR: No test ad account found")
        return False

    try:
        from uuid import UUID
        service = BalanceSnapshotService(db)

        # Use a past date to pass schema validation (future dates not allowed)
        # Use 30 days ago to avoid conflicts with existing data
        test_date = date.today() - timedelta(days=30)

        # 1. Create snapshot
        print(f"\n1. Creating balance snapshot for account {ad_account_id}...")
        create_data = BalanceSnapshotCreate(
            ad_account_id=ad_account_id,
            snapshot_date=test_date,
            balance=Decimal("10000.00"),
            deposit=Decimal("500.00"),
            source=BalanceSnapshotSource.MANUAL,
            notes="Test snapshot"
        )
        snapshot = service.create(create_data, UUID(user_id))
        print(f"   Created: id={snapshot.id}, date={snapshot.snapshot_date}, balance={snapshot.balance}")
        snapshot_id = snapshot.id

        # 2. Get by ID
        print("\n2. Getting snapshot by ID...")
        fetched = service.get_by_id(snapshot_id)
        print(f"   Fetched: id={fetched.id}, remaining={fetched.remaining_balance}")

        # 3. Get by account and date
        print("\n3. Getting snapshot by account and date...")
        by_date = service.get_by_account_date(ad_account_id, test_date)
        print(f"   Found: id={by_date.id if by_date else 'None'}")

        # 4. List snapshots
        print("\n4. Listing snapshots...")
        snapshots, total = service.list_snapshots(
            ad_account_id=ad_account_id,
            skip=0,
            limit=10
        )
        print(f"   Found {total} snapshots for account {ad_account_id}")

        # 5. Create another snapshot for next day (for conservation test)
        print("\n5. Creating second snapshot for conservation test...")
        test_date_2 = test_date + timedelta(days=1)  # 29 days ago
        create_data_2 = BalanceSnapshotCreate(
            ad_account_id=ad_account_id,
            snapshot_date=test_date_2,
            balance=Decimal("9500.00"),  # Balance decreased by 500
            deposit=Decimal("500.00"),
            source=BalanceSnapshotSource.MANUAL
        )
        snapshot2 = service.create(create_data_2, UUID(user_id))
        print(f"   Created: id={snapshot2.id}, date={snapshot2.snapshot_date}")

        # 6. Verify conservation
        print("\n6. Verifying conservation formula...")
        # Balance change: 9500 - 10000 = -500
        # Deposit change: 500 - 500 = 0
        # Expected: topup - spend = balance_delta + deposit_delta
        # If topup=100, spend=600: 100 - 600 = -500 + 0 = -500 (correct)
        is_valid, details = service.verify_conservation(
            ad_account_id=ad_account_id,
            start_date=test_date,
            end_date=test_date_2,
            topup_total=Decimal("100.00"),
            spend_total=Decimal("600.00")
        )
        print(f"   Valid: {is_valid}")
        print(f"   Details: {details}")

        # Clean up test snapshots
        print("\n7. Cleaning up test snapshots...")
        db.execute(text(f"DELETE FROM ad_account_balance_snapshots WHERE id IN ({snapshot_id}, {snapshot2.id})"))
        db.commit()
        print("   Cleaned up")

        print("\n[PASS] Balance Snapshots tests PASSED")
        return True

    except Exception as e:
        print(f"\n[FAIL] Balance Snapshots tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


def test_reconciliation_issues():
    """Test Reconciliation Issues endpoints."""
    print("\n" + "="*60)
    print("Testing Reconciliation Issues API")
    print("="*60)

    from backend.services.reconciliation_control_service import ReconciliationIssueService
    from backend.schemas.reconciliation import (
        ReconciliationIssueCreate,
        ReconciliationIssueAssign,
        ReconciliationIssueResolve,
        ReconciliationIssueType,
        ReconciliationIssueResolutionType
    )

    db = SessionLocal()
    user_id = get_test_user_id()
    ad_account_id = get_test_ad_account_id()

    if not user_id:
        print("ERROR: No test user found")
        return False

    try:
        from uuid import UUID
        service = ReconciliationIssueService(db)

        # 1. Create issue
        print("\n1. Creating reconciliation issue...")
        create_data = ReconciliationIssueCreate(
            ad_account_id=ad_account_id,
            issue_date=date.today(),
            issue_type=ReconciliationIssueType.TOPUP_MISMATCH,
            expected_amount=Decimal("1000.00"),
            actual_amount=Decimal("950.00"),
            attachments=[]
        )
        issue = service.create(create_data, UUID(user_id))
        print(f"   Created: id={issue.id}, type={issue.issue_type}, status={issue.status}")
        print(f"   Difference: {issue.difference_amount}")
        issue_id = issue.id

        # 2. Get by ID
        print("\n2. Getting issue by ID...")
        fetched = service.get_by_id(issue_id)
        print(f"   Fetched: id={fetched.id}, status={fetched.status}")

        # 3. List issues
        print("\n3. Listing issues...")
        issues, total = service.list_issues(skip=0, limit=10)
        print(f"   Found {total} issues, returned {len(issues)}")

        # 4. Get summary
        print("\n4. Getting issues summary...")
        summary = service.get_summary()
        print(f"   Total: {summary['total_issues']}")
        print(f"   Open: {summary['open_issues']}")
        print(f"   By type: {summary['issues_by_type']}")

        # 5. Assign issue (open -> assigned)
        print("\n5. Assigning issue...")
        assign_data = ReconciliationIssueAssign(
            assigned_to=user_id,
            sla_deadline=datetime.now() + timedelta(days=7)
        )
        assigned = service.assign(issue_id, assign_data, UUID(user_id))
        print(f"   Status: {assigned.status}, assigned_to: {assigned.assigned_to}")

        # 6. Start investigation (assigned -> investigating)
        print("\n6. Starting investigation...")
        investigating = service.start_investigation(issue_id, UUID(user_id))
        print(f"   Status: {investigating.status}")

        # 7. Resolve issue (investigating -> resolved)
        print("\n7. Resolving issue...")
        resolve_data = ReconciliationIssueResolve(
            resolution_type=ReconciliationIssueResolutionType.DATA_CORRECTION,
            resolution_note="Data verified and corrected",
            attachments=[]
        )
        resolved = service.resolve(issue_id, resolve_data, UUID(user_id))
        print(f"   Status: {resolved.status}, resolution: {resolved.resolution_type}")

        # 8. Close issue (resolved -> closed)
        print("\n8. Closing issue...")
        closed = service.close(issue_id, UUID(user_id))
        print(f"   Status: {closed.status}")

        # 9. Check SLA breach
        print("\n9. Checking SLA breaches...")
        breached_count = service.check_sla_breach()
        print(f"   Breached count: {breached_count}")

        # Clean up test issue
        print("\n10. Cleaning up test issue...")
        db.execute(text(f"DELETE FROM reconciliation_issues WHERE id = {issue_id}"))
        db.commit()
        print("   Cleaned up")

        print("\n[PASS] Reconciliation Issues tests PASSED")
        return True

    except Exception as e:
        print(f"\n[FAIL] Reconciliation Issues tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


def main():
    print("="*60)
    print("Reconciliation Control API Tests")
    print("="*60)
    print(f"Database: {DATABASE_URL[:50]}...")

    results = {
        "Settlement Rules": test_settlement_rules(),
        "Balance Snapshots": test_balance_snapshots(),
        "Reconciliation Issues": test_reconciliation_issues(),
    }

    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    all_passed = True
    for name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    print("="*60)
    if all_passed:
        print("All tests PASSED!")
        return 0
    else:
        print("Some tests FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
