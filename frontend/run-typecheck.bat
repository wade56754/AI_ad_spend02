@echo off
cd /d D:\git\1108\AI_ad_spend02\frontend
call npm run type-check > typecheck-output.txt 2>&1
echo Exit code: %ERRORLEVEL% >> typecheck-output.txt
type typecheck-output.txt
