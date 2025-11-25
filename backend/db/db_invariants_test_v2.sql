-- =============================================================================
-- AI 广告代投系统 - 数据库不变量测试脚本 v2.0
-- 基于: DATA_SCHEMA.md v5.2, MASTER.md v3.4, STATE_MACHINE.md v2.6
-- 对应文档: TEST_CASES_v2.0.md
-- 版本: v2.0
-- 创建日期: 2025-11-25
-- =============================================================================

-- 测试约定:
-- 1. 本测试套件为顺序执行的单文件测试套件，测试用例之间存在依赖关系
-- 2. 测试数据使用特定 UUID/ID 前缀，便于清理
-- 3. 预期失败的操作通过 DO EXCEPTION 块验证
-- 4. 清理阶段使用 BEGIN...EXCEPTION...END 确保触发器恢复

-- =============================================================================
-- 0. 测试辅助函数
-- =============================================================================

-- 0.1 测试断言函数
CREATE OR REPLACE FUNCTION test_assert(
    p_condition BOOLEAN,
    p_test_name TEXT,
    p_error_message TEXT DEFAULT 'Test assertion failed'
)
RETURNS VOID AS $$
BEGIN
    IF NOT p_condition THEN
        RAISE EXCEPTION 'TEST_FAILED [%]: %', p_test_name, p_error_message;
    ELSE
        RAISE NOTICE 'PASS: %', p_test_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 0.2 测试期望异常函数 (记录预期的异常捕获)
CREATE OR REPLACE FUNCTION test_expect_exception(
    p_test_name TEXT,
    p_expected_pattern TEXT
)
RETURNS VOID AS $$
BEGIN
    RAISE NOTICE 'PASS: % (expected exception matched: %)', p_test_name, p_expected_pattern;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 1. 测试数据准备
-- =============================================================================

DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_user2_id UUID := '00000000-0000-0000-0000-000000000002';
    v_test_project_id BIGINT;
    v_test_supplier_id UUID := '00000000-0000-0000-0000-000000000010';
    v_test_supplier2_id UUID := '00000000-0000-0000-0000-000000000011';
    v_test_channel_id UUID := '00000000-0000-0000-0000-000000000020';
    v_test_ad_account_id BIGINT;
    v_test_ad_account2_id BIGINT;
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '开始准备测试数据...';
    RAISE NOTICE '========================================';

    -- 1.1 清理可能存在的旧测试数据 (需要先禁用触发器)
    BEGIN
        ALTER TABLE ledger_entries DISABLE TRIGGER trg_ledger_immutable_update;
        ALTER TABLE ledger_entries DISABLE TRIGGER trg_ledger_immutable_delete;
        ALTER TABLE suppliers DISABLE TRIGGER trg_suppliers_balance_readonly;
    EXCEPTION WHEN OTHERS THEN
        NULL; -- 触发器可能不存在，忽略错误
    END;

    DELETE FROM reconciliation_adjustments WHERE created_by = v_test_user_id;
    DELETE FROM reconciliation_details WHERE batch_id IN (SELECT id FROM reconciliation_batches WHERE created_by = v_test_user_id);
    DELETE FROM reconciliation_reports WHERE batch_id IN (SELECT id FROM reconciliation_batches WHERE created_by = v_test_user_id);
    DELETE FROM reconciliation_batches WHERE created_by = v_test_user_id;
    DELETE FROM ledger_entries WHERE created_by = v_test_user_id;
    DELETE FROM daily_reports WHERE created_by = v_test_user_id;
    DELETE FROM topup_transactions WHERE created_by = v_test_user_id;
    DELETE FROM topup_requests WHERE applicant_id = v_test_user_id;
    DELETE FROM transfer_requests WHERE created_by = v_test_user_id;
    DELETE FROM ad_accounts WHERE created_by = v_test_user_id;
    DELETE FROM projects WHERE created_by = v_test_user_id;
    DELETE FROM suppliers WHERE id IN (v_test_supplier_id, v_test_supplier2_id);
    DELETE FROM channels WHERE id = v_test_channel_id;
    DELETE FROM users WHERE id IN (v_test_user_id, v_test_user2_id);

    -- 重新启用触发器
    BEGIN
        ALTER TABLE ledger_entries ENABLE TRIGGER trg_ledger_immutable_update;
        ALTER TABLE ledger_entries ENABLE TRIGGER trg_ledger_immutable_delete;
        ALTER TABLE suppliers ENABLE TRIGGER trg_suppliers_balance_readonly;
    EXCEPTION WHEN OTHERS THEN
        NULL;
    END;

    -- 1.2 创建测试用户
    INSERT INTO users (id, username, full_name, role)
    VALUES
        (v_test_user_id, '_test_user_001', 'Test User 1', 'admin'),
        (v_test_user2_id, '_test_user_002', 'Test User 2', 'finance');

    -- 1.3 创建测试项目
    INSERT INTO projects (name, client_name, client_company, status, created_by)
    VALUES ('_test_project', '_test_client', '_test_company', 'active', v_test_user_id)
    RETURNING id INTO v_test_project_id;

    -- 1.4 创建测试供应商 (两个，用于迁移测试)
    INSERT INTO suppliers (id, name, code, balance, status)
    VALUES
        (v_test_supplier_id, '_test_supplier_1', '_TEST_SUP_001', 0.00, 'active'),
        (v_test_supplier2_id, '_test_supplier_2', '_TEST_SUP_002', 0.00, 'active');

    -- 1.5 创建测试渠道
    INSERT INTO channels (id, name, platform, status, created_by)
    VALUES (v_test_channel_id, '_test_channel', 'test_platform', 'active', v_test_user_id);

    -- 1.6 创建测试广告账户 (两个，用于迁移测试)
    INSERT INTO ad_accounts (project_id, channel_id, supplier_id, name, account_code, status, created_by)
    VALUES
        (v_test_project_id, v_test_channel_id, v_test_supplier_id, '_test_ad_account_1', '_TEST_ACC_001', 'active', v_test_user_id),
        (v_test_project_id, v_test_channel_id, v_test_supplier2_id, '_test_ad_account_2', '_TEST_ACC_002', 'dead', v_test_user_id);

    SELECT id INTO v_test_ad_account_id FROM ad_accounts WHERE account_code = '_TEST_ACC_001';
    SELECT id INTO v_test_ad_account2_id FROM ad_accounts WHERE account_code = '_TEST_ACC_002';

    RAISE NOTICE '测试数据准备完成: project_id=%, ad_account_id=%, ad_account2_id=%',
        v_test_project_id, v_test_ad_account_id, v_test_ad_account2_id;
