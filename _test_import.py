#!/usr/bin/env python
"""Quick import test."""
import sys
sys.path.insert(0, r'D:\git\1108\AI_ad_spend02')

try:
    from agents.agents_config import create_agent
    orch = create_agent("orch")
    print(f"SUCCESS: Created {type(orch).__name__}")

    # Test handle_request with action key (instead of flow)
    result = orch.handle_request({"action": "invalid_flow_test"})
    print(f"action key test: success={result['success']}, error contains 'Unknown flow': {'Unknown flow' in str(result.get('error', ''))}")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
