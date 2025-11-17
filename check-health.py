#!/usr/bin/env python3
"""
AI广告代投系统 - 健康检查脚本
用于验证系统是否正常启动
"""
import json
import requests
import time
import sys
from typing import Dict, Any

def check_backend_health() -> Dict[str, Any]:
    """检查后端健康状态"""
    try:
        response = requests.get("http://localhost:8000/healthz", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "healthy",
                "response_time": response.elapsed.total_seconds(),
                "data": data
            }
        else:
            return {
                "status": "unhealthy",
                "error": f"HTTP {response.status_code}",
                "response": response.text
            }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": str(e)
        }

def check_frontend_health() -> Dict[str, Any]:
    """检查前端健康状态"""
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            return {
                "status": "healthy",
                "response_time": response.elapsed.total_seconds(),
                "content_type": response.headers.get("content-type", "")
            }
        else:
            return {
                "status": "unhealthy",
                "error": f"HTTP {response.status_code}",
                "response": response.text[:200]  # 只显示前200字符
            }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": str(e)
        }

def check_api_docs() -> Dict[str, Any]:
    """检查API文档"""
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            return {
                "status": "available",
                "response_time": response.elapsed.total_seconds()
            }
        else:
            return {
                "status": "unavailable",
                "error": f"HTTP {response.status_code}"
            }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": str(e)
        }

def main():
    print("🔍 AI广告代投系统健康检查")
    print("=" * 50)

    # 等待系统启动
    print("⏳ 等待系统启动...")
    time.sleep(2)

    # 检查各个组件
    checks = {
        "后端API": check_backend_health(),
        "前端界面": check_frontend_health(),
        "API文档": check_api_docs()
    }

    all_healthy = True

    for name, result in checks.items():
        status = result.get("status", "unknown")
        if status == "healthy" or status == "available":
            icon = "✅"
            status_text = "正常"
        elif status == "unhealthy":
            icon = "⚠️"
            status_text = "异常"
            all_healthy = False
        else:
            icon = "❌"
            status_text = "错误"
            all_healthy = False

        print(f"{icon} {name}: {status_text}")

        if "response_time" in result:
            print(f"   ⏱️ 响应时间: {result['response_time']:.3f}s")

        if "error" in result:
            print(f"   🚨 错误: {result['error']}")

        print()

    # 总结
    print("=" * 50)
    if all_healthy:
        print("🎉 所有组件运行正常！")
        print("📡 后端API: http://localhost:8000")
        print("🌐 前端界面: http://localhost:3000")
        print("📚 API文档: http://localhost:8000/docs")
        sys.exit(0)
    else:
        print("❌ 部分组件存在问题，请检查日志")
        sys.exit(1)

if __name__ == "__main__":
    main()