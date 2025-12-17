# AI 广告代投系统 - Python 环境配置脚本 (PowerShell)
# 运行方式: .\scripts\setup_python_env.ps1

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  AI 广告代投系统 - Python 环境配置" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python 已安装: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] Python 未安装或不在 PATH 中" -ForegroundColor Red
    Write-Host ""
    Write-Host "请安装 Python 3.11+:" -ForegroundColor Yellow
    Write-Host "  1. 访问 https://www.python.org/downloads/"
    Write-Host "  2. 下载 Python 3.11 或更高版本"
    Write-Host "  3. 安装时勾选 'Add Python to PATH'"
    Write-Host "  4. 重新运行此脚本"
    exit 1
}
Write-Host ""

# 创建虚拟环境
Write-Host "[1/4] 创建虚拟环境..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "      虚拟环境已存在，跳过创建" -ForegroundColor Gray
} else {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[错误] 创建虚拟环境失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "      虚拟环境创建成功: .venv" -ForegroundColor Green
}
Write-Host ""

# 激活虚拟环境
Write-Host "[2/4] 激活虚拟环境..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1
Write-Host "      激活成功" -ForegroundColor Green
Write-Host ""

# 升级 pip
Write-Host "[3/4] 升级 pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip
Write-Host ""

# 安装依赖
Write-Host "[4/4] 安装项目依赖..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[警告] 部分依赖安装失败" -ForegroundColor Yellow
}
Write-Host ""

# 安装代码工厂依赖
Write-Host "[额外] 安装代码工厂依赖..." -ForegroundColor Yellow
if (Test-Path "agents\requirements.txt") {
    pip install -r agents\requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[警告] 代码工厂依赖安装失败" -ForegroundColor Yellow
    }
} else {
    Write-Host "[警告] agents\requirements.txt 不存在，跳过代码工厂依赖安装" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "============================================" -ForegroundColor Green
Write-Host "  环境配置完成!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "激活虚拟环境:" -ForegroundColor Cyan
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "运行代码工厂测试:" -ForegroundColor Cyan
Write-Host "  python agents\skills\test_code_factory.py"
Write-Host ""
