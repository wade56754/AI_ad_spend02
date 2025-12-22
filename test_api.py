import json
import requests

# 1. 登录获取 token
login_response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"identifier": "demo@test.com", "password": "demo1234"}
)
print(f"Login status: {login_response.status_code}")

login_data = login_response.json()
if not login_data.get("success"):
    print(f"Login failed: {login_data}")
    exit(1)

token = login_data["data"]["session"]["access_token"]
print(f"Token length: {len(token)}")
print(f"Token prefix: {token[:50]}...")

# 2. 测试 channels API
channels_response = requests.get(
    "http://localhost:8000/api/v1/channels/?page=1&page_size=1",
    headers={"Authorization": f"Bearer {token}"}
)
print(f"\nChannels API status: {channels_response.status_code}")
print(f"Channels response: {channels_response.text[:500]}")

# 3. 测试 projects API
projects_response = requests.get(
    "http://localhost:8000/api/v1/projects?page=1&page_size=1",
    headers={"Authorization": f"Bearer {token}"}
)
print(f"\nProjects API status: {projects_response.status_code}")
print(f"Projects response: {projects_response.text[:500]}")
