#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DeepRouter Anthropic 模式验证脚本

使用 anthropic 官方 SDK 通过 DeepRouter 网关调用 Claude，验证配置是否正确。

用法:
    python scripts/test_deeprouter_anthropic.py

要求:
    - 安装 anthropic 包: pip install anthropic
    - 环境变量 ANTHROPIC_API_KEY（DeepRouter 令牌）
    - 环境变量 ANTHROPIC_BASE_URL（可选，默认 https://deeprouter.top）
"""

import os
import sys
from pathlib import Path

# Windows 控制台编码修复
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def load_env_local():
    """从 .env.local 文件加载环境变量"""
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
                        # 只在环境变量中不存在时才设置（环境变量优先级更高）
                        if key not in os.environ:
                            os.environ[key] = value


def load_config():
    """
    从环境变量加载配置。
    
    支持从 ANTHROPIC_API_KEY 或 DEEPROUTER_CLAUDE_TOKEN 读取。
    
    Returns:
        tuple: (api_key, base_url, model)
    
    Raises:
        SystemExit: 如果缺少必需的配置
    """
    # 读取 ANTHROPIC_API_KEY 或 DEEPROUTER_CLAUDE_TOKEN
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        # 尝试从 DEEPROUTER_CLAUDE_TOKEN 读取
        api_key = os.environ.get("DEEPROUTER_CLAUDE_TOKEN")
        if api_key:
            print("提示: 从 DEEPROUTER_CLAUDE_TOKEN 读取 API key")
            os.environ["ANTHROPIC_API_KEY"] = api_key
    
    if not api_key:
        print("=" * 60)
        print("错误: 未找到 ANTHROPIC_API_KEY 或 DEEPROUTER_CLAUDE_TOKEN")
        print("=" * 60)
        print("\n请在 .env.local 或环境变量中配置:")
        print("  ANTHROPIC_API_KEY=<你的_deeprouter_token>")
        print("  或")
        print("  DEEPROUTER_CLAUDE_TOKEN=<你的_deeprouter_token>")
        print("\n示例 (.env.local):")
        print("  ANTHROPIC_API_KEY=cr_xxxxxxx")
        print("  ANTHROPIC_BASE_URL=https://deeprouter.top")
        sys.exit(1)
    
    # 读取 ANTHROPIC_BASE_URL 或 DEEPROUTER_BASE_URL（可选，有默认值）
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    if not base_url:
        base_url = os.environ.get("DEEPROUTER_BASE_URL")
        if base_url:
            print("提示: 从 DEEPROUTER_BASE_URL 读取 base_url")
            os.environ["ANTHROPIC_BASE_URL"] = base_url
    
    if not base_url:
        base_url = "https://deeprouter.top"
        print("提示: 未设置 ANTHROPIC_BASE_URL，使用默认值: https://deeprouter.top")
    else:
        # 规范化 base_url（移除尾部的 /v1，Anthropic SDK 会自动添加）
        base_url = base_url.rstrip('/')
        if base_url.endswith('/v1'):
            base_url = base_url[:-3].rstrip('/')
            print(f"提示: 规范化 base_url，移除了尾部的 /v1")
    
    # 读取模型名称（可选）
    model = os.environ.get("DEEPROUTER_MODEL", "claude-sonnet-4-20250514")
    
    return api_key, base_url, model


def create_anthropic_client(api_key: str, base_url: str):
    """
    创建 Anthropic 客户端。
    
    Args:
        api_key: API 密钥
        base_url: Base URL（DeepRouter 网关地址）
    
    Returns:
        Anthropic 客户端实例
    
    Raises:
        ImportError: 如果 anthropic 包未安装
    """
    try:
        import anthropic
    except ImportError:
        print("=" * 60)
        print("错误: anthropic 包未安装")
        print("=" * 60)
        print("\n请先安装 anthropic 包:")
        print("  pip install anthropic")
        sys.exit(1)
    
    # 创建客户端
    # Anthropic SDK 会自动添加 /v1/messages 路径
    # 注意：如果 base_url 已经包含 /v1，SDK 会自动处理路径拼接
    client = anthropic.Anthropic(
        api_key=api_key,
        base_url=base_url
    )
    
    # 打印诊断信息
    print(f"   ✓ Anthropic SDK 版本: {anthropic.__version__}")
    print(f"   ✓ Base URL: {base_url} (SDK 会自动添加 /v1/messages)")
    
    return client


def send_test_request(client, model: str):
    """
    发送测试请求。
    
    Args:
        client: Anthropic 客户端实例
        model: 模型名称
    
    Returns:
        tuple: (success: bool, response_text: str, usage: dict, error: str)
    """
    try:
        # 发送测试请求
        # 注意：DeepRouter 可能要求 system 参数为数组格式
        # 尝试两种格式：先尝试字符串（标准 Anthropic 格式），失败则尝试数组格式
        system_prompt = "你是一个用于 DeepRouter 连接测试的诊断助手。"
        
        try:
            # 方式 1: 标准 Anthropic 格式（system 为字符串）
            response = client.messages.create(
                model=model,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": "请用不超过 20 个中文字确认：DeepRouter Anthropic 直连正常。"
                    }
                ],
                max_tokens=64,
                stream=False
            )
        except Exception as first_error:
            # 如果失败且错误提示需要数组格式，尝试数组格式
            error_str = str(first_error).lower()
            if "arraylist" in error_str or "system" in error_str:
                # 方式 2: DeepRouter 兼容格式（system 为数组）
                response = client.messages.create(
                    model=model,
                    system=[{"type": "text", "text": system_prompt}],
                    messages=[
                        {
                            "role": "user",
                            "content": "请用不超过 20 个中文字确认：DeepRouter Anthropic 直连正常。"
                        }
                    ],
                    max_tokens=64,
                    stream=False
                )
            else:
                # 其他错误，直接抛出
                raise
        
        # 提取文本内容
        text_parts = []
        if hasattr(response, 'content') and response.content:
            for block in response.content:
                if hasattr(block, 'type') and block.type == 'text':
                    if hasattr(block, 'text'):
                        text_parts.append(block.text)
        
        response_text = ''.join(text_parts) if text_parts else str(response)
        
        # 提取 usage 信息
        usage = {}
        if hasattr(response, 'usage'):
            usage = {
                "input_tokens": getattr(response.usage, 'input_tokens', 0),
                "output_tokens": getattr(response.usage, 'output_tokens', 0),
            }
        
        return True, response_text, usage, None
        
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        # 尝试提取 HTTP 状态码
        status_code = None
        if hasattr(e, 'status_code'):
            status_code = e.status_code
        elif hasattr(e, 'response') and hasattr(e.response, 'status_code'):
            status_code = e.response.status_code
        
        error_detail = f"{error_type}: {error_msg}"
        if status_code:
            error_detail = f"HTTP {status_code} - {error_detail}"
        
        return False, "", {}, error_detail


def main():
    """主函数"""
    print("=" * 60)
    print("DeepRouter Anthropic 模式连通性验证")
    print("=" * 60)
    
    # 0. 从 .env.local 加载配置（如果存在）
    load_env_local()
    
    # 1. 加载配置
    print("\n1. 加载配置...")
    try:
        api_key, base_url, model = load_config()
        print(f"   ✓ API Key: 已加载 (长度: {len(api_key)})")
        print(f"   ✓ Base URL: {base_url}")
        print(f"   ✓ 模型: {model}")
    except SystemExit:
        return 1
    except Exception as e:
        print(f"   ✗ 配置加载失败: {e}")
        return 1
    
    # 2. 创建 Anthropic 客户端
    print("\n2. 初始化 Anthropic 客户端...")
    try:
        client = create_anthropic_client(api_key, base_url)
        print(f"   ✓ 客户端已创建")
        print(f"   ✓ 使用 DeepRouter 网关: {base_url}")
        print(f"   ✓ 目标模型: {model}")
    except SystemExit:
        return 1
    except Exception as e:
        print(f"   ✗ 客户端初始化失败: {e}")
        return 1
    
    # 3. 发送测试请求
    print("\n3. 发送测试请求...")
    print("   系统提示: '你是一个用于 DeepRouter 连接测试的诊断助手。'")
    print("   用户消息: '请用不超过 20 个中文字确认：DeepRouter Anthropic 直连正常。'")
    print("   max_tokens: 64")
    
    success, response_text, usage, error = send_test_request(client, model)
    
    # 4. 打印结果
    print("\n4. 测试结果:")
    print("-" * 60)
    
    if success:
        print("   ✓ 请求成功！")
        print(f"\n   模型回复 (前200字):")
        print(f"   {response_text[:200]}")
        if len(response_text) > 200:
            print("   ...")
        
        if usage:
            total_tokens = usage.get('input_tokens', 0) + usage.get('output_tokens', 0)
            print(f"\n   Token 使用:")
            print(f"   输入 tokens: {usage.get('input_tokens', 0)}")
            print(f"   输出 tokens: {usage.get('output_tokens', 0)}")
            print(f"   总计: {total_tokens}")
        
        print("\n" + "=" * 60)
        print("✓ DeepRouter Anthropic 模式验证通过！")
        print("=" * 60)
        return 0
    else:
        print("   ✗ 请求失败")
        print(f"\n   错误详情:")
        print(f"   {error}")
        
        print("\n" + "=" * 60)
        print("✗ DeepRouter Anthropic 直连失败")
        print("=" * 60)
        print("\n可能的原因:")
        print("1. ANTHROPIC_API_KEY 无效或已过期")
        print("2. ANTHROPIC_BASE_URL 不正确")
        print("3. DeepRouter 服务暂时不可用")
        print("4. 网络连接问题")
        print("5. 模型名称不正确或账户无权限")
        print("6. DeepRouter token 可能只支持 'claude code' 模式，不支持标准 Anthropic API 格式")
        print("\n建议:")
        print("- 检查 DeepRouter 控制台，确认 token 是否支持 Anthropic API 格式")
        print("- 尝试联系 DeepRouter 客服确认账户权限")
        print("- 查看 DeepRouter 文档确认正确的调用方式")
        return 1


if __name__ == "__main__":
    sys.exit(main())

