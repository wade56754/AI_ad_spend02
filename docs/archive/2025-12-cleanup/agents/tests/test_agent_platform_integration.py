"""
Agent Platform Integration Tests

Validates Phase 2 requirements:
1. create_agent("demo") and create_agent("be") return proper Agent instances
2. DummyClient gives clear error when no LLM backend is configured
3. Registered agents implement AgentProtocol correctly
"""

import pytest
import os
from unittest.mock import patch


class TestAgentPlatformRegistry:
    """Tests for agent_platform registry integration."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from agent_platform.core.registry import AgentRegistry
        AgentRegistry.reset()
        yield
        AgentRegistry.reset()

    def test_register_and_create_demo_agent(self):
        """register_all should register demo agent, create should return instance."""
        from agents.plugin import register_all
        from agent_platform.core.registry import create_agent
        from agent_platform.core.protocol import AgentProtocol

        register_all()

        agent = create_agent("demo")
        assert agent is not None
        assert isinstance(agent, AgentProtocol)
        assert agent.name == "demo"
        assert agent.version == "1.0.0"

    def test_register_and_create_be_agent(self):
        """register_all should register be agent, create should return BEAgent."""
        from agents.plugin import register_all
        from agent_platform.core.registry import create_agent
        from agent_platform.core.protocol import AgentProtocol

        register_all()

        agent = create_agent("be")
        assert agent is not None
        assert isinstance(agent, AgentProtocol)
        assert agent.name == "be"
        assert agent.version == "1.0.0"
        assert hasattr(agent, "handle_request")

    def test_demo_agent_handle_request(self):
        """Demo agent should echo back request with metadata."""
        from agents.plugin import register_all
        from agent_platform.core.registry import create_agent
        from agent_platform.core.protocol import AgentContext

        register_all()
        agent = create_agent("demo")

        request = {"task": "test task", "data": [1, 2, 3]}
        context = AgentContext(user_id="test_user")

        result = agent.handle_request(request, context)

        assert result["success"] is True
        assert result["data"]["echo"] == request
        assert result["data"]["agent"] == "demo"
        assert result["data"]["run_id"] == context.run_id

    def test_be_agent_handle_request_validation(self):
        """BE agent should validate request and return error for invalid input."""
        from agents.plugin import register_all
        from agent_platform.core.registry import create_agent

        register_all()
        agent = create_agent("be")

        # Empty request should fail validation
        result = agent.handle_request({})

        assert result["success"] is False
        assert result["error"] is not None
        assert "task" in result["error"].lower() or "required" in result["error"].lower()

    def test_list_agents_returns_registered_agents(self):
        """list_agents should return all registered agents."""
        from agents.plugin import register_all
        from agent_platform.core.registry import list_agents, get_registry

        register_all()

        agents = list_agents()
        agent_names = [a.name for a in agents]

        assert "demo" in agent_names
        assert "be" in agent_names
        assert get_registry().count >= 2

    def test_create_agent_not_found_raises(self):
        """create_agent with unknown name should raise AgentNotFoundError."""
        from agents.plugin import register_all
        from agent_platform.core.registry import create_agent
        from agent_platform.core.exceptions import AgentNotFoundError

        register_all()

        with pytest.raises(AgentNotFoundError):
            create_agent("nonexistent_agent")


class TestLLMClientFallback:
    """Tests for LLM client fallback behavior."""

    @pytest.fixture(autouse=True)
    def reset_llm_client(self):
        """Reset LLM client before each test."""
        from agent_platform.llm import reset_client
        reset_client()
        yield
        reset_client()

    def test_dummy_client_raises_clear_error(self):
        """DummyLLMClient should raise RuntimeError with clear instructions."""
        # Ensure no API key is set
        with patch.dict(os.environ, {}, clear=True):
            # Also patch to ensure Claude Code CLI is not available
            with patch(
                "agent_platform.llm.factory._create_claude_code_client",
                side_effect=Exception("CLI not available"),
            ):
                from agent_platform.llm import reset_client, get_llm_client

                reset_client()
                client = get_llm_client(allow_dummy=True)

                # Client should be DummyLLMClient
                from agent_platform.llm.base import DummyLLMClient
                assert isinstance(client, DummyLLMClient)

                # Calling generate should raise clear error
                with pytest.raises(RuntimeError) as exc_info:
                    client.generate(system="test", user="test")

                error_message = str(exc_info.value)
                assert "ANTHROPIC_API_KEY" in error_message
                assert "Claude Code" in error_message or "claude-code" in error_message

    def test_get_llm_client_raises_when_no_dummy_allowed(self):
        """get_llm_client(allow_dummy=False) should raise when no backend available."""
        from agent_platform.llm import reset_client, get_llm_client
        from agent_platform.core.exceptions import LLMNotConfiguredError

        # Ensure no API key is set
        with patch.dict(os.environ, {}, clear=True):
            with patch(
                "agent_platform.llm.factory._create_claude_code_client",
                side_effect=Exception("CLI not available"),
            ):
                reset_client()

                with pytest.raises(LLMNotConfiguredError):
                    get_llm_client(allow_dummy=False)

    def test_get_backend_type_returns_dummy_when_no_config(self):
        """get_backend_type should return 'dummy' when no LLM is configured."""
        from agent_platform.llm import reset_client, get_llm_client, get_backend_type

        with patch.dict(os.environ, {}, clear=True):
            with patch(
                "agent_platform.llm.factory._create_claude_code_client",
                side_effect=Exception("CLI not available"),
            ):
                reset_client()
                get_llm_client(allow_dummy=True)

                assert get_backend_type() == "dummy"


class TestLLMClientMessagesAPI:
    """Tests for LLM client messages.create() compatibility layer."""

    @pytest.fixture(autouse=True)
    def reset_llm_client(self):
        """Reset LLM client before each test."""
        from agent_platform.llm import reset_client
        reset_client()
        yield
        reset_client()

    def test_messages_create_compatibility(self):
        """LLMClient.messages.create() should work for backward compatibility."""
        from agent_platform.llm.base import DummyLLMClient

        # Use DummyLLMClient with raise_on_call=False for testing
        client = DummyLLMClient(raise_on_call=False)

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            messages=[{"role": "user", "content": "Hello"}],
            system="You are helpful.",
        )

        assert response is not None
        assert hasattr(response, "text")
        assert "DummyLLMClient" in response.text

    def test_generate_text_convenience_method(self):
        """LLMClient.generate_text() should return just the text."""
        from agent_platform.llm.base import DummyLLMClient

        client = DummyLLMClient(raise_on_call=False)

        text = client.generate_text(system="test system", user="test user")

        assert isinstance(text, str)
        assert "DummyLLMClient" in text

    # ========== Phase 2.1 新增测试 ==========

    def test_messages_create_empty_messages_raises_value_error(self):
        """messages.create() with empty messages should raise ValueError."""
        from agent_platform.llm.base import DummyLLMClient

        client = DummyLLMClient(raise_on_call=False)

        with pytest.raises(ValueError, match="messages cannot be empty"):
            client.messages.create(
                model="claude-sonnet-4-20250514",
                messages=[],
            )

    def test_messages_create_no_user_message_raises_value_error(self):
        """messages.create() without user message should raise ValueError."""
        from agent_platform.llm.base import DummyLLMClient

        client = DummyLLMClient(raise_on_call=False)

        with pytest.raises(ValueError, match="role='user'"):
            client.messages.create(
                model="claude-sonnet-4-20250514",
                messages=[{"role": "system", "content": "You are helpful"}],
            )

    def test_messages_create_multi_user_raises_not_implemented(self):
        """messages.create() with multiple user messages should raise NotImplementedError."""
        from agent_platform.llm.base import DummyLLMClient

        client = DummyLLMClient(raise_on_call=False)

        with pytest.raises(NotImplementedError, match="单轮对话"):
            client.messages.create(
                model="claude-sonnet-4-20250514",
                messages=[
                    {"role": "user", "content": "First message"},
                    {"role": "user", "content": "Second message"},
                ],
            )

    def test_messages_create_with_assistant_raises_not_implemented(self):
        """messages.create() with assistant messages should raise NotImplementedError."""
        from agent_platform.llm.base import DummyLLMClient

        client = DummyLLMClient(raise_on_call=False)

        # Only 1 user message + 1 assistant message to trigger assistant check
        # (multiple user messages would trigger user count check first)
        with pytest.raises(NotImplementedError, match="assistant"):
            client.messages.create(
                model="claude-sonnet-4-20250514",
                messages=[
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"},
                ],
            )

    def test_messages_create_max_tokens_optional(self):
        """messages.create() should work without explicit max_tokens."""
        from agent_platform.llm.base import DummyLLMClient

        client = DummyLLMClient(raise_on_call=False)

        # 不传 max_tokens 应该正常工作
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            messages=[{"role": "user", "content": "Hello"}],
            # max_tokens 不传
        )

        assert response is not None
        assert hasattr(response, "text")

    def test_messages_create_explicit_max_tokens(self):
        """messages.create() should respect explicit max_tokens."""
        from agent_platform.llm.base import DummyLLMClient

        client = DummyLLMClient(raise_on_call=False)

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=1024,  # 显式传递
        )

        assert response is not None

    def test_messages_create_multimodal_content(self):
        """messages.create() should handle multimodal content blocks."""
        from agent_platform.llm.base import DummyLLMClient

        client = DummyLLMClient(raise_on_call=False)

        # 多模态内容格式
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "What is in this image?"},
                    {"type": "image", "source": {"type": "base64", "data": "..."}},
                ],
            }],
        )

        assert response is not None
        # 文本应该被正确提取
        assert "What is in this image?" in response.text or "DummyLLMClient" in response.text


class TestDummyLLMClientMocking:
    """Tests for DummyLLMClient mock_response and mock_error features (Phase 2.1)."""

    def test_dummy_client_mock_response_string(self):
        """DummyLLMClient should return mock_response when set as string."""
        from agent_platform.llm.base import DummyLLMClient

        client = DummyLLMClient(mock_response="Custom mock response")

        response = client.generate(system="test", user="test")

        assert response.text == "Custom mock response"
        assert response.model == "dummy-mock"

    def test_dummy_client_mock_response_llm_response(self):
        """DummyLLMClient should return mock_response when set as LLMResponse."""
        from agent_platform.llm.base import DummyLLMClient, LLMResponse

        custom_response = LLMResponse(
            text="Custom LLMResponse",
            model="custom-model",
            usage={"input_tokens": 100, "output_tokens": 50},
        )
        client = DummyLLMClient(mock_response=custom_response)

        response = client.generate(system="test", user="test")

        assert response.text == "Custom LLMResponse"
        assert response.model == "custom-model"
        assert response.usage["input_tokens"] == 100

    def test_dummy_client_mock_error(self):
        """DummyLLMClient should raise mock_error when set."""
        from agent_platform.llm.base import DummyLLMClient

        class CustomLLMError(Exception):
            pass

        client = DummyLLMClient(mock_error=CustomLLMError("Rate limited!"))

        with pytest.raises(CustomLLMError, match="Rate limited"):
            client.generate(system="test", user="test")

    def test_dummy_client_mock_error_priority_over_response(self):
        """mock_error should take priority over mock_response."""
        from agent_platform.llm.base import DummyLLMClient

        client = DummyLLMClient(
            mock_response="This should not be returned",
            mock_error=ValueError("Error takes priority"),
        )

        with pytest.raises(ValueError, match="Error takes priority"):
            client.generate(system="test", user="test")

    def test_dummy_client_auto_disables_raise_on_call(self):
        """Setting mock_response or mock_error should auto-disable raise_on_call."""
        from agent_platform.llm.base import DummyLLMClient

        # raise_on_call=True but mock_response is set
        client = DummyLLMClient(raise_on_call=True, mock_response="Mock")

        # Should NOT raise RuntimeError, should return mock
        response = client.generate(system="test", user="test")
        assert response.text == "Mock"

    def test_dummy_client_via_messages_api_with_mock(self):
        """DummyLLMClient mock should work through messages.create() API."""
        from agent_platform.llm.base import DummyLLMClient

        client = DummyLLMClient(mock_response="Mock via messages API")

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            messages=[{"role": "user", "content": "Hello"}],
        )

        assert response.text == "Mock via messages API"


class TestExtractResponseText:
    """Tests for extract_response_text() function (Phase 2.1 improvements)."""

    def test_extract_from_string(self):
        """extract_response_text should return string as-is."""
        from agent_platform.llm import extract_response_text

        result = extract_response_text("Hello, world!")
        assert result == "Hello, world!"

    def test_extract_from_llm_response(self):
        """extract_response_text should extract from LLMResponse."""
        from agent_platform.llm import extract_response_text
        from agent_platform.llm.base import LLMResponse

        response = LLMResponse(text="Response text", model="test")
        result = extract_response_text(response)
        assert result == "Response text"

    def test_extract_from_duck_typed_object(self):
        """extract_response_text should handle duck-typed objects with .text."""
        from agent_platform.llm import extract_response_text

        class DuckTypedResponse:
            text = "Duck typed text"

        result = extract_response_text(DuckTypedResponse())
        assert result == "Duck typed text"

    def test_extract_from_none_raises_type_error(self):
        """extract_response_text should raise TypeError for None."""
        from agent_platform.llm import extract_response_text

        with pytest.raises(TypeError, match="received None"):
            extract_response_text(None)

    def test_extract_from_unknown_type_raises_type_error(self):
        """extract_response_text should raise TypeError for unknown types."""
        from agent_platform.llm import extract_response_text

        with pytest.raises(TypeError, match="cannot extract text"):
            extract_response_text(12345)  # int has no text attribute

    def test_extract_from_dict_raises_type_error(self):
        """extract_response_text should raise TypeError for dict without .text."""
        from agent_platform.llm import extract_response_text

        with pytest.raises(TypeError, match="cannot extract text"):
            extract_response_text({"text": "value"})  # dict, not object

    def test_extract_from_anthropic_like_response(self):
        """extract_response_text should handle Anthropic-like response objects."""
        from agent_platform.llm import extract_response_text

        # Simulate Anthropic response structure
        class TextBlock:
            type = "text"
            text = "Block 1 text"

        class TextBlock2:
            type = "text"
            text = " Block 2 text"

        class AnthropicResponse:
            content = [TextBlock(), TextBlock2()]

        result = extract_response_text(AnthropicResponse())
        assert result == "Block 1 text Block 2 text"


class TestBEAgentProtocolCompliance:
    """Tests for BEAgent AgentProtocol compliance."""

    def test_be_agent_implements_protocol(self):
        """BEAgent should properly implement AgentProtocol."""
        from agents.agent_core.be_agent import BEAgent
        from agent_platform.core.protocol import AgentProtocol

        agent = BEAgent()

        # Check inheritance
        assert isinstance(agent, AgentProtocol)

        # Check required properties
        assert agent.name == "be"
        assert isinstance(agent.description, str)
        assert len(agent.description) > 0
        assert agent.version == "1.0.0"

        # Check handle_request accepts context
        import inspect
        sig = inspect.signature(agent.handle_request)
        params = list(sig.parameters.keys())
        assert "request" in params
        assert "context" in params

    def test_be_agent_repr(self):
        """BEAgent should have readable repr."""
        from agents.agent_core.be_agent import BEAgent

        agent = BEAgent()
        repr_str = repr(agent)

        assert "BEAgent" in repr_str
        assert "be" in repr_str


# ============================================================
# Phase 2.1 Agent Layer Tests
# ============================================================


class TestBEAgentResponseStructure:
    """Tests for BEAgent AgentResponse structure compliance (Phase 2.1)."""

    def test_be_agent_error_response_has_meta(self):
        """BEAgent error response should include data.meta with run_id."""
        from agents.agent_core.be_agent import BEAgent
        from agent_platform.core.protocol import AgentContext

        agent = BEAgent()
        context = AgentContext(user_id="test_user")

        # Empty request triggers validation error
        result = agent.handle_request({}, context)

        assert result["success"] is False
        assert result["error"] is not None
        # Phase 2.1: Error response should still include meta
        assert result["data"] is not None
        assert "meta" in result["data"]
        assert result["data"]["meta"]["run_id"] == context.run_id
        assert result["data"]["meta"]["agent"] == "be"
        assert result["data"]["meta"]["version"] == "1.0.0"

    def test_be_agent_auto_creates_context(self):
        """BEAgent should auto-create AgentContext if None."""
        from agents.agent_core.be_agent import BEAgent

        agent = BEAgent()

        # No context provided - should auto-create
        result = agent.handle_request({})  # Validation error expected

        assert result["success"] is False
        # Should still have meta with auto-generated run_id
        assert result["data"] is not None
        assert "meta" in result["data"]
        assert result["data"]["meta"]["run_id"] is not None
        # run_id format: uuid
        run_id = result["data"]["meta"]["run_id"]
        assert len(run_id) == 36  # UUID length with hyphens

    def test_be_agent_run_id_consistency(self):
        """BEAgent should use consistent run_id from context throughout."""
        from agents.agent_core.be_agent import BEAgent
        from agent_platform.core.protocol import AgentContext

        agent = BEAgent()
        context = AgentContext(user_id="test_user")
        expected_run_id = context.run_id

        result = agent.handle_request({"task": "", "target_files": []}, context)

        # run_id in response should match context
        assert result["data"]["meta"]["run_id"] == expected_run_id


class TestAgentContextPassthrough:
    """Tests for AgentContext run_id transparency (Phase 2.1)."""

    def test_demo_agent_preserves_run_id(self):
        """Demo agent should preserve run_id from context."""
        from agents.plugin import DemoAgent
        from agent_platform.core.protocol import AgentContext

        agent = DemoAgent()
        context = AgentContext(user_id="test_user")
        expected_run_id = context.run_id

        result = agent.handle_request({"test": "data"}, context)

        assert result["success"] is True
        assert result["data"]["run_id"] == expected_run_id

    def test_context_user_id_available(self):
        """AgentContext.user_id should be accessible."""
        from agent_platform.core.protocol import AgentContext

        context = AgentContext(user_id="user_123")

        assert context.user_id == "user_123"
        assert context.run_id is not None

    def test_context_metadata_dict(self):
        """AgentContext.metadata should accept arbitrary dict data."""
        from agent_platform.core.protocol import AgentContext

        context = AgentContext(
            user_id="user_123",
            metadata={"source": "api", "tenant_id": "tenant_456"},
        )

        assert context.metadata["source"] == "api"
        assert context.metadata["tenant_id"] == "tenant_456"


class TestRegistryErrorHandling:
    """Tests for Registry.create() error handling (Phase 2.1)."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from agent_platform.core.registry import AgentRegistry
        AgentRegistry.reset()
        yield
        AgentRegistry.reset()

    def test_create_with_wrong_kwargs_raises_registration_error(self):
        """create() with wrong kwargs should raise AgentRegistrationError."""
        from agent_platform.core.registry import register_agent, create_agent
        from agent_platform.core.exceptions import AgentRegistrationError

        # Register an agent that requires specific kwargs
        class StrictAgent:
            def __init__(self, required_param: str):
                self.required_param = required_param

            @property
            def name(self):
                return "strict"

            @property
            def description(self):
                return "Agent with required param"

            @property
            def version(self):
                return "1.0.0"

            def handle_request(self, request, context=None):
                return {"success": True, "data": None, "error": None}

        register_agent("strict", StrictAgent, description="Strict agent")

        # Call without required param should raise AgentRegistrationError
        with pytest.raises(AgentRegistrationError) as exc_info:
            create_agent("strict")  # Missing required_param

        assert "Factory instantiation failed" in str(exc_info.value)
        assert "required_param" in str(exc_info.value)

    def test_create_with_factory_exception_wrapped(self):
        """create() should wrap factory exceptions as AgentRegistrationError."""
        from agent_platform.core.registry import register_agent, create_agent
        from agent_platform.core.exceptions import AgentRegistrationError

        # Register an agent whose factory raises custom exception
        def broken_factory(**kwargs):
            raise RuntimeError("Factory is broken!")

        register_agent("broken", broken_factory, description="Broken agent")

        with pytest.raises(AgentRegistrationError) as exc_info:
            create_agent("broken")

        assert "Agent creation failed" in str(exc_info.value)
        assert "RuntimeError" in str(exc_info.value)
        assert "Factory is broken" in str(exc_info.value)

    def test_create_with_correct_kwargs_succeeds(self):
        """create() with correct kwargs should return agent instance."""
        from agent_platform.core.registry import register_agent, create_agent
        from agent_platform.core.protocol import AgentProtocol

        class ConfigurableAgent(AgentProtocol):
            def __init__(self, model: str = "default", temperature: float = 0.0):
                self.model = model
                self.temperature = temperature

            @property
            def name(self):
                return "configurable"

            @property
            def description(self):
                return "Configurable agent"

            @property
            def version(self):
                return "1.0.0"

            def handle_request(self, request, context=None):
                return {
                    "success": True,
                    "data": {"model": self.model, "temperature": self.temperature},
                    "error": None,
                }

        register_agent("configurable", ConfigurableAgent, description="Configurable")

        agent = create_agent("configurable", model="claude-3", temperature=0.5)

        assert agent.model == "claude-3"
        assert agent.temperature == 0.5


