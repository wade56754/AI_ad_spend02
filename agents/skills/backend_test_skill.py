# agents/skills/backend_test_skill.py
"""
Backend Test Skill：生成后端 pytest 测试执行提示词。

职责：
- 根据 scope/level 参数，生成对应的 pytest 命令和报告格式要求
- 不直接执行测试，只生成 prompt 供 MCP / Claude 执行

改动历史：
- v1.2: 添加 timeout 参数支持 (AUTOMATION_TEST_SPEC_v1.4.md 第 2 章)
- v1.1: 移除硬编码路径，改为相对路径描述；增加 quick 模式命令；处理 None 值
"""
from typing import Dict, Any
import logging

from ..agents_config import SOT_FILES, read_optional
from ..tools.types import SkillResult

logger = logging.getLogger(__name__)


def backend_test_skill(scope: str = "all", level: str = "full", timeout: int = None) -> SkillResult:
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
    # 使用保守值以允许 setup/teardown 开销
    default_timeout = 10 if level == "quick" else 30
    timeout_value = timeout if timeout is not None else default_timeout
    timeout_flag = f"--timeout={timeout_value}"

    # 日志增强：打印最终执行参数（P1-CODE-002 修复）
    logger.info(f"[BackendTestSkill] 执行参数: scope={scope}, level={level}, timeout={timeout_value}s")
    logger.info(f"[BackendTestSkill] pytest timeout flag: {timeout_flag}")

    # 可选：加载 TESTING / MASTER 文档做上下文（不存在也没关系）
    # 处理 None 值，避免在 prompt 中出现 "None" 字符串
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
- 仓库根目录：当前工作区根目录（通常已通过 cd 切换或由工具自动定位）
- 后端目录：backend/
- 测试目录：backend/tests/

核心测试文件：
- backend/tests/conftest.py
  - 提供统一的 SQLite 测试环境与兼容层：
    - 数据库：SQLite (当前版本使用内存库或项目配置的测试库)
    - BigInteger 编译器：@compiles(BigInteger, "sqlite") → INTEGER（已在模型导入前注册）
    - GUID TypeDecorator：PostgreSQL UUID → SQLite CHAR(36)
    - JSONBCompat：PostgreSQL JSONB → SQLite JSON
  - 标准 fixtures：
    - db_session, test_user, test_ad_account 等

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

部分 SoT 上下文（可选，若为空则忽略）：
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

┌─────────────────┬─────────────────────────────────────────────────────────────────────────────────────────┬───────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ scope           │ level="full" (完整测试)                                                                  │ level="quick" (仅 service + api，跳过 permissions/performance/invariants)                                    │
├─────────────────┼─────────────────────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ledger          │ python -m pytest tests/ledger -v --tb=short --no-cov {timeout_flag}                     │ python -m pytest tests/ledger/test_ledger_service.py -v --tb=short --no-cov {timeout_flag}                   │
│ topups          │ python -m pytest tests/test_topup_*.py -v --tb=short --no-cov {timeout_flag}            │ python -m pytest tests/test_topup_service.py tests/test_topup_api.py -v --tb=short --no-cov {timeout_flag}   │
│ daily_reports   │ python -m pytest tests/test_daily_report_*.py -v --tb=short --no-cov {timeout_flag}     │ python -m pytest tests/test_daily_report_service.py tests/test_daily_report_api.py -v --tb=short --no-cov {timeout_flag} │
│ reconciliation  │ python -m pytest tests/test_reconciliation_*.py -v --tb=short --no-cov {timeout_flag}   │ python -m pytest tests/test_reconciliation_service.py tests/test_reconciliation_api.py -v --tb=short --no-cov {timeout_flag} │
│ all             │ python -m pytest tests/ -v --tb=short --no-cov {timeout_flag}                           │ python -m pytest tests/ledger/test_ledger_service.py tests/test_topup_service.py tests/test_topup_api.py tests/test_daily_report_service.py tests/test_daily_report_api.py tests/test_reconciliation_service.py tests/test_reconciliation_api.py -v --tb=short --no-cov {timeout_flag} │
└─────────────────┴─────────────────────────────────────────────────────────────────────────────────────────┴───────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

你需要：
1. 进入 backend 目录（cd backend）；
2. 根据 scope/level 执行上表中对应的 pytest 命令；
3. 收集 pytest 的汇总信息（short test summary info + exit code）。
</input>

<constraints>
- 不修改任何源代码，只执行测试并分析结果。
- 不隐藏错误：
  - 若有失败或 error，必须在报告中点名测试文件、用例以及错误类型（简要说明）。
- 优先使用 "python -m pytest" 形式，确保使用虚拟环境中的 Python。
- 如果存在数据库文件缓存（例如 SQLite 文件库），在认为有必要时可提示用户删除后重建测试库，
  但不要自行假设已经删除。
</constraints>

<thinking>
请使用多步推理方式分析和整理测试结果，大致流程：

1. 解析 scope / level，并构造对应的 pytest 命令列表。
2. 在 backend 目录中逐条执行这些命令，记录：
   - 命令字符串
   - 退出码（exit code）
   - pytest 摘要中的 Passed / Failed / Errors / Skipped 统计。
3. 将所有错误划分为：
   - 环境层错误（数据库连接、类型不兼容、导入失败等）
   - 业务层失败（断言失败、不变量不满足、状态机不符合 SoT 等）
4. 按模块聚合统计结果（ledger / topups / daily_reports / reconciliation）：
   - 测试文件数（可按已有清单推断）
   - 用例数（从 pytest 输出估算或按既有统计对齐）
   - Passed / Failed / Errors / Skipped
   - 是否出现环境层错误。
5. 生成一份「Backend 测试环境健康度报告」：
   - 明确写出环境层失败用例数（期望为 0）
   - 明确写出业务逻辑失败用例数
   - 若四个模块在当前 scope 下：
     - 环境层失败=0 且 业务失败=0，则给出「本轮测试健康度：100%，可进入上线评审」结论；
   - 若存在失败：
     - 列出几个典型失败用例和错误原因（1 行/条），并标明归属（环境 / 业务）。
</thinking>

<steps>
1. 切换工作目录：
   - cd backend（相对于项目根目录）
2. 根据 scope / level 选择并执行 <input> 部分表格中对应的 pytest 命令。
3. 记录每个命令的执行结果与摘要统计。
4. 将结果按模块/维度汇总成矩阵：
   - 模块、测试文件数、用例数、Passed/Failed/Errors/Skipped。
5. 标明环境层问题是否已全部解决（如 BigInteger/UUID/JSONB/SQLite 等）。
6. 写出最终结论与上线建议等级：
   - 例如：「可进入上线评审 / 建议先小流量灰度 / 暂不建议上线（需要先修复 X 问题）」。
</steps>

<output_format>
请用 Markdown 输出，建议结构：

**（可选）机器可解析状态头**：在报告最开头输出一个 JSON 代码块，方便上层自动解析结果：
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

1. Backend 测试环境健康度报告（本轮）
2. 测试环境概览（数据库、兼容层、核心配置文件）
3. 测试执行结果矩阵（按模块）
4. 环境问题修复情况（若本轮均为 0，明确写出）
5. 业务失败用例清单（如无，写明为 0）
6. SoT 对齐状态（列出相关 SoT 文档与版本）
7. 运行命令摘要（列出本轮实际执行的 pytest 命令）
8. 最终结论与上线建议。
</output_format>
""".strip()

    return {
        "success": True,
        "data": {"prompt": prompt},
        "error": None,
    }