END $$;

-- =============================================================================
-- 2. P0 测试: 账本不可变性 (Section 2)
-- =============================================================================

-- TC-LED-001: 禁止 UPDATE ledger_entries
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_project_id BIGINT;
    v_ledger_id BIGINT;
    v_exception_caught BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-LED-001: 禁止 UPDATE ledger_entries';
    RAISE NOTICE '----------------------------------------';

    SELECT id INTO v_test_project_id FROM projects WHERE created_by = v_test_user_id LIMIT 1;

    INSERT INTO ledger_entries (ledger_type, project_id, entry_type, amount, currency, occurred_at, created_by)
    VALUES ('PROJECT', v_test_project_id, 'REVENUE', 100.00, 'CNY', NOW(), v_test_user_id)
    RETURNING id INTO v_ledger_id;

    BEGIN
        UPDATE ledger_entries SET amount = 200.00 WHERE id = v_ledger_id;
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLERRM LIKE '%LEDGER_IMMUTABLE%' THEN
                v_exception_caught := TRUE;
                PERFORM test_expect_exception('TC-LED-001', 'LEDGER_IMMUTABLE');
            ELSE
                RAISE;
            END IF;
    END;

    IF NOT v_exception_caught THEN
        RAISE EXCEPTION 'TEST_FAILED [TC-LED-001]: UPDATE ledger_entries should have been blocked';
    END IF;
END $$;

-- TC-LED-002: 禁止 DELETE ledger_entries
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_project_id BIGINT;
    v_ledger_id BIGINT;
    v_exception_caught BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-LED-002: 禁止 DELETE ledger_entries';
    RAISE NOTICE '----------------------------------------';

    SELECT id INTO v_test_project_id FROM projects WHERE created_by = v_test_user_id LIMIT 1;

    INSERT INTO ledger_entries (ledger_type, project_id, entry_type, amount, currency, occurred_at, created_by)
    VALUES ('PROJECT', v_test_project_id, 'TOPUP', 500.00, 'CNY', NOW(), v_test_user_id)
    RETURNING id INTO v_ledger_id;

    BEGIN
        DELETE FROM ledger_entries WHERE id = v_ledger_id;
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLERRM LIKE '%LEDGER_IMMUTABLE%' THEN
                v_exception_caught := TRUE;
                PERFORM test_expect_exception('TC-LED-002', 'LEDGER_IMMUTABLE');
            ELSE
                RAISE;
            END IF;
    END;

    IF NOT v_exception_caught THEN
        RAISE EXCEPTION 'TEST_FAILED [TC-LED-002]: DELETE ledger_entries should have been blocked';
    END IF;
END $$;

-- =============================================================================
-- 3. P0 测试: 双账本隔离 (Section 3)
-- =============================================================================

-- TC-LED-003: PROJECT 账本必须关联 project_id
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_exception_caught BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-LED-003: PROJECT 账本必须关联 project_id';
    RAISE NOTICE '----------------------------------------';

    BEGIN
        INSERT INTO ledger_entries (ledger_type, project_id, entry_type, amount, currency, occurred_at, created_by)
        VALUES ('PROJECT', NULL, 'REVENUE', 100.00, 'CNY', NOW(), v_test_user_id);
    EXCEPTION
        WHEN check_violation THEN
            v_exception_caught := TRUE;
            PERFORM test_expect_exception('TC-LED-003', 'chk_ledger_type_entity');
    END;

    IF NOT v_exception_caught THEN
        RAISE EXCEPTION 'TEST_FAILED [TC-LED-003]: PROJECT ledger with NULL project_id should have been blocked';
    END IF;
END $$;

-- TC-LED-004: PROJECT 账本禁止关联 supplier_id
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_project_id BIGINT;
    v_test_supplier_id UUID := '00000000-0000-0000-0000-000000000010';
    v_exception_caught BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-LED-004: PROJECT 账本禁止关联 supplier_id';
    RAISE NOTICE '----------------------------------------';

    SELECT id INTO v_test_project_id FROM projects WHERE created_by = v_test_user_id LIMIT 1;

    BEGIN
        INSERT INTO ledger_entries (ledger_type, project_id, supplier_id, entry_type, amount, currency, occurred_at, created_by)
        VALUES ('PROJECT', v_test_project_id, v_test_supplier_id, 'REVENUE', 100.00, 'CNY', NOW(), v_test_user_id);
    EXCEPTION
        WHEN check_violation THEN
            v_exception_caught := TRUE;
            PERFORM test_expect_exception('TC-LED-004', 'chk_ledger_type_entity');
    END;

    IF NOT v_exception_caught THEN
        RAISE EXCEPTION 'TEST_FAILED [TC-LED-004]: PROJECT ledger with supplier_id should have been blocked';
    END IF;
END $$;

-- TC-LED-005: SUPPLIER 账本必须关联 supplier_id
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_exception_caught BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-LED-005: SUPPLIER 账本必须关联 supplier_id';
    RAISE NOTICE '----------------------------------------';

    BEGIN
        INSERT INTO ledger_entries (ledger_type, supplier_id, entry_type, amount, currency, occurred_at, created_by)
        VALUES ('SUPPLIER', NULL, 'COST', 100.00, 'CNY', NOW(), v_test_user_id);
    EXCEPTION
        WHEN check_violation THEN
            v_exception_caught := TRUE;
            PERFORM test_expect_exception('TC-LED-005', 'chk_ledger_type_entity');
    END;

    IF NOT v_exception_caught THEN
        RAISE EXCEPTION 'TEST_FAILED [TC-LED-005]: SUPPLIER ledger with NULL supplier_id should have been blocked';
    END IF;
END $$;

