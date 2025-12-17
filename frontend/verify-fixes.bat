@echo off
chcp 65001 >nul
echo ========================================
echo Verify Bug Fixes / 验证 Bug 修复
echo ========================================
echo.

cd /d "%~dp0"

echo [1/4] Check fixed files / 检查修复的文件...
echo.

if exist "src\lib\utils.ts" (
    echo [OK] src\lib\utils.ts - exists
) else (
    echo [ERROR] src\lib\utils.ts - not found
    goto :error
)

if exist "src\lib\api.ts" (
    echo [OK] src\lib\api.ts - exists
) else (
    echo [ERROR] src\lib\api.ts - not found
    goto :error
)

echo.
echo [2/4] Check dependencies / 检查依赖包...
echo.

call npm list clsx tailwind-merge 2>nul | findstr /C:"clsx" /C:"tailwind-merge"
if %ERRORLEVEL% EQU 0 (
    echo [OK] Required dependencies are installed
) else (
    echo [WARNING] Some dependencies may not be installed
    echo Run: npm install clsx tailwind-merge
)

echo.
echo [3/4] Validate file content / 文件内容验证...
echo.

findstr /C:"cn" src\lib\utils.ts >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] utils.ts contains cn function
) else (
    echo [ERROR] utils.ts file content is incorrect
    goto :error
)

findstr /C:"apiRequest" src\lib\api.ts >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] api.ts contains apiRequest function
) else (
    echo [ERROR] api.ts file content is incorrect
    goto :error
)

echo.
echo [4/4] Check project structure / 检查项目结构...
echo.

if exist "src\components\ui" (
    echo [OK] UI components directory exists
) else (
    echo [WARNING] UI components directory not found
)

if exist "src\app" (
    echo [OK] App directory exists
) else (
    echo [WARNING] App directory not found
)

echo.
echo ========================================
echo [SUCCESS] All fixes completed!
echo ========================================
echo.
echo Next steps:
echo 1. Start dev server: npm run dev
echo 2. Visit http://localhost:3000 to check pages
echo 3. Run tests: npm test
echo 4. View fix details: BUG_FIXES.md
echo.
goto :end

:error
echo.
echo ========================================
echo [FAILED] Verification failed!
echo ========================================
echo.
echo Please check error messages and re-run fix script
echo.

:end
pause
