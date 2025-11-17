# 数据库迁移脚本执行摘要

> **生成日期**: 2025-11-17
> **版本**: v1.0
> **适用范围**: reconciliation_* 和 ad_spend_daily 表的类型修复迁移

---

## 📋 已生成的迁移脚本总览

### Phase 1: 主键类型升级（可逆）

| 序号 | Revision ID | 文件名 | 目标 | 风险 | 可逆性 |
|------|-------------|--------|------|------|--------|
| Rev 001 | `20251117_reconciliation_pk_bigserial` | `20251117_reconciliation_pk_bigserial.py` | reconciliation_* 表主键 Integer→BIGSERIAL | 🟡 中等 | ✅ 可逆 |
| Rev 002 | `20251117_reconciliation_status_align` | `20251117_reconciliation_status_align.py` | reconciliation_batches.status 枚举对齐 STATE_MACHINE.md | 🟢 低 | ✅ 可逆 |
| Rev 003 | `20251117_analyze_user_fk` | `20251117_analyze_user_fk.py` | 创建分析表，统计用户FK类型不匹配情况 | 🟢 低 | ✅ 可逆 |

### Phase 2: 用户外键类型修复（不可逆）

| 序号 | Revision ID | 文件名 | 目标 | 风险 | 可逆性 |
|------|-------------|--------|------|------|--------|
| Rev 004 | `20251117_fix_ad_spend_user_fk` | `20251117_fix_ad_spend_user_fk.py` | ad_spend_daily 用户FK Integer→UUID | 🔴 高 | ❌ 不可逆 |
| Rev 005 | `20251117_fix_recon_detail_user_fk` | `20251117_fix_recon_detail_user_fk.py` | reconciliation_details 用户FK Integer→UUID | 🔴 高 | ❌ 不可逆 |
| Rev 006 | `20251117_fix_recon_other_user_fk` | `20251117_fix_recon_other_user_fk.py` | reconciliation_adjustments/reports 用户FK Integer→UUID | 🔴 高 | ❌ 不可逆 |

---

## 🎯 迁移策略说明

### Strategy B: 置NULL策略（用户FK修复）

**问题根源**:
- ad_spend_daily 和 reconciliation_* 表的用户FK声明为 Integer
- 但 FK 引用 `users.id`，实际上应该是 `user_profiles.id` (UUID)
- Integer 无法数学映射到 UUID（没有转换关系）

**解决方案**:
1. 将所有用户FK列类型从 Integer 改为 UUID
2. 现有 Integer 值备份到 `*_legacy` 列
3. 所有用户FK值设置为 NULL
4. 重建 FK 约束到 `user_profiles.id`
5. 业务层重新建立用户关联

**影响范围**:
- ✅ ad_spend_daily: `user_id`, `created_by`, `updated_by`
- ✅ reconciliation_details: `reviewed_by`, `resolved_by`
- ✅ reconciliation_adjustments: `approved_by`, `finance_approved_by`
- ✅ reconciliation_reports: `generated_by`

**孤儿率阈值**:
- ≤5%: ✅ PASS，继续执行
- 5-10%: ⚠️ WARNING，业务评估后决定
- \>10%: ❌ FAIL，停止迁移

---

## 🚀 快速执行指南

### 前置条件检查

```bash
# 1. 检查当前 alembic 版本
alembic current

# 2. 查看迁移历史
alembic history

# 3. 确认数据库连接
psql $DATABASE_URL -c "\dt"

# 4. 执行备份（⚠️ 必须！）
pg_dump -Fc $DATABASE_URL > backup_before_migration_$(date +%Y%m%d_%H%M%S).dump
```

### Phase 1 执行（可逆迁移）

```bash
# Step 1: 执行 Rev 001（主键升级）
alembic upgrade 20251117_reconciliation_pk_bigserial

# Gate #1 验证
psql $DATABASE_URL -f backend/validation_scripts/gate1_verify.sql

# Step 2: 执行 Rev 002（status枚举对齐）
alembic upgrade 20251117_reconciliation_status_align

# Gate #2 验证
psql $DATABASE_URL -f backend/validation_scripts/gate2_verify_status.sql

# Step 3: 执行 Rev 003（分析用户FK）
alembic upgrade 20251117_analyze_user_fk

# Gate #3 决策（查看分析结果）
psql $DATABASE_URL -c "SELECT * FROM temp_user_id_fk_analysis ORDER BY table_name, is_orphan DESC;"

# 统计孤儿率
psql $DATABASE_URL -c "
SELECT
    table_name,
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE is_orphan = true) as orphan_count,
    ROUND(COUNT(*) FILTER (WHERE is_orphan = true)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 2) as orphan_rate_percent
FROM temp_user_id_fk_analysis
GROUP BY table_name;
"
```

