"""
Test script for MCP Mode Phase 3.2 fixes
"""
import sys
import os

# Test P0-01 fix: agents.tools.llm_client now re-exports from agent_platform
print("=" * 60)
print("MCP Mode Phase 3.2 Fix Verification")
print("=" * 60)

# Test 1: Verify re-export
print("\nTest 1: Verify re-export pattern")
from agents.tools.llm_client import get_llm_client as llm1
from agent_platform.llm import get_llm_client as llm2
result1 = llm1 is llm2
print(f"  agents.tools.llm_client.get_llm_client is agent_platform.llm.get_llm_client: {result1}")
assert result1, "P0-01 FIX FAILED: Functions are not the same!"
print("  ✅ P0-01 fix verified: re-export works correctly")

# Test 2: Verify MCP mode check is enforced
print("\nTest 2: Verify MCP mode blocks LLM client creation")
os.environ['AGENT_PLATFORM_MODE'] = 'mcp'

# Reset the client singleton
from agent_platform.llm import reset_client
reset_client()

try:
    from agent_platform.llm import get_llm_client
    client = get_llm_client()
    print("  ❌ FAILED - should have raised exception")
    assert False
except Exception as e:
    mcp_check = 'MCP' in str(e) or '工具模式' in str(e)
    print(f"  Exception raised: {str(e)[:80]}...")
    print(f"  MCP mode check works: {mcp_check}")
    assert mcp_check, "P0-01 FIX FAILED: MCP mode check not working!"
    print("  ✅ P0-01 fix verified: MCP mode blocks LLM creation")

# Test 3: is_mcp_mode() real-time check (P1-01 fix)
print("\nTest 3: Verify is_mcp_mode() reads env var in real-time")
from agent_platform.llm.factory import is_mcp_mode

os.environ['AGENT_PLATFORM_MODE'] = 'cli'
result3a = is_mcp_mode() == False
print(f"  After setting to 'cli': is_mcp_mode() == False: {result3a}")

os.environ['AGENT_PLATFORM_MODE'] = 'mcp'
result3b = is_mcp_mode() == True
print(f"  After setting to 'mcp': is_mcp_mode() == True: {result3b}")

assert result3a and result3b, "P1-01 FIX FAILED: is_mcp_mode() not reading env var in real-time!"
print("  ✅ P1-01 fix verified: is_mcp_mode() reads env var in real-time")

# Test 4: Path security - UNC path rejection (P1-02 fix)
print("\nTest 4: Verify UNC path rejection")
os.environ['AGENT_PLATFORM_MODE'] = 'cli'  # Reset for this test
from agent_platform.mcp.server import validate_path_security

unc_paths = ['\\\\server\\share\\file.txt', '//server/share/file.txt']
for unc_path in unc_paths:
    try:
        validate_path_security(unc_path)
        print(f"  ❌ FAILED - UNC path '{unc_path}' was not rejected")
        assert False
    except ValueError as e:
        if 'UNC' in str(e):
            print(f"  UNC path '{unc_path}' correctly rejected")
        else:
            print(f"  ❌ Wrong error for '{unc_path}': {e}")
            assert False

print("  ✅ P1-02 fix verified: UNC paths are rejected")

print("\n" + "=" * 60)
print("All MCP Mode Phase 3.2 fixes verified successfully!")
print("=" * 60)
