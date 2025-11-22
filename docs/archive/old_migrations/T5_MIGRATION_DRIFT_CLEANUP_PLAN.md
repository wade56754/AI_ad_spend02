# T5: 迁移漂移清理执行计划

> **文档版本**: v1.0
> **创建日期**: 2025-11-20
> **状态**: 待执行 (Pending Execution)
> **风险等级**: 🟡 中等 - 需要先验证生产环境状态

---

## 📋 执行摘要

本计划旨在清理 `backend/alembic/versions/` 目录中的重复迁移脚本，解决迁移漂移问题。经分析发现 **5个重复脚本** 和 **2条冲突的revision链**。

**执行前提**: 必须先查询生产环境数据库的 `alembic_version` 表，确认哪些版本已应用。

---

## 🔍 问题分析

### 重复迁移脚本清单

| 文件名 | Revision ID | 功能 | 归档理由 |
|--------|-------------|------|----------|
| `20251117_reconciliation_pk_bigserial.py` | 20251117_reconciliation_pk_bigserial | 对账表PK升级为BIGSERIAL | 与 `reconciliation_pk_to_bigserial.py` 重复 |
| `20251117_reconciliation_status_align.py` | 20251117_reconciliation_status_align | 状态枚举对齐 | 与 `reconciliation_status_alignment.py` 重复 |
| `20251117_analyze_user_fk.py` | 20251117_analyze_user_fk | 用户FK分析（临时脚本） | 仅用于分析，正式环境不需要 |
| `20251117_fix_ad_spend_user_fk.py` | 20251117_fix_ad_spend_user_fk | 修复ad_spend_daily用户FK | 与 `ad_spend_daily_user_fks_fix.py` 重复 |
| `20251117_fix_recon_detail_user_fk.py` | 20251117_fix_recon_detail_user_fk | 修复recon_details用户FK | 已被 `reconciliation_user_fks_to_uuid.py` 覆盖 |

### 保留的脚本

| 文件名 | Revision ID | 保留理由 |
|--------|-------------|----------|
| `20251117_reconciliation_pk_to_bigserial.py` | 20251117_reconciliation_pk_to_bigserial | 更完整的命名，依赖主线revision |
| `20251117_reconciliation_status_alignment.py` | 20251117_reconciliation_status_alignment | 更规范的命名（alignment > align） |
| `20251117_reconciliation_user_fks_to_uuid.py` | 20251117_reconciliation_user_fks_to_uuid | 一次性修复所有对账模块FK，更简洁 |
| `20251117_ad_spend_daily_user_fks_fix.py` | 20251117_ad_spend_daily_user_fks_fix | 最终版本，修复ad_spend_daily表 |
| `20251117_fix_recon_other_user_fk.py` | 20251117_fix_recon_other_user_fk | 修复其他对账表FK（未被覆盖） |

---

## ⚠️ 执行前必检项

### 步骤1: 检查生产环境alembic版本

**在生产环境PostgreSQL数据库中执行**:

```sql
-- 1. 检查alembic_version表是否存在
SELECT EXISTS (
    SELECT FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name = 'alembic_version'
) AS alembic_table_exists;

-- 2. 查看所有已应用的迁移版本
SELECT version_num
FROM alembic_version
ORDER BY version_num DESC;

-- 3. ⚠️ 关键检查：查看是否有20251117开头的版本
SELECT version_num
FROM alembic_version
WHERE version_num LIKE '20251117%'
ORDER BY version_num;
```

### 步骤2: 判断安全性

根据SQL查询结果判断：

#### **场景A: 表不存在或无20251117版本** ✅ 安全
```
-- 查询结果为空
version_num
-----------
(0 rows)
```
**结论**: 可以安全归档所有5个重复脚本

---

#### **场景B: 部分版本已应用** ⚠️ 需要调整

**示例输出**:
```
version_num
------------------------------------------
20251117_reconciliation_pk_to_bigserial
20251117_ad_spend_daily_user_fks_fix
```

**决策规则**:
- ✅ 如果**待归档脚本的revision ID不在**查询结果中 → 可以归档
- ❌ 如果**待归档脚本的revision ID已在**查询结果中 → **不能归档**

**需要保留的脚本判断表**:

| Revision ID | 在生产环境? | 操作 |
|-------------|------------|------|
| 20251117_reconciliation_pk_bigserial | ❌ 否 | ✅ 归档 |
| 20251117_reconciliation_pk_bigserial | ✅ 是 | ❌ 保留 |
| 20251117_reconciliation_status_align | ❌ 否 | ✅ 归档 |
| 20251117_analyze_user_fk | ❌ 否 | ✅ 归档 |
| 20251117_fix_ad_spend_user_fk | ❌ 否 | ✅ 归档 |
| 20251117_fix_recon_detail_user_fk | ❌ 否 | ✅ 归档 |

