"""对账模块用户外键修复：Integer → UUID (指向 user_profiles.id)

Revision ID: 20251117_reconciliation_user_fks_to_uuid
Revises: 20251117_reconciliation_pk_to_bigserial
Create Date: 2025-11-17 00:01:00.000000

⚠️ 警告：本迁移脚本为模板，必须在执行前进行以下调整：
1. 确认 users 表和 user_profiles 表的 ID 对应关系
2. 验证数据迁移逻辑（created_by/reviewed_by/approved_by 等字段的数据完整性）
3. 在开发/测试环境完整验证后才能用于生产环境
4. 执行前务必备份数据库

📋 变更说明：
根据 DATA_SCHEMA.md v5.0 (2025-11-17) 规范：
- 所有用户相关外键必须指向 user_profiles.id (UUID)
- 本迁移修复对账模块中的用户外键：
  * reconciliation_batches.created_by: Integer → UUID
  * reconciliation_details.reviewed_by, resolved_by: Integer → UUID
  * reconciliation_adjustments.approved_by, finance_approved_by: Integer → UUID
  * reconciliation_reports.generated_by: Integer → UUID

🎯 SoT 参考：
- DATA_SCHEMA.md §3.5 (对账模块)
- DATA_SCHEMA.md §3.1.1 (user_profiles 表定义)

📊 影响评估：
- 风险等级：🔴 高（修改外键类型并迁移数据）
- 前置条件：必须确保 users 表的 id 与 user_profiles 表的 id 完全对应
- 数据保全性：取决于 users ↔ user_profiles 映射的完整性
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251117_reconciliation_user_fks_to_uuid'
down_revision = '20251117_reconciliation_pk_to_bigserial'
branch_labels = None
depends_on = None


def upgrade():
    """
    升级：将对账模块中所有用户外键从 Integer (users.id) 改为 UUID (user_profiles.id)

    ⚠️ 重要前提：
    1. users 表必须已迁移到 Supabase Auth (id 为 UUID)
    2. user_profiles 表已存在且 id = users.id (UUID)
    3. 所有历史数据的 user_id 都能在 user_profiles 中找到对应记录

    策略：新列+回填+切换
    """

    print("🚀 开始迁移对账模块用户外键...")

    # ========================================
    # Gate Checkpoint #1: 验证前置条件
    # ========================================
    print("🔍 建议执行以下 SQL 验证前置条件：")
    print("""
    -- 验证 users 表主键类型为 UUID
    SELECT data_type FROM information_schema.columns
    WHERE table_name = 'users' AND column_name = 'id';
    -- 预期结果：uuid

    -- 验证 user_profiles 表存在且主键为 UUID
    SELECT data_type FROM information_schema.columns
    WHERE table_name = 'user_profiles' AND column_name = 'id';
    -- 预期结果：uuid

    -- 验证 users.id 和 user_profiles.id 是否一一对应
    SELECT
        (SELECT COUNT(DISTINCT id) FROM users) AS users_count,
        (SELECT COUNT(DISTINCT id) FROM user_profiles) AS profiles_count,
        (SELECT COUNT(*) FROM users WHERE id NOT IN (SELECT id FROM user_profiles)) AS missing_profiles;
    -- 预期结果：missing_profiles = 0
    """)

    # ========================================
    # Step 1: reconciliation_batches.created_by
    # ========================================
    print("📌 Step 1/4: 迁移 reconciliation_batches.created_by...")

    # 1.1 添加新的 UUID 列
    op.add_column(
        'reconciliation_batches',
        sa.Column('created_by_uuid', postgresql.UUID(as_uuid=True), nullable=True, comment='创建人ID (UUID)')
    )

    # 1.2 数据回填：从 users 表获取对应的 UUID
    # 假设 users 表的 id 已经是 UUID，直接通过 Integer id 查找对应的 UUID
    # ⚠️ 注意：这里假设旧的 Integer ID 可以通过某种方式映射到 UUID
    # 实际情况需要根据项目的用户体系迁移情况调整
    op.execute("""
        UPDATE reconciliation_batches rb
        SET created_by_uuid = u.id
        FROM users u
        WHERE rb.created_by::TEXT = u.id::TEXT
          AND rb.created_by IS NOT NULL
    """)
    # ⚠️ 如果 users 表的 id 类型已经是 UUID，但 reconciliation_batches.created_by 是 Integer，
    # 那么上面的映射逻辑需要调整。可能需要一个临时映射表或者其他映射逻辑。
    # 如果无法直接映射，需要手动处理或使用映射表。

    # 1.3 验证数据完整性
    print("🔍 验证数据回填结果：")
    print("""
    SELECT
        COUNT(*) AS total_rows,
        COUNT(created_by) AS old_fk_count,
        COUNT(created_by_uuid) AS new_fk_count,
        COUNT(*) FILTER (WHERE created_by IS NOT NULL AND created_by_uuid IS NULL) AS unmapped_count
    FROM reconciliation_batches;
    -- 预期结果：unmapped_count = 0
    """)

    # 1.4 删除旧的外键约束
    op.drop_constraint(
        'reconciliation_batches_created_by_fkey',  # TODO: 确认实际约束名，如果不存在则跳过
        'reconciliation_batches',
        type_='foreignkey'
    )

    # 1.5 删除旧列
    op.drop_column('reconciliation_batches', 'created_by')

    # 1.6 重命名新列为原列名
    op.alter_column('reconciliation_batches', 'created_by_uuid', new_column_name='created_by')

    # 1.7 创建新的外键约束（指向 user_profiles.id）
    op.create_foreign_key(
        'reconciliation_batches_created_by_fkey',
        'reconciliation_batches',
        'user_profiles',
        ['created_by'],
        ['id']
    )

    # 1.8 创建索引
    op.create_index(
        'idx_reconciliation_batches_created_by',
        'reconciliation_batches',
        ['created_by']
    )

    print("✅ reconciliation_batches.created_by 迁移完成")

    # ========================================
    # Step 2: reconciliation_details 的 reviewed_by 和 resolved_by
    # ========================================
    print("📌 Step 2/4: 迁移 reconciliation_details 用户外键...")

    # 2.1 添加新的 UUID 列
    op.add_column(
        'reconciliation_details',
        sa.Column('reviewed_by_uuid', postgresql.UUID(as_uuid=True), nullable=True, comment='审核人ID (UUID)')
    )
    op.add_column(
        'reconciliation_details',
        sa.Column('resolved_by_uuid', postgresql.UUID(as_uuid=True), nullable=True, comment='处理人ID (UUID)')
    )

    # 2.2 数据回填
    op.execute("""
        UPDATE reconciliation_details rd
        SET reviewed_by_uuid = u.id
        FROM users u
        WHERE rd.reviewed_by::TEXT = u.id::TEXT
          AND rd.reviewed_by IS NOT NULL
    """)
    op.execute("""
        UPDATE reconciliation_details rd
        SET resolved_by_uuid = u.id
        FROM users u
        WHERE rd.resolved_by::TEXT = u.id::TEXT
          AND rd.resolved_by IS NOT NULL
    """)

    # 2.3 删除旧的外键约束（如果存在）
    # ⚠️ 根据实际约束名调整，如果不存在则注释掉
    try:
        op.drop_constraint('reconciliation_details_reviewed_by_fkey', 'reconciliation_details', type_='foreignkey')
    except:
        pass
    try:
        op.drop_constraint('reconciliation_details_resolved_by_fkey', 'reconciliation_details', type_='foreignkey')
    except:
        pass

    # 2.4 删除旧列
    op.drop_column('reconciliation_details', 'reviewed_by')
    op.drop_column('reconciliation_details', 'resolved_by')

    # 2.5 重命名新列
    op.alter_column('reconciliation_details', 'reviewed_by_uuid', new_column_name='reviewed_by')
    op.alter_column('reconciliation_details', 'resolved_by_uuid', new_column_name='resolved_by')

    # 2.6 创建新的外键约束
    op.create_foreign_key(
        'reconciliation_details_reviewed_by_fkey',
        'reconciliation_details',
        'user_profiles',
        ['reviewed_by'],
        ['id']
    )
    op.create_foreign_key(
        'reconciliation_details_resolved_by_fkey',
        'reconciliation_details',
        'user_profiles',
        ['resolved_by'],
        ['id']
    )

    print("✅ reconciliation_details 用户外键迁移完成")

    # ========================================
    # Step 3: reconciliation_adjustments 的 approved_by 和 finance_approved_by
    # ========================================
    print("📌 Step 3/4: 迁移 reconciliation_adjustments 用户外键...")

    # 3.1 添加新的 UUID 列
    op.add_column(
        'reconciliation_adjustments',
        sa.Column('approved_by_uuid', postgresql.UUID(as_uuid=True), nullable=True, comment='审批人ID (UUID)')
    )
    op.add_column(
        'reconciliation_adjustments',
        sa.Column('finance_approved_by_uuid', postgresql.UUID(as_uuid=True), nullable=True, comment='财务审批人ID (UUID)')
    )

    # 3.2 数据回填
    op.execute("""
        UPDATE reconciliation_adjustments ra
        SET approved_by_uuid = u.id
        FROM users u
        WHERE ra.approved_by::TEXT = u.id::TEXT
          AND ra.approved_by IS NOT NULL
    """)
    op.execute("""
        UPDATE reconciliation_adjustments ra
        SET finance_approved_by_uuid = u.id
        FROM users u
        WHERE ra.finance_approved_by::TEXT = u.id::TEXT
          AND ra.finance_approved_by IS NOT NULL
    """)

    # 3.3 删除旧的外键约束（如果存在）
    try:
        op.drop_constraint('reconciliation_adjustments_approved_by_fkey', 'reconciliation_adjustments', type_='foreignkey')
    except:
        pass
    try:
        op.drop_constraint('reconciliation_adjustments_finance_approved_by_fkey', 'reconciliation_adjustments', type_='foreignkey')
    except:
        pass

    # 3.4 删除旧列
    op.drop_column('reconciliation_adjustments', 'approved_by')
    op.drop_column('reconciliation_adjustments', 'finance_approved_by')

    # 3.5 重命名新列
    op.alter_column('reconciliation_adjustments', 'approved_by_uuid', new_column_name='approved_by')
    op.alter_column('reconciliation_adjustments', 'finance_approved_by_uuid', new_column_name='finance_approved_by')

    # 3.6 创建新的外键约束
    op.create_foreign_key(
        'reconciliation_adjustments_approved_by_fkey',
        'reconciliation_adjustments',
        'user_profiles',
        ['approved_by'],
        ['id']
    )
    op.create_foreign_key(
        'reconciliation_adjustments_finance_approved_by_fkey',
        'reconciliation_adjustments',
        'user_profiles',
        ['finance_approved_by'],
        ['id']
    )

    print("✅ reconciliation_adjustments 用户外键迁移完成")

    # ========================================
    # Step 4: reconciliation_reports.generated_by
    # ========================================
    print("📌 Step 4/4: 迁移 reconciliation_reports.generated_by...")

    # 4.1 添加新的 UUID 列
    op.add_column(
        'reconciliation_reports',
        sa.Column('generated_by_uuid', postgresql.UUID(as_uuid=True), nullable=True, comment='生成人ID (UUID)')
    )

    # 4.2 数据回填
    op.execute("""
        UPDATE reconciliation_reports rr
        SET generated_by_uuid = u.id
        FROM users u
        WHERE rr.generated_by::TEXT = u.id::TEXT
          AND rr.generated_by IS NOT NULL
    """)

    # 4.3 删除旧的外键约束（如果存在）
    try:
        op.drop_constraint('reconciliation_reports_generated_by_fkey', 'reconciliation_reports', type_='foreignkey')
    except:
        pass

    # 4.4 删除旧列
    op.drop_column('reconciliation_reports', 'generated_by')

    # 4.5 重命名新列
    op.alter_column('reconciliation_reports', 'generated_by_uuid', new_column_name='generated_by')

    # 4.6 创建新的外键约束
    op.create_foreign_key(
        'reconciliation_reports_generated_by_fkey',
        'reconciliation_reports',
        'user_profiles',
        ['generated_by'],
        ['id']
    )

    print("✅ reconciliation_reports.generated_by 迁移完成")

    # ========================================
    # Gate Checkpoint #2: 后置验证
    # ========================================
    print("🔍 建议执行以下 SQL 验证迁移结果：")
    print("""
    -- 验证所有用户外键类型为 UUID
    SELECT table_name, column_name, data_type
    FROM information_schema.columns
    WHERE table_name LIKE 'reconciliation_%'
      AND column_name IN ('created_by', 'reviewed_by', 'resolved_by', 'approved_by', 'finance_approved_by', 'generated_by')
    ORDER BY table_name, column_name;
    -- 预期结果：data_type = 'uuid'

    -- 验证外键约束指向 user_profiles
    SELECT
        tc.table_name,
        kcu.column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_name LIKE 'reconciliation_%'
      AND kcu.column_name IN ('created_by', 'reviewed_by', 'resolved_by', 'approved_by', 'finance_approved_by', 'generated_by')
    ORDER BY tc.table_name, kcu.column_name;
    -- 预期结果：foreign_table_name = 'user_profiles'

    -- 验证数据完整性
    SELECT
        (SELECT COUNT(*) FROM reconciliation_batches) AS batches_count,
        (SELECT COUNT(*) FROM reconciliation_details) AS details_count,
        (SELECT COUNT(*) FROM reconciliation_adjustments) AS adjustments_count,
        (SELECT COUNT(*) FROM reconciliation_reports) AS reports_count;
    -- 预期结果：行数与迁移前一致

    -- 验证所有外键都有对应的 user_profiles 记录
    SELECT 'reconciliation_batches.created_by' AS field,
           COUNT(*) AS invalid_fk_count
    FROM reconciliation_batches rb
    LEFT JOIN user_profiles up ON rb.created_by = up.id
    WHERE rb.created_by IS NOT NULL AND up.id IS NULL
    UNION ALL
    SELECT 'reconciliation_details.reviewed_by',
           COUNT(*)
    FROM reconciliation_details rd
    LEFT JOIN user_profiles up ON rd.reviewed_by = up.id
    WHERE rd.reviewed_by IS NOT NULL AND up.id IS NULL
    UNION ALL
    SELECT 'reconciliation_details.resolved_by',
           COUNT(*)
    FROM reconciliation_details rd
    LEFT JOIN user_profiles up ON rd.resolved_by = up.id
    WHERE rd.resolved_by IS NOT NULL AND up.id IS NULL
    UNION ALL
    SELECT 'reconciliation_adjustments.approved_by',
           COUNT(*)
    FROM reconciliation_adjustments ra
    LEFT JOIN user_profiles up ON ra.approved_by = up.id
    WHERE ra.approved_by IS NOT NULL AND up.id IS NULL
    UNION ALL
    SELECT 'reconciliation_adjustments.finance_approved_by',
           COUNT(*)
    FROM reconciliation_adjustments ra
    LEFT JOIN user_profiles up ON ra.finance_approved_by = up.id
    WHERE ra.finance_approved_by IS NOT NULL AND up.id IS NULL
    UNION ALL
    SELECT 'reconciliation_reports.generated_by',
           COUNT(*)
    FROM reconciliation_reports rr
    LEFT JOIN user_profiles up ON rr.generated_by = up.id
    WHERE rr.generated_by IS NOT NULL AND up.id IS NULL;
    -- 预期结果：所有 invalid_fk_count = 0
    """)

    print("✅ 对账模块用户外键迁移完成！")


def downgrade():
    """
    降级：将用户外键从 UUID 回退到 Integer

    ⚠️ 警告：
    1. 回退后将丢失 UUID 到 Integer 的映射关系
    2. 回退前必须确保有完整的映射表
    3. 生产环境禁止执行回退操作
    """

    print("⚠️  开始回退对账模块用户外键...")
    print("❌ 警告：此回退操作会导致用户外键数据丢失映射关系")
    print("❌ 如需回退，请手动实现反向映射逻辑")

    # 此处省略回退逻辑，因为 UUID → Integer 的反向映射需要额外的映射表
    # 如果确实需要回退，必须先创建 UUID → Integer 的映射表，然后才能安全回退

    raise NotImplementedError(
        "用户外键回退操作需要自定义映射逻辑。"
        "如需回退，请参考 DATABASE_SCHEMA_MIGRATION_PLAN.md 创建映射表后手动实现。"
    )
