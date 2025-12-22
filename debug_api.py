"""调试 API 响应"""
import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000/api/v1"

# 使用本地认证
login_resp = requests.post(f"{BASE_URL}/auth/login", json={
    "identifier": "admin@example.com",
    "password": "admin123"
})
print(f"登录响应: {login_resp.status_code}")

if login_resp.status_code != 200:
    # 尝试创建管理员用户
    print("尝试使用现有 token...")
    # 直接查询数据库中是否有数据

print(login_resp.json())
