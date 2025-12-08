"""对账批次状态枚举对齐STATE_MACHINE.md

Revision ID: 20251117_reconciliation_status_align
Revises: 20251117_reconciliation_pk_bigserial
Create Date: 2025-11-17 10:30:00.000000

风险等级: 🟢 低
影响范围: reconciliation_batches.status
变更内容:
  旧枚举: pending, processing, completed, exception, resolved
  新枚举: draft, pending, reviewing, closed (符合STATE_MACHINE.md)
映射规则:
  pending → draft (初始草稿状态)
  processing → pending (处理中)
  completed → closed (已完成)
  exception → reviewing (异常需审核)
  resolved → closed (已解决)
前置条件:
  1. 已阅读 STATE_MACHINE.md §3.5.1
  2. 已统计当前各状态分布
"""
from alembic import op
import sqlalchemy as sa

revision = '20251117_reconciliation_status_align'
down_revision = '20251117_reconciliation_pk_bigserial'
branch_labels = None
depends_on = None


def upgrade():
    """
    状态枚举对齐流程:
    1. 添加status_legacy列保存原值
    2. 执行状态映射
    3. 更新CHECK约束
    """

    print("🔧 开始对齐reconciliation_batches.status枚举...")

    # Step 1: 添加备份列（保留7天观察期后可删除）
    print("  → 添加status_legacy备份列...")
    op.add_column(
        'reconciliation_batches',
        sa.Column('status_legacy', sa.String(20), nullable=True, comment='原status值（迁移备份）')
    )

    # Step 2: 备份当前status值
    print("  → 备份当前status值...")
    op.execute("UPDATE reconciliation_batches SET status_legacy = status")

    # Step 3: 执行状态映射
    print("  → 执行状态映射...")
    op.execute("""
        UPDATE reconciliation_batches
        SET status = CASE
            WHEN status = 'pending' THEN 'draft'
            WHEN status = 'processing' THEN 'pending'
            WHEN status = 'completed' THEN 'closed'
            WHEN status = 'exception' THEN 'reviewing'
            WHEN status = 'resolved' THEN 'closed'
            ELSE status  -- 未知状态保持不变（不应出现）
        END
    """)

    # Step 4: 更新CHECK约束
    print("  → 更新CHECK约束...")
    # TODO: 替换下面的约束名为实际数据库中的名称
    op.execute("ALTER TABLE reconciliation_batches DROP CONSTRAINT IF EXISTS check_batch_status")

    op.create_check_constraint(
        'check_batch_status',
        'reconciliation_batches',
        "status IN ('draft', 'pending', 'reviewing', 'closed')"
    )

    # Step 5: 验证迁移结果
    print("  → 验证迁移结果...")
    op.execute("""
        DO $$
        DECLARE
            invalid_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO invalid_count
            FROM reconciliation_batches
            WHERE status NOT IN ('draft', 'pending', 'reviewing', 'closed');

            IF invalid_count > 0 THEN
                RAISE EXCEPTION '发现 % 条非法status值，迁移失败！', invalid_count;
            END IF;

            RAISE NOTICE '✅ 状态枚举验证通过，无非法值';
        END $$;
    """)

    print("✅ 状态枚举对齐完成！")
    print("📊 建议执行以下SQL查看迁移结果:")
    print("   SELECT status, status_legacy, COUNT(*) FROM reconciliation_batches GROUP BY status, status_legacy;")


def downgrade():
    """
    从status_legacy恢复原状态值
    """

    print("⚠️ 开始回退状态枚举...")

    # Step 1: 恢复旧CHECK约束
    op.execute("ALTER TABLE reconciliation_batches DROP CONSTRAINT IF EXISTS check_batch_status")
    op.create_check_constraint(
        'check_batch_status',
        'reconciliation_batches',
        "status IN ('pending', 'processing', 'completed', 'exception', 'resolved')"
    )

    # Step 2: 从备份列恢复
    op.execute("UPDATE reconciliation_batches SET status = status_legacy WHERE status_legacy IS NOT NULL")

    # Step 3: 删除备份列
    op.drop_column('reconciliation_batches', 'status_legacy')

    print("✅ 回退完成")
