#!/usr/bin/env python
"""测试对账模块导入"""
import sys
sys.path.insert(0, '.')

try:
    print("Testing reconciliation router import...")
    from backend.routers import reconciliation
    print(f"SUCCESS: reconciliation router imported, router: {reconciliation.router}")
    print(f"Router prefix: {reconciliation.router.prefix}")
    print(f"Router tags: {reconciliation.router.tags}")
    print("All imports successful!")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
