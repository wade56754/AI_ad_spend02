# DeepRouter 模型配置指南

## 如何设置模型为 Opus（或其他模型）

DeepRouter 支持通过多种方式设置模型。以下是三种配置方法：

### 方法 1: 环境变量配置（推荐，全局默认）

在 `.env.local` 文件中设置：

```env
LLM_BACKEND=deeprouter
DEEPROUTER_CLAUDE_TOKEN=你的_token
DEEPROUTER_BASE_URL=https://deeprouter.top
DEEPROUTER_MODEL=claude-opus-4-20250514  # 设置为你想要的模型
```

这样配置后，所有通过 `get_llm_client()` 获取的客户端都会使用这个模型。

### 方法 2: 代码中临时指定（单次调用）

如果只是某次调用需要使用不同的模型，可以在 `generate()` 方法中指定：

```python
from agent_platform.llm.factory import get_llm_client

client = get_llm_client()

# 临时使用 opus 模型
response = client.generate(
    system="你是一个助手",
    user="请回答问题",
    model="claude-opus-4-20250514",  # 临时指定模型
    max_tokens=1000
)
```

### 方法 3: 直接创建客户端时指定

如果需要为特定用途创建独立的客户端实例：

```python
from agent_platform.llm.deeprouter_client import DeepRouterLLMClient
import os

client = DeepRouterLLMClient(
    token=os.environ.get("DEEPROUTER_CLAUDE_TOKEN"),
    model="claude-opus-4-20250514"  # 指定模型
)

response = client.generate(system="...", user="...")
```

## 常见模型名称

根据 DeepRouter 和 Anthropic 的命名规范，常见的模型名称包括：

### Sonnet 系列（平衡性能和成本）
- `claude-sonnet-4-20250514` (默认)
- `claude-3-5-sonnet-20241022`
- `claude-3-5-sonnet-latest`
- `claude-3-5-sonnet-20240620`
- `claude-3-sonnet-20240229`

### Opus 系列（最强性能）
- `claude-opus-4-20250514`
- `claude-3-opus-20240229`
- `claude-3-5-opus-latest`

### Haiku 系列（最快最便宜）
- `claude-3-haiku-20240307`
- `claude-3-5-haiku-20241022`
- `claude-3-5-haiku-latest`

## 检查可用模型

运行以下脚本可以测试你的账户支持哪些模型：

```bash
python test_deeprouter_list_models.py
```

## 常见问题

### Q: 遇到 "无可用渠道" 错误怎么办？

**A:** 这表示你的 DeepRouter 账户在当前分组下没有购买或配置该模型的渠道。解决方法：

1. 登录 DeepRouter 控制台，检查已购买的模型渠道
2. 联系 DeepRouter 客服开通相应模型的权限
3. 确认模型名称是否正确（可能需要查看 DeepRouter 文档中的确切名称）

### Q: 如何知道我的账户支持哪些模型？

**A:** 有几种方法：

1. **查看 DeepRouter 控制台**：登录后查看"模型管理"或"渠道管理"
2. **运行测试脚本**：使用 `test_deeprouter_list_models.py` 测试常见模型
3. **查看 API 文档**：DeepRouter 可能提供模型列表 API

### Q: 模型设置的优先级是什么？

**A:** 优先级从高到低：

1. `generate()` 方法中的 `model` 参数（最高优先级）
2. 创建客户端时传入的 `model` 参数
3. 环境变量 `DEEPROUTER_MODEL`
4. 默认值 `claude-sonnet-4-20250514`（最低优先级）

### Q: 可以在运行时动态切换模型吗？

**A:** 可以。每次调用 `generate()` 时都可以指定不同的模型：

```python
client = get_llm_client()

# 第一次使用 sonnet
response1 = client.generate(..., model="claude-sonnet-4-20250514")

# 第二次使用 opus
response2 = client.generate(..., model="claude-opus-4-20250514")
```

## 示例：完整配置

`.env.local` 文件示例：

```env
# LLM Backend
LLM_BACKEND=deeprouter

# DeepRouter 配置
DEEPROUTER_BASE_URL=https://deeprouter.top
DEEPROUTER_CLAUDE_TOKEN=你的_deeprouter_token

# 模型配置（根据需要修改）
DEEPROUTER_MODEL=claude-opus-4-20250514  # 使用 Opus 模型
# DEEPROUTER_MODEL=claude-sonnet-4-20250514  # 或使用 Sonnet 模型
# DEEPROUTER_MODEL=claude-3-haiku-20240307  # 或使用 Haiku 模型
```

代码使用示例：

```python
from agent_platform.llm.factory import get_llm_client, reset_client

# 重置客户端以加载最新配置
reset_client()

# 获取客户端（会自动使用 .env.local 中配置的模型）
client = get_llm_client()

# 使用默认模型（.env.local 中配置的）
response1 = client.generate(
    system="你是一个助手",
    user="请介绍你自己"
)

# 临时切换到其他模型
response2 = client.generate(
    system="你是一个助手",
    user="请介绍你自己",
    model="claude-3-haiku-20240307"  # 临时使用 Haiku
)
```

