# Agents 子系统

AI Agent 子系统提供代码生成、文档处理、测试自动化等能力。

## 目录

- [LLM 后端选择策略](#llm-后端选择策略)
- [架构概览](#架构概览)
- [开发指南](#开发指南)

---

## LLM 后端选择策略

### 后端优先级

系统采用双后端策略，按以下优先级自动选择 LLM 后端：

1. **Anthropic 官方 API**（首选）
   - 当环境变量 `ANTHROPIC_API_KEY` 存在且非空时启用
   - 使用 `anthropic` Python 包提供的官方客户端
   - 支持自定义 API 网关（通过 `ANTHROPIC_BASE_URL` 环境变量）

2. **Claude Code CLI 适配器**（备选）
   - 当 `ANTHROPIC_API_KEY` 未设置时自动回退
   - 要求本机已安装并配置 `claude` CLI（在 PATH 中可调用）
   - 适用于 Claude Max 订阅用户

3. **错误处理**
   - 当两种后端都不可用时，系统抛出 `RuntimeError`
   - 错误信息包含清晰的解决建议（设置 API Key 或安装 CLI）

### 配置要求

#### 环境变量

- **`ANTHROPIC_API_KEY`**（可选）
  - 类型：字符串
  - 说明：Anthropic API 密钥，存在时优先使用官方 API
  - 获取方式：从 [Anthropic Console](https://console.anthropic.com/) 获取

- **`ANTHROPIC_BASE_URL`**（可选）
  - 类型：字符串（URL）
  - 说明：自定义 API 基础 URL，用于代理或自定义网关
  - 示例：`https://api.example.com/v1`

#### CLI 依赖

- **Claude Code CLI**
  - 安装命令：`npm install -g @anthropic-ai/claude-code`
  - 验证方式：在终端运行 `claude --version`，应返回版本号
  - 要求：CLI 必须在系统 PATH 中可调用

### 测试契约

LLM 后端选择策略的行为契约由以下测试用例定义：

**测试文件**：`agents/tests/test_llm_client.py`

**关键测试用例**：

- `test_uses_anthropic_when_api_key_set`
  - 验证：当 `ANTHROPIC_API_KEY` 设置时，使用 Anthropic API 后端
  - 断言：`get_backend_type()` 返回 `"anthropic_api"`

- `test_uses_claude_code_when_no_api_key`
  - 验证：当 `ANTHROPIC_API_KEY` 未设置但 CLI 可用时，使用 Claude Code CLI 后端
  - 断言：`get_backend_type()` 返回 `"claude_code"`

- `test_raises_error_when_no_backend_available`
  - 验证：当两种后端都不可用时，抛出 `RuntimeError`
  - 断言：错误信息包含 `"无法初始化 LLM 客户端"` 和 `"ANTHROPIC_API_KEY"`

**SoT 声明**：上述测试用例共同定义了 LLM 后端选择策略的官方行为契约。任何实现变更必须确保这些测试通过。

---

## 架构概览

### 核心组件

- **`agent_core/`** - Agent 核心实现（orchestrator, be_agent, fe_agent 等）
- **`tools/`** - 工具模块（LLM 客户端、文件系统工具、Supabase 工具等）
- **`skills/`** - Skill 注册表（后端开发、文档处理、测试等技能）
- **`tests/`** - 测试套件

### 相关文档

- **系统架构**：`docs/1.overview/MASTER.md` - Agent Layer 章节
- **Agent 协议**：`docs/6.agent-layer/SUBAGENT_PROTOCOL.md`
- **安全规范**：`docs/6.agent-layer/AGENT_SECURITY_SPEC.md`

---

## 开发指南

### 运行测试

```bash
# 运行所有 Agent 测试
python -m pytest agents/tests -v

# 运行 LLM 客户端测试（验证后端选择策略）
python -m pytest agents/tests/test_llm_client.py -v --tb=short
```

### 添加新 Skill

参考 `agents/skills/` 目录下的现有实现，遵循 Skill 注册表规范。

---

**最后更新**：2025-12-02  
**对齐版本**：Agent Layer Freeze v1.0, MASTER.md v3.6