-- TC-LED-006: SUPPLIER 账本禁止关联 project_id
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_project_id BIGINT;
    v_test_supplier_id UUID := '00000000-0000-0000-0000-000000000010';
    v_exception_caught BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-LED-006: SUPPLIER 账本禁止关联 project_id';
    RAISE NOTICE '----------------------------------------';

    SELECT id INTO v_test_project_id FROM projects WHERE created_by = v_test_user_id LIMIT 1;

    BEGIN
        INSERT INTO ledger_entries (ledger_type, project_id, supplier_id, entry_type, amount, currency, occurred_at, created_by)
        VALUES ('SUPPLIER', v_test_project_id, v_test_supplier_id, 'COST', 100.00, 'CNY', NOW(), v_test_user_id);
    EXCEPTION
        WHEN check_violation THEN
            v_exception_caught := TRUE;
            PERFORM test_expect_exception('TC-LED-006', 'chk_ledger_type_entity');
    END;

    IF NOT v_exception_caught THEN
        RAISE EXCEPTION 'TEST_FAILED [TC-LED-006]: SUPPLIER ledger with project_id should have been blocked';
    END IF;
END $$;

-- TC-LED-007: PROJECT 账本只允许 REVENUE/TOPUP/REVERSAL
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_project_id BIGINT;
    v_exception_caught BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-LED-007: PROJECT 账本只允许 REVENUE/TOPUP/REVERSAL';
    RAISE NOTICE '----------------------------------------';

    SELECT id INTO v_test_project_id FROM projects WHERE created_by = v_test_user_id LIMIT 1;

    BEGIN
        INSERT INTO ledger_entries (ledger_type, project_id, entry_type, amount, currency, occurred_at, created_by)
        VALUES ('PROJECT', v_test_project_id, 'COST', 100.00, 'CNY', NOW(), v_test_user_id);
    EXCEPTION
        WHEN check_violation THEN
            v_exception_caught := TRUE;
            PERFORM test_expect_exception('TC-LED-007', 'chk_ledger_entry_type_by_ledger');
    END;

    IF NOT v_exception_caught THEN
        RAISE EXCEPTION 'TEST_FAILED [TC-LED-007]: PROJECT ledger with COST entry_type should have been blocked';
    END IF;
END $$;

-- TC-LED-008: SUPPLIER 账本只允许 COST/TOPUP/TRANSFER_*/REVERSAL
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_supplier_id UUID := '00000000-0000-0000-0000-000000000010';
    v_exception_caught BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-LED-008: SUPPLIER 账本只允许 COST/TOPUP/TRANSFER_*/REVERSAL';
    RAISE NOTICE '----------------------------------------';

    BEGIN
        INSERT INTO ledger_entries (ledger_type, supplier_id, entry_type, amount, currency, occurred_at, created_by)
        VALUES ('SUPPLIER', v_test_supplier_id, 'REVENUE', 100.00, 'CNY', NOW(), v_test_user_id);
    EXCEPTION
        WHEN check_violation THEN
            v_exception_caught := TRUE;
            PERFORM test_expect_exception('TC-LED-008', 'chk_ledger_entry_type_by_ledger');
    END;

    IF NOT v_exception_caught THEN
        RAISE EXCEPTION 'TEST_FAILED [TC-LED-008]: SUPPLIER ledger with REVENUE entry_type should have been blocked';
    END IF;
END $$;

-- =============================================================================
-- 4. P0 测试: 供应商余额只读 (Section 4)
-- =============================================================================

-- TC-SUP-001: 禁止直接修改 suppliers.balance
DO $$
DECLARE
    v_test_supplier_id UUID := '00000000-0000-0000-0000-000000000010';
    v_exception_caught BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-SUP-001: 禁止直接修改 suppliers.balance';
    RAISE NOTICE '----------------------------------------';

    BEGIN
        UPDATE suppliers SET balance = 9999.99 WHERE id = v_test_supplier_id;
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLERRM LIKE '%BALANCE_READONLY%' THEN
                v_exception_caught := TRUE;
                PERFORM test_expect_exception('TC-SUP-001', 'BALANCE_READONLY');
            ELSE
                RAISE;
            END IF;
    END;

    IF NOT v_exception_caught THEN
        RAISE EXCEPTION 'TEST_FAILED [TC-SUP-001]: Direct UPDATE of suppliers.balance should have been blocked';
    END IF;
END $$;

-- TC-SUP-002: 允许修改 suppliers 其他字段
DO $$
DECLARE
    v_test_supplier_id UUID := '00000000-0000-0000-0000-000000000010';
    v_old_balance DECIMAL(15,2);
    v_new_balance DECIMAL(15,2);
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-SUP-002: 允许修改 suppliers 其他字段';
    RAISE NOTICE '----------------------------------------';

    SELECT balance INTO v_old_balance FROM suppliers WHERE id = v_test_supplier_id;

    UPDATE suppliers SET name = '_test_supplier_updated', status = 'inactive' WHERE id = v_test_supplier_id;

    SELECT balance INTO v_new_balance FROM suppliers WHERE id = v_test_supplier_id;

    PERFORM test_assert(
        v_old_balance = v_new_balance,
        'TC-SUP-002',
        'Balance should remain unchanged after updating other fields'
    );

    -- 恢复原值
    UPDATE suppliers SET name = '_test_supplier_1', status = 'active' WHERE id = v_test_supplier_id;
END $$;

-- =============================================================================
-- 5. P0 测试: 日报唯一约束与状态机 (Section 5)
-- =============================================================================

-- TC-RPT-001: daily_reports 日期+账户唯一约束
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_ad_account_id BIGINT;
    v_exception_caught BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-RPT-001: daily_reports 日期+账户唯一约束';
    RAISE NOTICE '----------------------------------------';

    SELECT id INTO v_test_ad_account_id FROM ad_accounts WHERE created_by = v_test_user_id LIMIT 1;

    INSERT INTO daily_reports (report_date, ad_account_id, status, created_by)
    VALUES ('2025-01-01', v_test_ad_account_id, 'raw_submitted', v_test_user_id);

    BEGIN
        INSERT INTO daily_reports (report_date, ad_account_id, status, created_by)
        VALUES ('2025-01-01', v_test_ad_account_id, 'raw_submitted', v_test_user_id);
    EXCEPTION
        WHEN unique_violation THEN
            v_exception_caught := TRUE;
            PERFORM test_expect_exception('TC-RPT-001', 'uq_daily_reports_date_account');
    END;

    IF NOT v_exception_caught THEN
        RAISE EXCEPTION 'TEST_FAILED [TC-RPT-001]: Duplicate daily_report should have been blocked';
    END IF;
