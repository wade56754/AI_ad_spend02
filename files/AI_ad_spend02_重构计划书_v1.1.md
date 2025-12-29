# AI广告代投系统 - 项目重构计划书

> **版本**: v1.1
> **日期**: 2025-12-27
> **状态**: 待评审
> **预计工时**: 18小时（2-3天）
> **风险等级**: 低

---

## 变更记录

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| v1.1 | 2025-12-27 | 修复P0缺陷：MASTER.md策略、引用更新命令、检查脚本、CI更新 |
| v1.0 | 2025-12-27 | 初始版本 |

---

## 一、执行摘要

### 1.1 重构决策

| 选项 | 工时 | 风险 | 决策 |
|------|:----:|:----:|:----:|
| 推倒重建 | 2-3个月 | 高 | ❌ 否决 |
| **渐进重构** | 2-3天 | 低 | ✅ 采纳 |

### 1.2 核心目标

```
将现有项目从"能跑"升级到"能上线、能追溯、能验收"
```

### 1.3 关键成果

| 成果 | 说明 | 验收标准 |
|------|------|---------|
| 根目录清洁度 | 从60+文件减少到<15个 | `ls -1 \| wc -l` < 15 |
| SoT治理 | 固定文件名 + 模块索引 + 变更记录 | docs/sot/下有MASTER/INDEX/CHANGELOG |
| 门禁可执行 | 每条门禁有命令/阈值/证据产物 | CI自动执行所有门禁 |
| 命令入口统一 | justfile跨平台一键执行 | `just --list` 正常 |
| 发布可追溯 | 每次上线有完整发布记录 | docs/releases/有记录 |

---

## 二、现状诊断

### 2.1 项目基本信息

| 维度 | 现状 |
|------|------|
| 仓库 | https://github.com/wade56754/AI_ad_spend02 |
| 分支 | sot-fix-20251123 |
| Commits | 170+ |
| 技术栈 | FastAPI + Next.js 15 + Supabase |
| 文档架构 | 5层(overview/sot/dev-guides/architecture/infrastructure) |

### 2.2 问题清单

#### P0 - 阻塞上线

| ID | 问题 | 影响 |
|----|------|------|
| P0-1 | 根目录60+文件混乱 | 新人无法理解项目结构 |
| P0-2 | 缺少模块→SoT映射 | AI编码时不知道查哪个规则 |
| P0-3 | 缺少可执行门禁 | CI只能检查lint/test，无法验证业务合规 |
| P0-4 | 缺少发布归档 | 上线不可追溯 |
| P0-5 | SoT分散在多个目录 | 不知道哪个是权威版本 |

#### P1 - 影响效率

| ID | 问题 | 影响 |
|----|------|------|
| P1-1 | 脚本不跨平台 | Windows用户需要额外配置 |
| P1-2 | AI工具配置6套并存 | 维护成本高 |
| P1-3 | CLAUDE.md可能过长 | 超出token预算 |
| P1-4 | SoT版本分散 | 不知道哪个是最新 |

#### P2 - 技术债务

| ID | 问题 | 影响 |
|----|------|------|
| P2-1 | 调试文件散落根目录 | 代码库不整洁 |
| P2-2 | 乱码文件名存在 | Git可能出问题 |
| P2-3 | 报告文件未归档 | 历史信息难查找 |

### 2.3 保留资产

| 资产 | 价值 | 处理 |
|------|------|------|
| backend/ | 后端API实现 | ✅ 保留 |
| frontend/ | 前端页面实现 | ✅ 保留 |
| tests/ | 测试代码 | ✅ 保留 |
| .github/workflows/ | CI/CD配置 | ✅ 保留并增强 |
| docs/2.sot/ | SoT文档 | ✅ **移动**到docs/sot/ |
| docs/3.dev-guides/ | 开发指南 | ✅ 保留 |
| .cursor/rules/ | Cursor规则 | ✅ 保留 |
| alembic迁移链 | 数据库版本 | ✅ 保留 |

