"""
Add fulfillment status fields to projects table

Revision ID: 20251226_add_project_fulfillment_fields
Revises: 20251226_add_reconciliation_control_center
Create Date: 2025-12-26

变更内容:
1. projects 表新增字段:
   - fulfillment_status: VARCHAR(20) 履约状态 (running/fulfilled)
   - fulfillment_reason: VARCHAR(30) 履约结束原因 (spend_exhausted/client_stopped)
   - fulfilled_at: TIMESTAMPTZ 履约完成时间

2. 新增 CHECK 约束:
   - chk_projects_fulfillment_status: 限制 fulfillment_status 合法值
   - chk_projects_fulfillment_reason: 限制 fulfillment_reason 合法值

业务背景:
- BUSINESS_RULES.md v4.6 BR-PROJ-006 定义履约状态字段
- BI-06 定义履约完成的唯一判定条件
- BI-05 定义履约完成前不得确认收入

SoT Reference: BUSINESS_RULES.md v4.6 §4.3.1, §1.5.2
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251226_add_project_fulfillment_fields'
down_revision = '20251226_add_reconciliation_control_center'
branch_labels = None
depends_on = None


def upgrade():
    """添加履约状态字段到 projects 表"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 检查 projects 表是否存在
    if 'projects' in [t for t in inspector.get_table_names()]:
        columns = [c['name'] for c in inspector.get_columns('projects')]

        # 添加 fulfillment_status 字段
        if 'fulfillment_status' not in columns:
            op.add_column(
                'projects',
                sa.Column(
                    'fulfillment_status',
                    sa.String(20),
                    nullable=False,
                    server_default='running',
                    comment='履约状态: running/fulfilled (SoT: BUSINESS_RULES.md v4.6 §4.3.1)'
                )
            )

        # 添加 fulfillment_reason 字段
        if 'fulfillment_reason' not in columns:
            op.add_column(
                'projects',
                sa.Column(
                    'fulfillment_reason',
                    sa.String(30),
                    nullable=True,
                    comment='履约结束原因: spend_exhausted/client_stopped (SoT: BI-06)'
                )
            )

        # 添加 fulfilled_at 字段
        if 'fulfilled_at' not in columns:
            op.add_column(
                'projects',
                sa.Column(
                    'fulfilled_at',
                    sa.DateTime(timezone=True),
                    nullable=True,
                    comment='履约完成时间 (UTC)'
                )
            )

        # 添加 CHECK 约束
        # 注意: PostgreSQL 语法
        try:
            op.create_check_constraint(
                'chk_projects_fulfillment_status',
                'projects',
                "fulfillment_status IN ('running', 'fulfilled')"
            )
        except Exception:
            # 约束可能已存在
            pass

        try:
            op.create_check_constraint(
                'chk_projects_fulfillment_reason',
                'projects',
                "fulfillment_reason IS NULL OR fulfillment_reason IN ('spend_exhausted', 'client_stopped')"
            )
        except Exception:
            # 约束可能已存在
            pass

        # 添加索引 (用于驾驶舱查询已履约项目数)
        try:
            op.create_index(
                'idx_projects_fulfillment_status',
                'projects',
                ['fulfillment_status']
            )
        except Exception:
            # 索引可能已存在
            pass


def downgrade():
    """移除履约状态字段"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'projects' in [t for t in inspector.get_table_names()]:
        columns = [c['name'] for c in inspector.get_columns('projects')]

        # 移除索引
        try:
            op.drop_index('idx_projects_fulfillment_status', 'projects')
        except Exception:
            pass

        # 移除约束
        try:
            op.drop_constraint('chk_projects_fulfillment_reason', 'projects')
        except Exception:
            pass

        try:
            op.drop_constraint('chk_projects_fulfillment_status', 'projects')
        except Exception:
            pass

        # 移除字段
        if 'fulfilled_at' in columns:
            op.drop_column('projects', 'fulfilled_at')

        if 'fulfillment_reason' in columns:
            op.drop_column('projects', 'fulfillment_reason')

        if 'fulfillment_status' in columns:
            op.drop_column('projects', 'fulfillment_status')
