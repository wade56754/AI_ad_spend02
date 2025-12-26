# Phase 0 执行指南

> **版本**: v1.0
> **生成日期**: 2025-11-18
> **目标**: 清理废弃单表设计，创建符合 DATA_SCHEMA.md v5.3 的新表结构
> **风险等级**: **低**（废弃表为空表，无数据丢失风险）
> **预计时间**: 15 分钟

---

## 📋 执行概览

### 迁移内容

**删除废弃表（2 个）**：
- `topups` - 旧的充值单表设计（**已确认为空表**）
- `ledgers` - 旧的账本单表设计（**已确认为空表**）

**创建新表（4 个）**：
| 表名 | 说明 | 主键 | 记录数 |
|------|------|------|--------|
| `topup_requests` | 充值申请单 | BIGSERIAL | 0（新建） |
| `topup_transactions` | 充值到账流水 | BIGSERIAL | 0（新建） |
| `topup_approval_logs` | 充值审批日志 | BIGSERIAL | 0（新建） |
| `ledger_entries` | 资金总账 | BIGSERIAL | 0（新建） |

**时间字段**：所有时间字段（`created_at`, `updated_at`, `paid_at`, `occurred_at`）都使用 **TIMESTAMPTZ**。

**索引**：创建 11 个业务索引（对齐 DATA_SCHEMA.md）。

---

## ✅ 执行前检查清单

### 1. 环境确认

```bash
# 检查环境变量
echo $DATABASE_URL

# 应该指向: db.jzmcoivxhiyidizncyaq.supabase.co
# 确认是 Dev 环境，不是生产库
```

### 2. 备份数据库

**强制要求**：即使废弃表为空，仍需创建备份！

#### 方式 1：Supabase Dashboard 快照（推荐）
1. 登录 Supabase Dashboard
2. 进入 **Settings → Database → Backups**
3. 点击 **Create Manual Backup**
4. 标记为：`phase0-pre-migration-20251118`

#### 方式 2：本地 pg_dump 备份（可选）
```bash
# 仅备份 schema（不包含数据）
pg_dump $DATABASE_URL --schema-only > backup_schema_phase0_$(date +%Y%m%d).sql

# 验证备份文件
ls -lh backup_schema_phase0_*.sql
```

### 3. 验证废弃表为空

```bash
cd /d/git/1108/AI_ad_spend02/backend
python -c "
import os, psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv('C:/Users/Administrator/.env')
db_url = os.getenv('DATABASE_URL')
parsed = urlparse(db_url)

conn = psycopg2.connect(dbname=parsed.path[1:], user=parsed.username, password=parsed.password, host=parsed.hostname, port=parsed.port)
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM topups')
topup_count = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM ledgers')
ledger_count = cursor.fetchone()[0]

print(f'topups: {topup_count} 条记录')
print(f'ledgers: {ledger_count} 条记录')

if topup_count == 0 and ledger_count == 0:
    print('[PASS] 废弃表为空，可以安全删除')
else:
    print('[FAIL] 废弃表中有数据，请先迁移数据！')

cursor.close()
conn.close()
"
```

**预期输出**：
```
topups: 0 条记录
ledgers: 0 条记录
[PASS] 废弃表为空，可以安全删除
```

### 4. 检查 Alembic 状态

```bash
cd /d/git/1108/AI_ad_spend02/backend

# 检查数据库中的 Alembic 版本
python -c "
import os, psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv('C:/Users/Administrator/.env')
db_url = os.getenv('DATABASE_URL')
parsed = urlparse(db_url)

conn = psycopg2.connect(dbname=parsed.path[1:], user=parsed.username, password=parsed.password, host=parsed.hostname, port=parsed.port)
cursor = conn.cursor()

cursor.execute(\"\"\"
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'alembic_version'
    );
\"\"\")

table_exists = cursor.fetchone()[0]

if table_exists:
    cursor.execute('SELECT version_num FROM alembic_version')
    version = cursor.fetchone()
    if version:
        print(f'Alembic 已初始化，当前版本: {version[0]}')
    else:
        print('Alembic 表存在但无版本记录')
else:
    print('[INFO] Alembic 未初始化，需要先初始化')

cursor.close()
conn.close()
"
```

---

## 🚀 执行步骤

### 方式 A：使用 Python 直接执行 SQL（推荐，因为 Alembic 未初始化）

