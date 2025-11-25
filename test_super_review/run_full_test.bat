@echo off
REM Super Review Agent v2.0 - 完整测试脚本 (Windows)
REM 此脚本用于在配置好环境变量后运行完整测试

echo ========================================================================
echo Super Review Agent v2.0 - 完整测试套件
echo ========================================================================
echo.

REM 1. 验证环境变量
echo [1/4] 验证环境变量...
if "%CLAUDE_CODE_GIT_BASH_PATH%"=="" (
    echo [ERROR] 环境变量 CLAUDE_CODE_GIT_BASH_PATH 未设置
    echo.
    echo 请运行以下命令设置环境变量:
    echo setx CLAUDE_CODE_GIT_BASH_PATH "D:\Program Files\Git\usr\bin\bash.exe"
    echo.
    echo 然后重新打开命令行窗口并重新运行此脚本
    pause
    exit /b 1
) else (
    echo [OK] CLAUDE_CODE_GIT_BASH_PATH = %CLAUDE_CODE_GIT_BASH_PATH%
)
echo.

REM 2. 测试 parse_p0_p1_count 函数
echo [2/4] 测试 parse_p0_p1_count 函数...
python test_parse_p0_p1.py
if errorlevel 1 (
    echo [ERROR] parse_p0_p1_count 测试失败
    pause
    exit /b 1
)
echo.

REM 3. 测试 review-only 模式
echo [3/4] 测试 review-only 模式 (Codex 审查)...
python super_review_agent.py review-only ^
  --doc "docs\3.dev-guides\DDD_API_ARCHITECTURE_polished.md" ^
  --codex-prompt "test_super_review\reviewer_prompt.txt" ^
  --codex-cmd "C:\Users\Administrator\AppData\Roaming\npm\codex.cmd" ^
  --output "test_super_review\review_output_batch.md" ^
  --verbose

if errorlevel 1 (
    echo [ERROR] review-only 模式测试失败
    pause
    exit /b 1
)
echo.

REM 4. 测试 fix-once 模式
echo [4/4] 测试 fix-once 模式 (Codex 审查 + Claude 修复)...
python super_review_agent.py fix-once ^
  --doc "docs\3.dev-guides\DDD_API_ARCHITECTURE_polished.md" ^
  --codex-prompt "test_super_review\reviewer_prompt.txt" ^
  --codex-cmd "C:\Users\Administrator\AppData\Roaming\npm\codex.cmd" ^
  --skill-name "doc-fixer-claude" ^
  --output "test_super_review\DDD_ARCH_fixed_once.md" ^
  --verbose

if errorlevel 1 (
    echo [ERROR] fix-once 模式测试失败
    echo [INFO] 请检查 Claude CLI 是否正常工作
    pause
    exit /b 1
)
echo.

echo ========================================================================
echo [SUCCESS] 所有测试通过!
echo ========================================================================
echo.
echo 生成的文件:
echo - test_super_review\review_output_batch.md  (review-only 输出)
echo - test_super_review\DDD_ARCH_fixed_once.md  (fix-once 输出)
echo.
pause
