"""P0-005: 为缺失 CHECK 约束的表添加状态约束

Revision ID: 20251120_add_missing_check_constraints_p0
Revises: 20251120_fix_reconciliation_batch_constraint_p0
Create Date: 2025-11-20

根据 STATE_MACHINE.md v2.5 第15章，为以下表添加 CHECK 约束：
- projects.status
- ad_accounts.status
- reconciliation_details.status
- channels.status
- channel_reviews.review_status
- channel_account_requests.status
- account_alerts.status

注意：daily_reports 和 topup_requests 的约束已在模型中定义，会自动创建
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '20251120_add_missing_check_constraints_p0'
down_revision = '20251120_fix_reconciliation_batch_constraint_p0'
branch_labels = None
depends_on = None


def upgrade():
    """添加所有缺失的 CHECK 约束"""

    # 1. projects.status
    try:
        op.create_check_constraint(
            'chk_projects_status',
            'projects',
            "status IN ('draft', 'active', 'suspended', 'archived')"
        )
    except Exception:
        pass  # 可能已存在

    # 2. ad_accounts.status
    try:
        op.create_check_constraint(
            'chk_ad_accounts_status',
            'ad_accounts',
            "status IN ('new', 'testing', 'active', 'suspended', 'dead', 'archived')"
        )
    except Exception:
        pass

    # 3. reconciliation_details.status
    try:
        op.create_check_constraint(
            'chk_reconciliation_details_status',
            'reconciliation_details',
            "status IN ('pending', 'confirmed', 'adjusted')"
        )
    except Exception:
        pass

    # 4. channels.status
    try:
        op.create_check_constraint(
            'chk_channels_status',
            'channels',
            "status IN ('active', 'inactive')"
        )
    except Exception:
        pass

    # 5. channel_reviews.review_status
    try:
        op.create_check_constraint(
            'chk_channel_reviews_review_status',
            'channel_reviews',
            "review_status IN ('draft', 'pending', 'approved', 'rejected')"
        )
    except Exception:
        pass

    # 6. channel_account_requests.status
    try:
        op.create_check_constraint(
            'chk_channel_account_requests_status',
            'channel_account_requests',
            "status IN ('draft', 'pending', 'approved', 'rejected')"
        )
    except Exception:
        pass

    # 7. account_alerts.status
    try:
        op.create_check_constraint(
            'chk_account_alerts_status',
            'account_alerts',
            "status IN ('open', 'ack', 'resolved')"
        )
    except Exception:
        pass


def downgrade():
    """移除所有 CHECK 约束"""

    constraints = [
        ('chk_projects_status', 'projects'),
        ('chk_ad_accounts_status', 'ad_accounts'),
        ('chk_reconciliation_details_status', 'reconciliation_details'),
        ('chk_channels_status', 'channels'),
        ('chk_channel_reviews_review_status', 'channel_reviews'),
        ('chk_channel_account_requests_status', 'channel_account_requests'),
        ('chk_account_alerts_status', 'account_alerts'),
    ]

    for constraint_name, table_name in constraints:
        try:
            op.drop_constraint(constraint_name, table_name, type_='check')
        except Exception:
            pass
