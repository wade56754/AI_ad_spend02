# MCP 服务器配置文档

> 本文档描述了 AI_ad_spend02 项目中配置的 MCP (Model Context Protocol) 服务器。

---

## 📋 已配置的 MCP 服务器

### 1. Chrome DevTools MCP

**用途**: 浏览器自动化和调试

**配置**:
```json
{
  "command": "npx",
  "args": [
    "-y",
    "chrome-devtools-mcp@latest",
    "--browser-url=http://127.0.0.1:9222"
  ]
}
```

**功能**:
- 启动 Chrome 浏览器并连接到 DevTools Protocol
- 自动化浏览器操作（点击、输入、导航等）
- 分析网页性能
- 执行端到端测试
- 截图和 DOM 操作

**使用前准备**:
需要先启动 Chrome 并启用远程调试：
```bash
# Windows
start chrome --remote-debugging-port=9222

# macOS
open -a "Google Chrome" --args --remote-debugging-port=9222
```

**使用示例**:
```bash
# 启动 Chrome 并连接到本地开发服务器
start_chrome_and_connect("localhost:3000")

# 分析页面性能
analyze_page_performance()

# 执行自动化测试
run_e2e_test()
```

---

### 2. Context7 MCP

**用途**: 提供最新、特定版本的文档和代码示例，帮助 AI 生成更准确的代码

**配置**:
```json
{
  "command": "npx",
  "args": ["-y", "@upstash/context7-mcp@latest"]
}
```

**功能**:
- 提供最新版本的文档和代码示例
- 自动提供上下文信息
- 增强代码生成的准确性

**使用方法**:
在 Cursor 中使用时，只需在提示中包含 `use context7`，Context7 MCP 将自动提供最新的文档和代码示例。

---

### 3. AI Ad Agents MCP

**用途**: 项目内部的 AI Agent 平台 MCP 服务器

**配置**:
```json
{
  "command": "D:\\\\git\\\\1108\\\\AI_ad_spend02\\\\.venv\\\\Scripts\\\\python.exe",
  "args": ["-m", "agent_platform.mcp.server"],
  "cwd": "D:\\\\git\\\\1108\\\\AI_ad_spend02",
  "env": {
    "AGENT_PLATFORM_MODE": "mcp"
  }
}
```

**功能**:
- 文件读写操作 (`ap_read_file`, `ap_write_file`)
- 运行测试 (`ap_run_pytest`)
- 执行 Agent (`ap_run_agent`)
- 读取 SoT 文档 (`ap_read_sot_file`)
- 列出可用工具和技能

**启动脚本**: `.claude/ai-ad-agents-mcp-start.bat`

---

### 4. Supabase MCP

**用途**: Supabase 数据库和 API 管理

**配置**:
```json
{
  "command": "npx",
  "args": ["-y", "@supabase/mcp-server-supabase@latest"]
}
```

**功能**:
- 数据库查询和管理
- API 端点管理
- 项目配置管理

---

### 5. Sequential Thinking MCP

**用途**: 结构化思维和推理

**配置**:
```json
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-sequential-thinking@latest"]
}
```

**功能**:
- 分步骤思考复杂问题
- 结构化推理过程
- 逻辑链分析

---

## 📁 配置文件位置

### 项目级配置
- **文件**: `.mcp.json` (项目根目录)
- **用途**: 项目级别的 MCP 服务器配置
- **格式**: JSON

### Cursor 用户配置
- **文件**: `.claude/settings.local.json`
- **字段**: `enabledMcpjsonServers`
- **用途**: 启用/禁用特定的 MCP 服务器

---

## 🚀 快速开始

### 1. 安装依赖

Chrome DevTools MCP 会在首次使用时自动通过 `npx` 下载，无需手动安装。

### 2. 验证配置

在 Cursor 中，MCP 服务器应该自动加载。您可以通过以下方式验证：

1. 打开 Cursor Settings → MCP
2. 查看已配置的服务器列表
3. 确认所有服务器状态为 "Connected"

### 3. 使用 MCP 工具

在 Cursor 中，您可以直接使用 MCP 工具：

```
# 使用 Chrome DevTools MCP
启动 Chrome 并连接到 localhost:3000

# 使用 AI Ad Agents MCP
读取文件 frontend/app/dashboard/page.tsx
```

---

## 🔧 故障排除

### Chrome DevTools MCP 无法连接

1. **检查 Chrome 是否安装**:
   ```bash
   # Windows
   where chrome
   
   # macOS
   which google-chrome
   ```

2. **检查端口是否被占用**:
   ```bash
   # Windows
   netstat -ano | findstr :3000
   
   # macOS/Linux
   lsof -i :3000
   ```

3. **手动启动 Chrome**:
   ```bash
   # Windows
   start chrome --remote-debugging-port=9222
   
   # macOS
   open -a "Google Chrome" --args --remote-debugging-port=9222
   ```

### AI Ad Agents MCP 无法启动

1. **检查 Python 虚拟环境**:
   ```bash
   .venv\Scripts\python.exe --version
   ```

2. **检查模块是否可导入**:
   ```bash
   .venv\Scripts\python.exe -c "import agent_platform.mcp.server"
   ```

3. **查看启动日志**:
   ```bash
   .claude\ai-ad-agents-mcp-start.bat
   ```

---

## 📚 相关文档

- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Supabase MCP Server](https://github.com/supabase/mcp-server-supabase)
- [AI Ad Agents MCP 文档](../.claude/commands/mcp-orch.md)

---

**版本**: v1.1  
**最后更新**: 2024-12-03

**更新日志**:
- v1.1: 添加 Context7 MCP 配置，优化 Chrome DevTools MCP 配置（添加浏览器 URL 参数）

