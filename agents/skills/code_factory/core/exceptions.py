"""
自定义异常

基准文档: MASTER.md v4.6
版本: v4.2
"""

from typing import List, Optional


class CodeFactoryError(Exception):
    """代码工厂基础异常"""

    pass


class SotVersionMismatchError(CodeFactoryError):
    """SoT 版本不匹配异常

    当加载的 SoT 文档版本与期望版本不一致时抛出
    """

    def __init__(self, file: str, expected: str, actual: str):
        self.file = file
        self.expected = expected
        self.actual = actual
        super().__init__(f"{file}: 期望 {expected}, 实际 {actual}")


class RiskBlockedError(CodeFactoryError):
    """高风险阻断异常

    当检测到高风险模块或关键词时抛出，阻止代码生成
    """

    def __init__(self, reason: str, module_id: Optional[str] = None):
        self.reason = reason
        self.module_id = module_id
        super().__init__(f"阻断: {reason}")


class TraceFailedError(CodeFactoryError):
    """追溯率不足异常

    当代码追溯率低于阈值时抛出
    """

    def __init__(self, rate: float, threshold: float = 1.0):
        self.rate = rate
        self.threshold = threshold
        super().__init__(f"追溯率 {rate:.0%} < {threshold:.0%}")


class EditRejectedError(CodeFactoryError):
    """编辑被 Guardrails 拒绝异常

    当代码编辑无法通过语法/lint 检查时抛出
    """

    def __init__(self, file: str, errors: List[str]):
        self.file = file
        self.errors = errors
        super().__init__(f"{file}: {errors}")


class PhaseExecutionError(CodeFactoryError):
    """阶段执行错误

    当某个阶段执行失败时抛出
    """

    def __init__(self, phase_id: int, phase_name: str, message: str):
        self.phase_id = phase_id
        self.phase_name = phase_name
        super().__init__(f"Phase {phase_id} ({phase_name}): {message}")


class SessionRecoveryError(CodeFactoryError):
    """会话恢复错误

    当无法恢复之前的会话时抛出
    """

    def __init__(self, session_id: str, reason: str):
        self.session_id = session_id
        self.reason = reason
        super().__init__(f"无法恢复会话 {session_id}: {reason}")