---

## 📝 执行步骤

### 阶段1: 备份 (⏱ 5分钟)

```bash
# 进入项目目录
cd d:\git\1108\AI_ad_spend02\backend

# 1. 备份alembic版本目录
mkdir -p alembic\versions\backup_20251120_pre_t5
copy alembic\versions\*.py alembic\versions\backup_20251120_pre_t5\

# 2. 验证备份完整性
dir alembic\versions\backup_20251120_pre_t5 | find /C ".py"
# 应该显示 24 (与原目录文件数一致)

# 3. 记录当前alembic状态
alembic current > alembic_status_pre_t5.txt
alembic history >> alembic_status_pre_t5.txt
alembic heads >> alembic_status_pre_t5.txt
```

---

### 阶段2: 创建归档目录 (⏱ 1分钟)

```bash
# 创建专用归档目录
mkdir backend\alembic\versions\archived_duplicate_migrations_20251117

# 验证目录创建成功
dir backend\alembic\versions | findstr "archived"
```

---

### 阶段3: 归档重复脚本 (⏱ 3分钟)

**⚠️ 仅在确认生产环境未应用这些版本后执行**

```bash
# 移动待归档文件（Windows命令）
move backend\alembic\versions\20251117_reconciliation_pk_bigserial.py backend\alembic\versions\archived_duplicate_migrations_20251117\
move backend\alembic\versions\20251117_reconciliation_status_align.py backend\alembic\versions\archived_duplicate_migrations_20251117\
move backend\alembic\versions\20251117_analyze_user_fk.py backend\alembic\versions\archived_duplicate_migrations_20251117\
move backend\alembic\versions\20251117_fix_ad_spend_user_fk.py backend\alembic\versions\archived_duplicate_migrations_20251117\
move backend\alembic\versions\20251117_fix_recon_detail_user_fk.py backend\alembic\versions\archived_duplicate_migrations_20251117\

# 验证文件已移动
dir backend\alembic\versions\archived_duplicate_migrations_20251117 | find /C ".py"
# 应该显示 5
```

---

### 阶段4: 验证Alembic健康性 (⏱ 3分钟)

```bash
# 1. 检查revision链条完整性
alembic history

# 2. 确保没有冲突的heads
alembic heads
# 预期输出: 单个head (最新的revision)

# 3. 尝试生成测试迁移（dry-run）
alembic revision --autogenerate -m "test_after_t5_cleanup" --sql

# 4. 检查测试输出无异常后删除
del backend\alembic\versions\*test_after_t5_cleanup*.py
```

**验证成功标准**:
- ✅ `alembic history` 显示线性revision链，无分支
- ✅ `alembic heads` 仅显示1个head
- ✅ `alembic revision --autogenerate` 不报错

---

### 阶段5: 文档归档 (⏱ 2分钟)

在 `backend/alembic/versions/archived_duplicate_migrations_20251117/README.md` 中记录：

```markdown
# 重复迁移脚本归档记录

**归档日期**: 2025-11-20
**归档原因**: 清理迁移漂移，移除重复功能的迁移脚本
**执行人**: [填写]
**关联文档**: `docs/migrations/T5_MIGRATION_DRIFT_CLEANUP_PLAN.md`

## 归档文件清单

| 文件名 | Revision ID | 归档理由 |
|--------|-------------|----------|
| `20251117_reconciliation_pk_bigserial.py` | 20251117_reconciliation_pk_bigserial | 与 `reconciliation_pk_to_bigserial.py` 功能重复 |
| `20251117_reconciliation_status_align.py` | 20251117_reconciliation_status_align | 与 `reconciliation_status_alignment.py` 功能重复 |
| `20251117_analyze_user_fk.py` | 20251117_analyze_user_fk | 临时分析脚本，正式环境不需要 |
| `20251117_fix_ad_spend_user_fk.py` | 20251117_fix_ad_spend_user_fk | 与 `ad_spend_daily_user_fks_fix.py` 功能重复 |
| `20251117_fix_recon_detail_user_fk.py` | 20251117_fix_recon_detail_user_fk | 已被 `reconciliation_user_fks_to_uuid.py` 覆盖 |

## 保留的替代脚本

| 保留的脚本 | 替代的归档脚本 |
|-----------|---------------|
| `20251117_reconciliation_pk_to_bigserial.py` | `20251117_reconciliation_pk_bigserial.py` |
| `20251117_reconciliation_status_alignment.py` | `20251117_reconciliation_status_align.py` |
| `20251117_reconciliation_user_fks_to_uuid.py` + `20251117_ad_spend_daily_user_fks_fix.py` | `20251117_analyze_user_fk.py` + `20251117_fix_ad_spend_user_fk.py` + `20251117_fix_recon_detail_user_fk.py` |

## 回退说明

如果需要恢复归档的脚本：

```bash
# 从归档目录复制回主目录
copy backend\alembic\versions\archived_duplicate_migrations_20251117\*.py backend\alembic\versions\

