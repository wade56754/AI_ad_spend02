"""
Agent Platform 异常定义

所有平台级异常的基类和具体异常类型。
"""


class AgentPlatformError(Exception):
    """Agent Platform 基础异常"""

    def __init__(self, message: str, code: str = "PLATFORM_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
        }


class AgentNotFoundError(AgentPlatformError):
    """Agent 未找到"""

    def __init__(self, agent_name: str, available: list[str] | None = None):
        self.agent_name = agent_name
        self.available = available or []
        message = f"Agent '{agent_name}' not found"
        if self.available:
            message += f". Available: {', '.join(self.available)}"
        super().__init__(message, code="AGENT_NOT_FOUND")


class AgentRegistrationError(AgentPlatformError):
    """Agent 注册失败"""

    def __init__(self, agent_name: str, reason: str):
        self.agent_name = agent_name
        message = f"Failed to register agent '{agent_name}': {reason}"
        super().__init__(message, code="AGENT_REGISTRATION_ERROR")


class AgentExecutionError(AgentPlatformError):
    """Agent 执行失败"""

    def __init__(self, agent_name: str, reason: str, run_id: str | None = None):
        self.agent_name = agent_name
        self.run_id = run_id
        message = f"Agent '{agent_name}' execution failed: {reason}"
        super().__init__(message, code="AGENT_EXECUTION_ERROR")


class LLMClientError(AgentPlatformError):
    """LLM 客户端错误"""

    def __init__(self, message: str, provider: str | None = None):
        self.provider = provider
        super().__init__(message, code="LLM_CLIENT_ERROR")


class LLMNotConfiguredError(LLMClientError):
    """LLM 未配置或在 MCP 模式下被禁用"""

    def __init__(self, message: str | None = None):
        default_message = (
            "No LLM backend available. "
            "Set ANTHROPIC_API_KEY or install Claude Code CLI."
        )
        super().__init__(
            message or default_message,
            provider=None,
        )


# ============================================================
# Skill 相关异常 (Phase 3)
# ============================================================


class SkillNotFoundError(AgentPlatformError):
    """Skill 未找到"""

    def __init__(self, skill_name: str, available: list[str] | None = None):
        self.skill_name = skill_name
        self.available = available or []
        message = f"Skill '{skill_name}' not found"
        if self.available:
            message += f". Available: {', '.join(self.available)}"
        super().__init__(message, code="SKILL_NOT_FOUND")


class SkillExecutionError(AgentPlatformError):
    """Skill 执行失败"""

    def __init__(self, skill_name: str, reason: str):
        self.skill_name = skill_name
        message = f"Skill '{skill_name}' execution failed: {reason}"
        super().__init__(message, code="SKILL_EXECUTION_ERROR")
