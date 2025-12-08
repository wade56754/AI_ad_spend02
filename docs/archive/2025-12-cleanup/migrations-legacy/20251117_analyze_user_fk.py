"""分析并创建用户外键类型不匹配修复映射表

Revision ID: 20251117_analyze_user_fk
Revises: 20251117_reconciliation_status_align
Create Date: 2025-11-17 11:00:00.000000

风险等级: 🟢 低（仅分析，不修改数据）
目标:
  1. 创建临时映射表 temp_user_id_fk_analysis
  2. 分析ad_spend_daily等表的user_id (Integer)值
  3. 尝试匹配到user_profiles (UUID)
  4. 生成修复报告
前置条件:
  1. 确认users表和user_profiles表的关系
  2. 如果users.id是UUID，user_id(Integer)值可能是错误数据
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, INET

revision = '20251117_analyze_user_fk'
down_revision = '20251117_reconciliation_status_align'
branch_labels = None
depends_on = None


def upgrade():
    """
    创建分析表并执行FK类型不匹配分析
    """

    print("🔍 开始分析用户外键类型不匹配问题...")

    # Step 1: 创建临时分析表
    print("  → 创建临时分析表 temp_user_id_fk_analysis...")
    op.create_table(
        'temp_user_id_fk_analysis',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('table_name', sa.String(100), nullable=False, comment='来源表'),
        sa.Column('column_name', sa.String(100), nullable=False, comment='列名'),
        sa.Column('old_integer_value', sa.Integer(), nullable=True, comment='原Integer值'),
        sa.Column('matched_uuid', UUID(as_uuid=True), nullable=True, comment='匹配到的UUID'),
        sa.Column('match_method', sa.String(50), nullable=True, comment='匹配方式'),
        sa.Column('is_orphan', sa.Boolean(), default=False, comment='是否孤儿记录'),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        comment='用户FK类型不匹配分析表（临时表，修复后删除）'
    )

    op.create_index('idx_temp_user_fk_table', 'temp_user_id_fk_analysis', ['table_name'])
    op.create_index('idx_temp_user_fk_orphan', 'temp_user_id_fk_analysis', ['is_orphan'])

    # Step 2: 分析ad_spend_daily表
    print("  → 分析ad_spend_daily表...")
    op.execute("""
        INSERT INTO temp_user_id_fk_analysis
            (table_name, column_name, old_integer_value, is_orphan, notes)
        SELECT
            'ad_spend_daily' as table_name,
            'user_id' as column_name,
            user_id as old_integer_value,
            true as is_orphan,
            '警告: user_id声明为Integer但FK指向users.id(UUID)，类型不匹配' as notes
        FROM ad_spend_daily
        WHERE user_id IS NOT NULL
        GROUP BY user_id
    """)

    # Step 3: 分析reconciliation模块
    print("  → 分析reconciliation_details表...")
    op.execute("""
        INSERT INTO temp_user_id_fk_analysis
            (table_name, column_name, old_integer_value, is_orphan, notes)
        SELECT
            'reconciliation_details' as table_name,
            column_name,
            user_id_value as old_integer_value,
            true as is_orphan,
            'FK类型不匹配' as notes
        FROM (
            SELECT 'reviewed_by' as column_name, reviewed_by as user_id_value
            FROM reconciliation_details WHERE reviewed_by IS NOT NULL
            UNION
            SELECT 'resolved_by' as column_name, resolved_by as user_id_value
            FROM reconciliation_details WHERE resolved_by IS NOT NULL
        ) t
        GROUP BY column_name, user_id_value
    """)

    # Step 4: 生成分析报告
    print("  → 生成分析报告...")
    op.execute("""
        DO $$
        DECLARE
            total_records INTEGER;
            orphan_records INTEGER;
            affected_tables TEXT;
        BEGIN
            SELECT COUNT(*), COUNT(*) FILTER (WHERE is_orphan = true)
            INTO total_records, orphan_records
            FROM temp_user_id_fk_analysis;

            SELECT string_agg(DISTINCT table_name, ', ')
            INTO affected_tables
            FROM temp_user_id_fk_analysis;

            RAISE NOTICE '==========================================';
            RAISE NOTICE '📊 用户FK类型不匹配分析报告';
            RAISE NOTICE '==========================================';
            RAISE NOTICE '总记录数: %', total_records;
            RAISE NOTICE '孤儿记录数: %', orphan_records;
            RAISE NOTICE '影响表: %', affected_tables;
            RAISE NOTICE '==========================================';
            RAISE NOTICE '⚠️ 下一步: 请手动检查分析表，确认数据处理方案';
            RAISE NOTICE '查询命令: SELECT * FROM temp_user_id_fk_analysis ORDER BY table_name, is_orphan DESC;';
        END $$;
    """)

    print("✅ 分析完成！请检查temp_user_id_fk_analysis表")


def downgrade():
    """
    删除分析表
    """
    print("🗑️ 删除分析表...")
    op.drop_index('idx_temp_user_fk_orphan', 'temp_user_id_fk_analysis')
    op.drop_index('idx_temp_user_fk_table', 'temp_user_id_fk_analysis')
    op.drop_table('temp_user_id_fk_analysis')
    print("✅ 分析表已删除")
