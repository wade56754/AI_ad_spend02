---
version: v1.0
status: production
layer: agent
owner: wade
last_reviewed: 2025-12-03
baseline: >
  Agent Layer Freeze v1.0, MASTER.md v4.4
---

# Agent Platform Observability SoT

> **Document Version**: v1.0
> **Phase**: 3.1
> **Status**: Production

## 1. Overview

This document defines the observability standards for the Agent Platform, including structured logging, error classification, and execution tracing.

### 1.1 Goals

- **Unified Logging**: Consistent log format across all Agents and Orchestrator
- **Error Classification**: Standardized error taxonomy for automated alerting
- **Distributed Tracing**: `run_id` propagation for end-to-end request tracking
- **Plan/Execute Mode**: Preview flows before execution

### 1.2 Alignment

| Upstream Document | Version | Reference |
|-------------------|---------|-----------|
| MASTER.md | v4.4 | SoT Referee Chain |
| SUBAGENT_PROTOCOL.md | v1.0 | AgentProtocol definition |
| AGENT_ORCHESTRATION_PIPELINE.md | v1.0 | Flow coordination |
| ERROR_CODES_SOT.md | v2.1 | Error code taxonomy |

## 2. ErrorKind Enumeration

All Agent responses include an `error_kind` field for error classification.

### 2.1 Error Types

| ErrorKind | Value | Description | Typical Causes |
|-----------|-------|-------------|----------------|
| OK | `"OK"` | No error | Successful execution |
| VALIDATION_ERROR | `"VALIDATION_ERROR"` | Input validation failed | Missing fields, invalid format |
| SOT_VIOLATION | `"SOT_VIOLATION"` | SoT rule violation | State machine, business rules |
| LLM_ERROR | `"LLM_ERROR"` | LLM API error | Timeout, rate limit, token limit |
| INFRA_ERROR | `"INFRA_ERROR"` | Infrastructure error | Database, network, filesystem |
| AGENT_ERROR | `"AGENT_ERROR"` | Agent execution error | Sub-agent failure, flow error |
| UNKNOWN | `"UNKNOWN"` | Unclassified error | Unexpected exceptions |

### 2.2 Usage in AgentResponse

```python
from agent_platform.core.logging_utils import ErrorKind

# Success response
{
    "success": True,
    "data": {...},
    "error": None,
    "error_kind": "OK"  # Always include error_kind
}

# Error response
{
    "success": False,
    "data": None,
    "error": "Missing required field: task",
    "error_kind": "VALIDATION_ERROR"
}
```

### 2.3 Deriving ErrorKind from Exceptions

```python
from agent_platform.core.logging_utils import derive_error_kind, ErrorKind

try:
    result = agent.handle_request(request, context)
except Exception as e:
    error_kind = derive_error_kind(e)  # Auto-classifies exception
    # error_kind will be LLM_ERROR, AGENT_ERROR, etc.
```

## 3. Structured Logging

### 3.1 log_event Function

```python
from agent_platform.core.logging_utils import log_event, ErrorKind

entry = log_event(
    run_id="abc-123-xyz",           # Required: UUID from AgentContext
    agent_name="orch",              # Required: Agent identifier
    flow="be_then_test",            # Required: Flow name
    stage="start|step:X|end|error", # Required: Execution stage
    success=True,                   # Required: Stage success
    error_kind=ErrorKind.OK,        # Required: Error classification
    message="Starting flow",        # Required: Human-readable message
    extra={"key": "value"},         # Optional: Additional metadata
)
```

### 3.2 Log Entry Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| timestamp | ISO 8601 | Yes | Event timestamp (UTC) |
| run_id | string | Yes | Execution trace ID |
| agent_name | string | Yes | Agent identifier |
| flow | string | Yes | Flow name |
| stage | string | Yes | Execution stage |
| success | boolean | Yes | Stage success |
| error_kind | string | Yes | Error classification |
| message | string | Yes | Event description |
| extra | object | No | Additional metadata |

### 3.3 Standard Stages

| Stage | When Used |
|-------|-----------|
| `start` | Flow/step beginning |
| `step:backend` | BEAgent execution |
| `step:test` | TestAgent execution |
| `step:frontend` | FEAgent execution |
| `end` | Flow/step completion |
| `error` | Exception handling |
| `plan` | Plan mode execution |

### 3.4 Example Log Output

```json
{
  "timestamp": "2025-12-03T10:30:00.000Z",
  "run_id": "abc-123-def-456",
  "agent_name": "orch",
  "flow": "be_then_test",
  "stage": "step:backend",
  "success": true,
  "error_kind": "OK",
  "message": "Calling BEAgent"
}
```

## 4. Plan/Execute Mode

### 4.1 Overview

OrchestratorAgent supports two execution modes:

| Mode | Description | Use Case |
|------|-------------|----------|
| `execute` | Runs the flow (default) | Production execution |
| `plan` | Returns execution plan only | Preview, dry-run |

### 4.2 Plan Mode Request

```python
result = orch_agent.handle_request({
    "mode": "plan",
    "flow": "be_then_test",
    "task": "Generate user API",
    "target_files": ["routers/users.py"],
}, context)
```

### 4.3 Plan Mode Response

