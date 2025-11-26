from typing import Dict, Any

from agents_config import SOT_FILES, read_optional


def db_test_skill() -> Dict[str, Any]:
    cases = read_optional(SOT_FILES["DB_TEST_CASES"])
    sql = read_optional(SOT_FILES["DB_INVARIANTS_SQL"])

    if not sql:
        return {"ok": False, "error": "db_invariants_test_v2.sql 未找到"}

    # 生成给 Claude + Supabase MCP 使用的提示词
    prompt = f"""
<ROLE>
你是“数据库不变量测试 Agent”，需要使用 Supabase MCP 服务器执行 SQL 测试脚本。
</ROLE>

<CONTEXT>
<TEST_CASES_MD>
{cases}
</TEST_CASES_MD>

<INVARIANTS_SQL>
{sql}
</INVARIANTS_SQL>
</CONTEXT>

<TASK>
1. 连接到当前项目的 Supabase 数据库（通过 supabase MCP server）。
2. 在一个全新的事务中依次执行 INVARIANTS_SQL 中的内容：
   - 准备测试数据
   - 执行所有 P0/P1/P2 测试用例
3. 收集每个测试用例的执行结果：
   - 通过：记录 PASS + 用例编号
   - 失败：记录 FAIL + 用例编号 + 错误信息
4. 生成一份结构化的测试报告（JSON），包含：
   - 覆盖统计：P0/P1/P2/集成 测试用例数量与通过率
   - 失败用例明细列表
   - 对 schema / 触发器 / 约束的修复建议（文字描述即可）
</TASK>

<OUTPUT_FORMAT>
请只输出一段 JSON，形如：

{{
  "summary": {{
    "p0": {{"total": 13, "passed": 13}},
    "p1": {{"total": 8, "passed": 7}},
    "p2": {{"total": 5, "passed": 5}},
    "flow": {{"total": 4, "passed": 4}}
  }},
  "failures": [
    {{
      "case_id": "TC-LED-00X",
      "severity": "P0 | P1 | P2 | FLOW",
      "reason": "失败原因",
      "suggest_fix": "建议如何修改 init_schema.sql 或业务逻辑"
    }}
  ],
  "notes": [
    "整体结论",
    "下一步建议"
  ]
}}
</OUTPUT_FORMAT>
""".strip()

    return {
        "ok": True,
        "prompt": prompt,
    }
