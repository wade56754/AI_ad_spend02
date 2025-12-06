# Claude 扩展插件认证问题修复指南

## 🔍 问题诊断

**错误信息**：
```
API Error: 401 {"error":{"code":"","message":"无效的令牌 (request id: ...)","type":"new_api_error"}}
```

**问题原因**：
- Claude API 密钥未配置或已过期
- Cursor 的 Claude 扩展插件需要重新认证
- 环境变量 `ANTHROPIC_API_KEY` 未设置

---

## ✅ 解决方案

### 方案 1：在 Cursor 中重新登录（推荐）

1. **打开 Cursor 设置**
   - 按 `Ctrl + ,` (Windows) 或 `Cmd + ,` (Mac)
   - 或点击左下角齿轮图标 → Settings

2. **找到 Claude 认证设置**
   - 在设置中搜索 "Claude" 或 "Anthropic"
   - 找到 "Claude API" 或 "Authentication" 相关选项

3. **重新登录**
   - 点击 "Sign In" 或 "Login"
   - 按照提示完成认证流程
   - 或点击 "Logout" 后重新登录

4. **验证连接**
   - 重启 Cursor
   - 尝试使用 Claude 功能，确认错误已解决

---

### 方案 2：手动配置 API 密钥

1. **获取 Anthropic API 密钥**
   - 访问：https://console.anthropic.com/
   - 登录账户
   - 进入 "API Keys" 页面
   - 创建新密钥或复制现有密钥

2. **在 Cursor 中配置**
   - 打开 Cursor 设置
   - 找到 "Claude API Key" 或类似选项
   - 粘贴 API 密钥
   - 保存设置

3. **或通过环境变量配置**（Windows PowerShell）
   ```powershell
   # 设置用户级环境变量（永久）
   [System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "your-api-key-here", "User")
   
   # 设置当前会话环境变量（临时）
   $env:ANTHROPIC_API_KEY = "your-api-key-here"
   ```

4. **重启 Cursor**
   - 完全退出 Cursor
   - 重新启动应用

---

### 方案 3：检查 Cursor 扩展状态

1. **检查扩展是否启用**
   - 打开 Cursor 扩展面板
   - 确认 Claude 相关扩展已启用

2. **更新扩展**
   - 检查是否有扩展更新
   - 更新到最新版本

3. **重新安装扩展**（如果上述方法无效）
   - 禁用 Claude 扩展
   - 重启 Cursor
   - 重新启用扩展

---

## 🔧 高级排查

### 检查 Cursor 配置文件

Cursor 的配置通常存储在：
- **Windows**: `%APPDATA%\Cursor\User\settings.json`
- **Mac**: `~/Library/Application Support/Cursor/User/settings.json`
- **Linux**: `~/.config/Cursor/User/settings.json`

查找以下配置项：
```json
{
  "claude.apiKey": "your-key-here",
  "anthropic.apiKey": "your-key-here"
}
```

### 检查网络连接

1. **确认可以访问 Anthropic API**
   ```powershell
   # 测试 API 连接（需要先设置 API 密钥）
   curl https://api.anthropic.com/v1/messages -H "x-api-key: $env:ANTHROPIC_API_KEY"
   ```

2. **检查代理设置**
   - 如果使用代理，确保 Cursor 的代理配置正确
   - 检查防火墙是否阻止了连接

### 查看 Cursor 日志

1. **打开开发者工具**
   - 按 `Ctrl + Shift + I` (Windows) 或 `Cmd + Option + I` (Mac)
   - 查看 Console 标签页的错误信息

2. **检查日志文件**
   - Windows: `%APPDATA%\Cursor\logs\`
   - Mac: `~/Library/Logs/Cursor/`
   - 查找与 Claude/Anthropic 相关的错误

---

## 📝 验证修复

修复后，尝试以下操作验证：

1. **在 Cursor 中询问 Claude**
   - 打开对话面板
   - 输入简单问题，如 "Hello"
   - 确认可以正常响应

2. **检查项目配置**
   - 确认 `.claude/settings.local.json` 中的 MCP 服务器配置正常
   - 验证 Skill 可以正常加载

3. **测试 MCP 服务器**
   ```powershell
   # 如果配置了 MCP 服务器，测试连接
   claude mcp list
   ```

---

## 🚨 常见问题

### Q1: 提示 "无效的令牌" 但已配置 API 密钥

**可能原因**：
- API 密钥格式错误（应包含 `sk-ant-` 前缀）
- API 密钥已过期或被撤销
- 使用了错误的密钥类型（需要 Messages API 密钥）

**解决方法**：
1. 在 Anthropic Console 中重新生成密钥
2. 确认密钥类型为 "Messages API"
3. 在 Cursor 中重新配置

### Q2: 配置后仍然报错

**可能原因**：
- Cursor 缓存了旧的认证信息
- 环境变量未正确加载

**解决方法**：
1. 完全退出 Cursor（确保所有进程结束）
2. 清除 Cursor 缓存（可选）
3. 重新启动并登录

### Q3: 使用企业账户或团队账户

**注意事项**：
- 某些企业账户可能需要特殊配置
- 检查账户权限和 API 配额
- 联系 Anthropic 支持确认账户状态

---

## 📚 相关资源

- **Anthropic Console**: https://console.anthropic.com/
- **Cursor 文档**: https://cursor.sh/docs
- **Anthropic API 文档**: https://docs.anthropic.com/

---

## ✅ 快速检查清单

- [ ] 在 Cursor 设置中重新登录 Claude
- [ ] 确认 API 密钥格式正确（`sk-ant-...`）
- [ ] 检查 API 密钥是否过期
- [ ] 重启 Cursor
- [ ] 验证网络连接正常
- [ ] 检查 Cursor 扩展是否启用
- [ ] 查看 Cursor 日志中的错误信息

---

**最后更新**: 2025-12-07
**状态**: 待验证


