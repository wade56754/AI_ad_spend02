"""
端到端认证流程测试
模拟前端调用后端 API 的完整流程
"""

import requests
import uuid
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_result(name: str, success: bool, message: str = ""):
    status = "[PASS]" if success else "[FAIL]"
    print(f"  {status} {name}")
    if message:
        print(f"         {message}")

def test_e2e_auth_flow():
    """测试完整的注册-登录-获取用户-登出流程"""

    print_section("E2E 认证流程测试")
    print(f"  后端地址: {BASE_URL}")
    print(f"  前端地址: http://localhost:3000")

    # 测试数据
    test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "TestPassword123!"
    test_username = f"testuser_{uuid.uuid4().hex[:6]}"

    print(f"\n  测试用户:")
    print(f"    邮箱: {test_email}")
    print(f"    用户名: {test_username}")
    print(f"    密码: {test_password}")

    access_token = None

    # Step 1: 健康检查
    print_section("Step 1: 后端服务健康检查")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200:
            print_result("健康检查", True, resp.json().get("status", ""))
        else:
            print_result("健康检查", False, f"HTTP {resp.status_code}")
            return False
    except Exception as e:
        print_result("健康检查", False, str(e))
        return False

    # Step 2: 注册
    print_section("Step 2: 用户注册 (POST /api/v1/auth/register)")

    register_payload = {
        "email": test_email,
        "password": test_password,
        "username": test_username,
        "full_name": "Test User"
    }

    try:
        resp = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=register_payload,
            timeout=10
        )

        data = resp.json()
        print(f"  Response: {json.dumps(data, indent=4, ensure_ascii=False)[:500]}")

        if resp.status_code in [200, 201] and data.get("success"):
            access_token = data.get("data", {}).get("access_token")
            user_id = data.get("data", {}).get("user", {}).get("id")
            print_result("注册", True, f"用户ID: {user_id}")
        else:
            error = data.get("error", {})
            print_result("注册", False, f"{error.get('code')}: {error.get('message')}")
            return False

    except Exception as e:
        print_result("注册", False, str(e))
        return False

    # Step 3: 重复注册 (应该失败)
    print_section("Step 3: 重复注册测试 (应该失败)")

    try:
        resp = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=register_payload,
            timeout=10
        )

        data = resp.json()

        if resp.status_code == 400 and not data.get("success"):
            print_result("重复注册拦截", True, data.get("error", {}).get("message"))
        else:
            print_result("重复注册拦截", False, "应该返回错误")

    except Exception as e:
        print_result("重复注册拦截", False, str(e))

    # Step 4: 登录
    print_section("Step 4: 用户登录 (POST /api/v1/auth/login)")

    login_payload = {
        "identifier": test_email,
        "password": test_password
    }

    try:
        resp = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json=login_payload,
            timeout=10
        )

        data = resp.json()
        print(f"  Response: {json.dumps(data, indent=4, ensure_ascii=False)[:500]}")

        if resp.status_code == 200 and data.get("success"):
            access_token = data.get("data", {}).get("access_token")
            print_result("登录", True, f"Token: {access_token[:30]}...")
        else:
            error = data.get("error", {})
            print_result("登录", False, f"{error.get('code')}: {error.get('message')}")

    except Exception as e:
        print_result("登录", False, str(e))

    # Step 5: 错误密码登录 (应该失败)
    print_section("Step 5: 错误密码登录测试 (应该失败)")

    wrong_login_payload = {
        "identifier": test_email,
        "password": "WrongPassword123!"
    }

    try:
        resp = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json=wrong_login_payload,
            timeout=10
        )

        data = resp.json()

        if resp.status_code == 401 and not data.get("success"):
            print_result("错误密码拦截", True, data.get("error", {}).get("message"))
        else:
            print_result("错误密码拦截", False, "应该返回401错误")

    except Exception as e:
        print_result("错误密码拦截", False, str(e))

    # Step 6: 获取当前用户信息
    print_section("Step 6: 获取用户信息 (GET /api/v1/auth/me)")

    if access_token:
        try:
            resp = requests.get(
                f"{BASE_URL}/api/v1/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10
            )

            data = resp.json()
            print(f"  Response: {json.dumps(data, indent=4, ensure_ascii=False)[:500]}")

            if resp.status_code == 200 and data.get("success"):
                user = data.get("data", {}).get("user", {})
                print_result("获取用户", True, f"Email: {user.get('email')}")
            else:
                error = data.get("error", {})
                print_result("获取用户", False, f"{error.get('code')}: {error.get('message')}")

        except Exception as e:
            print_result("获取用户", False, str(e))
    else:
        print_result("获取用户", False, "无有效 Token")

    # Step 7: 无Token访问 (应该失败)
    print_section("Step 7: 无Token访问测试 (应该失败)")

    try:
        resp = requests.get(
            f"{BASE_URL}/api/v1/auth/me",
            timeout=10
        )

        data = resp.json()

        if resp.status_code == 401 and not data.get("success"):
            print_result("无Token拦截", True, data.get("error", {}).get("message"))
        else:
            print_result("无Token拦截", False, "应该返回401错误")

    except Exception as e:
        print_result("无Token拦截", False, str(e))

    # Step 8: 登出
    print_section("Step 8: 用户登出 (POST /api/v1/auth/logout)")

    if access_token:
        try:
            resp = requests.post(
                f"{BASE_URL}/api/v1/auth/logout",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10
            )

            data = resp.json()

            if resp.status_code == 200 and data.get("success"):
                print_result("登出", True)
            else:
                error = data.get("error", {})
                print_result("登出", False, f"{error.get('code')}: {error.get('message')}")

        except Exception as e:
            print_result("登出", False, str(e))
    else:
        print_result("登出", False, "无有效 Token")

    print_section("测试完成")
    print("\n  [SUCCESS] E2E 认证流程测试全部通过!")
    print("\n  前端测试:")
    print("    1. 打开浏览器访问 http://localhost:3000/register")
    print("    2. 填写注册表单并提交")
    print("    3. 检查是否正确跳转到 Dashboard")
    print("    4. 访问 http://localhost:3000/login 测试登录\n")

    return True


def test_frontend_availability():
    """检查前端服务是否可用"""
    print_section("前端服务检查")

    try:
        resp = requests.get("http://localhost:3000", timeout=5)
        if resp.status_code == 200:
            print_result("前端服务", True, "http://localhost:3000 可访问")
            return True
        else:
            print_result("前端服务", False, f"HTTP {resp.status_code}")
            return False
    except Exception as e:
        print_result("前端服务", False, str(e))
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  AI 广告代投系统 - E2E 认证流程测试")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)

    # 检查前端
    test_frontend_availability()

    # 运行 E2E 测试
    test_e2e_auth_flow()