**决策点 Gate #3**:
- 如果孤儿率 ≤5%: 继续执行 Phase 2
- 如果孤儿率 5-10%: 业务评估，确认可接受后继续
- 如果孤儿率 >10%: 停止迁移，制定映射方案或数据清洗方案

### Phase 2 执行（不可逆迁移，⚠️ 谨慎！）

```bash
# ⚠️ 警告: Phase 2 不可通过 alembic downgrade 回退！
# ⚠️ 确认已完成备份后再执行！

# Step 4: 执行 Rev 004（ad_spend_daily用户FK修复）
alembic upgrade 20251117_fix_ad_spend_user_fk

# Step 5: 执行 Rev 005（reconciliation_details用户FK修复）
alembic upgrade 20251117_fix_recon_detail_user_fk

# Step 6: 执行 Rev 006（其他reconciliation表用户FK修复）
alembic upgrade 20251117_fix_recon_other_user_fk

# Gate #4 验证（所有用户FK修复完成）
psql $DATABASE_URL -f backend/validation_scripts/gate4_verify_user_fk.sql
```

### 一键执行（仅限 Dev/Test 环境）

```bash
# ⚠️ 仅在 Dev/Test 环境使用！生产环境必须逐步执行并验证

# 执行所有迁移
alembic upgrade head

# 执行所有验证
psql $DATABASE_URL -f backend/validation_scripts/gate1_verify.sql
psql $DATABASE_URL -f backend/validation_scripts/gate2_verify_status.sql
psql $DATABASE_URL -f backend/validation_scripts/gate4_verify_user_fk.sql

# 查看分析结果
psql $DATABASE_URL -c "SELECT * FROM temp_user_id_fk_analysis LIMIT 20;"
```

---

## 🔄 回退策略

### Phase 1 回退（Rev 001-003）

```bash
# 方式1: 使用 alembic downgrade（推荐）
alembic downgrade 20251115_add_reconciliation_indexes  # 回退到Rev 001之前

# 方式2: 逐个回退
alembic downgrade -1  # 回退一个版本
alembic downgrade -1  # 再回退一个版本
```

### Phase 2 回退（Rev 004-006）

**⚠️ 不支持 alembic downgrade！**

**唯一回退方式**: 从备份恢复

```bash
# 方式1: 全库恢复（最安全）
pg_restore -d $DATABASE_URL -c backup_before_migration_YYYYMMDD_HHMMSS.dump

# 方式2: 仅恢复受影响的表（需DBA操作）
pg_restore -d $DATABASE_URL -t ad_spend_daily backup_before_migration_YYYYMMDD_HHMMSS.dump
pg_restore -d $DATABASE_URL -t reconciliation_details backup_before_migration_YYYYMMDD_HHMMSS.dump
pg_restore -d $DATABASE_URL -t reconciliation_adjustments backup_before_migration_YYYYMMDD_HHMMSS.dump
pg_restore -d $DATABASE_URL -t reconciliation_reports backup_before_migration_YYYYMMDD_HHMMSS.dump

# 方式3: 手动回退（不推荐，仅紧急情况）
# 参考 MIGRATION_EXECUTION_GUIDE.md §6.3
```

---

## 📊 验证脚本说明

| 验证脚本 | 用途 | 执行时机 |
|---------|------|---------|
| `gate1_verify.sql` | 验证主键类型升级（BIGSERIAL） | Rev 001 执行后 |
| `gate2_verify_status.sql` | 验证 status 枚举对齐 | Rev 002 执行后 |
| `gate4_verify_user_fk.sql` | 验证用户FK类型修复（UUID） | Rev 004-006 全部执行后 |

**Gate #3** 不需要独立脚本，直接查询 `temp_user_id_fk_analysis` 表即可。

---

## ⚠️ 重要注意事项

### 1. 备份要求

- **必须**: 执行 Phase 2 前必须完成全库备份
- **推荐**: 每个 Phase 执行前都备份一次
- **保留期**: 备份至少保留 7 天，确认无问题后删除

### 2. 环境差异

**Dev/Test 环境**:
- ✅ 可以使用一键执行
- ✅ 可以直接执行 Phase 2（不可逆迁移）
- ✅ 数据损失影响较小

