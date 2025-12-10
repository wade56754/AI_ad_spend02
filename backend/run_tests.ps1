# AI 代码工厂 - 后端全面测试运行脚本
# PowerShell Script for Backend Testing

Write-Host "🏭 AI 代码工厂 - 后端测试启动" -ForegroundColor Cyan
Write-Host "=" * 60

# 设置环境变量
$env:PYTHONPATH = "D:\git\1108"
Set-Location "D:\git\1108\backend"

# 检查 pytest 是否安装
Write-Host "`n📦 检查测试依赖..." -ForegroundColor Yellow
$pytestInstalled = python -m pytest --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  pytest 未安装，正在安装测试依赖..." -ForegroundColor Red
    pip install pytest pytest-cov pytest-asyncio pytest-mock httpx
} else {
    Write-Host "✅ pytest 已安装: $pytestInstalled" -ForegroundColor Green
}

# 菜单选择
Write-Host "`n🎯 请选择测试执行策略:" -ForegroundColor Cyan
Write-Host "1. 快速验证 (冒烟测试 + 健康检查) - 2分钟"
Write-Host "2. 核心模块测试 (认证 + 项目 + 日报) - 5分钟"
Write-Host "3. 财务模块测试 (充值 + 对账 + 总账) - 8分钟"
Write-Host "4. 完整单元测试 (所有 unit 标记) - 10分钟"
Write-Host "5. 完整回归测试 (全部测试 + 覆盖率) - 25分钟"
Write-Host "6. 自定义测试路径"
Write-Host ""

$choice = Read-Host "请输入选项 (1-6)"

switch ($choice) {
    "1" {
        Write-Host "`n🚀 执行快速验证测试..." -ForegroundColor Green
        python -m pytest tests/test_api_health.py tests/test_app_smoke.py -v --tb=short
    }
    "2" {
        Write-Host "`n🚀 执行核心模块测试..." -ForegroundColor Green
        python -m pytest -m "auth or project or daily_report" -v --tb=short
    }
    "3" {
        Write-Host "`n🚀 执行财务模块测试..." -ForegroundColor Green
        python -m pytest tests/test_topup_*.py tests/test_reconciliation_*.py tests/ledger/ -v
    }
    "4" {
        Write-Host "`n🚀 执行完整单元测试..." -ForegroundColor Green
        python -m pytest -m unit --cov=backend --cov-report=term-missing --cov-report=html
    }
    "5" {
        Write-Host "`n🚀 执行完整回归测试（这将需要较长时间）..." -ForegroundColor Green
        python -m pytest --cov=backend --cov-report=html --cov-report=term-missing -v

        Write-Host "`n📊 生成覆盖率报告..." -ForegroundColor Yellow
        Write-Host "HTML 报告: D:\git\1108\backend\htmlcov\index.html" -ForegroundColor Cyan
    }
    "6" {
        $customPath = Read-Host "请输入测试文件路径 (例: tests/test_topup_api.py)"
        Write-Host "`n🚀 执行自定义测试: $customPath" -ForegroundColor Green
        python -m pytest $customPath -v --tb=short
    }
    default {
        Write-Host "❌ 无效选项，退出" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n" + "=" * 60
Write-Host "✅ 测试执行完成！" -ForegroundColor Green

# 询问是否查看覆盖率报告
if ($choice -in @("4", "5")) {
    $openReport = Read-Host "`n是否打开 HTML 覆盖率报告? (Y/N)"
    if ($openReport -eq "Y" -or $openReport -eq "y") {
        Start-Process "D:\git\1108\backend\htmlcov\index.html"
    }
}

Write-Host "`n📋 查看完整测试计划: D:\git\1108\backend\TEST_EXECUTION_PLAN.md" -ForegroundColor Cyan
