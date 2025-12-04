# AI_ad_spend02 本地开发环境基线规范 v1.0

> **版本**: v1.0
> **创建日期**: 2025-12-04
> **适用范围**: Windows 开发环境（cmd / PowerShell）
> **维护者**: Wade

---

## 1. 适用范围

本文档定义 AI_ad_spend02 项目的本地开发环境标准，确保：
- 所有开发者使用一致的 Python/Node.js 版本
- MCP (ai-ad-agents) 服务启动方式统一
- 减少"在我机器上能跑"的问题

---

## 2. 必需环境与版本要求

| 组件 | 推荐版本 | 最低版本 | 备注 |
|------|---------|---------|------|
| Python | 3.11.x | 3.11.0 | 项目 venv 使用 3.11.9 |
| Node.js | 20.x LTS | 18.x | Next.js 16 要求 |
| pnpm | 9.x | 8.x | 前端包管理器（推荐） |
| npm | 10.x | 8.x | pnpm 备选方案 |
| Git | 2.40+ | 2.30 | Windows 版本 |

### 2.1 安装验证

```cmd
REM 验证 Python
python --version
REM 期望输出: Python 3.11.x

REM 验证 Node.js
node --version
REM 期望输出: v20.x.x

REM 验证 pnpm（如使用）
pnpm --version
REM 期望输出: 9.x.x
```

---

## 3. 项目目录与虚拟环境

### 3.1 标准目录结构

```
D:\git\1108\AI_ad_spend02\
├── .claude\                    # Claude Code 配置目录
│   ├── mcp.json               # MCP Server 配置（权威来源）
│   ├── settings.local.json    # 本地权限配置
│   ├── commands\              # 自定义斜杠命令
│   └── ai-ad-agents-mcp-start.bat  # MCP 启动脚本
├── .venv\                     # Python 虚拟环境（标准）
├── agent_platform\            # Agent 平台核心代码
│   └── mcp\
│       └── server.py          # MCP Server 实现
├── backend\                   # FastAPI 后端
├── frontend\                  # Next.js 前端
├── docs\                      # 项目文档
└── requirements.txt           # Python 依赖清单
```

### 3.2 虚拟环境约定

**标准虚拟环境路径**: `D:\git\1108\AI_ad_spend02\.venv\`

> **注意**: 项目中可能存在 `.venv311` 等历史虚拟环境，统一使用 `.venv` 作为标准。

#### cmd 激活方式
```cmd
cd /d D:\git\1108\AI_ad_spend02
call .venv\Scripts\activate.bat
```

#### PowerShell 激活方式
```powershell
cd D:\git\1108\AI_ad_spend02
.\.venv\Scripts\Activate.ps1
```

#### 依赖安装
```cmd
REM 激活 venv 后
pip install -r requirements.txt
pip install -r requirements-test.txt
```

---

## 4. MCP 配置规范

### 4.1 配置文件位置

**权威配置文件**: `D:\git\1108\AI_ad_spend02\.claude\mcp.json`

> **历史说明**: 根目录的 `.mcp.json` 已废弃并删除。所有 MCP 配置统一在 `.claude\mcp.json` 中管理。

### 4.2 ai-ad-agents MCP 配置结构

```json
{
  "mcpServers": {
    "ai-ad-agents": {
      "command": "D:\\git\\1108\\AI_ad_spend02\\.venv\\Scripts\\python.exe",
      "args": ["-m", "agent_platform.mcp.server"],
      "cwd": "D:\\git\\1108\\AI_ad_spend02",
      "env": {
        "AGENT_PLATFORM_MODE": "mcp"
      }
    }
  }
}
```

**配置说明**:
- `command`: 使用项目 `.venv` 内的 Python 解释器
- `args`: 通过 `-m` 模块方式启动 MCP Server
- `cwd`: 工作目录设为项目根目录（REPO_ROOT）
- `env.AGENT_PLATFORM_MODE`: 必须设为 `mcp`，启用 MCP 工具模式

### 4.3 其他 MCP Server

`.claude\mcp.json` 中还包含以下 MCP Server（按需启用）：
- `context7`: 代码库文档查询
- `magic`: 21st.dev UI 组件生成
- `puppeteer`: 浏览器自动化
- `sequential-thinking`: 结构化思考
- `eslint`: ESLint 代码检查

---

## 5. 标准启动流程

### 5.1 启动 ai-ad-agents MCP（推荐方式）

**方式 A：双击脚本**
```
D:\git\1108\AI_ad_spend02\.claude\ai-ad-agents-mcp-start.bat
```

**方式 B：命令行手动启动**
```cmd
cd /d D:\git\1108\AI_ad_spend02
set AGENT_PLATFORM_MODE=mcp
.venv\Scripts\python.exe -m agent_platform.mcp.server
```

> **注意**: MCP Server 使用 stdio 模式，启动后会等待 JSON-RPC 输入。正常情况下由 Claude Code 自动调用，无需手动交互。

### 5.2 在 Claude Code 中验证 MCP 状态

```
claude mcp list
```

期望看到 `ai-ad-agents` 在列表中，状态为连接成功。

### 5.3 启动 Backend (FastAPI)

```cmd
cd /d D:\git\1108\AI_ad_spend02
call .venv\Scripts\activate.bat
cd backend
uvicorn main:app --reload --port 8000
```

### 5.4 启动 Frontend (Next.js)

```cmd
cd /d D:\git\1108\AI_ad_spend02\frontend
pnpm install
pnpm dev
```

访问: http://localhost:3000

---

## 6. 常见问题排查

### 6.1 PowerShell 中 `&&` 报错

**现象**: PowerShell 不支持 `&&` 链接命令

**解决方案**:
```powershell
# 方式 1：使用分号
cd D:\git\1108\AI_ad_spend02; .\.venv\Scripts\Activate.ps1