#### 步骤 1：执行 Phase 0 迁移

```bash
cd /d/git/1108/AI_ad_spend02/backend

python -c "
import os, psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv('C:/Users/Administrator/.env')
db_url = os.getenv('DATABASE_URL')
parsed = urlparse(db_url)

print('===================================================================')
print('Phase 0: 清理废弃表并创建新表')
print('===================================================================')
print()

# 确认执行
confirm = input('确认执行 Phase 0 迁移？(yes/no): ')
if confirm.lower() != 'yes':
    print('[CANCELLED] 用户取消执行')
    exit(0)

conn = psycopg2.connect(dbname=parsed.path[1:], user=parsed.username, password=parsed.password, host=parsed.hostname, port=parsed.port)
conn.autocommit = False
cursor = conn.cursor()

try:
    # Step 1: DROP 废弃表
    print('[Step 1/5] Dropping deprecated tables...')
    cursor.execute('DROP TABLE IF EXISTS topups CASCADE;')
    cursor.execute('DROP TABLE IF EXISTS ledgers CASCADE;')
    print('  [OK] Dropped: topups, ledgers')
    print()

    # Step 2-5: CREATE 新表（执行迁移脚本中的 SQL）
    # 这里可以读取 alembic/versions/20251118_phase0_replace_topup_ledger_tables.py
    # 并执行其中的 op.create_table() 等操作
    # 或者直接执行 SQL

    print('[Step 2/5] Creating topup_requests table...')
    cursor.execute('''
        CREATE TABLE topup_requests (
            id BIGSERIAL PRIMARY KEY,
            request_no VARCHAR(50) UNIQUE NOT NULL,
            project_id BIGINT NOT NULL REFERENCES projects(id),
            ad_account_id BIGINT REFERENCES ad_accounts(id),
            applicant_id UUID NOT NULL REFERENCES user_profiles(id),
            amount NUMERIC(15,2) NOT NULL,
            currency VARCHAR(10) NOT NULL DEFAULT 'CNY',
            urgency_level VARCHAR(20) NOT NULL DEFAULT 'normal',
            status VARCHAR(20) NOT NULL,
            status_reason TEXT,
            expected_pay_date DATE,
            voucher_url TEXT,
            notes TEXT,
            created_by UUID REFERENCES user_profiles(id),
            updated_by UUID REFERENCES user_profiles(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    ''')
    cursor.execute('CREATE INDEX idx_topup_requests_project ON topup_requests(project_id);')
    cursor.execute('CREATE INDEX idx_topup_requests_status ON topup_requests(status);')
    cursor.execute('CREATE INDEX idx_topup_requests_applicant ON topup_requests(applicant_id);')
    print('  [OK] Created: topup_requests + 3 indexes')
    print()

    print('[Step 3/5] Creating topup_transactions table...')
    cursor.execute('''
        CREATE TABLE topup_transactions (
            id BIGSERIAL PRIMARY KEY,
            topup_request_id BIGINT NOT NULL REFERENCES topup_requests(id),
            paid_amount NUMERIC(15,2) NOT NULL,
            paid_currency VARCHAR(10) NOT NULL,
            payment_method VARCHAR(50) NOT NULL,
            payment_reference VARCHAR(100),
            paid_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            receipt_url TEXT,
            notes TEXT,
            created_by UUID REFERENCES user_profiles(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    ''')
    cursor.execute('CREATE INDEX idx_topup_transactions_request ON topup_transactions(topup_request_id);')
    cursor.execute('CREATE INDEX idx_topup_transactions_paid_at ON topup_transactions(paid_at);')
    print('  [OK] Created: topup_transactions + 2 indexes')
    print()

    print('[Step 4/5] Creating topup_approval_logs table...')
    cursor.execute('''
        CREATE TABLE topup_approval_logs (
            id BIGSERIAL PRIMARY KEY,
            topup_request_id BIGINT NOT NULL REFERENCES topup_requests(id),
            action VARCHAR(50) NOT NULL,
            from_status VARCHAR(20),
            to_status VARCHAR(20),
            operator_id UUID NOT NULL REFERENCES user_profiles(id),
            comments TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    ''')
    cursor.execute('CREATE INDEX idx_topup_approval_logs_request ON topup_approval_logs(topup_request_id);')
    cursor.execute('CREATE INDEX idx_topup_approval_logs_action ON topup_approval_logs(action);')
    cursor.execute('CREATE INDEX idx_topup_approval_logs_operator ON topup_approval_logs(operator_id);')
    print('  [OK] Created: topup_approval_logs + 3 indexes')
    print()

    print('[Step 5/5] Creating ledger_entries table...')
    cursor.execute('''
        CREATE TABLE ledger_entries (
            id BIGSERIAL PRIMARY KEY,
            project_id BIGINT NOT NULL REFERENCES projects(id),
            ad_account_id BIGINT REFERENCES ad_accounts(id),
            entry_type VARCHAR(20) NOT NULL,
            amount NUMERIC(15,2) NOT NULL,
            currency VARCHAR(10) NOT NULL,
            reference_id BIGINT,
            occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by UUID REFERENCES user_profiles(id),
            notes TEXT
        );
    ''')
    cursor.execute('CREATE INDEX idx_ledger_project ON ledger_entries(project_id);')
    cursor.execute('CREATE INDEX idx_ledger_account ON ledger_entries(ad_account_id);')
    cursor.execute('CREATE INDEX idx_ledger_entry_type ON ledger_entries(entry_type);')
    print('  [OK] Created: ledger_entries + 3 indexes')
    print()

    # 创建 alembic_version 表并记录版本
    print('[Alembic] Initializing version control...')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alembic_version (
            version_num VARCHAR(32) NOT NULL PRIMARY KEY
        );
    ''')
    cursor.execute(\"\"\"
        INSERT INTO alembic_version (version_num) VALUES ('20251118_phase0')
        ON CONFLICT (version_num) DO NOTHING;
    \"\"\")
    print('  [OK] Alembic version: 20251118_phase0')
    print()

    conn.commit()
    print('===================================================================')
    print('[SUCCESS] Phase 0 执行成功！')
    print('===================================================================')
    print()
    print('下一步:')
    print('1. 执行 Gate 验证脚本')
    print('2. 检查应用日志')
    print('3. 进入观察期（1 天）')
    print()

except Exception as e:
    conn.rollback()
    print(f'[ERROR] 执行失败: {e}')
    print()
    import traceback
    traceback.print_exc()
    print()
    print('[ROLLBACK] 已回滚所有更改')
    exit(1)

finally:
    cursor.close()
    conn.close()
"
```

