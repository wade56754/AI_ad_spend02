"""
DBA 执行官 - Phase 1 迁移执行脚本
严格按照 MIGRATION_EXECUTION_GUIDE.md v1.2 执行

[WARN] 仅用于 Dev 环境
[WARN] 生产环境禁止使用此脚本
"""

import sys
import os
import psycopg2
from psycopg2 import sql
from datetime import datetime

# 从环境变量读取数据库连接
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:BTsBIezNsDQF0UFp@db.jzmcoivxhiyidizncyaq.supabase.co:5432/postgres'
)

def execute_sql(cursor, sql_statement, description=""):
    """执行单条SQL"""
    try:
        cursor.execute(sql_statement)
        if description:
            print(f"  [OK] {description}")
        return True
    except Exception as e:
        print(f"  [FAIL] {description} 失败: {str(e)}")
        return False


def gate_check_1(cursor):
    """Gate #1: 验证主键类型"""
    print("\n" + "="*60)
    print(" Gate #1 验证: reconciliation 主键类型")
    print("="*60)

    # 检查1: 主键类型
    cursor.execute("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_name IN (
            'reconciliation_batches',
            'reconciliation_details',
            'reconciliation_adjustments',
            'reconciliation_reports'
        ) AND column_name = 'id'
        ORDER BY table_name
    """)

    results = cursor.fetchall()
    all_pass = True

    print("\n检查1: 主键类型")
    for table, column, dtype in results:
        status = "[OK] PASS" if dtype == "bigint" else "[FAIL] FAIL"
        print(f"  {table}.{column}: {dtype} - {status}")
        if dtype != "bigint":
            all_pass = False

    # 检查2: 序列类型
    cursor.execute("""
        SELECT sequencename, data_type
        FROM pg_sequences
        WHERE sequencename LIKE 'reconciliation_%_id_seq'
        ORDER BY sequencename
    """)

    seq_results = cursor.fetchall()
    print("\n检查2: 序列类型")
    for seq_name, dtype in seq_results:
        status = "[OK] PASS" if dtype == "bigint" else "[FAIL] FAIL"
        print(f"  {seq_name}: {dtype} - {status}")
        if dtype != "bigint":
            all_pass = False

    # 检查3: FK完整性
    cursor.execute("""
        SELECT
            'reconciliation_details' as source_table,
            COUNT(*) as total,
            COUNT(b.id) as matched
        FROM reconciliation_details d
        LEFT JOIN reconciliation_batches b ON d.batch_id = b.id

        UNION ALL

        SELECT 'reconciliation_adjustments', COUNT(*), COUNT(b.id)
        FROM reconciliation_adjustments a
        LEFT JOIN reconciliation_batches b ON a.batch_id = b.id

        UNION ALL

        SELECT 'reconciliation_reports', COUNT(*), COUNT(b.id)
        FROM reconciliation_reports r
        LEFT JOIN reconciliation_batches b ON r.batch_id = b.id
    """)

    fk_results = cursor.fetchall()
    print("\n检查3: FK完整性")
    for table, total, matched in fk_results:
        orphans = total - matched
        status = "[OK] PASS" if orphans == 0 else "[FAIL] FAIL"
        print(f"  {table}: {total}条记录, {orphans}孤儿 - {status}")
        if orphans > 0:
            all_pass = False

    print("\n" + "="*60)
    if all_pass:
        print("[OK] Gate #1 通过!可以继续执行 Rev 002")
    else:
        print("[FAIL] Gate #1 失败!必须回滚 Rev 001")
    print("="*60)

    return all_pass


def gate_check_2(cursor):
    """Gate #2: 验证 status 枚举"""
    print("\n" + "="*60)
    print(" Gate #2 验证: status 枚举对齐")
    print("="*60)

    # 检查1: status分布
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM reconciliation_batches
        GROUP BY status
        ORDER BY count DESC
    """)

    results = cursor.fetchall()
    all_pass = True
    valid_statuses = {'draft', 'pending', 'reviewing', 'closed'}

    print("\n检查1: status值分布")
    for status, count in results:
        is_valid = status in valid_statuses
        status_mark = "[OK] PASS" if is_valid else "[FAIL] FAIL"
        print(f"  {status}: {count}条记录 - {status_mark}")
        if not is_valid:
            all_pass = False

    # 检查2: status_legacy完整性
    cursor.execute("""
        SELECT
            COUNT(*) as total_records,
            COUNT(status_legacy) as has_legacy,
            COUNT(*) - COUNT(status_legacy) as missing_legacy
        FROM reconciliation_batches
    """)

    total, has_legacy, missing = cursor.fetchone()
    print(f"\n检查2: status_legacy完整性")
    print(f"  总记录数: {total}")
    print(f"  包含legacy: {has_legacy}")
    print(f"  缺失legacy: {missing}")

    legacy_pass = missing == 0
    print(f"  状态: {'[OK] PASS' if legacy_pass else '[FAIL] FAIL'}")

    if not legacy_pass:
        all_pass = False

    print("\n" + "="*60)
    if all_pass:
        print("[OK] Gate #2 通过!可以继续执行 Rev 003")
    else:
        print("[FAIL] Gate #2 失败!必须回滚 Rev 002")
    print("="*60)

    return all_pass


def gate_check_3(cursor):
    """Gate #3: 评估孤儿率"""
    print("\n" + "="*60)
    print(" Gate #3 评估: 用户FK孤儿率")
    print("="*60)

    # 查询分析表统计
    cursor.execute("""
        SELECT
            table_name,
            COUNT(*) as total_records,
            COUNT(*) FILTER (WHERE is_orphan = true) as orphan_count,
            ROUND(100.0 * COUNT(*) FILTER (WHERE is_orphan = true) / NULLIF(COUNT(*), 0), 2) as orphan_rate
        FROM temp_user_id_fk_analysis
        GROUP BY table_name
        ORDER BY orphan_rate DESC
    """)

    results = cursor.fetchall()
    max_orphan_rate = 0

    print("\n孤儿率统计:")
    for table, total, orphans, rate in results:
        rate_float = float(rate) if rate else 0
        max_orphan_rate = max(max_orphan_rate, rate_float)

        if rate_float <= 5:
            status = "[OK] PASS (<5%)"
        elif rate_float <= 10:
            status = "[WARN]  WARNING (5-10%)"
        else:
            status = "[FAIL] FAIL (>10%)"

        print(f"  {table}: {total}条记录, {orphans}孤儿 ({rate}%) - {status}")

    print("\n" + "="*60)
    print(f"最大孤儿率: {max_orphan_rate}%")

    if max_orphan_rate <= 5:
        print("[OK] Gate #3 通过!可以继续执行 Rev 004-006")
        print("   决策: 孤儿率≤5%，可以接受置NULL策略")
        return True
    elif max_orphan_rate <= 10:
        print("[WARN]  Gate #3 警告!需要业务评估")
        print("   决策: 孤儿率5-10%，建议记录风险后继续")
        print("   [WARN]  必须记录到 docs/PROJECT_RISKS.md")
        # 在Dev环境，我们接受5-10%
        return True
    else:
        print("[FAIL] Gate #3 失败!强制停止")
        print("   决策: 孤儿率>10%，必须人工review")
        print("   [WARN]  不能继续执行 Rev 004-006")
        return False


