"""修复reconciliation_adjustments和reconciliation_reports用户外键类型 (Integer→UUID)

Revision ID: 20251117_fix_recon_other_user_fk
Revises: 20251117_fix_recon_detail_user_fk
Create Date: 2025-11-17 13:00:00.000000

风险等级: 🔴 高（不可逆，数据将被置NULL）
影响范围:
  - reconciliation_adjustments: approved_by, finance_approved_by
  - reconciliation_reports: generated_by
执行策略: Strategy B - 类型转换 + 置NULL
前置条件:
  1. 已执行Rev 003-005，完成前序用户FK修复
  2. 已完成数据备份
  3. 业务方确认接受NULL值策略

⚠️ 重要说明:
  - 本迁移将删除审批人/生成人的Integer值
  - approved_by/finance_approved_by/generated_by将被置NULL
  - FK将重建为user_profiles.id (UUID)
  - 调整审批记录和报告生成记录的用户信息将丢失
  - 此操作不可通过alembic downgrade回退
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '20251117_fix_recon_other_user_fk'
down_revision = '20251117_fix_recon_detail_user_fk'
branch_labels = None
depends_on = None


def upgrade():
    """
    reconciliation其他表用户FK类型修复流程:

    表1: reconciliation_adjustments
      - approved_by (Integer, NOT NULL) → (UUID, NULL)
      - finance_approved_by (Integer, NULL) → (UUID, NULL)

    表2: reconciliation_reports
      - generated_by (Integer, NOT NULL) → (UUID, NULL)
    """

    print("🔴 开始修复reconciliation_adjustments和reconciliation_reports用户外键类型...")
    print("⚠️  警告: 此操作不可逆！审批人/生成人信息将被置NULL")

    # ============================================
    # 表1: reconciliation_adjustments
    # ============================================
    print("\n[表1/2] reconciliation_adjustments")

    # Step 1.1: 备份当前Integer值
    print("  → 步骤1: 添加备份列...")
    op.add_column(
        'reconciliation_adjustments',
        sa.Column('approved_by_legacy', sa.Integer(), nullable=True, comment='迁移前Integer值（仅供审计）')
    )
    op.add_column(
        'reconciliation_adjustments',
        sa.Column('finance_approved_by_legacy', sa.Integer(), nullable=True, comment='迁移前Integer值（仅供审计）')
    )

    print("  → 备份当前Integer值...")
    op.execute("""
        UPDATE reconciliation_adjustments
        SET approved_by_legacy = approved_by,
            finance_approved_by_legacy = finance_approved_by
    """)

    # Step 1.2: 删除旧FK约束
    print("  → 步骤2: 删除旧FK约束...")
    op.drop_constraint('reconciliation_adjustments_approved_by_fkey', 'reconciliation_adjustments', type_='foreignkey')
    op.drop_constraint('reconciliation_adjustments_finance_approved_by_fkey', 'reconciliation_adjustments', type_='foreignkey')

    # Step 1.3: 修改列类型 + 置NULL
    print("  → 步骤3: 修改列类型为UUID并置NULL...")

    # approved_by: Integer NOT NULL → UUID NULL (需先解除NOT NULL)
    op.execute("ALTER TABLE reconciliation_adjustments ALTER COLUMN approved_by DROP NOT NULL")
    op.execute("UPDATE reconciliation_adjustments SET approved_by = NULL")
    op.execute("ALTER TABLE reconciliation_adjustments ALTER COLUMN approved_by TYPE UUID USING NULL::UUID")

    # finance_approved_by: Integer NULL → UUID NULL
    op.execute("UPDATE reconciliation_adjustments SET finance_approved_by = NULL")
    op.execute("ALTER TABLE reconciliation_adjustments ALTER COLUMN finance_approved_by TYPE UUID USING NULL::UUID")

    # Step 1.4: 重建FK约束
    print("  → 步骤4: 重建FK到user_profiles.id...")
    op.create_foreign_key(
        'reconciliation_adjustments_approved_by_fkey',
        'reconciliation_adjustments', 'user_profiles',
        ['approved_by'], ['id'],
        ondelete='SET NULL'
    )

    op.create_foreign_key(
        'reconciliation_adjustments_finance_approved_by_fkey',
        'reconciliation_adjustments', 'user_profiles',
        ['finance_approved_by'], ['id'],
        ondelete='SET NULL'
    )

    # Step 1.5: 验证结果
    print("  → 步骤5: 验证迁移结果...")
    op.execute("""
        DO $$
        DECLARE
            total_adjustments INTEGER;
            null_approved INTEGER;
            null_finance_approved INTEGER;
        BEGIN
            SELECT COUNT(*) INTO total_adjustments FROM reconciliation_adjustments;
            SELECT COUNT(*) INTO null_approved FROM reconciliation_adjustments WHERE approved_by IS NULL;
            SELECT COUNT(*) INTO null_finance_approved FROM reconciliation_adjustments WHERE finance_approved_by IS NULL;

            RAISE NOTICE '========================================';
            RAISE NOTICE '📊 reconciliation_adjustments 用户FK迁移结果';
            RAISE NOTICE '========================================';
            RAISE NOTICE '总调整记录数: %', total_adjustments;
            RAISE NOTICE 'approved_by为NULL: %', null_approved;
            RAISE NOTICE 'finance_approved_by为NULL: %', null_finance_approved;
            RAISE NOTICE '========================================';
        END $$;
    """)

    # ============================================
    # 表2: reconciliation_reports
    # ============================================
    print("\n[表2/2] reconciliation_reports")

    # Step 2.1: 备份当前Integer值
    print("  → 步骤1: 添加备份列...")
    op.add_column(
        'reconciliation_reports',
        sa.Column('generated_by_legacy', sa.Integer(), nullable=True, comment='迁移前Integer值（仅供审计）')
    )

    print("  → 备份当前Integer值...")
    op.execute("""
        UPDATE reconciliation_reports
        SET generated_by_legacy = generated_by
    """)

    # Step 2.2: 删除旧FK约束
    print("  → 步骤2: 删除旧FK约束...")
    op.drop_constraint('reconciliation_reports_generated_by_fkey', 'reconciliation_reports', type_='foreignkey')

    # Step 2.3: 修改列类型 + 置NULL
    print("  → 步骤3: 修改列类型为UUID并置NULL...")

    # generated_by: Integer NOT NULL → UUID NULL
    op.execute("ALTER TABLE reconciliation_reports ALTER COLUMN generated_by DROP NOT NULL")
    op.execute("UPDATE reconciliation_reports SET generated_by = NULL")
    op.execute("ALTER TABLE reconciliation_reports ALTER COLUMN generated_by TYPE UUID USING NULL::UUID")

    # Step 2.4: 重建FK约束
    print("  → 步骤4: 重建FK到user_profiles.id...")
    op.create_foreign_key(
        'reconciliation_reports_generated_by_fkey',
        'reconciliation_reports', 'user_profiles',
        ['generated_by'], ['id'],
        ondelete='SET NULL'
    )

    # Step 2.5: 验证结果
    print("  → 步骤5: 验证迁移结果...")
    op.execute("""
        DO $$
        DECLARE
            total_reports INTEGER;
            null_generated INTEGER;
        BEGIN
            SELECT COUNT(*) INTO total_reports FROM reconciliation_reports;
            SELECT COUNT(*) INTO null_generated FROM reconciliation_reports WHERE generated_by IS NULL;

            RAISE NOTICE '========================================';
            RAISE NOTICE '📊 reconciliation_reports 用户FK迁移结果';
            RAISE NOTICE '========================================';
            RAISE NOTICE '总报告记录数: %', total_reports;
            RAISE NOTICE 'generated_by为NULL: %', null_generated;
            RAISE NOTICE '========================================';
        END $$;
    """)

    print("\n✅ 所有reconciliation表用户FK类型修复完成！")
    print("📋 后续操作:")
    print("   1. 审批记录应从audit_logs表恢复")
    print("   2. 报告生成记录应从系统日志恢复")
    print("   3. 监控新数据生成，确保正确填充UUID")
    print("   4. 7天观察期后可删除所有_legacy列")


def downgrade():
    """
    ⚠️ 不支持自动回退！

    原因:
    1. Integer值已被清空，无法从UUID恢复
    2. 审批记录和报告生成记录的用户关联已断开

    回退策略:
    1. 从备份恢复整个reconciliation_adjustments和reconciliation_reports表
    2. 或者从audit_logs表重建用户关联（需DBA介入）

    ⚠️ 强烈建议: 使用数据库备份回退
    """

    raise NotImplementedError(
        "此迁移不支持自动回退！\n"
        "请使用数据库备份恢复，或参考 MIGRATION_EXECUTION_GUIDE.md §6.3 手动回退"
    )
