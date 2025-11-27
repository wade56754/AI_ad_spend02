from agents.skills.sot_guard_skill import SotGuardSkill

class BackendAgent:
    def __init__(self, claude_client):
        self.claude = claude_client
        self.sot_guard = SotGuardSkill(claude_client)

    def run(self, task: BackendTaskConfig):
        # 1. 官方后端 sub-agent 干活（例如对 daily_reports 生成/修改 Router+Service）
        code_result = self._call_backend_subagent(task)

        # 2. 调 SoT 守门员
        guard_result = self.sot_guard.run_check(
            target_description=f"backend: {task.module_name}",
            artifacts=code_result.changed_files,
        )

        # 3. 如果有 P0 问题：可以直接 fail，或者自动再触发一轮修复
        if guard_result.issues.get("P0"):
            # 简单版本：直接报告错误
            return BackendRunResult(
                success=False,
                message="SoT 审查未通过（存在 P0 问题）",
                guard_report=guard_result.raw_report,
            )

        # 4. P1/P2 先报告，但不阻塞（你可以之后再决定要不要自动修）
        return BackendRunResult(
            success=True,
            message="生成成功，已通过 SoT P0 审查",
            guard_report=guard_result.raw_report,
        )
