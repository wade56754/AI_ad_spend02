# Agent Platform LLM 后端架构说明（SoT）

**版本**: v1.0  
**最后更新**: 2025-12-03  
**文档类型**: Single Source of Truth (SoT)  
**维护者**: AI_ad_spend02 项目组

---

## 1. 概述

### 1.1 文档作用

本文档是 AI_ad_spend02 项目中 **LLM 后端架构设计与 DeepRouter 集成方案** 的单一事实来源（Single Source of Truth）。

本文档统一说明：
- 支持的 LLM 后端类型及其选择优先级
- DeepRouter 代理集成方案（推荐模式）
- 环境变量配置与自动转换规则
- AnthropicLLMClient 的行为与约束
- 测试与验证流程
- 常见问题排查路径

### 1.2 目标读者

- **后端/前端开发工程师**：了解如何在代码中使用 LLM 客户端
- **测试工程师**：了解如何运行测试与验证脚本
- **运维人员**：了解环境配置与故障排查
- **未来接手项目的人员**：快速理解 LLM 后端架构

### 1.3 文档结构

1. 概述（当前章节）
2. LLM 后端类型与优先级策略
3. DeepRouter + Anthropic 模式（推荐模式）
4. 环境变量与 .env.local 约定
5. AnthropicLLMClient 行为说明
6. 测试与验证流程
7. Orchestrator 与多 Agent 使用建议
8. 常见问题与排查建议

---

## 2. LLM 后端类型与优先级策略

### 2.1 支持的后端类型

当前项目支持以下三种 LLM 后端类型：

| 后端类型 | 标识符 | 实现类 | 说明 |
|---------|--------|--------|------|
| **Anthropic API（推荐）** | `anthropic_api` | `AnthropicLLMClient` | 通过 Anthropic 官方 SDK 调用，支持官方 API 和第三方代理（如 DeepRouter） |
| **Claude Code CLI** | `claude_code` | `ClaudeCodeLLMClient` | 通过 Claude Code CLI 适配层调用，需要本地安装 Claude Code |
| **Dummy（占位）** | `dummy` | `DummyLLMClient` | 用于无 API key/离线环境，默认 `raise_on_call=True` 会抛出清晰错误提示 |

### 2.2 后端选择优先级

`agent_platform.llm.factory.get_llm_client()` 的后端选择逻辑如下：

#### 优先级 1：Anthropic API（推荐）

**条件**：
- 存在 `ANTHROPIC_API_KEY`（或通过自动转换获得）
- 已安装 `anthropic` Python 包

**行为**：
- 创建 `AnthropicLLMClient` 实例
- 如果配置了 `ANTHROPIC_BASE_URL`（如 `https://deeprouter.top`），则通过代理调用
- 如果未配置 `ANTHROPIC_BASE_URL`，则使用官方端点 `https://api.anthropic.com`

**后端类型标识**：`anthropic_api`

#### 优先级 2：Claude Code CLI（回退）

**条件**：
- 优先级 1 不满足（无 API key 或未安装 anthropic 包）
- 本地已安装 Claude Code CLI（通过 `npm install -g @anthropic-ai/claude-code`）

**行为**：
- 创建 `ClaudeCodeLLMClient` 实例
- 通过 CLI 适配层调用 Claude Code

**后端类型标识**：`claude_code`

#### 优先级 3：DummyLLMClient（兜底）

**条件**：
- 优先级 1 和 2 都不满足

**行为**：
- 创建 `DummyLLMClient(raise_on_call=True)` 实例
- 调用 `generate()` 时会抛出 `RuntimeError`，包含清晰的配置提示信息

**后端类型标识**：`dummy`

### 2.3 显式指定后端类型

可以通过环境变量 `LLM_BACKEND` 显式指定后端类型：

```bash
# 显式指定使用 DeepRouter 后端（但推荐使用 ANTHROPIC_API_KEY + ANTHROPIC_BASE_URL）
LLM_BACKEND=deeprouter
```

