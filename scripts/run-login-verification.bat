@echo off
REM 运行登录页面验证测试
REM 前提: 前后端服务必须已经启动

echo ========================================
echo 登录页面验证测试
echo ========================================
echo.

REM 检查是否在正确的目录
if not exist "frontend\e2e\tests\login-verification.test.js" (
    echo 错误: 找不到测试文件
    echo 请确保在项目根目录运行此脚本
    pause
    exit /b 1
)

echo [1/3] 检查前端服务 (localhost:3000)...
curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo ❌ 前端服务未启动
    echo.
    echo 请先运行: scripts\start-dev-servers.bat
    echo 或手动启动:
    echo   cd frontend
    echo   npm run dev
    pause
    exit /b 1
)
echo ✅ 前端服务正常

echo [2/3] 检查后端服务 (localhost:8000)...
curl -s http://localhost:8000/healthz >nul 2>&1
if errorlevel 1 (
    echo ❌ 后端服务未启动
    echo.
    echo 请先运行: scripts\start-dev-servers.bat
    echo 或手动启动:
    echo   cd backend
    echo   python -m uvicorn backend.main:app --reload --port 8000
    pause
    exit /b 1
)
echo ✅ 后端服务正常

echo [3/3] 运行验证测试...
echo.
cd frontend
node e2e\tests\login-verification.test.js

REM 保存退出码
set TEST_EXIT_CODE=%ERRORLEVEL%

echo.
echo ========================================
if %TEST_EXIT_CODE%==0 (
    echo ✅ 测试完成
) else (
    echo ❌ 测试失败 ^(退出码: %TEST_EXIT_CODE%^)
)
echo ========================================
echo.

REM 检查是否生成了报告
if exist "e2e\reports\login-verification-report.json" (
    echo 📊 详细报告已生成:
    echo    frontend\e2e\reports\login-verification-report.json
    echo.
)

if exist "e2e\screenshots\login-page.png" (
    echo 📸 截图已保存:
    echo    frontend\e2e\screenshots\login-page.png
    echo    frontend\e2e\screenshots\login-final-state.png
    echo.
)

echo 按任意键查看JSON报告...
pause >nul

if exist "e2e\reports\login-verification-report.json" (
    start notepad e2e\reports\login-verification-report.json
)

exit /b %TEST_EXIT_CODE%