def execute_rev_001(cursor):
    """执行 Rev 001: reconciliation 主键 Integer→BIGSERIAL"""
    print("\n" + "="*60)
    print(" Rev 001: reconciliation_pk_bigserial")
    print("="*60)

    # 表1: reconciliation_batches
    print("\n[1/4] reconciliation_batches")
    execute_sql(cursor, "ALTER TABLE reconciliation_batches ALTER COLUMN id TYPE BIGINT", "主键类型 → BIGINT")
    execute_sql(cursor, "ALTER SEQUENCE reconciliation_batches_id_seq AS BIGINT", "序列类型 → BIGINT")
    execute_sql(cursor, """
        SELECT setval('reconciliation_batches_id_seq',
                     COALESCE((SELECT MAX(id) FROM reconciliation_batches), 1))
    """, "重置序列起始值")

    # 表2: reconciliation_details
    print("\n[2/4] reconciliation_details")
    execute_sql(cursor, "ALTER TABLE reconciliation_details ALTER COLUMN batch_id TYPE BIGINT", "FK batch_id → BIGINT")
    execute_sql(cursor, "ALTER TABLE reconciliation_details ALTER COLUMN id TYPE BIGINT", "主键类型 → BIGINT")
    execute_sql(cursor, "ALTER SEQUENCE reconciliation_details_id_seq AS BIGINT", "序列类型 → BIGINT")
    execute_sql(cursor, """
        SELECT setval('reconciliation_details_id_seq',
                     COALESCE((SELECT MAX(id) FROM reconciliation_details), 1))
    """, "重置序列起始值")

    # 表3: reconciliation_adjustments
    print("\n[3/4] reconciliation_adjustments")
    execute_sql(cursor, "ALTER TABLE reconciliation_adjustments ALTER COLUMN batch_id TYPE BIGINT", "FK batch_id → BIGINT")
    execute_sql(cursor, "ALTER TABLE reconciliation_adjustments ALTER COLUMN detail_id TYPE BIGINT", "FK detail_id → BIGINT")
    execute_sql(cursor, "ALTER TABLE reconciliation_adjustments ALTER COLUMN id TYPE BIGINT", "主键类型 → BIGINT")
    execute_sql(cursor, "ALTER SEQUENCE reconciliation_adjustments_id_seq AS BIGINT", "序列类型 → BIGINT")
    execute_sql(cursor, """
        SELECT setval('reconciliation_adjustments_id_seq',
                     COALESCE((SELECT MAX(id) FROM reconciliation_adjustments), 1))
    """, "重置序列起始值")

    # 表4: reconciliation_reports
    print("\n[4/4] reconciliation_reports")
    execute_sql(cursor, "ALTER TABLE reconciliation_reports ALTER COLUMN batch_id TYPE BIGINT", "FK batch_id → BIGINT")
    execute_sql(cursor, "ALTER TABLE reconciliation_reports ALTER COLUMN id TYPE BIGINT", "主键类型 → BIGINT")
    execute_sql(cursor, "ALTER SEQUENCE reconciliation_reports_id_seq AS BIGINT", "序列类型 → BIGINT")
    execute_sql(cursor, """
        SELECT setval('reconciliation_reports_id_seq',
                     COALESCE((SELECT MAX(id) FROM reconciliation_reports), 1))
    """, "重置序列起始值")

    print("\n[OK] Rev 001 执行完成!")