**注意**：即使设置了 `LLM_BACKEND=deeprouter`，如果同时存在 `ANTHROPIC_API_KEY` + `ANTHROPIC_BASE_URL`（指向 DeepRouter），系统仍会优先使用 `AnthropicLLMClient`（Anthropic API 风格），这是推荐方式。

---

## 3. DeepRouter + Anthropic 模式（推荐模式）

### 3.1 DeepRouter 定位

DeepRouter 在本项目中作为 **Anthropic Messages API 的代理网关**，用于：
- 降低 API 调用成本
- 提供统一的 Claude 模型访问入口
- 支持多种 Claude 模型（Sonnet、Opus、Haiku 等）

### 3.2 消息路径概览

```
业务 Agent / Orchestrator
    ↓
AnthropicLLMClient (agent_platform/llm/anthropic_client.py)
    ↓
anthropic.Anthropic SDK (官方 Python SDK)
    ↓
DeepRouter base_url (https://deeprouter.top)
    ↓
Claude 模型 (由 DEEPROUTER_MODEL 指定)
```

### 3.3 模型选择

#### 模型名称来源（优先级从高到低）

1. **调用时指定**：`client.generate(..., model="claude-opus-4-20250514")`
2. **环境变量**：`DEEPROUTER_MODEL=claude-sonnet-4-20250514`
3. **默认值**：`claude-sonnet-4-20250514`（仅作为占位值，不限制其他模型）

#### 模型配置建议

- **当前默认**：`claude-sonnet-4-20250514`（Sonnet-4 模型）
- **可切换模型**：架构上支持任意 Claude 模型名称，例如：
  - `claude-opus-4-20250514`（Opus-4）
  - `claude-3-5-sonnet-20241022`（Sonnet-3.5）
  - `claude-3-opus-20240229`（Opus-3）
  - `claude-3-haiku-20240307`（Haiku-3）

#### 模型可用性确认

在切换模型前，建议：
1. 调用 DeepRouter 的 `/v1/models` 接口确认可用模型列表
2. 查看 DeepRouter 控制台确认账户权限
3. 使用 `scripts/test_deeprouter_anthropic.py` 验证新模型是否可用

---

## 4. 环境变量与 .env.local 约定

### 4.1 推荐配置（新项目）

在 `.env.local` 文件中配置以下变量：

```bash
# Anthropic API Key（DeepRouter token 或官方 API key）
ANTHROPIC_API_KEY=cr_xxxxxxxxxxxxxxxxxxxxx

# Base URL（DeepRouter 代理或官方端点）
ANTHROPIC_BASE_URL=https://deeprouter.top

# 模型名称（可选，默认 claude-sonnet-4-20250514）
DEEPROUTER_MODEL=claude-sonnet-4-20250514
```

**说明**：
- `ANTHROPIC_API_KEY`：若使用 DeepRouter 代理，填写 DeepRouter 提供的 token；若使用官方 API，填写官方 API key
- `ANTHROPIC_BASE_URL`：DeepRouter 代理为 `https://deeprouter.top`；官方 API 为 `https://api.anthropic.com`（或省略此变量）
- `DEEPROUTER_MODEL`：当前建议默认 `claude-sonnet-4-20250514`，可按需修改为其他 Claude 模型

### 4.2 自动转换规则（兼容旧配置）

为了兼容旧配置，系统支持自动转换：

| 旧变量名 | 自动转换为 | 说明 |
|---------|-----------|------|
| `DEEPROUTER_CLAUDE_TOKEN` | `ANTHROPIC_API_KEY` | 如果 `ANTHROPIC_API_KEY` 不存在，则从 `DEEPROUTER_CLAUDE_TOKEN` 读取 |
| `DEEPROUTER_BASE_URL` | `ANTHROPIC_BASE_URL` | 如果 `ANTHROPIC_BASE_URL` 不存在，则从 `DEEPROUTER_BASE_URL` 读取 |

