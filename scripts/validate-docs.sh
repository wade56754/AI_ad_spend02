#!/bin/bash
# 文档规则快速验证脚本
# 版本: v1.0
# 更新日期: 2025-11-16

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCS_DIR="$PROJECT_ROOT/docs"

echo -e "${BLUE}ℹ️  开始文档规则一致性验证...${NC}\n"

TOTAL_ISSUES=0

# 检查1: Next.js版本统一性
echo -e "${BLUE}检查1: Next.js版本统一性...${NC}"
NEXTJS_ISSUES=$(grep -rn --include="*.md" --exclude-dir=archive "Next\.js" "$DOCS_DIR" | grep -vE "16\.0\.2" | grep -E "Next\.js\s+[0-9]" || true)
if [ -n "$NEXTJS_ISSUES" ]; then
    COUNT=$(echo "$NEXTJS_ISSUES" | wc -l)
    echo -e "${RED}❌ 发现 $COUNT 处Next.js版本不一致:${NC}"
    echo "$NEXTJS_ISSUES" | head -10
    TOTAL_ISSUES=$((TOTAL_ISSUES + COUNT))
else
    echo -e "${GREEN}✅ Next.js版本检查通过${NC}"
fi
echo

# 检查2: 错误码规范
echo -e "${BLUE}检查2: 错误码命名规范...${NC}"
ERROR_CODE_ISSUES=$(grep -rn --include="*.md" --exclude-dir=archive '"code":' "$DOCS_DIR" | grep -vE 'SYS_|BIZ_|SEC_|SUCCESS' || true)
if [ -n "$ERROR_CODE_ISSUES" ]; then
    COUNT=$(echo "$ERROR_CODE_ISSUES" | wc -l)
    echo -e "${YELLOW}⚠️  发现 $COUNT 处错误码可能不符合规范:${NC}"
    echo "$ERROR_CODE_ISSUES" | head -10
    TOTAL_ISSUES=$((TOTAL_ISSUES + COUNT))
else
    echo -e "${GREEN}✅ 错误码规范检查通过${NC}"
fi
echo

# 检查3: AppShell使用
echo -e "${BLUE}检查3: AppShell废弃检查...${NC}"
APPSHELL_ISSUES=$(grep -rn --include="*.md" --exclude-dir=archive -E "import.*AppShell|<AppShell" "$DOCS_DIR" | grep -v "已废弃\|deprecated\|⚠️\|COMPONENT_MIGRATION" || true)
if [ -n "$APPSHELL_ISSUES" ]; then
    COUNT=$(echo "$APPSHELL_ISSUES" | wc -l)
    echo -e "${YELLOW}⚠️  发现 $COUNT 处仍在使用AppShell:${NC}"
    echo "$APPSHELL_ISSUES" | head -10
    TOTAL_ISSUES=$((TOTAL_ISSUES + COUNT))
else
    echo -e "${GREEN}✅ AppShell废弃检查通过${NC}"
fi
echo

# 检查4: 文档中的TODO标记
echo -e "${BLUE}检查4: 文档TODO标记...${NC}"
TODO_ISSUES=$(grep -rn --include="*.md" --exclude-dir=archive -E "TODO|FIXME|XXX" "$DOCS_DIR" || true)
if [ -n "$TODO_ISSUES" ]; then
    COUNT=$(echo "$TODO_ISSUES" | wc -l)
    echo -e "${YELLOW}⚠️  发现 $COUNT 处TODO标记:${NC}"
    echo "$TODO_ISSUES" | head -10
else
    echo -e "${GREEN}✅ 未发现TODO标记${NC}"
fi
echo

# 总结
echo "============================================================"
if [ $TOTAL_ISSUES -eq 0 ]; then
    echo -e "${GREEN}✅ 核心检查通过！文档规则一致性验证成功 🎉${NC}"
    exit 0
else
    echo -e "${RED}❌ 发现 $TOTAL_ISSUES 处需要关注的问题${NC}"
    echo -e "${BLUE}ℹ️  运行 Python 版本可获得更详细的检查结果:${NC}"
    echo -e "   ${BLUE}python scripts/validate-docs.py${NC}"
    exit 1
fi