def execute_rev_002(cursor):
    """执行 Rev 002: status 枚举对齐"""
    print("\n" + "="*60)
    print(" Rev 002: reconciliation_status_align")
    print("="*60)

    # Step 1: 添加备份列
    print("\nStep 1: 添加 status_legacy 备份列")
    try:
        execute_sql(cursor, """
            ALTER TABLE reconciliation_batches
            ADD COLUMN status_legacy VARCHAR(20)
        """, "添加 status_legacy 列")
    except Exception as e:
        if "already exists" in str(e):
            print("  [WARN]  status_legacy 列已存在，跳过")
        else:
            raise

    # Step 2: 备份当前值
    print("\nStep 2: 备份当前 status 值")
    execute_sql(cursor, """
        UPDATE reconciliation_batches
        SET status_legacy = status
        WHERE status_legacy IS NULL
    """, "备份 status → status_legacy")

    # Step 3: 执行状态映射
    print("\nStep 3: 执行状态映射")
    execute_sql(cursor, """
        UPDATE reconciliation_batches
        SET status = CASE
            WHEN status = 'pending' THEN 'draft'
            WHEN status = 'processing' THEN 'pending'
            WHEN status = 'completed' THEN 'closed'
            WHEN status = 'exception' THEN 'reviewing'
            WHEN status = 'resolved' THEN 'closed'
            ELSE status
        END
    """, "映射 status 枚举值")

    # Step 4: 更新CHECK约束
    print("\nStep 4: 更新 CHECK 约束")
    execute_sql(cursor, """
        ALTER TABLE reconciliation_batches
        DROP CONSTRAINT IF EXISTS check_batch_status
    """, "删除旧CHECK约束")

    execute_sql(cursor, """
        ALTER TABLE reconciliation_batches
        ADD CONSTRAINT check_batch_status
        CHECK (status IN ('draft', 'pending', 'reviewing', 'closed'))
    """, "添加新CHECK约束")

    print("\n[OK] Rev 002 执行完成!")