---

## 三、目标结构

### 3.1 目标目录树

```
AI_ad_spend02/
├── README.md                           # 项目入口（更新结构说明）
├── CLAUDE.md                           # 极简记忆（<30行）
├── justfile                            # 跨平台命令入口 ⭐新增
│
├── docs/
│   ├── sot/                            # SoT唯一真相源 ⭐重组
│   │   ├── MASTER.md                   # 规格文档（从1.overview/移入）
│   │   ├── INDEX.md                    # 模块→规格映射 ⭐新增
│   │   ├── CHANGELOG.md                # 变更记录 ⭐新增
│   │   ├── STATE_MACHINE.md            # 状态机
│   │   ├── DATA_SCHEMA.md              # 数据模型
│   │   ├── LEDGER_SOT.md               # 账本规格 ⭐确保包含
│   │   ├── API_SOT.md                  # API规格
│   │   ├── BUSINESS_RULES.md           # 业务规则
│   │   ├── ERROR_CODES_SOT.md          # 错误码
│   │   └── AUTH_SPEC.md                # 认证规格
│   │
│   ├── adr/                            # 架构决策记录 ⭐新增
│   │   ├── template.md
│   │   ├── 001-七角色模型.md
│   │   ├── 002-phase1只提示.md
│   │   └── 003-可用资金术语统一.md
│   │
│   ├── releases/                       # 发布归档 ⭐新增
│   │   ├── template.md
│   │   ├── approvals/                  # 审批截图存放
│   │   └── artifacts/                  # 验收产物存放
│   │
│   ├── runbooks/                       # 运维手册 ⭐新增
│   │   ├── deploy.md
│   │   ├── rollback.md
│   │   └── incident-response.md
│   │
│   ├── exemptions/                     # 门禁豁免 ⭐新增
│   │
│   ├── 1.overview/                     # 保留（移除MASTER.md）
│   │   ├── PROJECT.md
│   │   ├── CORE_MODULES.md
│   │   └── MASTER_MOVED.md             # 引用说明文件
│   │
│   ├── 3.dev-guides/                   # 保留
│   ├── 4.architecture/                 # 保留
│   │
│   └── archive/                        # 归档
│       ├── 2.sot-legacy/               # 旧SoT备份（重构后删除目录）
│       ├── reports-2024/               # 报告归档
│       └── 5.infrastructure-legacy/    # 旧infra备份
│
├── .ai-rules/                          # AI规则 ⭐新增
│   ├── engineering.md                  # 工程规范（引用sot/）
│   └── quality-gates.md                # 门禁（可执行）
│
├── .cursor/rules/                      # 保留
│   ├── core.mdc
│   ├── backend.mdc
│   └── frontend.mdc
│
├── .claude/                            # 保留并整理
│   ├── commands/
│   │   ├── create-feature.md
│   │   ├── check-sot.md
│   │   └── release-check.md
│   └── PROJECT_RULES.md                # 保留（.ai-rules引用它）
│
├── scripts/                            # 整理后保留
│   ├── check_migration.py              # ⭐新增（门禁依赖）
│   ├── check_changelog.py              # ⭐新增（门禁依赖）
│   ├── verify_refactor.sh              # ⭐新增（验证脚本）
│   ├── dev.sh / dev.bat
│   └── ...
│
├── backend/                            # 保留不动
├── frontend/                           # 保留不动
├── tests/                              # 保留（移入散落的测试文件）
│
├── .github/workflows/                  # 保留并增强
│   ├── ci.yml                          # ⭐更新门禁
│   └── deploy.yml
│
└── [配置文件]                          # 保留
    ├── package.json
    ├── requirements.txt
    ├── alembic.ini
    ├── pytest.ini
    ├── ruff.toml
    └── ...
```

### 3.2 关键决策：MASTER.md 处理策略