class TestPluginExportStrategy:
    """Tests for plugin.py export strategy (Phase 2.1)."""

    def test_plugin_exports_registration_functions(self):
        """plugin.py should export registration functions."""
        from agents import plugin

        assert hasattr(plugin, "register_demo")
        assert hasattr(plugin, "register_all_business_agents")
        assert hasattr(plugin, "register_all")
        assert callable(plugin.register_demo)
        assert callable(plugin.register_all)

    def test_plugin_exports_demo_agent_class(self):
        """plugin.py should export DemoAgent class directly."""
        from agents.plugin import DemoAgent

        agent = DemoAgent()
        assert agent.name == "demo"

    def test_plugin_does_not_export_be_agent(self):
        """plugin.py should NOT export BEAgent (use create_agent instead)."""
        from agents import plugin

        # BEAgent should not be in __all__ or directly accessible
        assert "BEAgent" not in plugin.__all__

    def test_create_agent_is_canonical_way(self):
        """create_agent() is the canonical way to get agent instances."""
        from agent_platform.core.registry import AgentRegistry, create_agent
        from agents.plugin import register_all

        AgentRegistry.reset()
        register_all()

        # This is the correct way to get BEAgent
        be_agent = create_agent("be")
        assert be_agent.name == "be"

        AgentRegistry.reset()


