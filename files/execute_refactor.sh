#!/bin/bash
# AI广告代投系统 - 项目重构执行脚本 v1.1
# 使用方法: bash scripts/refactor/execute_refactor.sh
# 警告: 执行前请确保已阅读重构计划书

set -e

echo "=============================================="
echo "  AI广告代投系统 - 项目重构脚本 v1.1"
echo "  日期: 2025-12-27"
echo "=============================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 检查是否在Git仓库
if [ ! -d ".git" ]; then
    echo -e "${RED}错误: 请在项目根目录执行此脚本${NC}"
    exit 1
fi

# 确认执行
echo -e "${YELLOW}警告: 此脚本将修改项目结构${NC}"
echo ""
echo "请确保:"
echo "  1. 已阅读重构计划书 v1.1"
echo "  2. 已备份重要数据"
echo "  3. 当前分支状态干净 (git status)"
echo ""
read -p "是否继续? (yes/no) " confirm
if [ "$confirm" != "yes" ]; then
    echo "取消执行"
    exit 0
fi

# ==================== Phase 1: 清理 ====================
echo ""
echo -e "${BLUE}========== Phase 1: 清理根目录 ==========${NC}"

# 1.1 创建工作分支
echo "1.1 创建工作分支..."
git checkout -b refactor/doc-structure-v2 2>/dev/null || git checkout refactor/doc-structure-v2
echo -e "    ${GREEN}✓${NC} 分支: refactor/doc-structure-v2"

# 1.2 创建归档目录
echo "1.2 创建归档目录..."
mkdir -p docs/archive/reports-2024
mkdir -p docs/archive/2.sot-legacy
mkdir -p docs/archive/5.infrastructure-legacy
echo -e "    ${GREEN}✓${NC} 归档目录已创建"

# 1.3 删除临时/调试文件
echo "1.3 删除临时文件..."
files_to_delete=(
    "analyze_excel.py"
    "analyze_excel_files.py"
    "analyze_excel_v2.py"
    "debug_api.py"
    "quick_test.py"
    "check_with_team.py"
    "fix_team_data.py"
    "import_daily_reports.py"
    "import_excel_data.py"
    "import_to_database.py"
    "import_to_sqlite.py"
    "import_to_supabase.py"
    "import_to_supabase_v2.py"
    "excel_analysis.json"
    "excel_analysis.txt"
    "excel_stats.json"
    "coverage.json"
    "processed_data.json"
    "excel_analysis_result.md"
)

deleted_count=0
for file in "${files_to_delete[@]}"; do
    if [ -f "$file" ]; then
        rm -f "$file"
        ((deleted_count++))
    fi
done
echo -e "    ${GREEN}✓${NC} 删除了 $deleted_count 个临时文件"

# 删除乱码文件
rm -f "dgit1108frontendsrcapppage.tsx" 2>/dev/null || true
rm -f "打造小红书自动化运营"* 2>/dev/null || true
echo -e "    ${GREEN}✓${NC} 删除了乱码文件"

# 1.4 归档报告文件
echo "1.4 归档报告文件..."
report_files=(
    "CODE_AUDIT_REPORT.md"
    "DOCS_ALIGNMENT_REPORT.md"
    "DOC_AUDIT_REPORT_v2.0.md"
    "API_AUDIT_REPORT.json"
    "FLOW_ARCHITECTURE_ANALYSIS_REPORT.md"
    "DASHBOARD_DESIGN_COMPLIANCE_ANALYSIS.md"
    "FRONTEND_DEVELOPMENT_PROGRESS_REPORT_v1.0.md"
    "FACEBOOK_AD_COST_ATTRIBUTION_BENCHMARK_v1.0.md"
)

archived_count=0
for file in "${report_files[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" docs/archive/reports-2024/
        ((archived_count++))
    fi
done
echo -e "    ${GREEN}✓${NC} 归档了 $archived_count 个报告文件"

# 1.5 移动测试文件
echo "1.5 移动测试文件..."
mkdir -p tests/e2e tests/integration
[ -f "test_auth_navigation.js" ] && mv test_auth_navigation.js tests/e2e/
[ -f "test_reconciliation_api.py" ] && mv test_reconciliation_api.py tests/integration/
echo -e "    ${GREEN}✓${NC} 测试文件已移动"

