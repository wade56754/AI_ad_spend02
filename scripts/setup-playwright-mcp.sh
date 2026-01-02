#!/bin/bash
# Playwright MCP 配置助手
# 此脚本将帮助您配置 Playwright MCP Server

echo "========================================"
echo "Playwright MCP 配置助手"
echo "========================================"
echo ""

# 检查 node 和 npm 是否安装
if ! command -v node &> /dev/null; then
    echo "[错误] 未找到 Node.js，请先安装 Node.js"
    echo "请从 https://nodejs.org/ 下载并安装 Node.js"
    exit 1
fi

echo "[√] Node.js 已安装: $(node --version)"

if ! command -v npx &> /dev/null; then
    echo "[错误] 未找到 npx，请确保 Node.js 正确安装"
    exit 1
fi

echo "[√] npx 可用: $(npx --version)"
echo ""

# 安装 Playwright 浏览器驱动
echo "正在安装 Playwright 浏览器驱动..."
echo "这可能需要几分钟时间，请耐心等待..."
npx -y playwright install

if [ $? -ne 0 ]; then
    echo "[错误] Playwright 浏览器驱动安装失败"
    exit 1
fi

echo "[√] Playwright 浏览器驱动安装完成"
echo ""

# 验证 MCP 配置
echo "检查 MCP 配置文件..."
if [ -f ".claude/mcp.json" ]; then
    echo "[√] .claude/mcp.json 存在"
    if grep -q "@playwright/mcp" .claude/mcp.json; then
        echo "[√] Playwright MCP 配置已存在"
    else
        echo "[警告] Playwright MCP 配置未找到，请手动添加"
    fi
else
    echo "[警告] .claude/mcp.json 不存在"
fi

if [ -f ".mcp.json" ]; then
    echo "[√] .mcp.json 存在"
    if grep -q "@playwright/mcp" .mcp.json; then
        echo "[√] Playwright MCP 配置已存在"
    else
        echo "[警告] Playwright MCP 配置未找到，请手动添加"
    fi
else
    echo "[警告] .mcp.json 不存在"
fi

echo ""
echo "========================================"
echo "[√] 配置完成!"
echo "========================================"
echo ""
echo "下一步:"
echo "1. 重启 Cursor 编辑器以使配置生效"
echo "2. Playwright MCP 工具将自动可用"
echo "3. 可以开始使用 MCP 执行浏览器自动化任务"
echo ""
echo "已更新的配置:"
echo "- .claude/mcp.json (项目配置)"
echo "- .mcp.json (项目配置)"
echo ""