# ============================================================
# Phase 3.0A Agent Tests (FEAgent, TestAgent)
# ============================================================


class TestFEAgentProtocolCompliance:
    """Tests for FEAgent AgentProtocol compliance (Phase 3.0A)."""

    def test_fe_agent_implements_protocol(self):
        """FEAgent should properly implement AgentProtocol."""
        from agents.agent_core.fe_agent import FEAgent
        from agent_platform.core.protocol import AgentProtocol

        agent = FEAgent()

        # Check inheritance
        assert isinstance(agent, AgentProtocol)

        # Check required properties
        assert agent.name == "fe"
        assert isinstance(agent.description, str)
        assert len(agent.description) > 0
        assert agent.version == "1.0.0"

        # Check handle_request accepts context
        import inspect
        sig = inspect.signature(agent.handle_request)
        params = list(sig.parameters.keys())
        assert "request" in params
        assert "context" in params

    def test_fe_agent_handle_request_validation(self):
        """FEAgent should validate request and return error for invalid input."""
        from agents.agent_core.fe_agent import FEAgent
        from agent_platform.core.protocol import AgentContext

        agent = FEAgent()
        context = AgentContext(user_id="test_user")

        # Empty request should fail validation
        result = agent.handle_request({}, context)

        assert result["success"] is False
        assert result["error"] is not None
        # Should have meta with run_id even on error
        assert result["data"] is not None
        assert "meta" in result["data"]
        assert result["data"]["meta"]["run_id"] == context.run_id
        assert result["data"]["meta"]["agent"] == "fe"

    def test_fe_agent_uses_agent_context_run_id(self):
        """FEAgent should use run_id from AgentContext in response."""
        from agents.agent_core.fe_agent import FEAgent
        from agent_platform.core.protocol import AgentContext

        agent = FEAgent()
        context = AgentContext(user_id="test_user")
        expected_run_id = context.run_id

        # Empty task triggers validation error but still includes meta
        result = agent.handle_request({"task": "", "target_files": []}, context)

        assert result["data"]["meta"]["run_id"] == expected_run_id
        assert result["data"]["meta"]["agent"] == "fe"
        assert result["data"]["meta"]["version"] == "1.0.0"

    def test_fe_agent_auto_creates_context(self):
        """FEAgent should auto-create AgentContext if None."""
        from agents.agent_core.fe_agent import FEAgent

        agent = FEAgent()

        # No context provided - should auto-create
        result = agent.handle_request({})  # Validation error expected

        assert result["success"] is False
        # Should still have meta with auto-generated run_id
        assert result["data"] is not None
        assert "meta" in result["data"]
        run_id = result["data"]["meta"]["run_id"]
        assert run_id is not None
        assert len(run_id) == 36  # UUID length


