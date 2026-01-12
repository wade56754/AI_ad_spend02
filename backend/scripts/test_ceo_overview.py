"""
测试 CEO Dashboard Overview API
用于诊断 500 错误
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from backend.core.db import get_db
from backend.services.dashboard.ceo_dashboard_service import CEODashboardService
import traceback

def test_ceo_overview():
    """测试 CEO Overview 各个服务调用"""
    db: Session = next(get_db())
    service = CEODashboardService(db)
    
    period = "2026-01"
    
    print("=" * 60)
    print("测试 CEO Dashboard Overview")
    print("=" * 60)
    print(f"Period: {period}\n")
    
    # 测试各个服务
    services_to_test = [
        ("Cash Status", lambda: service.cash_service.get_cash_status(period)),
        ("Profit Summary", lambda: service.profit_service.get_profit_summary(period)),
        ("Project Balance", lambda: service.balance_service.get_all_balances(period)),
        ("Action Items", lambda: service.get_action_items(period)),
        ("Project Ranking", lambda: service.profit_service.get_project_ranking(period, limit=5)),
    ]
    
    results = {}
    
    for name, func in services_to_test:
        print(f"测试 {name}...")
        try:
            result = func()
            print(f"  ✅ {name} 成功")
            results[name] = {"status": "success", "data": result}
        except Exception as e:
            print(f"  ❌ {name} 失败: {type(e).__name__}: {e}")
            print(f"  错误详情:")
            traceback.print_exc()
            results[name] = {"status": "error", "error": str(e), "type": type(e).__name__}
        print()
    
    # 测试完整的 get_overview
    print("测试完整的 get_overview...")
    try:
        overview = service.get_overview(period)
        print("  ✅ get_overview 成功")
        print(f"  返回数据键: {list(overview.keys())}")
        results["get_overview"] = {"status": "success", "keys": list(overview.keys())}
    except Exception as e:
        print(f"  ❌ get_overview 失败: {type(e).__name__}: {e}")
        print(f"  错误详情:")
        traceback.print_exc()
        results["get_overview"] = {"status": "error", "error": str(e), "type": type(e).__name__}
    
    print("\n" + "=" * 60)
    print("测试结果摘要:")
    print("=" * 60)
    
    for name, result in results.items():
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"{status_icon} {name}: {result['status']}")
        if result["status"] == "error":
            print(f"   错误类型: {result.get('type', 'Unknown')}")
            print(f"   错误信息: {result.get('error', 'Unknown error')}")
    
    # 找出失败的服务
    failed_services = [name for name, result in results.items() if result["status"] == "error"]
    if failed_services:
        print(f"\n⚠️  失败的服务: {', '.join(failed_services)}")
        print("请检查这些服务的实现和数据库数据")
    else:
        print("\n✅ 所有服务测试通过")

if __name__ == "__main__":
    test_ceo_overview()