END $$;

-- TC-RPT-002: daily_reports 8 状态枚举约束
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_ad_account_id BIGINT;
    v_exception_caught BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-RPT-002: daily_reports 8 状态枚举约束';
    RAISE NOTICE '----------------------------------------';

    SELECT id INTO v_test_ad_account_id FROM ad_accounts WHERE created_by = v_test_user_id LIMIT 1;

    BEGIN
        INSERT INTO daily_reports (report_date, ad_account_id, status, created_by)
        VALUES ('2025-01-02', v_test_ad_account_id, 'invalid_status', v_test_user_id);
    EXCEPTION
        WHEN check_violation THEN
            v_exception_caught := TRUE;
            PERFORM test_expect_exception('TC-RPT-002', 'CHECK constraint on status');
    END;

    IF NOT v_exception_caught THEN
        RAISE EXCEPTION 'TEST_FAILED [TC-RPT-002]: Invalid status should have been blocked';
    END IF;
END $$;

-- TC-RPT-003: daily_reports 合法状态值验证
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_ad_account_id BIGINT;
    v_status TEXT;
    v_statuses TEXT[] := ARRAY['raw_submitted', 'trend_pending', 'trend_ok', 'trend_flagged',
                                'trend_resolved', 'final_pending', 'final_confirmed', 'final_locked'];
    v_report_date DATE := '2025-02-01';
    v_count INT := 0;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-RPT-003: daily_reports 合法状态值验证';
    RAISE NOTICE '----------------------------------------';

    SELECT id INTO v_test_ad_account_id FROM ad_accounts WHERE created_by = v_test_user_id LIMIT 1;

    FOREACH v_status IN ARRAY v_statuses LOOP
        INSERT INTO daily_reports (report_date, ad_account_id, status, created_by)
        VALUES (v_report_date, v_test_ad_account_id, v_status, v_test_user_id);

        v_report_date := v_report_date + 1;
        v_count := v_count + 1;
    END LOOP;

    PERFORM test_assert(
        v_count = 8,
        'TC-RPT-003',
        'All 8 valid statuses should be insertable'
    );
END $$;

-- =============================================================================
-- 6. P1 测试: 用户角色枚举 (Section 6)
-- =============================================================================

-- TC-USR-001: users.role 5 角色枚举约束
DO $$
DECLARE
    v_exception_caught BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-USR-001: users.role 5 角色枚举约束';
    RAISE NOTICE '----------------------------------------';

    BEGIN
        INSERT INTO users (id, username, full_name, role)
        VALUES (gen_random_uuid(), '_test_invalid_role', 'Invalid Role User', 'superadmin');
    EXCEPTION
        WHEN check_violation THEN
            v_exception_caught := TRUE;
            PERFORM test_expect_exception('TC-USR-001', 'CHECK constraint on role');
    END;

    IF NOT v_exception_caught THEN
        RAISE EXCEPTION 'TEST_FAILED [TC-USR-001]: Invalid role should have been blocked';
    END IF;
END $$;

-- TC-USR-002: users.role 合法值验证
DO $$
DECLARE
    v_role TEXT;
    v_roles TEXT[] := ARRAY['admin', 'finance', 'data_operator', 'account_manager', 'media_buyer'];
    v_count INT := 0;
    v_user_id UUID;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-USR-002: users.role 合法值验证';
    RAISE NOTICE '----------------------------------------';

    FOREACH v_role IN ARRAY v_roles LOOP
        v_user_id := gen_random_uuid();
        INSERT INTO users (id, username, full_name, role)
        VALUES (v_user_id, '_test_role_' || v_role, 'Test User ' || v_role, v_role);

        v_count := v_count + 1;

        DELETE FROM users WHERE id = v_user_id;
    END LOOP;

    PERFORM test_assert(
        v_count = 5,
        'TC-USR-002',
        'All 5 valid roles should be insertable'
    );
END $$;

-- =============================================================================
-- 7. P1 测试: 充值状态枚举 (Section 7)
-- =============================================================================

-- TC-TOP-001: topup_requests.status 7 状态枚举约束
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_project_id BIGINT;
    v_exception_caught BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-TOP-001: topup_requests.status 7 状态枚举约束';
    RAISE NOTICE '----------------------------------------';

    SELECT id INTO v_test_project_id FROM projects WHERE created_by = v_test_user_id LIMIT 1;

    BEGIN
        INSERT INTO topup_requests (request_no, project_id, applicant_id, amount, status)
        VALUES ('_TEST_REQ_INVALID', v_test_project_id, v_test_user_id, 1000.00, 'processing');
    EXCEPTION
        WHEN check_violation THEN
            v_exception_caught := TRUE;
            PERFORM test_expect_exception('TC-TOP-001', 'CHECK constraint on status');
    END;

    IF NOT v_exception_caught THEN
        RAISE EXCEPTION 'TEST_FAILED [TC-TOP-001]: Invalid topup status should have been blocked';
    END IF;
END $$;

-- TC-TOP-002: topup_requests.status 合法值验证
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_project_id BIGINT;
    v_status TEXT;
    v_statuses TEXT[] := ARRAY['draft', 'pending_review', 'finance_approve', 'paid', 'completed', 'rejected', 'cancelled'];
    v_count INT := 0;
    v_req_no TEXT;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-TOP-002: topup_requests.status 合法值验证';
    RAISE NOTICE '----------------------------------------';

    SELECT id INTO v_test_project_id FROM projects WHERE created_by = v_test_user_id LIMIT 1;

    FOREACH v_status IN ARRAY v_statuses LOOP
        v_req_no := '_TEST_REQ_' || upper(v_status);
        INSERT INTO topup_requests (request_no, project_id, applicant_id, amount, status)
        VALUES (v_req_no, v_test_project_id, v_test_user_id, 1000.00, v_status);

        v_count := v_count + 1;
    END LOOP;

    PERFORM test_assert(
        v_count = 7,
        'TC-TOP-002',
        'All 7 valid topup statuses should be insertable'
    );