**转换时机**：
- 在 `agent_platform.llm.factory._load_anthropic_api_key()` 中自动转换
- 在 `agent_platform.llm.factory._load_anthropic_base_url()` 中自动转换
- 转换后会在日志中提示：`"Auto-converting DEEPROUTER_CLAUDE_TOKEN to ANTHROPIC_API_KEY for DeepRouter compatibility"`

**建议**：新项目直接使用 `ANTHROPIC_API_KEY` 和 `ANTHROPIC_BASE_URL`，无需使用旧变量名。

### 4.3 配置加载优先级

环境变量和配置文件的加载优先级（从高到低）：

1. **系统环境变量**（最高优先级，不会被本地文件覆盖）
2. **仓库根目录 `.env.local` 文件**
3. **仓库根目录 `local_config/anthropic.json` 文件**

### 4.4 .env.local 示例（占位符）

```bash
# ============================================
# LLM 后端配置（DeepRouter + Anthropic）
# ============================================

# DeepRouter Claude Token（自动转换为 ANTHROPIC_API_KEY）
# 注意：请替换为你的实际 token，不要提交到 git
ANTHROPIC_API_KEY=cr_xxxxxxxxxxxxxxxxxxxxx

# DeepRouter 代理地址
ANTHROPIC_BASE_URL=https://deeprouter.top

# 模型名称（当前默认 Sonnet-4，可按需修改）
DEEPROUTER_MODEL=claude-sonnet-4-20250514

# ============================================
# 可选：显式指定后端类型
# ============================================
# LLM_BACKEND=anthropic_api
```

**安全提示**：
- `.env.local` 文件已加入 `.gitignore`，不会提交到版本控制
- 所有密钥相关内容必须使用占位符，不要使用真实 key

---

## 5. AnthropicLLMClient 行为说明

### 5.1 文件位置

- **实现文件**：`agent_platform/llm/anthropic_client.py`
- **工厂文件**：`agent_platform/llm/factory.py`

### 5.2 初始化行为

`AnthropicLLMClient` 初始化时：
1. 接收 `anthropic.Anthropic` 原生客户端实例（由工厂创建）
2. 自动检测是否使用代理 API（通过检查 `base_url` 是否包含 `deeprouter.top` 等域名）
3. 根据代理类型调整参数格式（某些代理需要 `system` 参数为数组格式）

### 5.3 generate() 方法

#### 方法签名

```python
def generate(
    self,
    system: str,
    user: str,
    *,
    model: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 0.0,
    thinking: bool = False,
    **kwargs: Any,
) -> LLMResponse:
```

#### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `system` | `str` | - | 系统提示词（必需） |
| `user` | `str` | - | 用户消息（必需） |
| `model` | `Optional[str]` | `None` | 模型名称（可选，优先级：参数 > 环境变量 > 默认值） |
| `max_tokens` | `int` | `4096` | 最大生成 token 数 |
| `temperature` | `float` | `0.0` | 温度参数（0.0-1.0） |
| `thinking` | `bool` | `False` | 是否启用思考模式（可选） |
| `**kwargs` | `Any` | - | 其他模型特定参数 |

#### 内部调用流程

1. **模型选择**：调用 `_get_model(model)` 确定最终使用的模型名称
2. **参数规范化**：调用 `_normalize_system_param(system)` 处理代理 API 兼容性
3. **SDK 调用**：调用 `self._client.messages.create(...)`
4. **响应解析**：从 `response.content` 中提取所有 `type=="text"` 的块，拼接成文本
5. **返回封装**：构造 `LLMResponse` 对象，包含 `text`、`model`、`usage`、`raw` 字段

#### 思考模式（thinking）

当 `thinking=True` 时：
- 在请求参数中添加 `thinking` 字段（Anthropic 官方支持）
- 可用于需要模型进行深度思考的场景
- **注意**：思考模式会增加 token 消耗，建议谨慎使用并限制 `budget_tokens`

### 5.4 返回结构

`LLMResponse` 对象包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `text` | `str` | 提取的文本内容（从 `content` 中所有 `type=="text"` 的块拼接） |
| `model` | `str` | 实际使用的模型名称 |
| `usage` | `Dict[str, int]` | Token 使用统计，格式：`{"input_tokens": int, "output_tokens": int}` |
| `raw` | `Any` | 完整的 SDK 返回对象（用于调试） |

