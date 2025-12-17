# 项目清理清单 (Cleanup Manifest)

> **清理日期**: 2025-12-06 / **更新**: 2025-12-18
> **执行者**: Claude Code
> **基准**: ASDD 6-Layer Framework + SoT Freeze v2.6

---

## 1. 清理统计

| 类别 | 归档数量 | 删除数量 | 说明 |
|------|----------|----------|------|
| 根目录 Python 脚本 | 20 | 2 | 一次性脚本、测试脚本、重复脚本 |
| Backend 脚本 | 22 | 0 | 迁移脚本、测试脚本、调试脚本 |
| 重复迁移文件 | 3 | 0 | 2025-11-17 重复迁移 |
| 过时文档 | 4 | 0 | 旧版本文档 |
| 系统文件 | 0 | 8 | .DS_Store 文件 |
| 根目录过时文档 (2025-12-18) | 2 | 0 | 迁移计划、旧索引 |
| Backend 过时文档 (2025-12-18) | 5 | 0 | 阶段执行报告、待办事项 |
| Backend 测试过时报告 (2025-12-18) | 1 | 0 | 旧版SoT报告 |
| **总计** | **57** | **10** | - |

---

## 2. 归档目录结构

```
docs/archive/2025-12-cleanup/
├── python-scripts-legacy/     # 20 个根目录脚本
├── backend-scripts-legacy/    # 22 个后端脚本
├── migrations-legacy/         # 3 个重复迁移
├── docs-outdated/             # 4 个过时文档
├── root-outdated/             # 2 个根目录过时文档 (2025-12-18)
├── backend-outdated/          # 5 个后端过时文档 (2025-12-18)
├── backend-tests-outdated/    # 1 个测试过时报告 (2025-12-18)
└── CLEANUP_MANIFEST.md        # 本文件
```

---

## 3. 根目录 Python 脚本归档详情

### 3.1 Git 自动化脚本 (重复)
| 文件名 | 大小 | 归档原因 |
|--------|------|----------|
| github_update_ascii.py | 1.8KB | 与 quick_update.py 功能重复 |
| quick_update.py | 1.8KB | 与 update_to_github.py 功能重复 |
| update_to_github.py | 9.7KB | 过时的 git 自动化脚本 |

### 3.2 测试脚本 (一次性/Ad-hoc)
| 文件名 | 大小 | 归档原因 |
|--------|------|----------|
| test_claude_cli.py | 1.4KB | Ad-hoc CLI 测试 |
| test_db_connection.py | 1.5KB | Ad-hoc 数据库连接测试 |
| test_model_imports.py | 5.9KB | 模型重构验证脚本，任务已完成 |
| test_parse_p0_p1.py | 2.9KB | P0/P1 解析测试 |
| test_quick_check.py | 1.1KB | Ad-hoc 快速检查 |
| test_supabase_api.py | 1.6KB | Supabase API 测试 |
| test_supabase_mcp.py | 1.5KB | MCP 测试脚本 |
| test_orch_be_then_test.py | 1.6KB | Agent 编排测试 |

### 3.3 一次性工具脚本
| 文件名 | 大小 | 归档原因 |
|--------|------|----------|
| ai_pipeline.py | 8.0KB | 遗留 AI 管道脚本 |
| check-health.py | 3.8KB | 健康检查脚本 |
| create_agents_structure.py | 12.1KB | 脚手架脚本，agents 目录已创建 |
| fix_imports.py | 7.2KB | 导入路径修复脚本 |
| generate_models_refactor.py | 7.1KB | 模型重构生成器 |
| run_full_test_suite.py | 8.1KB | 遗留测试运行器 |
| super_review_agent.py | 42.4KB | 遗留 Agent 脚本，已被 agents/ 替代 |
| verify_models.py | 1.3KB | 模型验证脚本 |

### 3.4 已删除文件
| 文件名 | 删除原因 |
|--------|----------|
| _test_import.py | 临时测试文件 (下划线前缀) |
| Dgit1108AI_ad_spend02backendmodelsenums.py | 路径编码错误的畸形文件 |

---

## 4. Backend 脚本归档详情

### 4.1 迁移执行脚本
| 文件名 | 归档原因 |
|--------|----------|
| execute_phase0.py | Phase 0 迁移脚本，已执行 |
| execute_phase2a.py | Phase 2a 迁移脚本，已执行 |
| execute_rev_005.py | Revision 005 脚本 |
| execute_rev_006.py | Revision 006 脚本 |
| dba_execute_migration.py | DBA 迁移脚本 |
| migrate_now.py | Ad-hoc 迁移运行器 |
| pre_check.py | 迁移前检查脚本 |
| final_verification.py | 迁移后验证脚本 |
| run_supabase_migration.py | Supabase 迁移运行器 |
| run_supabase_migration_interactive.py | 交互式迁移运行器 |

### 4.2 测试/调试脚本
| 文件名 | 归档原因 |
|--------|----------|
| check_env.py | 环境检查脚本 (6 行) |
| quick_test.py | Ad-hoc 快速测试 |
| test_routes.py | 最小测试路由 (15 行) |
| simple_backend.py | Mock 后端 (85 行) |
| test_api_auth_flow.py | Ad-hoc 认证流程测试 |
| test_auth_simple.py | 简单认证测试 |
| test_config.py | 配置测试 (与 core/test_config.py 重复) |
| test_import.py | 导入测试 |
| test_simple_import.py | 简单导入测试 |
| test_supabase_auth.py | Supabase 认证测试 |
| run_pytest.py | 简单 pytest 包装器 |

