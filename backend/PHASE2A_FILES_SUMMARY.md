# Phase 2A 文件清单

> **生成日期**: 2025-11-18
> **目的**: Phase 2A 时间字段 timezone 修复
> **影响范围**: 7 个表，14 个字段

---

## 📁 生成的文件列表

### 1. Alembic 迁移脚本（3 个）

| 文件名 | 位置 | 说明 | 行数 |
| --- | --- | --- | --- |
| `20251118_phase2a_001_projects_timezone.py` | `backend/alembic/versions/` | projects 模块时间字段修复 | ~200 |
| `20251118_phase2a_002_topup_timezone.py` | `backend/alembic/versions/` | topup 模块时间字段修复 | ~200 |
| `20251118_phase2a_003_ledger_timezone.py` | `backend/alembic/versions/` | ledger 模块时间字段修复 | ~100 |

**用途**: 通过 Alembic 执行数据库迁移（推荐方式）

**执行命令**:
```bash
cd backend
alembic upgrade phase2a_003
```

---

### 2. Gate 验证脚本（1 个）

| 文件名 | 位置 | 说明 | 行数 |
| --- | --- | --- | --- |
| `phase2a_gate_verification.sql` | `backend/` | 综合验证脚本 | ~400 |

**用途**: 验证迁移结果是否符合预期

**执行命令**:
```bash
psql $DATABASE_URL -f phase2a_gate_verification.sql
```

**验证内容**:
- Check 1: 所有 14 个字段类型为 TIMESTAMPTZ
- Check 2: 数据完整性（无记录丢失）
- Check 3: 时间范围合理性（2020-01-01 至当前）
- Check 4: Timezone 设置正确
- Check 5: 综合统计

---

### 3. 执行指南（1 个）

| 文件名 | 位置 | 说明 | 字数 |
| --- | --- | --- | --- |
| `PHASE2A_EXECUTION_GUIDE.md` | `backend/` | 完整的执行指南 | ~8,000 |

**包含内容**:
- ✅ 执行前检查清单
- 🚀 执行步骤（Alembic 和 SQL 两种方式）
- ✅ Gate 验证通过标准
- 🔄 回滚步骤
- 📊 观察期监控指南
- 📝 SQLAlchemy 模型更新说明
- 🆘 故障排查

---

### 4. Python 执行脚本（1 个，备用）

| 文件名 | 位置 | 说明 | 行数 |
| --- | --- | --- | --- |
| `execute_phase2a.py` | `backend/` | 直接执行 SQL 的 Python 脚本 | ~300 |

**用途**: Alembic 不可用时的备用方案

**执行命令**:
```bash
cd backend
python execute_phase2a.py
```

**特点**:
- 包含用户确认流程
- 自动执行所有 SQL
- 内置基础 Gate 验证
- 失败自动回滚

---

## 📊 影响范围汇总

### 修复的表和字段

| 模块 | 表名 | 字段 | 修复前 | 修复后 |
| --- | --- | --- | --- | --- |
| 项目 | projects | created_at, updated_at | TIMESTAMP | TIMESTAMPTZ |
| 项目 | project_members | joined_at | TIMESTAMP | TIMESTAMPTZ |
| 项目 | project_expenses | occurred_at, created_at | TIMESTAMP | TIMESTAMPTZ |
| 充值 | topup_requests | created_at, updated_at | TIMESTAMP | TIMESTAMPTZ |
| 充值 | topup_transactions | paid_at, created_at | TIMESTAMP | TIMESTAMPTZ |
| 充值 | topup_approval_logs | created_at | TIMESTAMP | TIMESTAMPTZ |
| 账本 | ledger_entries | occurred_at | TIMESTAMP | TIMESTAMPTZ |

**合计**: 7 个表，14 个字段

---

## 🎯 执行优先级

### 推荐执行顺序

1. **优先使用 Alembic**（推荐）:
   ```bash
   cd backend
   alembic upgrade phase2a_003
   psql $DATABASE_URL -f phase2a_gate_verification.sql
   ```

2. **备用方案：Python 脚本**:
   ```bash
   cd backend
   python execute_phase2a.py
   psql $DATABASE_URL -f phase2a_gate_verification.sql
   ```

3. **最后手段：直接 SQL**（不推荐，无版本控制）:
   - 从 `PHASE2A_EXECUTION_GUIDE.md` 复制 SQL
   - 手动执行

---

## ✅ 执行前准备

### 必须完成的任务

- [ ] 1. **创建 Supabase 快照备份**
  - 登录 Supabase Dashboard
  - 进入 Settings → Database → Backups
  - 创建手动快照

