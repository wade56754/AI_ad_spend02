# agents/skills/sot_guard_skill.py

from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class SotGuardResult:
    ok: bool
    raw_report: str
    issues: Dict[str, list]  # {"P0": [...], "P1": [...], "P2": [...]}

class SotGuardSkill:
    name = "sot_guard"

    def __init__(self, claude_client):
        self.client = claude_client  # 你现在用的官方 CLI / API 适配层

    def run_check(self, target_description: str, artifacts: list[str]) -> SotGuardResult:
        """
        :param target_description: 本次审查的对象说明，比如 'backend daily_reports router'
        :param artifacts: 要审查的文件路径列表
        """
        # 1. 把文件内容读出来，打包成 prompt
        # 2. 调用官方 sub-agent `sot-guard`
        #    类似：/agent sot-guard + 附带文件内容 / diff
        # 伪代码示意：
        prompt = self._build_prompt(target_description, artifacts)

        # 这里用你现有的官方调用封装，例如：self.client.call_agent("sot-guard", prompt)
        response = self.client.call_sub_agent("sot-guard", prompt)

        # 再解析成结构化结果，方便上层 Agent 判断要不要进入下一轮
        parsed = self._parse_response(response)
        return parsed

    def _build_prompt(self, target_description: str, artifacts: list[str]) -> str:
        # 从 artifacts 中读文件 + 简单包一层说明就行
        ...

    def _parse_response(self, response: str) -> SotGuardResult:
        # 解析成 {"P0": [...], "P1": [...], "P2": [...]} 这种结构
        ...
