@echo off
chcp 65001 >nul
cd /d "%~dp0.."

echo ==============================================
echo   监工系统验证 (Supervisor System Test)
echo ==============================================

echo.
echo [Step 1] 配置模块验证
python -c "import sys; sys.path.insert(0, '.claude/hooks'); from lib.config import get_sot_versions, get_valid_roles; v=get_sot_versions(); r=get_valid_roles(); print(f'  SoT: {len(v)} versions, Roles: {len(r)}'); assert len(v)==8 and len(r)==7"
if %errorlevel% neq 0 (echo FAIL & exit /b 1) else (echo PASS)

echo.
echo [Step 2] 进度追踪验证
python -c "import sys; sys.path.insert(0, '.claude/hooks'); from lib.progress_tracker import ProgressTracker; t=ProgressTracker(); t.load_tasks(); print(f'  Modules: {len(t.modules)}, Tasks: {len(t.tasks)}'); assert len(t.modules)==11"
if %errorlevel% neq 0 (echo FAIL & exit /b 1) else (echo PASS)

echo.
echo [Step 3] 合规检查验证
python -c "import sys; sys.path.insert(0, '.claude/hooks'); from lib.compliance_checker import is_compliant; assert is_compliant('def x(): pass')==True; assert is_compliant('account.balance -= 1')==False; print('  Normal: pass, Balance: reject')"
if %errorlevel% neq 0 (echo FAIL & exit /b 1) else (echo PASS)

echo.
echo [Step 4] 风险检测验证
python -c "import sys; sys.path.insert(0, '.claude/hooks'); from lib.risk_detector import RiskDetector; d=RiskDetector(); r=d.detect_all(); print(f'  Detected {len(r.risks)} risks')"
if %errorlevel% neq 0 (echo FAIL & exit /b 1) else (echo PASS)

echo.
echo [Step 5] 报告生成验证
python -c "import sys; sys.path.insert(0, '.claude/hooks'); from lib.report_generator import ReportGenerator; g=ReportGenerator(); c=g.generate_daily(); print(f'  Daily report: {len(c)} chars')"
if %errorlevel% neq 0 (echo FAIL & exit /b 1) else (echo PASS)

echo.
echo ==============================================
echo   All tests passed!
echo ==============================================
