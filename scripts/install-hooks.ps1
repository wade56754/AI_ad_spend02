# =============================================================================
# AI 代码工厂 - Hook 安装脚本 (Windows PowerShell)
# =============================================================================
#
# 用法: .\scripts\install-hooks.ps1
#
# 此脚本会:
# 1. 安装 pre-commit hook (违规阻断)
# 2. 生成 .claude/rules.md 文件
# 3. 初始化 memory-bank 目录
#
# =============================================================================

$ErrorActionPreference = "Stop"

Write-Host "🔧 安装 AI 代码工厂 Hook..." -ForegroundColor Cyan
Write-Host ""

# 检查是否在 git 仓库中
if (-not (Test-Path ".git")) {
    Write-Host "❌ 错误: 请在 git 仓库根目录运行此脚本" -ForegroundColor Red
    exit 1
}

# 检查 Python 是否可用
try {
    python --version | Out-Null
} catch {
    Write-Host "❌ 错误: 找不到 Python" -ForegroundColor Red
    exit 1
}

# =============================================================================
# 1. 安装 pre-commit hook
# =============================================================================

$HOOK_PATH = ".git\hooks\pre-commit"

Write-Host "📝 安装 pre-commit hook..." -ForegroundColor Yellow

$hookContent = @'
#!/bin/bash
# AI 代码工厂 Pre-Commit Hook
# 检查 SoT 合规性，违规将阻断提交

python -m agents.skills.code_factory.hooks.pre_commit
exit $?
'@

# 确保 hooks 目录存在
New-Item -ItemType Directory -Force -Path ".git\hooks" | Out-Null

# 写入 hook 文件
$hookContent | Out-File -FilePath $HOOK_PATH -Encoding utf8 -NoNewline

Write-Host "   ✅ pre-commit hook 已安装" -ForegroundColor Green

# =============================================================================
# 2. 生成 rules 文件
# =============================================================================

Write-Host "📝 生成 .claude/rules.md..." -ForegroundColor Yellow

New-Item -ItemType Directory -Force -Path ".claude" | Out-Null

try {
    python -m agents.skills.code_factory.hooks.rules_generator 2>$null
    if (Test-Path ".claude\rules.md") {
        Write-Host "   ✅ .claude/rules.md 已生成" -ForegroundColor Green
    }
} catch {
    Write-Host "   ⚠️ 规则文件生成失败，请手动运行:" -ForegroundColor Yellow
    Write-Host "      python -m agents.skills.code_factory.hooks.rules_generator" -ForegroundColor Gray
}

# =============================================================================
# 3. 初始化 memory-bank
# =============================================================================

Write-Host "📝 初始化 memory-bank..." -ForegroundColor Yellow

New-Item -ItemType Directory -Force -Path "memory-bank\session" | Out-Null

try {
    python -c "from agents.skills.code_factory.context import get_memory_bank; get_memory_bank()" 2>$null
    Write-Host "   ✅ memory-bank 已初始化" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️ Memory Bank 初始化失败，请手动运行:" -ForegroundColor Yellow
    Write-Host "      python -c 'from agents.skills.code_factory.context import get_memory_bank; get_memory_bank()'" -ForegroundColor Gray
}

# =============================================================================
# 完成
# =============================================================================

Write-Host ""
Write-Host "✅ 安装完成！" -ForegroundColor Green
Write-Host ""
Write-Host "已安装:" -ForegroundColor Cyan
Write-Host "  - pre-commit hook (违规阻断)"
Write-Host "  - .claude/rules.md (SoT 约束)"
Write-Host "  - memory-bank/ (上下文持久化)"
Write-Host ""
Write-Host "使用说明:" -ForegroundColor Cyan
Write-Host "  1. 提交代码时会自动检查 SoT 合规性"
Write-Host "  2. 违规代码将被阻断，需修复后重新提交"
Write-Host "  3. AI 对话时会自动读取 memory-bank/ 中的上下文"
Write-Host ""
