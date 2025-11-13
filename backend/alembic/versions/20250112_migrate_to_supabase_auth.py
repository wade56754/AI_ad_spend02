"""迁移到Supabase Auth混合方案

Revision ID: 20250112_migrate_to_supabase_auth
Revises: 20250112_update_user_models_for_auth
Create Date: 2025-01-12 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250112_migrate_to_supabase_auth'
down_revision = '20250112_update_user_models_for_auth'
branch_labels = None
depends_on = None


def upgrade():
    """迁移到Supabase Auth混合方案"""

    # 1. 创建用户资料表
    op.create_table(
        'user_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=True, comment='用户名'),
        sa.Column('full_name', sa.String(length=100), nullable=True, comment='全名'),
        sa.Column('phone', sa.String(length=20), nullable=True, comment='手机号'),
        sa.Column('avatar_url', sa.String(length=500), nullable=True, comment='头像URL'),
        sa.Column('role', sa.String(length=20), nullable=False, default='media_buyer', comment='用户角色'),
        sa.Column('department', sa.String(length=100), nullable=True, comment='部门'),
        sa.Column('position', sa.String(length=100), nullable=True, comment='职位'),
        sa.Column('account_manager_id', postgresql.UUID(as_uuid=True), nullable=True, comment='上级经理ID'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='是否激活'),
        sa.Column('is_verified', sa.Boolean(), nullable=True, default=False, comment='是否已验证'),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True, comment='最后登录时间'),
        sa.Column('last_login_ip', sa.String(length=45), nullable=True, comment='最后登录IP'),
        sa.Column('preferences', postgresql.JSON(astext_type=sa.Text()), nullable=True, default=dict, comment='用户偏好设置'),
        sa.Column('timezone', sa.String(length=50), nullable=True, default='UTC', comment='时区'),
        sa.Column('language', sa.String(length=10), nullable=True, default='zh-CN', comment='语言'),
        sa.Column('notification_settings', postgresql.JSON(astext_type=sa.Text()), nullable=True, default=dict, comment='通知设置'),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True, default=dict, comment='额外的元数据'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True, comment='创建人ID'),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True, comment='更新人ID'),
        sa.ForeignKeyConstraint(['account_manager_id'], ['user_profiles.id']),
        sa.ForeignKeyConstraint(['created_by'], ['user_profiles.id']),
        sa.ForeignKeyConstraint(['id'], ['auth.users(id)'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by'], ['user_profiles.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.CheckConstraint("role IN ('admin', 'finance', 'data_operator', 'account_manager', 'media_buyer')", name='check_profile_role'),
        sa.Index('idx_user_profiles_role', 'role'),
        sa.Index('idx_user_profiles_created_at', 'created_at'),
        sa.Index('idx_user_profiles_last_login', 'last_login_at'),
        sa.Index('idx_user_profiles_department', 'department'),
        sa.Index('idx_user_profiles_position', 'position'),
        {'comment': '用户资料表（与Supabase Auth关联）'}
    )

    # 2. 创建用户登录历史表（更新为使用UUID）
    op.create_table(
        'user_login_history_new',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='用户ID'),
        sa.Column('email', sa.String(length=255), nullable=True, comment='邮箱（用于记录未注册用户）'),
        sa.Column('login_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='登录时间'),
        sa.Column('logout_time', sa.DateTime(timezone=True), nullable=True, comment='登出时间'),
        sa.Column('ip_address', sa.String(length=45), nullable=True, comment='IP地址'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='用户代理'),
        sa.Column('device_info', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='设备信息'),
        sa.Column('login_type', sa.String(length=20), nullable=False, default='password', comment='登录类型'),
        sa.Column('status', sa.String(length=20), nullable=False, default='success', comment='登录状态'),
        sa.Column('failure_reason', sa.String(length=255), nullable=True, comment='失败原因'),
        sa.Column('country', sa.String(length=50), nullable=True, comment='国家'),
        sa.Column('city', sa.String(length=100), nullable=True, comment='城市'),
        sa.ForeignKeyConstraint(['user_id'], ['auth.users(id)'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("login_type IN ('password', 'oauth', 'sso', 'api', 'registration')", name='check_login_type'),
        sa.CheckConstraint("status IN ('success', 'failed', 'logout', 'timeout')", name='check_login_status'),
        sa.Index('idx_login_history_user_uuid', 'user_id'),
        sa.Index('idx_login_history_time_uuid', 'login_time'),
        sa.Index('idx_login_history_status_uuid', 'status'),
        sa.Index('idx_login_history_ip_uuid', 'ip_address'),
        {'comment': '用户登录历史表'}
    )

    # 3. 创建用户会话表
    op.create_table(
        'user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='用户ID'),
        sa.Column('session_token', sa.String(length=500), nullable=False, comment='会话令牌'),
        sa.Column('device_info', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='设备信息'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='是否活跃'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True, comment='过期时间'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='最后访问时间'),
        sa.ForeignKeyConstraint(['user_id'], ['auth.users(id)'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_token'),
        sa.Index('idx_sessions_user_uuid', 'user_id'),
        sa.Index('idx_sessions_token_uuid', 'session_token'),
        sa.Index('idx_sessions_active_uuid', 'is_active'),
        sa.Index('idx_sessions_expires_uuid', 'expires_at'),
        {'comment': '用户会话表'}
    )

    # 4. 数据迁移（从旧表到新表）
    connection = op.get_bind()

    # 检查是否存在旧的登录历史表
    inspector = sa.inspect(connection)
    if 'user_login_history' in inspector.get_table_names():
        # 迁移登录历史数据
        op.execute("""
            INSERT INTO user_login_history_new (
                id, user_id, email, login_time, logout_time,
                ip_address, user_agent, device_info, login_type,
                status, failure_reason, country, city
            )
            SELECT
                gen_random_uuid(),
                CAST(user_id AS UUID),
                NULL,
                login_time,
                logout_time,
                ip_address,
                user_agent,
                device_info,
                login_type,
                status,
                failure_reason,
                NULL,
                NULL
            FROM user_login_history
        """)

        # 删除旧表
        op.drop_table('user_login_history')

        # 重命名新表
        op.execute('ALTER TABLE user_login_history_new RENAME TO user_login_history')

    # 5. 创建触发器函数
    op.execute("""
        CREATE OR REPLACE FUNCTION public.handle_new_user()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = public
        AS $$
        BEGIN
            INSERT INTO public.user_profiles (
                id,
                username,
                full_name,
                role,
                account_manager_id,
                created_at
            )
            VALUES (
                new.id,
                new.raw_user_meta_data->>'username',
                COALESCE(
                    new.raw_user_meta_data->>'full_name',
                    new.email
                ),
                COALESCE(
                    new.raw_user_meta_data->>'role',
                    'media_buyer'
                ),
                CASE
                    WHEN new.raw_user_meta_data->>'account_manager_id' IS NOT NULL
                    THEN new.raw_user_meta_data->>'account_manager_id'::UUID
                    ELSE NULL
                END,
                NOW()
            );

            -- 记录注册日志
            INSERT INTO public.user_login_history (
                user_id,
                email,
                login_type,
                status
            )
            VALUES (
                new.id,
                new.email,
                'registration',
                'success'
            );

            RETURN new;
        END;
        $$;
    """)

    # 创建更新时间戳的触发器函数
    op.execute("""
        CREATE OR REPLACE FUNCTION public.handle_profile_update()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        BEGIN
            new.updated_at = NOW();
            RETURN new;
        END;
        $$;
    """)

    # 创建更新最后访问时间的触发器函数
    op.execute("""
        CREATE OR REPLACE FUNCTION public.update_session_access()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        BEGIN
            new.last_accessed_at = NOW();
            RETURN new;
        END;
        $$;
    """)

    # 6. 应用触发器
    op.execute("""
        CREATE TRIGGER on_auth_user_created
            AFTER INSERT ON auth.users
            FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
    """)

    op.execute("""
        CREATE TRIGGER on_profile_updated
            BEFORE UPDATE ON user_profiles
            FOR EACH ROW EXECUTE FUNCTION public.handle_profile_update();
    """)

    op.execute("""
        CREATE TRIGGER on_session_accessed
            BEFORE UPDATE ON user_sessions
            FOR EACH ROW EXECUTE FUNCTION public.update_session_access();
    """)

    # 7. 启用RLS
    op.execute('ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE user_login_history ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY')

    # 8. 创建RLS策略
    # 用户资料策略
    op.execute("""
        CREATE POLICY "Users can view own profile" ON user_profiles
        FOR SELECT USING (auth.uid() = id);
    """)

    op.execute("""
        CREATE POLICY "Users can update own profile" ON user_profiles
        FOR UPDATE USING (auth.uid() = id);
    """)

    op.execute("""
        CREATE POLICY "Admins can view all profiles" ON user_profiles
        FOR SELECT USING (
            EXISTS (
                SELECT 1 FROM user_profiles
                WHERE id = auth.uid() AND role = 'admin'
            )
        );
    """)

    op.execute("""
        CREATE POLICY "Account managers can view their team" ON user_profiles
        FOR SELECT USING (
            account_manager_id = auth.uid()
            OR auth.uid() = id
        );
    """)

    # 登录历史策略
    op.execute("""
        CREATE POLICY "Users can view own login history" ON user_login_history
        FOR SELECT USING (auth.uid() = user_id);
    """)

    op.execute("""
        CREATE POLICY "Admins can view all login history" ON user_login_history
        FOR ALL USING (
            EXISTS (
                SELECT 1 FROM user_profiles
                WHERE id = auth.uid() AND role = 'admin'
            )
        );
    """)

    # 会话策略
    op.execute("""
        CREATE POLICY "Users can manage own sessions" ON user_sessions
        FOR ALL USING (auth.uid() = user_id);
    """)

    # 9. 创建用于数据迁移的函数
    op.execute("""
        CREATE OR REPLACE FUNCTION migrate_existing_users()
        RETURNS TABLE(success BOOLEAN, message TEXT)
        LANGUAGE plpgsql
        SECURITY DEFINER
        AS $$
        DECLARE
            user_record RECORD;
            user_count INTEGER := 0;
        BEGIN
            -- 备份现有用户数据到临时表
            CREATE TEMPORARY TABLE IF NOT EXISTS users_backup AS
            SELECT * FROM users;

            -- 计算需要迁移的用户数
            SELECT COUNT(*) INTO user_count FROM users_backup;

            -- 迁移每个用户
            FOR user_record IN SELECT * FROM users_backup LOOP
                -- 这里需要应用层来处理实际的Supabase Auth用户创建
                -- 数据库函数只能返回需要迁移的用户信息
                CONTINUE;
            END LOOP;

            RETURN NEXT ROW(true, 'Prepared ' || user_count || ' users for migration');
        END;
        $$;
    """)


def downgrade():
    """回滚Supabase Auth混合方案"""

    # 删除触发器
    op.execute('DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users')
    op.execute('DROP TRIGGER IF EXISTS on_profile_updated ON user_profiles')
    op.execute('DROP TRIGGER IF EXISTS on_session_accessed ON user_sessions')

    # 删除RLS策略
    op.execute('DROP POLICY IF EXISTS "Users can view own profile" ON user_profiles')
    op.execute('DROP POLICY IF EXISTS "Users can update own profile" ON user_profiles')
    op.execute('DROP POLICY IF EXISTS "Admins can view all profiles" ON user_profiles')
    op.execute('DROP POLICY IF EXISTS "Account managers can view their team" ON user_profiles')
    op.execute('DROP POLICY IF EXISTS "Users can view own login history" ON user_login_history')
    op.execute('DROP POLICY IF EXISTS "Admins can view all login history" ON user_login_history')
    op.execute('DROP POLICY IF EXISTS "Users can manage own sessions" ON user_sessions')

    # 删除函数
    op.execute('DROP FUNCTION IF EXISTS public.handle_new_user()')
    op.execute('DROP FUNCTION IF EXISTS public.handle_profile_update()')
    op.execute('DROP FUNCTION IF EXISTS public.update_session_access()')
    op.execute('DROP FUNCTION IF EXISTS public.migrate_existing_users()')

    # 删除表
    op.drop_table('user_sessions')
    op.drop_table('user_login_history')
    op.drop_table('user_profiles')

    # 恢复旧的登录历史表（如果需要）
    # op.create_table(
    #     'user_login_history',
    #     # ... 旧表结构
    # )