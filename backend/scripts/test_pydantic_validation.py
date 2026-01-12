"""
测试 Pydantic 模型验证
"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.services.dashboard.ceo_dashboard_service import CEODashboardService
from backend.core.db import get_db
from backend.schemas.dashboard.ceo import CEOOverviewResponse

def test_validation():
    db = next(get_db())
    service = CEODashboardService(db)
    
    print("=" * 60)
    print("测试 Pydantic 模型验证")
    print("=" * 60)
    
    try:
        data = service.get_overview('2026-01')
        print("✅ Service.get_overview() 成功")
        print(f"   数据键: {list(data.keys())}")
        
        # 检查 profit_rate_pct
        profit_rate_pct = data.get('profit_summary', {}).get('profit_rate_pct')
        print(f"   profit_rate_pct: {profit_rate_pct} (type: {type(profit_rate_pct)})")
        
        # 测试 Pydantic 验证
        print("\n测试 Pydantic 验证...")
        try:
            validated = CEOOverviewResponse(**data)
            print("✅ Pydantic 验证通过")
            print(f"   验证后的数据键: {list(validated.model_dump().keys())}")
        except Exception as e:
            print(f"❌ Pydantic 验证失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Service.get_overview() 失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_validation()