### 4.3 模型文件
| 文件名 | 归档原因 |
|--------|----------|
| topup_legacy.py | 旧版 TopupRequest 模型 (已标记 __abstract__) |

---

## 5. 重复迁移归档详情

| 文件名 | 保留版本 | 归档原因 |
|--------|----------|----------|
| 20251117_analyze_user_fk.py | N/A | 分析脚本，非实际迁移 |
| 20251117_reconciliation_pk_bigserial.py | 20251117_reconciliation_pk_to_bigserial.py | 重复迁移 |
| 20251117_reconciliation_status_align.py | 20251117_reconciliation_status_alignment.py | 重复迁移 |

---

## 6. 文档归档详情

| 文件名 | 新位置/归档原因 |
|--------|-----------------|
| PROJECT_DOCS_INDEX_v1.0.md | 已被 docs/README.md v1.2 替代 |
| AUTOMATION_TEST_SPEC_v1.2.md | 已被 v1.4 替代 |
| AUTOMATION_TEST_SPEC_v1.3.md | 已被 v1.4 替代 |
| BACKEND_TEST_FREEZE_REPORT_v1.2.md | 已被 v1.3 替代 |

---

## 7. 文档层级修正

### 已移动到正确层级
| 原位置 | 新位置 |
|--------|--------|
| docs/testing/AUTOMATION_TEST_SPEC_v1.4.md | docs/5.testing/AUTOMATION_TEST_SPEC_v1.4.md |
| docs/testing/BACKEND_TEST_ENV_HEALTH_v1.0.md | docs/5.testing/BACKEND_TEST_ENV_HEALTH_v1.0.md |

### 已删除的空目录
- docs/testing/ (内容已移至 docs/5.testing/)

---

## 8. 保留的关键文件

以下根目录文件保留不动：
- `run_tests.py` - 主测试运行器 (8.1KB，仍在使用)
- `update_mcp_config.py` - MCP 配置更新器 (1.5KB，最近使用)

---

## 9. 安全提醒

⚠️ **已归档文件 `check_and_clean_tables.py` 包含硬编码数据库凭据**

位置: `docs/archive/2025-12-cleanup/backend-scripts-legacy/check_and_clean_tables.py`

建议操作:
1. 确认该凭据是否仍然有效
2. 如有效，立即轮换 Supabase 数据库密码
3. 更新 `.gitignore` 防止类似文件提交

---

## 10. 清理后项目结构

```
AI_Ads/
├── backend/                    # 后端代码 (已清理)
│   ├── alembic/versions/      # 迁移文件 (已去重)
│   ├── models/                # 模型 (保留 topup_fixed.py)
│   ├── routers/               # API 路由
│   ├── services/              # 业务服务
│   ├── tests/                 # 测试套件
│   └── run_tests.py           # 主测试运行器
├── frontend/                   # 前端代码
├── agents/                     # Agent 系统
├── docs/                       # 文档 (6 层架构)
│   ├── 1.overview/            # 概览层
│   ├── 2.sot/                 # 真相源层
│   ├── 3.dev-guides/          # 开发指南层
│   ├── 4.architecture/        # 架构视图层
│   ├── 5.infrastructure/      # 基础设施层
│   ├── 5.testing/             # 测试文档 (已整合)
│   ├── 6.agent-layer/         # Agent 层
│   ├── archive/               # 归档目录
│   └── README.md              # 文档导航 v1.2
├── run_tests.py               # 根目录测试运行器
└── update_mcp_config.py       # MCP 配置工具
```

---

## 11. 验证检查清单

- [x] 根目录 .py 文件减少到 2 个 (run_tests.py, update_mcp_config.py)
- [x] backend/ 无冗余测试脚本
- [x] docs/ 无重复版本文档
- [x] 迁移文件无重复
- [x] .DS_Store 文件已清理
- [x] 文档层级正确 (5.testing 整合完成)

---

**清理完成时间**: 2025-12-06 22:15 UTC+8
**清理状态**: ✅ 完成

---

## 12. 2025-12-18 补充归档

### 12.1 根目录过时文档 (root-outdated/)

| 文件名 | 归档原因 |
|--------|----------|
| AI Spec Driven Development 迁移计划.md | 迁移计划已完成，基于SoT v1.0，现已v2.6 |
| DOCS_README.md | v4.0 旧文档索引，已被 docs/README.md v1.2 替代 |

### 12.2 Backend 过时文档 (backend-outdated/)

| 文件名 | 归档原因 |
|--------|----------|
| TODO_ROUTES.md | 开发待办已过时 (最后更新 2025-11-15) |
| PHASE0_EXECUTION_GUIDE.md | Phase 0 执行指南，已完成 |
| PHASE0_EXECUTION_REPORT.md | Phase 0 执行报告，已完成 |
| PHASE2A_EXECUTION_GUIDE.md | Phase 2a 执行指南，已完成 |
| PHASE2A_FILES_SUMMARY.md | Phase 2a 文件汇总，已完成 |

### 12.3 Backend 测试过时报告 (backend-tests-outdated/)

| 文件名 | 归档原因 |
|--------|----------|
| SOT_ALIGNMENT_FIX_REPORT_v2.0.md | 已被 v3.0 替代 |

### 12.4 修复的问题

| 文件 | 问题 | 修复 |
|------|------|------|
| docs/proposals/AI_CODE_FACTORY_REFACTOR_PROPOSAL.md | 日期笔误 2024-12-17 | 已修正为 2025-12-17 |

---

**补充归档时间**: 2025-12-18 05:15 UTC+8
**补充归档状态**: ✅ 完成