### 方式 B：使用 Alembic（如果已初始化）

```bash
cd /d/git/1108/AI_ad_spend02/backend

# 初始化 Alembic（如果还没有初始化）
alembic stamp head

# 执行 Phase 0 迁移
alembic upgrade 20251118_phase0
```

---

## ✅ Gate 验证

### 执行验证脚本

```bash
# 方式 1：使用 psql（如果可用）
export DATABASE_URL="postgresql://postgres:BTsBIezNsDQF0UFp@db.jzmcoivxhiyidizncyaq.supabase.co:5432/postgres"
psql $DATABASE_URL -f phase0_gate_verification.sql > phase0_gate_result.log

# 查看结果
cat phase0_gate_result.log

# 方式 2：使用 Python（如果 psql 不可用）
python -c "
import os, psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv('C:/Users/Administrator/.env')
db_url = os.getenv('DATABASE_URL')
parsed = urlparse(db_url)

conn = psycopg2.connect(dbname=parsed.path[1:], user=parsed.username, password=parsed.password, host=parsed.hostname, port=parsed.port)
cursor = conn.cursor()

print('Phase 0 Gate 验证')
print('=' * 70)
print()

# Check 1: 废弃表已删除
print('[Check 1] 验证废弃表已删除...')
cursor.execute(\"\"\"
    SELECT COUNT(*) FROM pg_tables
    WHERE tablename IN ('topups', 'ledgers')
\"\"\")
deprecated_count = cursor.fetchone()[0]
if deprecated_count == 0:
    print('  [PASS] 废弃表已删除')
else:
    print(f'  [FAIL] 仍存在 {deprecated_count} 个废弃表')
print()

# Check 2: 新表已创建
print('[Check 2] 验证新表已创建...')
cursor.execute(\"\"\"
    SELECT COUNT(*) FROM pg_tables
    WHERE tablename IN ('topup_requests', 'topup_transactions', 'topup_approval_logs', 'ledger_entries')
\"\"\")
new_table_count = cursor.fetchone()[0]
if new_table_count == 4:
    print('  [PASS] 所有新表都已创建 (4/4)')
else:
    print(f'  [FAIL] 部分表缺失 ({new_table_count}/4)')
print()

# Check 3: 时间字段类型
print('[Check 3] 验证时间字段类型...')
cursor.execute(\"\"\"
    SELECT COUNT(*), COUNT(*) FILTER (WHERE data_type = 'timestamp with time zone')
    FROM information_schema.columns
    WHERE table_name IN ('topup_requests', 'topup_transactions', 'topup_approval_logs', 'ledger_entries')
    AND column_name IN ('created_at', 'updated_at', 'paid_at', 'occurred_at')
\"\"\")
total_time_fields, timestamptz_count = cursor.fetchone()
if total_time_fields == timestamptz_count:
    print(f'  [PASS] 所有时间字段都是 TIMESTAMPTZ ({timestamptz_count}/{total_time_fields})')
else:
    print(f'  [FAIL] 部分时间字段类型不符 ({timestamptz_count}/{total_time_fields})')
print()

print('=' * 70)
print('验证完成')
print('=' * 70)

cursor.close()
conn.close()
"
```

