#!/bin/bash
# =============================================================================
# AI 代码工厂 - Hook 安装脚本
# =============================================================================
#
# 用法: bash scripts/install-hooks.sh
#
# 此脚本会:
# 1. 安装 pre-commit hook (违规阻断)
# 2. 生成 .claude/rules.md 文件
# 3. 初始化 memory-bank 目录
#
# =============================================================================

set -e

echo "🔧 安装 AI 代码工厂 Hook..."
echo ""

# 检查是否在 git 仓库中
if [ ! -d ".git" ]; then
    echo "❌ 错误: 请在 git 仓库根目录运行此脚本"
    exit 1
fi

# 检查 Python 是否可用
if ! command -v python &> /dev/null; then
    echo "❌ 错误: 找不到 Python"
    exit 1
fi

# =============================================================================
# 1. 安装 pre-commit hook
# =============================================================================

HOOK_PATH=".git/hooks/pre-commit"

echo "📝 安装 pre-commit hook..."

cat > "$HOOK_PATH" << 'EOF'
#!/bin/bash
# AI 代码工厂 Pre-Commit Hook
# 检查 SoT 合规性，违规将阻断提交

python -m agents.skills.code_factory.hooks.pre_commit
exit $?
EOF

chmod +x "$HOOK_PATH"
echo "   ✅ pre-commit hook 已安装"

# =============================================================================
# 2. 生成 rules 文件
# =============================================================================

echo "📝 生成 .claude/rules.md..."
mkdir -p .claude
python -m agents.skills.code_factory.hooks.rules_generator 2>/dev/null || {
    echo "   ⚠️ 规则文件生成失败，请手动运行:"
    echo "      python -m agents.skills.code_factory.hooks.rules_generator"
}

if [ -f ".claude/rules.md" ]; then
    echo "   ✅ .claude/rules.md 已生成"
fi

# =============================================================================
# 3. 初始化 memory-bank
# =============================================================================

echo "📝 初始化 memory-bank..."
mkdir -p memory-bank/session

# 初始化 Memory Bank (会创建模板文件)
python -c "from agents.skills.code_factory.context import get_memory_bank; get_memory_bank()" 2>/dev/null || {
    echo "   ⚠️ Memory Bank 初始化失败，请手动运行:"
    echo "      python -c 'from agents.skills.code_factory.context import get_memory_bank; get_memory_bank()'"
}

if [ -d "memory-bank" ]; then
    echo "   ✅ memory-bank 已初始化"
fi

# =============================================================================
# 完成
# =============================================================================

echo ""
echo "✅ 安装完成！"
echo ""
echo "已安装:"
echo "  - pre-commit hook (违规阻断)"
echo "  - .claude/rules.md (SoT 约束)"
echo "  - memory-bank/ (上下文持久化)"
echo ""
echo "使用说明:"
echo "  1. 提交代码时会自动检查 SoT 合规性"
echo "  2. 违规代码将被阻断，需修复后重新提交"
echo "  3. AI 对话时会自动读取 memory-bank/ 中的上下文"
echo ""
