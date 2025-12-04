# Claude Code CLI 执行层修复总结

## 设计说明

### 核心改动

1. **新增 `_run_cli()` 统一执行助手**：
   - 统一使用列表形式的命令参数：`[cli_path] + args`
   - 统一使用 `shell=False`，避免 Windows 上的路径和字符串拼接问题
   - 统一错误处理：将 `FileNotFoundError` 和 `OSError` 转换为 `RuntimeError`，保持错误消息一致性
   - 特殊处理 WinError 206（命令行过长）错误

2. **统一调用方式**：
   - `check_claude_code_available()` 和 `call_claude_code()` 都使用 `_run_cli()`
   - 确保两条路径使用完全相同的 subprocess 调用方式
   - 移除了所有 `shell=True` 和字符串命令拼接逻辑

3. **错误处理增强**：
   - 识别 WinError 206（命令行过长）并给出明确提示
   - 所有 CLI 执行错误统一转换为 `RuntimeError`，保持错误消息格式一致

### 关键改进

- **统一执行路径**：检查函数和执行函数使用相同的 subprocess 调用方式
- **消除 shell=True**：完全移除 shell 模式，避免 Windows 上的路径解析问题
- **错误消息一致性**：所有错误都通过 `_run_cli()` 统一处理，确保错误消息格式一致

## 修改的文件

### `agents/tools/claude_code_adapter.py`

**主要改动**：

1. **新增 `_run_cli()` 函数**（46-132 行）：
   - 统一的 CLI 执行助手
   - 使用列表命令 + `shell=False`
   - 统一的错误处理和日志记录

2. **重构 `call_claude_code()`**（155-366 行）：
   - 移除 `shell=True` 和字符串命令拼接逻辑
   - 使用 `_run_cli()` 统一执行
   - 简化命令构建逻辑

3. **重构 `check_claude_code_available()`**（399-441 行）：
   - 使用 `_run_cli()` 替代直接 `subprocess.run()`
   - 确保与主执行路径使用相同的调用方式

## 验证命令清单

### 1. 基础验证（PowerShell）

```powershell
# 确认 claude 命令可用
claude --version
```

**预期结果**：
- 输出版本信息（如 `2.0.56 (Claude Code)`）

### 2. 适配器检查测试

```powershell
# 测试适配器能否找到 CLI
python -c "from agents.tools.claude_code_adapter import check_claude_code_available; import json; print(json.dumps(check_claude_code_available(), indent=2, ensure_ascii=False))"
```

**预期结果**：
```json
{
  "available": true,
  "path": "D:\\git\\1108\\AI_ad_spend02\\claude.bat",
  "version": "2.0.55 (Claude Code)",
  "error": null
}
```

### 3. Orchestrator 流程测试（dry-run）

```powershell
# 使用预设运行 dry-run（不实际调用 LLM）
python -m agent_platform.cli orch --preset finance_profit_backend_full --mode dry-run
```

**预期结果**：
- ✅ **不再出现** "Claude CLI 可执行文件未找到: claude" 错误
- ✅ 日志中显示：`Using Claude Code CLI (path: D:\...\claude.bat, version: 2.0.55)`
- ✅ BEAgent 开始处理任务
- ⚠️ 如果出现 WinError 206（命令行过长），错误消息应为："Claude CLI 命令过长（Windows 限制）"
- ⚠️ 如果出现其他业务错误，`error_kind` 应为 `LLM_ERROR`，而不是 `AGENT_ERROR` 或 `INFRA_ERROR`

### 4. 完整流程测试（execute，需要 LLM 后端）

```powershell
# 如果配置了 LLM 后端，可以尝试实际执行
python -m agent_platform.cli orch --preset finance_profit_backend_full --mode execute
```

**预期结果**：
- CLI 路径解析成功
- BEAgent 能够调用 Claude Code CLI
- 流程正常执行（或因为其他业务逻辑原因失败，但不应该是 CLI 路径问题）

## 预期日志变化

### 修复前
```
[ERROR] agents.tools.claude_code_adapter: Claude CLI not found at: claude
[ERROR] agents.skills.be_dev_skill: LLM API error: Claude Code CLI call failed: Claude CLI 可执行文件未找到: claude。请确保已正确安装。
```

### 修复后（成功场景）
```
[DEBUG] agents.tools.claude_code_adapter: Resolved CLI path (command): claude -> D:\...\claude.bat
[DEBUG] agents.tools.claude_code_adapter: Executing CLI command: ['D:\\...\\claude.bat', '-p', ...] (total 4 args)
[INFO] agent_platform.llm.factory: Using Claude Code CLI (path: D:\...\claude.bat, version: 2.0.55)
[INFO] agents.agent_core.be_agent: BE Agent processing task: ...
```

### 修复后（命令行过长场景）
```
[ERROR] agents.tools.claude_code_adapter: Claude CLI command too long (WinError 206). CLI path: D:\...\claude.bat, Args count: 4
[ERROR] agents.skills.be_dev_skill: LLM API error: Claude CLI 命令过长（Windows 限制）。请简化 prompt 或使用 Anthropic API。
```

## 注意事项

1. **Windows 命令行长度限制**：
   - Windows 命令行有约 8191 字符的限制
   - 如果 prompt 过长，会出现 WinError 206
   - 修复后的代码会识别此错误并给出明确提示

2. **统一执行方式**：
   - 所有 CLI 调用现在都使用 `_run_cli()`
   - 确保检查函数和执行函数使用完全相同的调用方式
   - 消除了 `shell=True` 带来的路径解析问题

3. **错误消息一致性**：
   - 所有 CLI 相关错误都通过 `_run_cli()` 统一处理
   - 错误消息格式保持一致，便于排查

