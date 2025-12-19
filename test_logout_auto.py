"""
使用 Playwright 自动测试登出功能
"""

import asyncio
import uuid
import sys
from datetime import datetime

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("[ERROR] 请安装 playwright: pip install playwright")
    sys.exit(1)


async def test_logout():
    """自动测试登出功能"""

    print("\n" + "="*60)
    print("  Playwright 登出功能自动测试")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)

    # 测试数据
    test_id = uuid.uuid4().hex[:8]
    test_email = f"test_{test_id}@example.com"
    test_password = "TestPassword123!"
    test_username = f"testuser_{test_id}"

    print(f"\n测试用户:")
    print(f"  邮箱: {test_email}")
    print(f"  用户名: {test_username}")

    results = []

    async with async_playwright() as p:
        # 启动浏览器 (headless 模式)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # ============================================================
            # Step 0: 注册并登录测试用户
            # ============================================================
            print("\n[0/4] 注册测试用户...")

            await page.goto("http://localhost:3000/register", wait_until="networkidle")

            # 填写注册表单
            await page.locator("#username").fill(test_username)
            full_name = page.locator("#full_name")
            if await full_name.count() > 0 and await full_name.is_visible():
                await full_name.fill("Test User")
            await page.locator("#email").fill(test_email)
            await page.locator("#password").fill(test_password)
            await page.locator("#confirmPassword").fill(test_password)

            # 提交注册
            await page.locator("button[type='submit']").click()
            await page.wait_for_timeout(3000)

            # After registration, should redirect to home page (/)
            current_url = page.url
            if current_url == "http://localhost:3000/" or "localhost:3000" in current_url and current_url.endswith("/"):
                print("  [PASS] 用户注册并登录成功")
                results.append(("用户注册登录", True))
            elif "register" not in current_url and "login" not in current_url:
                print(f"  [PASS] 用户注册成功，当前页面: {current_url}")
                results.append(("用户注册登录", True))
            else:
                print(f"  [FAIL] 用户注册失败，当前页面: {current_url}")
                results.append(("用户注册登录", False))
                return results

            await page.screenshot(path="test_screenshots/logout_01_dashboard.png")

            # ============================================================
            # Step 1: 验证当前处于已登录状态
            # ============================================================
            print("\n[1/4] 验证已登录状态...")

            current_url = page.url
            # Home page is at / which is the dashboard
            if "login" not in current_url and "register" not in current_url:
                print(f"  当前URL: {current_url}")
                print("  [PASS] 用户已登录，处于主页/Dashboard")
                results.append(("已登录状态验证", True))
            else:
                print(f"  [FAIL] 未在 Dashboard 页面: {current_url}")
                results.append(("已登录状态验证", False))

            # ============================================================
            # Step 2: 查找并点击登出按钮
            # ============================================================
            print("\n[2/4] 查找登出按钮...")

            # 登出按钮在侧边栏底部，包含"退出登录"文字
            logout_button = page.locator("button:has-text('退出登录')")

            if await logout_button.count() > 0:
                print("  [PASS] 找到登出按钮")
                results.append(("找到登出按钮", True))

                await page.screenshot(path="test_screenshots/logout_02_button_found.png")

                # 点击登出按钮
                print("\n[3/4] 点击登出按钮...")
                await logout_button.click()
                await page.wait_for_timeout(2000)

                await page.screenshot(path="test_screenshots/logout_03_after_click.png")
            else:
                # 尝试其他选择器
                print("  [INFO] 尝试其他选择器...")

                # 尝试通过图标查找
                logout_button = page.locator("button:has-text('🚪')")
                if await logout_button.count() > 0:
                    print("  [PASS] 通过图标找到登出按钮")
                    results.append(("找到登出按钮", True))
                    await logout_button.click()
                    await page.wait_for_timeout(2000)
                else:
                    print("  [FAIL] 未找到登出按钮")
                    results.append(("找到登出按钮", False))
                    await page.screenshot(path="test_screenshots/logout_error_no_button.png")
                    return results

            # ============================================================
            # Step 4: 验证登出结果
            # ============================================================
            print("\n[4/4] 验证登出结果...")

            current_url = page.url
            print(f"  当前URL: {current_url}")

            await page.screenshot(path="test_screenshots/logout_04_result.png")

            if "login" in current_url:
                print("  [PASS] 登出成功 - 已跳转到登录页面")
                results.append(("登出跳转", True))
            elif "register" in current_url:
                print("  [PASS] 登出成功 - 已跳转到注册页面")
                results.append(("登出跳转", True))
            else:
                print(f"  [INFO] 当前页面: {current_url}")
                # 检查是否还能访问受保护的页面
                # 尝试直接访问主页 (dashboard)
                await page.goto("http://localhost:3000/", wait_until="networkidle")
                await page.wait_for_timeout(1000)

                final_url = page.url
                if "login" in final_url or "register" in final_url:
                    print("  [PASS] 登出成功 - 无法访问受保护页面")
                    results.append(("登出跳转", True))
                else:
                    print(f"  [FAIL] 登出可能未成功，仍可访问: {final_url}")
                    results.append(("登出跳转", False))

            # ============================================================
            # 额外验证: 检查 Token 是否被清除
            # ============================================================
            print("\n[额外] 验证 Token 清除...")

            # 检查 localStorage 中的 token
            token = await page.evaluate("localStorage.getItem('auth_token') || localStorage.getItem('token') || localStorage.getItem('access_token')")

            if token is None or token == "":
                print("  [PASS] Token 已清除")
                results.append(("Token清除", True))
            else:
                print(f"  [WARN] Token 仍存在: {token[:20]}...")
                results.append(("Token清除", False))

        except Exception as e:
            print(f"\n[ERROR] {e}")
            try:
                await page.screenshot(path="test_screenshots/logout_error.png")
            except:
                pass
            results.append(("测试执行", False))

        finally:
            await browser.close()

    return results


def print_summary(results):
    """打印测试摘要"""
    print("\n" + "="*60)
    print("  登出测试结果摘要")
    print("="*60)

    passed = 0
    failed = 0

    for name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status} {name}")
        if success:
            passed += 1
        else:
            failed += 1

    print(f"\n  总计: {passed} 通过, {failed} 失败")
    print("\n  截图保存在: test_screenshots/")
    print("="*60)

    return failed == 0


if __name__ == "__main__":
    import os

    # 创建截图目录
    os.makedirs("test_screenshots", exist_ok=True)

    # 运行测试
    results = asyncio.run(test_logout())

    # 打印摘要
    success = print_summary(results)

    sys.exit(0 if success else 1)
