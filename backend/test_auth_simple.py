#!/usr/bin/env python3
"""
简化的认证模块测试
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """测试导入"""
    try:
        from services.auth_service import AuthService
        from routers.authentication import router
        print("[成功] 认证模块导入成功")
        return True
    except Exception as e:
        print(f"[失败] 导入失败: {e}")
        return False

def test_main_router():
    """测试主路由注册"""
    try:
        from main import app
        routes = [route.path for route in app.routes]

        # 检查认证路由是否注册
        auth_routes = [r for r in routes if '/auth' in r or '/authentication' in r]
        if auth_routes:
            print(f"[成功] 认证路由已注册: {auth_routes[:5]}...")  # 只显示前5个
            return True
        else:
            print("[失败] 认证路由未注册")
            return False
    except Exception as e:
        print(f"[失败] 路由检查失败: {e}")
        return False

def test_auth_endpoints():
    """测试认证端点"""
    try:
        from main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # 测试健康检查
        response = client.get("/api/v1/health")
        if response.status_code == 200:
            print("[成功] API健康检查通过")
        else:
            print(f"[失败] API健康检查失败: {response.status_code}")

        # 测试认证端点是否存在
        response = client.post("/api/v1/auth/register")
        # 应该返回422（参数验证错误）而不是404（路由不存在）
        if response.status_code == 422:
            print("[成功] 认证注册端点存在")
            return True
        else:
            print(f"[失败] 认证注册端点可能不存在: {response.status_code}")
            return False
    except Exception as e:
        print(f"[失败] 端点测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("\n开始认证模块测试...")
    print("=" * 50)

    results = []

    # 运行测试
    print("\n1. 测试模块导入...")
    results.append(test_imports())

    print("\n2. 测试路由注册...")
    results.append(test_main_router())

    print("\n3. 测试API端点...")
    results.append(test_auth_endpoints())

    # 汇总结果
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"[成功] 所有测试通过! ({passed}/{total})")
        print("\n[完成] 认证授权模块已成功完成！")
    else:
        print(f"[警告] 部分测试未通过 ({passed}/{total})")
        print("请检查错误信息并修复问题")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)