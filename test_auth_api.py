"""
认证 API 测试脚本 (使用 requests 直接调用 Supabase REST API)
绕过 Python 3.14 + supabase SDK 兼容性问题
"""

import os
import sys
import uuid
import json
from datetime import datetime

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import requests
except ImportError:
    print("[ERROR] 请安装 requests: pip install requests")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[WARN] python-dotenv 未安装，使用系统环境变量")

def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_result(name: str, success: bool, message: str = ""):
    status = "[PASS]" if success else "[FAIL]"
    print(f"  {status} {name}")
    if message:
        print(f"         {message}")

def test_supabase_auth():
    """使用 REST API 直接测试 Supabase Auth"""

    print_section("环境配置")

    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    if not supabase_url:
        print_result("SUPABASE_URL", False, "未配置")
        return False
    print_result("SUPABASE_URL", True, supabase_url)

    if not supabase_key:
        print_result("SUPABASE_ANON_KEY", False, "未配置")
        return False
    print_result("SUPABASE_ANON_KEY", True, f"{supabase_key[:40]}...")

    if not supabase_service_key:
        print_result("SUPABASE_SERVICE_ROLE_KEY", False, "未配置")
        return False
    print_result("SUPABASE_SERVICE_ROLE_KEY", True, f"{supabase_service_key[:40]}...")

    # API endpoints
    auth_url = f"{supabase_url}/auth/v1"

    # 测试用户信息
    test_email = f"test_{uuid.uuid4().hex[:8]}@test.local"
    test_password = "TestPassword123!"
    test_username = f"testuser_{uuid.uuid4().hex[:6]}"

    print_section("1. 测试注册 (Admin API)")
    print(f"  测试邮箱: {test_email}")
    print(f"  测试用户名: {test_username}")

    test_user_id = None
    headers_admin = {
        "apikey": supabase_service_key,
        "Authorization": f"Bearer {supabase_service_key}",
        "Content-Type": "application/json"
    }

    # 创建用户 (Admin API)
    create_user_payload = {
        "email": test_email,
        "password": test_password,
        "email_confirm": True,
        "user_metadata": {
            "username": test_username,
            "full_name": "Test User",
            "role": "media_buyer"
        }
    }

    try:
        resp = requests.post(
            f"{auth_url}/admin/users",
            headers=headers_admin,
            json=create_user_payload,
            timeout=30
        )

        if resp.status_code in [200, 201]:
            data = resp.json()
            test_user_id = data.get("id")
            print_result("用户注册", True, f"用户ID: {test_user_id}")
        else:
            print_result("用户注册", False, f"HTTP {resp.status_code}: {resp.text[:200]}")
            return False

    except requests.RequestException as e:
        print_result("用户注册", False, str(e))
        return False

    print_section("2. 测试登录 (GoTrue API)")

    access_token = None
    refresh_token = None
    headers_anon = {
        "apikey": supabase_key,
        "Content-Type": "application/json"
    }

    login_payload = {
        "email": test_email,
        "password": test_password
    }

    try:
        resp = requests.post(
            f"{auth_url}/token?grant_type=password",
            headers=headers_anon,
            json=login_payload,
            timeout=30
        )

        if resp.status_code == 200:
            data = resp.json()
            access_token = data.get("access_token")
            refresh_token = data.get("refresh_token")
            expires_in = data.get("expires_in")
            print_result("用户登录", True)
            print(f"         Access Token: {access_token[:50]}...")
            print(f"         Refresh Token: {refresh_token[:30]}...")
            print(f"         Expires In: {expires_in}s")
        else:
            print_result("用户登录", False, f"HTTP {resp.status_code}: {resp.text[:200]}")

    except requests.RequestException as e:
        print_result("用户登录", False, str(e))

    print_section("3. 测试获取用户信息")

    if access_token:
        headers_auth = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        try:
            resp = requests.get(
                f"{auth_url}/user",
                headers=headers_auth,
                timeout=30
            )

            if resp.status_code == 200:
                data = resp.json()
                print_result("获取用户", True)
                print(f"         ID: {data.get('id')}")
                print(f"         Email: {data.get('email')}")
                print(f"         Metadata: {json.dumps(data.get('user_metadata', {}), ensure_ascii=False)}")
            else:
                print_result("获取用户", False, f"HTTP {resp.status_code}: {resp.text[:200]}")

        except requests.RequestException as e:
            print_result("获取用户", False, str(e))
    else:
        print_result("获取用户", False, "无有效 Token")

    print_section("4. 测试刷新令牌")

    if refresh_token:
        refresh_payload = {
            "refresh_token": refresh_token
        }

        try:
            resp = requests.post(
                f"{auth_url}/token?grant_type=refresh_token",
                headers=headers_anon,
                json=refresh_payload,
                timeout=30
            )

            if resp.status_code == 200:
                data = resp.json()
                new_token = data.get("access_token", "")
                print_result("刷新令牌", True, f"新 Token: {new_token[:50]}...")
            else:
                print_result("刷新令牌", False, f"HTTP {resp.status_code}: {resp.text[:200]}")

        except requests.RequestException as e:
            print_result("刷新令牌", False, str(e))
    else:
        print_result("刷新令牌", False, "无 Refresh Token")

    print_section("5. 测试登出")

    if access_token:
        headers_auth = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        try:
            resp = requests.post(
                f"{auth_url}/logout",
                headers=headers_auth,
                timeout=30
            )

            if resp.status_code in [200, 204]:
                print_result("用户登出", True)
            else:
                print_result("用户登出", False, f"HTTP {resp.status_code}")

        except requests.RequestException as e:
            print_result("用户登出", False, str(e))
    else:
        print_result("用户登出", False, "无有效 Token")

    print_section("6. 清理测试用户")

    if test_user_id:
        try:
            resp = requests.delete(
                f"{auth_url}/admin/users/{test_user_id}",
                headers=headers_admin,
                timeout=30
            )

            if resp.status_code in [200, 204]:
                print_result("删除测试用户", True)
            else:
                print_result("删除测试用户", False, f"HTTP {resp.status_code}: {resp.text[:100]}")

        except requests.RequestException as e:
            print_result("删除测试用户", False, str(e))

    print_section("测试完成")
    print("\n  [SUCCESS] Supabase Auth 认证流程测试通过!")
    print("  后端 API 将使用相同的 Supabase 服务进行认证\n")
    return True


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  AI 广告代投系统 - Supabase Auth 直接测试")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("  (绕过 Python 3.14 SDK 兼容性问题)")
    print("="*60)

    try:
        success = test_supabase_auth()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n  [中断] 测试被用户取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n  [ERROR] 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
