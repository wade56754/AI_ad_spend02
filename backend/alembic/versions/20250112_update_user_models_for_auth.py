"""更新用户模型支持新的认证功能

Revision ID: 20250112_update_user_models_for_auth
Revises: 20251112_update_ad_account_models
Create Date: 2025-01-12 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250112_update_user_models_for_auth'
down_revision = '20251112_update_ad_account_models'
branch_labels = None
depends_on = None


def upgrade():
    """升级用户模型"""

    # 创建用户令牌表
    op.create_table(
        'user_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('token_type', sa.String(length=20), nullable=False, comment='令牌类型'),
        sa.Column('token', sa.String(length=500), nullable=False, comment='令牌内容'),
        sa.Column('jti', sa.String(length=255), nullable=False, comment='JWT ID'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, comment='过期时间'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True, comment='最后使用时间'),
        sa.Column('is_revoked', sa.Boolean(), default=False, comment='是否已撤销'),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True, comment='撤销时间'),
        sa.Column('revoked_reason', sa.String(length=255), nullable=True, comment='撤销原因'),
        sa.Column('device_info', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='设备信息'),
        sa.Column('ip_address', sa.String(length=45), nullable=True, comment='IP地址'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='用户代理'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("token_type IN ('access', 'refresh', 'reset', 'verification')", name='check_token_type'),
        sa.Index('idx_user_tokens_user', 'user_id'),
        sa.Index('idx_user_tokens_jti', 'jti'),
        sa.Index('idx_user_tokens_expires', 'expires_at'),
        sa.Index('idx_user_tokens_type', 'token_type'),
        {'comment': '用户令牌表'}
    )

    # 创建登录历史表
    op.create_table(
        'user_login_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('login_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='登录时间'),
        sa.Column('logout_time', sa.DateTime(timezone=True), nullable=True, comment='登出时间'),
        sa.Column('ip_address', sa.String(length=45), nullable=True, comment='IP地址'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='用户代理'),
        sa.Column('device_info', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='设备信息'),
        sa.Column('login_type', sa.String(length=20), default='password', comment='登录类型'),
        sa.Column('status', sa.String(length=20), default='success', comment='登录状态'),
        sa.Column('failure_reason', sa.String(length=255), nullable=True, comment='失败原因'),
        sa.Column('session_id', sa.String(length=255), nullable=True, comment='会话ID'),
        sa.Column('location', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='地理位置'),
        sa.Column('fingerprint', sa.String(length=255), nullable=True, comment='设备指纹'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("login_type IN ('password', 'oauth', 'sso', 'api')", name='check_login_type'),
        sa.CheckConstraint("status IN ('success', 'failed', 'logout', 'timeout')", name='check_login_status'),
        sa.Index('idx_user_login_history_user', 'user_id'),
        sa.Index('idx_user_login_history_time', 'login_time'),
        sa.Index('idx_user_login_history_status', 'status'),
        {'comment': '用户登录历史表'}
    )

    # 创建密码重置表
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('token', sa.String(length=255), unique=True, nullable=False, comment='重置令牌'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, comment='过期时间'),
        sa.Column('used', sa.Boolean(), default=False, comment='是否已使用'),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True, comment='使用时间'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('ip_address', sa.String(length=45), nullable=True, comment='请求IP'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='用户代理'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_password_reset_tokens_user', 'user_id'),
        sa.Index('idx_password_reset_tokens_token', 'token'),
        sa.Index('idx_password_reset_tokens_expires', 'expires_at'),
        {'comment': '密码重置令牌表'}
    )

    # 创建邮箱验证表
    op.create_table(
        'email_verifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('email', sa.String(length=255), nullable=False, comment='邮箱地址'),
        sa.Column('token', sa.String(length=255), unique=True, nullable=False, comment='验证令牌'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, comment='过期时间'),
        sa.Column('verified', sa.Boolean(), default=False, comment='是否已验证'),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True, comment='验证时间'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('attempts', sa.Integer(), default=0, comment='尝试次数'),
        sa.Column('max_attempts', sa.Integer(), default=5, comment='最大尝试次数'),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True, comment='锁定到期时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_email_verifications_user', 'user_id'),
        sa.Index('idx_email_verifications_email', 'email'),
        sa.Index('idx_email_verifications_token', 'token'),
        {'comment': '邮箱验证表'}
    )

    # 添加用户表新字段
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True, comment='最后登录时间'))
    op.add_column('users', sa.Column('last_login_ip', sa.String(length=45), nullable=True, comment='最后登录IP'))
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), default=False, comment='邮箱是否验证'))
    op.add_column('users', sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True, comment='邮箱验证时间'))
    op.add_column('users', sa.Column('phone', sa.String(length=20), nullable=True, comment='手机号'))
    op.add_column('users', sa.Column('phone_verified', sa.Boolean(), default=False, comment='手机是否验证'))
    op.add_column('users', sa.Column('phone_verified_at', sa.DateTime(timezone=True), nullable=True, comment='手机验证时间'))
    op.add_column('users', sa.Column('avatar_url', sa.String(length=500), nullable=True, comment='头像URL'))
    op.add_column('users', sa.Column('timezone', sa.String(length=50), default='UTC', comment='时区'))
    op.add_column('users', sa.Column('language', sa.String(length=10), default='zh-CN', comment='语言'))
    op.add_column('users', sa.Column('login_attempts', sa.Integer(), default=0, comment='登录尝试次数'))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True, comment='锁定到期时间'))
    op.add_column('users', sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True, comment='密码修改时间'))
    op.add_column('users', sa.Column('mfa_enabled', sa.Boolean(), default=False, comment='是否启用多因素认证'))
    op.add_column('users', sa.Column('mfa_secret', sa.String(length=255), nullable=True, comment='MFA密钥'))
    op.add_column('users', sa.Column('backup_codes', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='备用代码'))
    op.add_column('users', sa.Column('preferences', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='用户偏好设置'))
    op.add_column('users', sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='元数据'))

    # 创建索引
    op.create_index('idx_users_last_login', 'users', ['last_login_at'])
    op.create_index('idx_users_email_verified', 'users', ['email_verified'])
    op.create_index('idx_users_phone', 'users', ['phone'])
    op.create_index('idx_users_locked_until', 'users', ['locked_until'])

    # 启用RLS
    op.execute('ALTER TABLE user_tokens ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE user_login_history ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE password_reset_tokens ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE email_verifications ENABLE ROW LEVEL SECURITY')

    # 创建RLS策略
    # 用户只能访问自己的令牌
    op.execute("""
        CREATE POLICY user_own_tokens ON user_tokens
        FOR ALL TO authenticated_role
        USING (user_id = current_setting('app.current_user_id')::integer)
        WITH CHECK (user_id = current_setting('app.current_user_id')::integer)
    """)

    # 用户只能访问自己的登录历史
    op.execute("""
        CREATE POLICY user_own_login_history ON user_login_history
        FOR ALL TO authenticated_role
        USING (user_id = current_setting('app.current_user_id')::integer)
        WITH CHECK (user_id = current_setting('app.current_user_id')::integer)
    """)

    # 用户只能访问自己的密码重置令牌
    op.execute("""
        CREATE POLICY user_own_password_resets ON password_reset_tokens
        FOR ALL TO authenticated_role
        USING (user_id = current_setting('app.current_user_id')::integer)
        WITH CHECK (user_id = current_setting('app.current_user_id')::integer)
    """)

    # 用户只能访问自己的邮箱验证
    op.execute("""
        CREATE POLICY user_own_email_verifications ON email_verifications
        FOR ALL TO authenticated_role
        USING (user_id = current_setting('app.current_user_id')::integer)
        WITH CHECK (user_id = current_setting('app.current_user_id')::integer)
    """)

    # 管理员全权限
    op.execute("""
        CREATE POLICY admin_full_user_tokens ON user_tokens
        FOR ALL TO admin_role
        USING (true)
        WITH CHECK (true)
    """)

    op.execute("""
        CREATE POLICY admin_full_login_history ON user_login_history
        FOR ALL TO admin_role
        USING (true)
        WITH CHECK (true)
    """)

    op.execute("""
        CREATE POLICY admin_full_password_resets ON password_reset_tokens
        FOR ALL TO admin_role
        USING (true)
        WITH CHECK (true)
    """)

    op.execute("""
        CREATE POLICY admin_full_email_verifications ON email_verifications
        FOR ALL TO admin_role
        USING (true)
        WITH CHECK (true)
    """)


def downgrade():
    """回滚用户模型"""
    # 删除表
    op.drop_table('email_verifications')
    op.drop_table('password_reset_tokens')
    op.drop_table('user_login_history')
    op.drop_table('user_tokens')

    # 删除用户表新增字段
    op.drop_column('users', 'metadata')
    op.drop_column('users', 'preferences')
    op.drop_column('users', 'backup_codes')
    op.drop_column('users', 'mfa_secret')
    op.drop_column('users', 'mfa_enabled')
    op.drop_column('users', 'password_changed_at')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'login_attempts')
    op.drop_column('users', 'language')
    op.drop_column('users', 'timezone')
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'phone_verified_at')
    op.drop_column('users', 'phone_verified')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'email_verified_at')
    op.drop_column('users', 'email_verified')
    op.drop_column('users', 'last_login_ip')
    op.drop_column('users', 'last_login_at')