class TestTestAgentProtocolCompliance:
    """Tests for TestAgent AgentProtocol compliance (Phase 3.0A)."""

    def test_test_agent_implements_protocol(self):
        """TestAgent should properly implement AgentProtocol."""
        from agents.agent_core.test_agent import TestAgent
        from agent_platform.core.protocol import AgentProtocol

        agent = TestAgent()

        # Check inheritance
        assert isinstance(agent, AgentProtocol)

        # Check required properties
        assert agent.name == "test"
        assert isinstance(agent.description, str)
        assert len(agent.description) > 0
        assert agent.version == "1.0.0"

    def test_test_agent_returns_agentresponse_shape(self):
        """TestAgent should return proper AgentResponse structure."""
        from agents.agent_core.test_agent import TestAgent
        from agent_platform.core.protocol import AgentContext

        agent = TestAgent()
        context = AgentContext(user_id="test_user")

        # Default mode is "db"
        result = agent.handle_request({}, context)

        # Check AgentResponse shape
        assert "success" in result
        assert "data" in result
        assert "error" in result

        # Check test-specific fields
        if result["success"]:
            assert "prompt" in result["data"]
            assert "status" in result["data"]
            assert "executed" in result["data"]
            assert result["data"]["executed"] is False  # Never auto-executes
            assert "meta" in result["data"]
            assert result["data"]["meta"]["run_id"] == context.run_id

    def test_test_agent_backend_mode(self):
        """TestAgent backend mode should generate pytest prompt."""
        from agents.agent_core.test_agent import TestAgent
        from agent_platform.core.protocol import AgentContext

        agent = TestAgent()
        context = AgentContext(user_id="test_user")

        result = agent.handle_request({
            "mode": "backend",
            "scope": "ledger",
            "level": "quick",
        }, context)

        assert result["success"] is True
        assert result["data"]["mode"] == "backend"
        assert result["data"]["scope"] == "ledger"
        assert result["data"]["level"] == "quick"
        assert result["data"]["executed"] is False
        assert "pytest" in result["data"]["prompt"].lower()
        assert result["data"]["meta"]["run_id"] == context.run_id
        assert result["data"]["meta"]["skill_used"] == "backend_test_skill"

    def test_test_agent_unsupported_mode(self):
        """TestAgent should return error for unsupported mode."""
        from agents.agent_core.test_agent import TestAgent
        from agent_platform.core.protocol import AgentContext

        agent = TestAgent()
        context = AgentContext(user_id="test_user")

        result = agent.handle_request({"mode": "invalid_mode"}, context)

        assert result["success"] is False
        assert "Unsupported" in result["error"]
        assert result["data"]["meta"]["run_id"] == context.run_id

    def test_test_agent_auto_creates_context(self):
        """TestAgent should auto-create AgentContext if None."""
        from agents.agent_core.test_agent import TestAgent

        agent = TestAgent()

        result = agent.handle_request({"mode": "backend"})

        assert result["success"] is True
        # Should have meta with auto-generated run_id
        run_id = result["data"]["meta"]["run_id"]
        assert run_id is not None
        assert len(run_id) == 36  # UUID length


