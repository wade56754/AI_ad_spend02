#!/usr/bin/env python
"""测试 Reports 模块导入"""
import sys
sys.path.insert(0, '.')

try:
    print("Testing reports router import...")
    from backend.routers import reports
    print(f"SUCCESS: reports router imported, router: {reports.router}")
    print(f"Router prefix: {reports.router.prefix}")
    print(f"Router tags: {reports.router.tags}")

    # 测试service导入
    print("\nTesting reports service import...")
    from backend.services.reports_service import ReportsService
    print(f"SUCCESS: ReportsService imported: {ReportsService}")

    # 测试schema导入
    print("\nTesting reports schema import...")
    from backend.schemas.reports import DashboardSummary, PerformanceReportResponse
    print(f"SUCCESS: DashboardSummary: {DashboardSummary}")
    print(f"SUCCESS: PerformanceReportResponse: {PerformanceReportResponse}")

    print("\n=== All imports successful! ===")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
