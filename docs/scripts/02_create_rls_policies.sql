-- =====================================================
-- RLS (Row Level Security) 策略配置脚本
-- 版本: 2.1
-- 更新日期: 2025-01-11
--
-- 说明: 配置行级安全策略，实现数据隔离
-- =====================================================

-- =====================================================
-- 1. 启用RLS
-- =====================================================

-- 为所有需要保护的表启用RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE topups ENABLE ROW LEVEL SECURITY;
ALTER TABLE reconciliations ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- 2. 创建RLS策略辅助函数
-- =====================================================

-- 获取当前用户ID
CREATE OR REPLACE FUNCTION current_user_id()
RETURNS INTEGER AS $$
BEGIN
    -- 从JWT token中提取用户ID
    -- 这里需要根据实际的JWT实现调整
    RETURN current_setting('app.current_user_id', true)::INTEGER;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 获取当前用户角色
CREATE OR REPLACE FUNCTION current_user_role()
RETURNS TEXT AS $$
BEGIN
    RETURN current_setting('app.current_user_role', true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 检查用户是否为管理员
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN current_user_role() = 'admin';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 检查用户是否有特定角色
CREATE OR REPLACE FUNCTION has_role(roles TEXT[])
RETURNS BOOLEAN AS $$
BEGIN
    RETURN current_user_role() = ANY(roles);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 检查是否可以访问用户资源
CREATE OR REPLACE FUNCTION can_access_user(user_id_param INTEGER)
RETURNS BOOLEAN AS $$
BEGIN
    -- 管理员可以访问所有用户
    IF is_admin() THEN
        RETURN true;
    END IF;

    -- 用户只能访问自己的信息
    RETURN user_id_param = current_user_id();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 检查是否可以访问项目
CREATE OR REPLACE FUNCTION can_access_project(project_id_param INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    project_role TEXT;
BEGIN
    -- 管理员可以访问所有项目
    IF is_admin() THEN
        RETURN true;
    END IF;

    -- 检查是否是项目成员
    SELECT role INTO project_role
    FROM project_members
    WHERE project_id = project_id_param AND user_id = current_user_id();

    -- 项目成员可以访问项目
    IF project_role IS NOT NULL THEN
        RETURN true;
    END IF;

    -- 检查是否是项目负责人
    SELECT owner_id INTO project_role
    FROM projects
    WHERE id = project_id_param AND owner_id = current_user_id();

    IF FOUND THEN
        RETURN true;
    END IF;

    -- 检查是否是账户管理员
    SELECT 1 INTO project_role
    FROM projects
    WHERE id = project_id_param AND account_manager_id = current_user_id();

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 检查是否可以访问广告账户
CREATE OR REPLACE FUNCTION can_access_ad_account(account_id_param INTEGER)
RETURNS BOOLEAN AS $$
BEGIN
    -- 管理员可以访问所有账户
    IF is_admin() THEN
        RETURN true;
    END IF;

    -- 账户负责人可以访问
    SELECT 1 FROM ad_accounts
    WHERE id = account_id_param AND assigned_to = current_user_id();

    IF FOUND THEN
        RETURN true;
    END IF;

    -- 项目成员可以访问项目下的账户
    SELECT 1 FROM ad_accounts aa
    JOIN project_members pm ON aa.project_id = pm.project_id
    WHERE aa.id = account_id_param AND pm.user_id = current_user_id();

    IF FOUND THEN
        RETURN true;
    END IF;

    -- 户管可以访问渠道下的账户
    SELECT 1 FROM ad_accounts aa
    JOIN channels c ON aa.channel_id = c.id
    WHERE aa.id = account_id_param AND c.manager_id = current_user_id();

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 3. 用户表RLS策略
-- =====================================================

-- 用户表策略
-- 管理员可以查看所有用户，其他用户只能查看自己
CREATE POLICY "Users can view their own profile" ON users
    FOR SELECT
    USING (can_access_user(id));

-- 管理员可以更新所有用户，用户只能更新自己的非敏感字段
CREATE POLICY "Users can update their own profile" ON users
    FOR UPDATE
    USING (can_access_user(id))
    WITH CHECK (
        can_access_user(id) AND
        -- 不允许通过更新改变角色和超级用户状态
        (role = (SELECT role FROM users WHERE id = current_user_id()) OR is_admin()) AND
        (is_superuser = (SELECT is_superuser FROM users WHERE id = current_user_id()) OR is_admin())
    );

-- 只有管理员可以创建用户
CREATE POLICY "Only admins can create users" ON users
    FOR INSERT
    WITH CHECK (is_admin());

-- 只有管理员可以删除用户
CREATE POLICY "Only admins can delete users" ON users
    FOR DELETE
    USING (is_admin());

-- 用户配置表策略
CREATE POLICY "Users can view their own profile data" ON user_profiles
    FOR ALL
    USING (can_access_user(user_id))
    WITH CHECK (can_access_user(user_id));

-- 会话表策略
CREATE POLICY "Users can view their own sessions" ON sessions
    FOR SELECT
    USING (user_id = current_user_id());

CREATE POLICY "Users can delete their own sessions" ON sessions
    FOR DELETE
    USING (user_id = current_user_id());

-- =====================================================
-- 4. 项目表RLS策略
-- =====================================================

-- 项目查看策略
CREATE POLICY "Project members can view projects" ON projects
    FOR SELECT
    USING (
        is_admin() OR
        owner_id = current_user_id() OR
        account_manager_id = current_user_id() OR
        EXISTS (
            SELECT 1 FROM project_members
            WHERE project_id = projects.id AND user_id = current_user_id()
        )
    );

-- 项目更新策略
CREATE POLICY "Project managers can update projects" ON projects
    FOR UPDATE
    USING (can_access_project(id))
    WITH CHECK (
        -- 不能更改项目所有者，除非是管理员
        (owner_id = (SELECT owner_id FROM projects WHERE id = id) OR is_admin())
    );

-- 项目创建策略
CREATE POLICY "Users can create projects" ON projects
    FOR INSERT
    WITH CHECK (
        is_admin() OR has_role(ARRAY['data_operator', 'account_manager', 'admin'])
    );

-- 项目成员表策略
CREATE POLICY "Project members management" ON project_members
    FOR ALL
    USING (can_access_project(project_id))
    WITH CHECK (can_access_project(project_id));

-- =====================================================
-- 5. 渠道表RLS策略
-- =====================================================

-- 渠道查看策略
CREATE POLICY "Channel access policy" ON channels
    FOR SELECT
    USING (
        is_admin() OR
        manager_id = current_user_id() OR
        EXISTS (
            SELECT 1 FROM ad_accounts aa
            WHERE aa.channel_id = channels.id AND can_access_ad_account(aa.id)
        )
    );

-- 渠道管理策略
CREATE POLICY "Channel managers can update channels" ON channels
    FOR UPDATE
    USING (is_admin() OR manager_id = current_user_id())
    WITH CHECK (is_admin() OR manager_id = current_user_id());

-- 渠道创建策略
CREATE POLICY "Admins and managers can create channels" ON channels
    FOR INSERT
    WITH CHECK (is_admin() OR has_role(ARRAY['account_manager', 'admin']));

-- =====================================================
-- 6. 广告账户表RLS策略
-- =====================================================

-- 广告账户查看策略
CREATE POLICY "Ad account access policy" ON ad_accounts
    FOR SELECT
    USING (can_access_ad_account(id));

-- 广告账户更新策略
CREATE POLICY "Ad account update policy" ON ad_accounts
    FOR UPDATE
    USING (can_access_ad_account(id))
    WITH CHECK (
        -- 账户分配只能由特定角色修改
        (assigned_to IS NULL OR assigned_to = (SELECT assigned_to FROM ad_accounts WHERE id = id) OR is_admin() OR has_role(ARRAY['data_operator', 'account_manager']))
    );

-- 广告账户创建策略
CREATE POLICY "Channel managers can create accounts" ON ad_accounts
    FOR INSERT
    WITH CHECK (
        is_admin() OR
        (EXISTS (
            SELECT 1 FROM channels
            WHERE id = channel_id AND manager_id = current_user_id()
        )) OR
        has_role(ARRAY['account_manager', 'admin'])
    );

-- =====================================================
-- 7. 日报表RLS策略
-- =====================================================

-- 日报查看策略
CREATE POLICY "Daily reports view policy" ON daily_reports
    FOR SELECT
    USING (
        is_admin() OR
        submitter_id = current_user_id() OR
        reviewer_id = current_user_id() OR
        can_access_ad_account(account_id)
    );

-- 日报提交策略
CREATE POLICY "Users can submit reports" ON daily_reports
    FOR INSERT
    WITH CHECK (
        submitter_id = current_user_id() AND
        can_access_ad_account(account_id)
    );

-- 日报更新策略
CREATE POLICY "Report owners and reviewers can update" ON daily_reports
    FOR UPDATE
    USING (
        submitter_id = current_user_id() OR
        reviewer_id = current_user_id() OR
        is_admin()
    )
    WITH CHECK (
        -- 状态变更规则
        CASE
            WHEN status = 'draft' THEN submitter_id = current_user_id
            WHEN status = 'submitted' THEN submitter_id = current_user_id
            WHEN status IN ('reviewed', 'approved', 'rejected') THEN
                reviewer_id = current_user_id OR is_admin()
            ELSE false
        END
    );

-- =====================================================
-- 8. 充值表RLS策略
-- =====================================================

-- 充值查看策略
CREATE POLICY "Topup view policy" ON topups
    FOR SELECT
    USING (
        is_admin() OR
        requester_id = current_user_id() OR
        reviewer_id = current_user_id() OR
        approver_id = current_user_id() OR
        can_access_ad_account(account_id) OR
        has_role(ARRAY['finance', 'admin'])
    );

-- 充值创建策略
CREATE POLICY "Users can request topups" ON topups
    FOR INSERT
    WITH CHECK (
        requester_id = current_user_id() AND
        can_access_ad_account(account_id)
    );

-- 充值更新策略
CREATE POLICY "Topup update policy" ON topups
    FOR UPDATE
    USING (
        is_admin() OR
        (requester_id = current_user_id AND status IN ('draft', 'pending_review')) OR
        (reviewer_id = current_user_id AND status = 'pending_review') OR
        (approver_id = current_user_id AND status = 'approved') OR
        has_role(ARRAY['finance', 'admin'])
    );

-- =====================================================
-- 9. 对账表RLS策略
-- =====================================================

-- 对账查看策略
CREATE POLICY "Reconciliation view policy" ON reconciliations
    FOR SELECT
    USING (
        is_admin() OR
        reconciled_by = current_user_id() OR
        can_access_ad_account(account_id) OR
        has_role(ARRAY['finance', 'admin'])
    );

-- 对账创建策略
CREATE POLICY "Finance can create reconciliations" ON reconciliations
    FOR INSERT
    WITH CHECK (is_admin() OR has_role(ARRAY['finance', 'admin']));

-- 对账更新策略
CREATE POLICY "Reconciliation update policy" ON reconciliations
    FOR UPDATE
    USING (
        is_admin() OR
        (reconciled_by = current_user_id AND status IN ('draft', 'pending')) OR
        has_role(ARRAY['finance', 'admin'])
    );

-- =====================================================
-- 10. 审计日志表RLS策略
-- =====================================================

-- 审计日志查看策略
CREATE POLICY "Audit log view policy" ON audit_logs
    FOR SELECT
    USING (
        is_admin() OR
        user_id = current_user_id() OR
        has_role(ARRAY['finance', 'data_operator', 'admin'])
    );

-- 审计日志插入策略
CREATE POLICY "System creates audit logs" ON audit_logs
    FOR INSERT
    WITH CHECK (true); -- 由触发器系统插入，不需要额外检查

-- =====================================================
-- 11. 创建安全函数
-- =====================================================

-- 检查用户权限的通用函数
CREATE OR REPLACE FUNCTION check_permission(
    resource_type TEXT,
    resource_id INTEGER,
    action TEXT DEFAULT 'read'
)
RETURNS BOOLEAN AS $$
BEGIN
    -- 管理员拥有所有权限
    IF is_admin() THEN
        RETURN true;
    END IF;

    -- 根据资源类型检查权限
    CASE resource_type
        WHEN 'user' THEN
            RETURN can_access_user(resource_id) AND action IN ('read', 'update');
        WHEN 'project' THEN
            RETURN can_access_project(resource_id) AND action IN ('read', 'update');
        WHEN 'ad_account' THEN
            RETURN can_access_ad_account(resource_id) AND action IN ('read', 'update');
        WHEN 'daily_report' THEN
            RETURN EXISTS (
                SELECT 1 FROM daily_reports
                WHERE id = resource_id AND
                (submitter_id = current_user_id() OR
                 reviewer_id = current_user_id() OR
                 can_access_ad_account(account_id))
            ) AND action IN ('read', 'update', 'delete');
        ELSE
            RETURN false;
    END CASE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 记录登录尝试
CREATE OR REPLACE FUNCTION log_login_attempt(
    user_email_param TEXT,
    ip_address_param INET,
    user_agent_param TEXT,
    success_param BOOLEAN
)
RETURNS VOID AS $$
DECLARE
    user_id_val INTEGER;
BEGIN
    -- 获取用户ID
    SELECT id INTO user_id_val
    FROM users
    WHERE email = user_email_param;

    -- 记录审计日志
    INSERT INTO audit_logs (
        event_type,
        user_id,
        user_email,
        resource_type,
        action,
        ip_address,
        user_agent,
        success,
        details
    ) VALUES (
        CASE WHEN success_param THEN 'USER_LOGIN' ELSE 'LOGIN_FAILED' END,
        user_id_val,
        user_email_param,
        'auth',
        'login',
        ip_address_param,
        user_agent_param,
        success_param,
        jsonb_build_object('timestamp', NOW())
    );

    -- 更新最后登录时间
    IF success_param AND user_id_val IS NOT NULL THEN
        UPDATE users
        SET last_login_at = NOW()
        WHERE id = user_id_val;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 12. 完成提示
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '=====================================================';
    RAISE NOTICE 'RLS策略配置完成！';
    RAISE NOTICE '';
    RAISE NOTICE '已配置的策略:';
    RAISE NOTICE '- 用户数据隔离：用户只能访问自己的信息';
    RAISE NOTICE '- 项目数据隔离：基于项目成员关系';
    RAISE NOTICE '- 广告账户隔离：基于分配关系';
    RAISE NOTICE '- 财务数据隔离：基于角色权限';
    RAISE NOTICE '';
    RAISE NOTICE '权限角色说明:';
    RAISE NOTICE '- admin: 管理员，拥有所有权限';
    RAISE NOTICE '- finance: 财务，可访问充值和对账数据';
    RAISE NOTICE '- data_operator: 数据员，可审核日报和分配账户';
    RAISE NOTICE '- account_manager: 户管，可管理渠道和账户';
    RAISE NOTICE '- media_buyer: 投手，可提交日报和申请充值';
    RAISE NOTICE '=====================================================';
END $$;