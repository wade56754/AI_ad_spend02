"""对账模块主键Integer→BIGSERIAL迁移

Revision ID: 20251117_reconciliation_pk_bigserial
Revises: 20251115_add_reconciliation_indexes
Create Date: 2025-11-17 10:00:00.000000

风险等级: 🟡 中等
影响范围: reconciliation_batches, reconciliation_details,
          reconciliation_adjustments, reconciliation_reports
执行策略: Dev/Test环境直接ALTER,生产环境使用影子表
前置条件:
  1. 确认4个表的最大id值 < 2147483647 (Integer上限)
  2. 确认无正在运行的长事务
  3. 已执行全库备份
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251117_reconciliation_pk_bigserial'
down_revision = '20251115_add_reconciliation_indexes'  # TODO: 替换为实际的前一个revision
branch_labels = None
depends_on = None


def upgrade():
    """
    将4个reconciliation表的主键从Integer升级为BIGSERIAL

    执行顺序（重要！必须按依赖关系处理）:
    1. reconciliation_batches (无依赖)
    2. reconciliation_details (依赖batches)
    3. reconciliation_adjustments (依赖batches和details)
    4. reconciliation_reports (依赖batches)
    """

    # ============ 表1: reconciliation_batches ============
    print("🔧 开始迁移 reconciliation_batches...")

    # Step 1: 修改主键类型
    op.execute("ALTER TABLE reconciliation_batches ALTER COLUMN id TYPE BIGINT")

    # Step 2: 修改序列类型
    op.execute("ALTER SEQUENCE reconciliation_batches_id_seq AS BIGINT")

    # Step 3: 重置序列起始值（可选，确保序列正确）
    op.execute("""
        SELECT setval('reconciliation_batches_id_seq',
                     COALESCE((SELECT MAX(id) FROM reconciliation_batches), 1))
    """)

    print("✅ reconciliation_batches 主键迁移完成")

    # ============ 表2: reconciliation_details ============
    print("🔧 开始迁移 reconciliation_details...")

    # Step 1: 修改外键列类型（必须先于主键，因为FK约束）
    op.execute("ALTER TABLE reconciliation_details ALTER COLUMN batch_id TYPE BIGINT")

    # Step 2: 修改主键类型
    op.execute("ALTER TABLE reconciliation_details ALTER COLUMN id TYPE BIGINT")

    # Step 3: 修改序列
    op.execute("ALTER SEQUENCE reconciliation_details_id_seq AS BIGINT")
    op.execute("""
        SELECT setval('reconciliation_details_id_seq',
                     COALESCE((SELECT MAX(id) FROM reconciliation_details), 1))
    """)

    print("✅ reconciliation_details 主键迁移完成")

    # ============ 表3: reconciliation_adjustments ============
    print("🔧 开始迁移 reconciliation_adjustments...")

    # Step 1: 修改外键列
    op.execute("ALTER TABLE reconciliation_adjustments ALTER COLUMN batch_id TYPE BIGINT")
    op.execute("ALTER TABLE reconciliation_adjustments ALTER COLUMN detail_id TYPE BIGINT")

    # Step 2: 修改主键
    op.execute("ALTER TABLE reconciliation_adjustments ALTER COLUMN id TYPE BIGINT")

    # Step 3: 修改序列
    op.execute("ALTER SEQUENCE reconciliation_adjustments_id_seq AS BIGINT")
    op.execute("""
        SELECT setval('reconciliation_adjustments_id_seq',
                     COALESCE((SELECT MAX(id) FROM reconciliation_adjustments), 1))
    """)

    print("✅ reconciliation_adjustments 主键迁移完成")

    # ============ 表4: reconciliation_reports ============
    print("🔧 开始迁移 reconciliation_reports...")

    # Step 1: 修改外键列
    op.execute("ALTER TABLE reconciliation_reports ALTER COLUMN batch_id TYPE BIGINT")

    # Step 2: 修改主键
    op.execute("ALTER TABLE reconciliation_reports ALTER COLUMN id TYPE BIGINT")

    # Step 3: 修改序列
    op.execute("ALTER SEQUENCE reconciliation_reports_id_seq AS BIGINT")
    op.execute("""
        SELECT setval('reconciliation_reports_id_seq',
                     COALESCE((SELECT MAX(id) FROM reconciliation_reports), 1))
    """)

    print("✅ reconciliation_reports 主键迁移完成")
    print("🎉 所有reconciliation表主键迁移完成！")


def downgrade():
    """
    回退到Integer主键

    ⚠️ 警告: 仅在以下情况支持回退:
    1. 所有id值仍在Integer范围内 (< 2147483647)
    2. 未有业务代码依赖BIGINT特性
    """

    # 按相反顺序回退
    print("⚠️ 开始回退主键类型...")

    # 表4
    op.execute("ALTER SEQUENCE reconciliation_reports_id_seq AS INTEGER")
    op.execute("ALTER TABLE reconciliation_reports ALTER COLUMN id TYPE INTEGER")
    op.execute("ALTER TABLE reconciliation_reports ALTER COLUMN batch_id TYPE INTEGER")

    # 表3
    op.execute("ALTER SEQUENCE reconciliation_adjustments_id_seq AS INTEGER")
    op.execute("ALTER TABLE reconciliation_adjustments ALTER COLUMN id TYPE INTEGER")
    op.execute("ALTER TABLE reconciliation_adjustments ALTER COLUMN detail_id TYPE INTEGER")
    op.execute("ALTER TABLE reconciliation_adjustments ALTER COLUMN batch_id TYPE INTEGER")

    # 表2
    op.execute("ALTER SEQUENCE reconciliation_details_id_seq AS INTEGER")
    op.execute("ALTER TABLE reconciliation_details ALTER COLUMN id TYPE INTEGER")
    op.execute("ALTER TABLE reconciliation_details ALTER COLUMN batch_id TYPE INTEGER")

    # 表1
    op.execute("ALTER SEQUENCE reconciliation_batches_id_seq AS INTEGER")
    op.execute("ALTER TABLE reconciliation_batches ALTER COLUMN id TYPE INTEGER")

    print("✅ 回退完成")
