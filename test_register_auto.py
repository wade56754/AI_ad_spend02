"""
使用 Playwright 自动测试注册页面 (非交互模式)
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


async def test_register_page():
    """自动测试注册页面"""

    print("\n" + "="*60)
    print("  Playwright 注册页面自动测试")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)

    # 测试数据
    test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "TestPassword123!"
    test_username = f"testuser_{uuid.uuid4().hex[:6]}"

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
            # Step 1: 打开注册页面
            print("\n[1/4] 打开注册页面...")
            response = await page.goto("http://localhost:3000/register", wait_until="networkidle")

            if response and response.status == 200:
                print("  [PASS] 页面加载成功")
                results.append(("页面加载", True))
            else:
                print(f"  [FAIL] 页面加载失败: {response.status if response else 'No response'}")
                results.append(("页面加载", False))
                return results

            await page.screenshot(path="test_screenshots/01_register.png")

            # Step 2: 检查表单元素
            print("\n[2/4] 检查表单元素...")

            elements = {
                "用户名输入框": "#username",
                "邮箱输入框": "#email",
                "密码输入框": "#password",
                "确认密码输入框": "#confirmPassword",
                "提交按钮": "button[type='submit']"
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

            # Step 3: 填写表单
            print("\n[3/4] 填写注册表单...")

            await page.locator("#username").fill(test_username)
            print(f"  用户名: {test_username}")

            # 检查是否有 full_name 字段
            full_name = page.locator("#full_name")
            if await full_name.count() > 0 and await full_name.is_visible():
                await full_name.fill("Test User")
                print("  全名: Test User")

            await page.locator("#email").fill(test_email)
            print(f"  邮箱: {test_email}")

            await page.locator("#password").fill(test_password)
            await page.locator("#confirmPassword").fill(test_password)
            print(f"  密码: ***已填写***")

            await page.screenshot(path="test_screenshots/02_filled.png")
            results.append(("表单填写", True))

            # Step 4: 提交表单
            print("\n[4/4] 提交表单...")

            await page.locator("button[type='submit']").click()

            # 等待响应
            await page.wait_for_timeout(3000)
            await page.screenshot(path="test_screenshots/03_submitted.png")

            # 检查结果
            current_url = page.url
            print(f"  当前URL: {current_url}")

            if "dashboard" in current_url:
                print("  [PASS] 注册成功 - 已跳转到 Dashboard")
                results.append(("注册提交", True))
            elif "login" in current_url:
                print("  [PASS] 注册成功 - 已跳转到登录页")
                results.append(("注册提交", True))
            else:
                # 检查 toast 消息
                try:
                    toast = await page.locator("[data-sonner-toast]").first.text_content()
                    print(f"  Toast消息: {toast}")
                    if "成功" in toast or "success" in toast.lower():
                        results.append(("注册提交", True))
                    else:
                        results.append(("注册提交", False))
                except:
                    print("  [INFO] 未检测到跳转或toast消息")
                    # 检查是否还在注册页面且有错误
                    if "register" in current_url:
                        results.append(("注册提交", False))
                    else:
                        results.append(("注册提交", True))

            await page.screenshot(path="test_screenshots/04_result.png")

        except Exception as e:
            print(f"\n[ERROR] {e}")
            try:
                await page.screenshot(path="test_screenshots/error.png")
            except:
                pass
            results.append(("测试执行", False))

        finally:
            await browser.close()

    return results


def print_summary(results):
    """打印测试摘要"""
    print("\n" + "="*60)
    print("  测试结果摘要")
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
    results = asyncio.run(test_register_page())

    # 打印摘要
    success = print_summary(results)

    sys.exit(0 if success else 1)