### 5.5 错误处理

#### 代理 API 不支持错误

如果检测到代理 API 不支持标准 Anthropic API 格式（错误信息包含 "不支持"、"not supported"、"claude code" 等关键词），会抛出 `LLMClientError`，包含：
- 清晰的错误描述
- 解决方案建议（移除 `ANTHROPIC_BASE_URL` 或使用 Claude Code CLI）

#### 其他错误

其他异常会包装为 `LLMClientError`，包含原始错误信息。

### 5.6 成本与安全约束（建议）

#### max_tokens 控制

- **建议**：在调用侧控制合理的 `max_tokens` 上限
- **默认值**：`4096`（可根据实际需求调整）
- **测试场景**：建议使用较小的 `max_tokens`（如 64-128）以控制成本

#### 思考模式使用

- **默认关闭**：`thinking=False`
- **按需开启**：仅在需要深度思考的场景启用
- **限制预算**：如果启用，建议通过 `budget_tokens` 参数限制思考 token 消耗

#### 系统提示词长度

- **建议**：保持系统提示词简洁，避免不必要的 token 消耗
- **最佳实践**：将详细的规则和约束放在文档中，系统提示词仅包含核心指令

---

## 6. 测试与验证流程

### 6.1 逻辑层测试（不打网）

**目的**：验证 LLM 工厂逻辑、后端选择优先级、配置加载等，不访问真实 API。

**测试文件**：`agent_platform/tests/test_llm_factory.py`

**运行命令**：

```powershell
# 激活虚拟环境
cd D:\git\1108\AI_ad_spend02
.\.venv\Scripts\Activate.ps1

# 运行工厂测试
python -m pytest agent_platform/tests/test_llm_factory.py -v
```

**测试覆盖**：
- 环境变量优先级（env > .env.local > anthropic.json）
- 后端选择逻辑（anthropic_api > claude_code > dummy）
- base_url 注入与规范化
- DeepRouter 自动转换逻辑

### 6.2 DeepRouter Anthropic 连通性测试（会打网）

**目的**：直接使用 `anthropic` SDK + DeepRouter `base_url` 验证 Messages 接口是否可用。

**测试脚本**：`scripts/test_deeprouter_anthropic.py`

**运行命令**：

```powershell
python scripts/test_deeprouter_anthropic.py
```

**测试内容**：
- 加载配置（`ANTHROPIC_API_KEY`、`ANTHROPIC_BASE_URL`、`DEEPROUTER_MODEL`）
- 初始化 `anthropic.Anthropic` 客户端
- 发送极简测试请求（`max_tokens=64`）
- 验证响应文本和 token 使用统计

**预期输出**：
```
============================================================
DeepRouter Anthropic 模式连通性验证
============================================================

1. 加载配置...
   ✓ API Key: 已加载 (长度: 51)
   ✓ Base URL: https://deeprouter.top
   ✓ 模型: claude-sonnet-4-20250514

2. 初始化 Anthropic 客户端...
   ✓ Anthropic SDK 版本: 0.75.0
   ✓ Base URL: https://deeprouter.top (SDK 会自动添加 /v1/messages)
   ✓ 客户端已创建

3. 发送测试请求...
   ...

4. 测试结果:
   ✓ 请求成功！
   模型回复 (前200字): DeepRouter Anthropic 直连正常，连接测试成功。
   Token 使用: 输入 tokens: 71, 输出 tokens: 22, 总计: 93

============================================================
✓ DeepRouter Anthropic 模式验证通过！
============================================================
```

### 6.3 Orchestrator Live Smoke 测试

**目的**：验证 Orchestrator 在 execute 模式下，确实通过 `AnthropicLLMClient`（DeepRouter）完成多 Agent 协作。

**测试文件**：`agent_platform/tests/test_orch_live_smoke.py`

#### Plan 模式测试（0 成本，不打网）

