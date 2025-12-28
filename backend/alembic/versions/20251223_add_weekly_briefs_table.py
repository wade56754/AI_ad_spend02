"""
Add weekly_briefs table for project weekly reports

Revision ID: 20251223_add_weekly_briefs_table
Revises: 20251222_add_project_owner_role
Create Date: 2025-12-23

SoT Reference: B3-weekly-brief.md §2.2
状态机: draft → submitted (终态)

新增表:
- weekly_briefs: 周度简报表
  - project_id: 关联项目 (FK)
  - week_start/week_end: 周期范围
  - submitter_id: 提交人 (FK users.id)
  - status: draft/submitted
  - weekly_spend/weekly_conversions/weekly_cpl: 汇总数据
  - achievements/issues/solutions/next_week_plan: 周报内容
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID


# revision identifiers, used by Alembic.
revision = '20251223_add_weekly_briefs_table'
down_revision = '20251222_add_project_owner_role'
branch_labels = None
depends_on = None


def upgrade():
    """创建 weekly_briefs 表"""

    # 1. 创建 weekly_briefs 表
    op.create_table(
        'weekly_briefs',
        # 主键
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True, comment='周报ID'),

        # 外键 - 项目
        sa.Column('project_id', sa.BigInteger, sa.ForeignKey('projects.id', ondelete='CASCADE'),
                  nullable=False, index=True, comment='项目ID'),

        # 周期字段
        sa.Column('week_start', sa.Date, nullable=False, comment='周开始日期（周一）'),
        sa.Column('week_end', sa.Date, nullable=False, comment='周结束日期（周日）'),

        # 提交人
        sa.Column('submitter_id', PGUUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'),
                  nullable=True, index=True, comment='提交人ID'),

        # 状态
        sa.Column('status', sa.String(20), nullable=False,
                  server_default='draft', comment='状态（draft/submitted）'),

        # 汇总数据
        sa.Column('weekly_spend', sa.Numeric(15, 2), nullable=False,
                  server_default='0.00', comment='周消耗'),
        sa.Column('weekly_conversions', sa.Integer, nullable=False,
                  server_default='0', comment='周进粉'),
        sa.Column('weekly_cpl', sa.Numeric(10, 2), nullable=False,
                  server_default='0.00', comment='周CPL'),

        # 周报内容
        sa.Column('achievements', sa.Text, nullable=True, comment='本周成果'),
        sa.Column('issues', sa.Text, nullable=True, comment='遇到问题'),
        sa.Column('solutions', sa.Text, nullable=True, comment='解决方案'),
        sa.Column('next_week_plan', sa.Text, nullable=True, comment='下周计划'),

        # 提交时间
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True, comment='提交时间'),

        # 时间戳
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), comment='更新时间'),
    )

    # 2. 添加约束
    # 每项目每周只能有一份周报
    op.create_unique_constraint(
        'uq_weekly_briefs_project_week',
        'weekly_briefs',
        ['project_id', 'week_start']
    )

    # 状态约束
    op.execute("""
        ALTER TABLE weekly_briefs
        ADD CONSTRAINT chk_weekly_briefs_status
        CHECK (status IN ('draft', 'submitted'))
    """)

    # 周期合法性约束
    op.execute("""
        ALTER TABLE weekly_briefs
        ADD CONSTRAINT chk_weekly_briefs_week_range
        CHECK (week_end >= week_start)
    """)

    # 3. 创建索引
    op.create_index('idx_weekly_briefs_project', 'weekly_briefs', ['project_id'])
    op.create_index('idx_weekly_briefs_week', 'weekly_briefs', ['week_start'])
    op.create_index('idx_weekly_briefs_submitter', 'weekly_briefs', ['submitter_id'])
    op.create_index('idx_weekly_briefs_status', 'weekly_briefs', ['status'])
    op.create_index('idx_weekly_briefs_project_week', 'weekly_briefs', ['project_id', 'week_start'])

    # 4. 创建更新时间触发器
    op.execute("""
        CREATE OR REPLACE FUNCTION update_weekly_briefs_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS trigger_update_weekly_briefs_updated_at ON weekly_briefs;

        CREATE TRIGGER trigger_update_weekly_briefs_updated_at
            BEFORE UPDATE ON weekly_briefs
            FOR EACH ROW
            EXECUTE FUNCTION update_weekly_briefs_updated_at();
    """)

    # 5. 添加表注释
    op.execute("""
        COMMENT ON TABLE weekly_briefs IS
            '周度简报表 - 记录项目周度汇报 (B3-weekly-brief.md §2.2)';
    """)


def downgrade():
    """删除 weekly_briefs 表"""

    # 1. 移除触发器和函数
    op.execute("""
        DROP TRIGGER IF EXISTS trigger_update_weekly_briefs_updated_at ON weekly_briefs;
        DROP FUNCTION IF EXISTS update_weekly_briefs_updated_at();
    """)

    # 2. 移除索引
    op.drop_index('idx_weekly_briefs_project_week', table_name='weekly_briefs')
    op.drop_index('idx_weekly_briefs_status', table_name='weekly_briefs')
    op.drop_index('idx_weekly_briefs_submitter', table_name='weekly_briefs')
    op.drop_index('idx_weekly_briefs_week', table_name='weekly_briefs')
    op.drop_index('idx_weekly_briefs_project', table_name='weekly_briefs')

    # 3. 移除约束
    op.execute("ALTER TABLE weekly_briefs DROP CONSTRAINT IF EXISTS chk_weekly_briefs_week_range")
    op.execute("ALTER TABLE weekly_briefs DROP CONSTRAINT IF EXISTS chk_weekly_briefs_status")
    op.drop_constraint('uq_weekly_briefs_project_week', 'weekly_briefs', type_='unique')

    # 4. 删除表
    op.drop_table('weekly_briefs')
