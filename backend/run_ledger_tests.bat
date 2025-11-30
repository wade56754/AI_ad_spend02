@echo off
REM ============================================================================
REM Ledger Module Test Runner (Windows Batch)
REM ============================================================================
REM
REM Usage:
REM     run_ledger_tests.bat          - Run all ledger tests
REM     run_ledger_tests.bat -v       - Verbose output
REM     run_ledger_tests.bat --check  - Check environment only
REM
REM Prerequisites:
REM     - Python 3.9+
REM     - pip install -r requirements.txt
REM
REM Aligned Documents:
REM     - LEDGER_SOT.md v1.1
REM     - DATA_SCHEMA.md v5.2
REM ============================================================================

echo.
echo ============================================================
echo Ledger Module Test Runner
echo ============================================================

REM Navigate to backend directory
cd /d "%~dp0"
echo Working directory: %CD%

REM Set environment variables
set TESTING=true
set PYTHONPATH=%CD%

REM Check Python
python --version 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+
    exit /b 1
)

REM Load .env.test if exists
if exist ".env.test" (
    echo [OK] Found .env.test
) else (
    echo [WARN] .env.test not found
)

REM Run tests
echo.
echo Running pytest for ledger module...
echo ============================================================

python -m pytest tests/ledger -v --tb=short --no-cov --disable-warnings %*

if errorlevel 1 (
    echo.
    echo [RESULT] Some tests failed
    exit /b 1
) else (
    echo.
    echo [RESULT] All tests passed!
    exit /b 0
)
