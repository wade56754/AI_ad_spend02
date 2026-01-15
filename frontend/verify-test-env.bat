@echo off
echo ========================================
echo Verifying Test Environment
echo ========================================
echo.

cd /d "%~dp0"

echo [1/7] Checking Node.js...
node --version
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js not found!
    goto :error
)
echo OK: Node.js installed
echo.

echo [2/7] Checking pnpm...
pnpm --version
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: pnpm not found!
    goto :error
)
echo OK: pnpm installed
echo.

echo [3/7] Checking Jest...
call pnpm exec jest --version
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Jest may not be installed correctly
) else (
    echo OK: Jest installed
)
echo.

echo [4/7] Checking Puppeteer...
call pnpm exec puppeteer --version
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Puppeteer may not be installed correctly
) else (
    echo OK: Puppeteer installed
)
echo.

echo [5/7] Checking test configuration files...
if exist "jest.config.js" (
    echo OK: jest.config.js found
) else (
    echo ERROR: jest.config.js NOT found!
    goto :error
)

if exist "e2e\jest.config.js" (
    echo OK: e2e/jest.config.js found
) else (
    echo ERROR: e2e/jest.config.js NOT found!
    goto :error
)
echo.

echo [6/7] Checking test setup files...
if exist "tests\setup.ts" (
    echo OK: tests/setup.ts found
) else (
    echo ERROR: tests/setup.ts NOT found!
    goto :error
)

if exist "tests\test-utils.tsx" (
    echo OK: tests/test-utils.tsx found
) else (
    echo WARNING: tests/test-utils.tsx NOT found!
)
echo.

echo [7/7] Listing test files...
echo.
echo Unit Test Files:
dir /b /s "__tests__\*.test.ts" "__tests__\*.test.tsx" 2>nul | findstr /i "test"
echo.
echo E2E Test Files:
dir /b /s "e2e\tests\*.e2e.ts" 2>nul | findstr /i "e2e"
echo.

echo ========================================
echo Test Environment Verification Complete!
echo ========================================
echo.
echo You can now run:
echo   - pnpm test (unit tests)
echo   - pnpm run test:e2e (E2E tests)
echo.
goto :end

:error
echo.
echo ========================================
echo ERROR: Test environment verification failed!
echo ========================================
echo.
echo Please run: pnpm install
echo.

:end
pause
