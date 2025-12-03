# Flow Presets Configuration

Flow Presets 允许你为常用的 OrchestratorAgent 流程定义标准参数模板，避免每次手动输入参数。

## 快速开始

### 1. 查看可用预设

```bash
python -m agent_platform.cli list-presets
```

### 2. 使用预设运行流程

```bash
# 使用预设（推荐）
python -m agent_platform.cli orch --preset finance_profit_backend_full --mode execute

# 覆盖预设中的任务描述
python -m agent_platform.cli orch --preset finance_profit_backend_full \
  --task "Custom task description" --mode execute
```

## 预设配置文件格式

预设配置文件位于 `agents/config/` 目录，使用 YAML 格式：

```yaml
flows:
  preset_name:
    flow: be_then_test          # 必需的 flow 名称
    task: "Task description"    # 任务描述
    module: module_name         # 模块名称（可选）
    target_files:               # 目标文件列表
      - backend/routers/api.py
      - backend/services/service.py
```

## 创建新预设

1. 在 `agents/config/` 目录创建或编辑 YAML 文件（例如 `flows_my_module.yaml`）
2. 定义预设：

```yaml
flows:
  my_module_backend_full:
    flow: be_then_test
    task: "Implement my_module API and tests"
    module: my_module
    target_files:
      - backend/routers/my_module.py
      - backend/services/my_module_service.py
      - backend/tests/api/test_my_module.py
```

3. 使用新预设：

```bash
python -m agent_platform.cli orch --preset my_module_backend_full --mode execute
```

## CLI 参数覆盖

使用 `--preset` 时，可以通过 CLI 参数覆盖预设中的值：

- `--task`: 覆盖任务描述
- `--target-files`: 追加到预设的文件列表
- `--module`: 覆盖模块名称
- `--flow`: 覆盖 flow 类型（不推荐）

示例：

```bash
# 只覆盖任务描述
python -m agent_platform.cli orch --preset finance_profit_backend_full \
  --task "Fix finance_profit API bugs" --mode execute

# 追加额外文件
python -m agent_platform.cli orch --preset finance_profit_backend_full \
  --target-files backend/models/finance.py --mode execute
```

## 现有预设

### finance_profit 模块

- `finance_profit_backend_full`: 完整的后端 API + 测试流程
- `finance_profit_backend_only`: 仅后端 API 生成
- `finance_profit_test_only`: 仅测试生成

## 技术细节

- 预设加载器会搜索 `agents/config/*.yaml` 文件
- 预设名称必须唯一（跨所有 YAML 文件）
- CLI 参数覆盖优先级高于预设值
- `target_files` 会合并（预设文件在前，CLI 文件在后）

