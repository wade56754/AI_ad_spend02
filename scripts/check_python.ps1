# Python Installation Check Script
# This script checks if Python is installed (no admin rights required)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Python Installation Check" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is in PATH
Write-Host "[1/3] Checking if Python is in PATH..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "      Found: $pythonVersion" -ForegroundColor Green
    
    # Check pip
    $pipVersion = pip --version 2>&1
    Write-Host "      pip: $pipVersion" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  Python is ready to use!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now run:" -ForegroundColor Cyan
    Write-Host "  scripts\setup_python_env.bat" -ForegroundColor White
    Write-Host ""
    exit 0
} catch {
    Write-Host "      Python not found in PATH" -ForegroundColor Red
}

Write-Host ""
Write-Host "[2/3] Searching for Python installation..." -ForegroundColor Yellow

# Common Python installation paths
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
        Write-Host "      Found Python at: $path" -ForegroundColor Green
        
        # Try to get version
        try {
            $version = & $path --version 2>&1
            Write-Host "      Version: $version" -ForegroundColor Green
        } catch {
            Write-Host "      (Could not get version)" -ForegroundColor Gray
        }
        break
    }
}

Write-Host ""
Write-Host "[3/3] Results..." -ForegroundColor Yellow

if ($foundPython) {
    Write-Host ""
    Write-Host "Python is installed but not in PATH!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To add Python to PATH:" -ForegroundColor Cyan
    Write-Host "  Option 1: Run as Administrator:" -ForegroundColor White
    Write-Host "    .\scripts\install_python_guide.ps1" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Option 2: Manual setup:" -ForegroundColor White
    Write-Host "    1. Right-click 'This PC' -> Properties" -ForegroundColor Gray
    Write-Host "    2. Advanced System Settings -> Environment Variables" -ForegroundColor Gray
    $pythonDir = Split-Path $foundPython -Parent
    Write-Host "    3. Add to System PATH:" -ForegroundColor Gray
    Write-Host "       $pythonDir" -ForegroundColor Yellow
    Write-Host "       $pythonDir\Scripts" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Python is NOT installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python:" -ForegroundColor Yellow
    Write-Host "  1. Visit https://www.python.org/downloads/" -ForegroundColor Cyan
    Write-Host "  2. Download Python 3.11 or higher" -ForegroundColor Cyan
    Write-Host "  3. Run installer, CHECK 'Add Python to PATH'" -ForegroundColor Cyan
    Write-Host "  4. After installation, run this script again" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host ""
Read-Host "Press Enter to exit"