**测试类**：`TestOrchestratorPlanSmoke`

**运行命令**：

```powershell
python -m pytest agent_platform/tests/test_orch_live_smoke.py::TestOrchestratorPlanSmoke::test_plan_be_then_test_flow -v
```

**测试内容**：
- 验证 `flow="be_then_test"` 的执行计划结构
- 验证 `estimated_agents` 包含 `['be', 'test']`
- 验证 plan 步骤信息完整

#### Execute 模式测试（打网，有成本，可跳过）

**测试类**：`TestOrchestratorExecuteLive`

**运行命令**：

```powershell
# 运行所有测试（会自动跳过 execute 测试如果没有 API key）
python -m pytest agent_platform/tests/test_orch_live_smoke.py -v

# 只运行 execute 模式测试（需要 API key）
python -m pytest agent_platform/tests/test_orch_live_smoke.py::TestOrchestratorExecuteLive::test_execute_be_then_test_live -v
```

**测试内容**：
- 验证 `backend_type` 为 `anthropic_api`
- 验证客户端类型为 `AnthropicLLMClient`
- 执行极简的 `be_then_test` 流程（task: "只回答：orch live ok，不要生成或修改任何代码，不要长回复。"）
- 验证返回 `success=True`，`run_id` 存在，`called_agents` 包含 `"be"`

**skipif 机制**：
- 使用 `@pytest.mark.skipif` + `has_llm_api_key()` 检查
- 无 API key 时自动跳过，不影响默认 pytest 结果
- 跳过原因：`"需要 ANTHROPIC_API_KEY 或 DEEPROUTER_CLAUDE_TOKEN 环境变量（会调用 DeepRouter/Anthropic，有真实成本）"`

**成本控制**：
- 使用极简 task 文案
- 较小的 `max_tokens`（由 Agent/Skill 层控制）
- 单次测试 token 消耗约 100-200 tokens

---

## 7. Orchestrator 与多 Agent 使用建议

### 7.1 推荐用法示例

#### be_then_test Flow

用于"后端改动 + 测试补全"的组合任务。

**步骤 1：Plan 模式（0 成本，预览执行计划）**

```powershell
python -m agent_platform.cli orch \
  --flow be_then_test \
  --mode plan \
  --task "为 daily_reports 模块添加新的统计接口" \
  --target-files "backend/routers/daily_reports.py"
```

**步骤 2：Execute 模式（真实执行，有成本）**

```powershell
python -m agent_platform.cli orch \
  --flow be_then_test \
  --mode execute \
  --task "为 daily_reports 模块添加新的统计接口" \
  --target-files "backend/routers/daily_reports.py"
```

### 7.2 其他支持的 Flow

| Flow | 说明 | 使用场景 |
|------|------|----------|
| `be_then_test` | 后端代码生成 → 测试补全 | 后端功能开发 |
| `backend_only` | 仅后端代码生成 | 纯后端重构 |
| `frontend_only` | 仅前端代码生成 | 纯前端重构 |
| `full_pipeline` | 后端 → 前端 → 测试 | 全栈功能开发 |
| `frontend_restructure` | 前端重构流水线（7 步） | 前端架构调整 |
| `gen_backend` | 批量生成多个后端模块 | 批量后端开发 |
| `auto_fix` | 生成 → 测试 → 修复 → 重试循环 | 自动修复流程 |

### 7.3 最佳实践

1. **先 Plan 后 Execute**：使用 `mode=plan` 预览执行计划，确认无误后再执行
2. **控制 Token 消耗**：在 task 描述中明确要求简洁回复，避免不必要的长文本生成
3. **监控 run_id**：使用 `run_id` 追踪整个流程的执行情况
4. **错误处理**：检查返回的 `success` 字段和 `error` 信息，及时处理失败步骤

---

## 8. 常见问题与排查建议

### 8.1 Token 仅支持 Claude Code 模式

**现象**：
```
HTTP 400 - BadRequestError: Error code: 400 - {'error': {'type': '<nil>', 'message': '暂不支持非 claude code 请求 ...'}}
```

