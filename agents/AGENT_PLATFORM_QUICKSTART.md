# Agent Platform Quickstart

> **Version**: Phase 3.0C
> **Last Updated**: 2025-12-03

## Overview

The AI_ad_spend02 Agent Platform provides a unified interface for running AI code generation agents. It supports both CLI and HTTP entry points for flexible integration.

### Registered Agents

| Agent | Description | Tags |
|-------|-------------|------|
| `demo` | Demo agent that echoes requests | demo, testing |
| `be` | Backend FastAPI/SQLAlchemy code generation | codegen, backend, sot |
| `fe` | Frontend Next.js/React/TypeScript code generation | codegen, frontend, nextjs |
| `test` | Test prompt generation for pytest and DB invariants | test, pytest, qa |
| `orch` | Multi-Agent workflow orchestrator | orchestrator, multi-agent |

### Orchestrator Flows

| Flow | Description |
|------|-------------|
| `be_then_test` | BEAgent → TestAgent with context passthrough |
| `backend_only` | Run BEAgent only |
| `frontend_only` | Run FEAgent only |
| `full_pipeline` | Backend → Frontend → Test |
| `frontend_restructure` | SC-ORCH 7-step frontend restructure |
| `gen_backend` | Batch backend module generation |
| `auto_fix` | Generate → Test → Fix loop |

---

## CLI Usage

### Installation

The CLI is available as a Python module:

```bash
# From project root
python -m agent_platform.cli --help
```

### Commands

#### List Agents

```bash
python -m agent_platform.cli list
```

Output:
```
Registered agents (5):
------------------------------------------------------------
  demo         v1.0.0   [demo, testing]
    Demo agent that echoes requests (for testing)
  be           v1.0.0   [codegen, backend, sot]
    Backend FastAPI/SQLAlchemy code generation with SoT compliance
  ...
```

#### Show Agent Info

```bash
python -m agent_platform.cli info be
```

Output:
```
Agent: be
  Version:     1.0.0
  Description: Backend FastAPI/SQLAlchemy code generation with SoT compliance
  Tags:        codegen, backend, sot
```

#### Run Agent Directly

```bash
# Run backend agent
python -m agent_platform.cli run be \
  --task "Generate topup list API with pagination" \
  --target-files backend/routers/topup.py backend/services/topup_service.py

# Run with JSON output
python -m agent_platform.cli run be \
  --task "Add validation" \
  --target-files routers/foo.py \
  --output json
```

#### Run Orchestrator

```bash
# be_then_test flow (dry-run)
python -m agent_platform.cli orch \
  --flow be_then_test \
  --task "Implement finance_profit module with tests" \
  --module finance_profit \
  --target-files backend/routers/finance_profit.py backend/tests/api/test_finance_profit.py

# Execute mode (writes files)
python -m agent_platform.cli orch \
  --flow be_then_test \
  --task "Implement feature" \
  --mode execute

# Full pipeline
python -m agent_platform.cli orch \
  --flow full_pipeline \
  --task "Add user dashboard" \
  --target-files backend/routers/dashboard.py frontend/src/pages/Dashboard.tsx

# With extra JSON params
python -m agent_platform.cli orch \
  --flow gen_backend \
  --task "daily_reports,topups,ledger" \
  --json '{"auto_write": true}'
```

### Global Options

| Option | Description |
|--------|-------------|
| `-v, --verbose` | Enable verbose output |
| `-o, --output` | Output format: `human` (default) or `json` |
| `--compact` | Compact JSON output (no indentation) |

---

