"""对账模块主键类型迁移：Integer → BIGSERIAL

Revision ID: 20251117_reconciliation_pk_to_bigserial
Revises: 20250115_add_missing_core_models_v3
Create Date: 2025-11-17 00:00:00.000000

⚠️ 警告：本迁移脚本为模板，必须在执行前进行以下调整：
1. 确认当前数据库中约束名、索引名、序列名（使用 \\d+ table_name 查询）
2. 评估数据量，若 > 10万行需使用生产环境零停机策略
3. 在开发/测试环境完整验证后才能用于生产环境
4. 执行前务必备份数据库

📋 变更说明：
根据 DATA_SCHEMA.md v5.0 (2025-11-17) 规范：
- 核心业务表主键统一使用 BIGSERIAL
- 本迁移修复对账模块4个表的主键类型：
  * reconciliation_batches
  * reconciliation_details
  * reconciliation_adjustments
  * reconciliation_reports

🎯 SoT 参考：
- DATA_SCHEMA.md §3.5 (对账模块)
- DATABASE_SCHEMA_MIGRATION_PLAN.md v2.1

📊 影响评估：
- 风险等级：🟡 中等（修改主键类型，影响外键关系）
- 预计停机时间：开发环境 < 1分钟，生产环境需评估
- 数据保全性：100%（仅修改类型，不丢失数据）
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251117_reconciliation_pk_to_bigserial'
down_revision = '20250115_add_missing_core_models_v3'
branch_labels = None
depends_on = None


def upgrade():
    """
    升级：将对账模块4个表的主键从 Integer 修改为 BIGSERIAL (BIGINT)

    策略：开发/测试环境使用直接 ALTER 方式
    注意：生产环境若数据量大（>10万行）需使用影子表策略，参考 DATABASE_SCHEMA_MIGRATION_PLAN.md
    """

    # ========================================
    # Gate Checkpoint #1: 前置验证
    # ========================================
    # 建议执行前手动运行以下 SQL 验证：
    # SELECT COUNT(*) FROM reconciliation_batches;
    # SELECT COUNT(*) FROM reconciliation_details;
    # SELECT COUNT(*) FROM reconciliation_adjustments;
    # SELECT COUNT(*) FROM reconciliation_reports;
    #
    # 若任一表 > 10万行，强烈建议使用生产环境零停机策略

    print("🚀 开始迁移对账模块主键类型...")

    # ========================================
    # Step 1: reconciliation_batches 主键迁移
    # ========================================
    print("📌 Step 1/4: 迁移 reconciliation_batches 主键...")

    # 1.1 删除依赖此主键的外键约束（需要先记录，迁移后重建）
    # ⚠️ 注意：以下约束名需要根据实际数据库调整！
    # 使用 \d+ reconciliation_details 查看实际约束名
    op.drop_constraint(
        'reconciliation_details_batch_id_fkey',  # TODO: 替换为实际约束名
        'reconciliation_details',
        type_='foreignkey'
    )
    op.drop_constraint(
        'reconciliation_adjustments_batch_id_fkey',  # TODO: 替换为实际约束名
        'reconciliation_adjustments',
        type_='foreignkey'
    )
    op.drop_constraint(
        'reconciliation_reports_batch_id_fkey',  # TODO: 替换为实际约束名
        'reconciliation_reports',
        type_='foreignkey'
    )

    # 1.2 修改主键类型和序列类型
    op.execute("ALTER TABLE reconciliation_batches ALTER COLUMN id TYPE BIGINT")
    # 调整序列类型（如果使用了 SERIAL）
    op.execute("ALTER SEQUENCE reconciliation_batches_id_seq AS BIGINT")  # TODO: 确认序列名

    # 1.3 同步修改外键列类型
    op.execute("ALTER TABLE reconciliation_details ALTER COLUMN batch_id TYPE BIGINT")
    op.execute("ALTER TABLE reconciliation_adjustments ALTER COLUMN batch_id TYPE BIGINT")
    op.execute("ALTER TABLE reconciliation_reports ALTER COLUMN batch_id TYPE BIGINT")

    # 1.4 重建外键约束（使用 BIGINT 类型）
    op.create_foreign_key(
        'reconciliation_details_batch_id_fkey',  # TODO: 使用原约束名或新名称
        'reconciliation_details',
        'reconciliation_batches',
        ['batch_id'],
        ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'reconciliation_adjustments_batch_id_fkey',
        'reconciliation_adjustments',
        'reconciliation_batches',
        ['batch_id'],
        ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'reconciliation_reports_batch_id_fkey',
        'reconciliation_reports',
        'reconciliation_batches',
        ['batch_id'],
        ['id']
    )

    print("✅ reconciliation_batches 主键迁移完成")

    # ========================================
    # Step 2: reconciliation_details 主键迁移
    # ========================================
    print("📌 Step 2/4: 迁移 reconciliation_details 主键...")

    # 2.1 删除依赖此主键的外键约束
    op.drop_constraint(
        'reconciliation_adjustments_detail_id_fkey',  # TODO: 替换为实际约束名
        'reconciliation_adjustments',
        type_='foreignkey'
    )

    # 2.2 修改主键类型
    op.execute("ALTER TABLE reconciliation_details ALTER COLUMN id TYPE BIGINT")
    op.execute("ALTER SEQUENCE reconciliation_details_id_seq AS BIGINT")  # TODO: 确认序列名

    # 2.3 同步修改外键列类型
    op.execute("ALTER TABLE reconciliation_adjustments ALTER COLUMN detail_id TYPE BIGINT")

    # 2.4 重建外键约束
    op.create_foreign_key(
        'reconciliation_adjustments_detail_id_fkey',
        'reconciliation_adjustments',
        'reconciliation_details',
        ['detail_id'],
        ['id'],
        ondelete='CASCADE'
    )

    print("✅ reconciliation_details 主键迁移完成")

    # ========================================
    # Step 3: reconciliation_adjustments 主键迁移
    # ========================================
    print("📌 Step 3/4: 迁移 reconciliation_adjustments 主键...")

    # 3.1 修改主键类型（无外键依赖）
    op.execute("ALTER TABLE reconciliation_adjustments ALTER COLUMN id TYPE BIGINT")
    op.execute("ALTER SEQUENCE reconciliation_adjustments_id_seq AS BIGINT")  # TODO: 确认序列名

    print("✅ reconciliation_adjustments 主键迁移完成")

    # ========================================
    # Step 4: reconciliation_reports 主键迁移
    # ========================================
    print("📌 Step 4/4: 迁移 reconciliation_reports 主键...")

    # 4.1 修改主键类型（无外键依赖）
    op.execute("ALTER TABLE reconciliation_reports ALTER COLUMN id TYPE BIGINT")
    op.execute("ALTER SEQUENCE reconciliation_reports_id_seq AS BIGINT")  # TODO: 确认序列名

    print("✅ reconciliation_reports 主键迁移完成")

    # ========================================
    # Gate Checkpoint #2: 后置验证
    # ========================================
    print("🔍 建议执行以下 SQL 验证迁移结果：")
    print("""
    -- 验证主键类型
    SELECT table_name, column_name, data_type
    FROM information_schema.columns
    WHERE table_name IN (
        'reconciliation_batches',
        'reconciliation_details',
        'reconciliation_adjustments',
        'reconciliation_reports'
    )
    AND column_name = 'id';
    -- 预期结果：data_type = 'bigint'

    -- 验证外键类型
    SELECT table_name, column_name, data_type
    FROM information_schema.columns
    WHERE (table_name = 'reconciliation_details' AND column_name = 'batch_id')
       OR (table_name = 'reconciliation_adjustments' AND column_name IN ('batch_id', 'detail_id'))
       OR (table_name = 'reconciliation_reports' AND column_name = 'batch_id');
    -- 预期结果：data_type = 'bigint'

    -- 验证外键约束存在
    SELECT conname, conrelid::regclass AS table_name, confrelid::regclass AS referenced_table
    FROM pg_constraint
    WHERE conname LIKE '%reconciliation%batch_id%' OR conname LIKE '%reconciliation%detail_id%';
    -- 预期结果：所有外键约束都应存在

    -- 验证数据完整性
    SELECT
        (SELECT COUNT(*) FROM reconciliation_batches) AS batches_count,
        (SELECT COUNT(*) FROM reconciliation_details) AS details_count,
        (SELECT COUNT(*) FROM reconciliation_adjustments) AS adjustments_count,
        (SELECT COUNT(*) FROM reconciliation_reports) AS reports_count;
    -- 预期结果：行数与迁移前一致
    """)

    print("✅ 对账模块主键类型迁移完成！")


def downgrade():
    """
    降级：将主键类型从 BIGSERIAL 回退到 Integer

    ⚠️ 警告：
    1. 若 id 值超过 2147483647，回退将失败
    2. 回退前必须检查最大 id 值
    3. 生产环境慎用回退操作
    """

    print("⚠️  开始回退对账模块主键类型...")

    # 验证是否可以安全回退
    print("🔍 建议执行以下 SQL 验证是否可以安全回退：")
    print("""
    SELECT
        'reconciliation_batches' AS table_name,
        MAX(id) AS max_id,
        CASE WHEN MAX(id) > 2147483647 THEN '❌ 不可回退' ELSE '✅ 可回退' END AS rollback_safe
    FROM reconciliation_batches
    UNION ALL
    SELECT 'reconciliation_details', MAX(id),
        CASE WHEN MAX(id) > 2147483647 THEN '❌ 不可回退' ELSE '✅ 可回退' END
    FROM reconciliation_details
    UNION ALL
    SELECT 'reconciliation_adjustments', MAX(id),
        CASE WHEN MAX(id) > 2147483647 THEN '❌ 不可回退' ELSE '✅ 可回退' END
    FROM reconciliation_adjustments
    UNION ALL
    SELECT 'reconciliation_reports', MAX(id),
        CASE WHEN MAX(id) > 2147483647 THEN '❌ 不可回退' ELSE '✅ 可回退' END
    FROM reconciliation_reports;
    """)

    # Step 4 回退: reconciliation_reports
    print("📌 Step 1/4: 回退 reconciliation_reports...")
    op.execute("ALTER TABLE reconciliation_reports ALTER COLUMN id TYPE INTEGER")
    op.execute("ALTER SEQUENCE reconciliation_reports_id_seq AS INTEGER")

    # Step 3 回退: reconciliation_adjustments
    print("📌 Step 2/4: 回退 reconciliation_adjustments...")
    op.execute("ALTER TABLE reconciliation_adjustments ALTER COLUMN id TYPE INTEGER")
    op.execute("ALTER SEQUENCE reconciliation_adjustments_id_seq AS INTEGER")

    # Step 2 回退: reconciliation_details
    print("📌 Step 3/4: 回退 reconciliation_details...")
    op.drop_constraint('reconciliation_adjustments_detail_id_fkey', 'reconciliation_adjustments', type_='foreignkey')
    op.execute("ALTER TABLE reconciliation_details ALTER COLUMN id TYPE INTEGER")
    op.execute("ALTER SEQUENCE reconciliation_details_id_seq AS INTEGER")
    op.execute("ALTER TABLE reconciliation_adjustments ALTER COLUMN detail_id TYPE INTEGER")
    op.create_foreign_key(
        'reconciliation_adjustments_detail_id_fkey',
        'reconciliation_adjustments',
        'reconciliation_details',
        ['detail_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Step 1 回退: reconciliation_batches
    print("📌 Step 4/4: 回退 reconciliation_batches...")
    op.drop_constraint('reconciliation_details_batch_id_fkey', 'reconciliation_details', type_='foreignkey')
    op.drop_constraint('reconciliation_adjustments_batch_id_fkey', 'reconciliation_adjustments', type_='foreignkey')
    op.drop_constraint('reconciliation_reports_batch_id_fkey', 'reconciliation_reports', type_='foreignkey')

    op.execute("ALTER TABLE reconciliation_batches ALTER COLUMN id TYPE INTEGER")
    op.execute("ALTER SEQUENCE reconciliation_batches_id_seq AS INTEGER")
    op.execute("ALTER TABLE reconciliation_details ALTER COLUMN batch_id TYPE INTEGER")
    op.execute("ALTER TABLE reconciliation_adjustments ALTER COLUMN batch_id TYPE INTEGER")
    op.execute("ALTER TABLE reconciliation_reports ALTER COLUMN batch_id TYPE INTEGER")

    op.create_foreign_key(
        'reconciliation_details_batch_id_fkey',
        'reconciliation_details',
        'reconciliation_batches',
        ['batch_id'],
        ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'reconciliation_adjustments_batch_id_fkey',
        'reconciliation_adjustments',
        'reconciliation_batches',
        ['batch_id'],
        ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'reconciliation_reports_batch_id_fkey',
        'reconciliation_reports',
        'reconciliation_batches',
        ['batch_id'],
        ['id']
    )

    print("✅ 回退完成！")
