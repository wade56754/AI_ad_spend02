@echo off
echo ========================================
echo Running Tests NOW
echo ========================================
echo.

cd /d "%~dp0"

echo Starting test run...
echo.

call pnpm test -- --no-coverage --verbose 2>&1

echo.
echo ========================================
echo Test run complete
echo ========================================