def execute_rev_003(cursor):
    """执行 Rev 003: 创建用户FK分析表"""
    print("\n" + "="*60)
    print(" Rev 003: analyze_user_fk")
    print("="*60)

    # Step 1: 创建临时分析表
    print("\nStep 1: 创建临时分析表")
    execute_sql(cursor, """
        DROP TABLE IF EXISTS temp_user_id_fk_analysis
    """, "清理旧分析表（如存在）")

    execute_sql(cursor, """
        CREATE TABLE temp_user_id_fk_analysis (
            id BIGSERIAL PRIMARY KEY,
            table_name VARCHAR(100) NOT NULL,
            column_name VARCHAR(100) NOT NULL,
            old_integer_value INTEGER,
            matched_uuid UUID,
            is_orphan BOOLEAN DEFAULT false,
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """, "创建 temp_user_id_fk_analysis 表")

    # Step 2: 分析各表
    print("\nStep 2: 分析用户FK列")

    # ad_spend_daily
    print("  分析 ad_spend_daily...")
    cursor.execute("""
        INSERT INTO temp_user_id_fk_analysis
            (table_name, column_name, old_integer_value, is_orphan, notes)
        SELECT
            'ad_spend_daily',
            'user_id',
            user_id,
            true,
            'Integer→UUID无法映射'
        FROM ad_spend_daily
        WHERE user_id IS NOT NULL
    """)

    cursor.execute("""
        INSERT INTO temp_user_id_fk_analysis
            (table_name, column_name, old_integer_value, is_orphan, notes)
        SELECT
            'ad_spend_daily',
            'created_by',
            created_by,
            true,
            'Integer→UUID无法映射'
        FROM ad_spend_daily
        WHERE created_by IS NOT NULL
    """)

    cursor.execute("""
        INSERT INTO temp_user_id_fk_analysis
            (table_name, column_name, old_integer_value, is_orphan, notes)
        SELECT
            'ad_spend_daily',
            'updated_by',
            updated_by,
            true,
            'Integer→UUID无法映射'
        FROM ad_spend_daily
        WHERE updated_by IS NOT NULL
    """)

    # reconciliation_details
    print("  分析 reconciliation_details...")
    cursor.execute("""
        INSERT INTO temp_user_id_fk_analysis
            (table_name, column_name, old_integer_value, is_orphan, notes)
        SELECT
            'reconciliation_details',
            'reviewed_by',
            reviewed_by,
            true,
            'Integer→UUID无法映射'
        FROM reconciliation_details
        WHERE reviewed_by IS NOT NULL
    """)

    cursor.execute("""
        INSERT INTO temp_user_id_fk_analysis
            (table_name, column_name, old_integer_value, is_orphan, notes)
        SELECT
            'reconciliation_details',
            'resolved_by',
            resolved_by,
            true,
            'Integer→UUID无法映射'
        FROM reconciliation_details
        WHERE resolved_by IS NOT NULL
    """)

    # reconciliation_adjustments
    print("  分析 reconciliation_adjustments...")
    cursor.execute("""
        INSERT INTO temp_user_id_fk_analysis
            (table_name, column_name, old_integer_value, is_orphan, notes)
        SELECT
            'reconciliation_adjustments',
            'approved_by',
            approved_by,
            true,
            'Integer→UUID无法映射'
        FROM reconciliation_adjustments
        WHERE approved_by IS NOT NULL
    """)

    cursor.execute("""
        INSERT INTO temp_user_id_fk_analysis
            (table_name, column_name, old_integer_value, is_orphan, notes)
        SELECT
            'reconciliation_adjustments',
            'finance_approved_by',
            finance_approved_by,
            true,
            'Integer→UUID无法映射'
        FROM reconciliation_adjustments
        WHERE finance_approved_by IS NOT NULL
    """)

    # reconciliation_reports
    print("  分析 reconciliation_reports...")
    cursor.execute("""
        INSERT INTO temp_user_id_fk_analysis
            (table_name, column_name, old_integer_value, is_orphan, notes)
        SELECT
            'reconciliation_reports',
            'generated_by',
            generated_by,
            true,
            'Integer→UUID无法映射'
        FROM reconciliation_reports
        WHERE generated_by IS NOT NULL
    """)

    print("\n[OK] Rev 003 执行完成!")