> ⚠️ **重要**: 采用"移动"而非"复制"，确保SoT唯一性

```bash
# 正确做法：移动
mv docs/1.overview/MASTER.md docs/sot/MASTER.md

# 在原位置创建引用说明
cat > docs/1.overview/MASTER_MOVED.md << 'EOF'
# MASTER.md 已迁移

本文件已移至 `docs/sot/MASTER.md`。

请直接访问: [docs/sot/MASTER.md](../sot/MASTER.md)

迁移日期: 2025-12-27
EOF
```

### 3.3 删除清单

```
待删除文件（约25个）:

# 调试/临时文件
analyze_excel.py
analyze_excel_files.py
analyze_excel_v2.py
debug_api.py
quick_test.py
check_with_team.py
fix_team_data.py

# 导入脚本（功能已完成）
import_daily_reports.py
import_excel_data.py
import_to_database.py
import_to_sqlite.py
import_to_supabase.py
import_to_supabase_v2.py

# 临时数据文件
excel_analysis.json
excel_analysis.txt
excel_stats.json
coverage.json
processed_data.json
excel_analysis_result.md

# 乱码/错误文件
dgit1108frontendsrcapppage.tsx
打造小红书自动化运营（二）...副本.docx

# 根目录散落的测试文件（移动到tests/）
test_auth_navigation.js
test_reconciliation_api.py
```

### 3.4 归档清单

```
待归档文件（约10个）→ docs/archive/reports-2024/

CODE_AUDIT_REPORT.md
DOCS_ALIGNMENT_REPORT.md
DOC_AUDIT_REPORT_v2.0.md
API_AUDIT_REPORT.json
FLOW_ARCHITECTURE_ANALYSIS_REPORT.md
DASHBOARD_DESIGN_COMPLIANCE_ANALYSIS.md
FRONTEND_DEVELOPMENT_PROGRESS_REPORT_v1.0.md
FACEBOOK_AD_COST_ATTRIBUTION_BENCHMARK_v1.0.md
```

### 3.5 移动清单

```
待移动文件:

# 测试文件 → tests/
test_auth_navigation.js → tests/e2e/
test_reconciliation_api.py → tests/integration/

# 脚本文件 → scripts/
setup-playwright-mcp.bat → scripts/
setup-supabase-mcp.bat → scripts/
start-dev.bat → scripts/
start-dev.sh → scripts/
run_migration_and_import.py → scripts/
run_regression_tests.sh → scripts/
run_tests.py → scripts/
build_package.py → scripts/
update_mcp_config.py → scripts/

# SoT文件重组
docs/1.overview/MASTER.md → docs/sot/MASTER.md（移动，非复制）
docs/2.sot/* → docs/sot/（移动）
```

### 3.6 旧目录清理策略

```bash
# 重构完成后执行

# 1. docs/2.sot/ 目录处理
#    先备份到 archive，移动内容后删除空目录
cp -r docs/2.sot docs/archive/2.sot-legacy  # Phase 2.2 已执行
mv docs/2.sot/* docs/sot/                    # Phase 2.3 已执行
rmdir docs/2.sot                             # Phase 2.9 删除空目录

# 2. docs/1.overview/MASTER.md 处理
#    移动后创建引用文件
mv docs/1.overview/MASTER.md docs/sot/MASTER.md
# 创建 MASTER_MOVED.md 说明文件（见3.2节）
```

---

## 四、执行计划

### 4.1 阶段划分

