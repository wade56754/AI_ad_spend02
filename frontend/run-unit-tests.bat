@echo off
echo ========================================
echo Running Frontend Unit Tests
echo ========================================
echo.

cd /d "%~dp0"

echo Checking Node version...
node --version
echo.

echo Checking Jest version...
call npx jest --version
echo.

echo Running tests...
call npm test -- --passWithNoTests --verbose
echo.

echo ========================================
echo Tests Complete
echo ========================================
pause