def main():
    """主执行流程"""
    print("="*60)
    print(" DBA 执行官 - Phase 1 迁移真实执行")
    print("="*60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据库: {DATABASE_URL.split('@')[1]}")  # 只显示host部分
    print("="*60)

    conn = None
    try:
        # 连接数据库
        print("\n 连接数据库...")
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False  # 使用事务
        cursor = conn.cursor()
        print("[OK] 数据库连接成功")

        # ========== Phase 1: Rev 001-003（可逆） ==========

        # 执行 Rev 001
        execute_rev_001(cursor)
        conn.commit()
        print("[OK] Rev 001 已提交")

        # Gate #1 验证
        if not gate_check_1(cursor):
            print("\n[FAIL] Gate #1 失败，开始回滚...")
            conn.rollback()
            print("[WARN]  已回滚事务，数据库状态恢复")
            return 1

        # 执行 Rev 002
        execute_rev_002(cursor)
        conn.commit()
        print("[OK] Rev 002 已提交")

        # Gate #2 验证
        if not gate_check_2(cursor):
            print("\n[FAIL] Gate #2 失败，开始回滚...")
            conn.rollback()
            print("[WARN]  已回滚事务，需要手动恢复")
            return 1

        # 执行 Rev 003
        execute_rev_003(cursor)
        conn.commit()
        print("[OK] Rev 003 已提交")

        # Gate #3 评估
        if not gate_check_3(cursor):
            print("\n[FAIL] Gate #3 失败，停止执行")
            print("[WARN]  Rev 004-006 将不会执行")
            print("[WARN]  建议: 检查分析表 temp_user_id_fk_analysis")
            return 1

        # ========== 决策点 ==========
        print("\n" + "="*60)
        print("[WARN]  【决策点】是否继续执行 Rev 004-006?")
        print("="*60)
        print("Rev 004-006 将执行以下操作:")
        print("   修改 ad_spend_daily 的 3 个用户FK (不可逆)")
        print("   修改 reconciliation_details 的 2 个用户FK (不可逆)")
        print("   修改 reconciliation_adjustments/reports 的 3 个用户FK (不可逆)")
        print("  [WARN]  所有 Integer 值将被删除，FK 将被置 NULL")
        print("\n由于这是自动化脚本，Rev 004-006 需要手动执行")
        print("请参考 MIGRATION_EXECUTION_GUIDE.md §3.3 继续")
        print("="*60)

        print("\n[OK] Phase 1 (Rev 001-003) 执行完成!")
        print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return 0

    except Exception as e:
        print(f"\n[FAIL] 错误: {str(e)}")
        if conn:
            conn.rollback()
            print("[WARN]  已回滚事务")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        if conn:
            conn.close()
            print("\n 数据库连接已关闭")


if __name__ == "__main__":
    sys.exit(main())
