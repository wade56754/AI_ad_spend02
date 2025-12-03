#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LLM 连通性烟雾测试脚本

快速验证 DeepRouter / Anthropic API 连接是否正常。
- 从 .env.local 加载配置
- 打印 backend_type 和 client 类名
- 发起一次极小的请求（max_tokens=64）
- 打印响应前 200 字

用法:
    python scripts/test_llm_live.py

要求:
    - .env.local 中配置了 LLM_BACKEND 和相应的 API key
    - 网络连接正常
"""

import os
import sys
from pathlib import Path

# Windows 控制台编码修复
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 加载 .env.local 文件
repo_root = Path(__file__).resolve().parent.parent
env_local = repo_root / ".env.local"
if env_local.exists():
    with open(env_local, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and value:
                    os.environ[key] = value

# 自动转换 DeepRouter 配置为 Anthropic API 格式（推荐方式）
if not os.environ.get("ANTHROPIC_API_KEY") and os.environ.get("DEEPROUTER_CLAUDE_TOKEN"):
    os.environ["ANTHROPIC_API_KEY"] = os.environ["DEEPROUTER_CLAUDE_TOKEN"]
    print("提示: 自动将 DEEPROUTER_CLAUDE_TOKEN 设置为 ANTHROPIC_API_KEY")

if not os.environ.get("ANTHROPIC_BASE_URL") and os.environ.get("DEEPROUTER_BASE_URL"):
    os.environ["ANTHROPIC_BASE_URL"] = os.environ["DEEPROUTER_BASE_URL"]
    print("提示: 自动将 DEEPROUTER_BASE_URL 设置为 ANTHROPIC_BASE_URL")

# 如果 LLM_BACKEND=deeprouter，改为使用 anthropic_api（推荐）
if os.environ.get("LLM_BACKEND") == "deeprouter":
    os.environ["LLM_BACKEND"] = "anthropic_api"
    print("提示: 将 LLM_BACKEND 从 deeprouter 改为 anthropic_api（使用 Anthropic SDK 通过 DeepRouter 代理）")

# 添加项目路径
sys.path.insert(0, str(repo_root))

def main():
    """运行 LLM 连通性测试"""
    print("=" * 60)
    print("LLM 连通性烟雾测试")
    print("=" * 60)
    
    try:
        from agent_platform.llm.factory import get_llm_client, get_backend_type, reset_client
        
        # 重置客户端以加载最新配置
        reset_client()
        
        # 获取客户端
        print("\n1. 初始化 LLM 客户端...")
        client = get_llm_client()
        backend_type = get_backend_type()
        client_class_name = client.__class__.__name__
        
        print(f"   ✓ 后端类型: {backend_type}")
        print(f"   ✓ 客户端类: {client_class_name}")
        
        # 验证后端类型（应该优先使用 Anthropic API 风格，而不是 DeepRouterLLMClient 或 Claude CLI）
        if backend_type == "claude_code":
            print("   ⚠️  警告: 当前使用 Claude Code CLI，建议配置 ANTHROPIC_API_KEY + ANTHROPIC_BASE_URL 使用 DeepRouter 代理")
        elif backend_type == "deeprouter":
            print("   ⚠️  提示: 使用 DeepRouterLLMClient（直接调用），建议改用 ANTHROPIC_API_KEY + ANTHROPIC_BASE_URL 方式")
        elif backend_type == "anthropic_api":
            base_url = os.environ.get("ANTHROPIC_BASE_URL", "")
            if "deeprouter" in base_url.lower():
                print("   ✓ 使用 Anthropic API 格式通过 DeepRouter 代理（推荐）")
            else:
                print("   ✓ 使用 Anthropic 官方 API")
        
        # 发起极小的测试请求
        print("\n2. 发送测试请求...")
        print("   系统提示: '你是一个助手'")
        print("   用户输入: '请用中文回复：测试通过'")
        print("   max_tokens: 64")
        
        response = client.generate(
            system="你是一个助手",
            user="请用中文回复：测试通过",
            max_tokens=64
        )
        
        print(f"\n3. 响应内容 (前200字):")
        print("-" * 60)
        response_text = response.text[:200]
        print(response_text)
        if len(response.text) > 200:
            print("...")
        print("-" * 60)
        
        print(f"\n4. 响应详情:")
        print(f"   模型: {response.model}")
        print(f"   输入 tokens: {response.usage.get('input_tokens', 0)}")
        print(f"   输出 tokens: {response.usage.get('output_tokens', 0)}")
        print(f"   总 tokens: {response.usage.get('input_tokens', 0) + response.usage.get('output_tokens', 0)}")
        
        print("\n" + "=" * 60)
        print("✓ LLM 连通性测试通过！")
        print("=" * 60)
        return 0
        
    except ImportError as e:
        print(f"\n✗ 导入错误: {e}")
        print("请确保在项目根目录运行此脚本")
        return 1
    except Exception as e:
        print(f"\n✗ 测试失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

