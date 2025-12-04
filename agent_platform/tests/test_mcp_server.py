"""
Tests for agent_platform.mcp.server module - MCP Mode Phase 3.3

Test coverage:
- P2-01: ap_run_pytest whitelist validation
- P2-02: ap_run_agent tool functionality

基准对齐:
- MCP Mode Phase 3.3
- MASTER.md v3.5
"""

import os
import pytest
from unittest.mock import MagicMock, patch


# =============================================================================
# P2-01: ap_run_pytest Whitelist Validation Tests
# =============================================================================

class TestPytestExtraArgsWhitelist:
    """Tests for _validate_pytest_extra_args whitelist function."""

    def test_allows_simple_flags(self):
        """Simple flags like -v, -q, -s should be allowed."""
        from agent_platform.mcp.server import _validate_pytest_extra_args

        allowed, rejected = _validate_pytest_extra_args(["-v", "-q", "-s"])

        assert allowed == ["-v", "-q", "-s"]
        assert rejected == []

    def test_allows_verbose_variants(self):
        """Verbose flag variants should be allowed."""
        from agent_platform.mcp.server import _validate_pytest_extra_args

        allowed, rejected = _validate_pytest_extra_args(["-vv", "--verbose", "--quiet"])

        assert allowed == ["-vv", "--verbose", "--quiet"]
        assert rejected == []

    def test_allows_prefix_args(self):
        """Prefix arguments like --tb=short, --color=yes should be allowed."""
        from agent_platform.mcp.server import _validate_pytest_extra_args

        allowed, rejected = _validate_pytest_extra_args([
            "--tb=short", "--color=yes", "--maxfail=5", "--durations=10"
        ])

        assert allowed == ["--tb=short", "--color=yes", "--maxfail=5", "--durations=10"]
        assert rejected == []

    def test_allows_value_args(self):
        """Value arguments like -k, -m, -W should be allowed with their values."""
        from agent_platform.mcp.server import _validate_pytest_extra_args

        allowed, rejected = _validate_pytest_extra_args([
            "-k", "test_something",
            "-m", "slow",
            "-W", "ignore::DeprecationWarning"
        ])

        assert allowed == ["-k", "test_something", "-m", "slow", "-W", "ignore::DeprecationWarning"]
        assert rejected == []

    def test_rejects_dangerous_args(self):
        """Dangerous args like --confcutdir should be rejected."""
        from agent_platform.mcp.server import _validate_pytest_extra_args

        allowed, rejected = _validate_pytest_extra_args([
            "-v",
            "--confcutdir=/etc",
            "--collect-only"  # Not in whitelist but not dangerous
        ])

        assert "-v" in allowed
        assert "--confcutdir=/etc" in rejected
        assert "--collect-only" in rejected  # Not whitelisted

    def test_rejects_unknown_args(self):
        """Unknown args not in whitelist should be rejected."""
        from agent_platform.mcp.server import _validate_pytest_extra_args

        allowed, rejected = _validate_pytest_extra_args([
            "-v",
            "--unknown-flag",
            "--foo=bar"
        ])

        assert allowed == ["-v"]
        assert "--unknown-flag" in rejected
        assert "--foo=bar" in rejected

    def test_empty_input_returns_empty(self):
        """Empty input should return empty lists."""
        from agent_platform.mcp.server import _validate_pytest_extra_args

        allowed, rejected = _validate_pytest_extra_args([])

        assert allowed == []
        assert rejected == []

    def test_mixed_allowed_and_rejected(self):
        """Mixed input should correctly separate allowed and rejected."""
        from agent_platform.mcp.server import _validate_pytest_extra_args

        allowed, rejected = _validate_pytest_extra_args([
            "-v",
            "-k", "integration",
            "--confcutdir=/tmp",
            "--tb=short",
            "--rootdir=/bad"
        ])

        assert "-v" in allowed
        assert "-k" in allowed
        assert "integration" in allowed
        assert "--tb=short" in allowed
        assert "--confcutdir=/tmp" in rejected
        assert "--rootdir=/bad" in rejected


class TestRunPytestWithWhitelist:
    """Integration tests for run_pytest with whitelist enforcement."""

    def test_run_pytest_filters_dangerous_args(self, tmp_path):
        """run_pytest should filter out non-whitelisted args."""
        from agent_platform.mcp.server import run_pytest

        # Create a mock test directory
        test_dir = tmp_path / "tests"
        test_dir.mkdir()

        # Mock subprocess to avoid actual pytest execution
        with patch("agent_platform.mcp.server.subprocess.run") as mock_run, \
             patch("agent_platform.mcp.server.REPO_ROOT", tmp_path):
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="All tests passed",
                stderr=""
            )

            result = run_pytest(
                test_paths=["tests/"],
                extra_args=["--confcutdir=/etc", "-v"]
            )

            # Should have filtered --confcutdir
            assert "rejected_args" in result
            assert "--confcutdir=/etc" in result["rejected_args"]

    def test_run_pytest_logs_rejected_args(self, tmp_path):
        """run_pytest should include rejected args in result."""
        from agent_platform.mcp.server import run_pytest

        # Create a mock test directory
        test_dir = tmp_path / "tests"
        test_dir.mkdir()

        with patch("agent_platform.mcp.server.subprocess.run") as mock_run, \
             patch("agent_platform.mcp.server.REPO_ROOT", tmp_path):
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="OK",
                stderr=""
            )

            result = run_pytest(
                test_paths=["tests/"],
                extra_args=["--unknown", "-v", "--dangerous=yes"]
            )

            assert "rejected_args" in result
            assert "--unknown" in result["rejected_args"]
            assert "--dangerous=yes" in result["rejected_args"]


