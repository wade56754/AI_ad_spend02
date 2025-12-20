"""分析用户外键类型不匹配问题 (占位迁移)

Revision ID: 20251117_analyze_user_fk
Revises: 20251117_ad_spend_daily_user_fks_fix
Create Date: 2025-11-17 11:30:00.000000

注意: 这是一个占位迁移文件，用于修复迁移链断裂。
原始迁移是分析脚本，用于检查用户外键类型不匹配问题。
分析结果已在后续修复迁移 (20251117_fix_ad_spend_user_fk) 中使用。
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251117_analyze_user_fk'
down_revision = '20251117_ad_spend_daily_user_fks_fix'
branch_labels = None
depends_on = None


def upgrade():
    """
    占位升级 - 原始迁移为分析脚本

    原始功能:
    - 分析 ad_spend_daily 表的 user_id/created_by/updated_by 列类型
    - 检查与 user_profiles.id (UUID) 的类型不匹配
    - 计算孤儿记录比例
    - 输出分析报告

    分析结果已记录，实际修复在 20251117_fix_ad_spend_user_fk 中执行。
    """
    pass


def downgrade():
    """
    占位降级 - 不执行任何操作
    """
    pass
