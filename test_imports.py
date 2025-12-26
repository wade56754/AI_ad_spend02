"""Test CEO Dashboard V3 imports"""
import sys
sys.path.insert(0, 'd:\\project\\AI_ad_spend02')

try:
    from backend.services.dashboard.ceo_dashboard_service import CEODashboardService
    print("[OK] CEODashboardService imported")
except Exception as e:
    print(f"[FAIL] CEODashboardService: {e}")

try:
    from backend.services.dashboard.profit_service import ProfitService
    print("[OK] ProfitService imported")
except Exception as e:
    print(f"[FAIL] ProfitService: {e}")

try:
    from backend.services.dashboard.project_balance_service import ProjectBalanceService
    print("[OK] ProjectBalanceService imported")
except Exception as e:
    print(f"[FAIL] ProjectBalanceService: {e}")

try:
    from backend.services.dashboard.cash_status_service import CashStatusService
    print("[OK] CashStatusService imported")
except Exception as e:
    print(f"[FAIL] CashStatusService: {e}")

try:
    from backend.schemas.dashboard.ceo import CEOOverviewResponse, ProfitSummaryResponse
    print("[OK] CEO Schemas imported")
except Exception as e:
    print(f"[FAIL] CEO Schemas: {e}")

try:
    from backend.routers.dashboard import router
    print("[OK] Dashboard router imported")
    # Check V3 endpoints exist
    routes = [r.path for r in router.routes]
    v3_routes = [r for r in routes if '/ceo/v3/' in r]
    print(f"[OK] Found {len(v3_routes)} V3 endpoints: {v3_routes}")
except Exception as e:
    print(f"[FAIL] Dashboard router: {e}")

print("")
print("=== All imports test complete ===")