```
Phase 1: 清理（Day 1上午，3小时）
├── 1.1 创建工作分支
├── 1.2 删除临时文件
├── 1.3 归档报告文件
├── 1.4 移动测试文件
├── 1.5 移动脚本文件
└── 1.6 提交checkpoint

Phase 2: 重组（Day 1下午，4小时）
├── 2.1 创建新目录结构
├── 2.2 备份旧SoT
├── 2.3 移动SoT文件
├── 2.4 移动MASTER.md（非复制）
├── 2.5 创建MASTER_MOVED.md引用
├── 2.6 创建INDEX.md
├── 2.7 创建CHANGELOG.md
├── 2.8 更新文档引用（批量替换）
├── 2.9 删除空的旧目录
└── 2.10 提交checkpoint

Phase 3: 增强（Day 2上午，5小时）
├── 3.1 创建quality-gates.md
├── 3.2 创建engineering.md
├── 3.3 创建justfile
├── 3.4 精简CLAUDE.md
├── 3.5 创建ADR文件（3个）
├── 3.6 创建runbooks（3个）
├── 3.7 创建发布模板
├── 3.8 创建检查脚本（check_migration.py, check_changelog.py）
├── 3.9 创建验证脚本（verify_refactor.sh）
├── 3.10 更新CI配置
├── 3.11 更新README.md
└── 3.12 提交checkpoint

Phase 4: 验证（Day 2下午，3小时）
├── 4.1 运行后端测试
├── 4.2 运行前端检查
├── 4.3 运行验证脚本
├── 4.4 验证justfile
├── 4.5 验证CI门禁
├── 4.6 创建PR
├── 4.7 团队评审
└── 4.8 合并到主分支
```

### 4.2 详细任务清单

#### Phase 1: 清理（3小时）

| 序号 | 任务 | 命令/操作 | 检查点 |
|:----:|------|----------|--------|
| 1.1 | 创建工作分支 | `git checkout -b refactor/doc-structure-v2` | 分支创建成功 |
| 1.2 | 删除临时文件 | 执行 `scripts/refactor/phase1_cleanup.sh` | 根目录文件<30个 |
| 1.3 | 归档报告文件 | `mkdir -p docs/archive/reports-2024 && mv *_REPORT*.md docs/archive/reports-2024/` | 报告归档完成 |
| 1.4 | 移动测试文件 | `mkdir -p tests/e2e tests/integration && mv test_*.js tests/e2e/ && mv test_*.py tests/integration/` | 根目录无test_* |
| 1.5 | 移动脚本文件 | `mv setup-*.bat scripts/ && mv start-dev.* scripts/` | 根目录无脚本 |
| 1.6 | 提交checkpoint | `git add -A && git commit -m "refactor: phase1 清理根目录"` | commit成功 |

**Phase 1 清理脚本** (`scripts/refactor/phase1_cleanup.sh`):
```bash
#!/bin/bash
set -e

echo "=== Phase 1: 清理根目录 ==="

# 删除调试文件
rm -f analyze_excel*.py
rm -f debug_api.py quick_test.py
rm -f check_with_team.py fix_team_data.py

# 删除导入脚本
rm -f import_daily_reports.py
rm -f import_excel_data.py
rm -f import_to_database.py
rm -f import_to_sqlite.py
rm -f import_to_supabase*.py

# 删除临时数据
rm -f excel_analysis.json excel_analysis.txt excel_stats.json
rm -f coverage.json processed_data.json
rm -f excel_analysis_result.md

# 删除乱码文件
rm -f "dgit1108frontendsrcapppage.tsx" 2>/dev/null || true
rm -f "打造小红书自动化运营"* 2>/dev/null || true

echo "✓ Phase 1 清理完成"
echo "当前根目录文件数: $(ls -1 | wc -l)"
```

#### Phase 2: 重组（4小时）