class TestPhase30ARegistration:
    """Tests for Phase 3.0A agent registration."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from agent_platform.core.registry import AgentRegistry
        AgentRegistry.reset()
        yield
        AgentRegistry.reset()

    def test_register_and_create_fe_agent(self):
        """register_all should register fe agent."""
        from agents.plugin import register_all
        from agent_platform.core.registry import create_agent
        from agent_platform.core.protocol import AgentProtocol

        register_all()

        agent = create_agent("fe")
        assert agent is not None
        assert isinstance(agent, AgentProtocol)
        assert agent.name == "fe"
        assert agent.version == "1.0.0"

    def test_register_and_create_test_agent(self):
        """register_all should register test agent."""
        from agents.plugin import register_all
        from agent_platform.core.registry import create_agent
        from agent_platform.core.protocol import AgentProtocol

        register_all()

        agent = create_agent("test")
        assert agent is not None
        assert isinstance(agent, AgentProtocol)
        assert agent.name == "test"
        assert agent.version == "1.0.0"

    def test_list_agents_includes_phase30a_agents(self):
        """list_agents should include FEAgent and TestAgent."""
        from agents.plugin import register_all
        from agent_platform.core.registry import list_agents, get_registry

        register_all()

        agents = list_agents()
        agent_names = [a.name for a in agents]

        # Phase 2 agents
        assert "demo" in agent_names
        assert "be" in agent_names

        # Phase 3.0A agents
        assert "fe" in agent_names
        assert "test" in agent_names

        # Total count
        assert get_registry().count >= 4

    def test_fe_agent_via_registry_handle_request(self):
        """FEAgent obtained via registry should handle requests properly."""
        from agents.plugin import register_all
        from agent_platform.core.registry import create_agent
        from agent_platform.core.protocol import AgentContext

        register_all()

        agent = create_agent("fe")
        context = AgentContext(user_id="registry_test")

        result = agent.handle_request({}, context)

        # Validation error expected but response structure should be correct
        assert result["success"] is False
        assert result["data"]["meta"]["run_id"] == context.run_id

    def test_test_agent_via_registry_handle_request(self):
        """TestAgent obtained via registry should handle requests properly."""
        from agents.plugin import register_all
        from agent_platform.core.registry import create_agent
        from agent_platform.core.protocol import AgentContext

        register_all()

        agent = create_agent("test")
        context = AgentContext(user_id="registry_test")

        result = agent.handle_request({"mode": "backend"}, context)

        assert result["success"] is True
        assert result["data"]["meta"]["run_id"] == context.run_id
        assert result["data"]["meta"]["agent"] == "test"

    def test_orch_agent_registration(self):
        """OrchestratorAgent should be registered via register_all."""
        from agents.plugin import register_all
        from agent_platform.core.registry import create_agent, get_registry
        from agent_platform.core.protocol import AgentProtocol

        register_all()

        # Verify orch is registered
        assert get_registry().has("orch")

        # Create and verify instance
        agent = create_agent("orch")
        assert agent is not None
        assert isinstance(agent, AgentProtocol)
        assert agent.name == "orch"
        assert agent.version == "1.0.0"


# ============================================================
# Phase 3.0B OrchestratorAgent Tests
# ============================================================


class TestOrchestratorAgentProtocolCompliance:
    """Tests for OrchestratorAgent AgentProtocol compliance (Phase 3.0B)."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from agent_platform.core.registry import AgentRegistry
        AgentRegistry.reset()
        yield
        AgentRegistry.reset()

    def test_orch_agent_implements_protocol(self):
        """OrchestratorAgent should properly implement AgentProtocol."""
        from agents.agent_core.orchestrator_agent import OrchestratorAgent
        from agent_platform.core.protocol import AgentProtocol

        agent = OrchestratorAgent()

        # Check inheritance
        assert isinstance(agent, AgentProtocol)

        # Check required properties
        assert agent.name == "orch"
        assert isinstance(agent.description, str)
        assert len(agent.description) > 0
        assert agent.version == "1.0.0"

        # Check handle_request accepts context
        import inspect
        sig = inspect.signature(agent.handle_request)
        params = list(sig.parameters.keys())
        assert "request" in params
        assert "context" in params

    def test_orch_agent_repr(self):
        """OrchestratorAgent should have readable repr."""
        from agents.agent_core.orchestrator_agent import OrchestratorAgent

        agent = OrchestratorAgent()
        repr_str = repr(agent)

        assert "OrchestratorAgent" in repr_str
        assert "orch" in repr_str

    def test_orch_agent_auto_creates_context(self):
        """OrchestratorAgent should auto-create AgentContext if None."""
        from agents.agent_core.orchestrator_agent import OrchestratorAgent

        agent = OrchestratorAgent()

        # Missing flow triggers error but still includes meta
        result = agent.handle_request({})  # No context provided

        assert result["success"] is False
        assert result["data"] is not None
        assert "meta" in result["data"]
        run_id = result["data"]["meta"]["run_id"]
        assert run_id is not None
        assert len(run_id) == 36  # UUID length

    def test_orch_agent_unsupported_flow(self):
        """OrchestratorAgent should return error for unsupported flow."""
        from agents.agent_core.orchestrator_agent import OrchestratorAgent
        from agent_platform.core.protocol import AgentContext

        agent = OrchestratorAgent()
        context = AgentContext(user_id="test_user")

        result = agent.handle_request({"flow": "invalid_flow_xyz"}, context)

        assert result["success"] is False
        assert "Unsupported flow" in result["error"]
        assert result["data"]["meta"]["run_id"] == context.run_id

    def test_orch_agent_missing_flow(self):
        """OrchestratorAgent should return error when flow is missing."""
        from agents.agent_core.orchestrator_agent import OrchestratorAgent
        from agent_platform.core.protocol import AgentContext

        agent = OrchestratorAgent()
        context = AgentContext(user_id="test_user")

        result = agent.handle_request({}, context)

        assert result["success"] is False
        assert "Missing 'flow'" in result["error"]
        assert result["data"]["meta"]["run_id"] == context.run_id
        assert result["data"]["meta"]["agent"] == "orch"


