#!/usr/bin/env python3
"""更新用户目录下的 MCP 配置文件，添加 context7"""
import json
import os
from pathlib import Path

# 用户目录下的 MCP 配置文件路径
mcp_config_path = Path.home() / ".mcp.json"

# 读取现有配置
if mcp_config_path.exists():
    with open(mcp_config_path, 'r', encoding='utf-8-sig') as f:
        config = json.load(f)
else:
    config = {"mcpServers": {}}

# 确保 mcpServers 存在
if "mcpServers" not in config:
    config["mcpServers"] = {}

# 添加或更新 sequential-thinking（如果不存在）
if "sequential-thinking" not in config["mcpServers"]:
    config["mcpServers"]["sequential-thinking"] = {
        "command": "npx",
        "args": [
            "-y",
            "@modelcontextprotocol/server-sequential-thinking"
        ]
    }

# 添加或更新 context7（如果不存在）
if "context7" not in config["mcpServers"]:
    config["mcpServers"]["context7"] = {
        "command": "npx",
        "args": [
            "-y",
            "@upstash/context7-mcp"
        ]
    }

# 写入配置文件
with open(mcp_config_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"[OK] MCP config updated: {mcp_config_path}")
print(f"[OK] Configured MCP servers:")
for server_name in sorted(config["mcpServers"].keys()):
    status = "[OK]" if server_name in ["sequential-thinking", "context7"] else "    "
    print(f"   {status} {server_name}")