| 序号 | 任务 | 命令/操作 | 检查点 |
|:----:|------|----------|--------|
| 2.1 | 创建新目录 | 执行 `scripts/refactor/phase2_structure.sh` | 目录结构正确 |
| 2.2 | 备份旧SoT | `cp -r docs/2.sot docs/archive/2.sot-legacy` | 备份完成 |
| 2.3 | 移动SoT文件 | `mv docs/2.sot/* docs/sot/` | 文件移动完成 |
| 2.4 | **移动**MASTER.md | `mv docs/1.overview/MASTER.md docs/sot/MASTER.md` | MASTER在sot/下 |
| 2.5 | 创建引用文件 | 创建 `docs/1.overview/MASTER_MOVED.md` | 引用文件存在 |
| 2.6 | 创建INDEX.md | 复制附件A | INDEX.md存在 |
| 2.7 | 创建CHANGELOG.md | 复制附件B | CHANGELOG存在 |
| 2.8 | **更新文档引用** | 执行 `scripts/refactor/update_refs.sh` | 无断链 |
| 2.9 | 删除空目录 | `rmdir docs/2.sot` | 旧目录已删除 |
| 2.10 | 提交checkpoint | `git add -A && git commit -m "refactor: phase2 重组SoT结构"` | commit成功 |

**Phase 2 创建目录脚本** (`scripts/refactor/phase2_structure.sh`):
```bash
#!/bin/bash
set -e

echo "=== Phase 2: 创建目录结构 ==="

# 创建新目录
mkdir -p docs/sot
mkdir -p docs/adr
mkdir -p docs/releases/artifacts
mkdir -p docs/releases/approvals
mkdir -p docs/runbooks
mkdir -p docs/exemptions
mkdir -p docs/archive/2.sot-legacy
mkdir -p docs/archive/reports-2024
mkdir -p docs/archive/5.infrastructure-legacy
mkdir -p .ai-rules
mkdir -p tests/e2e
mkdir -p tests/integration

echo "✓ 目录结构创建完成"
```

**Phase 2 更新引用脚本** (`scripts/refactor/update_refs.sh`):
```bash
#!/bin/bash
set -e

echo "=== 更新文档引用 ==="

# 替换 docs/2.sot/ → docs/sot/
echo "替换 docs/2.sot/ → docs/sot/ ..."
find . -name "*.md" -not -path "./docs/archive/*" -exec sed -i 's|docs/2\.sot/|docs/sot/|g' {} \;
find . -name "*.py" -exec sed -i 's|docs/2\.sot/|docs/sot/|g' {} \;
find . -name "*.ts" -exec sed -i 's|docs/2\.sot/|docs/sot/|g' {} \;
find . -name "*.tsx" -exec sed -i 's|docs/2\.sot/|docs/sot/|g' {} \;
find . -name "*.mdc" -exec sed -i 's|docs/2\.sot/|docs/sot/|g' {} \;

# 替换 docs/1.overview/MASTER.md → docs/sot/MASTER.md
echo "替换 MASTER.md 引用..."
find . -name "*.md" -not -path "./docs/archive/*" -exec sed -i 's|docs/1\.overview/MASTER\.md|docs/sot/MASTER.md|g' {} \;
find . -name "*.py" -exec sed -i 's|docs/1\.overview/MASTER\.md|docs/sot/MASTER.md|g' {} \;

# 检查是否还有遗漏
echo ""
echo "检查遗漏的旧路径引用..."
remaining=$(grep -r "docs/2.sot" . --include="*.md" --include="*.py" --include="*.ts" 2>/dev/null | grep -v "archive" | wc -l)
if [ "$remaining" -gt 0 ]; then
    echo "⚠️ 发现 $remaining 处遗漏，请手动检查:"
    grep -r "docs/2.sot" . --include="*.md" --include="*.py" --include="*.ts" 2>/dev/null | grep -v "archive"
else
    echo "✓ 无遗漏"
fi

echo "✓ 引用更新完成"
```

**MASTER_MOVED.md 内容**:
```markdown
# MASTER.md 已迁移

> ⚠️ 本文件已移至 `docs/sot/MASTER.md`

## 新位置

请直接访问: [docs/sot/MASTER.md](../sot/MASTER.md)

## 迁移说明

- **迁移日期**: 2025-12-27
- **原因**: 统一SoT目录结构，确保唯一真相源
- **影响**: 所有引用已自动更新

如发现断链，请更新为 `docs/sot/MASTER.md`
```

