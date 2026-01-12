"""
直接测试 API 端点，查看具体错误
"""

import requests
import json

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1/dashboards/ceo/v3/overview?period=2026-01"

# 使用 admin 账号的 token（需要先登录获取）
# 这里先测试不带 token 的情况，看看错误信息
print("=" * 60)
print("测试 CEO Dashboard API")
print("=" * 60)
print(f"URL: {API_URL}\n")

try:
    # 先测试不带认证
    print("1. 测试不带认证...")
    response = requests.get(API_URL, timeout=10)
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"   错误: {e}")

print("\n" + "=" * 60)
print("请查看后端控制台日志，查找以下信息:")
print("  - Error in CEO dashboard V3 overview: ...")
print("  - Error getting cash status: ...")
print("  - Error getting profit summary: ...")
print("  - 或其他异常堆栈信息")
print("=" * 60)

