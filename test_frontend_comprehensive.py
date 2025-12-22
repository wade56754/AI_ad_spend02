#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 Playwright MCP 对前端进行全面测试
测试所有主要页面的加载、导航和基本功能
"""

import json
import subprocess
import sys
import time
import io
from pathlib import Path

# 设置控制台编码为 UTF-8 (Windows)
if sys.platform == 'win32':
    import codecs
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 测试配置
FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"

# 要测试的页面列表
PAGES_TO_TEST = [
    {"path": "/", "name": "首页", "requires_auth": False},
    {"path": "/login", "name": "登录页", "requires_auth": False},
    {"path": "/register", "name": "注册页", "requires_auth": False},
    {"path": "/forgot-password", "name": "忘记密码", "requires_auth": False},
    {"path": "/reset-password", "name": "重置密码", "requires_auth": False},
    # Dashboard 页面（需要认证）
    {"path": "/projects", "name": "项目管理", "requires_auth": True},
    {"path": "/ad-accounts", "name": "广告账户", "requires_auth": True},
    {"path": "/daily-reports", "name": "日报管理", "requires_auth": True},
    {"path": "/topups", "name": "充值管理", "requires_auth": True},
    {"path": "/reconciliation", "name": "对账管理", "requires_auth": True},
    {"path": "/ledger", "name": "账本管理", "requires_auth": True},
    {"path": "/transfers", "name": "转账管理", "requires_auth": True},
    {"path": "/settlements", "name": "结算管理", "requires_auth": True},
    {"path": "/suppliers", "name": "供应商管理", "requires_auth": True},
    {"path": "/channels", "name": "渠道管理", "requires_auth": True},
    {"path": "/users", "name": "用户管理", "requires_auth": True},
    {"path": "/finance", "name": "财务管理", "requires_auth": True},
    {"path": "/finance/profit", "name": "利润分析", "requires_auth": True},
    {"path": "/cost-analysis", "name": "成本分析", "requires_auth": True},
    {"path": "/reports", "name": "报表管理", "requires_auth": True},
    {"path": "/import-jobs", "name": "导入任务", "requires_auth": True},
    {"path": "/audit-logs", "name": "审计日志", "requires_auth": True},
    {"path": "/settings", "name": "系统设置", "requires_auth": True},
    {"path": "/profile", "name": "个人资料", "requires_auth": True},
    {"path": "/help", "name": "帮助中心", "requires_auth": True},
]

# 日志文件路径
LOG_PATH = Path(".cursor/debug.log")

def log_debug(message: str, data: dict = None):
    """写入调试日志"""
    log_entry = {
        "id": f"log_{int(time.time() * 1000)}",
        "timestamp": int(time.time() * 1000),
        "location": "test_frontend_comprehensive.py",
        "message": message,
        "data": data or {},
        "sessionId": "frontend-test-session",
        "runId": "comprehensive-test",
    }
    
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"警告: 无法写入日志: {e}")

def check_server_running(url: str, name: str) -> bool:
    """检查服务器是否运行"""
    import urllib.request
    import urllib.error
    
    try:
        req = urllib.request.Request(url, method="HEAD")
        urllib.request.urlopen(req, timeout=5)
        print(f"[OK] {name} 服务器运行中: {url}")
        log_debug(f"{name} 服务器检查", {"url": url, "status": "running"})
        return True
    except Exception as e:
        print(f"[FAIL] {name} 服务器未运行: {url}")
        log_debug(f"{name} 服务器检查", {"url": url, "status": "not_running", "error": str(e)})
        return False

def run_playwright_test():
    """使用 Playwright MCP 运行测试"""
    
    # 清空日志文件
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    
    log_debug("开始前端全面测试", {
        "frontend_url": FRONTEND_URL,
        "backend_url": BACKEND_URL,
        "total_pages": len(PAGES_TO_TEST)
    })
    
    print("=" * 60)
    print("前端全面测试 - 使用 Playwright MCP")
    print("=" * 60)
    print()
    
    # 检查服务器
    print("检查服务器状态...")
    frontend_running = check_server_running(FRONTEND_URL, "前端")
    backend_running = check_server_running(BACKEND_URL, "后端")
    
    if not frontend_running:
        print("\n[ERROR] 前端服务器未运行，请先启动:")
        print(f"   cd frontend && pnpm run dev")
        return 1
    
    if not backend_running:
        print("\n[WARN] 后端服务器未运行，某些功能可能无法测试")
        print(f"   建议启动: cd backend && uvicorn main:app --reload")
    
    print()
    print("=" * 60)
    print("开始测试页面...")
    print("=" * 60)
    print()
    
    # 创建测试脚本
    test_script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    const browser = await chromium.launch({{ headless: false }});
    const context = await browser.newContext();
    const page = await context.newPage();
    
    const results = [];
    const pages = {json.dumps(PAGES_TO_TEST, ensure_ascii=False)};
    const baseUrl = '{FRONTEND_URL}';
    
    console.log('开始测试 ' + pages.length + ' 个页面...');
    
    for (const pageConfig of pages) {{
        const url = baseUrl + pageConfig.path;
        console.log('\\n测试: ' + pageConfig.name + ' (' + url + ')');
        
        try {{
            const startTime = Date.now();
            const response = await page.goto(url, {{
                waitUntil: 'networkidle',
                timeout: 30000
            }});
            
            const loadTime = Date.now() - startTime;
            const status = response.status();
            
            // 检查页面标题
            const title = await page.title();
            
            // 检查是否有明显错误
            const errorSelectors = [
                'text=/错误/i',
                'text=/Error/i',
                'text=/404/i',
                'text=/500/i',
                '[data-testid="error"]',
                '.error',
                '#error'
            ];
            
            let hasError = false;
            for (const selector of errorSelectors) {{
                try {{
                    const element = await page.locator(selector).first();
                    if (await element.count() > 0) {{
                        hasError = true;
                        break;
                    }}
                }} catch (e) {{
                    // 忽略选择器错误
                }}
            }}
            
            // 检查控制台错误
            const consoleErrors = [];
            page.on('console', msg => {{
                if (msg.type() === 'error') {{
                    consoleErrors.push(msg.text());
                }}
            }});
            
            // 等待页面稳定
            await page.waitForTimeout(2000);
            
            // 检查关键元素是否存在
            const hasContent = await page.locator('body').count() > 0;
            
            const result = {{
                name: pageConfig.name,
                path: pageConfig.path,
                url: url,
                status: status,
                loadTime: loadTime,
                title: title,
                hasError: hasError,
                hasContent: hasContent,
                consoleErrors: consoleErrors.slice(0, 5), // 只记录前5个错误
                success: status >= 200 && status < 400 && !hasError && hasContent
            }};
            
            results.push(result);
            
            if (result.success) {{
                console.log('[OK] 通过: ' + pageConfig.name + ' (' + loadTime + 'ms)');
            }} else {{
                console.log('[FAIL] 失败: ' + pageConfig.name);
                console.log('  状态码: ' + status);
                console.log('  有错误: ' + hasError);
                if (consoleErrors.length > 0) {{
                    console.log('  控制台错误: ' + consoleErrors[0]);
                }}
            }}
            
        }} catch (error) {{
            console.log('[ERROR] 异常: ' + pageConfig.name);
            console.log('  错误: ' + error.message);
            results.push({{
                name: pageConfig.name,
                path: pageConfig.path,
                url: url,
                success: false,
                error: error.message
            }});
        }}
        
        // 页面间延迟
        await page.waitForTimeout(1000);
    }}
    
    await browser.close();
    
    // 输出结果
    console.log('\\n' + '='.repeat(60));
    console.log('测试结果汇总');
    console.log('='.repeat(60));
    
    const successCount = results.filter(r => r.success).length;
    const failCount = results.length - successCount;
    
    console.log('总计: ' + results.length + ' 个页面');
    console.log('通过: ' + successCount);
    console.log('失败: ' + failCount);
    console.log();
    
    // 详细结果
    console.log('详细结果:');
    for (const result of results) {{
        const icon = result.success ? '[OK]' : '[FAIL]';
        console.log(icon + ' ' + result.name + ' (' + result.path + ')');
        if (!result.success) {{
            if (result.error) {{
                console.log('  错误: ' + result.error);
            }}
            if (result.status) {{
                console.log('  状态码: ' + result.status);
            }}
        }} else {{
            console.log('  加载时间: ' + result.loadTime + 'ms');
        }}
    }}
    
    // 返回结果
    process.exit(failCount > 0 ? 1 : 0);
}})();
"""
    
    # 写入临时测试文件
    test_file = Path("temp_playwright_test.js")
    test_file.write_text(test_script, encoding="utf-8")
    
    try:
        # 运行测试
        print("正在运行 Playwright 测试...")
        print("(这将打开浏览器窗口进行测试)")
        print()
        
        result = subprocess.run(
            ["node", str(test_file)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=600  # 10分钟超时
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("错误输出:", result.stderr)
        
        log_debug("测试完成", {
            "exit_code": result.returncode,
            "stdout_length": len(result.stdout) if result.stdout else 0,
            "stderr_length": len(result.stderr) if result.stderr else 0
        })
        
        return result.returncode
        
    except subprocess.TimeoutExpired:
        print("[ERROR] 测试超时（超过10分钟）")
        log_debug("测试超时", {})
        return 1
    except FileNotFoundError:
        print("[ERROR] 未找到 Node.js，请先安装 Node.js")
        log_debug("Node.js 未找到", {})
        return 1
    except Exception as e:
        print(f"[ERROR] 运行测试时出错: {e}")
        log_debug("测试异常", {"error": str(e)})
        return 1
    finally:
        # 清理临时文件
        if test_file.exists():
            test_file.unlink()

if __name__ == "__main__":
    sys.exit(run_playwright_test())