#### Phase 3: 增强（5小时）

| 序号 | 任务 | 命令/操作 | 检查点 |
|:----:|------|----------|--------|
| 3.1 | 创建quality-gates.md | 复制附件C | 门禁文件存在 |
| 3.2 | 创建engineering.md | 复制附件D | 工程规范存在 |
| 3.3 | 创建justfile | 复制附件E | `just --list` 正常 |
| 3.4 | 精简CLAUDE.md | 复制附件F | <30行 |
| 3.5 | 创建ADR文件 | 复制附件G/H/I/J | ADR目录有4个文件 |
| 3.6 | 创建runbooks | 复制附件K/L/M | runbooks/有3个文件 |
| 3.7 | 创建发布模板 | 复制附件N | releases/有模板 |
| 3.8 | 创建检查脚本 | 复制附件O/P | 脚本可执行 |
| 3.9 | 创建验证脚本 | 复制附件Q | verify_refactor.sh存在 |
| 3.10 | **更新CI配置** | 复制附件R | CI包含新门禁 |
| 3.11 | **更新README.md** | 复制附件S | README反映新结构 |
| 3.12 | 提交checkpoint | `git commit -m "refactor: phase3 增强治理能力"` | commit成功 |

#### Phase 4: 验证（3小时）

| 序号 | 任务 | 命令/操作 | 检查点 |
|:----:|------|----------|--------|
| 4.1 | 运行后端测试 | `cd backend && pytest -q` | 测试通过 |
| 4.2 | 运行前端检查 | `cd frontend && npm run lint && npm run type-check` | 无错误 |
| 4.3 | **运行验证脚本** | `bash scripts/verify_refactor.sh` | 全部通过 |
| 4.4 | 验证justfile | `just test` | 命令正常 |
| 4.5 | **验证CI门禁** | `just ci-check` | 门禁通过 |
| 4.6 | 创建PR | GitHub PR | PR创建成功 |
| 4.7 | 团队评审 | 等待review | 2人approve |
| 4.8 | 合并到主分支 | Squash merge | 合并成功 |

### 4.3 时间表

```
Day 1 (12月28日)
├── 09:00-12:00  Phase 1: 清理（3h）
├── 12:00-13:00  午休
├── 13:00-17:00  Phase 2: 重组（4h）
└── 17:00-18:00  自测

Day 2 (12月29日)
├── 09:00-14:00  Phase 3: 增强（5h）
├── 14:00-17:00  Phase 4: 验证（3h）
└── 17:00-18:00  PR评审

Day 3 (12月30日)
├── 处理评审意见
└── 合并到主分支
```

---

## 五、风险评估

### 5.1 风险矩阵

| 风险 | 概率 | 影响 | 缓解措施 |
|------|:----:|:----:|---------|
| 删错文件 | 低 | 中 | Git可恢复；先备份到archive |
| 文档链接断裂 | 中 | 低 | update_refs.sh自动替换；verify_refactor.sh检查 |
| 测试失败 | 低 | 中 | 不动业务代码；只动文档 |
| 团队不适应新结构 | 中 | 低 | 写迁移说明；更新README |
| justfile不兼容 | 低 | 低 | 保留原脚本作为备选 |
| Windows兼容性 | 中 | 低 | 提供PowerShell备选命令 |

### 5.2 回滚方案

```bash
# 如果重构失败，可以快速回滚
git checkout main
git branch -D refactor/doc-structure-v2

# 或者部分回滚
git revert <commit-hash>

# 恢复SoT文件
cp -r docs/archive/2.sot-legacy/* docs/2.sot/
```

### 5.3 Windows 兼容性说明

```powershell
# Windows用户安装just
winget install Casey.Just

# 或使用scoop
scoop install just

# 如果just不可用，使用备选命令
# just dev-backend → cd backend && uvicorn main:app --reload
# just test → cd backend && pytest
```