**Production 环境**:
- ❌ 禁止一键执行，必须逐步验证
- ⚠️ Phase 2 需要业务方签字确认
- ⚠️ 建议使用影子表策略（参考 MIGRATION_EXECUTION_GUIDE.md）
- ⚠️ 必须在维护窗口期执行

### 3. 业务影响

**数据丢失**:
- 所有用户FK值将被置NULL
- 审核/处理/生成记录的用户信息丢失
- legacy 列保留原值，但无法直接恢复

**业务功能影响**:
- 新记录必须填充正确的 UUID 用户ID
- 历史数据的用户关联需要业务层重建
- 审计日志可能需要从 `audit_logs` 表恢复

### 4. 后续清理

**7天观察期后**:

```sql
-- 删除所有 legacy 备份列
ALTER TABLE ad_spend_daily DROP COLUMN user_id_legacy;
ALTER TABLE ad_spend_daily DROP COLUMN created_by_legacy;
ALTER TABLE ad_spend_daily DROP COLUMN updated_by_legacy;

ALTER TABLE reconciliation_details DROP COLUMN reviewed_by_legacy;
ALTER TABLE reconciliation_details DROP COLUMN resolved_by_legacy;

ALTER TABLE reconciliation_adjustments DROP COLUMN approved_by_legacy;
ALTER TABLE reconciliation_adjustments DROP COLUMN finance_approved_by_legacy;

ALTER TABLE reconciliation_reports DROP COLUMN generated_by_legacy;

-- 删除临时分析表
DROP TABLE temp_user_id_fk_analysis;

-- 删除 status_legacy 列
ALTER TABLE reconciliation_batches DROP COLUMN status_legacy;
```

---

## 📞 问题排查

### 常见问题

**Q1: alembic upgrade 报错 "constraint does not exist"**
A: FK约束名可能与数据库实际名称不一致，需要手动调整脚本中的约束名。

```sql
-- 查询实际约束名
SELECT conname FROM pg_constraint WHERE conrelid = 'ad_spend_daily'::regclass;
```

**Q2: Gate #3 孤儿率 >10%，如何处理？**
A: 有以下选项：
1. 停止迁移，制定 Integer→UUID 映射方案（需要额外的映射表）
2. 业务评估后接受数据丢失，继续执行（需业务方签字）
3. 数据清洗，删除无效记录后重试

**Q3: 如何恢复用户关联？**
A: 可以从以下来源恢复：
1. `*_legacy` 列保留的 Integer 值（如果有映射关系）
2. `audit_logs` 表的操作记录
3. 应用日志中的用户操作记录

**Q4: Windows 环境 psql 命令无法识别 $DATABASE_URL**
A: 使用 PowerShell 变量：

```powershell
$env:DATABASE_URL = "postgresql://user:pass@host:5432/dbname"
psql $env:DATABASE_URL -f backend\validation_scripts\gate1_verify.sql
```

---

## 📚 相关文档

- **完整执行指南**: `MIGRATION_EXECUTION_GUIDE.md`
- **数据库迁移计划**: `DATABASE_SCHEMA_MIGRATION_PLAN.md`
- **数据结构SoT**: `docs/core/DATA_SCHEMA.md`
- **状态机SoT**: `docs/core/STATE_MACHINE.md`

---

## ✅ 执行检查清单

**执行前**:
- [ ] 已阅读 MIGRATION_EXECUTION_GUIDE.md
- [ ] 已完成数据库备份
- [ ] 已确认当前 alembic 版本
- [ ] 已确认无正在运行的长事务
- [ ] 已获得业务方确认（生产环境）

**Phase 1 执行后**:
- [ ] Gate #1 验证通过（主键类型）
- [ ] Gate #2 验证通过（status枚举）
- [ ] Gate #3 孤儿率在可接受范围内

**Phase 2 执行后**:
- [ ] Gate #4 验证通过（用户FK类型）
- [ ] 所有 FK 约束指向 user_profiles.id
- [ ] legacy 列存在且包含原值
- [ ] 业务层已实现用户关联重建逻辑

**清理**:
- [ ] 观察期 7 天后删除 legacy 列
- [ ] 删除临时分析表 temp_user_id_fk_analysis
- [ ] 归档备份文件

---

**最后更新**: 2025-11-17
**维护团队**: 数据库迁移团队
**审核状态**: ✅ 已生成，待执行验证