```python
{
    "success": True,
    "data": {
        "mode": "plan",
        "flow": "be_then_test",
        "plan": {
            "description": "Backend code generation followed by test validation",
            "steps": [
                {
                    "step": 1,
                    "agent": "be",
                    "action": "Generate backend code",
                    "inputs": ["task", "target_files"],
                    "outputs": ["changes (file_path -> content)"],
                    "blocking": True
                },
                {
                    "step": 2,
                    "agent": "test",
                    "action": "Generate test prompts",
                    "inputs": ["mode=backend", "scope", "level"],
                    "outputs": ["prompt", "executed"],
                    "blocking": False,
                    "condition": "step 1 succeeds"
                }
            ],
            "estimated_agents": ["be", "test"],
            "auto_write": False,
            "request_context": {
                "task": "Generate user API",
                "target_files": ["routers/users.py"],
                "module": null,
                "auto_write": False
            }
        },
        "meta": {
            "run_id": "...",
            "agent": "orch",
            "version": "1.0.0"
        },
        "notes": [
            "Plan generated for flow: be_then_test",
            "Use mode='execute' to run this flow"
        ]
    },
    "error": None,
    "error_kind": "OK"
}
```

### 4.4 Supported Flows for Planning

| Flow | Description |
|------|-------------|
| `be_then_test` | Backend + Test validation |
| `backend_only` | Backend code generation |
| `frontend_only` | Frontend code generation |
| `full_pipeline` | Backend + Frontend + Test |
| `frontend_restructure` | SC-ORCH 7-step pipeline |
| `gen_backend` | Multi-module backend generation |
| `auto_fix` | Generate → Test → Fix loop |

## 5. Run ID Tracing

### 5.1 Context Propagation

```python
from agent_platform.core.protocol import AgentContext

# Create context with run_id
context = AgentContext(user_id="user_123")
run_id = context.run_id  # Auto-generated UUID

# Pass context to agents
result = orch_agent.handle_request(request, context)

# Same run_id in all sub-agents
assert result["data"]["meta"]["run_id"] == run_id
assert result["data"]["backend_result"]["run_id"] == run_id
assert result["data"]["test_result"]["run_id"] == run_id
```

### 5.2 Tracing in Logs

All log entries with the same `run_id` belong to the same request chain:

```bash
# Find all logs for a specific run
grep "run_id.*abc-123-def-456" agent_platform.log
```

## 6. Integration Guidelines

### 6.1 Adding Observability to New Agents

```python
from agent_platform.core.logging_utils import log_event, ErrorKind, derive_error_kind

class MyAgent(AgentProtocol):
    def handle_request(self, request, context=None):
        context = context or AgentContext()
        run_id = context.run_id

        # Log start
        log_event(
            run_id=run_id,
            agent_name=self.name,
            flow="my_flow",
            stage="start",
            success=True,
            error_kind=ErrorKind.OK,
            message="Starting execution",
        )

        try:
            result = self._do_work(request)

            # Log success
            log_event(
                run_id=run_id,
                agent_name=self.name,
                flow="my_flow",
                stage="end",
                success=True,
                error_kind=ErrorKind.OK,
                message="Completed successfully",
            )

            return {
                "success": True,
                "data": result,
                "error": None,
                "error_kind": ErrorKind.OK.value,
            }

        except Exception as e:
            error_kind = derive_error_kind(e)

            # Log error
            log_event(
                run_id=run_id,
                agent_name=self.name,
                flow="my_flow",
                stage="error",
                success=False,
                error_kind=error_kind,
                message=str(e),
            )

            return {
                "success": False,
                "data": None,
                "error": str(e),
                "error_kind": error_kind.value,
            }
```

### 6.2 Alerting Rules (Example)

```yaml
# Prometheus AlertManager rule
- alert: AgentHighErrorRate
  expr: |
    sum(rate(agent_errors_total{error_kind!="OK"}[5m]))
    / sum(rate(agent_requests_total[5m])) > 0.1
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Agent error rate exceeds 10%"
```

## 7. API Reference

### 7.1 Exports from agent_platform.core

```python
from agent_platform.core import (
    # Logging & Observability (Phase 3.1)
    ErrorKind,
    log_event,
    derive_error_kind,
    create_error_response,
)
```

### 7.2 ErrorKind Enum

```python
class ErrorKind(str, Enum):
    OK = "OK"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    SOT_VIOLATION = "SOT_VIOLATION"
    LLM_ERROR = "LLM_ERROR"
    INFRA_ERROR = "INFRA_ERROR"
    AGENT_ERROR = "AGENT_ERROR"
    UNKNOWN = "UNKNOWN"
```

### 7.3 log_event Signature

```python
def log_event(
    run_id: str,
    agent_name: str,
    flow: str,
    stage: str,
    success: bool,
    error_kind: ErrorKind = ErrorKind.OK,
    message: str = "",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    ...
```

### 7.4 derive_error_kind Signature

```python
def derive_error_kind(error: Exception) -> ErrorKind:
    ...
```

### 7.5 create_error_response Signature

```python
def create_error_response(
    error: Exception,
    run_id: str,
    agent_name: str,
    flow: str = "unknown",
) -> Dict[str, Any]:
    ...
```

## 8. Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2025-12-03 | Initial release (Phase 3.1) |

---

**Document Status**: Production
**Phase**: 3.1
**Baseline**: Agent Layer Freeze v1.0, MASTER.md v4.4