**原因**：
- DeepRouter token 可能仅支持 Claude Code CLI 模式，不支持标准 Anthropic Messages API 格式

**排查步骤**：
1. 检查 DeepRouter 控制台，确认 token 类型和支持的接口
2. 查看 DeepRouter 文档，确认当前 token 是否支持 Anthropic API 格式
3. 联系 DeepRouter 客服确认账户权限

**解决方案**：
- **方案 1**：更换支持 Anthropic Messages API 的 token 或通道
- **方案 2**：使用 Claude Code CLI 后端（设置 `LLM_BACKEND=claude_code` 或移除 `ANTHROPIC_API_KEY`）

### 8.2 模型名不在 /v1/models 列表

**现象**：
```
HTTP 400 - BadRequestError: Error code: 400 - {'error': {'type': 'invalid_request_error', 'message': 'Model not found: claude-xxx'}}
```

**原因**：
- `DEEPROUTER_MODEL` 配置的模型名称在当前账户中不可用
- 模型名称拼写错误

**排查步骤**：
1. 调用 DeepRouter 的 `/v1/models` 接口确认可用模型列表：
   ```bash
   curl -H "Authorization: Bearer $ANTHROPIC_API_KEY" \
        https://deeprouter.top/v1/models
   ```
2. 检查 `.env.local` 中的 `DEEPROUTER_MODEL` 配置
3. 查看 DeepRouter 控制台确认账户权限

**解决方案**：
- 调整 `DEEPROUTER_MODEL` 为可用模型名称
- 或联系 DeepRouter 客服开通相应模型的权限

### 8.3 anthropic 包未安装

**现象**：
```
LLMClientError: anthropic package not installed. Run: pip install anthropic
```

**原因**：
- 虚拟环境中未安装 `anthropic` Python 包

**解决方案**：
```powershell
# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 安装 anthropic 包
pip install anthropic
```

**验证**：
```powershell
python -c "import anthropic; print(f'anthropic version: {anthropic.__version__}')"
```

### 8.4 无 API key

**现象**：
- 连通性脚本直接报错：`"错误: 未找到 ANTHROPIC_API_KEY 或 DEEPROUTER_CLAUDE_TOKEN"`
- Live smoke 测试自动 skip：`"SKIPPED [1] ... 需要 ANTHROPIC_API_KEY 或 DEEPROUTER_CLAUDE_TOKEN 环境变量"`

**原因**：
- `.env.local` 中未配置 `ANTHROPIC_API_KEY` 或 `DEEPROUTER_CLAUDE_TOKEN`
- 环境变量未正确加载

**排查步骤**：
1. 检查 `.env.local` 文件是否存在且包含正确的配置
2. 确认环境变量加载优先级（env > .env.local > anthropic.json）
3. 检查 `.env.local` 文件格式（KEY=value，注意不要有多余空格）

**解决方案**：
- 在 `.env.local` 中配置 `ANTHROPIC_API_KEY` 或 `DEEPROUTER_CLAUDE_TOKEN`
- 或在系统环境变量中设置（Windows PowerShell）：
  ```powershell
  $env:ANTHROPIC_API_KEY="cr_xxxxxxxxxxxxxxxxxxxxx"
  ```

### 8.5 后端类型不是 anthropic_api

**现象**：
- `get_backend_type()` 返回 `claude_code` 或 `dummy`
- 期望使用 `AnthropicLLMClient` 但实际使用了其他后端

**排查步骤**：
1. 检查 `ANTHROPIC_API_KEY` 是否存在：
   ```powershell
   python -c "import os; print('ANTHROPIC_API_KEY:', '已设置' if os.environ.get('ANTHROPIC_API_KEY') else '未设置')"
   ```
2. 检查 `anthropic` 包是否安装：
   ```powershell
   python -c "try: import anthropic; print('anthropic 已安装'); except ImportError: print('anthropic 未安装')"
   ```
