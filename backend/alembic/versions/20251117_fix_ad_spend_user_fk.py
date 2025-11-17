"""修复ad_spend_daily用户外键类型不匹配 (Integer→UUID)

Revision ID: 20251117_fix_ad_spend_user_fk
Revises: 20251117_analyze_user_fk
Create Date: 2025-11-17 12:00:00.000000

风险等级: 🔴 高（不可逆，数据将被置NULL）
影响范围: ad_spend_daily.user_id, created_by, updated_by
执行策略: Strategy B - 类型转换 + 置NULL
前置条件:
  1. 已执行Rev 003分析，确认孤儿率可接受
  2. 已阅读MIGRATION_EXECUTION_GUIDE.md §4.3
  3. 已完成数据备份
  4. 业务方确认接受NULL值策略

⚠️ 重要说明:
  - 本迁移将删除user_id/created_by/updated_by的Integer值
  - 所有值将被设置为NULL
  - FK将重建为user_profiles.id (UUID)
  - 业务层需要重新建立用户关联
  - 此操作不可通过alembic downgrade回退
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '20251117_fix_ad_spend_user_fk'
down_revision = '20251117_analyze_user_fk'
branch_labels = None
depends_on = None


def upgrade():
    """
    ad_spend_daily用户FK类型修复流程:
    1. 备份当前Integer值到临时列
    2. 删除旧FK约束
    3. 修改列类型为UUID + 置NULL
    4. 重建FK到user_profiles.id
    5. 更新注释
    """

    print("🔴 开始修复ad_spend_daily用户外键类型...")
    print("⚠️  警告: 此操作不可逆！所有user_id/created_by/updated_by值将被置NULL")

    # ============ Step 1: 备份当前Integer值 ============
    print("  → 步骤1: 添加备份列...")
    op.add_column(
        'ad_spend_daily',
        sa.Column('user_id_legacy', sa.Integer(), nullable=True, comment='迁移前Integer值（仅供审计）')
    )
    op.add_column(
        'ad_spend_daily',
        sa.Column('created_by_legacy', sa.Integer(), nullable=True, comment='迁移前Integer值（仅供审计）')
    )
    op.add_column(
        'ad_spend_daily',
        sa.Column('updated_by_legacy', sa.Integer(), nullable=True, comment='迁移前Integer值（仅供审计）')
    )

    # 备份数据
    print("  → 备份当前Integer值...")
    op.execute("""
        UPDATE ad_spend_daily
        SET user_id_legacy = user_id,
            created_by_legacy = created_by,
            updated_by_legacy = updated_by
    """)

    # ============ Step 2: 删除旧FK约束 ============
    print("  → 步骤2: 删除旧FK约束...")
    # 注意: 约束名可能需要根据实际数据库调整
    op.drop_constraint('ad_spend_daily_user_id_fkey', 'ad_spend_daily', type_='foreignkey')
    op.drop_constraint('ad_spend_daily_created_by_fkey', 'ad_spend_daily', type_='foreignkey')
    op.drop_constraint('ad_spend_daily_updated_by_fkey', 'ad_spend_daily', type_='foreignkey')

    # ============ Step 3: 修改列类型 + 置NULL ============
    print("  → 步骤3: 修改列类型为UUID并置NULL...")

    # 3.1 user_id: Integer NOT NULL → UUID NULL
    op.execute("ALTER TABLE ad_spend_daily ALTER COLUMN user_id DROP NOT NULL")
    op.execute("ALTER TABLE ad_spend_daily ALTER COLUMN user_id DROP DEFAULT")
    op.execute("UPDATE ad_spend_daily SET user_id = NULL")  # 清空数据
    op.execute("ALTER TABLE ad_spend_daily ALTER COLUMN user_id TYPE UUID USING NULL::UUID")

    # 3.2 created_by: Integer NULL → UUID NULL
    op.execute("UPDATE ad_spend_daily SET created_by = NULL")
    op.execute("ALTER TABLE ad_spend_daily ALTER COLUMN created_by TYPE UUID USING NULL::UUID")

    # 3.3 updated_by: Integer NULL → UUID NULL
    op.execute("UPDATE ad_spend_daily SET updated_by = NULL")
    op.execute("ALTER TABLE ad_spend_daily ALTER COLUMN updated_by TYPE UUID USING NULL::UUID")

    # ============ Step 4: 重建FK约束 ============
    print("  → 步骤4: 重建FK到user_profiles.id...")

    # user_id暂时设为可空，业务层后续填充后可再改为NOT NULL
    op.create_foreign_key(
        'ad_spend_daily_user_id_fkey',
        'ad_spend_daily', 'user_profiles',
        ['user_id'], ['id'],
        ondelete='RESTRICT'
    )

    op.create_foreign_key(
        'ad_spend_daily_created_by_fkey',
        'ad_spend_daily', 'user_profiles',
        ['created_by'], ['id'],
        ondelete='SET NULL'
    )

    op.create_foreign_key(
        'ad_spend_daily_updated_by_fkey',
        'ad_spend_daily', 'user_profiles',
        ['updated_by'], ['id'],
        ondelete='SET NULL'
    )

    # ============ Step 5: 验证迁移结果 ============
    print("  → 步骤5: 验证迁移结果...")
    op.execute("""
        DO $$
        DECLARE
            total_records INTEGER;
            null_user_id INTEGER;
            null_created_by INTEGER;
            null_updated_by INTEGER;
            orphan_rate NUMERIC;
        BEGIN
            SELECT COUNT(*) INTO total_records FROM ad_spend_daily;
            SELECT COUNT(*) INTO null_user_id FROM ad_spend_daily WHERE user_id IS NULL;
            SELECT COUNT(*) INTO null_created_by FROM ad_spend_daily WHERE created_by IS NULL;
            SELECT COUNT(*) INTO null_updated_by FROM ad_spend_daily WHERE updated_by IS NULL;

            orphan_rate := CASE WHEN total_records > 0
                                THEN (null_user_id::NUMERIC / total_records * 100)
                                ELSE 0 END;

            RAISE NOTICE '========================================';
            RAISE NOTICE '📊 ad_spend_daily 用户FK迁移结果';
            RAISE NOTICE '========================================';
            RAISE NOTICE '总记录数: %', total_records;
            RAISE NOTICE 'user_id为NULL: % (%.2f%%)', null_user_id, orphan_rate;
            RAISE NOTICE 'created_by为NULL: %', null_created_by;
            RAISE NOTICE 'updated_by为NULL: %', null_updated_by;
            RAISE NOTICE '========================================';
            RAISE NOTICE '⚠️ 业务层需要重新建立用户关联！';
            RAISE NOTICE '参考legacy列恢复映射: user_id_legacy, created_by_legacy, updated_by_legacy';
        END $$;
    """)

    print("✅ ad_spend_daily用户FK类型修复完成！")
    print("📋 后续操作:")
    print("   1. 业务层实现用户关联重建逻辑")
    print("   2. 监控NULL值比例，确保逐步填充")
    print("   3. 7天观察期后可删除_legacy列")


def downgrade():
    """
    ⚠️ 不支持自动回退！

    原因:
    1. Integer值已被清空，无法从UUID恢复
    2. 即使有legacy列，也只是备份，不能作为主键引用

    回退策略:
    1. 从备份恢复整个ad_spend_daily表
    2. 或者执行以下手动步骤（需DBA介入）:
       - 从legacy列恢复Integer值
       - 修改列类型回Integer
       - 重建旧FK约束

    ⚠️ 强烈建议: 使用数据库备份回退，而非手动操作
    """

    raise NotImplementedError(
        "此迁移不支持自动回退！\n"
        "请使用数据库备份恢复，或参考 MIGRATION_EXECUTION_GUIDE.md §6.3 手动回退"
    )