END $$;

-- =============================================================================
-- 8. P1 测试: 广告账户状态枚举 (Section 8)
-- =============================================================================

-- TC-ACC-001: ad_accounts.status 6 状态枚举约束
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_project_id BIGINT;
    v_exception_caught BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-ACC-001: ad_accounts.status 6 状态枚举约束';
    RAISE NOTICE '----------------------------------------';

    SELECT id INTO v_test_project_id FROM projects WHERE created_by = v_test_user_id LIMIT 1;

    BEGIN
        INSERT INTO ad_accounts (project_id, name, account_code, status, created_by)
        VALUES (v_test_project_id, '_test_invalid_status', '_TEST_ACC_INVALID', 'deleted', v_test_user_id);
    EXCEPTION
        WHEN check_violation THEN
            v_exception_caught := TRUE;
            PERFORM test_expect_exception('TC-ACC-001', 'CHECK constraint on status');
    END;

    IF NOT v_exception_caught THEN
        RAISE EXCEPTION 'TEST_FAILED [TC-ACC-001]: Invalid ad_account status should have been blocked';
    END IF;
END $$;

-- TC-ACC-002: ad_accounts.status 合法值验证
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_project_id BIGINT;
    v_status TEXT;
    v_statuses TEXT[] := ARRAY['new', 'testing', 'active', 'suspended', 'dead', 'archived'];
    v_count INT := 0;
    v_acc_code TEXT;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-ACC-002: ad_accounts.status 合法值验证';
    RAISE NOTICE '----------------------------------------';

    SELECT id INTO v_test_project_id FROM projects WHERE created_by = v_test_user_id LIMIT 1;

    FOREACH v_status IN ARRAY v_statuses LOOP
        v_acc_code := '_TEST_ACC_' || upper(v_status);
        INSERT INTO ad_accounts (project_id, name, account_code, status, created_by)
        VALUES (v_test_project_id, '_test_' || v_status, v_acc_code, v_status, v_test_user_id);

        v_count := v_count + 1;
    END LOOP;

    PERFORM test_assert(
        v_count = 6,
        'TC-ACC-002',
        'All 6 valid ad_account statuses should be insertable'
    );
END $$;

-- =============================================================================
-- 9. P1 测试: 死号迁移状态 (Section 9)
-- =============================================================================

-- TC-TRF-001: transfer_requests.status 5 状态枚举约束
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_ad_account_id BIGINT;
    v_exception_caught BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-TRF-001: transfer_requests.status 5 状态枚举约束';
    RAISE NOTICE '----------------------------------------';

    SELECT id INTO v_test_ad_account_id FROM ad_accounts WHERE created_by = v_test_user_id LIMIT 1;

    BEGIN
        INSERT INTO transfer_requests (request_no, source_ad_account_id, target_ad_account_id, transfer_amount, status, created_by)
        VALUES ('_TEST_TRF_INVALID', v_test_ad_account_id, v_test_ad_account_id, 100.00, 'processing', v_test_user_id);
    EXCEPTION
        WHEN check_violation THEN
            v_exception_caught := TRUE;
            PERFORM test_expect_exception('TC-TRF-001', 'CHECK constraint on status');
    END;

    IF NOT v_exception_caught THEN
        RAISE EXCEPTION 'TEST_FAILED [TC-TRF-001]: Invalid transfer_request status should have been blocked';
    END IF;
END $$;

-- TC-TRF-002: transfer_requests.status 合法值验证
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_ad_account_id BIGINT;
    v_test_ad_account2_id BIGINT;
    v_status TEXT;
    v_statuses TEXT[] := ARRAY['draft', 'pending_approval', 'approved', 'rejected', 'completed'];
    v_count INT := 0;
    v_req_no TEXT;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-TRF-002: transfer_requests.status 合法值验证';
    RAISE NOTICE '----------------------------------------';

    SELECT id INTO v_test_ad_account_id FROM ad_accounts WHERE account_code = '_TEST_ACC_001';
    SELECT id INTO v_test_ad_account2_id FROM ad_accounts WHERE account_code = '_TEST_ACC_002';

    FOREACH v_status IN ARRAY v_statuses LOOP
        v_req_no := '_TEST_TRF_' || upper(v_status);
        INSERT INTO transfer_requests (request_no, source_ad_account_id, target_ad_account_id, transfer_amount, status, created_by)
        VALUES (v_req_no, v_test_ad_account2_id, v_test_ad_account_id, 100.00, v_status, v_test_user_id);

        v_count := v_count + 1;
    END LOOP;

    PERFORM test_assert(
        v_count = 5,
        'TC-TRF-002',
        'All 5 valid transfer_request statuses should be insertable'
    );
END $$;

-- =============================================================================
-- 10. P2 测试: 视图验证 (Section 10)
-- =============================================================================

-- TC-VW-001: v_project_balance 与 ledger_entries 聚合一致性
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_project_id BIGINT;
    v_view_balance DECIMAL(15,2);
    v_expected_balance DECIMAL(15,2);
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-VW-001: v_project_balance 与 ledger_entries 聚合一致性';
    RAISE NOTICE '----------------------------------------';

    SELECT id INTO v_test_project_id FROM projects WHERE created_by = v_test_user_id LIMIT 1;

    -- 计算预期余额 (之前插入的 100 + 500 + 本次 100 + 200 - 50)
    INSERT INTO ledger_entries (ledger_type, project_id, entry_type, amount, currency, occurred_at, created_by)
    VALUES
        ('PROJECT', v_test_project_id, 'TOPUP', 100.00, 'CNY', NOW(), v_test_user_id),
        ('PROJECT', v_test_project_id, 'REVENUE', 200.00, 'CNY', NOW(), v_test_user_id),
        ('PROJECT', v_test_project_id, 'REVERSAL', -50.00, 'CNY', NOW(), v_test_user_id);

    -- 查询视图
    SELECT balance INTO v_view_balance FROM v_project_balance WHERE project_id = v_test_project_id;

    -- 计算实际账本聚合
    SELECT COALESCE(SUM(amount), 0) INTO v_expected_balance
    FROM ledger_entries
    WHERE project_id = v_test_project_id AND ledger_type = 'PROJECT';

    PERFORM test_assert(
        v_view_balance = v_expected_balance,
        'TC-VW-001',
        format('View balance should be %s, got %s', v_expected_balance, v_view_balance)
    );
