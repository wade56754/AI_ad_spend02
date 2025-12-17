# Python 安装和环境变量配置辅助脚本
# 需要以管理员身份运行 PowerShell
# 编码: UTF-8

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Python Installation and PATH Configuration" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否以管理员身份运行
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[WARNING] Administrator privileges required to modify system PATH" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please right-click PowerShell and select 'Run as Administrator', then run this script again" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[1/3] Checking Python installation..." -ForegroundColor Yellow

# 常见的 Python 安装路径
$pythonPaths = @(
    "C:\Python311\python.exe",
    "C:\Python312\python.exe",
    "C:\Python313\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
    "$env:ProgramFiles\Python311\python.exe",
    "$env:ProgramFiles\Python312\python.exe",
    "$env:ProgramFiles\Python313\python.exe"
)

$foundPython = $null
foreach ($path in $pythonPaths) {
    if (Test-Path $path) {
        $foundPython = $path
        Write-Host "      Found Python: $path" -ForegroundColor Green
        break
    }
}

if (-not $foundPython) {
    Write-Host "[NOT FOUND] Python installation not found in system" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python first:" -ForegroundColor Yellow
    Write-Host "  1. Visit https://www.python.org/downloads/" -ForegroundColor Cyan
    Write-Host "  2. Download Python 3.11 or higher" -ForegroundColor Cyan
    Write-Host "  3. Run installer, check 'Add Python to PATH'" -ForegroundColor Cyan
    Write-Host "  4. After installation, run this script again" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Or, if Python is already installed, please provide the installation path" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# 获取 Python 目录和 Scripts 目录
$pythonDir = Split-Path $foundPython -Parent
$scriptsDir = Join-Path $pythonDir "Scripts"

Write-Host ""
Write-Host "[2/3] Configuring environment variables..." -ForegroundColor Yellow

# 获取当前 PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")

# 检查是否已在 PATH 中
$pythonInPath = $currentPath -like "*$pythonDir*"
$scriptsInPath = $currentPath -like "*$scriptsDir*"

if ($pythonInPath -and $scriptsInPath) {
    Write-Host "      Python is already in PATH, no changes needed" -ForegroundColor Green
} else {
    Write-Host "      Adding Python to PATH..." -ForegroundColor Cyan
    
    # Add Python directory to PATH (if not exists)
    if (-not $pythonInPath) {
        $newPath = $currentPath + ";$pythonDir"
        Write-Host "        Added: $pythonDir" -ForegroundColor Gray
    } else {
        $newPath = $currentPath
    }
    
    # Add Scripts directory to PATH (if not exists)
    if (-not $scriptsInPath -and (Test-Path $scriptsDir)) {
        $newPath = $newPath + ";$scriptsDir"
        Write-Host "        Added: $scriptsDir" -ForegroundColor Gray
    }
    
    # Set system environment variable
    [Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
    Write-Host "      Environment variable updated" -ForegroundColor Green
    Write-Host ""
    Write-Host "[IMPORTANT] Please close and reopen CMD/PowerShell window for PATH to take effect" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[3/3] Verifying configuration..." -ForegroundColor Yellow

Write-Host ""
Write-Host "Please run these commands in a NEW CMD/PowerShell window to verify:" -ForegroundColor Cyan
Write-Host "  python --version" -ForegroundColor White
Write-Host "  pip --version" -ForegroundColor White
Write-Host ""

Write-Host "============================================" -ForegroundColor Green
Write-Host "  Configuration Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

Read-Host "Press Enter to exit"

