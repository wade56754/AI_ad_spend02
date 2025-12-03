#!/usr/bin/env python
"""Test script to verify agent_platform imports work correctly."""

import sys


def test_core_imports():
    """Test 1: Core imports"""
    print("Test 1: Core imports...")
    try:
        from agent_platform.core import (
            AgentProtocol,
            AgentContext,
            register_agent,
            create_agent,
        )
        from agent_platform.core import AgentRun, AgentRunStep, RunStatus
        from agent_platform.core import OrchestratorBase
        from agent_platform.core import AgentRegistry, AgentMeta
        from agent_platform.core.exceptions import (
            AgentPlatformError,
            AgentNotFoundError,
        )
        print("  OK: Core imports successful")
        return True
    except Exception as e:
        print(f"  FAILED: {e}")
        return False


def test_llm_imports():
    """Test 2: LLM imports"""
    print("Test 2: LLM imports...")
    try:
        from agent_platform.llm import LLMClient, LLMResponse, get_llm_client
        from agent_platform.llm.base import DummyLLMClient
        print("  OK: LLM imports successful")
        return True
    except Exception as e:
        print(f"  FAILED: {e}")
        return False


def test_tools_imports():
    """Test 3: Tools imports"""
    print("Test 3: Tools imports...")
    try:
        from agent_platform.tools import AgentResponse, SkillResult
        from agent_platform.tools import read_files, write_files, WritePreview
        from agent_platform.tools import validate_task_and_files
        print("  OK: Tools imports successful")
        return True
    except Exception as e:
        print(f"  FAILED: {e}")
        return False


def test_plugin_imports():
    """Test 4: Plugin imports"""
    print("Test 4: Plugin imports...")
    try:
        from agents.plugin import DemoAgent, register_demo, register_all
        print("  OK: Plugin imports successful")
        return True
    except Exception as e:
        print(f"  FAILED: {e}")
        return False


def test_demo_agent():
    """Test 5: Demo Agent functionality"""
    print("Test 5: Demo Agent functionality...")
    try:
        from agents.plugin import DemoAgent

        demo = DemoAgent()
        result = demo.handle_request({"test": "hello"})
        assert result["success"] is True, "success should be True"
        assert result["data"]["echo"] == {"test": "hello"}, "echo mismatch"
        print("  OK: Demo Agent works correctly")
        return True
    except Exception as e:
        print(f"  FAILED: {e}")
        return False


def test_registry():
    """Test 6: Registry functionality"""
    print("Test 6: Registry functionality...")
    try:
        from agent_platform.core import AgentRegistry
        from agents.plugin import register_demo

        AgentRegistry.reset()  # Clean slate
        register_demo()
        registry = AgentRegistry.instance()
        assert registry.has("demo"), "demo should be registered"
        agent = registry.create("demo")
        result = agent.handle_request({"foo": "bar"})
        assert result["success"] is True, "success should be True"
        print("  OK: Registry works correctly")
        return True
    except Exception as e:
        print(f"  FAILED: {e}")
        return False


def test_dummy_llm():
    """Test 7: LLM Dummy client"""
    print("Test 7: LLM Dummy client...")
    try:
        from agent_platform.llm.base import DummyLLMClient

        dummy = DummyLLMClient(raise_on_call=False)
        resp = dummy.generate("system", "user")
        assert resp.model == "dummy", "model should be dummy"
        print("  OK: DummyLLMClient works correctly")
        return True
    except Exception as e:
        print(f"  FAILED: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Agent Platform Import Tests")
    print("=" * 60)
    print()

    results = [
        test_core_imports(),
        test_llm_imports(),
        test_tools_imports(),
        test_plugin_imports(),
        test_demo_agent(),
        test_registry(),
        test_dummy_llm(),
    ]

    print()
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    if passed == total:
        print(f"All {total} tests passed!")
        return 0
    else:
        print(f"FAILED: {total - passed}/{total} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
