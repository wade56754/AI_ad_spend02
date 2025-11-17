"""修复 ad_spend_daily 用户外键类型：Integer → UUID

Revision ID: 20251117_ad_spend_daily_user_fks_fix
Revises: 20251117_reconciliation_status_alignment
Create Date: 2025-11-17 00:03:00.000000

⚠️ 警告：本迁移脚本为模板，必须在执行前进行以下调整：
1. 确认 users 表和 user_profiles 表的 ID 对应关系
2. 验证数据迁移逻辑（user_id/created_by/updated_by 字段的数据完整性）
3. 在开发/测试环境完整验证后才能用于生产环境
4. 执行前务必备份数据库

📋 变更说明：
修复 ad_spend_daily 表中用户外键的类型不匹配问题：
- 当前 model 定义：user_id/created_by/updated_by 为 Integer, ForeignKey("users.id")
- 实际 users 表主键：id 为 UUID (GUID类型)
- 需要修正外键类型为 UUID，并确保指向正确的用户表

🎯 SoT 参考：
- DATA_SCHEMA.md §3.3.3 (ad_spend_daily 表定义)
- DATA_SCHEMA.md §3.1.1 (user_profiles 表定义)

📊 影响评估：
- 风险等级：🟡 中等（修改外键类型并迁移数据）
- 前置条件：必须确保 users 表的 id 为 UUID 类型
- 数据保全性：取决于 Integer ID 与 UUID 的映射关系
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251117_ad_spend_daily_user_fks_fix'
down_revision = '20251117_reconciliation_status_alignment'
branch_labels = None
depends_on = None


def upgrade():
    """
    升级：将 ad_spend_daily 表中的用户外键从 Integer 改为 UUID

    涉及字段：
    - user_id: Integer → UUID (指向导入数据的用户)
    - created_by: Integer → UUID (指向创建记录的用户)
    - updated_by: Integer → UUID (指向更新记录的用户)

    策略：新列+回填+切换
    """

    print("🚀 开始修复 ad_spend_daily 用户外键类型...")

    # ========================================
    # Gate Checkpoint #1: 验证前置条件
    # ========================================
    print("🔍 建议执行以下 SQL 验证前置条件：")
    print("""
    -- 验证 users 表主键类型为 UUID
    SELECT data_type FROM information_schema.columns
    WHERE table_name = 'users' AND column_name = 'id';
    -- 预期结果：uuid

    -- 验证 ad_spend_daily 表存在
    SELECT table_name FROM information_schema.tables
    WHERE table_name = 'ad_spend_daily';
    -- 预期结果：应该有1行

    -- 检查 ad_spend_daily 当前的用户外键类型
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'ad_spend_daily'
      AND column_name IN ('user_id', 'created_by', 'updated_by');
    -- 记录当前类型（可能是 integer 或已经是 uuid）
    """)

    # ========================================
    # Step 1: user_id 字段迁移
    # ========================================
    print("📌 Step 1/3: 迁移 ad_spend_daily.user_id...")

    # 1.1 添加新的 UUID 列
    op.add_column(
        'ad_spend_daily',
        sa.Column('user_id_uuid', postgresql.UUID(as_uuid=True), nullable=True, comment='导入用户ID (UUID)')
    )

    # 1.2 数据回填
    # ⚠️ 注意：这里的映射逻辑需要根据实际情况调整
    # 如果 users 表的 id 已经是 UUID，但旧的 user_id 是 Integer，
    # 那么需要一个映射表或者其他映射逻辑来转换
    # 以下示例假设可以通过某种方式将 Integer ID 转换为 UUID

    # 方案A：如果 users 表同时保留了旧的 Integer ID（如在metadata或另一个字段中）
    # op.execute("""
    #     UPDATE ad_spend_daily ad
    #     SET user_id_uuid = u.id
    #     FROM users u
    #     WHERE ad.user_id::TEXT = u.legacy_id::TEXT
    #       AND ad.user_id IS NOT NULL
    # """)

    # 方案B：如果无法映射，设置为 NULL 并记录日志（需要手动处理）
    print("⚠️  警告：user_id 字段的 Integer → UUID 映射需要手动处理")
    print("   请根据实际情况编写映射逻辑，或者将旧数据的 user_id 设置为 NULL")
    # op.execute("UPDATE ad_spend_daily SET user_id_uuid = NULL WHERE user_id IS NOT NULL")

    # 方案C：如果 user_id 实际上已经存储的是 UUID 的字符串表示（虽然列类型是 Integer）
    # 这种情况需要先检查数据的实际内容
    op.execute("""
        UPDATE ad_spend_daily ad
        SET user_id_uuid = u.id
        FROM users u
        WHERE ad.user_id::TEXT = u.id::TEXT
          AND ad.user_id IS NOT NULL
    """)

    # 1.3 删除旧的外键约束（如果存在）
    try:
        op.drop_constraint('ad_spend_daily_user_id_fkey', 'ad_spend_daily', type_='foreignkey')
    except:
        pass

    # 1.4 删除旧列
    op.drop_column('ad_spend_daily', 'user_id')

    # 1.5 重命名新列为原列名
    op.alter_column('ad_spend_daily', 'user_id_uuid', new_column_name='user_id')

    # 1.6 创建新的外键约束（指向 user_profiles.id）
    # 根据 DATA_SCHEMA.md §3.3.3，ad_spend_daily.user_id 应该指向导入数据的用户
    op.create_foreign_key(
        'ad_spend_daily_user_id_fkey',
        'ad_spend_daily',
        'user_profiles',  # 指向 user_profiles 而不是 users
        ['user_id'],
        ['id']
    )

    # 1.7 创建索引
    op.create_index('idx_ad_spend_daily_user_id', 'ad_spend_daily', ['user_id'])

    print("✅ user_id 字段迁移完成")

    # ========================================
    # Step 2: created_by 字段迁移
    # ========================================
    print("📌 Step 2/3: 迁移 ad_spend_daily.created_by...")

    # 2.1 添加新的 UUID 列
    op.add_column(
        'ad_spend_daily',
        sa.Column('created_by_uuid', postgresql.UUID(as_uuid=True), nullable=True, comment='创建人ID (UUID)')
    )

    # 2.2 数据回填
    op.execute("""
        UPDATE ad_spend_daily ad
        SET created_by_uuid = u.id
        FROM users u
        WHERE ad.created_by::TEXT = u.id::TEXT
          AND ad.created_by IS NOT NULL
    """)

    # 2.3 删除旧的外键约束（如果存在）
    try:
        op.drop_constraint('ad_spend_daily_created_by_fkey', 'ad_spend_daily', type_='foreignkey')
    except:
        pass

    # 2.4 删除旧列
    op.drop_column('ad_spend_daily', 'created_by')

    # 2.5 重命名新列
    op.alter_column('ad_spend_daily', 'created_by_uuid', new_column_name='created_by')

    # 2.6 创建新的外键约束
    op.create_foreign_key(
        'ad_spend_daily_created_by_fkey',
        'ad_spend_daily',
        'user_profiles',
        ['created_by'],
        ['id']
    )

    print("✅ created_by 字段迁移完成")

    # ========================================
    # Step 3: updated_by 字段迁移
    # ========================================
    print("📌 Step 3/3: 迁移 ad_spend_daily.updated_by...")

    # 3.1 添加新的 UUID 列
    op.add_column(
        'ad_spend_daily',
        sa.Column('updated_by_uuid', postgresql.UUID(as_uuid=True), nullable=True, comment='更新人ID (UUID)')
    )

    # 3.2 数据回填
    op.execute("""
        UPDATE ad_spend_daily ad
        SET updated_by_uuid = u.id
        FROM users u
        WHERE ad.updated_by::TEXT = u.id::TEXT
          AND ad.updated_by IS NOT NULL
    """)

    # 3.3 删除旧的外键约束（如果存在）
    try:
        op.drop_constraint('ad_spend_daily_updated_by_fkey', 'ad_spend_daily', type_='foreignkey')
    except:
        pass

    # 3.4 删除旧列
    op.drop_column('ad_spend_daily', 'updated_by')

    # 3.5 重命名新列
    op.alter_column('ad_spend_daily', 'updated_by_uuid', new_column_name='updated_by')

    # 3.6 创建新的外键约束
    op.create_foreign_key(
        'ad_spend_daily_updated_by_fkey',
        'ad_spend_daily',
        'user_profiles',
        ['updated_by'],
        ['id']
    )

    print("✅ updated_by 字段迁移完成")

    # ========================================
    # Gate Checkpoint #2: 后置验证
    # ========================================
    print("🔍 建议执行以下 SQL 验证迁移结果：")
    print("""
    -- 验证所有用户外键类型为 UUID
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'ad_spend_daily'
      AND column_name IN ('user_id', 'created_by', 'updated_by');
    -- 预期结果：data_type = 'uuid'

    -- 验证外键约束指向 user_profiles
    SELECT
        tc.table_name,
        kcu.column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_name = 'ad_spend_daily'
      AND kcu.column_name IN ('user_id', 'created_by', 'updated_by');
    -- 预期结果：foreign_table_name = 'user_profiles'

    -- 验证数据完整性
    SELECT COUNT(*) AS total_rows
    FROM ad_spend_daily;
    -- 预期结果：行数与迁移前一致

    -- 验证所有外键都有对应的 user_profiles 记录
    SELECT 'ad_spend_daily.user_id' AS field,
           COUNT(*) AS invalid_fk_count
    FROM ad_spend_daily ad
    LEFT JOIN user_profiles up ON ad.user_id = up.id
    WHERE ad.user_id IS NOT NULL AND up.id IS NULL
    UNION ALL
    SELECT 'ad_spend_daily.created_by',
           COUNT(*)
    FROM ad_spend_daily ad
    LEFT JOIN user_profiles up ON ad.created_by = up.id
    WHERE ad.created_by IS NOT NULL AND up.id IS NULL
    UNION ALL
    SELECT 'ad_spend_daily.updated_by',
           COUNT(*)
    FROM ad_spend_daily ad
    LEFT JOIN user_profiles up ON ad.updated_by = up.id
    WHERE ad.updated_by IS NOT NULL AND up.id IS NULL;
    -- 预期结果：所有 invalid_fk_count = 0
    """)

    print("✅ ad_spend_daily 用户外键修复完成！")


def downgrade():
    """
    降级：将用户外键从 UUID 回退到 Integer

    ⚠️ 警告：
    1. 回退后将丢失 UUID 到 Integer 的映射关系
    2. 回退前必须确保有完整的映射表
    3. 生产环境禁止执行回退操作
    """

    print("⚠️  开始回退 ad_spend_daily 用户外键...")
    print("❌ 警告：此回退操作会导致用户外键数据丢失映射关系")
    print("❌ 如需回退，请手动实现反向映射逻辑")

    # 此处省略回退逻辑，因为 UUID → Integer 的反向映射需要额外的映射表
    # 如果确实需要回退，必须先创建 UUID → Integer 的映射表，然后才能安全回退

    raise NotImplementedError(
        "用户外键回退操作需要自定义映射逻辑。"
        "如需回退，请创建 UUID → Integer 映射表后手动实现。"
    )