# 方式 2：使用 -and 运算符
(cd D:\git\1108\AI_ad_spend02) -and (.\.venv\Scripts\Activate.ps1)
```

### 6.2 MCP Server 无法连接

**检查步骤**:
1. 确认 `.venv` 存在且包含正确的 Python 版本
2. 确认 `agent_platform` 包已安装
3. 检查 `.claude\mcp.json` 中的路径是否正确
4. 手动测试 MCP Server 能否启动：
   ```cmd
   cd /d D:\git\1108\AI_ad_spend02
   .venv\Scripts\python.exe -c "import agent_platform.mcp.server; print('OK')"
   ```

### 6.3 多个 .mcp.json 冲突

**现状**: 根目录 `.mcp.json` 已删除，统一使用 `.claude\mcp.json`

**如果仍有问题**: 检查 `%APPDATA%\Claude\` 下是否有全局配置覆盖项目配置

### 6.4 venv 未激活导致依赖缺失

**现象**: `ModuleNotFoundError: No module named 'xxx'`

**解决方案**:
```cmd
REM 确认当前 Python 路径
where python

REM 如果不是 .venv 内的 Python，重新激活
call D:\git\1108\AI_ad_spend02\.venv\Scripts\activate.bat
```

### 6.5 Python 版本不匹配

**检查方式**:
```cmd
.venv\Scripts\python.exe --version
REM 期望: Python 3.11.x
```

如果版本不对，需要重建 venv：
```cmd
cd /d D:\git\1108\AI_ad_spend02
rmdir /s /q .venv
python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt
```

### 6.6 MCP Server 日志查看

MCP Server 的日志输出到 stderr（不干扰 stdout 上的 JSON-RPC 协议）。

如需查看调试日志，可以手动启动并重定向：
```cmd
.venv\Scripts\python.exe -m agent_platform.mcp.server 2> mcp_debug.log
```

---

## 7. 可用 MCP 工具清单

ai-ad-agents MCP Server 提供以下工具：

| 工具名 | 功能 | 示例用途 |
|--------|------|---------|
| `ap_list_agents` | 列出所有可用 Agent | 查看 fe/be/test/orch 等 Agent |
| `ap_read_sot_file` | 读取 SoT 文档 | 获取 DATA_SCHEMA、STATE_MACHINE 内容 |
| `ap_list_sot_files` | 列出所有 SoT 文档 key | 查看有哪些 SoT 可读取 |
| `ap_read_file` | 读取仓库内文件 | 安全读取代码/配置文件 |
| `ap_write_file` | 写入仓库内文件 | 安全写入代码/配置文件 |
| `ap_run_pytest` | 运行 pytest 测试 | 执行单元测试/集成测试 |
| `ap_run_agent` | 调用已注册 Agent | 运行 fe/be/test/orch 等 Agent |

**安全约束**:
- 所有文件操作限制在 `REPO_ROOT` 内
- 禁止绝对路径、盘符路径、UNC 路径
- 禁止 `../` 目录遍历

---

## 8. 新机器/新环境一键复现

```cmd
REM 1. 克隆仓库
git clone <repo-url> D:\git\1108\AI_ad_spend02
cd /d D:\git\1108\AI_ad_spend02

REM 2. 创建 Python 虚拟环境
python -m venv .venv

REM 3. 激活并安装依赖
call .venv\Scripts\activate.bat
pip install -r requirements.txt
pip install -r requirements-test.txt

REM 4. 安装前端依赖
cd frontend
pnpm install
cd ..

REM 5. 验证 MCP Server
.venv\Scripts\python.exe -c "import agent_platform.mcp.server; print('MCP Server OK')"

REM 6. 在 Claude Code 中启动项目
claude
```

---

## 附录 A: 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| v1.0 | 2025-12-04 | 初始版本，建立环境基线规范 |

---

## 附录 B: 相关文档

- `CLAUDE.md` - Claude Code 项目指令
- `.claude\PROJECT_RULES.md` - 项目规则详细版
- `docs/2.sot/` - SoT 文档目录
- `agent_platform/mcp/server.py` - MCP Server 实现

