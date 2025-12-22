"""通过 HTTP 测试 API 响应"""
import sys
import os
import json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests

BASE_URL = "http://localhost:8000/api/v1"

# 登录
print("登录中...")
login_resp = requests.post(f"{BASE_URL}/auth/login", json={
    "identifier": "qwc1032217993@gmail.com",
    "password": "Qwc@199538"  # 尝试常见密码
})

if login_resp.status_code != 200:
    print(f"登录失败: {login_resp.json()}")
    # 尝试其他方式
    print("\n尝试直接检查响应格式...")

    # 读取本地 token（如果有）
    token_file = os.path.join(os.path.dirname(__file__), '.token')
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            token = f.read().strip()
    else:
        print("没有保存的 token")
        exit(1)
else:
    data = login_resp.json()
    token = data.get('data', {}).get('access_token')
    print(f"登录成功，token: {token[:30]}...")

# 获取日报
print("\n获取日报...")
headers = {"Authorization": f"Bearer {token}"}
resp = requests.get(f"{BASE_URL}/daily-reports?page=1&page_size=5", headers=headers)
print(f"响应状态: {resp.status_code}")

if resp.status_code == 200:
    data = resp.json()
    print(f"success: {data.get('success')}")
    print(f"data 长度: {len(data.get('data', []))}")

    print("\n前3条记录的关键字段:")
    for i, item in enumerate(data.get('data', [])[:3]):
        print(f"\n记录 {i+1}:")
        print(f"  id: {item.get('id')}")
        print(f"  report_date: {item.get('report_date')}")
        print(f"  submitter_name: {item.get('submitter_name')}")
        print(f"  team_name: {item.get('team_name')}")
        print(f"  region: {item.get('region')}")

    # 检查响应中所有的键
    if data.get('data'):
        first_item = data['data'][0]
        print(f"\n第一条记录的所有键: {list(first_item.keys())}")
else:
    print(f"请求失败: {resp.json()}")