class TestOrchestratorBeThenTestFlow:
    """Tests for OrchestratorAgent be_then_test flow (Phase 3.0B)."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from agent_platform.core.registry import AgentRegistry
        AgentRegistry.reset()
        yield
        AgentRegistry.reset()

    def test_be_then_test_happy_path_mocked(self):
        """
        be_then_test flow should call BEAgent then TestAgent when both succeed.

        Uses mock agents to avoid LLM dependencies.
        """
        from agents.agent_core.orchestrator_agent import OrchestratorAgent
        from agent_platform.core.protocol import AgentContext
        from unittest.mock import MagicMock, patch

        agent = OrchestratorAgent()
        context = AgentContext(user_id="test_user")
        run_id = context.run_id

        # Mock BEAgent response (success)
        mock_be_response = {
            "success": True,
            "data": {
                "changes": {"routers/test.py": "# generated code"},
                "notes": ["Generated 1 file"],
                "meta": {"run_id": run_id, "agent": "be", "version": "1.0.0"},
            },
            "error": None,
        }

        # Mock TestAgent response (success)
        mock_test_response = {
            "success": True,
            "data": {
                "prompt": "pytest backend/tests/",
                "status": "prompt_generated",
                "executed": False,
                "mode": "backend",
                "scope": "all",
                "meta": {"run_id": run_id, "agent": "test", "version": "1.0.0"},
            },
            "error": None,
        }

        # Patch the internal agents
        agent._backend_agent = MagicMock()
        agent._backend_agent.handle_request.return_value = mock_be_response
        agent._test_agent = MagicMock()
        agent._test_agent.handle_request.return_value = mock_test_response

        # Execute flow
        result = agent.handle_request({
            "flow": "be_then_test",
            "task": "Generate test API",
            "target_files": ["routers/test.py"],
            "module": "test",
        }, context)

        # Verify success
        assert result["success"] is True
        assert result["error"] is None

        # Verify response structure
        assert result["data"]["flow"] == "be_then_test"
        assert result["data"]["meta"]["run_id"] == run_id
        assert result["data"]["meta"]["called_agents"] == ["be", "test"]

        # Verify backend_result
        backend_result = result["data"]["backend_result"]
        assert backend_result["success"] is True
        assert backend_result["agent"] == "be"
        assert backend_result["files_generated"] == 1

        # Verify test_result
        test_result = result["data"]["test_result"]
        assert test_result["success"] is True
        assert test_result["agent"] == "test"
        assert test_result["mode"] == "backend"
        assert test_result["executed"] is False

        # Verify agents were called with context
        agent._backend_agent.handle_request.assert_called_once()
        agent._test_agent.handle_request.assert_called_once()

    def test_be_then_test_be_fails_skips_test(self):
        """
        be_then_test flow should skip TestAgent if BEAgent fails.
        """
        from agents.agent_core.orchestrator_agent import OrchestratorAgent
        from agent_platform.core.protocol import AgentContext
        from unittest.mock import MagicMock

        agent = OrchestratorAgent()
        context = AgentContext(user_id="test_user")
        run_id = context.run_id

        # Mock BEAgent response (failure)
        mock_be_response = {
            "success": False,
            "data": {
                "meta": {"run_id": run_id, "agent": "be", "version": "1.0.0"},
            },
            "error": "Missing task description",
        }

        agent._backend_agent = MagicMock()
        agent._backend_agent.handle_request.return_value = mock_be_response
        agent._test_agent = MagicMock()

        # Execute flow
        result = agent.handle_request({
            "flow": "be_then_test",
            "task": "",  # Empty task causes validation error
            "target_files": [],
        }, context)

        # Verify failure
        assert result["success"] is False
        assert "BEAgent failed" in result["error"]

        # Verify only BE was called (test should be skipped)
        assert result["data"]["meta"]["called_agents"] == ["be"]
        assert result["data"]["backend_result"]["success"] is False
        assert result["data"]["test_result"] is None

        # TestAgent should NOT be called
        agent._test_agent.handle_request.assert_not_called()

    def test_be_then_test_test_fails_returns_partial(self):
        """
        be_then_test flow should return partial success if TestAgent fails.
        """
        from agents.agent_core.orchestrator_agent import OrchestratorAgent
        from agent_platform.core.protocol import AgentContext
        from unittest.mock import MagicMock

        agent = OrchestratorAgent()
        context = AgentContext(user_id="test_user")
        run_id = context.run_id

        # Mock BEAgent response (success)
        mock_be_response = {
            "success": True,
            "data": {
                "changes": {"routers/test.py": "# code"},
                "notes": [],
                "meta": {"run_id": run_id, "agent": "be", "version": "1.0.0"},
            },
            "error": None,
        }

        # Mock TestAgent response (failure)
        mock_test_response = {
            "success": False,
            "data": {
                "status": "failed",
                "executed": False,
                "meta": {"run_id": run_id, "agent": "test", "version": "1.0.0"},
            },
            "error": "backend_test_skill failed",
        }

        agent._backend_agent = MagicMock()
        agent._backend_agent.handle_request.return_value = mock_be_response
        agent._test_agent = MagicMock()
        agent._test_agent.handle_request.return_value = mock_test_response

        # Execute flow
        result = agent.handle_request({
            "flow": "be_then_test",
            "task": "Generate API",
            "target_files": ["routers/test.py"],
        }, context)

        # Overall should fail because TestAgent failed
        assert result["success"] is False
        assert "TestAgent" in result["error"]

        # But both agents should have been called
        assert result["data"]["meta"]["called_agents"] == ["be", "test"]
        assert result["data"]["backend_result"]["success"] is True
        assert result["data"]["test_result"]["success"] is False

    def test_be_then_test_context_passthrough(self):
        """
        be_then_test flow should pass same context to both agents.
        """
        from agents.agent_core.orchestrator_agent import OrchestratorAgent
        from agent_platform.core.protocol import AgentContext
        from unittest.mock import MagicMock

        agent = OrchestratorAgent()
        context = AgentContext(user_id="test_user")
        expected_run_id = context.run_id

        # Track the context passed to each agent
        captured_contexts = []

        def capture_be_context(request, ctx=None):
            captured_contexts.append(("be", ctx))
            return {
                "success": True,
                "data": {
                    "changes": {},
                    "notes": [],
                    "meta": {"run_id": ctx.run_id if ctx else None, "agent": "be", "version": "1.0.0"},
                },
                "error": None,
            }

        def capture_test_context(request, ctx=None):
            captured_contexts.append(("test", ctx))
            return {
                "success": True,
                "data": {
                    "status": "prompt_generated",
                    "executed": False,
                    "meta": {"run_id": ctx.run_id if ctx else None, "agent": "test", "version": "1.0.0"},
                },
                "error": None,
            }

        agent._backend_agent = MagicMock()
        agent._backend_agent.handle_request.side_effect = capture_be_context
        agent._test_agent = MagicMock()
        agent._test_agent.handle_request.side_effect = capture_test_context

        # Execute flow
        result = agent.handle_request({
            "flow": "be_then_test",
            "task": "Test task",
            "target_files": ["test.py"],
        }, context)

        # Verify both agents received the SAME context
        assert len(captured_contexts) == 2
        assert captured_contexts[0][0] == "be"
        assert captured_contexts[1][0] == "test"

        # Both should have the same run_id
        be_ctx = captured_contexts[0][1]
        test_ctx = captured_contexts[1][1]
        assert be_ctx.run_id == expected_run_id
        assert test_ctx.run_id == expected_run_id
        assert be_ctx is test_ctx  # Same context object

        # Result meta should also have consistent run_id
        assert result["data"]["meta"]["run_id"] == expected_run_id


class TestOrchestratorAgentViaRegistry:
    """Tests for OrchestratorAgent accessed via registry (Phase 3.0B)."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from agent_platform.core.registry import AgentRegistry
        AgentRegistry.reset()
        yield
        AgentRegistry.reset()

    def test_orch_agent_via_registry(self):
        """OrchestratorAgent obtained via registry should work properly."""
        from agents.plugin import register_all
        from agent_platform.core.registry import create_agent
        from agent_platform.core.protocol import AgentContext

        register_all()

        agent = create_agent("orch")
        context = AgentContext(user_id="registry_test")

        # Test with missing flow (should return error with proper meta)
        result = agent.handle_request({}, context)

        assert result["success"] is False
        assert result["data"]["meta"]["run_id"] == context.run_id
        assert result["data"]["meta"]["agent"] == "orch"

    def test_list_agents_includes_orch(self):
        """list_agents should include OrchestratorAgent."""
        from agents.plugin import register_all
        from agent_platform.core.registry import list_agents, get_registry

        register_all()

        agents = list_agents()
        agent_names = [a.name for a in agents]

        assert "orch" in agent_names

        # Verify tags
        orch_meta = get_registry().get("orch")
        assert "orchestrator" in orch_meta.tags
        assert "multi-agent" in orch_meta.tags

    def test_orch_agent_total_count(self):
        """Registry should have at least 5 agents after Phase 3.0B."""
        from agents.plugin import register_all
        from agent_platform.core.registry import get_registry

        register_all()

        # demo, be, fe, test, orch = 5 agents
        assert get_registry().count >= 5


# ============================================================
# Phase 3.1 Observability Tests
# ============================================================