## HTTP API Usage

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/agents` | List all registered agents |
| GET | `/api/v1/agents/{name}` | Get agent metadata |
| POST | `/api/v1/agents/run` | Run any agent by name |
| POST | `/api/v1/agents/orch` | Run OrchestratorAgent |

### List Agents

```bash
curl http://localhost:8000/api/v1/agents
```

Response:
```json
{
  "success": true,
  "data": {
    "agents": [
      {
        "name": "be",
        "version": "1.0.0",
        "description": "Backend FastAPI/SQLAlchemy code generation",
        "tags": ["codegen", "backend", "sot"]
      }
    ],
    "count": 5
  },
  "message": "Found 5 registered agents"
}
```

### Get Agent Info

```bash
curl http://localhost:8000/api/v1/agents/orch
```

### Run Agent

```bash
curl -X POST http://localhost:8000/api/v1/agents/run \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "be",
    "request": {
      "task": "Generate topup API endpoint",
      "target_files": ["routers/topup.py"]
    }
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "run_id": "abc123-def456",
    "agent": "be",
    "result": {
      "success": true,
      "data": {
        "changes": {"routers/topup.py": "..."},
        "notes": ["Generated endpoint following SoT patterns"],
        "meta": {"run_id": "abc123-def456", "agent": "be", "version": "1.0.0"}
      },
      "error": null
    }
  },
  "message": "Agent 'be' executed successfully"
}
```

### Run Orchestrator

```bash
curl -X POST http://localhost:8000/api/v1/agents/orch \
  -H "Content-Type: application/json" \
  -d '{
    "flow": "be_then_test",
    "task": "Implement finance_profit API with tests",
    "target_files": ["routers/finance_profit.py"],
    "module": "finance_profit",
    "mode": "dry-run"
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "run_id": "xyz789",
    "flow": "be_then_test",
    "mode": "dry-run",
    "result": {
      "success": true,
      "data": {
        "flow": "be_then_test",
        "backend_result": {
          "success": true,
          "files_generated": 1,
          "files": ["routers/finance_profit.py"]
        },
        "test_result": {
          "success": true,
          "mode": "backend",
          "executed": false
        },
        "meta": {
          "run_id": "xyz789",
          "called_agents": ["be", "test"]
        }
      }
    }
  },
  "message": "Orchestrator flow 'be_then_test' completed successfully"
}
```

### Request Body Schema

#### AgentRunRequest

```json
{
  "agent": "string (required)",
  "request": {
    "task": "string",
    "target_files": ["array of strings"],
    "...": "agent-specific fields"
  }
}
```

#### OrchRunRequest

```json
{
  "flow": "string (required) - be_then_test|backend_only|frontend_only|...",
  "task": "string (optional)",
  "target_files": ["array of strings (optional)"],
  "module": "string (optional)",
  "mode": "string (optional) - dry-run|execute",
  "extra": {"object (optional) - flow-specific params"}
}
```

---

## Programmatic Usage

### Python Integration

```python
from agents.plugin import register_all
from agent_platform.core.registry import create_agent
from agent_platform.core.protocol import AgentContext

# Register all agents (call once at startup)
register_all()

# Create agent instance
be_agent = create_agent("be")

# Create context for tracing
context = AgentContext()
print(f"Run ID: {context.run_id}")

# Execute request
result = be_agent.handle_request(
    {
        "task": "Generate pagination for topup list",
        "target_files": ["routers/topup.py"],
    },
    context,
)

if result["success"]:
    changes = result["data"]["changes"]
    for path, content in changes.items():
        print(f"Generated: {path}")
else:
    print(f"Error: {result['error']}")
```

### Orchestrator Integration

```python
from agent_platform.core.registry import create_agent
from agent_platform.core.protocol import AgentContext

# Create orchestrator
orch = create_agent("orch")
context = AgentContext()

# Run be_then_test flow
result = orch.handle_request(
    {
        "flow": "be_then_test",
        "task": "Implement and test finance module",
        "target_files": ["routers/finance.py"],
        "module": "finance",
    },
    context,
)

# Check results
if result["success"]:
    data = result["data"]
    print(f"Backend: {data['backend_result']['success']}")
    print(f"Test: {data['test_result']['success']}")
    print(f"Called agents: {data['meta']['called_agents']}")
