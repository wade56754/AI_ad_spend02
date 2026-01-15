#!/bin/sh
# SoT 5秒扫描 - AI编程防幻觉检查
# 注: 使用 POSIX sh 以提高 Windows Git Bash 兼容性
# 用途: pre-commit hook 或手动执行
# 版本: v1.1 (2025-12-29)
#
# 用法:
#   ./scripts/sot-scan.sh          # 标准检查
#   STRICT=1 ./scripts/sot-scan.sh # 严格模式（包含注释中的角色）
#   WARN_ONLY=1 ./scripts/sot-scan.sh # 仅警告，不阻断

set -e

# 配置
STRICT=${STRICT:-0}
WARN_ONLY=${WARN_ONLY:-0}

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

echo "=========================================="
echo "  SoT 5秒扫描 - AI编程防幻觉检查"
echo "=========================================="
echo ""

# 1. 废弃角色检查 (BLOCKING)
# 排除：注释、迁移说明（→）、废弃角色列表文档
echo -n "检查废弃角色 'supervisor'... "
if [ "$STRICT" = "1" ]; then
    SUPERVISOR_VIOLATIONS=$(grep -rn "supervisor" frontend/src/ --include="*.ts" --include="*.tsx" 2>/dev/null || true)
else
    # 非严格模式：排除 JSDoc 注释、迁移说明、废弃列表文档
    SUPERVISOR_VIOLATIONS=$(grep -rn "supervisor" frontend/src/ --include="*.ts" --include="*.tsx" 2>/dev/null \
        | grep -v "@permission" \
        | grep -v "// " \
        | grep -v "/\*" \
        | grep -v "禁止访问" \
        | grep -v "→" \
        | grep -v "废弃" \
        || true)
fi
if [ -n "$SUPERVISOR_VIOLATIONS" ]; then
    echo -e "${RED}FAIL${NC}"
    echo "  发现废弃角色 'supervisor' (PRD v5.1 已移除)"
    echo "$SUPERVISOR_VIOLATIONS" | head -5
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}PASS${NC}"
fi

echo -n "检查废弃角色 'data_operator'... "
# data_operator 在代码中使用是严重问题，需要检查
# 排除迁移文档说明
DATA_OP_VIOLATIONS=$(grep -rn "data_operator" frontend/src/ --include="*.ts" --include="*.tsx" 2>/dev/null \
    | grep -v "// " \
    | grep -v "→" \
    | grep -v "废弃" \
    || true)
if [ -n "$DATA_OP_VIOLATIONS" ]; then
    echo -e "${RED}FAIL${NC}"
    echo "  发现非白名单角色 'data_operator'"
    echo "$DATA_OP_VIOLATIONS" | head -5
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}PASS${NC}"
fi

echo -n "检查废弃角色 'data_clerk'... "
if grep -rq "data_clerk" frontend/src/ 2>/dev/null; then
    echo -e "${RED}FAIL${NC}"
    echo "  发现废弃角色 'data_clerk'"
    grep -rn "data_clerk" frontend/src/ --include="*.ts" --include="*.tsx" 2>/dev/null | head -5
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}PASS${NC}"
fi

# 2. 直接 fetch 检查 (BLOCKING)
echo -n "检查直接 fetch 调用... "
# 排除 lib/api.ts、注释、refetch (TanStack Query)、prefetch
FETCH_VIOLATIONS=$(grep -rn "fetch\s*(" frontend/src/ --include="*.ts" --include="*.tsx" 2>/dev/null | grep -v "lib/api" | grep -v "apiFetch" | grep -v "//" | grep -v "WebFetch" | grep -v "refetch" | grep -v "prefetch" | grep -v "usePrefetch" || true)
if [ -n "$FETCH_VIOLATIONS" ]; then
    echo -e "${RED}FAIL${NC}"
    echo "  发现直接 fetch 调用，请使用 apiGet/apiPost"
    echo "$FETCH_VIOLATIONS" | head -5
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}PASS${NC}"
fi

# 3. axios 检查 (BLOCKING)
echo -n "检查 axios 调用... "
if grep -rq "axios" frontend/src/ 2>/dev/null; then
    echo -e "${RED}FAIL${NC}"
    echo "  发现 axios 调用，请使用 apiFetch"
    grep -rn "axios" frontend/src/ --include="*.ts" --include="*.tsx" 2>/dev/null | head -5
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}PASS${NC}"
fi

# 4. 手写 HTML 标签检查 (WARNING)
echo -n "检查手写 HTML 标签... "
# 检查 <button>, <input>, <select>, <table> 但排除组件引用
HTML_VIOLATIONS=$(grep -rn "<button\|<input\|<select\|<table" frontend/src/ --include="*.tsx" 2>/dev/null \
    | grep -v "frontend/src/components/ui/" \
    | grep -v "Button\|Input\|Select\|Table\|DataTable" \
    | grep -v "//" \
    || true)
if [ -n "$HTML_VIOLATIONS" ]; then
    echo -e "${YELLOW}WARN${NC}"
    echo "  发现手写 HTML 标签，建议使用 shadcn/ui 组件"
    echo "$HTML_VIOLATIONS" | head -3
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}PASS${NC}"
fi

# 5. 后端废弃角色检查 (BLOCKING)
echo -n "检查后端废弃角色 'supervisor'... "
# 修复: grep -rq 会抑制输出，导致管道无效。改用变量捕获模式
# 排除: 测试文件、注释、docstring 示例 (>>>)、迁移映射定义 (:)
BACKEND_SUPERVISOR_VIOLATIONS=$(grep -rn "'supervisor'" backend/ --include="*.py" 2>/dev/null \
    | grep -v "test" \
    | grep -v "#" \
    | grep -v ">>>" \
    | grep -v "roles.py" \
    || true)
if [ -n "$BACKEND_SUPERVISOR_VIOLATIONS" ]; then
    echo -e "${RED}FAIL${NC}"
    echo "  后端发现废弃角色 'supervisor'"
    echo "$BACKEND_SUPERVISOR_VIOLATIONS" | head -5
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}PASS${NC}"
fi

# 6. 后端直接 SQL 检查 (WARNING)
echo -n "检查后端 SQL 注入风险... "
SQL_VIOLATIONS=$(grep -rn "f\".*SELECT\|f\".*INSERT\|f\".*UPDATE\|f\".*DELETE" backend/ --include="*.py" 2>/dev/null | grep -v "test" || true)
if [ -n "$SQL_VIOLATIONS" ]; then
    echo -e "${YELLOW}WARN${NC}"
    echo "  发现 f-string SQL，可能存在注入风险"
    echo "$SQL_VIOLATIONS" | head -3
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}PASS${NC}"
fi

echo ""
echo "=========================================="
echo "  扫描结果"
echo "=========================================="
echo ""

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}错误: $ERRORS 项 (必须修复)${NC}"
fi

if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}警告: $WARNINGS 项 (建议修复)${NC}"
fi

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}全部通过! 代码符合 SoT 规范${NC}"
fi

echo ""

# 只有错误时阻断提交
if [ $ERRORS -gt 0 ]; then
    if [ "$WARN_ONLY" = "1" ]; then
        echo -e "${YELLOW}警告模式: 发现错误但不阻断提交${NC}"
        exit 0
    else
        echo -e "${RED}提交被阻止: 请先修复以上错误${NC}"
        echo ""
        echo "提示: 如需临时跳过检查，可使用:"
        echo "  WARN_ONLY=1 ./scripts/sot-scan.sh"
        echo "  git commit --no-verify"
        exit 1
    fi
fi

echo -e "${GREEN}5秒扫描通过${NC}"
exit 0