---

## 六、验收标准

### 6.1 结构验收

| 检查项 | 标准 | 验证命令 |
|--------|------|---------|
| 根目录文件数 | < 15个（不含隐藏） | `ls -1 \| wc -l` |
| docs/sot/MASTER.md | 存在且版本正确 | `head -5 docs/sot/MASTER.md` |
| docs/sot/INDEX.md | 存在且>50行 | `wc -l docs/sot/INDEX.md` |
| docs/sot/CHANGELOG.md | 存在 | `test -f docs/sot/CHANGELOG.md` |
| docs/sot/LEDGER_SOT.md | 存在 | `test -f docs/sot/LEDGER_SOT.md` |
| .ai-rules/quality-gates.md | 存在且含pytest | `grep "pytest" .ai-rules/quality-gates.md` |
| justfile | 存在且可用 | `just --list` |
| 旧目录已清理 | docs/2.sot/不存在 | `! test -d docs/2.sot` |

### 6.2 功能验收

| 检查项 | 标准 | 验证命令 |
|--------|------|---------|
| 后端测试 | 全部通过 | `cd backend && pytest` |
| 前端lint | 无错误 | `cd frontend && npm run lint` |
| 前端类型 | 无错误 | `cd frontend && npm run type-check` |
| just dev | 能启动 | `just dev-backend` |
| just test | 能执行 | `just test` |
| CI门禁 | 全部通过 | `just ci-check` |

### 6.3 文档验收

| 检查项 | 标准 | 验证命令 |
|--------|------|---------|
| 无断链 | 无docs/2.sot引用 | `grep -r "docs/2.sot" . --include="*.md" \| grep -v archive` |
| 引用一致 | 旧路径已更新 | verify_refactor.sh |
| README更新 | 反映新结构 | 人工检查 |
| CLAUDE.md | < 30行 | `wc -l CLAUDE.md` |

### 6.4 跨平台验收

| 平台 | 检查项 | 验证方式 |
|------|--------|---------|
| macOS/Linux | just命令正常 | `just --list` |
| Windows | just命令正常 | `just --list` (PowerShell) |
| Windows备选 | 原脚本可用 | `scripts/start-dev.bat` |

---

## 七、附件清单

| 序号 | 附件 | 路径 | 状态 | 优先级 |
|:----:|------|------|:----:|:------:|
| A | INDEX.md | docs/sot/INDEX.md | ✅ 已生成 | P0 |
| B | CHANGELOG.md | docs/sot/CHANGELOG.md | ✅ 已生成 | P0 |
| C | quality-gates.md | .ai-rules/quality-gates.md | ✅ 已生成 | P0 |
| D | engineering.md | .ai-rules/engineering.md | ✅ 已生成 | P0 |
| E | justfile | justfile | ✅ 已生成 | P0 |
| F | CLAUDE.md | CLAUDE.md | ✅ 已生成 | P0 |
| G | ADR template | docs/adr/template.md | ✅ 已生成 | P1 |
| H | ADR-001 | docs/adr/001-七角色模型.md | ✅ 已生成 | P1 |
| I | ADR-002 | docs/adr/002-phase1只提示.md | ✅ 已生成 | P1 |
| J | ADR-003 | docs/adr/003-可用资金术语.md | ⏳ 待生成 | P1 |
| K | deploy.md | docs/runbooks/deploy.md | ✅ 已生成 | P1 |
| L | rollback.md | docs/runbooks/rollback.md | ✅ 已生成 | P1 |
| M | incident-response.md | docs/runbooks/incident-response.md | ⏳ 待生成 | P2 |
| N | release template | docs/releases/template.md | ✅ 已生成 | P1 |
| O | check_migration.py | scripts/check_migration.py | ⏳ 待生成 | P0 |
| P | check_changelog.py | scripts/check_changelog.py | ⏳ 待生成 | P0 |
| Q | verify_refactor.sh | scripts/verify_refactor.sh | ⏳ 待生成 | P0 |
| R | ci.yml更新 | .github/workflows/ci.yml | ⏳ 待生成 | P0 |
| S | README更新 | README.md（更新章节） | ⏳ 待生成 | P1 |