class TestLoggingUtils:
    """Tests for logging_utils module (Phase 3.1)."""

    def test_error_kind_enum_values(self):
        """ErrorKind enum should have expected values."""
        from agent_platform.core.logging_utils import ErrorKind

        assert ErrorKind.OK.value == "OK"
        assert ErrorKind.VALIDATION_ERROR.value == "VALIDATION_ERROR"
        assert ErrorKind.SOT_VIOLATION.value == "SOT_VIOLATION"
        assert ErrorKind.LLM_ERROR.value == "LLM_ERROR"
        assert ErrorKind.INFRA_ERROR.value == "INFRA_ERROR"
        assert ErrorKind.AGENT_ERROR.value == "AGENT_ERROR"
        assert ErrorKind.UNKNOWN.value == "UNKNOWN"

    def test_log_event_returns_entry(self):
        """log_event should return the generated log entry."""
        from agent_platform.core.logging_utils import log_event, ErrorKind

        entry = log_event(
            run_id="test-run-123",
            agent_name="orch",
            flow="be_then_test",
            stage="start",
            success=True,
            error_kind=ErrorKind.OK,
            message="Test message",
        )

        assert entry["run_id"] == "test-run-123"
        assert entry["agent_name"] == "orch"
        assert entry["flow"] == "be_then_test"
        assert entry["stage"] == "start"
        assert entry["success"] is True
        assert entry["error_kind"] == "OK"
        assert entry["message"] == "Test message"
        assert "timestamp" in entry

    def test_log_event_with_extra_data(self):
        """log_event should include extra data when provided."""
        from agent_platform.core.logging_utils import log_event, ErrorKind

        entry = log_event(
            run_id="test-run-456",
            agent_name="be",
            flow="backend_only",
            stage="end",
            success=True,
            error_kind=ErrorKind.OK,
            message="Completed",
            extra={"files_generated": 3, "model": "claude-3"},
        )

        assert "extra" in entry
        assert entry["extra"]["files_generated"] == 3
        assert entry["extra"]["model"] == "claude-3"

    def test_derive_error_kind_validation_error(self):
        """derive_error_kind should detect validation errors."""
        from agent_platform.core.logging_utils import derive_error_kind, ErrorKind

        # ValueError with "required" in message
        result = derive_error_kind(ValueError("required field missing"))
        assert result == ErrorKind.VALIDATION_ERROR

        # ValidationError class name
        class ValidationError(Exception):
            pass
        result = derive_error_kind(ValidationError("invalid"))
        assert result == ErrorKind.VALIDATION_ERROR

    def test_derive_error_kind_llm_error(self):
        """derive_error_kind should detect LLM errors."""
        from agent_platform.core.logging_utils import derive_error_kind, ErrorKind
        from agent_platform.core.exceptions import LLMClientError

        error = LLMClientError("API timeout")
        result = derive_error_kind(error)
        assert result == ErrorKind.LLM_ERROR

    def test_derive_error_kind_agent_error(self):
        """derive_error_kind should detect agent errors."""
        from agent_platform.core.logging_utils import derive_error_kind, ErrorKind
        from agent_platform.core.exceptions import AgentExecutionError

        error = AgentExecutionError("be", "failed to generate")
        result = derive_error_kind(error)
        assert result == ErrorKind.AGENT_ERROR

    def test_derive_error_kind_unknown(self):
        """derive_error_kind should return UNKNOWN for unrecognized errors."""
        from agent_platform.core.logging_utils import derive_error_kind, ErrorKind

        result = derive_error_kind(Exception("some random error"))
        assert result == ErrorKind.UNKNOWN

    def test_create_error_response(self):
        """create_error_response should generate proper error response."""
        from agent_platform.core.logging_utils import create_error_response, ErrorKind

        error = ValueError("missing required field")
        response = create_error_response(
            error=error,
            run_id="test-run-789",
            agent_name="orch",
            flow="be_then_test",
        )

        assert response["success"] is False
        assert response["data"] is None
        assert "missing required field" in response["error"]
        assert response["error_kind"] == ErrorKind.VALIDATION_ERROR.value