```

---

## Tracing and Debugging

### Run ID

Every request generates a unique `run_id` for tracing:

```python
context = AgentContext()
print(context.run_id)  # e.g., "a1b2c3d4-e5f6-..."
```

The `run_id` is propagated through all sub-agent calls, enabling end-to-end tracing.

### Verbose Output

CLI:
```bash
python -m agent_platform.cli -v orch --flow be_then_test --task "Test"
```

Logs:
```
2025-12-03 10:00:00 [INFO] agent_platform.cli: [run_id=abc123] Running orchestrator flow 'be_then_test'
2025-12-03 10:00:01 [INFO] agents.agent_core.orchestrator_agent: [run_id=abc123] Orchestrator calling BEAgent
2025-12-03 10:00:02 [INFO] agents.agent_core.be_agent: [run_id=abc123] BE Agent processing task...
```

### Error Handling

All responses follow the SoT-compliant format:

```json
{
  "success": false,
  "data": {
    "meta": {
      "run_id": "abc123",
      "agent": "be",
      "version": "1.0.0"
    }
  },
  "error": "Validation failed: task is required"
}
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Entry Points                           │
├─────────────────────┬───────────────────────────────────────┤
│  CLI                │  HTTP API                             │
│  agent_platform/    │  backend/routers/agents.py            │
│  cli.py             │  POST /agents/run                     │
│  python -m ...      │  POST /agents/orch                    │
└─────────┬───────────┴───────────────┬───────────────────────┘
          │                           │
          ▼                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Agent Platform Core                       │
├─────────────────────────────────────────────────────────────┤
│  agent_platform/core/registry.py                            │
│  - register_agent(name, cls)                                │
│  - create_agent(name) -> AgentProtocol                      │
│  - list_agents() -> List[AgentMetadata]                     │
├─────────────────────────────────────────────────────────────┤
│  agent_platform/core/protocol.py                            │
│  - AgentProtocol (abstract base)                            │
│  - AgentContext (Pydantic model with run_id)                │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Business Agents                          │
├─────────────────────────────────────────────────────────────┤
│  agents/agent_core/                                         │
│  ├── be_agent.py      (Backend code generation)             │
│  ├── fe_agent.py      (Frontend code generation)            │
│  ├── test_agent.py    (Test prompt generation)              │
│  └── orchestrator_agent.py (Multi-agent coordination)       │
├─────────────────────────────────────────────────────────────┤
│  agents/plugin.py                                           │
│  - register_all() - registers all agents                    │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                       Skills Layer                          │
├─────────────────────────────────────────────────────────────┤
│  agents/skills/                                             │
│  ├── be_dev_skill.py      (Backend generation logic)        │
│  ├── fe_dev_skill.py      (Frontend generation logic)       │
│  ├── db_test_skill.py     (DB invariant tests)              │
│  └── backend_test_skill.py (Pytest generation)              │
└─────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Agent Not Found

```
Error: Agent 'xyz' not found in registry
```

Solution: Ensure `register_all()` is called before creating agents:
```python
from agents.plugin import register_all
register_all()
```

### Import Errors

```
ModuleNotFoundError: No module named 'agent_platform'
```

Solution: Run from project root or add to PYTHONPATH:
```bash
export PYTHONPATH=/path/to/AI_ad_spend02:$PYTHONPATH
```

### HTTP 500 on /agents/orch

Check logs for agent registration:
```bash
python -c "from agents.plugin import register_all; register_all()"
```

---

## Related Documentation

- [MASTER.md](../docs/1.overview/MASTER.md) - Project master specification
- [API_SOT.md](../docs/2.sot/API_SOT.md) - API Source of Truth
- [AGENT_LAYER_OVERVIEW.md](../docs/6.agent-layer/AGENT_LAYER_OVERVIEW.md) - Agent layer architecture
- [SUBAGENT_PROTOCOL.md](../docs/6.agent-layer/SUBAGENT_PROTOCOL.md) - AgentProtocol specification