END $$;

-- TC-VW-002: v_project_balance 空项目返回 0
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_empty_project_id BIGINT;
    v_view_balance DECIMAL(15,2);
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-VW-002: v_project_balance 空项目返回 0';
    RAISE NOTICE '----------------------------------------';

    INSERT INTO projects (name, client_name, client_company, status, created_by)
    VALUES ('_test_empty_project', '_test_client', '_test_company', 'draft', v_test_user_id)
    RETURNING id INTO v_empty_project_id;

    SELECT balance INTO v_view_balance FROM v_project_balance WHERE project_id = v_empty_project_id;

    PERFORM test_assert(
        COALESCE(v_view_balance, 0.00) = 0.00,
        'TC-VW-002',
        'Empty project balance should be 0.00'
    );

    DELETE FROM projects WHERE id = v_empty_project_id;
END $$;

-- TC-VW-003: v_supplier_balance 计算值验证
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_supplier_id UUID := '00000000-0000-0000-0000-000000000010';
    v_calculated_balance DECIMAL(15,2);
    v_expected_balance DECIMAL(15,2);
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-VW-003: v_supplier_balance 计算值验证';
    RAISE NOTICE '----------------------------------------';

    -- 插入测试账本记录
    INSERT INTO ledger_entries (ledger_type, supplier_id, entry_type, amount, currency, occurred_at, created_by)
    VALUES
        ('SUPPLIER', v_test_supplier_id, 'TOPUP', 200.00, 'CNY', NOW(), v_test_user_id),
        ('SUPPLIER', v_test_supplier_id, 'COST', 300.00, 'CNY', NOW(), v_test_user_id),
        ('SUPPLIER', v_test_supplier_id, 'REVERSAL', -150.00, 'CNY', NOW(), v_test_user_id);

    -- 计算预期余额
    SELECT COALESCE(SUM(amount), 0) INTO v_expected_balance
    FROM ledger_entries
    WHERE supplier_id = v_test_supplier_id AND ledger_type = 'SUPPLIER';

    -- 查询视图
    SELECT calculated_balance INTO v_calculated_balance FROM v_supplier_balance WHERE supplier_id = v_test_supplier_id;

    PERFORM test_assert(
        v_calculated_balance = v_expected_balance,
        'TC-VW-003',
        format('Supplier calculated_balance should be %s, got %s', v_expected_balance, v_calculated_balance)
    );
END $$;

-- =============================================================================
-- 11. P2 测试: 对账模块 (Section 11)
-- =============================================================================

-- TC-REC-001: reconciliation_batches.status 5 状态枚举约束
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_project_id BIGINT;
    v_exception_caught BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-REC-001: reconciliation_batches.status 5 状态枚举约束';
    RAISE NOTICE '----------------------------------------';

    SELECT id INTO v_test_project_id FROM projects WHERE created_by = v_test_user_id LIMIT 1;

    BEGIN
        INSERT INTO reconciliation_batches (batch_no, project_id, status, created_by)
        VALUES ('_TEST_BATCH_INVALID', v_test_project_id, 'invalid', v_test_user_id);
    EXCEPTION
        WHEN check_violation THEN
            v_exception_caught := TRUE;
            PERFORM test_expect_exception('TC-REC-001', 'CHECK constraint on status');
    END;

    IF NOT v_exception_caught THEN
        RAISE EXCEPTION 'TEST_FAILED [TC-REC-001]: Invalid reconciliation_batches status should have been blocked';
    END IF;
END $$;

-- TC-REC-002: reconciliation_details.status 3 状态枚举约束
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_project_id BIGINT;
    v_batch_id BIGINT;
    v_exception_caught BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-REC-002: reconciliation_details.status 3 状态枚举约束';
    RAISE NOTICE '----------------------------------------';

    SELECT id INTO v_test_project_id FROM projects WHERE created_by = v_test_user_id LIMIT 1;

    -- 创建有效批次
    INSERT INTO reconciliation_batches (batch_no, project_id, status, created_by)
    VALUES ('_TEST_BATCH_001', v_test_project_id, 'draft', v_test_user_id)
    RETURNING id INTO v_batch_id;

    BEGIN
        INSERT INTO reconciliation_details (batch_id, status)
        VALUES (v_batch_id, 'invalid');
    EXCEPTION
        WHEN check_violation THEN
            v_exception_caught := TRUE;
            PERFORM test_expect_exception('TC-REC-002', 'CHECK constraint on status');
    END;

    IF NOT v_exception_caught THEN
        RAISE EXCEPTION 'TEST_FAILED [TC-REC-002]: Invalid reconciliation_details status should have been blocked';
    END IF;
END $$;

-- =============================================================================
-- 12. 集成测试: 充值流程 (Section 12)
-- =============================================================================

-- TC-FLOW-001: 完整充值流程
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_project_id BIGINT;
    v_topup_request_id BIGINT;
    v_balance_before DECIMAL(15,2);
    v_balance_after DECIMAL(15,2);
    v_topup_amount DECIMAL(15,2) := 5000.00;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-FLOW-001: 完整充值流程';
    RAISE NOTICE '----------------------------------------';

    SELECT id INTO v_test_project_id FROM projects WHERE created_by = v_test_user_id LIMIT 1;

    SELECT COALESCE(balance, 0) INTO v_balance_before FROM v_project_balance WHERE project_id = v_test_project_id;

    -- 1. 创建充值申请 (draft)
    INSERT INTO topup_requests (request_no, project_id, applicant_id, amount, status)
    VALUES ('_TEST_FLOW_001', v_test_project_id, v_test_user_id, v_topup_amount, 'draft')
    RETURNING id INTO v_topup_request_id;

    -- 2-5. 状态流转
    UPDATE topup_requests SET status = 'pending_review' WHERE id = v_topup_request_id;
    UPDATE topup_requests SET status = 'finance_approve' WHERE id = v_topup_request_id;
    UPDATE topup_requests SET status = 'paid' WHERE id = v_topup_request_id;

    -- 6. 插入账本记录
    INSERT INTO ledger_entries (ledger_type, project_id, entry_type, amount, currency, occurred_at, reference_id, created_by)
    VALUES ('PROJECT', v_test_project_id, 'TOPUP', v_topup_amount, 'CNY', NOW(), v_topup_request_id, v_test_user_id);

    -- 7. 完成充值
    UPDATE topup_requests SET status = 'completed' WHERE id = v_topup_request_id;

    -- 8. 验证余额
    SELECT balance INTO v_balance_after FROM v_project_balance WHERE project_id = v_test_project_id;

    PERFORM test_assert(
        v_balance_after = v_balance_before + v_topup_amount,
        'TC-FLOW-001',
        format('Project balance should increase by %s', v_topup_amount)
    );