# 1.6 移动脚本文件
echo "1.6 移动脚本文件..."
script_files=(
    "setup-playwright-mcp.bat"
    "setup-supabase-mcp.bat"
    "start-dev.bat"
    "start-dev.sh"
    "run_migration_and_import.py"
    "run_regression_tests.sh"
    "run_tests.py"
    "build_package.py"
    "update_mcp_config.py"
)

for file in "${script_files[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" scripts/
    fi
done
echo -e "    ${GREEN}✓${NC} 脚本文件已移动到 scripts/"

# 1.7 提交Phase 1
echo "1.7 提交Phase 1..."
git add -A
git commit -m "refactor: phase1 清理根目录

- 删除临时/调试文件
- 归档报告文件到 docs/archive/reports-2024/
- 移动测试文件到 tests/
- 移动脚本文件到 scripts/
" || echo "    (无变更需提交)"
echo -e "    ${GREEN}✓${NC} Phase 1 完成"

# ==================== Phase 2: 重组 ====================
echo ""
echo -e "${BLUE}========== Phase 2: 重组SoT结构 ==========${NC}"

# 2.1 创建新目录结构
echo "2.1 创建新目录结构..."
mkdir -p docs/sot
mkdir -p docs/adr
mkdir -p docs/releases/artifacts
mkdir -p docs/releases/approvals
mkdir -p docs/runbooks
mkdir -p docs/exemptions
mkdir -p .ai-rules
echo -e "    ${GREEN}✓${NC} 新目录结构已创建"

