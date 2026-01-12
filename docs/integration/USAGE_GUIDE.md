# AI 代码工厂使用指南

> **版本**: v5.1  
> **更新日期**: 2026-01-09  
> **状态**: ✅ 生产就绪

## 目录

1. [快速开始](#快速开始)
2. [环境准备](#环境准备)
3. [基本使用](#基本使用)
4. [工作流类型](#工作流类型)
5. [高级用法](#高级用法)
6. [配置选项](#配置选项)
7. [示例场景](#示例场景)
8. [故障排查](#故障排查)

---

## 快速开始

### 最简单的使用方式

```python
from agents.skills.code_factory.core.orchestrator import CodeFactoryOrchestrator

# 创建编排器
orchestrator = CodeFactoryOrchestrator()

# 执行工作流
result = orchestrator.execute(
    requirement="创建一个用户管理功能，包括列表、创建、编辑、删除",
    workflow_type="full_stack_development"
)

# 查看结果
print(f"状态: {result['status']}")
if result['status'] == 'completed':
    for exec_result in result['execution_results']:
        print(f"代理 {exec_result['agent_id']}: {exec_result['output'][:100]}...")
```

---

## 环境准备

### 1. 安装依赖

```bash
# 安装后端依赖（包含 anthropic）
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

创建或编辑 `.env` 文件：

```bash
# Anthropic API 密钥（可选，无密钥时使用模拟模式）
ANTHROPIC_API_KEY=sk-ant-...

# 缓存配置（可选）
CACHE_ENABLED=true
CACHE_SIZE=100

# 项目路径（可选，默认自动检测）
PROJECT_ROOT=/path/to/project

# 日志级别（可选）
LOG_LEVEL=INFO
```

### 3. 验证安装

```python
# 测试导入
from agents.skills.code_factory.core.orchestrator import CodeFactoryOrchestrator
from agents.skills.skill_system.config import get_config

# 检查配置
config = get_config()
print(f"配置验证: {config.validate()}")
print(f"缓存启用: {config.cache_enabled}")
```

---

## 基本使用

### 方式一：使用编排器（推荐）

```python
from agents.skills.code_factory.core.orchestrator import CodeFactoryOrchestrator

# 1. 创建编排器
orchestrator = CodeFactoryOrchestrator()

# 2. 执行工作流
result = orchestrator.execute(
    requirement="你的需求描述",
    workflow_type="full_stack_development"  # 或其他工作流类型
)

# 3. 处理结果
if result['status'] == 'completed':
    print("✅ 执行成功")
    for exec_result in result['execution_results']:
        agent_id = exec_result['agent_id']
        output = exec_result.get('output', '')
        print(f"\n代理 {agent_id} 的输出:")
        print(output[:500])  # 显示前 500 字符
elif result['status'] == 'partial_failure':
    print("⚠️ 部分失败")
    for exec_result in result['execution_results']:
        if not exec_result['success']:
            print(f"❌ {exec_result['agent_id']}: {exec_result.get('error')}")
```

### 方式二：直接使用代理执行器

```python
from agents.skills.code_factory.core.agent_executor import AgentExecutor
from agents.skills.skill_system.wshobson_agent_loader import WshobsonAgentLoader

# 1. 加载代理
loader = WshobsonAgentLoader()
agent = loader.load_agent("backend-architect")

# 2. 创建执行器
executor = AgentExecutor()

# 3. 执行任务
result = executor.execute_agent(
    agent=agent,
    requirement="创建用户登录 API",
    context={}
)

# 4. 查看结果
if result.success:
    print(f"✅ 执行成功")
    print(f"输出: {result.output}")
    print(f"Token 使用: {result.tokens_used}")
    print(f"执行时间: {result.execution_time:.2f}s")
else:
    print(f"❌ 执行失败: {result.error}")
```

---

## 工作流类型

### 1. 全栈功能开发

```python
result = orchestrator.execute(
    requirement="创建用户管理功能，包括列表、创建、编辑、删除",
    workflow_type="full_stack_development"
)
```

**执行顺序**:
1. `system-architect` (Opus 4.5) - 系统架构设计
2. `backend-architect` (Opus 4.5) - 后端 API 开发
3. `frontend-developer` (Sonnet 4.5) - 前端页面开发
4. `code-reviewer` (Opus 4.5) - 代码审查
5. `test-automator` (Sonnet 4.5) - 测试生成

### 2. 代码审查

```python
result = orchestrator.execute(
    requirement="审查用户管理模块的代码质量",
    workflow_type="code_review"
)
```

**执行模式**: 并行执行
- `code-reviewer` (Opus 4.5) - 代码质量审查
- `security-auditor` (Opus 4.5) - 安全审计
- `performance-engineer` (Opus 4.5) - 性能分析

### 3. Bug 修复

```python
result = orchestrator.execute(
    requirement="修复用户登录功能的 bug",
    workflow_type="bug_fixing"
)
```

**执行顺序**:
1. `debugging-specialist` (Opus 4.5) - 调试分析
2. `code-reviewer` (Opus 4.5) - 代码审查
3. `test-automator` (Sonnet 4.5) - 测试生成

### 4. 性能优化

```python
result = orchestrator.execute(
    requirement="优化用户列表查询性能",
    workflow_type="performance_optimization"
)
```

**执行顺序**:
1. `performance-engineer` (Opus 4.5) - 性能分析
2. `backend-architect` (Opus 4.5) - 优化实现
3. `code-reviewer` (Opus 4.5) - 代码审查

### 5. 系统架构

```python
result = orchestrator.execute(
    requirement="设计微服务架构方案",
    workflow_type="system_architecture"
)
```

**执行顺序**:
1. `system-architect` (Opus 4.5) - 架构设计
2. `code-reviewer` (Opus 4.5) - 架构审查

---

## 高级用法

### 1. 自定义工作流

```python
from agents.skills.code_factory.workflow.presets import WorkflowPresets

# 获取工作流定义
workflow = WorkflowPresets.full_stack_development()

# 修改工作流
workflow['agents'] = [
    {'id': 'backend-architect', 'model': 'opus-4.5'},
    {'id': 'frontend-developer', 'model': 'sonnet-4.5'},
]

# 使用自定义工作流
orchestrator = CodeFactoryOrchestrator()
result = orchestrator.execute(
    requirement="创建 API",
    workflow_type="custom"
)
```

### 2. 加载特定代理

```python
from agents.skills.skill_system.wshobson_agent_loader import WshobsonAgentLoader
from agents.skills.code_factory.core.agent_executor import AgentExecutor

# 加载代理
loader = WshobsonAgentLoader()
agent = loader.load_agent("code-reviewer")

# 执行特定代理
executor = AgentExecutor()
result = executor.execute_agent(
    agent=agent,
    requirement="审查这段代码的安全性",
    context={
        "code": """
def login(username, password):
    # 代码内容
    pass
        """
    }
)
```

### 3. 使用技能

```python
from agents.skills.skill_system.wshobson_skill_loader import WshobsonSkillLoader
from agents.skills.skill_system.skill_adapter import SkillAdapter

# 加载技能
skill_loader = WshobsonSkillLoader()
skill = skill_loader.load_skill("backend-development")

# 适配技能
adapter = SkillAdapter()
adapted_skill = adapter.adapt_skill(skill)

# 查看技能指令
print(adapted_skill.instructions)
```

### 4. 性能监控

```python
from agents.skills.code_factory.core.monitoring import get_monitor

# 获取监控器
monitor = get_monitor()

# 执行一些任务
orchestrator = CodeFactoryOrchestrator()
result = orchestrator.execute(
    requirement="创建用户管理功能",
    workflow_type="full_stack_development"
)

# 查看性能指标
metrics = monitor.get_metrics()
print(f"执行次数: {metrics['execution_count']}")
print(f"总 Token: {metrics['total_tokens']}")
print(f"平均时间: {metrics['avg_time']:.2f}s")
print(f"错误率: {metrics['error_rate']:.2%}")
print(f"缓存命中率: {metrics['cache_hit_rate']:.2%}")

# 查看代理执行统计
print("\n代理执行统计:")
for agent_id, count in metrics['agent_executions'].items():
    print(f"  {agent_id}: {count} 次")

# 查看模型使用统计
print("\n模型使用统计:")
for model, tokens in metrics['model_usage'].items():
    print(f"  {model}: {tokens} tokens")
```

### 5. 配置管理

```python
from agents.skills.skill_system.config import get_config

# 获取配置
config = get_config()

# 查看配置
print(f"项目根目录: {config.project_root}")
print(f"缓存启用: {config.cache_enabled}")
print(f"缓存大小: {config.cache_size}")
print(f"最大并发: {config.max_concurrent_agents}")

# 验证配置
if not config.validate():
    print("⚠️ 配置验证失败")
```

### 6. 缓存管理

```python
from agents.skills.skill_system.cache import AgentCache, SkillCache

# 创建缓存
agent_cache = AgentCache(max_size=100)
skill_cache = SkillCache(max_size=100)

# 查看缓存统计
agent_stats = agent_cache.stats()
print(f"代理缓存大小: {agent_stats['size']}")
print(f"代理缓存命中率: {agent_stats['hit_rate']:.2%}")

skill_stats = skill_cache.stats()
print(f"技能缓存大小: {skill_stats['size']}")
print(f"技能缓存命中率: {skill_stats['hit_rate']:.2%}")

# 清空缓存
agent_cache.clear()
skill_cache.clear()
```

---

## 配置选项

### 环境变量配置

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | 无 | `sk-ant-...` |
| `CACHE_ENABLED` | 是否启用缓存 | `true` | `true` / `false` |
| `CACHE_SIZE` | 缓存大小 | `100` | `200` |
| `PROJECT_ROOT` | 项目根目录 | 自动检测 | `/path/to/project` |
| `WSHOBSON_AGENTS_PATH` | wshobson/agents 路径 | `external/wshobson-agents` | `/path/to/wshobson-agents` |
| `LOG_LEVEL` | 日志级别 | `INFO` | `DEBUG` / `INFO` / `WARNING` |
| `MAX_CONCURRENT_AGENTS` | 最大并发代理数 | `5` | `10` |
| `REQUEST_TIMEOUT` | 请求超时（秒） | `60` | `120` |

### 代码配置

```python
from agents.skills.skill_system.config import Config

# 创建自定义配置
config = Config()
config.cache_enabled = True
config.cache_size = 200
config.max_concurrent_agents = 10

# 验证配置
if config.validate():
    print("配置有效")
```

---

## 示例场景

### 场景 1: 创建完整的 CRUD 功能

```python
from agents.skills.code_factory.core.orchestrator import CodeFactoryOrchestrator

orchestrator = CodeFactoryOrchestrator()

result = orchestrator.execute(
    requirement="""
    创建一个完整的用户管理功能：
    1. 后端 API：列表、创建、编辑、删除、详情
    2. 前端页面：用户列表、创建表单、编辑表单、详情页
    3. 数据验证：用户名唯一、邮箱格式验证
    4. 权限控制：只有管理员可以删除用户
    """,
    workflow_type="full_stack_development"
)

if result['status'] == 'completed':
    print("✅ 功能创建成功")
    # 查看每个代理的输出
    for exec_result in result['execution_results']:
        print(f"\n{'='*50}")
        print(f"代理: {exec_result['agent_id']}")
        print(f"状态: {'✅ 成功' if exec_result['success'] else '❌ 失败'}")
        if exec_result.get('output'):
            print(f"输出预览: {exec_result['output'][:200]}...")
```

### 场景 2: 代码审查和安全审计

```python
result = orchestrator.execute(
    requirement="""
    审查以下代码的安全性和质量：
    1. 检查 SQL 注入风险
    2. 检查 XSS 漏洞
    3. 检查权限控制
    4. 检查代码规范
    """,
    workflow_type="code_review"
)

# 并行执行多个审查代理
for exec_result in result['execution_results']:
    agent_id = exec_result['agent_id']
    if exec_result['success']:
        print(f"\n{agent_id} 审查结果:")
        print(exec_result['output'])
    else:
        print(f"\n{agent_id} 审查失败: {exec_result.get('error')}")
```

### 场景 3: 性能优化

```python
result = orchestrator.execute(
    requirement="""
    优化用户列表查询性能：
    1. 当前问题：查询 1000 条记录需要 5 秒
    2. 目标：优化到 1 秒以内
    3. 要求：保持数据一致性
    """,
    workflow_type="performance_optimization"
)

# 查看性能分析结果
for exec_result in result['execution_results']:
    if exec_result['agent_id'] == 'performance-engineer':
        print("性能分析结果:")
        print(exec_result['output'])
```

### 场景 4: Bug 修复

```python
result = orchestrator.execute(
    requirement="""
    修复用户登录功能的问题：
    1. 问题：用户输入错误密码 3 次后，账户被锁定，但解锁逻辑有问题
    2. 错误信息：解锁后仍然提示账户被锁定
    3. 要求：修复 bug 并添加测试
    """,
    workflow_type="bug_fixing"
)

# 查看调试结果
for exec_result in result['execution_results']:
    if exec_result['agent_id'] == 'debugging-specialist':
        print("调试分析:")
        print(exec_result['output'])
```

---

## 故障排查

### 问题 1: 导入错误

**错误**: `ImportError: cannot import name 'AgentExecutor'`

**解决**:
```bash
# 确保在项目根目录
cd /path/to/AI_ad_spend02

# 检查 Python 路径
python -c "import sys; print(sys.path)"

# 重新安装依赖
pip install -r backend/requirements.txt
```

### 问题 2: API 密钥未设置

**错误**: `Using mock execution for agent ... (no API client)`

**解决**:
```bash
# 设置环境变量
export ANTHROPIC_API_KEY=sk-ant-...

# 或在 .env 文件中设置
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
```

### 问题 3: 代理加载失败

**错误**: `Agent 'xxx' not found`

**解决**:
```python
# 检查代理是否存在
from agents.skills.skill_system.wshobson_agent_loader import WshobsonAgentLoader

loader = WshobsonAgentLoader()
agent = loader.load_agent("backend-architect")

if agent is None:
    print("代理不存在，检查 agent_mapping.yaml")
else:
    print(f"代理加载成功: {agent.name}")
```

### 问题 4: 缓存问题

**错误**: 缓存命中率低

**解决**:
```python
# 检查缓存配置
from agents.skills.skill_system.config import get_config

config = get_config()
print(f"缓存启用: {config.cache_enabled}")
print(f"缓存大小: {config.cache_size}")

# 如果缓存未启用，设置环境变量
# CACHE_ENABLED=true
```

### 问题 5: 执行超时

**错误**: `Request timeout`

**解决**:
```bash
# 增加超时时间
export REQUEST_TIMEOUT=120

# 或在代码中设置
from agents.skills.skill_system.config import get_config
config = get_config()
config.request_timeout = 120
```

---

## 最佳实践

### 1. 需求描述要清晰

✅ **好的需求**:
```
创建一个用户管理功能，包括：
1. 后端 API：列表（分页、搜索）、创建、编辑、删除
2. 前端页面：用户列表、创建表单、编辑表单
3. 数据验证：用户名唯一、邮箱格式
4. 权限控制：只有管理员可以删除
```

❌ **不好的需求**:
```
做个用户管理
```

### 2. 选择合适的工作流

- **全栈开发**: 创建新功能
- **代码审查**: 审查现有代码
- **Bug 修复**: 修复已知问题
- **性能优化**: 优化性能瓶颈
- **系统架构**: 架构设计

### 3. 监控性能指标

```python
# 定期查看性能指标
from agents.skills.code_factory.core.monitoring import get_monitor

monitor = get_monitor()
metrics = monitor.get_metrics()

# 如果错误率高，检查日志
if metrics['error_rate'] > 0.1:
    print("⚠️ 错误率过高，请检查日志")
```

### 4. 使用缓存提升性能

```python
# 确保缓存启用
from agents.skills.skill_system.config import get_config

config = get_config()
if not config.cache_enabled:
    print("建议启用缓存以提升性能")
```

### 5. 处理执行结果

```python
result = orchestrator.execute(...)

# 检查状态
if result['status'] == 'completed':
    # 处理成功结果
    pass
elif result['status'] == 'partial_failure':
    # 处理部分失败
    for exec_result in result['execution_results']:
        if not exec_result['success']:
            # 记录错误或重试
            print(f"失败: {exec_result['agent_id']} - {exec_result.get('error')}")
```

---

## 参考资源

- [整合文档](./WSHOBSON_AGENTS_INTEGRATION.md) - wshobson/agents 整合说明
- [版本对比](./VERSION_COMPARISON.md) - 版本改进对比
- [P0/P1 修复总结](./P0_P1_IMPLEMENTATION_SUMMARY.md) - 最新修复说明
- [代码工厂 README](../../agents/skills/code_factory/README.md) - 完整文档

---

*最后更新: 2026-01-09 | 版本: v5.1*

