"""
API 认证流程端到端测试
测试完整的注册、登录、访问受保护API的流程
"""

import requests
import json
from datetime import datetime

# 配置
API_BASE_URL = "http://localhost:8000"
SUPABASE_URL = "https://jzmcoivxhiyidizncyaq.supabase.co"

# 测试用户
TEST_USER = {
    "email": "api_test@example.com",
    "password": "Test123456!",
    "metadata": {
        "username": "api_tester",
        "full_name": "API测试用户",
        "role": "media_buyer"
    }
}


class APIAuthTester:
    """API 认证测试器"""

    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None

    def print_section(self, title):
        """打印分节标题"""
        print(f"\n{'='*60}")
        print(f"{title}")
        print(f"{'='*60}\n")

    def print_result(self, success, message):
        """打印测试结果"""
        status = "[OK]" if success else "[FAIL]"
        print(f"{status} {message}")

    def test_1_backend_health(self):
        """测试1：检查后端健康状态"""
        self.print_section("测试 1: 后端健康检查")

        try:
            response = self.session.get(f"{API_BASE_URL}/health", timeout=5)

            if response.status_code == 200:
                self.print_result(True, "后端API正常运行")
                return True
            else:
                self.print_result(False, f"后端返回状态码: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.print_result(False, "无法连接到后端服务")
            print(f"     请确保后端正在运行: uvicorn main:app --reload")
            return False
        except Exception as e:
            self.print_result(False, f"健康检查失败: {str(e)}")
            return False

    def test_2_supabase_registration(self):
        """测试2：通过Supabase注册用户"""
        self.print_section("测试 2: Supabase 用户注册")

        from supabase import create_client

        try:
            # 使用service role key清理旧用户
            service_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp6bWNvaXZ4aGl5aWRpem5jeWFxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjMxNzgxMSwiZXhwIjoyMDc3ODkzODExfQ.IP2Gu-KIYDJvd2ahKLc60dca5KWV90uNHN7GtE5Sx8s'
            supabase = create_client(SUPABASE_URL, service_key)

            # 删除测试用户（如果存在）
            try:
                users = supabase.auth.admin.list_users()
                for user in users:
                    if user.email == TEST_USER["email"]:
                        supabase.auth.admin.delete_user(user.id)
                        print(f"[INFO] 已删除旧测试用户")
                        break
            except:
                pass

            # 创建新用户
            response = supabase.auth.admin.create_user({
                "email": TEST_USER["email"],
                "password": TEST_USER["password"],
                "email_confirm": True,
                "user_metadata": TEST_USER["metadata"]
            })

            if response.user:
                self.user_id = response.user.id
                self.print_result(True, f"用户注册成功")
                print(f"     用户ID: {self.user_id}")
                print(f"     邮箱: {response.user.email}")
                return True
            else:
                self.print_result(False, "用户注册失败")
                return False

        except Exception as e:
            self.print_result(False, f"注册失败: {str(e)}")
            return False

    def test_3_supabase_login(self):
        """测试3：通过Supabase登录"""
        self.print_section("测试 3: Supabase 用户登录")

        from supabase import create_client

        try:
            # 使用service role key进行测试登录
            service_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp6bWNvaXZ4aGl5aWRpem5jeWFxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjMxNzgxMSwiZXhwIjoyMDc3ODkzODExfQ.IP2Gu-KIYDJvd2ahKLc60dca5KWV90uNHN7GtE5Sx8s'
            print("[INFO] 使用 Service Role Key 进行登录测试")

            supabase = create_client(SUPABASE_URL, service_key)

            response = supabase.auth.sign_in_with_password({
                "email": TEST_USER["email"],
                "password": TEST_USER["password"]
            })

            if response.session:
                self.access_token = response.session.access_token
                self.print_result(True, "登录成功")
                print(f"     Access Token: {self.access_token[:50]}...")
                print(f"     Expires At: {response.session.expires_at}")
                return True
            else:
                self.print_result(False, "登录失败")
                return False

        except Exception as e:
            self.print_result(False, f"登录失败: {str(e)}")
            return False

    def test_4_backend_token_validation(self):
        """测试4：后端验证Supabase Token"""
        self.print_section("测试 4: 后端验证 Supabase Token")

        if not self.access_token:
            self.print_result(False, "未获取到 Access Token，跳过测试")
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            # 调用受保护的API端点
            response = self.session.get(
                f"{API_BASE_URL}/api/v1/auth/me",
                headers=headers,
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                self.print_result(True, "Token验证成功")
                print(f"     用户信息: {json.dumps(data.get('data', {}), indent=2, ensure_ascii=False)}")
                return True
            elif response.status_code == 404:
                self.print_result(False, "API端点不存在")
                print(f"     可能需要实现 /api/v1/auth/me 端点")
                return False
            else:
                self.print_result(False, f"Token验证失败: {response.status_code}")
                print(f"     响应: {response.text}")
                return False

        except Exception as e:
            self.print_result(False, f"请求失败: {str(e)}")
            return False

    def test_5_access_protected_resource(self):
        """测试5：访问受保护的资源"""
        self.print_section("测试 5: 访问受保护资源")

        if not self.access_token:
            self.print_result(False, "未获取到 Access Token，跳过测试")
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            # 尝试访问项目列表
            response = self.session.get(
                f"{API_BASE_URL}/api/v1/projects",
                headers=headers,
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                self.print_result(True, "成功访问受保护资源")
                print(f"     项目数: {len(data.get('data', {}).get('items', []))}")
                return True
            elif response.status_code == 401:
                self.print_result(False, "认证失败（401）")
                print(f"     可能需要在后端配置Supabase认证")
                return False
            else:
                self.print_result(False, f"访问失败: {response.status_code}")
                return False

        except Exception as e:
            self.print_result(False, f"请求失败: {str(e)}")
            return False

    def test_6_unauthorized_access(self):
        """测试6：未授权访问应被拒绝"""
        self.print_section("测试 6: 测试未授权访问")

        try:
            # 不带Token访问受保护资源
            response = self.session.get(
                f"{API_BASE_URL}/api/v1/projects",
                timeout=5
            )

            if response.status_code == 401:
                self.print_result(True, "正确拒绝未授权访问")
                return True
            else:
                self.print_result(False, f"应该返回401，实际返回: {response.status_code}")
                return False

        except Exception as e:
            self.print_result(False, f"请求失败: {str(e)}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("API 认证流程端到端测试")
        print("="*60)

        results = {
            "backend_health": self.test_1_backend_health(),
            "registration": self.test_2_supabase_registration(),
            "login": self.test_3_supabase_login(),
            "token_validation": self.test_4_backend_token_validation(),
            "protected_access": self.test_5_access_protected_resource(),
            "unauthorized": self.test_6_unauthorized_access(),
        }

        # 总结
        self.print_section("测试总结")

        passed = sum(1 for v in results.values() if v)
        total = len(results)

        print(f"通过: {passed}/{total} 个测试\n")

        for test_name, result in results.items():
            status = "[PASS]" if result else "[FAIL]"
            print(f"{status} {test_name}")

        print("\n" + "="*60)

        if passed == total:
            print("[SUCCESS] 所有测试通过！")
        else:
            print("[WARNING] 部分测试未通过")

        print("="*60)

        # 下一步建议
        print("\n下一步:")
        if not results["backend_health"]:
            print("  1. 启动后端服务: cd backend && uvicorn main:app --reload")
        if not results["token_validation"]:
            print("  2. 确保后端已集成 Supabase 认证中间件")
            print("     参考: backend/deps/supabase_auth.py")
        if passed == total:
            print("  1. 在前端测试登录功能")
            print("  2. 验证 RLS 策略效果")
            print("  3. 测试不同角色的权限")


def main():
    """主函数"""
    tester = APIAuthTester()
    tester.run_all_tests()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] 测试已中断")
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
