@echo off
echo ========================================
echo Running E2E Tests (Headed Mode)
echo ========================================
echo.
echo This will show the browser window during testing.
echo.

cd /d "%~dp0"

echo NOTE: Make sure the development server is running on http://localhost:3000
echo Press any key to continue or Ctrl+C to cancel...
pause > nul
echo.

echo Running E2E tests with visible browser...
call npm run test:e2e:headed
echo.

echo ========================================
echo E2E Tests Complete
echo ========================================
pause
