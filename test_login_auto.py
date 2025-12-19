"""
使用 Playwright 自动测试登录页面
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


async def test_login_page():
    """自动测试登录页面"""

    print("\n" + "="*60)
    print("  Playwright 登录页面自动测试")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)

    # 测试数据 - 先注册一个用户，然后用该用户测试登录
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
            # Step 0: 先注册一个测试用户
            # ============================================================
            print("\n[0/5] 注册测试用户...")

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

            # 注册成功后重定向到 / (route group不创建URL段)
            current_url = page.url
            if "register" not in current_url and "login" not in current_url:
                print("  [PASS] 用户注册成功")
                results.append(("用户注册", True))

                # 登出以便测试登录
                # 清除 token
                await context.clear_cookies()
                await page.evaluate("localStorage.clear()")
            else:
                print("  [FAIL] 用户注册失败")
                results.append(("用户注册", False))
                return results

            # ============================================================
            # Step 1: 打开登录页面
            # ============================================================
            print("\n[1/5] 打开登录页面...")
            response = await page.goto("http://localhost:3000/login", wait_until="networkidle")

            if response and response.status == 200:
                print("  [PASS] 页面加载成功")
                results.append(("页面加载", True))
            else:
                print(f"  [FAIL] 页面加载失败: {response.status if response else 'No response'}")
                results.append(("页面加载", False))
                return results

            await page.screenshot(path="test_screenshots/login_01_page.png")

            # ============================================================
            # Step 2: 检查表单元素
            # ============================================================
            print("\n[2/5] 检查表单元素...")

            elements = {
                "用户名/邮箱输入框": "#identifier",
                "密码输入框": "#password",
                "记住我复选框": "#remember_me",
                "登录按钮": "button[type='submit']"
            }

            all_visible = True
            for name, selector in elements.items():
                try:
                    elem = page.locator(selector)
                    if await elem.is_visible():
                        print(f"  [OK] {name}")
                    else:
                        print(f"  [FAIL] {name} 不可见")
                        all_visible = False
                except Exception as e:
                    print(f"  [FAIL] {name}: {e}")
                    all_visible = False

            results.append(("表单元素", all_visible))

            # ============================================================
            # Step 3: 测试空表单提交
            # ============================================================
            print("\n[3/5] 测试空表单提交...")

            await page.locator("button[type='submit']").click()
            await page.wait_for_timeout(1000)

            # 检查是否显示错误提示
            # HTML5 required 属性会阻止提交
            current_url = page.url
            if "login" in current_url:
                print("  [PASS] 空表单被正确阻止")
                results.append(("空表单验证", True))
            else:
                print("  [FAIL] 空表单未被阻止")
                results.append(("空表单验证", False))

            await page.screenshot(path="test_screenshots/login_02_empty.png")

            # ============================================================
            # Step 4: 测试错误密码登录
            # ============================================================
            print("\n[4/5] 测试错误密码登录...")

            await page.locator("#identifier").fill(test_email)
            await page.locator("#password").fill("WrongPassword123!")
            await page.locator("button[type='submit']").click()

            await page.wait_for_timeout(3000)
            await page.screenshot(path="test_screenshots/login_03_wrong_password.png")

            # 检查是否还在登录页面 (错误应该被拦截)
            if "login" in page.url:
                print("  [PASS] 错误密码被正确拒绝")
                results.append(("错误密码验证", True))
            else:
                print("  [FAIL] 错误密码未被正确处理")
                results.append(("错误密码验证", False))

            # ============================================================
            # Step 5: 测试正确登录
            # ============================================================
            print("\n[5/5] 测试正确登录...")

            # 清空并重新填写
            await page.locator("#identifier").fill("")
            await page.locator("#password").fill("")

            await page.locator("#identifier").fill(test_email)
            await page.locator("#password").fill(test_password)

            # 勾选"记住我"
            remember_me = page.locator("#remember_me")
            if not await remember_me.is_checked():
                await remember_me.click()

            await page.screenshot(path="test_screenshots/login_04_filled.png")

            # 提交登录
            await page.locator("button[type='submit']").click()

            # 等待响应
            await page.wait_for_timeout(3000)
            await page.screenshot(path="test_screenshots/login_05_result.png")

            # 检查结果
            current_url = page.url
            print(f"  当前URL: {current_url}")

            # 登录成功后重定向到 / (route group不创建URL段)
            if "login" not in current_url and "register" not in current_url:
                print(f"  [PASS] 登录成功 - 已跳转到: {current_url}")
                results.append(("正确登录", True))
            else:
                # 检查 toast 消息
                try:
                    toast = await page.locator("[data-sonner-toast]").first.text_content()
                    print(f"  Toast消息: {toast}")
                    if "成功" in toast or "success" in toast.lower():
                        results.append(("正确登录", True))
                    else:
                        results.append(("正确登录", False))
                except:
                    print("  [FAIL] 登录失败，仍在登录页面")
                    results.append(("正确登录", False))

        except Exception as e:
            print(f"\n[ERROR] {e}")
            try:
                await page.screenshot(path="test_screenshots/login_error.png")
            except:
                pass
            results.append(("测试执行", False))

        finally:
            await browser.close()

    return results


def print_summary(results):
    """打印测试摘要"""
    print("\n" + "="*60)
    print("  登录测试结果摘要")
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
    results = asyncio.run(test_login_page())

    # 打印摘要
    success = print_summary(results)

    sys.exit(0 if success else 1)
