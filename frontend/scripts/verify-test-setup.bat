@echo off
REM 测试框架验证脚本（Windows）
REM 用于快速验证测试框架是否正确配置

echo ==================================================
echo   前端测试框架验证
echo ==================================================
echo.

REM 检查 Node.js 和 pnpm
echo 1. 检查 Node.js 和 pnpm...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Node.js 未安装
    exit /b 1
) else (
    echo [OK] Node.js 已安装
)

pnpm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] pnpm 未安装
    exit /b 1
) else (
    echo [OK] pnpm 已安装
)

echo.

REM 检查配置文件
echo 2. 检查配置文件...
if exist "jest.config.js" (
    echo [OK] jest.config.js
) else (
    echo [X] jest.config.js 不存在
    exit /b 1
)

if exist "tests\setup.ts" (
    echo [OK] tests\setup.ts
) else (
    echo [X] tests\setup.ts 不存在
    exit /b 1
)

if exist "tests\test-utils.tsx" (
    echo [OK] tests\test-utils.tsx
) else (
    echo [X] tests\test-utils.tsx 不存在
    exit /b 1
)

echo.

REM 运行框架验证测试
echo 3. 运行框架验证测试...
call pnpm test -- __tests__/setup.test.ts --silent
if %errorlevel% neq 0 (
    echo [X] 框架验证测试失败
    exit /b 1
) else (
    echo [OK] 框架验证测试通过
)

echo.

REM 运行示例测试
echo 4. 运行示例测试...
call pnpm test -- __tests__/example/ --silent
if %errorlevel% neq 0 (
    echo [X] 示例测试失败
    exit /b 1
) else (
    echo [OK] 示例测试通过
)

echo.
echo ==================================================
echo   测试框架验证成功！
echo ==================================================
echo.
echo 下一步:
echo   1. 查看测试模板: type tests\TEST_TEMPLATE.md
echo   2. 查看使用文档: type tests\README.md
echo   3. 运行所有测试: pnpm test
echo   4. 监听模式: pnpm run test:watch
echo   5. 生成覆盖率: pnpm run test:coverage
echo.

exit /b 0
