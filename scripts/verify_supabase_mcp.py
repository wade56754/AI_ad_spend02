#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase MCP 配置验证脚本
检查环境变量和 MCP 配置是否正确
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# 设置 Windows 控制台编码为 UTF-8
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass


def check_env_vars():
    """检查必需的环境变量"""
    print("=" * 60)
    print("检查环境变量")
    print("=" * 60)
    
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_ACCESS_TOKEN",
        "SUPABASE_PROJECT_REF"
    ]
    
    all_set = True
    for var in required_vars:
        value = os.getenv(var, "")
        if value:
            # 隐藏敏感信息
            if "TOKEN" in var:
                display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            else:
                display_value = value
            print(f"[OK] {var}: {display_value}")
        else:
            print(f"[FAIL] {var}: 未设置")
            all_set = False
    
    return all_set


def check_mcp_config():
    """检查 .mcp.json 配置文件"""
    print("\n" + "=" * 60)
    print("检查 .mcp.json 配置文件")
    print("=" * 60)
    
    config_path = Path(".mcp.json")
    if not config_path.exists():
        print("[FAIL] .mcp.json 文件不存在")
        return False
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        print("[OK] .mcp.json 文件存在且格式正确")
        
        # 检查 supabase 配置
        if "mcpServers" in config and "supabase" in config["mcpServers"]:
            supabase_config = config["mcpServers"]["supabase"]
            print("\nSupabase MCP 配置:")
            print(f"  command: {supabase_config.get('command', 'N/A')}")
            print(f"  args: {supabase_config.get('args', [])}")
            print(f"  env keys: {list(supabase_config.get('env', {}).keys())}")
            return True
        else:
            print("[FAIL] 未找到 supabase MCP 服务器配置")
            return False
            
    except json.JSONDecodeError as e:
        print(f"[FAIL] .mcp.json 文件格式错误: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] 读取配置文件时出错: {e}")
        return False


def check_nodejs():
    """检查 Node.js 是否安装"""
    print("\n" + "=" * 60)
    print("检查 Node.js 环境")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"[OK] Node.js 已安装: {result.stdout.strip()}")
            return True
        else:
            print("[FAIL] Node.js 未安装或无法运行")
            return False
    except FileNotFoundError:
        print("[FAIL] Node.js 未安装（找不到 node 命令）")
        print("   请从 https://nodejs.org/ 下载并安装 Node.js")
        return False
    except Exception as e:
        print(f"[FAIL] 检查 Node.js 时出错: {e}")
        return False


def check_npx():
    """检查 npx 是否可用"""
    print("\n" + "=" * 60)
    print("检查 npx 工具")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ["npx", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"[OK] npx 可用: {result.stdout.strip()}")
            return True
        else:
            print("[FAIL] npx 不可用")
            return False
    except FileNotFoundError:
        print("[FAIL] npx 未找到（通常与 Node.js 一起安装）")
        return False
    except Exception as e:
        print(f"[FAIL] 检查 npx 时出错: {e}")
        return False


def test_supabase_mcp_package():
    """测试 Supabase MCP 包是否可以安装"""
    print("\n" + "=" * 60)
    print("测试 Supabase MCP 包")
    print("=" * 60)
    
    print("尝试安装 @supabase/mcp-server-supabase...")
    try:
        # 只检查包是否存在，不实际运行
        result = subprocess.run(
            ["npx", "-y", "@supabase/mcp-server-supabase@latest", "--version"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("[OK] Supabase MCP 包可以安装和运行")
            if result.stdout:
                print(f"   输出: {result.stdout.strip()[:100]}")
            return True
        else:
            print("[WARN] 包安装可能有问题")
            if result.stderr:
                print(f"   错误: {result.stderr.strip()[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("[WARN] 安装超时（可能需要网络连接）")
        return False
    except Exception as e:
        print(f"[WARN] 测试时出错: {e}")
        print("   这可能是因为需要网络连接或访问令牌")
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Supabase MCP 配置验证")
    print("=" * 60 + "\n")
    
    results = {
        "环境变量": check_env_vars(),
        "配置文件": check_mcp_config(),
        "Node.js": check_nodejs(),
        "npx": check_npx(),
    }
    
    # 只有在前面都通过的情况下才测试包
    if all([results["Node.js"], results["npx"]]):
        results["MCP 包"] = test_supabase_mcp_package()
    
    # 总结
    print("\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)
    
    all_passed = True
    for check, passed in results.items():
        status = "[OK] 通过" if passed else "[FAIL] 失败"
        print(f"{check}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[OK] 所有检查通过！")
        print("\n下一步：")
        print("1. 确保环境变量在 Cursor 中可用")
        print("2. 完全重启 Cursor 编辑器")
        print("3. 在 Cursor 中运行 /mcp 查看 MCP 服务器状态")
        print("4. 尝试运行 /mcp__supabase__list_tables 测试连接")
    else:
        print("[FAIL] 部分检查未通过，请修复上述问题")
        print("\n常见问题解决方案：")
        if not results["环境变量"]:
            print("- 在 .env 文件中设置环境变量，或")
            print("- 在系统环境变量中设置 SUPABASE_URL, SUPABASE_ACCESS_TOKEN, SUPABASE_PROJECT_REF")
        if not results["Node.js"]:
            print("- 从 https://nodejs.org/ 安装 Node.js LTS 版本")
        if not results["配置文件"]:
            print("- 检查 .mcp.json 文件格式是否正确")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())