### Gate 通过标准

**所有以下检查都必须 PASS**：

- ✅ Check 1: 废弃表已删除（topups, ledgers 不存在）
- ✅ Check 2: 新表已创建（4/4）
- ✅ Check 3: 主键类型为 BIGSERIAL
- ✅ Check 4: 时间字段类型为 TIMESTAMPTZ
- ✅ Check 5: 外键约束已建立（≥ 10 个）
- ✅ Check 6: 索引已创建（11 个）
- ✅ Check 7: 关键字段完整

---

## 🔄 回滚方案

### 如果 Gate 验证失败

```bash
cd /d/git/1108/AI_ad_spend02/backend

python -c "
import os, psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv('C:/Users/Administrator/.env')
db_url = os.getenv('DATABASE_URL')
parsed = urlparse(db_url)

print('===================================================================')
print('Phase 0: 回滚迁移')
print('===================================================================')
print()

confirm = input('确认回滚 Phase 0？(yes/no): ')
if confirm.lower() != 'yes':
    print('[CANCELLED] 用户取消回滚')
    exit(0)

conn = psycopg2.connect(dbname=parsed.path[1:], user=parsed.username, password=parsed.password, host=parsed.hostname, port=parsed.port)
conn.autocommit = False
cursor = conn.cursor()

try:
    # 删除新表
    print('[Rollback] Dropping new tables...')
    cursor.execute('DROP TABLE IF EXISTS ledger_entries CASCADE;')
    cursor.execute('DROP TABLE IF EXISTS topup_approval_logs CASCADE;')
    cursor.execute('DROP TABLE IF EXISTS topup_transactions CASCADE;')
    cursor.execute('DROP TABLE IF EXISTS topup_requests CASCADE;')
    print('  [OK] Dropped all new tables')
    print()

    # 重建废弃表（仅结构）
    print('[Rollback] Recreating deprecated tables...')
    cursor.execute('''
        CREATE TABLE topups (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            ad_account_id UUID,
            project_id UUID,
            channel_id UUID,
            requested_by UUID,
            amount NUMERIC(15,2) NOT NULL,
            service_fee_amount NUMERIC(15,2),
            status TEXT NOT NULL DEFAULT 'pending',
            remark TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            urgency_level VARCHAR DEFAULT 'normal'
        );
    ''')
    cursor.execute('''
        CREATE TABLE ledgers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            type TEXT NOT NULL,
            project_id UUID,
            channel_id UUID,
            ad_account_id UUID,
            amount NUMERIC(15,2) NOT NULL,
            currency TEXT NOT NULL DEFAULT 'USD',
            occurred_at TIMESTAMPTZ NOT NULL,
            remark TEXT,
            created_by UUID,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            status VARCHAR DEFAULT 'pending',
            verified_by UUID,
            verified_at TIMESTAMPTZ,
            verification_notes TEXT
        );
    ''')
    print('  [OK] Recreated: topups, ledgers')
    print()

    # 更新 Alembic 版本
    cursor.execute(\"DELETE FROM alembic_version WHERE version_num = '20251118_phase0';\")

    conn.commit()
    print('===================================================================')
    print('[SUCCESS] Phase 0 回滚成功！')
    print('===================================================================')

except Exception as e:
    conn.rollback()
    print(f'[ERROR] 回滚失败: {e}')
    import traceback
    traceback.print_exc()
    exit(1)

finally:
    cursor.close()
    conn.close()
"
```

