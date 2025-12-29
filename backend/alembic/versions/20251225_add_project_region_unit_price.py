"""
Add region and unit_price columns to projects table

Revision ID: 20251225_add_project_region_unit_price
Revises: 20251224_add_ceo_role
Create Date: 2025-12-25

变更内容:
1. projects 表新增字段:
   - region: VARCHAR(50) 主要投放地区
   - unit_price: NUMERIC(15,2) 单粉价格

业务背景:
- 项目管理需要展示地区和单价信息
- 数据来源: 前端项目表格需要展示这些维度
- total_follows 由日报聚合计算，无需新增列

SoT Reference: DATA_SCHEMA.md v5.2 (projects entity)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251225_add_project_region_unit_price'
down_revision = '20251224_add_ceo_role'
branch_labels = None
depends_on = None


def upgrade():
    """添加 region 和 unit_price 字段到 projects 表"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 检查 projects 表是否存在
    if 'projects' in [t for t in inspector.get_table_names()]:
        columns = [c['name'] for c in inspector.get_columns('projects')]

        # 添加 region 字段
        if 'region' not in columns:
            op.add_column(
                'projects',
                sa.Column('region', sa.String(50), nullable=True,
                         comment='主要投放地区')
            )

        # 添加 unit_price 字段
        if 'unit_price' not in columns:
            op.add_column(
                'projects',
                sa.Column('unit_price', sa.Numeric(15, 2), nullable=True,
                         comment='单粉价格')
            )


def downgrade():
    """移除 region 和 unit_price 字段"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'projects' in [t for t in inspector.get_table_names()]:
        columns = [c['name'] for c in inspector.get_columns('projects')]

        if 'region' in columns:
            op.drop_column('projects', 'region')

        if 'unit_price' in columns:
            op.drop_column('projects', 'unit_price')