END $$;

-- =============================================================================
-- 13. 集成测试: 日报流程 (Section 13)
-- =============================================================================

-- TC-FLOW-002: 日报 8 状态流转
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_ad_account_id BIGINT;
    v_daily_report_id BIGINT;
    v_final_status TEXT;
    v_locked_at TIMESTAMPTZ;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-FLOW-002: 日报 8 状态流转';
    RAISE NOTICE '----------------------------------------';

    SELECT id INTO v_test_ad_account_id FROM ad_accounts WHERE created_by = v_test_user_id LIMIT 1;

    -- 1. 创建日报
    INSERT INTO daily_reports (report_date, ad_account_id, status, created_by)
    VALUES ('2025-03-01', v_test_ad_account_id, 'raw_submitted', v_test_user_id)
    RETURNING id INTO v_daily_report_id;

    -- 2-6. 状态流转 (正常路径)
    UPDATE daily_reports SET status = 'trend_pending' WHERE id = v_daily_report_id;
    UPDATE daily_reports SET status = 'trend_ok' WHERE id = v_daily_report_id;
    UPDATE daily_reports SET status = 'final_pending' WHERE id = v_daily_report_id;
    UPDATE daily_reports SET status = 'final_confirmed' WHERE id = v_daily_report_id;
    UPDATE daily_reports SET status = 'final_locked', final_locked_at = NOW() WHERE id = v_daily_report_id;

    -- 7. 验证终态
    SELECT status, final_locked_at INTO v_final_status, v_locked_at
    FROM daily_reports WHERE id = v_daily_report_id;

    PERFORM test_assert(
        v_final_status = 'final_locked' AND v_locked_at IS NOT NULL,
        'TC-FLOW-002',
        'Daily report should reach final_locked with locked_at timestamp'
    );
END $$;

-- =============================================================================
-- 14. 集成测试: 死号余额迁移流程 (Section 14)
-- =============================================================================

-- TC-FLOW-003: 死号余额迁移流程
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_user2_id UUID := '00000000-0000-0000-0000-000000000002';
    v_test_supplier_id UUID := '00000000-0000-0000-0000-000000000010';
    v_test_supplier2_id UUID := '00000000-0000-0000-0000-000000000011';
    v_source_ad_account_id BIGINT;
    v_target_ad_account_id BIGINT;
    v_transfer_request_id BIGINT;
    v_source_balance_before DECIMAL(15,2);
    v_target_balance_before DECIMAL(15,2);
    v_source_balance_after DECIMAL(15,2);
    v_target_balance_after DECIMAL(15,2);
    v_transfer_amount DECIMAL(15,2) := 1000.00;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-FLOW-003: 死号余额迁移流程';
    RAISE NOTICE '----------------------------------------';

    -- 获取账户ID (supplier_id 分别为 supplier_1 和 supplier_2)
    SELECT id INTO v_source_ad_account_id FROM ad_accounts WHERE account_code = '_TEST_ACC_002'; -- dead账户
    SELECT id INTO v_target_ad_account_id FROM ad_accounts WHERE account_code = '_TEST_ACC_001'; -- active账户

    -- 记录迁移前余额
    SELECT COALESCE(calculated_balance, 0) INTO v_source_balance_before
    FROM v_supplier_balance WHERE supplier_id = v_test_supplier2_id;
    SELECT COALESCE(calculated_balance, 0) INTO v_target_balance_before
    FROM v_supplier_balance WHERE supplier_id = v_test_supplier_id;

    -- 1. 创建迁移申请 (draft)
    INSERT INTO transfer_requests (request_no, source_ad_account_id, target_ad_account_id, transfer_amount, status, created_by)
    VALUES ('_TEST_FLOW_003', v_source_ad_account_id, v_target_ad_account_id, v_transfer_amount, 'draft', v_test_user_id)
    RETURNING id INTO v_transfer_request_id;

    -- 2. 更新为 pending_approval
    UPDATE transfer_requests SET status = 'pending_approval' WHERE id = v_transfer_request_id;

    -- 3. 更新为 approved
    UPDATE transfer_requests SET status = 'approved', approved_by = v_test_user2_id, approved_at = NOW() WHERE id = v_transfer_request_id;

    -- 4. 插入 TRANSFER_OUT 账本记录 (源供应商)
    INSERT INTO ledger_entries (ledger_type, supplier_id, ad_account_id, entry_type, amount, currency, occurred_at, reference_id, created_by)
    VALUES ('SUPPLIER', v_test_supplier2_id, v_source_ad_account_id, 'TRANSFER_OUT', -v_transfer_amount, 'CNY', NOW(), v_transfer_request_id, v_test_user_id);

    -- 5. 插入 TRANSFER_IN 账本记录 (目标供应商)
    INSERT INTO ledger_entries (ledger_type, supplier_id, ad_account_id, entry_type, amount, currency, occurred_at, reference_id, created_by)
    VALUES ('SUPPLIER', v_test_supplier_id, v_target_ad_account_id, 'TRANSFER_IN', v_transfer_amount, 'CNY', NOW(), v_transfer_request_id, v_test_user_id);

    -- 6. 更新为 completed
    UPDATE transfer_requests SET status = 'completed' WHERE id = v_transfer_request_id;

    -- 7. 验证余额变化
    SELECT COALESCE(calculated_balance, 0) INTO v_source_balance_after
    FROM v_supplier_balance WHERE supplier_id = v_test_supplier2_id;
    SELECT COALESCE(calculated_balance, 0) INTO v_target_balance_after
    FROM v_supplier_balance WHERE supplier_id = v_test_supplier_id;

    PERFORM test_assert(
        v_source_balance_after = v_source_balance_before - v_transfer_amount,
        'TC-FLOW-003-SOURCE',
        format('Source supplier balance should decrease by %s', v_transfer_amount)
    );

    PERFORM test_assert(
        v_target_balance_after = v_target_balance_before + v_transfer_amount,
        'TC-FLOW-003-TARGET',
        format('Target supplier balance should increase by %s', v_transfer_amount)
    );
