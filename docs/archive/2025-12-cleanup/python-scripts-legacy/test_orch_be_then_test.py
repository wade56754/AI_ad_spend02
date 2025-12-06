"""测试 OrchestratorAgent 的 be_then_test 流程"""

import os
from agents.plugin import register_all
from agent_platform.core.registry import create_agent
from agent_platform.core.protocol import AgentContext
import json

# 设置环境变量以使用 DummyClient（用于测试）
# 这样可以看到完整的流程，即使没有真实的 LLM 后端
os.environ.pop("ANTHROPIC_API_KEY", None)

# 注册所有 agents
register_all()

# 获取 OrchestratorAgent
orch = create_agent("orch")

# 创建 context 用于追溯
context = AgentContext(user_id="user_123")

# 执行 be_then_test 流程
result = orch.handle_request({
    "flow": "be_then_test",
    "task": "为 finance_profit 模块补全 API 并补上测试",
    "target_files": ["routers/finance.py", "services/finance_service.py"],
    "module": "finance_profit"
}, context)

# 打印结果
print("=" * 80)
print("OrchestratorAgent be_then_test 流程结果")
print("=" * 80)
print(json.dumps(result, indent=2, ensure_ascii=False))
print("=" * 80)

# 结果结构验证
assert "success" in result
assert "data" in result
assert "error" in result

if result["success"]:
    assert "flow" in result["data"]
    assert "backend_result" in result["data"]
    assert "test_result" in result["data"]
    assert "meta" in result["data"]
    assert result["data"]["meta"]["run_id"] == context.run_id
    assert result["data"]["meta"]["called_agents"] == ["be", "test"]
    assert result["data"]["meta"]["agent"] == "orch"
    print("\n✅ 所有验证通过！")
else:
    print(f"\n❌ 流程失败: {result.get('error', 'Unknown error')}")

