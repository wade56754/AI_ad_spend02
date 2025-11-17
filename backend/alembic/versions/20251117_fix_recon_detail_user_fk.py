"""修复reconciliation_details用户外键类型不匹配 (Integer→UUID)

Revision ID: 20251117_fix_recon_detail_user_fk
Revises: 20251117_fix_ad_spend_user_fk
Create Date: 2025-11-17 12:30:00.000000

风险等级: 🔴 高（不可逆，数据将被置NULL）
影响范围: reconciliation_details.reviewed_by, resolved_by
执行策略: Strategy B - 类型转换 + 置NULL
前置条件:
  1. 已执行Rev 003分析，确认孤儿率可接受
  2. 已完成ad_spend_daily修复（Rev 004）
  3. 已完成数据备份
  4. 业务方确认接受NULL值策略

⚠️ 重要说明:
  - 本迁移将删除reviewed_by/resolved_by的Integer值
  - 所有值将被设置为NULL
  - FK将重建为user_profiles.id (UUID)
  - 审核/处理记录的用户信息将丢失
  - 此操作不可通过alembic downgrade回退
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '20251117_fix_recon_detail_user_fk'
down_revision = '20251117_fix_ad_spend_user_fk'
branch_labels = None
depends_on = None


def upgrade():
    """
    reconciliation_details用户FK类型修复流程:
    1. 备份当前Integer值到临时列
    2. 删除旧FK约束
    3. 修改列类型为UUID + 置NULL
    4. 重建FK到user_profiles.id
    5. 更新注释
    """

    print("🔴 开始修复reconciliation_details用户外键类型...")
    print("⚠️  警告: 此操作不可逆！reviewed_by/resolved_by值将被置NULL")

    # ============ Step 1: 备份当前Integer值 ============
    print("  → 步骤1: 添加备份列...")
    op.add_column(
        'reconciliation_details',
        sa.Column('reviewed_by_legacy', sa.Integer(), nullable=True, comment='迁移前Integer值（仅供审计）')
    )
    op.add_column(
        'reconciliation_details',
        sa.Column('resolved_by_legacy', sa.Integer(), nullable=True, comment='迁移前Integer值（仅供审计）')
    )

    # 备份数据
    print("  → 备份当前Integer值...")
    op.execute("""
        UPDATE reconciliation_details
        SET reviewed_by_legacy = reviewed_by,
            resolved_by_legacy = resolved_by
    """)

    # ============ Step 2: 删除旧FK约束 ============
    print("  → 步骤2: 删除旧FK约束...")
    # 注意: 约束名可能需要根据实际数据库调整
    op.drop_constraint('reconciliation_details_reviewed_by_fkey', 'reconciliation_details', type_='foreignkey')
    op.drop_constraint('reconciliation_details_resolved_by_fkey', 'reconciliation_details', type_='foreignkey')

    # ============ Step 3: 修改列类型 + 置NULL ============
    print("  → 步骤3: 修改列类型为UUID并置NULL...")

    # 3.1 reviewed_by: Integer NULL → UUID NULL
    op.execute("UPDATE reconciliation_details SET reviewed_by = NULL")
    op.execute("ALTER TABLE reconciliation_details ALTER COLUMN reviewed_by TYPE UUID USING NULL::UUID")

    # 3.2 resolved_by: Integer NULL → UUID NULL
    op.execute("UPDATE reconciliation_details SET resolved_by = NULL")
    op.execute("ALTER TABLE reconciliation_details ALTER COLUMN resolved_by TYPE UUID USING NULL::UUID")

    # ============ Step 4: 重建FK约束 ============
    print("  → 步骤4: 重建FK到user_profiles.id...")

    op.create_foreign_key(
        'reconciliation_details_reviewed_by_fkey',
        'reconciliation_details', 'user_profiles',
        ['reviewed_by'], ['id'],
        ondelete='SET NULL'
    )

    op.create_foreign_key(
        'reconciliation_details_resolved_by_fkey',
        'reconciliation_details', 'user_profiles',
        ['resolved_by'], ['id'],
        ondelete='SET NULL'
    )

    # ============ Step 5: 验证迁移结果 ============
    print("  → 步骤5: 验证迁移结果...")
    op.execute("""
        DO $$
        DECLARE
            total_records INTEGER;
            null_reviewed INTEGER;
            null_resolved INTEGER;
            affected_reviews INTEGER;
            affected_resolutions INTEGER;
        BEGIN
            SELECT COUNT(*) INTO total_records FROM reconciliation_details;
            SELECT COUNT(*) INTO null_reviewed FROM reconciliation_details WHERE reviewed_by IS NULL;
            SELECT COUNT(*) INTO null_resolved FROM reconciliation_details WHERE resolved_by IS NULL;
            SELECT COUNT(*) INTO affected_reviews FROM reconciliation_details WHERE reviewed_by_legacy IS NOT NULL;
            SELECT COUNT(*) INTO affected_resolutions FROM reconciliation_details WHERE resolved_by_legacy IS NOT NULL;

            RAISE NOTICE '========================================';
            RAISE NOTICE '📊 reconciliation_details 用户FK迁移结果';
            RAISE NOTICE '========================================';
            RAISE NOTICE '总记录数: %', total_records;
            RAISE NOTICE 'reviewed_by为NULL: %', null_reviewed;
            RAISE NOTICE 'resolved_by为NULL: %', null_resolved;
            RAISE NOTICE '丢失的审核记录: %', affected_reviews;
            RAISE NOTICE '丢失的处理记录: %', affected_resolutions;
            RAISE NOTICE '========================================';
            RAISE NOTICE '⚠️ 审核/处理用户信息已丢失！';
            RAISE NOTICE '参考legacy列: reviewed_by_legacy, resolved_by_legacy';
        END $$;
    """)

    print("✅ reconciliation_details用户FK类型修复完成！")
    print("📋 后续操作:")
    print("   1. 审核日志应从audit_logs表恢复")
    print("   2. 监控对账流程，确保新数据正确填充UUID")
    print("   3. 7天观察期后可删除_legacy列")


def downgrade():
    """
    ⚠️ 不支持自动回退！

    原因:
    1. Integer值已被清空，无法从UUID恢复
    2. 审核/处理记录的用户关联已断开

    回退策略:
    1. 从备份恢复整个reconciliation_details表
    2. 或者从audit_logs表重建用户关联（需DBA介入）

    ⚠️ 强烈建议: 使用数据库备份回退
    """

    raise NotImplementedError(
        "此迁移不支持自动回退！\n"
        "请使用数据库备份恢复，或参考 MIGRATION_EXECUTION_GUIDE.md §6.3 手动回退"
    )
