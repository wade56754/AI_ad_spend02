"""添加充值管理表 (占位迁移)

Revision ID: 20251112_add_topup_management_tables
Revises: 20251112_update_ad_account_models
Create Date: 2025-11-12 09:00:00.000000

注意: 这是一个占位迁移文件，用于修复迁移链断裂。
实际的 topup_requests 表已通过其他方式创建。
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251112_add_topup_management_tables'
down_revision = '20250115_add_missing_core_models_v3'
branch_labels = None
depends_on = None


def upgrade():
    """
    占位升级 - 表已存在

    topup_requests 表已通过以下方式之一创建:
    - Supabase 迁移
    - 手动 SQL
    - 其他迁移脚本
    """
    pass


def downgrade():
    """
    占位降级 - 不执行任何操作
    """
    pass