# =============================================================================
# P2-02: ap_run_agent Tool Tests
# =============================================================================

class TestRunAgent:
    """Tests for ap_run_agent MCP tool."""

    def test_run_existing_agent_success(self):
        """Should successfully invoke an existing MCP-safe agent."""
        from agent_platform.mcp.server import run_agent

        # Phase 4: Only MCP-safe agents can be run
        # Use "review" agent with empty changes - should succeed
        result = run_agent(
            agent_name="review",
            payload={"action": "review", "changes": {}}
        )

        assert result["success"] is True
        assert result["mcp_safe"] is True
        assert result["agent_name"] == "review"

    def test_run_nonexistent_agent_fails(self):
        """Should return error for non-existent agent."""
        from agent_platform.mcp.server import run_agent

        # Mock create_agent to raise KeyError
        with patch("agent_platform.mcp.server.create_agent", side_effect=KeyError("unknown")):
            result = run_agent(
                agent_name="unknown_agent",
                payload={"task": "test"}
            )

            assert result["success"] is False
            assert "AGENT_NOT_FOUND" in result["error_kind"]

    def test_run_mcp_unsafe_agent_blocked(self):
        """Should block MCP-unsafe agents with appropriate error."""
        from agent_platform.mcp.server import run_agent

        # Phase 4: MCP-unsafe agents (be, fe, orch) are blocked
        result = run_agent(
            agent_name="be",
            payload={"task": "generate code"}
        )

        assert result["success"] is False
        assert result["error_kind"] == "MCP_UNSAFE_AGENT"
        assert result["mcp_safe"] is False
        assert "available_agents" in result

    def test_run_agent_with_context(self):
        """Should pass context to agent handle_request."""
        from agent_platform.mcp.server import run_agent

        # Phase 4: Use MCP-safe agent "doc" for context test
        test_context = {"project_root": "/path/to/project", "dry_run": True}

        result = run_agent(
            agent_name="doc",
            payload={"action": "generate", "doc_type": "spec", "target": "test.md", "context": "test"},
            context=test_context
        )

        # Verify the agent was called successfully
        assert result["success"] is True
        assert result["agent_name"] == "doc"

    def test_run_agent_list_available(self):
        """Should be able to list available agents."""
        from agent_platform.mcp.server import list_agents

        # Phase 4: list_agents now uses agent_platform.agents registry directly
        # Call the real function - it should return MCP-safe agents by default
        result = list_agents()

        assert result["success"] is True
        # Should have at least the 3 MCP-safe agents: test, review, doc
        assert result["count"] >= 3
        assert result["mcp_mode"] is True

        # Verify MCP-safe agents are included
        agent_names = [a["name"] for a in result["agents"]]
        assert "test" in agent_names
        assert "review" in agent_names
        assert "doc" in agent_names


class TestExtractAgentSummary:
    """Tests for _extract_agent_summary helper function."""

    def test_extracts_be_agent_summary(self):
        """Should extract BE agent specific summary."""
        from agent_platform.mcp.server import _extract_agent_summary

        response = {
            "success": True,
            "data": {
                "changes": {"api/route.py": "..."},
                "notes": ["Generated 1 file"]
            }
        }

        summary = _extract_agent_summary("be", response)

        assert "changes" in summary.lower() or "file" in summary.lower()

    def test_extracts_test_agent_summary(self):
        """Should extract Test agent specific summary."""
        from agent_platform.mcp.server import _extract_agent_summary

        response = {
            "success": True,
            "data": {
                "executed": False,
                "reason": "MCP mode"
            }
        }

        summary = _extract_agent_summary("test", response)

        assert "executed" in summary.lower() or "mcp" in summary.lower()

    def test_extracts_review_agent_summary(self):
        """Should extract Review agent specific summary."""
        from agent_platform.mcp.server import _extract_agent_summary

        response = {
            "success": True,
            "data": {
                "passed": True,
                "violations": [],
                "warnings": [{"rule": "DOC-001"}]
            }
        }

        summary = _extract_agent_summary("review", response)

        assert "passed" in summary.lower() or "warning" in summary.lower()


# =============================================================================
# Security Tests
# =============================================================================

class TestPathSecurityValidation:
    """Tests for validate_path_security function."""

    def test_rejects_unc_backslash_paths(self):
        """Should reject UNC paths with backslashes."""
        from agent_platform.mcp.server import validate_path_security

        with pytest.raises(ValueError, match="UNC"):
            validate_path_security("\\\\server\\share\\file.txt")

    def test_rejects_unc_forward_slash_paths(self):
        """Should reject UNC paths with forward slashes."""
        from agent_platform.mcp.server import validate_path_security

        with pytest.raises(ValueError, match="UNC"):
            validate_path_security("//server/share/file.txt")

    def test_allows_absolute_local_paths(self):
        """Should allow absolute local paths."""
        from agent_platform.mcp.server import validate_path_security

        # These should not raise
        validate_path_security("C:\\Users\\test\\file.txt")
        validate_path_security("/home/user/file.txt")

    def test_allows_relative_paths(self):
        """Should allow relative paths."""
        from agent_platform.mcp.server import validate_path_security

        # These should not raise
        validate_path_security("./src/file.py")
        validate_path_security("tests/test_file.py")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
