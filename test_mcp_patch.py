"""
Quick verification script for MCP mode patches.
Run with: py test_mcp_patch.py
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_cli_mode():
    """Test default CLI mode behavior"""
    # Ensure CLI mode
    os.environ.pop("AGENT_PLATFORM_MODE", None)

    # Force reimport to pick up env change
    import importlib
    import agent_platform.llm.factory as factory

    # Reload module to reset state
    importlib.reload(factory)

    assert factory.is_mcp_mode() == False, "Should be CLI mode by default"
    assert factory.get_platform_mode() == "cli", "Default mode should be 'cli'"
    print("[PASS] CLI mode functions work correctly")


def test_mcp_mode():
    """Test MCP mode behavior"""
    # Set MCP mode
    os.environ["AGENT_PLATFORM_MODE"] = "mcp"

    # Force reimport
    import importlib
    import agent_platform.llm.factory as factory
    importlib.reload(factory)

    assert factory.is_mcp_mode() == True, "Should be MCP mode"
    assert factory.get_platform_mode() == "mcp", "Mode should be 'mcp'"

    # Test that get_llm_client raises error in MCP mode
    factory.reset_client()
    try:
        factory.get_llm_client()
        assert False, "Should have raised LLMNotConfiguredError"
    except Exception as e:
        assert "MCP" in str(e), f"Error should mention MCP: {e}"
        print(f"[PASS] MCP mode blocks LLM client: {type(e).__name__}")

    print("[PASS] MCP mode functions work correctly")

    # Cleanup
    os.environ.pop("AGENT_PLATFORM_MODE", None)


def test_types_reexport():
    """Test that types.py re-exports work"""
    from agent_platform.tools.types import AgentResponse, SkillResult
    from agents.tools.types import AgentResponse as CanonicalAgentResponse

    # Should be the same class
    assert AgentResponse is CanonicalAgentResponse, "AgentResponse should be re-exported"
    print("[PASS] types.py re-export works correctly")


def test_exception_custom_message():
    """Test LLMNotConfiguredError accepts custom message"""
    from agent_platform.core.exceptions import LLMNotConfiguredError

    # Default message
    exc1 = LLMNotConfiguredError()
    assert "ANTHROPIC_API_KEY" in str(exc1), "Default message should mention API key"

    # Custom message
    custom_msg = "Custom error message for testing"
    exc2 = LLMNotConfiguredError(custom_msg)
    assert custom_msg in str(exc2), "Should use custom message"

    print("[PASS] LLMNotConfiguredError accepts custom message")


def test_mcp_server_registry():
    """Test MCP server tool registry"""
    # Set MCP mode for server import
    os.environ["AGENT_PLATFORM_MODE"] = "mcp"

    from agent_platform.mcp.server import create_mcp_server

    registry = create_mcp_server()
    tools = registry.list_tools()

    # Check expected tools
    tool_names = [t["name"] for t in tools]
    expected_tools = [
        "ap_list_agents",
        "ap_read_sot_file",
        "ap_list_sot_files",
        "ap_read_file",
        "ap_write_file",
    ]

    for expected in expected_tools:
        assert expected in tool_names, f"Missing tool: {expected}"

    print(f"[PASS] MCP server has {len(tools)} tools registered: {tool_names}")

    # Cleanup
    os.environ.pop("AGENT_PLATFORM_MODE", None)


if __name__ == "__main__":
    print("=" * 60)
    print("MCP Patch Verification Tests")
    print("=" * 60)

    try:
        test_cli_mode()
        test_mcp_mode()
        test_types_reexport()
        test_exception_custom_message()
        test_mcp_server_registry()

        print("=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
    except AssertionError as e:
        print(f"[FAIL] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
