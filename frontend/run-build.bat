@echo off
cd /d D:\git\1108\AI_ad_spend02\frontend
npm run build > build-output.log 2>&1
echo Build completed with exit code: %ERRORLEVEL% >> build-output.log
