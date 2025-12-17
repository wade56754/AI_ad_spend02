@echo off
echo ========================================
echo Running Frontend E2E Tests
echo ========================================
echo.

cd /d "%~dp0"

echo Checking Node version...
node --version
echo.

echo Checking Puppeteer...
call npx puppeteer --version
echo.

echo.
echo NOTE: Make sure the development server is running on http://localhost:3000
echo Press any key to continue or Ctrl+C to cancel...
pause > nul
echo.

echo Running E2E tests (headless mode)...
call npm run test:e2e
echo.

echo ========================================
echo E2E Tests Complete
echo ========================================
pause
