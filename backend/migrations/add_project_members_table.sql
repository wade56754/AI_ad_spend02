-- 添加 project_members 表
-- 用途：记录用户在项目中的成员关系和角色权限
-- 作者：Claude Code
-- 日期：2025-11-19

-- 创建 project_members 表
CREATE TABLE IF NOT EXISTS project_members (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    permissions JSONB,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 约束：同一用户在同一项目中只能有一个成员关系
    CONSTRAINT project_members_project_user_key UNIQUE (project_id, user_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_project_members_project_id ON project_members(project_id);
CREATE INDEX IF NOT EXISTS idx_project_members_user_id ON project_members(user_id);
CREATE INDEX IF NOT EXISTS idx_project_members_project_user ON project_members(project_id, user_id);

-- 添加字段注释
COMMENT ON TABLE project_members IS '项目成员表 - 记录用户在项目中的角色和权限';
COMMENT ON COLUMN project_members.id IS '成员关系ID';
COMMENT ON COLUMN project_members.project_id IS '项目ID';
COMMENT ON COLUMN project_members.user_id IS '用户ID';
COMMENT ON COLUMN project_members.role IS '项目内角色：project_admin/member/viewer';
COMMENT ON COLUMN project_members.permissions IS '扩展权限配置（JSON格式）';
COMMENT ON COLUMN project_members.notes IS '备注';
COMMENT ON COLUMN project_members.created_at IS '创建时间';
COMMENT ON COLUMN project_members.updated_at IS '更新时间';

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_project_members_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_project_members_updated_at
    BEFORE UPDATE ON project_members
    FOR EACH ROW
    EXECUTE FUNCTION update_project_members_updated_at();

-- RLS 策略（如果启用）
-- ALTER TABLE project_members ENABLE ROW LEVEL SECURITY;

-- 允许用户查看自己所属项目的成员
-- CREATE POLICY "用户可查看所属项目成员" ON project_members
--     FOR SELECT
--     USING (
--         project_id IN (
--             SELECT project_id FROM project_members WHERE user_id = auth.uid()
--         )
--         OR
--         project_id IN (
--             SELECT id FROM projects WHERE created_by = auth.uid()
--         )
--     );

-- 允许项目管理员管理成员
-- CREATE POLICY "项目管理员可管理成员" ON project_members
--     FOR ALL
--     USING (
--         EXISTS (
--             SELECT 1 FROM project_members pm
--             WHERE pm.project_id = project_members.project_id
--             AND pm.user_id = auth.uid()
--             AND pm.role = 'project_admin'
--         )
--         OR
--         EXISTS (
--             SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin'
--         )
--     );
