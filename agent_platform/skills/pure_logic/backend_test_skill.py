"""
backend_test_skill.py - 后端测试 Skill

Phase 3: 从 agents/skills/backend_test_skill.py 迁移

职责：
- 根据 scope/level 参数，生成对应的 pytest 命令和报告格式要求
- 不直接执行测试，只生成 prompt 供 MCP / Claude 执行

改动历史：
- v1.2: 添加 timeout 参数支持 (AUTOMATION_TEST_SPEC_v1.4.md 第 2 章)
- v1.1: 移除硬编码路径，改为相对路径描述

基准对齐:
- AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md Phase 3
- SoT Freeze v2.6
"""

from typing import Dict, Any, Optional
import logging

from agent_platform.config.sot_files import SOT_FILES
from agent_platform.config.paths import read_optional

logger = logging.getLogger(__name__)


def backend_test_skill(
    scope: str = "all",
    level: str = "full",
    timeout: Optional[int] = None
) -> Dict[str, Any]:
    """
    后端测试 Skill：生成「Backend 测试环境健康度报告」的执行提示词。

    Args:
        scope: "ledger" | "topups" | "daily_reports" | "reconciliation" | "all"
        level: "quick" (仅 service+api) | "full" (全部测试文件)
        timeout: 测试超时时间（秒），None 表示使用默认值
                 默认值参考 AUTOMATION_TEST_SPEC_v1.4.md 第 2 章:
                 - L0 Unit: 1s (100ms per test, buffer for setup)
                 - L1 Integration: 5s (500ms per test, buffer for DB)
                 - L2 API: 10s (1s per test, buffer for HTTP)
                 - L3 E2E: 30s (5s per test, buffer for full flow)

    Returns:
        SkillResult with prompt in data.prompt
    """
    scope = (scope or "all").lower()
    level = (level or "full").lower()

    # 默认超时配置 (秒) - 基于 AUTOMATION_TEST_SPEC_v1.4.md 第 2 章
    default_timeout = 10 if level == "quick" else 30
    timeout_value = timeout if timeout is not None else default_timeout
    timeout_flag = f"--timeout={timeout_value}"

    logger.info(f"[BackendTestSkill] 执行参数: scope={scope}, level={level}, timeout={timeout_value}s")
    logger.info(f"[BackendTestSkill] pytest timeout flag: {timeout_flag}")

    # 可选：加载 TESTING / MASTER 文档做上下文
    testing_md = read_optional(SOT_FILES.get("TESTING")) or ""
    master_md = read_optional(SOT_FILES.get("MASTER")) or ""

    prompt = f"""
<task>
你是 AI_ad_spend02 项目的后端测试执行与健康度评估 Agent。
你的职责是：在指定范围内运行 backend 单元测试（ledger / topups / daily_reports / reconciliation / 全量），
并生成一份结构化的「Backend 测试环境健康度报告」，帮助开发者判断当前代码是否可以进入上线流程。
</task>

<context>
use context7

项目结构（相对于当前工作区根目录）：
- 仓库根目录：当前工作区根目录
- 后端目录：backend/
- 测试目录：backend/tests/

核心测试文件：
- backend/tests/conftest.py
  - 提供统一的 SQLite 测试环境与兼容层

模块测试文件清单（按模块）：
- ledger:
  - backend/tests/ledger/test_ledger_service.py
  - backend/tests/ledger/test_ledger_invariants.py
- topups:
  - backend/tests/test_topup_service.py
  - backend/tests/test_topup_api.py
  - backend/tests/test_topup_permissions.py
- daily_reports:
  - backend/tests/test_daily_report_service.py
  - backend/tests/test_daily_report_api.py
  - backend/tests/test_daily_report_permissions.py
  - backend/tests/test_daily_report_performance.py
- reconciliation:
  - backend/tests/test_reconciliation_service.py
  - backend/tests/test_reconciliation_api.py
  - backend/tests/test_reconciliation_permissions.py

当前测试范围:
- scope = "{scope}"
- level = "{level}"
- timeout = {timeout_value}s (per test)

部分 SoT 上下文（可选）：
<MASTER_MD>
{master_md if master_md else "(未加载)"}
</MASTER_MD>

<TESTING_MD>
{testing_md if testing_md else "(未加载)"}
</TESTING_MD>
</context>

<input>
你需要在真实代码目录中执行 pytest（通过终端 / shell 工具），而不是假想执行。

工作目录：
- 先切换到 backend 目录：cd backend

根据 scope 和 level 选择测试命令（包含 {timeout_flag}）：

注意：需要安装 pytest-timeout 插件（pip install pytest-timeout）

| scope           | level="full"                                              | level="quick"                                                    |
|-----------------|-----------------------------------------------------------|------------------------------------------------------------------|
| ledger          | python -m pytest tests/ledger -v --tb=short --no-cov {timeout_flag} | python -m pytest tests/ledger/test_ledger_service.py -v --tb=short --no-cov {timeout_flag} |
| topups          | python -m pytest tests/test_topup_*.py -v --tb=short --no-cov {timeout_flag} | python -m pytest tests/test_topup_service.py tests/test_topup_api.py -v --tb=short --no-cov {timeout_flag} |
| daily_reports   | python -m pytest tests/test_daily_report_*.py -v --tb=short --no-cov {timeout_flag} | python -m pytest tests/test_daily_report_service.py tests/test_daily_report_api.py -v --tb=short --no-cov {timeout_flag} |
| reconciliation  | python -m pytest tests/test_reconciliation_*.py -v --tb=short --no-cov {timeout_flag} | python -m pytest tests/test_reconciliation_service.py tests/test_reconciliation_api.py -v --tb=short --no-cov {timeout_flag} |
| all             | python -m pytest tests/ -v --tb=short --no-cov {timeout_flag} | python -m pytest tests/ledger/test_ledger_service.py tests/test_topup_service.py tests/test_topup_api.py tests/test_daily_report_service.py tests/test_daily_report_api.py tests/test_reconciliation_service.py tests/test_reconciliation_api.py -v --tb=short --no-cov {timeout_flag} |

你需要：
1. 进入 backend 目录（cd backend）；
2. 根据 scope/level 执行上表中对应的 pytest 命令；
3. 收集 pytest 的汇总信息（short test summary info + exit code）。
</input>

<constraints>
- 不修改任何源代码，只执行测试并分析结果。
- 若有失败或 error，必须在报告中点名测试文件、用例以及错误类型。
- 优先使用 "python -m pytest" 形式，确保使用虚拟环境中的 Python。
</constraints>

<output_format>
请用 Markdown 输出，建议结构：

**机器可解析状态头**：
```json
{{
  "status": "pass" | "fail" | "partial",
  "scope": "{scope}",
  "level": "{level}",
  "total_tests": <int>,
  "passed": <int>,
  "failed": <int>,
  "errors": <int>,
  "skipped": <int>,
  "env_issues": <int>,
  "business_issues": <int>
}}
```

然后是人类可读的报告正文：
1. Backend 测试环境健康度报告
2. 测试环境概览
3. 测试执行结果矩阵（按模块）
4. 环境问题修复情况
5. 业务失败用例清单
6. 最终结论与上线建议
</output_format>
""".strip()

    return {
        "success": True,
        "data": {"prompt": prompt},
        "error": None,
    }