3. 检查后端类型：
   ```powershell
   python -c "from agent_platform.llm.factory import get_llm_client, get_backend_type, reset_client; reset_client(); client = get_llm_client(); print(f'后端类型: {get_backend_type()}'); print(f'客户端类: {client.__class__.__name__}')"
   ```

**解决方案**：
- 确保 `ANTHROPIC_API_KEY` 已配置
- 确保 `anthropic` 包已安装
- 如果使用 DeepRouter，确保 `ANTHROPIC_BASE_URL` 指向 `https://deeprouter.top`

### 8.6 base_url 路径重复

**现象**：
```
HTTP 404 - 请求路径错误，例如：https://deeprouter.top/v1/v1/messages
```

**原因**：
- `ANTHROPIC_BASE_URL` 配置包含了 `/v1` 路径，而 Anthropic SDK 会自动添加 `/v1/messages`

**解决方案**：
- 配置 `ANTHROPIC_BASE_URL` 时不要包含 `/v1` 路径：
  ```bash
  # 正确
  ANTHROPIC_BASE_URL=https://deeprouter.top
  
  # 错误（会导致路径重复）
  ANTHROPIC_BASE_URL=https://deeprouter.top/v1
  ```
- 系统会自动规范化 base_url（移除尾部的 `/v1`）

### 8.7 测试自动跳过但期望运行

**现象**：
- Live smoke 测试显示 `SKIPPED`，但期望在有 API key 时运行

**排查步骤**：
1. 检查 `has_llm_api_key()` 函数逻辑：
   ```python
   # 检查环境变量
   os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("DEEPROUTER_CLAUDE_TOKEN")
   ```
2. 确认环境变量是否正确加载（可能需要重启终端或重新加载 `.env.local`）

**解决方案**：
- 确保环境变量在测试运行时可用
- 如果使用 `.env.local`，确认文件格式正确且未被 `.gitignore` 排除
- 可以临时在测试中直接设置环境变量：
  ```python
  import os
  os.environ["ANTHROPIC_API_KEY"] = "your_token_here"
  ```

---

## 9. 附录

### 9.1 相关文件清单

| 文件路径 | 说明 |
|---------|------|
| `agent_platform/llm/base.py` | LLM 客户端抽象基类、LLMResponse 模型 |
| `agent_platform/llm/anthropic_client.py` | AnthropicLLMClient 实现 |
| `agent_platform/llm/factory.py` | LLM 工厂、后端选择逻辑 |
| `agent_platform/llm/deeprouter_client.py` | DeepRouterLLMClient 实现（备用） |
| `scripts/test_deeprouter_anthropic.py` | DeepRouter Anthropic 连通性测试脚本 |
| `agent_platform/tests/test_llm_factory.py` | LLM 工厂逻辑测试 |
| `agent_platform/tests/test_orch_live_smoke.py` | Orchestrator live smoke 测试 |

### 9.2 环境变量参考

| 变量名 | 说明 | 必需 | 默认值 |
|--------|------|------|--------|
| `ANTHROPIC_API_KEY` | Anthropic API 密钥（DeepRouter token 或官方 key） | 是（推荐模式） | - |
| `ANTHROPIC_BASE_URL` | API 端点 URL（DeepRouter 或官方） | 否 | `https://api.anthropic.com` |
| `DEEPROUTER_MODEL` | 模型名称 | 否 | `claude-sonnet-4-20250514` |
| `LLM_BACKEND` | 显式指定后端类型 | 否 | `anthropic_api` |
| `DEEPROUTER_CLAUDE_TOKEN` | 旧配置（自动转换为 `ANTHROPIC_API_KEY`） | 否 | - |
| `DEEPROUTER_BASE_URL` | 旧配置（自动转换为 `ANTHROPIC_BASE_URL`） | 否 | - |

### 9.3 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0 | 2025-12-03 | 初始版本，涵盖 DeepRouter + Anthropic Messages 集成方案 |

---

## 10. 联系与反馈

如有问题或建议，请：
1. 查看本文档的"常见问题与排查建议"章节
2. 检查相关测试文件验证配置
3. 联系项目维护者或提交 Issue

---

**文档结束**