---

## 八、执行进度追踪

> 执行时更新此表

| Phase | 任务 | 状态 | 执行人 | 完成时间 | 备注 |
|:-----:|------|:----:|--------|---------|------|
| 1.1 | 创建工作分支 | ☐ | | | |
| 1.2 | 删除临时文件 | ☐ | | | |
| 1.3 | 归档报告文件 | ☐ | | | |
| 1.4 | 移动测试文件 | ☐ | | | |
| 1.5 | 移动脚本文件 | ☐ | | | |
| 1.6 | 提交checkpoint | ☐ | | | |
| 2.1 | 创建新目录 | ☐ | | | |
| 2.2 | 备份旧SoT | ☐ | | | |
| 2.3 | 移动SoT文件 | ☐ | | | |
| 2.4 | 移动MASTER.md | ☐ | | | |
| 2.5 | 创建引用文件 | ☐ | | | |
| 2.6 | 创建INDEX.md | ☐ | | | |
| 2.7 | 创建CHANGELOG.md | ☐ | | | |
| 2.8 | 更新文档引用 | ☐ | | | |
| 2.9 | 删除空目录 | ☐ | | | |
| 2.10 | 提交checkpoint | ☐ | | | |
| 3.1-3.12 | Phase 3全部 | ☐ | | | |
| 4.1-4.8 | Phase 4全部 | ☐ | | | |

---

## 九、团队通知模板

重构完成后发送：

```markdown
@all 【项目结构重构完成通知】

## 变更内容

1. **SoT文档统一**
   - 原 `docs/2.sot/` → 现 `docs/sot/`
   - 原 `docs/1.overview/MASTER.md` → 现 `docs/sot/MASTER.md`

2. **新增文件**
   - `docs/sot/INDEX.md` - 模块→规格映射（开发前必查）
   - `.ai-rules/quality-gates.md` - 门禁规范
   - `justfile` - 统一命令入口

3. **命令入口统一**
   - `just dev` - 启动开发环境
   - `just test` - 运行测试
   - `just ci-check` - CI门禁检查

## 迁移指南

| 原路径 | 新路径 |
|--------|--------|
| docs/2.sot/xxx.md | docs/sot/xxx.md |
| docs/1.overview/MASTER.md | docs/sot/MASTER.md |

## 开发流程变更

开发前请查阅 `docs/sot/INDEX.md` 找到对应的SoT章节。

## 生效时间

2025-12-30 合并后生效

## 问题反馈

如遇问题请联系 @xxx
```

---

## 十、回归检查清单

重构后首次上线前验证：

```markdown
## 功能回归

- [ ] 登录/登出正常
- [ ] 投手日报CRUD正常
- [ ] 项目CRUD正常
- [ ] 账户CRUD正常
- [ ] 权限隔离正常（投手只能看自己账户）
- [ ] 状态流转正常

## 门禁回归

- [ ] pytest全部通过
- [ ] ruff检查通过
- [ ] mypy检查通过
- [ ] CI自动执行门禁

## 文档回归

- [ ] 无断链（verify_refactor.sh通过）
- [ ] README正确反映新结构
- [ ] CLAUDE.md正常工作
```

---

## 十一、审批签字

| 角色 | 姓名 | 日期 | 签字 |
|------|------|------|:----:|
| 项目负责人 | | | ☐ |
| 技术负责人 | | | ☐ |
| 执行者 | | | ☐ |

---

**文档状态**: 待评审
**下一步**: 确认后生成所有缺失附件（O/P/Q/R/S及J/M）
