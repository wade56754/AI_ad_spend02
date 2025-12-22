"""测试 API 响应"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# 登录
login_resp = requests.post(f"{BASE_URL}/auth/login", json={
    "identifier": "qwc1032217993@gmail.com",
    "password": "123456"
})
print("登录响应:", login_resp.status_code)
login_data = login_resp.json()
if not login_data.get("success"):
    print("登录失败:", login_data)
    exit(1)

token = login_data["data"]["access_token"]
print(f"Token: {token[:30]}...")

# 获取日报
headers = {"Authorization": f"Bearer {token}"}
reports_resp = requests.get(f"{BASE_URL}/daily-reports?page=1&page_size=3", headers=headers)
print("\n日报响应:", reports_resp.status_code)
reports_data = reports_resp.json()

if reports_data.get("success"):
    print(f"总数: {reports_data.get('meta', {}).get('pagination', {}).get('total', 'N/A')}")
    print("\n前3条数据:")
    for i, report in enumerate(reports_data.get("data", [])[:3]):
        print(f"\n--- 记录 {i+1} ---")
        print(f"  日期: {report.get('report_date')}")
        print(f"  账户名: {report.get('ad_account_name', 'N/A')}")
        print(f"  投手名: {report.get('submitter_name', 'NULL')}")
        print(f"  团队名: {report.get('team_name', 'NULL')}")
        print(f"  地区: {report.get('region')}")
        print(f"  平台: {report.get('platform')}")
        print(f"  消耗: {report.get('raw_spend')}")
else:
    print("获取日报失败:", reports_data)