END $$;

-- =============================================================================
-- 15. 集成测试: 对账流程 (Section 15)
-- =============================================================================

-- TC-FLOW-004: 对账批次完整流程
DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_user2_id UUID := '00000000-0000-0000-0000-000000000002';
    v_test_project_id BIGINT;
    v_test_ad_account_id BIGINT;
    v_batch_id BIGINT;
    v_detail_id BIGINT;
    v_final_status TEXT;
BEGIN
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE 'TC-FLOW-004: 对账批次完整流程';
    RAISE NOTICE '----------------------------------------';

    SELECT id INTO v_test_project_id FROM projects WHERE created_by = v_test_user_id LIMIT 1;
    SELECT id INTO v_test_ad_account_id FROM ad_accounts WHERE created_by = v_test_user_id LIMIT 1;

    -- 1. 创建对账批次 (draft)
    INSERT INTO reconciliation_batches (batch_no, project_id, status, period_start, period_end, created_by)
    VALUES ('_TEST_FLOW_004', v_test_project_id, 'draft', '2025-01-01', '2025-01-31', v_test_user_id)
    RETURNING id INTO v_batch_id;

    -- 2. 创建对账明细
    INSERT INTO reconciliation_details (batch_id, ad_account_id, report_date, system_spend, external_spend, difference_amount, status)
    VALUES (v_batch_id, v_test_ad_account_id, '2025-01-15', 1000.00, 1050.00, 50.00, 'pending')
    RETURNING id INTO v_detail_id;

    -- 3. 更新批次状态为 pending_review
    UPDATE reconciliation_batches SET status = 'pending_review' WHERE id = v_batch_id;

    -- 4. 更新批次状态为 approved
    UPDATE reconciliation_batches SET status = 'approved', approved_by = v_test_user2_id WHERE id = v_batch_id;

    -- 5. 更新批次状态为 completed
    UPDATE reconciliation_batches SET status = 'completed' WHERE id = v_batch_id;

    -- 验证终态
    SELECT status INTO v_final_status FROM reconciliation_batches WHERE id = v_batch_id;

    PERFORM test_assert(
        v_final_status = 'completed',
        'TC-FLOW-004',
        'Reconciliation batch should reach completed status'
    );
END $$;

-- =============================================================================
-- 16. 测试清理 (安全机制)
-- =============================================================================

DO $$
DECLARE
    v_test_user_id UUID := '00000000-0000-0000-0000-000000000001';
    v_test_user2_id UUID := '00000000-0000-0000-0000-000000000002';
    v_test_supplier_id UUID := '00000000-0000-0000-0000-000000000010';
    v_test_supplier2_id UUID := '00000000-0000-0000-0000-000000000011';
    v_test_channel_id UUID := '00000000-0000-0000-0000-000000000020';
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '开始清理测试数据...';
    RAISE NOTICE '========================================';

    -- 使用 BEGIN...EXCEPTION...END 确保触发器恢复
    BEGIN
        -- 禁用触发器以便清理 ledger_entries
        ALTER TABLE ledger_entries DISABLE TRIGGER trg_ledger_immutable_update;
        ALTER TABLE ledger_entries DISABLE TRIGGER trg_ledger_immutable_delete;
        ALTER TABLE suppliers DISABLE TRIGGER trg_suppliers_balance_readonly;

        -- 清理测试数据 (按依赖顺序)
        DELETE FROM reconciliation_adjustments WHERE created_by = v_test_user_id;
        DELETE FROM reconciliation_details WHERE batch_id IN (SELECT id FROM reconciliation_batches WHERE created_by = v_test_user_id);
        DELETE FROM reconciliation_reports WHERE batch_id IN (SELECT id FROM reconciliation_batches WHERE created_by = v_test_user_id);
        DELETE FROM reconciliation_batches WHERE created_by = v_test_user_id;
        DELETE FROM ledger_entries WHERE created_by = v_test_user_id;
        DELETE FROM topup_transactions WHERE created_by = v_test_user_id;
        DELETE FROM topup_requests WHERE applicant_id = v_test_user_id;
        DELETE FROM transfer_requests WHERE created_by = v_test_user_id;
        DELETE FROM daily_reports WHERE created_by = v_test_user_id;
        DELETE FROM ad_accounts WHERE created_by = v_test_user_id;
        DELETE FROM projects WHERE created_by = v_test_user_id;
        DELETE FROM suppliers WHERE id IN (v_test_supplier_id, v_test_supplier2_id);
        DELETE FROM channels WHERE id = v_test_channel_id;
        DELETE FROM users WHERE id IN (v_test_user_id, v_test_user2_id);

        RAISE NOTICE '测试数据清理完成';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE '清理过程中出现异常: %', SQLERRM;
    END;

    -- 无论清理是否成功，都确保触发器被恢复
    BEGIN
        ALTER TABLE ledger_entries ENABLE TRIGGER trg_ledger_immutable_update;
        ALTER TABLE ledger_entries ENABLE TRIGGER trg_ledger_immutable_delete;
        ALTER TABLE suppliers ENABLE TRIGGER trg_suppliers_balance_readonly;
        RAISE NOTICE '触发器已恢复';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE '触发器恢复失败: %', SQLERRM;
    END;
END $$;

-- =============================================================================
-- 17. 清理测试辅助函数
-- =============================================================================

DROP FUNCTION IF EXISTS test_assert(BOOLEAN, TEXT, TEXT);
DROP FUNCTION IF EXISTS test_expect_exception(TEXT, TEXT);

-- =============================================================================
-- 测试结束
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '所有测试执行完成 (v2.0)';
    RAISE NOTICE '========================================';
    RAISE NOTICE '测试覆盖: P0 (13) + P1 (8) + P2 (5) + 集成 (4) = 30 用例';
END $$;
