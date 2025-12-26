#!/bin/bash
# 重构验证脚本
# 用法: bash scripts/verify_refactor.sh

set -e

echo "=============================================="
echo "  项目重构验证脚本"
echo "=============================================="
echo ""

ERRORS=0
WARNINGS=0

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() {
    echo -e "${GREEN}✓${NC} $1"
}

fail() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

# ============================================
# 1. 结构检查
# ============================================
echo "【1. 结构检查】"
echo ""

# 1.1 根目录文件数
root_files=$(ls -1 | wc -l)
if [ "$root_files" -lt 20 ]; then
    pass "根目录文件数: $root_files (< 20)"
else
    fail "根目录文件数: $root_files (应 < 20)"
fi

# 1.2 关键文件存在性
key_files=(
    "docs/sot/MASTER.md"
    "docs/sot/INDEX.md"
    "docs/sot/CHANGELOG.md"
    "docs/sot/LEDGER_SOT.md"
    ".ai-rules/quality-gates.md"
    ".ai-rules/engineering.md"
    "justfile"
    "CLAUDE.md"
)

for f in "${key_files[@]}"; do
    if [ -f "$f" ]; then
        pass "$f 存在"
    else
        fail "$f 不存在"
    fi
done

# 1.3 旧目录已清理
if [ -d "docs/2.sot" ]; then
    if [ "$(ls -A docs/2.sot 2>/dev/null)" ]; then
        fail "docs/2.sot/ 目录不为空"
    else
        warn "docs/2.sot/ 目录存在但为空"
    fi
else
    pass "docs/2.sot/ 已删除"
fi

echo ""

# ============================================
# 2. 引用完整性检查
# ============================================
echo "【2. 引用完整性检查】"
echo ""

# 2.1 检查旧路径引用
old_refs=$(grep -r "docs/2\.sot" . --include="*.md" --include="*.py" --include="*.ts" 2>/dev/null | grep -v "archive" | grep -v "2.sot-legacy" | wc -l)
if [ "$old_refs" -eq 0 ]; then
    pass "无 docs/2.sot 旧引用"
else
    fail "发现 $old_refs 处 docs/2.sot 旧引用"
    grep -r "docs/2\.sot" . --include="*.md" --include="*.py" --include="*.ts" 2>/dev/null | grep -v "archive" | grep -v "2.sot-legacy" | head -5
fi

# 2.2 检查 1.overview/MASTER.md 引用
old_master_refs=$(grep -r "docs/1\.overview/MASTER\.md" . --include="*.md" --include="*.py" 2>/dev/null | grep -v "archive" | grep -v "MASTER_MOVED" | wc -l)
if [ "$old_master_refs" -eq 0 ]; then
    pass "无 docs/1.overview/MASTER.md 旧引用"
else
    warn "发现 $old_master_refs 处 docs/1.overview/MASTER.md 旧引用"
fi

echo ""

# ============================================
# 3. CLAUDE.md 检查
# ============================================
echo "【3. CLAUDE.md 检查】"
echo ""

if [ -f "CLAUDE.md" ]; then
    claude_lines=$(wc -l < CLAUDE.md)
    if [ "$claude_lines" -lt 40 ]; then
        pass "CLAUDE.md 行数: $claude_lines (< 40)"
    else
        warn "CLAUDE.md 行数: $claude_lines (建议 < 30)"
    fi
else
    fail "CLAUDE.md 不存在"
fi

echo ""

# ============================================
# 4. justfile 检查
# ============================================
echo "【4. justfile 检查】"
echo ""

if command -v just &> /dev/null; then
    if just --list &> /dev/null; then
        pass "just --list 正常"
    else
        fail "just --list 失败"
    fi
else
    warn "just 未安装，跳过检查"
fi

echo ""

# ============================================
# 5. 测试检查
# ============================================
echo "【5. 测试检查】"
echo ""

if [ -d "backend" ]; then
    if [ -f "backend/pytest.ini" ] || [ -f "pytest.ini" ]; then
        pass "pytest配置存在"
    else
        warn "未找到pytest配置"
    fi
fi

if [ -d "frontend" ]; then
    if [ -f "frontend/package.json" ]; then
        pass "前端package.json存在"
    else
        warn "前端package.json不存在"
    fi
fi

echo ""

# ============================================
# 6. CI配置检查
# ============================================
echo "【6. CI配置检查】"
echo ""

if [ -f ".github/workflows/ci.yml" ]; then
    if grep -q "check_migration" .github/workflows/ci.yml; then
        pass "CI包含migration检查"
    else
        warn "CI未包含migration检查"
    fi
    
    if grep -q "check_changelog" .github/workflows/ci.yml; then
        pass "CI包含changelog检查"
    else
        warn "CI未包含changelog检查"
    fi
else
    warn ".github/workflows/ci.yml 不存在"
fi

echo ""

# ============================================
# 结果汇总
# ============================================
echo "=============================================="
echo "  验证结果汇总"
echo "=============================================="
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ 全部通过！${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️ 通过，但有 $WARNINGS 个警告${NC}"
    exit 0
else
    echo -e "${RED}❌ 失败: $ERRORS 个错误, $WARNINGS 个警告${NC}"
    exit 1
fi