# 重新验证alembic状态
alembic history
```

**警告**: 回退前请确认不会导致revision冲突。
```

---

## 🔄 回退方案

如果归档后发现问题，可以通过以下步骤回退：

### 方案A: 恢复全部归档脚本

```bash
# 1. 从归档目录复制回主目录
copy backend\alembic\versions\archived_duplicate_migrations_20251117\*.py backend\alembic\versions\

# 2. 验证恢复成功
alembic history
alembic heads
```

### 方案B: 从备份恢复

```bash
# 1. 删除当前versions目录
del /Q backend\alembic\versions\*.py

# 2. 从备份恢复
copy alembic\versions\backup_20251120_pre_t5\*.py backend\alembic\versions\

# 3. 验证恢复
alembic history
```

---

## 📊 风险评估

| 风险 | 等级 | 概率 | 影响 | 缓解措施 |
|------|------|------|------|----------|
| 删除已在生产应用的迁移 | 🔴 高 | 低 | 严重 | **执行前必须查询生产DB** |
| Alembic revision链断裂 | 🟡 中 | 低 | 中等 | 归档前完整备份，验证 `alembic history` |
| 误删未来需要的脚本 | 🟢 低 | 极低 | 低 | 仅移动到archive/，不删除 |
| 本地开发环境迁移失败 | 🟢 低 | 低 | 低 | 使用 `alembic stamp` 重置版本 |

---

## ✅ 执行清单

**请在执行每个步骤后勾选**：

### 执行前检查
- [ ] 已在生产环境执行SQL查询，获取 `alembic_version` 表数据
- [ ] 已确认待归档脚本的revision ID **不在**生产环境的 `alembic_version` 表中
- [ ] 已通知团队成员，暂停提交新的迁移脚本
- [ ] 已备份当前git状态（`git status` 无未提交更改）

### 阶段1: 备份
- [ ] 创建备份目录 `alembic\versions\backup_20251120_pre_t5`
- [ ] 复制所有 `.py` 文件到备份目录
- [ ] 验证备份文件数 = 24
- [ ] 记录当前alembic状态到 `alembic_status_pre_t5.txt`

### 阶段2: 归档目录
- [ ] 创建归档目录 `archived_duplicate_migrations_20251117`
- [ ] 验证目录创建成功

### 阶段3: 归档脚本
- [ ] 移动 `20251117_reconciliation_pk_bigserial.py`
- [ ] 移动 `20251117_reconciliation_status_align.py`
- [ ] 移动 `20251117_analyze_user_fk.py`
- [ ] 移动 `20251117_fix_ad_spend_user_fk.py`
- [ ] 移动 `20251117_fix_recon_detail_user_fk.py`
- [ ] 验证归档目录包含5个文件

### 阶段4: 验证
- [ ] 执行 `alembic history` - 无报错
- [ ] 执行 `alembic heads` - 仅1个head
- [ ] 执行 `alembic revision --autogenerate` - 测试通过
- [ ] 删除测试迁移文件

### 阶段5: 文档
- [ ] 创建归档目录的 `README.md`
- [ ] 记录归档日期、执行人、文件清单
- [ ] 提交git: `git add . && git commit -m "chore(migrations): archive duplicate migration scripts (T5)"`

### 执行后验证
- [ ] 本地运行 `alembic upgrade head` - 成功
- [ ] 本地运行 `alembic downgrade -1` - 成功
- [ ] 本地运行 `alembic upgrade head` - 成功
- [ ] 通知团队成员迁移清理已完成

---

## 📞 联系方式

**如有疑问，请联系**:
- 执行计划作者: Claude AI Assistant
- 技术负责人: [填写]
- 创建日期: 2025-11-20

---

## 📚 参考文档

- [Alembic官方文档 - Branching](https://alembic.sqlalchemy.org/en/latest/branches.html)
- [项目规范 - 数据库迁移指南](../development/DATABASE_MIGRATIONS.md)
- [Phase 1 重构总计划](../../DEVELOPMENT_PROGRESS_REPORT.md)

---

**文档状态**: ✅ 已完成
**待执行**: 需要先查询生产环境数据库状态
**预计执行时间**: 15分钟（不含生产环境查询）
