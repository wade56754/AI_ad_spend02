# Claude Code CLI 适配器修复总结

## 设计说明

### 核心改动

1. **新增 `_resolve_cli_path()` 函数**：
   - 支持两种模式：
     - **文件路径模式**：绝对路径、包含路径分隔符、或显式后缀（.exe/.cmd/.bat/.ps1/.sh）
       - 直接检查 `Path.exists()`
     - **命令名模式**：纯命令名（如 "claude"）
       - 使用 `shutil.which()` 在 PATH 中查找
   - 返回解析后的绝对路径字符串

2. **重构 `_find_claude_cli()` 函数**：
   - 优先级顺序：
     1. 环境变量 `CLAUDE_CLI_PATH`（如果设置）
     2. 命令名 "claude"（通过 PATH 解析）
     3. 常见安装路径（Windows/Unix 特定）
   - 所有路径都通过 `_resolve_cli_path()` 统一解析

3. **统一使用解析后的路径**：
   - `call_claude_code()` 中，`claude_cli` 变量现在始终是解析后的绝对路径
   - 所有 `subprocess.run()` 调用都使用这个解析后的路径
   - Windows 上对于 `.cmd/.bat/.ps1` 文件，仍然使用 `shell=True`

### 关键改进

- **跨平台兼容**：`shutil.which()` 在 Windows/Linux/macOS 都可用
- **向后兼容**：仍然支持绝对路径和显式文件路径
- **PATH 解析**：解决了 Windows 上 "claude" 命令名无法找到的问题

## 修改的文件

- `agents/tools/claude_code_adapter.py`：
  - 添加 `import shutil`
  - 新增 `_resolve_cli_path()` 函数
  - 重构 `_find_claude_cli()` 函数
  - 简化 `call_claude_code()` 中的 shell 判断逻辑

## 验证命令清单

### 1. 基础验证（PowerShell）

```powershell
# 确认 claude 命令可用
claude --version

# 确认 PATH 中有 claude
Get-Command claude

# 确认 claude.cmd 存在（如果使用 cmd 包装器）
Get-Command claude.cmd -ErrorAction SilentlyContinue
```

**预期结果**：
- `claude --version` 输出版本信息（如 `2.0.55 (Claude Code)`）
- `Get-Command claude` 显示命令位置

### 2. Python 路径解析测试

```powershell
# 在项目根目录执行
python -c "import shutil; print(shutil.which('claude'))"
```

**预期结果**：
- 输出 claude 的绝对路径（如 `C:\Users\...\claude.cmd`）

### 3. 适配器检查测试

```powershell
# 测试适配器能否找到 CLI
python -c "from agents.tools.claude_code_adapter import check_claude_code_available; import json; print(json.dumps(check_claude_code_available(), indent=2, ensure_ascii=False))"
```

**预期结果**：
```json
{
  "available": true,
  "path": "C:\\Users\\...\\claude.cmd",
  "version": "2.0.55 (Claude Code)",
  "error": null
}
```

### 4. Orchestrator 流程测试（dry-run）

```powershell
# 使用预设运行 dry-run（不实际调用 LLM）
python -m agent_platform.cli orch --preset finance_profit_backend_full --mode dry-run
```

**预期结果**：
- 不再出现 "Claude CLI 可执行文件未找到: claude" 错误
- 日志中显示：`Using Claude Code CLI (path: C:\...\claude.cmd, version: 2.0.55)`
- BEAgent 开始处理任务（即使因为其他原因失败，也不应该是 CLI 路径问题）

### 5. 完整流程测试（execute，需要 LLM 后端）

```powershell
# 如果配置了 LLM 后端，可以尝试实际执行
python -m agent_platform.cli orch --preset finance_profit_backend_full --mode execute
```

**预期结果**：
- CLI 路径解析成功
- BEAgent 能够调用 Claude Code CLI
- 流程正常执行（或因为其他业务逻辑原因失败，但不应该是 CLI 路径问题）

### 6. 环境变量覆盖测试（可选）

```powershell
# 测试环境变量覆盖
$env:CLAUDE_CLI_PATH = "claude"
python -c "from agents.tools.claude_code_adapter import check_claude_code_available; print(check_claude_code_available()['path'])"
```

**预期结果**：
- 输出通过 `CLAUDE_CLI_PATH` 解析的路径

## 预期日志变化

### 修复前
```
[ERROR] agents.tools.claude_code_adapter: Claude CLI not found at: claude
[ERROR] agents.skills.be_dev_skill: LLM API error: Claude Code CLI call failed: Claude CLI 可执行文件未找到: claude。请确保已正确安装。
```

### 修复后
```
[DEBUG] agents.tools.claude_code_adapter: Resolved CLI path (command): claude -> C:\Users\...\claude.cmd
[INFO] agent_platform.llm.factory: Using Claude Code CLI (path: C:\Users\...\claude.cmd, version: 2.0.55)
[INFO] agents.agent_core.be_agent: BE Agent processing task: ...
```

## 注意事项

1. **Windows PowerShell 脚本**：
   - 如果 `claude` 是 PowerShell 脚本（`.ps1`），确保已创建 `.cmd` 包装器
   - `shutil.which()` 会找到 `.cmd` 文件，这是正确的

2. **PATH 环境变量**：
   - 确保 `claude` 命令在 PATH 中
   - 可以通过 `$env:PATH` 检查

3. **权限问题**：
   - 如果路径解析成功但执行失败，可能是权限问题
   - 检查文件是否有执行权限

