"""
Update daily_reports unique constraint to include region

Revision ID: 20251225_daily_reports_unique_region
Revises: 20251225_add_project_region_unit_price
Create Date: 2025-12-25

变更内容:
1. 删除旧唯一约束: uq_daily_reports_date_account (report_date, ad_account_id)
2. 创建新唯一约束: uq_daily_reports_date_account_region (report_date, ad_account_id, region)

业务背景:
- 投手可能同时投放多个地区（如 Turkey、India）
- 原约束不允许同一账户同一天有多条日报
- 新约束允许按地区分别报告（同一天同一账户可有多个地区报告）

SoT Reference:
- DATA_SCHEMA.md v5.4 daily_reports 约束
- daily_report.py v2.1 唯一约束更新

注意事项:
- 如果现有数据中存在 (report_date, ad_account_id, region) 重复，迁移会失败
- 建议在迁移前检查数据一致性
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251225_daily_reports_unique_region'
down_revision = '20251225_add_project_region_unit_price'
branch_labels = None
depends_on = None


def upgrade():
    """更新唯一约束：添加 region 维度"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 检查 daily_reports 表是否存在
    if 'daily_reports' not in [t for t in inspector.get_table_names()]:
        print("daily_reports 表不存在，跳过迁移")
        return

    # 获取现有约束
    constraints = inspector.get_unique_constraints('daily_reports')
    constraint_names = [c['name'] for c in constraints]

    # 1. 删除旧的唯一约束
    if 'uq_daily_reports_date_account' in constraint_names:
        op.drop_constraint('uq_daily_reports_date_account', 'daily_reports', type_='unique')
        print("已删除旧约束: uq_daily_reports_date_account")
    else:
        print("旧约束 uq_daily_reports_date_account 不存在，跳过删除")

    # 2. 创建新的唯一约束（包含 region）
    if 'uq_daily_reports_date_account_region' not in constraint_names:
        op.create_unique_constraint(
            'uq_daily_reports_date_account_region',
            'daily_reports',
            ['report_date', 'ad_account_id', 'region']
        )
        print("已创建新约束: uq_daily_reports_date_account_region")
    else:
        print("新约束 uq_daily_reports_date_account_region 已存在，跳过创建")


def downgrade():
    """回滚：恢复原唯一约束"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'daily_reports' not in [t for t in inspector.get_table_names()]:
        return

    constraints = inspector.get_unique_constraints('daily_reports')
    constraint_names = [c['name'] for c in constraints]

    # 1. 删除新的唯一约束
    if 'uq_daily_reports_date_account_region' in constraint_names:
        op.drop_constraint('uq_daily_reports_date_account_region', 'daily_reports', type_='unique')

    # 2. 恢复旧的唯一约束
    if 'uq_daily_reports_date_account' not in constraint_names:
        op.create_unique_constraint(
            'uq_daily_reports_date_account',
            'daily_reports',
            ['report_date', 'ad_account_id']
        )
