# Run pnpm build and capture output
cd D:\git\1108\AI_ad_spend02\frontend
pnpm build 2>&1 | Out-File -FilePath D:\git\1108\AI_ad_spend02\frontend\build_output.txt -Encoding UTF8
