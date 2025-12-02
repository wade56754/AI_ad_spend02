@echo off
REM 回归测试套件执行脚本（Windows）
REM 版本: v1.0
REM 最后更新: 2025-01-22

echo ========================================
echo 回归测试套件（Regression Test Suite）
echo ========================================
echo.

REM 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请确保已安装并添加到 PATH
    exit /b 1
)

echo [1/5] Daily Reports API 测试...
python -m pytest backend/tests/api/test_daily_report_flow_generated.py -q
if errorlevel 1 (
    echo [失败] Daily Reports 测试失败
    exit /b 1
)
echo [通过] Daily Reports 测试
echo.

echo [2/5] Trend Risk API 测试...
python -m pytest backend/tests/api/test_trend_risk_flow_generated.py -q
if errorlevel 1 (
    echo [失败] Trend Risk 测试失败
    exit /b 1
)
echo [通过] Trend Risk 测试
echo.

echo [3/5] Ledger 测试...
python -m pytest backend/tests/ledger -q
if errorlevel 1 (
    echo [失败] Ledger 测试失败
    exit /b 1
)
echo [通过] Ledger 测试
echo.

echo [4/5] Ad Accounts 测试...
python -m pytest backend/tests/ad_accounts -q
if errorlevel 1 (
    echo [失败] Ad Accounts 测试失败
    exit /b 1
)
echo [通过] Ad Accounts 测试
echo.

echo [5/5] Topup API 测试...
python -m pytest backend/tests/test_topup_api.py -q -k "not skip"
if errorlevel 1 (
    echo [失败] Topup 测试失败
    exit /b 1
)
echo [通过] Topup 测试
echo.

echo ========================================
echo 所有回归测试通过！✅
echo ========================================
exit /b 0


