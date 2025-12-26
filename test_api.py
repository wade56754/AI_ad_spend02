"""Test daily reports API"""

import requests
import json

# 尝试登录获取 token
login_data = {"identifier": "admin@test.com", "password": "admin123"}

try:
    resp = requests.post(
        "http://localhost:8000/api/v1/auth/login", json=login_data, timeout=10
    )
    print(f"Login Status: {resp.status_code}")
    data = resp.json()

    if resp.status_code == 200 and data.get("success"):
        print(f"Login data: {json.dumps(data, ensure_ascii=False)[:300]}")
        # Token is in data.session.access_token
        token = data.get("data", {}).get("session", {}).get("access_token")
        if not token:
            print("No access_token in response!")
            exit(1)
        print(f"Token: {token[:50]}...")

        # 用 token 测试日报 API
        headers = {"Authorization": f"Bearer {token}"}
        resp2 = requests.get(
            "http://localhost:8000/api/v1/daily-reports?page=1&page_size=5",
            headers=headers,
            timeout=10,
        )
        print(f"\nDaily Reports Status: {resp2.status_code}")
        data2 = resp2.json()
        print(f'Success: {data2.get("success")}')
        print(f"Response keys: {data2.keys()}")
        print(f"Data type: {type(data2.get('data'))}")

        # Handle different response structures
        response_data = data2.get("data", {})
        if isinstance(response_data, dict):
            items = response_data.get("items", [])
            meta = response_data.get("meta", {})
            pagination = meta.get("pagination", {}) if isinstance(meta, dict) else {}
            total = pagination.get("total", 0)
        else:
            items = response_data if isinstance(response_data, list) else []
            total = len(items)

        print(f"Total: {total}")
        print(f"Items count: {len(items)}")
        if items:
            first = items[0]
            print(f'First item ID: {first.get("id")}')
            print(f'First item date: {first.get("report_date")}')
            print(f'First item status: {first.get("status")}')
    else:
        print(f"Login failed: {json.dumps(data, ensure_ascii=False)}")
except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
