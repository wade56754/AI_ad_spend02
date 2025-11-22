# 数据库主键类型迁移说明：BIGINT → UUID

## 概述

本文档说明将以下表的主键从 `BIGINT/BIGSERIAL` 迁移为 `UUID` 的操作步骤：

1. `channels` - 渠道主表
2. `channel_reviews` - 渠道评审记录
3. `channel_performance` - 渠道表现统计
4. `channel_account_requests` - 渠道开户申请
5. `ad_spend_daily` - 外部导入日消耗

同时，所有引用这些表的外键列（如 `ad_accounts.channel_id`）也需要改为 `UUID` 类型。

**参考文档**: `docs/core/DATA_SCHEMA.md`

---

## 受影响的表清单

| 表名 | 主键变更 | 外键依赖 | 备注 |
|------|---------|---------|------|
| `channels` | BIGINT → UUID | 无 | 根表，其他表依赖它 |
| `channel_reviews` | BIGINT → UUID | `channel_id` → `channels.id` | 依赖 channels |
| `channel_performance` | BIGINT → UUID | `channel_id` → `channels.id` | 依赖 channels |
| `channel_account_requests` | BIGINT → UUID | `channel_id` → `channels.id` | 依赖 channels |
| `ad_spend_daily` | BIGINT → UUID | 无 | 独立表 |
| `ad_accounts` | 不变（BIGSERIAL） | `channel_id` → `channels.id` (BIGINT → UUID) | 仅外键变更 |

---

## 环境说明

### 开发/测试环境

如果数据库中没有正式数据，可以直接重建表结构：

1. 使用 `backend/migrations/001_uuid_primary_keys.sql` 脚本重建表
2. 或使用 Alembic 自动迁移（推荐）

### 生产环境

如果数据库中已有数据，必须进行安全迁移：

1. **数据备份**：完整备份数据库
2. **数据导出**：导出相关表的数据
3. **Schema 迁移**：按顺序执行迁移步骤
4. **数据导入**：将数据导入新结构
5. **验证**：验证数据完整性和外键关系

---

## 迁移步骤（生产环境）

### 阶段 1：准备工作

```sql
-- 1. 启用 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. 备份相关表数据（示例）
COPY channels TO '/backup/channels.csv' CSV HEADER;
COPY channel_reviews TO '/backup/channel_reviews.csv' CSV HEADER;
COPY channel_performance TO '/backup/channel_performance.csv' CSV HEADER;
COPY channel_account_requests TO '/backup/channel_account_requests.csv' CSV HEADER;
COPY ad_spend_daily TO '/backup/ad_spend_daily.csv' CSV HEADER;
COPY ad_accounts TO '/backup/ad_accounts.csv' CSV HEADER;
```

### 阶段 2：迁移 channels 表

```sql
-- 1. 创建新表结构（UUID 主键）
CREATE TABLE channels_new (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL,
    channel_code VARCHAR(20) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'inactive')),
    country VARCHAR(10),
    notes TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. 创建 ID 映射表（旧 BIGINT → 新 UUID）
CREATE TEMP TABLE channel_id_mapping (
    old_id BIGINT,
    new_id UUID
);

-- 3. 迁移数据并生成映射
INSERT INTO channels_new (name, channel_code, status, country, notes, created_by, created_at, updated_at)
SELECT name, channel_code, status, country, notes, created_by, created_at, updated_at
FROM channels;

INSERT INTO channel_id_mapping (old_id, new_id)
SELECT 
    c.id AS old_id,
    cn.id AS new_id
FROM channels c
JOIN channels_new cn ON c.channel_code = cn.channel_code;

-- 4. 删除旧表并重命名新表
DROP TABLE channels CASCADE;
ALTER TABLE channels_new RENAME TO channels;

-- 5. 重建索引
CREATE INDEX idx_channels_code ON channels(channel_code);
CREATE INDEX idx_channels_status ON channels(status);
CREATE INDEX idx_channels_created_at ON channels(created_at);
```

### 阶段 3：迁移依赖表（channel_reviews, channel_performance, channel_account_requests）

```sql
-- channel_reviews 迁移
CREATE TABLE channel_reviews_new (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    reviewer_id UUID REFERENCES users(id) ON DELETE SET NULL,
    review_status VARCHAR(20) NOT NULL,
    review_notes TEXT,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO channel_reviews_new (channel_id, reviewer_id, review_status, review_notes, reviewed_at, created_at, updated_at)
SELECT 
    m.new_id AS channel_id,
    cr.reviewer_id,
    cr.review_status,
    cr.review_notes,
    cr.reviewed_at,
    cr.created_at,
    cr.updated_at
FROM channel_reviews cr
JOIN channel_id_mapping m ON cr.channel_id = m.old_id;

DROP TABLE channel_reviews CASCADE;
ALTER TABLE channel_reviews_new RENAME TO channel_reviews;

-- channel_performance 迁移（类似）
-- channel_account_requests 迁移（类似）
```

### 阶段 4：迁移 ad_spend_daily 表