# 2.2 备份旧SoT
echo "2.2 备份旧SoT..."
if [ -d "docs/2.sot" ]; then
    cp -r docs/2.sot/* docs/archive/2.sot-legacy/ 2>/dev/null || true
    echo -e "    ${GREEN}✓${NC} 旧SoT已备份到 docs/archive/2.sot-legacy/"
else
    echo -e "    ${YELLOW}⚠${NC} docs/2.sot/ 不存在，跳过备份"
fi

# 2.3 移动SoT文件
echo "2.3 移动SoT文件..."
if [ -d "docs/2.sot" ]; then
    mv docs/2.sot/* docs/sot/ 2>/dev/null || true
    echo -e "    ${GREEN}✓${NC} SoT文件已移动到 docs/sot/"
fi

# 2.4 移动MASTER.md（非复制）
echo "2.4 移动MASTER.md..."
if [ -f "docs/1.overview/MASTER.md" ]; then
    mv docs/1.overview/MASTER.md docs/sot/MASTER.md
    echo -e "    ${GREEN}✓${NC} MASTER.md 已移动到 docs/sot/"
else
    echo -e "    ${YELLOW}⚠${NC} docs/1.overview/MASTER.md 不存在"
fi

# 2.5 创建MASTER_MOVED.md引用
echo "2.5 创建引用文件..."
cat > docs/1.overview/MASTER_MOVED.md << 'EOF'
# MASTER.md 已迁移

> ⚠️ 本文件已移至 `docs/sot/MASTER.md`

## 新位置

请直接访问: [docs/sot/MASTER.md](../sot/MASTER.md)

## 迁移说明

- **迁移日期**: 2025-12-27
- **原因**: 统一SoT目录结构，确保唯一真相源
- **影响**: 所有引用已自动更新

如发现断链，请更新为 `docs/sot/MASTER.md`
EOF
echo -e "    ${GREEN}✓${NC} 创建了 docs/1.overview/MASTER_MOVED.md"

# 2.6-2.7 INDEX.md 和 CHANGELOG.md 需要手动复制
echo "2.6 INDEX.md 和 CHANGELOG.md..."
echo -e "    ${YELLOW}⚠${NC} 请从附件复制 INDEX.md 和 CHANGELOG.md 到 docs/sot/"

# 2.8 更新文档引用
echo "2.8 更新文档引用..."
# 替换 docs/2.sot/ → docs/sot/
find . -name "*.md" -not -path "./docs/archive/*" -exec sed -i 's|docs/2\.sot/|docs/sot/|g' {} \; 2>/dev/null || true
find . -name "*.py" -exec sed -i 's|docs/2\.sot/|docs/sot/|g' {} \; 2>/dev/null || true
find . -name "*.ts" -exec sed -i 's|docs/2\.sot/|docs/sot/|g' {} \; 2>/dev/null || true
find . -name "*.tsx" -exec sed -i 's|docs/2\.sot/|docs/sot/|g' {} \; 2>/dev/null || true
find . -name "*.mdc" -exec sed -i 's|docs/2\.sot/|docs/sot/|g' {} \; 2>/dev/null || true

# 替换 docs/1.overview/MASTER.md → docs/sot/MASTER.md
find . -name "*.md" -not -path "./docs/archive/*" -exec sed -i 's|docs/1\.overview/MASTER\.md|docs/sot/MASTER.md|g' {} \; 2>/dev/null || true

# 检查遗漏
remaining=$(grep -r "docs/2.sot" . --include="*.md" --include="*.py" --include="*.ts" 2>/dev/null | grep -v "archive" | grep -v "2.sot-legacy" | wc -l)
if [ "$remaining" -gt 0 ]; then
    echo -e "    ${YELLOW}⚠${NC} 发现 $remaining 处遗漏，请手动检查"
else
    echo -e "    ${GREEN}✓${NC} 引用更新完成，无遗漏"
fi

# 2.9 删除空的旧目录
echo "2.9 删除空目录..."
rmdir docs/2.sot 2>/dev/null && echo -e "    ${GREEN}✓${NC} 删除了 docs/2.sot/" || echo -e "    ${YELLOW}⚠${NC} docs/2.sot/ 不存在或不为空"

# 2.10 提交Phase 2
echo "2.10 提交Phase 2..."
git add -A
git commit -m "refactor: phase2 重组SoT结构

- 创建 docs/sot/ 作为SoT唯一目录
- 移动 docs/2.sot/* 到 docs/sot/
- 移动 MASTER.md 到 docs/sot/（非复制）
- 创建 MASTER_MOVED.md 引用文件
- 创建 docs/adr/, docs/releases/, docs/runbooks/
- 创建 .ai-rules/
- 更新所有文档引用
" || echo "    (无变更需提交)"
echo -e "    ${GREEN}✓${NC} Phase 2 完成"

# ==================== Phase 3 提示 ====================
echo ""
echo -e "${BLUE}========== Phase 3: 增强治理能力 ==========${NC}"
echo ""
echo "Phase 3 需要手动复制以下附件:"
echo ""
echo "  docs/sot/"
echo "    - INDEX.md"
echo "    - CHANGELOG.md"
echo ""
echo "  .ai-rules/"
echo "    - quality-gates.md"
echo "    - engineering.md"
echo ""
echo "  docs/adr/"
echo "    - template.md"
echo "    - 001-七角色模型.md"
echo "    - 002-phase1只提示.md"
echo "    - 003-可用资金术语统一.md"
echo ""
echo "  docs/runbooks/"
echo "    - deploy.md"
echo "    - rollback.md"
echo "    - incident-response.md"
echo ""
echo "  docs/releases/"
echo "    - template.md"
echo ""
echo "  scripts/"
echo "    - check_migration.py"
echo "    - check_changelog.py"
echo "    - verify_refactor.sh"
echo ""
echo "  根目录"
echo "    - justfile"
echo "    - CLAUDE.md（精简版）"
echo ""
echo "  .github/workflows/"
echo "    - ci.yml（合并更新）"
echo ""

# ==================== 完成 ====================
echo ""
echo -e "${GREEN}=============================================="
echo "  Phase 1-2 执行完成"
echo "==============================================${NC}"
echo ""
echo "下一步:"
echo "  1. 复制 Phase 3 附件到对应目录"
echo "  2. 更新 README.md"
echo "  3. 运行验证: bash scripts/verify_refactor.sh"
echo "  4. 提交 Phase 3: git commit -m 'refactor: phase3 增强治理能力'"
echo "  5. 创建 PR"
echo ""

# 显示当前状态
echo "当前根目录文件数: $(ls -1 | wc -l)"
echo ""
echo "当前 docs/ 结构:"
ls -la docs/ 2>/dev/null || echo "(docs/目录不存在)"
