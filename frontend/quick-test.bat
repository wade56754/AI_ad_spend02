@echo off
echo Running quick test...
cd /d "%~dp0"
call npm test -- --no-coverage --maxWorkers=2 2>&1
pause