class TestOrchestratorErrorKindResponse:
    """Tests for OrchestratorAgent error_kind in responses (Phase 3.1)."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from agent_platform.core.registry import AgentRegistry
        AgentRegistry.reset()
        yield
        AgentRegistry.reset()

    def test_orch_missing_flow_returns_validation_error_kind(self):
        """OrchestratorAgent should return VALIDATION_ERROR for missing flow."""
        from agents.agent_core.orchestrator_agent import OrchestratorAgent
        from agent_platform.core.protocol import AgentContext

        agent = OrchestratorAgent()
        context = AgentContext(user_id="test_user")

        result = agent.handle_request({}, context)

        assert result["success"] is False
        assert result["error_kind"] == "VALIDATION_ERROR"

    def test_orch_unsupported_flow_returns_validation_error_kind(self):
        """OrchestratorAgent should return VALIDATION_ERROR for unsupported flow."""
        from agents.agent_core.orchestrator_agent import OrchestratorAgent
        from agent_platform.core.protocol import AgentContext

        agent = OrchestratorAgent()
        context = AgentContext(user_id="test_user")

        result = agent.handle_request({"flow": "invalid_xyz"}, context)

        assert result["success"] is False
        assert result["error_kind"] == "VALIDATION_ERROR"

    def test_orch_success_returns_ok_error_kind(self):
        """OrchestratorAgent should return OK error_kind on success."""
        from agents.agent_core.orchestrator_agent import OrchestratorAgent
        from agent_platform.core.protocol import AgentContext
        from unittest.mock import MagicMock

        agent = OrchestratorAgent()
        context = AgentContext(user_id="test_user")
        run_id = context.run_id

        # Mock successful responses
        agent._backend_agent = MagicMock()
        agent._backend_agent.handle_request.return_value = {
            "success": True,
            "data": {
                "changes": {},
                "notes": [],
                "meta": {"run_id": run_id, "agent": "be", "version": "1.0.0"},
            },
            "error": None,
        }
        agent._test_agent = MagicMock()
        agent._test_agent.handle_request.return_value = {
            "success": True,
            "data": {
                "executed": False,
                "meta": {"run_id": run_id, "agent": "test", "version": "1.0.0"},
            },
            "error": None,
        }

        result = agent.handle_request({
            "flow": "be_then_test",
            "task": "test",
            "target_files": [],
        }, context)

        assert result["success"] is True
        assert result["error_kind"] == "OK"

    def test_orch_agent_failure_returns_agent_error_kind(self):
        """OrchestratorAgent should return AGENT_ERROR when sub-agent fails."""
        from agents.agent_core.orchestrator_agent import OrchestratorAgent
        from agent_platform.core.protocol import AgentContext
        from unittest.mock import MagicMock

        agent = OrchestratorAgent()
        context = AgentContext(user_id="test_user")
        run_id = context.run_id

        # Mock BEAgent failure
        agent._backend_agent = MagicMock()
        agent._backend_agent.handle_request.return_value = {
            "success": False,
            "data": {
                "meta": {"run_id": run_id, "agent": "be", "version": "1.0.0"},
            },
            "error": "Task description required",
        }

        result = agent.handle_request({
            "flow": "be_then_test",
            "task": "",
            "target_files": [],
        }, context)

        assert result["success"] is False
        assert result["error_kind"] == "AGENT_ERROR"


class TestOrchestratorPlanExecuteMode:
    """Tests for OrchestratorAgent plan/execute mode (Phase 3.1)."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from agent_platform.core.registry import AgentRegistry
        AgentRegistry.reset()
        yield
        AgentRegistry.reset()

    def test_plan_mode_returns_plan_without_execution(self):
        """mode='plan' should return plan without executing the flow."""
        from agents.agent_core.orchestrator_agent import OrchestratorAgent
        from agent_platform.core.protocol import AgentContext
        from unittest.mock import MagicMock

        agent = OrchestratorAgent()
        context = AgentContext(user_id="test_user")

        # Mock agents to verify they are NOT called
        agent._backend_agent = MagicMock()
        agent._test_agent = MagicMock()

        result = agent.handle_request({
            "mode": "plan",
            "flow": "be_then_test",
            "task": "Generate API",
            "target_files": ["routers/api.py"],
        }, context)

        # Should succeed with plan
        assert result["success"] is True
        assert result["data"]["mode"] == "plan"
        assert result["data"]["flow"] == "be_then_test"
        assert "plan" in result["data"]
        assert result["error_kind"] == "OK"

        # Agents should NOT be called in plan mode
        agent._backend_agent.handle_request.assert_not_called()
        agent._test_agent.handle_request.assert_not_called()

    def test_plan_mode_includes_steps(self):
        """Plan mode should include detailed steps."""
        from agents.agent_core.orchestrator_agent import OrchestratorAgent
        from agent_platform.core.protocol import AgentContext

        agent = OrchestratorAgent()
        context = AgentContext(user_id="test_user")

        result = agent.handle_request({
            "mode": "plan",
            "flow": "be_then_test",
        }, context)

        plan = result["data"]["plan"]
        assert "description" in plan
        assert "steps" in plan
        assert len(plan["steps"]) >= 2  # BE + Test
        assert "estimated_agents" in plan
        assert "be" in plan["estimated_agents"]
        assert "test" in plan["estimated_agents"]

    def test_plan_mode_includes_request_context(self):
        """Plan mode should include request context."""
        from agents.agent_core.orchestrator_agent import OrchestratorAgent
        from agent_platform.core.protocol import AgentContext

        agent = OrchestratorAgent()
        context = AgentContext(user_id="test_user")

        result = agent.handle_request({
            "mode": "plan",
            "flow": "be_then_test",
            "task": "Generate user API",
            "target_files": ["routers/users.py"],
            "module": "users",
        }, context)

        plan = result["data"]["plan"]
        assert "request_context" in plan
        assert plan["request_context"]["task"] == "Generate user API"
        assert plan["request_context"]["target_files"] == ["routers/users.py"]
        assert plan["request_context"]["module"] == "users"

    def test_execute_mode_is_default(self):
        """mode='execute' (default) should actually run the flow."""
        from agents.agent_core.orchestrator_agent import OrchestratorAgent
        from agent_platform.core.protocol import AgentContext
        from unittest.mock import MagicMock

        agent = OrchestratorAgent()
        context = AgentContext(user_id="test_user")
        run_id = context.run_id

        # Mock successful execution
        agent._backend_agent = MagicMock()
        agent._backend_agent.handle_request.return_value = {
            "success": True,
            "data": {
                "changes": {},
                "notes": [],
                "meta": {"run_id": run_id, "agent": "be", "version": "1.0.0"},
            },
            "error": None,
        }
        agent._test_agent = MagicMock()
        agent._test_agent.handle_request.return_value = {
            "success": True,
            "data": {
                "executed": False,
                "meta": {"run_id": run_id, "agent": "test", "version": "1.0.0"},
            },
            "error": None,
        }

        # Default mode (no mode specified)
        result = agent.handle_request({
            "flow": "be_then_test",
            "task": "test",
            "target_files": [],
        }, context)

        # Agents SHOULD be called in execute mode
        agent._backend_agent.handle_request.assert_called_once()
        agent._test_agent.handle_request.assert_called_once()
        assert "mode" not in result["data"]  # Execute mode doesn't add mode field

    def test_explicit_execute_mode(self):
        """mode='execute' explicitly should work same as default."""
        from agents.agent_core.orchestrator_agent import OrchestratorAgent
        from agent_platform.core.protocol import AgentContext
        from unittest.mock import MagicMock

        agent = OrchestratorAgent()
        context = AgentContext(user_id="test_user")
        run_id = context.run_id

        agent._backend_agent = MagicMock()
        agent._backend_agent.handle_request.return_value = {
            "success": True,
            "data": {
                "changes": {},
                "notes": [],
                "meta": {"run_id": run_id, "agent": "be", "version": "1.0.0"},
            },
            "error": None,
        }
        agent._test_agent = MagicMock()
        agent._test_agent.handle_request.return_value = {
            "success": True,
            "data": {
                "executed": False,
                "meta": {"run_id": run_id, "agent": "test", "version": "1.0.0"},
            },
            "error": None,
        }

        result = agent.handle_request({
            "mode": "execute",
            "flow": "be_then_test",
            "task": "test",
            "target_files": [],
        }, context)

        agent._backend_agent.handle_request.assert_called_once()
        assert result["success"] is True

    def test_invalid_mode_returns_validation_error(self):
        """Invalid mode should return VALIDATION_ERROR."""
        from agents.agent_core.orchestrator_agent import OrchestratorAgent
        from agent_platform.core.protocol import AgentContext

        agent = OrchestratorAgent()
        context = AgentContext(user_id="test_user")

        result = agent.handle_request({
            "mode": "invalid_mode",
            "flow": "be_then_test",
        }, context)

        assert result["success"] is False
        assert "Invalid mode" in result["error"]
        assert result["error_kind"] == "VALIDATION_ERROR"

    def test_plan_mode_for_all_flows(self):
        """Plan mode should work for all supported flows."""
        from agents.agent_core.orchestrator_agent import OrchestratorAgent
        from agent_platform.core.protocol import AgentContext

        agent = OrchestratorAgent()

        flows_to_test = [
            "be_then_test",
            "backend_only",
            "frontend_only",
            "full_pipeline",
            "frontend_restructure",
            "gen_backend",
            "auto_fix",
        ]

        for flow in flows_to_test:
            context = AgentContext(user_id="test_user")
            result = agent.handle_request({
                "mode": "plan",
                "flow": flow,
                "task": "test_task",  # Required for gen_backend and auto_fix
                "target": "backend",  # Required for auto_fix
                "target_files": ["test.py"],  # Required for auto_fix
            }, context)

            assert result["success"] is True, f"Plan mode failed for flow: {flow}"
            assert result["data"]["flow"] == flow
            assert "plan" in result["data"]


class TestAgentResponseTypeWithErrorKind:
    """Tests for AgentResponse type definition update (Phase 3.1)."""

    def test_agent_response_type_has_error_kind(self):
        """AgentResponse TypedDict should have error_kind field."""
        from agents.tools.types import AgentResponse
        import typing

        # Get the annotations from AgentResponse
        # For TypedDict, we need to check __annotations__ from all bases
        annotations = {}
        for cls in AgentResponse.__mro__:
            if hasattr(cls, "__annotations__"):
                annotations.update(cls.__annotations__)

        assert "error_kind" in annotations
        assert annotations["error_kind"] == str