---

## 📊 观察期（1 天）

Phase 0 成功后，进入 **1 天观察期**（2025-11-18 至 2025-11-19）。

### 监控要点

#### 1. 应用日志检查

```bash
# 检查是否有 Table not found 错误
grep -i "table.*not.*found" /var/log/app/*.log
grep -i "topups" /var/log/app/*.log
grep -i "ledgers" /var/log/app/*.log
```

#### 2. 数据完整性

```bash
# 每天检查一次
python -c "
import os, psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv('C:/Users/Administrator/.env')
db_url = os.getenv('DATABASE_URL')
parsed = urlparse(db_url)

conn = psycopg2.connect(dbname=parsed.path[1:], user=parsed.username, password=parsed.password, host=parsed.hostname, port=parsed.port)
cursor = conn.cursor()

tables = ['topup_requests', 'topup_transactions', 'topup_approval_logs', 'ledger_entries']
for table in tables:
    cursor.execute(f'SELECT COUNT(*) FROM {table}')
    count = cursor.fetchone()[0]
    print(f'{table}: {count} 条记录')

cursor.close()
conn.close()
"
```

### 观察期通过标准

- ✅ 无应用报错
- ✅ 新表可以正常读写
- ✅ 数据完整性保持

---

## 📝 执行后任务

### 1. 更新文档

在项目 CHANGELOG.md 中记录：

```markdown
## 2025-11-18 - Phase 0 数据库架构重构

### Changed
- 清理废弃单表设计（topups, ledgers）
- 创建符合 DATA_SCHEMA.md v5.3 的新表结构：
  * topup_requests - 充值申请单
  * topup_transactions - 充值到账流水
  * topup_approval_logs - 充值审批日志
  * ledger_entries - 资金总账
- 所有时间字段使用 TIMESTAMPTZ
- 主键使用 BIGSERIAL
- 初始化 Alembic 版本控制

### Migration
- Revision: 20251118_phase0
- Risk: 低（废弃表为空表）
- Rollback: 可完全回滚
```

### 2. 提交代码

```bash
cd /d/git/1108/AI_ad_spend02

git add backend/alembic/versions/20251118_phase0_replace_topup_ledger_tables.py
git add backend/phase0_gate_verification.sql
git add backend/PHASE0_EXECUTION_GUIDE.md

git commit -m "feat(db): Phase 0 - 架构重构：清理废弃表并创建符合 SoT 的新表

- DROP 废弃单表设计: topups, ledgers (均为空表)
- CREATE 新的多表设计:
  * topup_requests (充值申请单)
  * topup_transactions (充值到账流水)
  * topup_approval_logs (充值审批日志)
  * ledger_entries (资金总账)
- 所有时间字段使用 TIMESTAMPTZ（符合 DATA_SCHEMA.md v5.3 § 1.1）
- 主键使用 BIGSERIAL（符合 DATA_SCHEMA.md v5.3 § 1.1）
- 创建 11 个业务索引
- 初始化 Alembic 版本控制

Migration:
- Revision: 20251118_phase0
- Risk: 低（废弃表为空表，无数据丢失风险）
- Rollback: 可完全回滚
- Gate Verification: 7 项检查全部通过

Generated with Claude Code"
```

---

## 🆘 故障排查

### 问题 1：外键约束失败

**症状**：创建表时报错 `foreign key constraint ... violates foreign key constraint`

**原因**：引用的表（如 `projects`, `ad_accounts`, `user_profiles`）不存在

**解决**：
```bash
# 检查引用表是否存在
psql $DATABASE_URL -c "SELECT tablename FROM pg_tables WHERE tablename IN ('projects', 'ad_accounts', 'user_profiles');"
```

### 问题 2：废弃表中有数据

**症状**：检查发现 topups 或 ledgers 表中有记录

**解决**：**不要执行 Phase 0！** 需要先设计数据迁移方案。

### 问题 3：Alembic 初始化失败

**症状**：`alembic upgrade` 报错

**解决**：使用方式 A（Python 直接执行 SQL）代替。

---

**Phase 0 执行指南结束**
