"""对账批次状态枚举对齐 STATE_MACHINE.md

Revision ID: 20251117_reconciliation_status_alignment
Revises: 20251117_reconciliation_user_fks_to_uuid
Create Date: 2025-11-17 00:02:00.000000

⚠️ 警告：本迁移脚本为模板，必须在执行前进行以下调整：
1. 确认现有数据中 status 字段的实际取值分布
2. 验证状态映射逻辑的正确性
3. 在开发/测试环境完整验证后才能用于生产环境
4. 执行前务必备份数据库

📋 变更说明：
根据 STATE_MACHINE.md v2.3 (2025-11-17) 规范：
- reconciliation_batches.status 的合法取值：draft, pending, reviewing, closed
- 当前 model 定义的 CHECK 约束：pending, processing, completed, exception, resolved
- 需要进行状态映射和 CHECK 约束更新

🎯 SoT 参考：
- STATE_MACHINE.md §4 (全局状态一览表)
- DATA_SCHEMA.md §3.5.1 (reconciliation_batches 表定义)

📊 影响评估：
- 风险等级：🟡 中等（修改状态枚举和数据）
- 数据迁移：需要映射旧状态值到新状态值
- 回退风险：状态映射可能存在多对一，回退会丢失精确状态

📝 状态映射方案：
旧状态 → 新状态
- pending → pending（保持不变）
- processing → pending（处理中归类为待处理）
- completed → closed（已完成归类为已关闭）
- exception → reviewing（异常归类为审核中）
- resolved → closed（已解决归类为已关闭）
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251117_reconciliation_status_alignment'
down_revision = '20251117_reconciliation_user_fks_to_uuid'
branch_labels = None
depends_on = None


def upgrade():
    """
    升级：将 reconciliation_batches.status 对齐到 STATE_MACHINE.md 定义的状态枚举

    目标状态：draft, pending, reviewing, closed
    """

    print("🚀 开始对齐 reconciliation_batches 状态枚举...")

    # ========================================
    # Gate Checkpoint #1: 验证现有状态分布
    # ========================================
    print("🔍 建议执行以下 SQL 验证现有状态分布：")
    print("""
    SELECT status, COUNT(*) AS count
    FROM reconciliation_batches
    GROUP BY status
    ORDER BY count DESC;
    -- 记录每个状态的数量，确认映射逻辑是否合理
    """)

    # ========================================
    # Step 1: 备份原始状态（添加临时列）
    # ========================================
    print("📌 Step 1/5: 备份原始状态...")

    op.add_column(
        'reconciliation_batches',
        sa.Column('status_legacy', sa.String(20), nullable=True, comment='迁移前的原始状态（用于回退）')
    )

    # 将当前状态复制到备份列
    op.execute("UPDATE reconciliation_batches SET status_legacy = status")

    print("✅ 原始状态已备份到 status_legacy 列")

    # ========================================
    # Step 2: 临时移除 CHECK 约束
    # ========================================
    print("📌 Step 2/5: 移除旧的 CHECK 约束...")

    # ⚠️ 注意：约束名需要根据实际数据库调整！
    # 使用 \d+ reconciliation_batches 查看实际约束名
    try:
        op.drop_constraint(
            'check_batch_status',  # TODO: 确认实际约束名
            'reconciliation_batches',
            type_='check'
        )
        print("✅ 旧的 CHECK 约束已移除")
    except Exception as e:
        print(f"⚠️  移除 CHECK 约束失败（可能不存在）：{e}")

    # ========================================
    # Step 3: 数据迁移 - 映射旧状态到新状态
    # ========================================
    print("📌 Step 3/5: 迁移状态数据...")

    # 状态映射逻辑
    status_mapping = {
        'pending': 'pending',       # 待处理 → 待处理（保持不变）
        'processing': 'pending',    # 处理中 → 待处理（归类为未完成）
        'completed': 'closed',      # 已完成 → 已关闭（终态）
        'exception': 'reviewing',   # 异常 → 审核中（需要人工介入）
        'resolved': 'closed',       # 已解决 → 已关闭（终态）
    }

    # 执行状态映射
    for old_status, new_status in status_mapping.items():
        result = op.execute(f"""
            UPDATE reconciliation_batches
            SET status = '{new_status}'
            WHERE status = '{old_status}'
        """)
        print(f"   • {old_status} → {new_status}")

    # 处理未预期的状态值（如果存在）
    # 将所有不在新枚举中的状态暂时设置为 'draft'（需要人工审核）
    op.execute("""
        UPDATE reconciliation_batches
        SET status = 'draft'
        WHERE status NOT IN ('draft', 'pending', 'reviewing', 'closed')
    """)

    print("✅ 状态数据迁移完成")

    # ========================================
    # Step 4: 创建新的 CHECK 约束
    # ========================================
    print("📌 Step 4/5: 创建新的 CHECK 约束...")

    # 根据 STATE_MACHINE.md 创建新的 CHECK 约束
    op.create_check_constraint(
        'check_batch_status',  # 约束名
        'reconciliation_batches',
        "status IN ('draft', 'pending', 'reviewing', 'closed')"
    )

    print("✅ 新的 CHECK 约束已创建")

    # ========================================
    # Step 5: 添加注释说明
    # ========================================
    print("📌 Step 5/5: 更新列注释...")

    op.execute("""
        COMMENT ON COLUMN reconciliation_batches.status IS
        '对账状态（参考 STATE_MACHINE.md §4）：draft=草稿, pending=待处理, reviewing=审核中, closed=已关闭'
    """)

    op.execute("""
        COMMENT ON COLUMN reconciliation_batches.status_legacy IS
        '迁移前的原始状态（保留7天后可删除，用于回退验证）'
    """)

    print("✅ 列注释已更新")

    # ========================================
    # Gate Checkpoint #2: 后置验证
    # ========================================
    print("🔍 建议执行以下 SQL 验证迁移结果：")
    print("""
    -- 验证新状态分布
    SELECT status, COUNT(*) AS count
    FROM reconciliation_batches
    GROUP BY status
    ORDER BY status;
    -- 预期结果：status 只有 draft, pending, reviewing, closed 四种

    -- 验证 CHECK 约束
    SELECT conname, pg_get_constraintdef(oid) AS constraint_def
    FROM pg_constraint
    WHERE conrelid = 'reconciliation_batches'::regclass
      AND contype = 'c'
      AND conname = 'check_batch_status';
    -- 预期结果：约束定义包含 draft, pending, reviewing, closed

    -- 对比迁移前后状态分布
    SELECT
        status_legacy AS old_status,
        status AS new_status,
        COUNT(*) AS count
    FROM reconciliation_batches
    GROUP BY status_legacy, status
    ORDER BY count DESC;
    -- 验证状态映射的正确性

    -- 检查是否有未映射的状态
    SELECT status, COUNT(*) AS count
    FROM reconciliation_batches
    WHERE status NOT IN ('draft', 'pending', 'reviewing', 'closed')
    GROUP BY status;
    -- 预期结果：应该为空（0行）
    """)

    print("✅ reconciliation_batches 状态枚举对齐完成！")
    print("📝 建议：观察 7 天后，确认无问题可执行以下 SQL 删除备份列：")
    print("   ALTER TABLE reconciliation_batches DROP COLUMN status_legacy;")


def downgrade():
    """
    降级：恢复旧的状态枚举值

    ⚠️ 警告：
    1. 状态映射存在多对一（processing/completed/resolved → pending/closed），回退会丢失精确状态
    2. 回退前必须验证 status_legacy 列存在且完整
    3. 生产环境慎用回退操作
    """

    print("⚠️  开始回退 reconciliation_batches 状态枚举...")

    # ========================================
    # Step 1: 验证是否可以回退
    # ========================================
    print("🔍 建议执行以下 SQL 验证是否可以回退：")
    print("""
    -- 检查 status_legacy 列是否存在
    SELECT column_name FROM information_schema.columns
    WHERE table_name = 'reconciliation_batches' AND column_name = 'status_legacy';
    -- 预期结果：应该有1行

    -- 检查 status_legacy 数据完整性
    SELECT
        COUNT(*) AS total_rows,
        COUNT(status_legacy) AS legacy_status_count,
        COUNT(*) - COUNT(status_legacy) AS missing_count
    FROM reconciliation_batches;
    -- 预期结果：missing_count = 0
    """)

    # ========================================
    # Step 2: 移除新的 CHECK 约束
    # ========================================
    print("📌 Step 1/4: 移除新的 CHECK 约束...")

    try:
        op.drop_constraint('check_batch_status', 'reconciliation_batches', type_='check')
        print("✅ 新的 CHECK 约束已移除")
    except Exception as e:
        print(f"⚠️  移除 CHECK 约束失败：{e}")

    # ========================================
    # Step 3: 恢复原始状态
    # ========================================
    print("📌 Step 2/4: 恢复原始状态数据...")

    op.execute("""
        UPDATE reconciliation_batches
        SET status = status_legacy
        WHERE status_legacy IS NOT NULL
    """)

    print("✅ 原始状态已恢复")

    # ========================================
    # Step 4: 重建旧的 CHECK 约束
    # ========================================
    print("📌 Step 3/4: 重建旧的 CHECK 约束...")

    op.create_check_constraint(
        'check_batch_status',
        'reconciliation_batches',
        "status IN ('pending', 'processing', 'completed', 'exception', 'resolved')"
    )

    print("✅ 旧的 CHECK 约束已重建")

    # ========================================
    # Step 5: 删除备份列
    # ========================================
    print("📌 Step 4/4: 删除备份列...")

    op.drop_column('reconciliation_batches', 'status_legacy')

    print("✅ 备份列已删除")

    # ========================================
    # 后置验证
    # ========================================
    print("🔍 建议执行以下 SQL 验证回退结果：")
    print("""
    -- 验证状态分布
    SELECT status, COUNT(*) AS count
    FROM reconciliation_batches
    GROUP BY status
    ORDER BY status;
    -- 预期结果：status 应恢复为 pending, processing, completed, exception, resolved

    -- 验证 CHECK 约束
    SELECT conname, pg_get_constraintdef(oid) AS constraint_def
    FROM pg_constraint
    WHERE conrelid = 'reconciliation_batches'::regclass
      AND contype = 'c'
      AND conname = 'check_batch_status';
    -- 预期结果：约束定义包含旧的5个状态值
    """)

    print("✅ 回退完成！")
    print("⚠️  注意：由于状态映射存在多对一，部分记录的精确状态可能已丢失")
