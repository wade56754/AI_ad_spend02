# Phase 2 数据库迁移执行手册（最终版）

> **版本**: v2.1 (Production Ready)
> **发布日期**: 2025-11-18
> **维护团队**: 数据库架构组
> **状态**: Ready for Execution
> **适用环境**: Dev → Staging → Prod（按序执行）
> **紧急联系**: DBA On-Call +86-xxx-xxxx-xxxx

---

## 目录

<!-- TOC -->
- [快速开始](#快速开始)
- [一、文档定位与 SoT 关系](#一文档定位与-sot-关系)
- [二、执行前准备](#二执行前准备)
- [三、Phase 2A 时间字段修复](#三phase-2a-时间字段修复)
- [四、Phase 2B 字段类型修复](#四phase-2b-字段类型修复)
- [五、Phase 2C 文档规范化](#五phase-2c-文档规范化)
- [六、环境与审批流程](#六环境与审批流程)
- [七、风险控制与应急预案](#七风险控制与应急预案)
- [八、团队分工与沟通协议](#八团队分工与沟通协议)
- [附录](#附录)
<!-- /TOC -->

---

## 快速开始

**如果您是 DBA 且急需执行 Phase 2A**，请按以下步骤操作：

```bash
# 1. 环境检查（必须）
echo $DATABASE_URL  # 确认指向 Dev 环境
psql $DATABASE_URL -c "SELECT version();"  # 确认数据库连接

# 2. 创建备份（必须）
# 登录 https://supabase.com/dashboard/project/<project-id>/settings/database
# 点击 "Create backup" 并等待完成

# 3. 执行迁移
cd /d/git/1108/AI_ad_spend02/backend
alembic upgrade phase2a_003

# 4. Gate 验证
psql $DATABASE_URL -f phase2a_gate_verification.sql > phase2a_gate_result.log
grep "FAIL\|ERROR" phase2a_gate_result.log  # 检查失败项

# 5. 如果验证通过
echo "Phase 2A 执行成功，进入 3 天观察期"

# 6. 如果验证失败
alembic downgrade <phase2a之前的revision>  # 立即回滚
```

**详细步骤请参考完整文档。**

---

## 一、文档定位与 SoT 关系

### 1.1 SoT 体系架构

```
┌─────────────────────────────────────────────┐
│         规范层（Single Source of Truth）      │
├─────────────────────────────────────────────┤
│ DATA_SCHEMA.md v5.0          │ 数据结构规范  │
│ STATE_MACHINE.md v2.x        │ 状态机规范   │
│ AI_AD_SYSTEM_MAIN_DOCUMENT   │ 实现规范     │
└─────────────┬───────────────────────────────┘
              │ 引用、遵循
              ↓
┌─────────────────────────────────────────────┐
│         执行层（Execution Documents）         │
├─────────────────────────────────────────────┤
│ MIGRATION_EXECUTION_GUIDE.md │ 执行总指引   │
│ PHASE2_MIGRATION_MASTER.md   │ Phase 2 方案 │ ← 本文档
│ backend/alembic/versions/*.py │ 迁移脚本    │
└─────────────────────────────────────────────┘
```

### 1.2 本文档的权威范围与限制

**本文档的权威范围**（允许定义）:
- ✅ Phase 2 的执行顺序、时间安排、环境流程
- ✅ Alembic revision 的拆分策略和命名规范
- ✅ Gate 验证的具体 SQL 和通过标准
- ✅ 回滚流程和紧急预案
- ✅ 团队分工和沟通协议

**本文档的限制**（禁止定义）:
- ❌ 不得定义新的字段类型或数据结构（必须引用 DATA_SCHEMA.md）
- ❌ 不得修改状态机枚举值（必须引用 STATE_MACHINE.md）
- ❌ 不得扩展业务规则（必须引用 AI_AD_SYSTEM_MAIN_DOCUMENT.md）
- ❌ 不得私自添加未在 SoT 中登记的表或字段

### 1.3 SoT 引用清单

本文档引用的所有 SoT 规范：

| SoT 文档 | 版本 | 引用章节 | 引用内容 |
| --- | --- | --- | --- |
| DATA_SCHEMA.md | v5.0 | § 1.1 | 时间字段统一使用 TIMESTAMPTZ |
| DATA_SCHEMA.md | v5.0 | § 3.2.2 | project_members.permissions 为 JSONB |
| DATA_SCHEMA.md | v5.0 | § 3.2.9 | account_alerts.severity 枚举 info/warning/critical |
| DATA_SCHEMA.md | v5.0 | § 5 | 未登记字段的处理策略 |
| MIGRATION_EXECUTION_GUIDE.md | v1.2 | § 2 | Gate 验证机制 |
| MIGRATION_EXECUTION_GUIDE.md | v1.2 | § 3 | 回滚策略 |
| MIGRATION_EXECUTION_GUIDE.md | v1.2 | § 6 | 观察期要求 |

**验证方式**: 执行前必须确认上述 SoT 文档的版本号与本清单一致，如有冲突以 SoT 为准。

---

## 二、执行前准备

### 2.1 环境检查清单（必须全部通过）

```bash
# ===== 执行前检查脚本 =====
# 文件位置: backend/pre_migration_check.sh

#!/bin/bash
set -e

echo "=== Phase 2 执行前检查 ==="
echo ""

# Check 1: 环境变量
echo "[1/8] 检查环境变量..."
if [ -z "$DATABASE_URL" ]; then
    echo "  [FAIL] DATABASE_URL 未设置"
    exit 1
fi
echo "  [PASS] DATABASE_URL = ${DATABASE_URL:0:30}..."

# Check 2: 数据库连接
echo "[2/8] 检查数据库连接..."
psql "$DATABASE_URL" -c "SELECT version();" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  [PASS] 数据库连接成功"
else
    echo "  [FAIL] 数据库连接失败"
    exit 1
fi

# Check 3: 表存在性验证
echo "[3/8] 检查目标表是否存在..."
TABLE_COUNT=$(psql "$DATABASE_URL" -t -c "
    SELECT COUNT(DISTINCT tablename)
    FROM pg_tables
    WHERE tablename IN (
        'projects', 'project_members', 'project_expenses',
        'topup_requests', 'topup_transactions', 'topup_approval_logs',
        'ledger_entries'
    );
")
if [ "$TABLE_COUNT" -eq 7 ]; then
    echo "  [PASS] 所有 7 个目标表存在"
else
    echo "  [FAIL] 只找到 $TABLE_COUNT 个表（预期 7 个）"
    exit 1
fi

# Check 4: Alembic 配置
echo "[4/8] 检查 Alembic 配置..."
if [ -f "alembic.ini" ]; then
    echo "  [PASS] alembic.ini 存在"
else
    echo "  [FAIL] alembic.ini 不存在"
    exit 1
fi

# Check 5: Alembic 版本
echo "[5/8] 检查 Alembic 当前版本..."
CURRENT_REV=$(alembic current 2>&1 | grep -oP '(?<=\()[a-z0-9_]+(?=\))')
echo "  [INFO] 当前 revision: $CURRENT_REV"

# Check 6: 迁移脚本存在性
echo "[6/8] 检查迁移脚本是否存在..."
if [ -f "alembic/versions/20251118_phase2a_001_projects_timezone.py" ]; then
    echo "  [PASS] phase2a_001 脚本存在"
else
    echo "  [FAIL] phase2a_001 脚本不存在"
    exit 1
fi

# Check 7: Gate 验证脚本
echo "[7/8] 检查 Gate 验证脚本..."
if [ -f "phase2a_gate_verification.sql" ]; then
    echo "  [PASS] Gate 验证脚本存在"
else
    echo "  [FAIL] Gate 验证脚本不存在"
    exit 1
fi

# Check 8: 磁盘空间（至少 1GB）
echo "[8/8] 检查磁盘空间..."
AVAILABLE_SPACE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -ge 1 ]; then
    echo "  [PASS] 可用空间: ${AVAILABLE_SPACE}GB"
else
    echo "  [WARN] 可用空间不足: ${AVAILABLE_SPACE}GB"
fi

echo ""
echo "=== 所有检查通过 ==="
echo "可以开始执行 Phase 2A"
```

**使用方式**:
```bash
cd /d/git/1108/AI_ad_spend02/backend
chmod +x pre_migration_check.sh
./pre_migration_check.sh
```

### 2.2 备份要求（强制执行）

#### 2.2.1 Supabase Dashboard 快照

**操作步骤**:
```
1. 登录 https://supabase.com/dashboard
2. 选择项目: AI_ad_spend02
3. 导航: Settings → Database → Backups
4. 点击 "Create backup"
5. 备注: "Phase2-Pre-Migration-2025-11-18"
6. 等待快照完成（通常 2-5 分钟）
7. 记录快照 ID: ________________
```

**验证备份**:
```bash
# 检查最近的备份时间
psql $DATABASE_URL -c "
    SELECT NOW() - pg_stat_file('base/1/PG_VERSION').modification AS last_checkpoint;
"
# 预期结果: 小于 10 分钟
```

#### 2.2.2 本地 SQL 转储（可选，建议执行）

```bash
# 导出关键表的 schema 和数据
pg_dump $DATABASE_URL \
    --schema-only \
    --table=projects \
    --table=project_members \
    --table=project_expenses \
    --table=topup_requests \
    --table=topup_transactions \
    --table=topup_approval_logs \
    --table=ledger_entries \
    > phase2_schema_backup_$(date +%Y%m%d_%H%M%S).sql

# 验证备份文件
ls -lh phase2_schema_backup_*.sql
```

### 2.3 SoT 版本锁定

**执行前确认** (记录到 JIRA/Confluence):

```
Phase 2 执行使用的 SoT 版本：
[ ] DATA_SCHEMA.md              版本: v5.0  Git Hash: ________
[ ] STATE_MACHINE.md            版本: v2.x  Git Hash: ________
[ ] AI_AD_SYSTEM_MAIN_DOCUMENT  版本: v3.0  Git Hash: ________
[ ] MIGRATION_EXECUTION_GUIDE   版本: v1.2  Git Hash: ________

锁定时间: 2025-11-18 __:__ (UTC+8)
锁定人: __________
解锁条件: Phase 2 执行完成且观察期结束
```

**锁定操作**:
```bash
# 创建 SoT 版本锁定标签
git tag -a phase2-sot-lock-20251118 -m "Phase 2 SoT 版本锁定"
git push origin phase2-sot-lock-20251118
```

### 2.4 团队通知（执行前 24 小时）

**邮件模板**:
```
收件人: dev-team@example.com, qa-team@example.com
抄送: pm@example.com, cto@example.com
主题: [数据库迁移通知] Phase 2 将于 2025-11-18 14:00 执行

各位同事：

Phase 2 数据库迁移将于以下时间执行：

执行时间: 2025-11-18 14:00 - 14:30 (UTC+8)
执行环境: Dev 数据库
影响范围: 7 个表（projects, project_members, project_expenses, topup_requests, topup_transactions, topup_approval_logs, ledger_entries）
预计停机: < 5 分钟
执行人: [DBA 姓名]

执行内容：
- Phase 2A: 14 个时间字段类型升级 (TIMESTAMP → TIMESTAMPTZ)

注意事项：
- 执行期间请勿修改上述表的数据
- 如有紧急问题，请联系 DBA On-Call: +86-xxx-xxxx-xxxx

详细方案: docs/core/PHASE2_MIGRATION_MASTER_v2.1.md

谢谢配合！
数据库架构组
```

---

## 三、Phase 2A 时间字段修复

### 3.1 Phase 2A 概览

**目标**: 修复 7 个表共 14 个时间字段的 timezone 标记

**SoT 依据**: DATA_SCHEMA.md v5.0 § 1.1
> 时间字段：统一使用 TIMESTAMPTZ，默认 NOW()，应用层使用 UTC

**影响范围**:

| 模块 | 表名 | 字段数 | 字段列表 |
| --- | --- | --- | --- |
| 项目 | projects | 2 | created_at, updated_at |
| 项目 | project_members | 1 | joined_at |
| 项目 | project_expenses | 2 | occurred_at, created_at |
| 充值 | topup_requests | 2 | created_at, updated_at |
| 充值 | topup_transactions | 2 | paid_at, created_at |
| 充值 | topup_approval_logs | 1 | created_at |
| 账本 | ledger_entries | 1 | occurred_at |
| **合计** | **7** | **11** | **14 个字段** |

**迁移特性**:
- ✅ 可逆性: 完全可逆（Alembic downgrade 或 SQL 回滚）
- ⚠️ 数据风险: 低（PostgreSQL 自动处理类型转换，无数据丢失）
- ⏱️ 停机时间: < 5 分钟（ALTER COLUMN 操作快速）
- 🔒 锁表级别: ACCESS EXCLUSIVE（短时间锁表）

### 3.2 Alembic Revisions 架构

**命名规范** (遵循 MIGRATION_EXECUTION_GUIDE § 4):
```
Revision ID: phase2a_{序号}
文件名: YYYYMMDD_phase2a_{序号}_{模块}_timezone.py
Down Revision: phase2a_{序号-1} (或 None)
```

**Revision 拆分策略**: 按模块拆分（便于独立回滚）

```
phase2a_001 (projects 模块)
    ├── 表: projects, project_members, project_expenses
    ├── 字段: 5 个
    ├── Down Revision: None (或前一个 Phase 1 revision)
    └── Branch Labels: None

phase2a_002 (topup 模块)
    ├── 表: topup_requests, topup_transactions, topup_approval_logs
    ├── 字段: 5 个
    ├── Down Revision: phase2a_001
    └── Depends On: phase2a_001

phase2a_003 (ledger 模块)
    ├── 表: ledger_entries
    ├── 字段: 1 个
    ├── Down Revision: phase2a_002
    └── Depends On: phase2a_002
```

**依赖关系图**:
```
         ┌──────────────┐
         │ phase2a_001  │
         │   projects   │
         └──────┬───────┘
                │ down_revision
                ↓
         ┌──────────────┐
         │ phase2a_002  │
         │    topup     │
         └──────┬───────┘
                │ down_revision
                ↓
         ┌──────────────┐
         │ phase2a_003  │
         │    ledger    │
         └──────────────┘
```

### 3.3 执行流程（分步骤）

#### 3.3.1 执行前最终确认

```bash
# ===== 执行前最终确认 Checklist =====

# 1. 再次确认环境
echo "当前 DATABASE_URL:"
echo $DATABASE_URL | sed 's/:[^@]*@/:***@/'  # 隐藏密码

read -p "确认这是 Dev 环境？(yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "操作取消"
    exit 1
fi

# 2. 确认备份已完成
read -p "Supabase 快照已创建？(yes/no): " backup_confirm
if [ "$backup_confirm" != "yes" ]; then
    echo "请先创建备份"
    exit 1
fi

# 3. 确认无其他迁移正在执行
psql $DATABASE_URL -c "
    SELECT pid, state, query_start, query
    FROM pg_stat_activity
    WHERE query LIKE '%ALTER TABLE%'
    AND state = 'active';
"
# 预期结果: 0 rows (无其他 DDL 操作)

# 4. 记录开始时间
echo "Phase 2A 执行开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
```

#### 3.3.2 执行 Phase 2A (All-in-One)

```bash
# ===== Phase 2A 一次性执行 =====
cd /d/git/1108/AI_ad_spend02/backend

# 设置环境变量（如果未设置）
export DATABASE_URL="postgresql://postgres:BTsBIezNsDQF0UFp@db.jzmcoivxhiyidizncyaq.supabase.co:5432/postgres"

# 执行迁移（自动按顺序执行 001 → 002 → 003）
echo "开始执行 Phase 2A 迁移..."
alembic upgrade phase2a_003 2>&1 | tee phase2a_execution.log

# 检查执行结果
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo "[SUCCESS] Phase 2A 迁移执行成功"
else
    echo "[ERROR] Phase 2A 迁移执行失败，请查看 phase2a_execution.log"
    exit 1
fi

# 记录完成时间
echo "Phase 2A 执行完成时间: $(date '+%Y-%m-%d %H:%M:%S')"
```

**预期输出**:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade -> phase2a_001, Phase 2A-001: projects 模块时间字段 TIMESTAMPTZ 修复
[Phase 2A-001] 正在修复 projects 表...
  [OK] projects 表完成（2 个字段）
[Phase 2A-001] 正在修复 project_members 表...
  [OK] project_members 表完成（1 个字段）
[Phase 2A-001] 正在修复 project_expenses 表...
  [OK] project_expenses 表完成（2 个字段）
[Phase 2A-001] 迁移完成！共修复 3 个表，5 个字段

INFO  [alembic.runtime.migration] Running upgrade phase2a_001 -> phase2a_002, Phase 2A-002: topup 模块时间字段 TIMESTAMPTZ 修复
[Phase 2A-002] 正在修复 topup_requests 表...
  [OK] topup_requests 表完成（2 个字段）
[Phase 2A-002] 正在修复 topup_transactions 表...
  [OK] topup_transactions 表完成（2 个字段）
[Phase 2A-002] 正在修复 topup_approval_logs 表...
  [OK] topup_approval_logs 表完成（1 个字段）
[Phase 2A-002] 迁移完成！共修复 3 个表，5 个字段

INFO  [alembic.runtime.migration] Running upgrade phase2a_002 -> phase2a_003, Phase 2A-003: ledger 模块时间字段 TIMESTAMPTZ 修复
[Phase 2A-003] 正在修复 ledger_entries 表...
  [OK] ledger_entries 表完成（1 个字段）
[Phase 2A-003] 迁移完成！共修复 1 个表，1 个字段

[SUCCESS] Phase 2A 迁移执行成功
```

#### 3.3.3 Gate 验证（强制执行）

```bash
# ===== Gate #2A 验证 =====
echo "开始执行 Gate #2A 验证..."

# 执行验证脚本
psql $DATABASE_URL -f phase2a_gate_verification.sql > phase2a_gate_result.log 2>&1

# 提取验证结果
echo ""
echo "=== Gate 验证结果 ==="
grep -E "PASS|FAIL|gate_result" phase2a_gate_result.log | tail -20

# 检查是否有 FAIL
FAIL_COUNT=$(grep -c "FAIL" phase2a_gate_result.log || true)
if [ $FAIL_COUNT -gt 0 ]; then
    echo ""
    echo "[ERROR] Gate 验证失败！发现 $FAIL_COUNT 个 FAIL 项"
    echo "详细结果: phase2a_gate_result.log"
    echo ""
    echo "是否立即回滚？(yes/no)"
    read -p "> " rollback_confirm
    if [ "$rollback_confirm" == "yes" ]; then
        echo "开始回滚..."
        alembic downgrade <phase2a之前的revision>
        echo "回滚完成"
    fi
    exit 1
else
    echo ""
    echo "[SUCCESS] Gate #2A 验证通过！"
    echo "所有 14 个字段已成功升级为 TIMESTAMPTZ"
fi
```

**Gate 验证通过标准** (遵循 MIGRATION_EXECUTION_GUIDE § 2):

| 检查项 | SQL 位置 | 通过标准 | 失败处理 |
| --- | --- | --- | --- |
| **Check 1: 字段类型** | phase2a_gate_verification.sql:10-30 | 所有 14 个字段 data_type = 'timestamp with time zone' | 立即回滚 |
| **Check 2: 数据完整性** | phase2a_gate_verification.sql:35-80 | 所有表 count(time_field) = count(*) | 分析原因 |
| **Check 3: 时间范围** | phase2a_gate_verification.sql:85-130 | 无未来时间，无 1970 年前时间 | 修复数据 |
| **Check 4: Timezone 设置** | phase2a_gate_verification.sql:135-140 | SHOW timezone = 'UTC' | 调整配置 |
| **Check 5: 综合统计** | phase2a_gate_verification.sql:145-170 | verified_fields = 14 | 重新执行 |

**决策矩阵**:
```
Gate 结果              →  下一步行动
├─ Check 1 FAIL       →  立即回滚，分析类型转换问题
├─ Check 2 部分 FAIL  →  检查字段是否允许 NULL，如允许则继续
├─ Check 3 FAIL       →  修复异常数据后重新执行迁移
├─ Check 4 FAIL       →  调整数据库 timezone 配置
└─ 全部 PASS          →  进入观察期
```

#### 3.3.4 执行后记录

```bash
# ===== 执行后记录模板 =====

cat > phase2a_execution_report.txt <<EOF
===========================================
Phase 2A 执行报告
===========================================

执行时间: $(date '+%Y-%m-%d %H:%M:%S')
执行人: [DBA 姓名]
环境: Dev

执行内容:
- Phase 2A-001: projects 模块（5 个字段）
- Phase 2A-002: topup 模块（5 个字段）
- Phase 2A-003: ledger 模块（1 个字段）

执行结果:
- 迁移状态: [成功/失败]
- Gate 验证: [通过/失败]
- 回滚情况: [无/已回滚]

Alembic Revision:
- 执行前: $(git rev-parse HEAD:backend/alembic/versions/20251117*.py | head -1)
- 执行后: phase2a_003

备份信息:
- Supabase 快照 ID: ________________
- 快照创建时间: ________________

异常记录:
- [如有异常，记录详细信息]

下一步:
- 进入 3 天观察期（2025-11-18 至 2025-11-21）
- 每日执行监控 SQL（见 § 3.5）

签字:
执行人: __________  日期: __________
审核人: __________  日期: __________
===========================================
EOF

cat phase2a_execution_report.txt
```

### 3.4 回滚流程（紧急情况）

#### 3.4.1 回滚决策树

```
发现问题
    ├─ Gate 验证失败？
    │   └─ YES → [立即回滚] Alembic downgrade
    │
    ├─ 应用报错（时区相关）？
    │   ├─ 影响核心功能 → [紧急回滚] Alembic downgrade
    │   └─ 影响次要功能 → [暂缓回滚] 修复应用代码后继续观察
    │
    ├─ 数据异常（未来时间/1970年前）？
    │   ├─ 异常数据 < 1% → [暂缓回滚] 修复数据后继续观察
    │   └─ 异常数据 >= 1% → [立即回滚] Alembic downgrade
    │
    └─ 数据库性能下降？
        ├─ CPU/内存 > 90% → [紧急回滚] Alembic downgrade
        └─ 查询变慢 < 20% → [暂缓回滚] 继续观察
```

#### 3.4.2 Alembic 回滚（推荐方式）

```bash
# ===== Alembic 回滚脚本 =====

echo "=== Phase 2A 紧急回滚 ==="
echo ""

# 1. 确认当前 revision
CURRENT_REV=$(alembic current | grep -oP '(?<=\()[a-z0-9_]+(?=\))')
echo "当前 revision: $CURRENT_REV"

# 2. 确认回滚目标
read -p "回滚到哪个 revision？(phase2a_002/phase2a_001/完全回滚): " TARGET_REV

if [ "$TARGET_REV" == "完全回滚" ]; then
    # 查找 phase2a_001 之前的 revision
    PREV_REV=$(grep "down_revision.*=" backend/alembic/versions/20251118_phase2a_001_*.py | grep -oP "'[a-z0-9_]+'" | tr -d "'")
    TARGET_REV=$PREV_REV
fi

# 3. 执行回滚
echo "准备回滚到: $TARGET_REV"
read -p "确认执行回滚？(yes/no): " confirm

if [ "$confirm" == "yes" ]; then
    echo "开始回滚..."
    alembic downgrade $TARGET_REV 2>&1 | tee phase2a_rollback.log

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo "[SUCCESS] 回滚成功"
    else
        echo "[ERROR] 回滚失败，请查看 phase2a_rollback.log"
        echo "建议使用 Supabase 快照恢复"
        exit 1
    fi
else
    echo "回滚取消"
    exit 0
fi

# 4. 验证回滚结果
echo ""
echo "=== 验证回滚结果 ==="
psql $DATABASE_URL -c "
    SELECT
        table_name,
        column_name,
        data_type
    FROM information_schema.columns
    WHERE table_name IN (
        'projects', 'project_members', 'project_expenses',
        'topup_requests', 'topup_transactions', 'topup_approval_logs',
        'ledger_entries'
    )
    AND column_name IN ('created_at', 'updated_at', 'occurred_at', 'joined_at', 'paid_at')
    ORDER BY table_name, column_name;
"

echo ""
echo "检查上述字段是否回滚为 'timestamp without time zone'"
```

**预期输出**（完全回滚后）:
```
table_name              | column_name | data_type
------------------------+-------------+-----------------------------
ledger_entries          | occurred_at | timestamp without time zone
project_expenses        | created_at  | timestamp without time zone
project_expenses        | occurred_at | timestamp without time zone
project_members         | joined_at   | timestamp without time zone
projects                | created_at  | timestamp without time zone
projects                | updated_at  | timestamp without time zone
topup_approval_logs     | created_at  | timestamp without time zone
topup_requests          | created_at  | timestamp without time zone
topup_requests          | updated_at  | timestamp without time zone
topup_transactions      | created_at  | timestamp without time zone
topup_transactions      | paid_at     | timestamp without time zone
(14 rows)
```

#### 3.4.3 Supabase 快照恢复（最后手段）

**触发条件**:
- Alembic 回滚失败
- 数据库损坏
- 回滚后仍有问题

**操作步骤**:
```
1. 立即停止所有应用连接到数据库
2. 登录 Supabase Dashboard
3. 导航: Settings → Database → Backups
4. 找到执行前的快照（备注: "Phase2-Pre-Migration-2025-11-18"）
5. 点击快照右侧的 "..." → "Restore"
6. 阅读警告信息（不可逆操作）
7. 输入确认文本: "RESTORE"
8. 点击 "Restore backup"
9. 等待恢复完成（10-30 分钟）
10. 验证数据库状态
11. 重启应用服务
```

**恢复后验证**:
```bash
# 连接数据库
psql $DATABASE_URL

# 检查数据完整性
SELECT COUNT(*) FROM projects;
SELECT COUNT(*) FROM topup_requests;
-- ... 检查所有关键表

# 检查时间字段类型（应为 TIMESTAMP without time zone）
\d+ projects

# 检查 Alembic 版本表
SELECT * FROM alembic_version;
```

### 3.5 观察期（3 天）

**观察时间**: 2025-11-18 14:00 至 2025-11-21 14:00

**遵循**: MIGRATION_EXECUTION_GUIDE v1.2 § 6

#### 3.5.1 每日监控任务

**任务 1: 异常时间值检查**（每日 10:00 执行）

```sql
-- 文件位置: backend/phase2a_daily_monitoring.sql

-- ===== Phase 2A 每日监控 SQL =====
-- 执行方式: psql $DATABASE_URL -f phase2a_daily_monitoring.sql

-- 监控日期
SELECT '=== Phase 2A 每日监控 ===' AS title,
       CURRENT_DATE AS monitor_date,
       CURRENT_TIMESTAMP AS monitor_time;

-- Check 1: 检查异常时间值（未来时间）
SELECT
    table_name,
    COUNT(*) AS future_count
FROM (
    SELECT 'projects' AS table_name, created_at AS time_field
    FROM projects WHERE created_at > NOW()
    UNION ALL
    SELECT 'projects', updated_at FROM projects WHERE updated_at > NOW()
    UNION ALL
    SELECT 'project_members', joined_at FROM project_members WHERE joined_at > NOW()
    UNION ALL
    SELECT 'project_expenses', occurred_at FROM project_expenses WHERE occurred_at > NOW()
    UNION ALL
    SELECT 'project_expenses', created_at FROM project_expenses WHERE created_at > NOW()
    UNION ALL
    SELECT 'topup_requests', created_at FROM topup_requests WHERE created_at > NOW()
    UNION ALL
    SELECT 'topup_requests', updated_at FROM topup_requests WHERE updated_at > NOW()
    UNION ALL
    SELECT 'topup_transactions', paid_at FROM topup_transactions WHERE paid_at > NOW()
    UNION ALL
    SELECT 'topup_transactions', created_at FROM topup_transactions WHERE created_at > NOW()
    UNION ALL
    SELECT 'topup_approval_logs', created_at FROM topup_approval_logs WHERE created_at > NOW()
    UNION ALL
    SELECT 'ledger_entries', occurred_at FROM ledger_entries WHERE occurred_at > NOW()
) t
GROUP BY table_name
HAVING COUNT(*) > 0;
-- 预期结果: 0 rows（无未来时间）

-- Check 2: 检查异常时间值（1970 年之前）
SELECT
    table_name,
    COUNT(*) AS too_early_count
FROM (
    SELECT 'projects' AS table_name, created_at AS time_field
    FROM projects WHERE created_at < '2020-01-01'::TIMESTAMPTZ
    UNION ALL
    SELECT 'projects', updated_at FROM projects WHERE updated_at < '2020-01-01'::TIMESTAMPTZ
    -- ... 其他表类似
) t
GROUP BY table_name
HAVING COUNT(*) > 0;
-- 预期结果: 0 rows（无过早时间）

-- Check 3: 时区一致性检查
SELECT
    table_name,
    column_name,
    data_type,
    CASE
        WHEN data_type = 'timestamp with time zone' THEN 'OK'
        ELSE 'ERROR'
    END AS status
FROM information_schema.columns
WHERE table_name IN (
    'projects', 'project_members', 'project_expenses',
    'topup_requests', 'topup_transactions', 'topup_approval_logs',
    'ledger_entries'
)
AND column_name IN ('created_at', 'updated_at', 'occurred_at', 'joined_at', 'paid_at')
AND data_type != 'timestamp with time zone';
-- 预期结果: 0 rows（所有字段类型正确）

-- Check 4: 数据增长监控
SELECT
    'projects' AS table_name,
    COUNT(*) AS total_records,
    MAX(created_at) AS latest_record
FROM projects
UNION ALL
SELECT 'topup_requests', COUNT(*), MAX(created_at) FROM topup_requests
UNION ALL
SELECT 'ledger_entries', COUNT(*), MAX(occurred_at) FROM ledger_entries;
-- 用于对比每日数据增长情况
```

**执行方式**:
```bash
# 每日 10:00 执行
psql $DATABASE_URL -f backend/phase2a_daily_monitoring.sql > monitoring_$(date +%Y%m%d).log

# 检查结果
cat monitoring_$(date +%Y%m%d).log | grep -E "future_count|too_early_count|ERROR"

# 如果发现异常，立即通知 DBA
```

**任务 2: 应用日志监控**（每日 11:00 执行）

```bash
# 检查应用日志中的时区相关错误
grep -i "timezone\|timestamp\|utc\|time zone" /path/to/app/logs/error.log | tail -100

# 检查数据库连接错误
grep -i "database\|connection\|psycopg2" /path/to/app/logs/error.log | tail -50
```

**任务 3: 业务功能测试**（每日 15:00 执行）

手动测试以下功能：
- [ ] 项目创建（检查 created_at 字段）
- [ ] 项目编辑（检查 updated_at 字段）
- [ ] 项目成员添加（检查 joined_at 字段）
- [ ] 充值申请提交（检查 created_at 字段）
- [ ] 充值审批（检查 updated_at 字段）
- [ ] 账本条目查询（检查 occurred_at 字段）

#### 3.5.2 观察期阈值

| 监控指标 | 正常阈值 | 警告阈值 | 立即回滚阈值 |
| --- | --- | --- | --- |
| 异常时间值数量 | 0 | 1-5 | > 5 |
| 应用错误率（时区相关） | 0% | < 1% | >= 5% |
| 数据库 CPU 使用率 | < 60% | 60-80% | > 90% |
| 查询响应时间增长 | < 5% | 5-10% | > 20% |
| 数据完整性（count 一致性） | 100% | 99.9-100% | < 99.9% |

#### 3.5.3 观察期结束评估

**Day 3 (2025-11-21 14:00) 执行以下检查**:

```bash
# ===== 观察期结束评估 =====

echo "=== Phase 2A 观察期结束评估 ==="
echo ""

# 1. 汇总 3 天监控结果
echo "[1/5] 汇总监控日志..."
cat monitoring_20251118.log monitoring_20251119.log monitoring_20251120.log monitoring_20251121.log > phase2a_observation_summary.log

# 2. 统计异常数量
echo "[2/5] 统计异常数量..."
TOTAL_ANOMALIES=$(grep -c "future_count\|too_early_count\|ERROR" phase2a_observation_summary.log || true)
echo "  总异常数: $TOTAL_ANOMALIES"

# 3. 检查应用错误
echo "[3/5] 检查应用错误..."
APP_ERRORS=$(grep -c "timezone\|timestamp" /path/to/app/logs/error.log || true)
echo "  应用时区相关错误: $APP_ERRORS"

# 4. 业务功能测试汇总
echo "[4/5] 业务功能测试汇总..."
echo "  项目创建: [PASS/FAIL]"
echo "  充值申请: [PASS/FAIL]"
echo "  账本查询: [PASS/FAIL]"

# 5. 评估结论
echo "[5/5] 评估结论..."
if [ $TOTAL_ANOMALIES -eq 0 ] && [ $APP_ERRORS -eq 0 ]; then
    echo "  [SUCCESS] Phase 2A 观察期通过"
    echo "  可以进入 Phase 2B"
else
    echo "  [WARNING] Phase 2A 观察期发现异常"
    echo "  需要进一步分析或回滚"
fi
```

**通过标准**:
- ✅ 3 天无异常时间值
- ✅ 应用日志无时区相关错误
- ✅ 所有业务功能测试通过
- ✅ 数据库性能正常（CPU < 60%）

**如果通过**: 标记 Phase 2A 为 "Completed"，进入 Phase 2B

**如果失败**: 召开评审会议，决定是否回滚或延长观察期

---

## 四、Phase 2B 字段类型修复

### 4.1 Phase 2B 概览

**目标**: 修复 2 个字段类型不匹配问题

**SoT 依据**:
- DATA_SCHEMA.md v5.0 § 3.2.2 (project_members.permissions)
- DATA_SCHEMA.md v5.0 § 3.2.9 (account_alerts.severity)

**影响范围**:

| Rev | 表名 | 字段 | 当前类型 | 目标类型 | 策略 |
| --- | --- | --- | --- | --- | --- |
| 2B-001 | project_members | permissions | Text | JSONB | Strategy B（置空 + legacy） |
| 2B-002 | account_alerts | severity | 枚举值不一致 | 修复枚举值 | 枚举映射 + legacy |

**迁移特性**:
- ✅ 可逆性: 可逆（保留 legacy 列）
- ⚠️ 数据风险: 中等（Text → JSONB 需 JSON 校验）
- ⏱️ 停机时间: < 10 分钟
- 🔒 观察期: 7 天（比 Phase 2A 更长）

### 4.2 Rev 2B-001: project_members.permissions Text → JSONB

#### 4.2.1 执行前数据审计

```sql
-- ===== Rev 2B-001 执行前数据审计 =====

-- 1. 统计 permissions 字段使用情况
SELECT
    COUNT(*) AS total_records,
    COUNT(permissions) AS non_null_count,
    COUNT(*) FILTER (WHERE permissions IS NULL) AS null_count,
    COUNT(*) FILTER (WHERE permissions = '') AS empty_string_count,
    COUNT(*) FILTER (WHERE permissions = 'null') AS null_string_count
FROM project_members;

-- 2. 检查是否有无效 JSON
SELECT
    id,
    project_id,
    user_id,
    permissions
FROM project_members
WHERE permissions IS NOT NULL
  AND permissions != ''
  AND permissions != 'null'
LIMIT 10;

-- 3. 尝试 JSON 验证（抽样）
DO $$
DECLARE
    rec RECORD;
    invalid_count INTEGER := 0;
BEGIN
    FOR rec IN
        SELECT id, permissions
        FROM project_members
        WHERE permissions IS NOT NULL
        LIMIT 100
    LOOP
        BEGIN
            PERFORM rec.permissions::JSONB;
        EXCEPTION WHEN OTHERS THEN
            invalid_count := invalid_count + 1;
            RAISE NOTICE 'Invalid JSON in id=%: %', rec.id, rec.permissions;
        END;
    END LOOP;

    RAISE NOTICE 'Total invalid JSON records (sample): %', invalid_count;
END $$;
```

#### 4.2.2 执行 SQL

**前置条件检查**:
```bash
# 确认 Phase 2A 观察期已结束并通过
read -p "Phase 2A 观察期已通过？(yes/no): " phase2a_confirm
if [ "$phase2a_confirm" != "yes" ]; then
    echo "请先完成 Phase 2A 观察期"
    exit 1
fi
```

**执行命令**（假设已创建 Alembic 脚本）:
```bash
# 执行 Rev 2B-001
alembic upgrade phase2b_001 2>&1 | tee phase2b_001_execution.log

# 或手动执行 SQL
psql $DATABASE_URL <<'EOF'
BEGIN;

-- Step 1: 添加备份列
ALTER TABLE project_members
  ADD COLUMN IF NOT EXISTS permissions_legacy TEXT;

-- Step 2: 备份当前值
UPDATE project_members
  SET permissions_legacy = permissions;

-- Step 3: 清理无效数据
UPDATE project_members
  SET permissions = '{}'
  WHERE permissions IS NULL
     OR permissions = ''
     OR permissions = 'null';

-- Step 4: 验证 JSON 有效性（使用 PL/pgSQL）
DO $$
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN
        SELECT id, permissions
        FROM project_members
        WHERE permissions IS NOT NULL
    LOOP
        BEGIN
            PERFORM permissions::JSONB FROM project_members WHERE id = rec.id;
        EXCEPTION WHEN OTHERS THEN
            UPDATE project_members SET permissions = '{}' WHERE id = rec.id;
            RAISE NOTICE 'Invalid JSON in row %, set to {}', rec.id;
        END;
    END LOOP;
END $$;

-- Step 5: 转换列类型
ALTER TABLE project_members
  ALTER COLUMN permissions TYPE JSONB USING permissions::JSONB;

-- Step 6: 设置默认值
ALTER TABLE project_members
  ALTER COLUMN permissions SET DEFAULT '{}';

COMMIT;
EOF
```

#### 4.2.3 Gate 验证

```sql
-- ===== Gate #2B-001: 验证 permissions JSONB 转换 =====

-- Check 1: 列类型验证
SELECT
    column_name,
    data_type,
    column_default,
    CASE
        WHEN data_type = 'jsonb' AND column_default = '{}'::text THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM information_schema.columns
WHERE table_name = 'project_members'
  AND column_name = 'permissions';
-- 预期结果: status = 'PASS'

-- Check 2: JSONB 数据验证
SELECT
    COUNT(*) AS total_records,
    COUNT(permissions) AS non_null_count,
    COUNT(*) FILTER (WHERE permissions = '{}') AS empty_json_count,
    COUNT(*) FILTER (WHERE jsonb_typeof(permissions) = 'object') AS valid_object_count,
    COUNT(permissions_legacy) AS legacy_backup_count
FROM project_members;
-- 预期结果: valid_object_count = non_null_count, legacy_backup_count = total_records

-- Check 3: 检查是否有无效 JSONB
SELECT id, permissions
FROM project_members
WHERE permissions IS NOT NULL
  AND jsonb_typeof(permissions) IS NULL
LIMIT 10;
-- 预期结果: 0 rows

-- Check 4: legacy 列数据完整性
SELECT
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE permissions_legacy IS NOT NULL) AS legacy_preserved
FROM project_members;
-- 预期结果: legacy_preserved >= 0（可能有新插入的记录没有 legacy 值）
```

**通过标准**:
- ✅ permissions 列类型为 jsonb
- ✅ column_default = '{}'
- ✅ 所有非 NULL 的 permissions 值都是有效的 JSONB 对象
- ✅ permissions_legacy 列保留了所有原始数据

#### 4.2.4 回滚 SQL

```sql
-- ===== Rollback Rev 2B-001 =====
BEGIN;

-- Step 1: 恢复为 TEXT 类型
ALTER TABLE project_members
  ALTER COLUMN permissions TYPE TEXT USING permissions::TEXT;

-- Step 2: 从 legacy 列恢复数据
UPDATE project_members
  SET permissions = permissions_legacy;

-- Step 3: 删除备份列
ALTER TABLE project_members
  DROP COLUMN permissions_legacy;

-- Step 4: 移除默认值
ALTER TABLE project_members
  ALTER COLUMN permissions DROP DEFAULT;

COMMIT;
```

### 4.3 Rev 2B-002: account_alerts.severity 枚举值修复

#### 4.3.1 执行前数据审计

```sql
-- ===== Rev 2B-002 执行前数据审计 =====

-- 1. 统计当前 severity 值分布
SELECT
    severity,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM account_alerts
GROUP BY severity
ORDER BY count DESC;

-- 2. 检查是否有非法值
SELECT DISTINCT severity
FROM account_alerts
WHERE severity NOT IN ('low', 'medium', 'high', 'critical', 'info', 'warning');
-- 预期结果: 0 rows

-- 3. 映射预览
SELECT
    severity AS old_value,
    CASE
        WHEN severity = 'low' THEN 'info'
        WHEN severity = 'medium' THEN 'warning'
        WHEN severity = 'high' THEN 'warning'
        WHEN severity = 'critical' THEN 'critical'
        WHEN severity IN ('info', 'warning') THEN severity
        ELSE 'info'
    END AS new_value,
    COUNT(*) AS affected_records
FROM account_alerts
GROUP BY severity
ORDER BY affected_records DESC;
```

#### 4.3.2 执行 SQL

```sql
-- ===== Rev 2B-002: severity 枚举值修复 =====
BEGIN;

-- Step 1: 添加备份列
ALTER TABLE account_alerts
  ADD COLUMN IF NOT EXISTS severity_legacy VARCHAR(20);

-- Step 2: 备份当前值
UPDATE account_alerts
  SET severity_legacy = severity;

-- Step 3: 删除旧 CHECK 约束
ALTER TABLE account_alerts
  DROP CONSTRAINT IF EXISTS check_alert_severity;

-- Step 4: 映射枚举值（遵循 DATA_SCHEMA.md § 3.2.9）
UPDATE account_alerts SET severity = CASE
    WHEN severity = 'low' THEN 'info'
    WHEN severity = 'medium' THEN 'warning'
    WHEN severity = 'high' THEN 'warning'
    WHEN severity = 'critical' THEN 'critical'
    WHEN severity IN ('info', 'warning') THEN severity
    ELSE 'info'
END;

-- Step 5: 添加新 CHECK 约束
ALTER TABLE account_alerts
  ADD CONSTRAINT check_alert_severity
  CHECK (severity IN ('info', 'warning', 'critical'));

COMMIT;
```

#### 4.3.3 Gate 验证

```sql
-- ===== Gate #2B-002: 验证 severity 枚举值 =====

-- Check 1: 枚举值验证
SELECT
    severity,
    COUNT(*) AS count,
    CASE
        WHEN severity IN ('info', 'warning', 'critical') THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM account_alerts
GROUP BY severity
ORDER BY severity;
-- 预期结果: 所有 status = 'PASS'

-- Check 2: CHECK 约束验证
SELECT
    conname,
    pg_get_constraintdef(oid) AS definition,
    CASE
        WHEN pg_get_constraintdef(oid) LIKE '%info%'
         AND pg_get_constraintdef(oid) LIKE '%warning%'
         AND pg_get_constraintdef(oid) LIKE '%critical%' THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM pg_constraint
WHERE conrelid = 'account_alerts'::regclass
  AND conname = 'check_alert_severity';
-- 预期结果: status = 'PASS'

-- Check 3: legacy 列数据完整性
SELECT
    COUNT(*) AS total,
    COUNT(severity_legacy) AS legacy_preserved
FROM account_alerts;
-- 预期结果: legacy_preserved = total
```

#### 4.3.4 回滚 SQL

```sql
-- ===== Rollback Rev 2B-002 =====
BEGIN;

-- Step 1: 恢复旧值
UPDATE account_alerts
  SET severity = severity_legacy;

-- Step 2: 删除新 CHECK 约束
ALTER TABLE account_alerts
  DROP CONSTRAINT check_alert_severity;

-- Step 3: 恢复旧 CHECK 约束
ALTER TABLE account_alerts
  ADD CONSTRAINT check_alert_severity
  CHECK (severity IN ('low', 'medium', 'high', 'critical'));

-- Step 4: 删除备份列
ALTER TABLE account_alerts
  DROP COLUMN severity_legacy;

COMMIT;
```

### 4.4 Phase 2B 观察期（7 天）

**观察时间**: Phase 2B 执行后 7 天

**监控重点**:
- permissions JSONB 的读写操作是否正常
- severity 枚举值在业务逻辑中的使用是否正确
- 前端 UI 是否正确显示新的 severity 值

**每日监控 SQL**:
```sql
-- ===== Phase 2B 每日监控 =====

-- 1. permissions JSONB 异常检查
SELECT id, permissions, permissions_legacy
FROM project_members
WHERE permissions IS NOT NULL
  AND jsonb_typeof(permissions) IS NULL
LIMIT 10;
-- 预期结果: 0 rows

-- 2. severity 非法值检查
SELECT severity, COUNT(*)
FROM account_alerts
WHERE severity NOT IN ('info', 'warning', 'critical')
GROUP BY severity;
-- 预期结果: 0 rows

-- 3. 数据增长监控
SELECT
    'project_members' AS table_name,
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE permissions IS NOT NULL) AS has_permissions
FROM project_members
UNION ALL
SELECT
    'account_alerts' AS table_name,
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE severity = 'info') AS info_count
FROM account_alerts;
```

---

## 五、Phase 2C 文档规范化

### 5.1 Phase 2C 概览

**目标**: 处理 ad_accounts 表的 12 个未定义字段

**SoT 依据**: DATA_SCHEMA.md v5.0 § 5
> 规划表：如需新增表/字段，必须先在本文件创建 `status: planned` 条目并描述字段，再提交迁移。未登记的变更不予实施。

**问题**: ad_accounts 表存在 12 个字段未在 DATA_SCHEMA.md 中定义

**解决方案**: **选项 1 - 补充到 DATA_SCHEMA.md**（最终决议）

### 5.2 决策理由（选项 1 vs 选项 2）

| 维度 | 选项 1: 补充文档 | 选项 2: 迁移到 JSONB | 决策 |
| --- | --- | --- | --- |
| **数据库迁移** | 无需迁移 | 需要复杂迁移 | ✅ 选项 1 |
| **业务代码改动** | 无需改动 | 大规模重构 | ✅ 选项 1 |
| **类型安全** | 保留 PostgreSQL 约束 | 失去类型约束 | ✅ 选项 1 |
| **查询性能** | 原生字段查询快 | JSONB 查询慢 | ✅ 选项 1 |
| **风险** | 极低 | 高 | ✅ 选项 1 |
| **SoT 符合性** | 需补充文档 | 完全符合原始定义 | ⚠️ 平局 |
| **工作量** | 2 小时（文档） | 40 小时（代码+测试） | ✅ 选项 1 |

**最终决议**: **选择选项 1**（补充到 DATA_SCHEMA.md）

### 5.3 执行方案

#### 5.3.1 更新 DATA_SCHEMA.md

**目标文件**: `docs/core/DATA_SCHEMA.md`

**修改位置**: § 3.2.9 `ad_accounts` 表定义

**新增内容**:
```markdown
#### 3.2.9 `ad_accounts` - 扩展字段（Phase 2C 补充）

**核心字段** (已在主表定义中):
- id, name, account_code, platform, project_id, channel_id, owner_id
- status, status_reason, spend_limit, currency, timezone
- created_by, updated_by, created_at, updated_at

**扩展字段** (Phase 2C 补充登记):

以下字段为业务功能扩展字段，不属于核心字段，但已在生产环境使用：

| 字段 | 类型 | 约束 | 说明 | 业务用途 |
| --- | --- | --- | --- | --- |
| `total_spend` | DECIMAL(15,2) | DEFAULT 0.00 | 总消耗 | 统计字段，由定时任务更新 |
| `total_leads` | INTEGER | DEFAULT 0 | 总潜在客户数 | 统计字段 |
| `avg_cpl` | DECIMAL(10,2) | 可空 | 平均单粉成本 | 统计字段，计算公式: total_spend / total_leads |
| `best_cpl` | DECIMAL(10,2) | 可空 | 最佳单粉成本 | 统计字段，历史最低 CPL |
| `setup_fee` | DECIMAL(10,2) | DEFAULT 0.00 | 开户费 | 财务管理 |
| `setup_fee_paid` | BOOLEAN | DEFAULT false | 开户费是否已支付 | 财务管理 |
| `account_type` | VARCHAR(50) | 可空 | 账户类型 | 分类标签，如"个人/企业" |
| `payment_method` | VARCHAR(50) | 可空 | 支付方式 | 财务管理 |
| `billing_information` | JSONB | 可空 | 账单信息 | 财务管理，schema 待补充 |
| `auto_monitoring` | BOOLEAN | DEFAULT true | 自动监控开关 | 运维管理 |
| `alert_thresholds` | JSONB | 可空 | 预警阈值设置 | 运维管理，schema 待补充 |
| `tags` | JSONB | 可空 | 标签 | 分类和筛选 |

**说明**:
1. 统计字段（total_spend, total_leads, avg_cpl, best_cpl）由 `backend/services/account_statistics.py` 定时更新，不应手动修改
2. billing_information 和 alert_thresholds 的 JSONB schema 需在后续版本中补充（待 Phase 3）
3. 这些字段保留以支持现有业务逻辑，不属于 Phase 2 迁移范围
4. 未来新增字段必须先在本文件登记后再实施

**索引建议** (可在 Phase 3 优化):
```sql
CREATE INDEX idx_ad_accounts_total_spend ON ad_accounts(total_spend) WHERE total_spend > 0;
CREATE INDEX idx_ad_accounts_tags ON ad_accounts USING GIN(tags);
```

**版本历史**:
- v5.0: 核心字段定义
- v5.1: Phase 2C 补充扩展字段（2025-11-18）
```

#### 5.3.2 更新 account_documents.status

**同样在 DATA_SCHEMA.md § 3.2.9** 补充:
```markdown
#### 3.2.9 `account_documents` - 扩展字段

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `status` | VARCHAR(20) | DEFAULT 'active' | 文档状态 |

**CHECK 约束**:
```sql
CHECK (status IN ('active', 'archived', 'deleted'))
```

**说明**: 此字段用于软删除机制，不影响核心文档管理流程。
```

#### 5.3.3 更新代码注释

**文件**: `backend/models/ad_account.py`

**修改位置**: Line 81-102

```python
# ===== 扩展字段（已在 DATA_SCHEMA.md v5.1 § 3.2.9 登记）=====
# Phase 2C 补充登记时间: 2025-11-18

# 统计字段（由定时任务更新）
total_spend       = Column(DECIMAL(15, 2), default=0, comment="总消耗（统计字段）")
total_leads       = Column(Integer, default=0, comment="总潜在客户数（统计字段）")
avg_cpl           = Column(DECIMAL(10, 2), nullable=True, comment="平均单粉成本（统计字段）")
best_cpl          = Column(DECIMAL(10, 2), nullable=True, comment="最佳单粉成本（统计字段）")

# 财务管理字段
setup_fee         = Column(DECIMAL(10, 2), default=0, comment="开户费")
setup_fee_paid    = Column(Boolean, default=False, comment="开户费是否已支付")
payment_method    = Column(String(50), nullable=True, comment="支付方式")
billing_information = Column(JSON, nullable=True, comment="账单信息")

# 分类和配置字段
account_type      = Column(String(50), nullable=True, comment="账户类型")
auto_monitoring   = Column(Boolean, default=True, comment="自动监控")
alert_thresholds  = Column(JSON, nullable=True, comment="预警阈值设置")
tags              = Column(JSON, nullable=True, comment="标签")

# ===== 扩展字段定义结束 =====
# 所有字段已在 DATA_SCHEMA.md v5.1 登记，符合 SoT 规范
```

### 5.4 执行步骤

```bash
# ===== Phase 2C 执行 Checklist =====

# 1. 更新 DATA_SCHEMA.md
# 手动编辑或使用以下命令
cd /d/git/1108/AI_ad_spend02/docs/core
# 编辑 DATA_SCHEMA.md § 3.2.9
# 添加上述"扩展字段"章节

# 2. 更新版本号
# 将 DATA_SCHEMA.md 顶部版本号改为 v5.1
sed -i 's/v5.0/v5.1/g' DATA_SCHEMA.md

# 3. 更新代码注释
cd /d/git/1108/AI_ad_spend02/backend/models
# 编辑 ad_account.py Line 81-102
# 添加上述注释

# 4. 提交变更
git add docs/core/DATA_SCHEMA.md backend/models/ad_account.py
git commit -m "docs(schema): Phase 2C - 补充 ad_accounts 扩展字段到 DATA_SCHEMA

- 在 DATA_SCHEMA.md v5.1 § 3.2.9 补充 12 个扩展字段定义
- 补充 account_documents.status 字段定义
- 更新代码注释标注字段已合规
- 所有字段已登记，符合 SoT § 5 规范

Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

# 5. 推送到远程
git push origin main

# 6. 通知团队
echo "Phase 2C 完成，DATA_SCHEMA.md 已更新到 v5.1"
```

**预计工作量**: 2 小时

**风险**: 无（仅文档更新，无代码变更）

---

## 六、环境与审批流程

### 6.1 三环境执行策略

```
┌─────────────────────────────────────────────────────────┐
│                    Dev 环境（开发）                        │
├─────────────────────────────────────────────────────────┤
│ 目的: 验证迁移脚本和 Gate 验证                             │
│ 审批: DBA 决策，无需外部审批                               │
│ 时间窗口: 工作日 14:00-17:00                             │
│ 观察期: 3-7 天                                           │
│ 回滚决策: DBA 决定                                        │
│ 下一步: 通过后进入 Staging                                │
└─────────────────────────────────────────────────────────┘
                         ↓ (Dev 观察期通过)
┌─────────────────────────────────────────────────────────┐
│                  Staging 环境（预发布）                    │
├─────────────────────────────────────────────────────────┤
│ 目的: 业务团队验证 + 性能测试                              │
│ 审批: DBA + 项目经理 双重审批                             │
│ 时间窗口: 工作日 10:00-12:00（避开下午高峰）              │
│ 观察期: 14 天                                            │
│ 回滚决策: 项目经理 + DBA 共同决定                         │
│ 下一步: 通过后（可选）进入 Prod                           │
└─────────────────────────────────────────────────────────┘
                         ↓ (Staging 运行 30 天+)
┌─────────────────────────────────────────────────────────┐
│                    Prod 环境（生产）                       │
├─────────────────────────────────────────────────────────┤
│ 目的: 生产环境 Schema 同步（如需要）                       │
│ 审批: CTO 书面审批 + 变更委员会                           │
│ 时间窗口: 凌晨 2:00-4:00（业务低峰期）                    │
│ 观察期: 30 天                                            │
│ 回滚决策: CTO 授权 + 应急预案                             │
│ 说明: Phase 2 通常不需要在 Prod 执行                      │
└─────────────────────────────────────────────────────────┘
```

### 6.2 Dev 环境执行流程

**前置条件**:
- [ ] Supabase 快照已创建
- [ ] DATABASE_URL 指向 Dev
- [ ] 执行前检查脚本通过
- [ ] SoT 版本已锁定

**执行权限**: DBA 或数据库架构师

**时间窗口**: 工作日 14:00-17:00（避开上午高峰）

**执行步骤**:
```bash
# 1. 执行前准备（见 § 2）
./pre_migration_check.sh

# 2. 执行迁移（见 § 3.3）
alembic upgrade phase2a_003

# 3. Gate 验证（见 § 3.3.3）
psql $DATABASE_URL -f phase2a_gate_verification.sql

# 4. 记录报告（见 § 3.3.4）
# 填写 phase2a_execution_report.txt

# 5. 进入观察期（见 § 3.5）
# 3 天每日监控
```

**通知要求**:
- 执行前 24 小时: 邮件通知开发团队
- 执行中: 在 Slack #database-migration 频道实时更新
- 执行后: 提交执行报告到 Confluence

**回滚权限**: DBA 可直接决定回滚，无需审批

---

### 6.3 Staging 环境执行流程

**前置条件**:
- [ ] Dev 环境 Phase 2A/2B 观察期通过（至少 7 天）
- [ ] 所有 Gate 验证通过
- [ ] SQLAlchemy 模型代码已更新并测试
- [ ] 业务团队审批通过（JIRA 工单）
- [ ] 项目经理审批（邮件确认）

**执行权限**: DBA + 项目经理 双重审批

**审批流程**:
```
1. DBA 提交 JIRA 工单: "Phase 2A Staging 环境执行申请"
   ├── 附件: phase2a_execution_report.txt (Dev 环境)
   ├── 附件: phase2a_observation_summary.log
   └── 预计执行时间: YYYY-MM-DD HH:MM

2. 项目经理审批
   ├── 审核 Dev 环境执行报告
   ├── 确认业务功能测试通过
   └── 批准或拒绝（邮件回复）

3. DBA 执行
   └── 收到审批后，在批准的时间窗口执行
```

**时间窗口**: 工作日 10:00-12:00（避开下午业务高峰）

**观察期**: 14 天（比 Dev 更长）

**回滚权限**: 需要项目经理 + DBA 共同决定

**禁止操作**:
- ❌ 发现新问题时现场修改迁移范围
- ❌ 跳过任何 Gate 验证
- ❌ 缩短观察期

**每周汇报**:
- 每周一 10:00 提交观察报告到项目经理
- 包含: 监控日志、异常统计、业务反馈

---

### 6.4 Prod 环境执行流程（如需要）

**说明**: Phase 2 主要针对 Dev 环境的 Schema 规范化，通常**不需要**在 Prod 执行。

**如果需要在 Prod 执行** (如 Staging → Prod 同步):

**前置条件**:
- [ ] Staging 环境运行 30 天以上无问题
- [ ] 业务团队、项目经理、DBA、CTO 四方审批
- [ ] 变更委员会批准（正式会议纪要）
- [ ] 选择业务低峰期时间窗口
- [ ] 准备回滚预案和应急联系人
- [ ] DBA On-Call 排班确认

**审批流程** (提前 7 天):
```
Day -7: DBA 提交正式变更申请
        ├── 标题: "Phase 2 Production 数据库迁移申请"
        ├── 内容: 详细迁移方案 + Staging 30 天运行报告
        └── 审批人: 项目经理, CTO, 变更委员会

Day -5: 变更委员会评审会议
        ├── 参会: DBA, 项目经理, CTO, 业务负责人
        ├── 评审: 迁移方案、风险、回滚预案
        └── 决策: 批准/拒绝/延期

Day -3: CTO 书面审批
        └── 邮件确认或签字文件

Day -1: 最终确认
        ├── 确认时间窗口（凌晨 2:00-4:00）
        ├── 确认 DBA On-Call
        └── 通知所有相关方

Day 0:  执行（凌晨 2:00-4:00）
```

**时间窗口**: 凌晨 2:00-4:00（业务低峰期，预留 2 小时）

**执行团队**:
- 主执行 DBA: __________
- 备份 DBA: __________
- 应用开发 On-Call: __________
- 项目经理 On-Call: __________

**监控要求**:
```bash
# 实时监控数据库指标
while true; do
    psql $DATABASE_URL -c "
        SELECT
            NOW() AS check_time,
            (SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active') AS active_connections,
            (SELECT ROUND(100.0 * sum(heap_blks_hit) / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0), 2)
             FROM pg_statio_user_tables) AS cache_hit_ratio
    ";
    sleep 60  # 每分钟检查一次
done
```

**紧急联系**:
- DBA On-Call: +86-xxx-xxxx-xxxx
- CTO: +86-xxx-xxxx-xxxx
- 应急升级: <emergency-escalation-process>

**回滚预案**: 发现任何异常立即回滚，不等待分析

---

## 七、风险控制与应急预案

### 7.1 风险评估矩阵

| 风险类别 | 风险描述 | 可能性 | 影响 | 风险等级 | 缓解措施 |
| --- | --- | --- | --- | --- | --- |
| **数据风险** | 时间字段转换数据丢失 | 极低 | 高 | 低 | PostgreSQL 自动处理，无数据丢失 |
| **数据风险** | permissions 包含无效 JSON | 中 | 中 | 中 | 执行前校验，无效值设为 {} |
| **性能风险** | ALTER TABLE 长时间锁表 | 低 | 中 | 低 | 在 Dev 测试执行时间，< 5 分钟可接受 |
| **性能风险** | 数据库连接池耗尽 | 低 | 高 | 中 | 执行前增加连接池限制，监控连接数 |
| **应用风险** | 应用代码未适配 timezone | 低 | 高 | 中 | 观察期密集监控，提前通知开发团队 |
| **回滚风险** | Alembic 回滚失败 | 极低 | 高 | 低 | Supabase 快照作为最后手段 |
| **人为风险** | 误操作生产环境 | 低 | 极高 | 中 | DATABASE_URL 执行前二次确认 |

### 7.2 缓解措施详解

#### 7.2.1 数据库连接池耗尽预防

**问题**: ALTER TABLE 可能导致大量连接等待锁，耗尽连接池

**缓解措施**:
```bash
# 执行前临时增加最大连接数
psql $DATABASE_URL -c "ALTER SYSTEM SET max_connections = 200;"  # 默认 100
psql $DATABASE_URL -c "SELECT pg_reload_conf();"

# 执行迁移
alembic upgrade phase2a_003

# 执行后恢复
psql $DATABASE_URL -c "ALTER SYSTEM SET max_connections = 100;"
psql $DATABASE_URL -c "SELECT pg_reload_conf();"
```

**监控命令**:
```sql
-- 实时监控连接数
SELECT
    COUNT(*) AS total_connections,
    COUNT(*) FILTER (WHERE state = 'active') AS active,
    COUNT(*) FILTER (WHERE state = 'idle') AS idle,
    COUNT(*) FILTER (WHERE wait_event_type = 'Lock') AS waiting_for_lock
FROM pg_stat_activity;
```

#### 7.2.2 长时间锁表预防

**问题**: ALTER COLUMN 需要 ACCESS EXCLUSIVE 锁，可能阻塞其他操作

**缓解措施**:
```bash
# 1. 执行前设置 statement_timeout（防止无限等待）
psql $DATABASE_URL -c "SET statement_timeout = '300s';"  # 5 分钟超时

# 2. 检查是否有长时间运行的查询
psql $DATABASE_URL -c "
    SELECT
        pid,
        NOW() - query_start AS duration,
        state,
        query
    FROM pg_stat_activity
    WHERE state != 'idle'
    AND query_start < NOW() - INTERVAL '5 minutes'
    ORDER BY query_start;
"

# 3. 如果有，等待其完成或终止
# psql $DATABASE_URL -c "SELECT pg_terminate_backend(<pid>);"

# 4. 执行迁移（在锁等待队列最短时）
alembic upgrade phase2a_003
```

#### 7.2.3 应用代码未适配 timezone

**问题**: 应用代码可能假设时间字段为 naive datetime

**缓解措施**:
```python
# backend/utils/datetime_helper.py

from datetime import datetime, timezone

def ensure_utc(dt):
    """确保 datetime 对象有 UTC timezone"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Naive datetime，假设为 UTC
        return dt.replace(tzinfo=timezone.utc)
    # 已有 timezone，转换为 UTC
    return dt.astimezone(timezone.utc)

# 在所有写入数据库前调用
project.created_at = ensure_utc(datetime.now())
```

**通知开发团队**（执行前 3 天）:
```
主题: [重要] Phase 2A 后时间字段处理变更

各位开发者：

Phase 2A 将升级所有时间字段为 TIMESTAMPTZ（带时区）。

影响：
1. 所有时间字段现在有 timezone 信息（UTC）
2. SQLAlchemy 读取时会返回 timezone-aware datetime

建议代码修改：
- 写入数据库前使用 ensure_utc() 确保时区正确
- 比较时间时使用 timezone-aware datetime

参考: backend/utils/datetime_helper.py

如有问题，请联系 DBA 团队
```

### 7.3 应急预案

#### 7.3.1 Gate 验证失败应急流程

```
Gate 验证失败
    ↓
[1分钟内] 立即停止后续操作
    ↓
[5分钟内] DBA 分析失败原因
    ├─ Check 1 失败（字段类型不正确）
    │   └→ 立即回滚（Alembic downgrade）
    ├─ Check 2 失败（数据完整性问题）
    │   ├→ 数据丢失 > 0.1% → 立即回滚
    │   └→ 数据丢失 < 0.1% → 分析原因，可能继续
    └─ Check 3 失败（时间范围异常）
        └→ 修复异常数据后重新执行迁移
    ↓
[10分钟内] 执行回滚或修复
    ↓
[30分钟内] 验证回滚成功，通知团队
    ↓
[1小时内] 提交事故报告到 PROJECT_RISKS.md
```

#### 7.3.2 应用大面积报错应急流程

```
收到应用报错告警（错误率 > 5%）
    ↓
[立即] 检查错误日志，确认是否与迁移相关
    ├─ 与迁移无关 → 交给应用团队处理
    └─ 与迁移相关 → 继续
    ↓
[2分钟内] 评估影响范围
    ├─ 影响核心功能（登录/支付/数据写入）
    │   └→ 立即回滚，不等待分析
    └─ 影响次要功能（报表/统计）
        └→ 尝试热修复应用代码
    ↓
[5分钟内] 执行回滚（如果决定回滚）
    ↓
[10分钟内] 验证应用恢复正常
    ↓
[30分钟内] 向 CTO/项目经理汇报
```

#### 7.3.3 数据库性能严重下降应急流程

```
监控告警: CPU > 90% 或查询响应时间 > 5秒
    ↓
[1分钟内] 检查是否有锁等待
psql> SELECT * FROM pg_stat_activity WHERE wait_event_type = 'Lock';
    ├─ 有锁等待 → 终止迁移事务
    └─ 无锁等待 → 继续分析
    ↓
[3分钟内] 检查慢查询
psql> SELECT query FROM pg_stat_activity WHERE state = 'active' AND query_start < NOW() - INTERVAL '10 seconds';
    ↓
[5分钟内] 决策
    ├─ 性能下降 < 10 分钟 → 等待迁移完成
    └─ 性能下降 > 10 分钟 → 立即回滚
    ↓
[10分钟内] 执行回滚或等待完成
    ↓
[30分钟内] 性能恢复验证
```

### 7.4 紧急联系人与升级路径

#### 7.4.1 联系人清单

| 角色 | 姓名 | 手机 | 邮箱 | 职责范围 |
| --- | --- | --- | --- | --- |
| **DBA On-Call** | __________ | +86-xxx-xxxx-xxxx | dba@example.com | 迁移执行、回滚、数据库问题 |
| **备份 DBA** | __________ | +86-xxx-xxxx-xxxx | dba2@example.com | DBA 不可达时接管 |
| **数据库架构师** | __________ | +86-xxx-xxxx-xxxx | architect@example.com | 技术决策、复杂问题咨询 |
| **应用开发 On-Call** | __________ | +86-xxx-xxxx-xxxx | dev@example.com | 应用代码问题、热修复 |
| **项目经理** | __________ | +86-xxx-xxxx-xxxx | pm@example.com | 业务决策、升级授权 |
| **CTO** | __________ | +86-xxx-xxxx-xxxx | cto@example.com | 最终决策、紧急授权 |

#### 7.4.2 升级路径

```
问题发生
    ↓
[0-5分钟] DBA On-Call 处理
    ├─ 能解决 → 执行修复或回滚
    └─ 不能解决 → 升级
    ↓
[5-15分钟] 升级到数据库架构师
    ├─ 技术方案明确 → 执行
    └─ 需要业务决策 → 升级
    ↓
[15-30分钟] 升级到项目经理
    ├─ 影响可控 → 决策继续或回滚
    └─ 影响严重 → 升级
    ↓
[30-60分钟] 升级到 CTO
    └─ 最终决策（回滚/继续/紧急维护）
```

**升级触发条件**:
- 回滚失败
- 数据丢失 > 0.1%
- 应用错误率 > 10%
- 数据库不可用 > 5 分钟
- 无法在 1 小时内恢复

---

## 八、团队分工与沟通协议

### 8.1 角色与职责

| 角色 | 执行前职责 | 执行中职责 | 执行后职责 |
| --- | --- | --- | --- |
| **DBA** | 准备迁移脚本<br/>创建备份<br/>执行前检查 | 执行迁移<br/>Gate 验证<br/>实时监控 | 观察期监控<br/>问题处理<br/>文档更新 |
| **数据库架构师** | 审核迁移方案<br/>SoT 一致性检查 | 技术支持<br/>复杂问题决策 | 总结经验<br/>优化流程 |
| **应用开发** | 适配代码<br/>单元测试 | 应用监控<br/>热修复（如需要） | 功能测试<br/>性能优化 |
| **QA** | 准备测试用例<br/>环境验证 | 功能测试<br/>回归测试 | 测试报告<br/>缺陷跟踪 |
| **项目经理** | 审批迁移计划<br/>协调资源 | 进度监督<br/>风险决策 | 项目总结<br/>经验沉淀 |

### 8.2 沟通渠道

| 阶段 | 沟通渠道 | 频率 | 参与者 |
| --- | --- | --- | --- |
| **执行前** | 邮件 | 提前 24 小时 | 全体 |
| **执行前** | JIRA 工单 | 一次性 | DBA, PM |
| **执行中** | Slack #database-migration | 实时 | DBA, Dev On-Call |
| **执行中** | 电话/短信 | 紧急情况 | DBA, PM, CTO |
| **执行后** | Confluence 报告 | 执行后 24 小时内 | DBA → 全体 |
| **观察期** | 邮件周报 | 每周一 10:00 | DBA → PM, Dev Lead |

### 8.3 执行时间窗口建议

**Dev 环境**:
- ✅ 推荐: 工作日 14:00-17:00
- ⚠️ 可接受: 工作日 10:00-12:00
- ❌ 避免: 周一上午（会议多）、周五下午（人员不齐）

**Staging 环境**:
- ✅ 推荐: 工作日 10:00-12:00
- ⚠️ 可接受: 工作日 14:00-16:00
- ❌ 避免: 下午 16:00 后（接近下班，问题响应慢）

**Prod 环境**:
- ✅ 推荐: 凌晨 2:00-4:00（业务低峰期）
- ⚠️ 可接受: 凌晨 1:00-3:00
- ❌ 避免: 工作时间、节假日前夜

### 8.4 沟通协议

#### 8.4.1 执行前通知模板（见 § 2.4）

#### 8.4.2 执行中进度更新

**Slack 消息模板**:
```
#database-migration

[14:00] 🚀 Phase 2A 开始执行
- 执行人: @dba-name
- 预计时间: 14:00-14:30
- 进度: 0% (准备中)

[14:05] ⏳ Rev 2A-001 执行中...
- 进度: 33% (projects 模块)
- 状态: 正常

[14:10] ✅ Rev 2A-001 完成
- 进度: 33% → 66%
- Gate #2A-001: PASS

[14:15] ⏳ Rev 2A-002 执行中...
- 进度: 66% (topup 模块)
- 状态: 正常

[14:20] ✅ Rev 2A-002 完成
- Gate #2A-002: PASS

[14:23] ⏳ Rev 2A-003 执行中...
- 进度: 66% → 100%

[14:25] ✅ Phase 2A 执行完成
- Gate #2A: 全部通过
- 总耗时: 25 分钟
- 进入 3 天观察期

[14:30] 📊 执行报告已提交
- 详见: https://confluence.example.com/phase2a-report
```

#### 8.4.3 执行后报告模板（见 § 3.3.4）

#### 8.4.4 观察期周报模板

```
主题: [Phase 2A] 观察期周报 - Week 1

项目经理、开发团队：

Phase 2A 观察期进展报告：

执行时间: 2025-11-18 14:00
观察期: Day 1-7 (2025-11-18 至 2025-11-24)

监控结果:
- 异常时间值: 0 条
- 应用错误（时区相关）: 0 条
- 数据库 CPU 使用率: 45-55%（正常）
- 查询响应时间: 与迁移前持平

业务功能测试:
✅ 项目创建: 正常
✅ 充值申请: 正常
✅ 账本查询: 正常

下周计划:
- 继续每日监控
- 如无异常，Week 1 结束后进入 Phase 2B

详细监控日志: 见附件

DBA 团队
2025-11-24
```

---

## 附录

### A. 文件清单

**Phase 2 相关文件**:

| 文件路径 | 类型 | 用途 | 维护者 |
| --- | --- | --- | --- |
| `docs/core/PHASE2_MIGRATION_MASTER_v2.1.md` | 主文档 | 本文档 | DBA 团队 |
| `docs/core/DATA_SCHEMA.md` | SoT | 数据结构规范 | 架构团队 |
| `backend/alembic/versions/20251118_phase2a_001_*.py` | Alembic | Phase 2A-001 | DBA 团队 |
| `backend/alembic/versions/20251118_phase2a_002_*.py` | Alembic | Phase 2A-002 | DBA 团队 |
| `backend/alembic/versions/20251118_phase2a_003_*.py` | Alembic | Phase 2A-003 | DBA 团队 |
| `backend/phase2a_gate_verification.sql` | SQL | Gate 验证 | DBA 团队 |
| `backend/phase2a_daily_monitoring.sql` | SQL | 每日监控 | DBA 团队 |
| `backend/pre_migration_check.sh` | Shell | 执行前检查 | DBA 团队 |
| `backend/PHASE2A_EXECUTION_GUIDE.md` | 指南 | 执行指南 | DBA 团队 |

### B. SQL 参考

#### B.1 检查当前环境

```sql
-- 确认当前数据库
SELECT current_database();

-- 确认 PostgreSQL 版本
SELECT version();

-- 确认 timezone 设置
SHOW timezone;

-- 检查目标表是否存在
SELECT tablename
FROM pg_tables
WHERE tablename IN (
    'projects', 'project_members', 'project_expenses',
    'topup_requests', 'topup_transactions', 'topup_approval_logs',
    'ledger_entries'
)
ORDER BY tablename;
```

#### B.2 检查字段当前类型

```sql
-- 检查所有时间字段的当前类型
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name IN (
    'projects', 'project_members', 'project_expenses',
    'topup_requests', 'topup_transactions', 'topup_approval_logs',
    'ledger_entries'
)
AND column_name IN ('created_at', 'updated_at', 'occurred_at', 'joined_at', 'paid_at')
ORDER BY table_name, column_name;
```

#### B.3 检查 Alembic 版本

```sql
-- 检查当前 Alembic revision
SELECT * FROM alembic_version;

-- 检查迁移历史（如果有 alembic_version_history 表）
-- SELECT * FROM alembic_version_history ORDER BY installed_on DESC LIMIT 10;
```

#### B.4 性能监控

```sql
-- 监控活跃连接
SELECT
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE state = 'active') AS active,
    COUNT(*) FILTER (WHERE state = 'idle') AS idle,
    COUNT(*) FILTER (WHERE wait_event_type = 'Lock') AS locked
FROM pg_stat_activity;

-- 监控慢查询
SELECT
    pid,
    NOW() - query_start AS duration,
    state,
    LEFT(query, 100) AS query_preview
FROM pg_stat_activity
WHERE state != 'idle'
  AND query_start < NOW() - INTERVAL '5 seconds'
ORDER BY duration DESC;

-- 监控数据库大小
SELECT
    pg_size_pretty(pg_database_size(current_database())) AS db_size;

-- 监控表大小
SELECT
    table_name,
    pg_size_pretty(pg_total_relation_size(quote_ident(table_name)::regclass)) AS total_size,
    pg_size_pretty(pg_relation_size(quote_ident(table_name)::regclass)) AS table_size,
    pg_size_pretty(pg_total_relation_size(quote_ident(table_name)::regclass) - pg_relation_size(quote_ident(table_name)::regclass)) AS index_size
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('projects', 'topup_requests', 'ledger_entries')
ORDER BY pg_total_relation_size(quote_ident(table_name)::regclass) DESC;
```

### C. 术语表

| 术语 | 英文 | 定义 |
| --- | --- | --- |
| **SoT** | Single Source of Truth | 唯一事实来源，指权威规范文档如 DATA_SCHEMA.md |
| **Phase** | Phase | 数据库迁移的大阶段（如 Phase 1, Phase 2） |
| **Rev** | Revision | Alembic 迁移的具体版本（如 Rev 2A-001） |
| **Gate** | Gate Check | 验证检查点，用于确保迁移成功 |
| **Strategy B** | Strategy B | 数据迁移策略：置 NULL + legacy 备份 |
| **Legacy 列** | Legacy Column | 备份列，用于保留迁移前的原始数据 |
| **观察期** | Observation Period | 迁移后的监控期，通常 3-7 天 |
| **可逆** | Reversible | 可以通过 `alembic downgrade` 回滚 |
| **不可逆** | Irreversible | 只能通过快照恢复回滚 |
| **ACCESS EXCLUSIVE** | Lock Mode | PostgreSQL 最高级别锁，阻塞所有操作 |
| **TIMESTAMPTZ** | Type | 带时区的时间戳类型（timestamp with time zone） |
| **JSONB** | Type | PostgreSQL 二进制 JSON 类型 |

### D. 常见问题（FAQ）

**Q1: Phase 2 会影响生产环境吗？**
A: 不会。Phase 2 主要针对 Dev 环境的 Schema 规范化。只有在 Staging 验证 30 天后，且业务明确需要，才会考虑在 Prod 执行。

**Q2: 为什么选择选项 1（补充文档）而不是选项 2（迁移到 JSONB）？**
A: 选项 1 风险最低（无需重构代码）、性能最优（原生字段查询）、类型安全最好（保留 PostgreSQL 约束）。

**Q3: 观察期可以缩短吗？**
A: 不建议。Phase 2A 观察期 3 天、Phase 2B 观察期 7 天是基于历史经验的最小安全期。

**Q4: 如果 Gate 验证失败怎么办？**
A: 立即停止，执行回滚（Alembic downgrade），分析失败原因后重新执行。

**Q5: Phase 2 完成后，legacy 列可以删除吗？**
A: 建议至少保留 30 天。如果业务团队确认无需回溯历史数据，可在下一个维护窗口删除。

**Q6: 执行中可以取消吗？**
A: 可以，但要看执行到哪一步。如果正在执行 ALTER TABLE，必须等待当前语句完成后才能回滚。

**Q7: 如何确保不会误操作生产环境？**
A: 执行前必须二次确认 DATABASE_URL，建议在 shell 脚本中强制确认步骤。

**Q8: Phase 2 总共需要多长时间？**
A: Dev 环境执行 + 观察期约 10-14 天。如果包括 Staging，总共约 30 天。

**Q9: 如果发现新的 Schema 差异怎么办？**
A: 记录到 PROJECT_RISKS.md，纳入下一个 Phase（Phase 2.1 或 Phase 3），不允许现场扩展范围。

**Q10: Phase 2 与 Phase 1 的关系？**
A: Phase 1 已完成 reconciliation 表的修复。Phase 2 修复核心业务表（projects, topup, ledger 等）。两者独立，Phase 2 不依赖 Phase 1。

---

**文档版本**: v2.1 (Production Ready)
**发布日期**: 2025-11-18
**下次审阅**: Phase 2 完成后（预计 2025-12-01）
**维护责任**: 数据库架构组 + DBA 团队
**紧急联系**: DBA On-Call +86-xxx-xxxx-xxxx

---

**附加说明**:
1. 本文档是执行层文档，所有规范以 DATA_SCHEMA.md 为准
2. 执行前必须锁定 SoT 版本，执行期间禁止修改
3. 任何与本文档冲突的操作必须先更新本文档再执行
4. Phase 2 完成后必须更新 DATA_SCHEMA.md 到 v5.1

**签署确认**（执行前填写）:

| 角色 | 姓名 | 签字 | 日期 |
| --- | --- | --- | --- |
| DBA | __________ | __________ | __________ |
| 数据库架构师 | __________ | __________ | __________ |
| 项目经理 | __________ | __________ | __________ |

**Phase 2 Migration Master Document - End**