```sql
-- ad_spend_daily 迁移（不依赖其他表，可直接迁移）
CREATE TABLE ad_spend_daily_new (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ad_account_code VARCHAR(50) NOT NULL,
    spend_date DATE NOT NULL,
    -- ... 其他字段
    UNIQUE(ad_account_code, spend_date)
);

INSERT INTO ad_spend_daily_new (ad_account_code, spend_date, ...)
SELECT ad_account_code, spend_date, ... FROM ad_spend_daily;

DROP TABLE ad_spend_daily CASCADE;
ALTER TABLE ad_spend_daily_new RENAME TO ad_spend_daily;
```

### 阶段 5：修复 ad_accounts.channel_id 外键

```sql
-- 1. 添加新的 UUID 列
ALTER TABLE ad_accounts ADD COLUMN channel_id_new UUID;

-- 2. 根据映射表填充新列
UPDATE ad_accounts aa
SET channel_id_new = m.new_id
FROM channel_id_mapping m
WHERE aa.channel_id = m.old_id;

-- 3. 删除旧列并重命名新列
ALTER TABLE ad_accounts DROP CONSTRAINT IF EXISTS ad_accounts_channel_id_fkey;
ALTER TABLE ad_accounts DROP COLUMN channel_id;
ALTER TABLE ad_accounts RENAME COLUMN channel_id_new TO channel_id;
ALTER TABLE ad_accounts ALTER COLUMN channel_id SET NOT NULL;

-- 4. 添加外键约束
ALTER TABLE ad_accounts ADD CONSTRAINT ad_accounts_channel_id_fkey 
    FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE;

-- 5. 重建索引
CREATE INDEX idx_ad_accounts_channel_id ON ad_accounts(channel_id);
```

---

## Alembic 迁移（推荐）

如果使用 Alembic，可以生成自动迁移脚本：

```bash
# 1. 修改 ORM 模型（已完成）
# backend/models/core/channel.py
# backend/models/accounts/account_request.py
# backend/models/workflow/ad_spend.py
# backend/models/accounts/ad_account.py

# 2. 生成迁移脚本
alembic revision --autogenerate -m "migrate channel tables to UUID primary keys"

# 3. 检查生成的迁移脚本，手动调整数据迁移逻辑

# 4. 执行迁移
alembic upgrade head
```

---

## 回滚方案

如果迁移失败，可以回滚：

1. 恢复数据库备份
2. 或按照相反顺序执行 DROP/CREATE 操作

**注意**：回滚前确保已备份所有数据。

---

## 验证清单

迁移完成后，请验证以下内容：

- [ ] 所有表的主键类型为 UUID
- [ ] 所有外键引用类型匹配（UUID → UUID, BIGINT → BIGINT）
- [ ] 数据完整性（记录数、关键字段值）
- [ ] 索引已重建
- [ ] 外键约束正常
- [ ] ORM 模型与数据库 Schema 一致

验证 SQL：

```sql
-- 检查主键类型
SELECT 
    table_name,
    column_name,
    data_type,
    column_default
FROM information_schema.columns
WHERE table_name IN ('channels', 'channel_reviews', 'channel_performance', 
                     'channel_account_requests', 'ad_spend_daily')
  AND column_name = 'id'
ORDER BY table_name;

-- 检查外键类型
SELECT 
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    c.data_type AS column_data_type,
    fc.data_type AS foreign_column_data_type
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.columns AS c
  ON c.table_name = tc.table_name AND c.column_name = kcu.column_name
JOIN information_schema.columns AS fc
  ON fc.table_name = ccu.table_name AND fc.column_name = ccu.column_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND (tc.table_name = 'ad_accounts' AND kcu.column_name = 'channel_id'
       OR tc.table_name IN ('channel_reviews', 'channel_performance', 'channel_account_requests'))
ORDER BY tc.table_name, kcu.column_name;
```

---

## 影响范围

### ORM 模型

以下模型文件已更新为 UUID 主键：

- `backend/models/core/channel.py` - Channel, ChannelReview, ChannelPerformance
- `backend/models/accounts/account_request.py` - ChannelAccountRequest
- `backend/models/workflow/ad_spend.py` - AdSpendDaily
- `backend/models/accounts/ad_account.py` - AdAccount.channel_id 改为 UUID

### API 端点

以下 API 端点可能受到影响：

- `/api/v1/channels/*` - 渠道相关接口
- `/api/v1/channel-requests/*` - 渠道申请接口
- `/api/v1/ad-spend/*` - 消耗数据接口
- `/api/v1/ad-accounts/*` - 账户接口（channel_id 参数类型）

### 前端代码

如果前端代码中硬编码了这些表的 ID 类型（如 TypeScript 类型定义），需要同步更新。

---

## 注意事项

1. **数据映射**：如果旧数据中有 BIGINT ID，需要创建映射表以确保外键关系正确
2. **API 兼容性**：UUID 格式的字符串长度与 BIGINT 不同，需要确认 API 兼容性
3. **性能考虑**：UUID 索引性能可能略低于 BIGINT，但对于这些表通常不是瓶颈
4. **唯一性**：确保 `channel_code` 等业务唯一字段在迁移过程中保持不变

---

## 完成标志

✅ 所有 ORM 模型已更新  
✅ 数据库 Schema 已迁移  
✅ 数据验证通过  
✅ 索引和外键约束正常  
✅ API 测试通过  

---

**最后更新**: 2025-01-XX  
**维护者**: 数据库架构团队