- [ ] 2. **确认环境**
  ```bash
  echo $DATABASE_URL
  # 确保指向 Dev 环境，不是生产库
  ```

- [ ] 3. **检查表存在性**
  ```sql
  SELECT tablename FROM pg_tables
  WHERE tablename IN (
      'projects', 'project_members', 'project_expenses',
      'topup_requests', 'topup_transactions', 'topup_approval_logs',
      'ledger_entries'
  );
  ```
  应返回 7 行

- [ ] 4. **阅读执行指南**
  ```bash
  cat backend/PHASE2A_EXECUTION_GUIDE.md
  ```

---

## 📈 预计时间和风险

| 项目 | 预计时间 | 风险等级 |
| --- | --- | --- |
| 迁移脚本执行 | 5 分钟 | 低 |
| Gate 验证 | 10 分钟 | 低 |
| SQLAlchemy 模型更新 | 30 分钟 | 低 |
| 观察期 | 3 天 | 低 |
| **总计** | **3.5 天** | **低** |

**数据风险**: 极低（完全可逆，PostgreSQL 自动处理类型转换）
**业务风险**: 低（时间字段类型升级不影响应用层读写）
**回滚难度**: 简单（一条 ALTER 语句即可回滚）

---

## 🔄 回滚方案

### 快速回滚（如果 Gate 验证失败）

#### 方式 1: Alembic 回滚
```bash
alembic downgrade <前一个revision>
```

#### 方式 2: SQL 回滚
```sql
-- 从 PHASE2A_EXECUTION_GUIDE.md 复制回滚 SQL
-- 或使用以下命令
psql $DATABASE_URL << 'EOF'
ALTER TABLE ledger_entries ALTER COLUMN occurred_at TYPE TIMESTAMP USING occurred_at;
ALTER TABLE topup_approval_logs ALTER COLUMN created_at TYPE TIMESTAMP USING created_at;
-- ... 其他表类似
EOF
```

#### 方式 3: Supabase 快照恢复（最后手段）
- 登录 Supabase Dashboard
- 进入 Settings → Database → Backups
- 选择执行前的快照
- 点击 Restore

---

## 📝 执行后任务

### 必须完成的任务

- [ ] 1. **更新 SQLAlchemy 模型**
  - 修改 `backend/models/projects.py`
  - 修改 `backend/models/topup.py`
  - 修改 `backend/models/ledger.py`
  - 详细说明见 `PHASE2A_EXECUTION_GUIDE.md`

- [ ] 2. **运行测试**
  ```bash
  pytest tests/
  ```

- [ ] 3. **更新文档**
  - 在 `DATABASE_SCHEMA_MIGRATION_PLAN.md` 记录 Phase 2A 执行
  - 在 `CHANGELOG.md` 记录变更

- [ ] 4. **提交代码**
  ```bash
  git add backend/alembic/versions/*phase2a*
  git add backend/models/projects.py backend/models/topup.py backend/models/ledger.py
  git commit -m "feat(db): Phase 2A - 升级时间字段为 TIMESTAMPTZ

  - 修复 7 个表共 14 个时间字段
  - 符合 DATA_SCHEMA.md v5.0 § 1.1 规范
  - 所有字段从 TIMESTAMP 升级为 TIMESTAMPTZ
  - 完全可逆，数据无丢失

  Tables:
  - projects, project_members, project_expenses
  - topup_requests, topup_transactions, topup_approval_logs
  - ledger_entries

  Generated with Claude Code"
  ```

---

## 📞 支持和反馈

### 如果遇到问题

1. **首先检查 Gate 验证结果**
   - 哪些 Check 失败？
   - 具体错误信息是什么？

2. **查阅故障排查章节**
   - `PHASE2A_EXECUTION_GUIDE.md` § 故障排查

3. **执行回滚确保系统可用**

4. **联系支持**
   - DBA 团队
   - 系统架构团队
   - Claude Code（通过 GitHub Issues）

---

## 🎉 下一步

Phase 2A 成功后：

1. **观察期 3 天**（2025-11-18 至 2025-11-21）
   - 每日监控异常时间值
   - 检查应用日志
   - 测试业务功能

2. **如果观察期无问题**
   - 进入 **Phase 2B**（字段类型修复）
     - project_members.permissions: Text → JSONB
     - account_alerts.severity: 枚举值修复

3. **最终目标**
   - 实现与 DATA_SCHEMA.md v5.0 的 **100% 符合**
   - 完成 Phase 2 全部迁移

---

**文件清单版本**: v1.0
**生成日期**: 2025-11-18
**维护人**: 数据库架构师（Claude Code）
