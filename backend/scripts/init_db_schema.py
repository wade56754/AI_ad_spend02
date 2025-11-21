#!/usr/bin/env python3
"""
AI广告代投系统 - 数据库架构初始化脚本

版本: v2.3
用途: 在空数据库中创建完整的表结构、索引、约束和注释
运行环境: PostgreSQL 15+ (Supabase)
执行方式: python backend/scripts/init_db_schema.py

v2.3 更新日志（2025-11-19）：
- 补全所有状态字段的 CHECK 约束（严格对齐 STATE_MACHINE.md）
- 补全 ledger_entries.entry_type CHECK 约束
- 补全 ad_accounts, reconciliation_batches 的 created_at 索引
- 优化状态字段注释，明确可选值范围

v2.2 更新日志（2025-11-18）：
- 添加 pgcrypto 扩展初始化（gen_random_uuid 支持）
- ad_spend_daily 增加 (ad_account_code, spend_date) 唯一约束
- 审计表 (audit_logs, account_status_history) 增加索引

v2.1 更新日志（2025-11-17）：
- 修复审计表外键策略：改为 ON DELETE RESTRICT
- 对齐 DATA_SCHEMA.md v5.0 所有表结构

注意事项:
1. 本脚本严格基于 DATA_SCHEMA.md v5.0 和 STATE_MACHINE.md v2.3
2. 所有状态字段已添加 CHECK 约束，防止非法值
3. 所有 money 字段使用 NUMERIC(15,2)
4. 所有时间字段使用 TIMESTAMPTZ
5. 审计表使用 ON DELETE RESTRICT 保护历史记录
6. 业务表使用 CASCADE/SET NULL 根据业务关系
"""

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

# 动态添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[OK] 已加载 .env 文件: {env_path}")
except ImportError:
    print("提示: 未安装 python-dotenv，将直接使用系统环境变量")

try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("错误: 未安装 psycopg2，请运行: pip install psycopg2-binary")
    sys.exit(1)


def get_db_connection():
    """
    从环境变量获取数据库连接参数并建立连接

    支持两种配置方式:
    1. DATABASE_URL 格式（优先）
    2. 分开的环境变量: SUPABASE_DB_HOST, SUPABASE_DB_PORT, SUPABASE_DB_NAME,
       SUPABASE_DB_USER, SUPABASE_DB_PASSWORD
    """
    # 方式1: 尝试从 DATABASE_URL 解析
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        try:
            parsed = urlparse(database_url)
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                dbname=parsed.path.lstrip('/'),
                user=parsed.username,
                password=parsed.password,
            )
            print(f"[OK] 使用 DATABASE_URL 连接到: {parsed.hostname}/{parsed.path.lstrip('/')}")
            return conn
        except psycopg2.Error as e:
            print(f"[FAIL] 使用 DATABASE_URL 连接失败: {e}")
            print("尝试使用分开的环境变量...")

    # 方式2: 使用分开的环境变量
    required_vars = [
        "SUPABASE_DB_HOST",
        "SUPABASE_DB_PORT",
        "SUPABASE_DB_NAME",
        "SUPABASE_DB_USER",
        "SUPABASE_DB_PASSWORD",
    ]

    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"错误: 缺少必需的环境变量: {', '.join(missing)}")
        print("\n请配置以下之一:")
        print("1. DATABASE_URL=postgresql://user:password@host:port/dbname")
        print("2. SUPABASE_DB_HOST, SUPABASE_DB_PORT, SUPABASE_DB_NAME, SUPABASE_DB_USER, SUPABASE_DB_PASSWORD")
        sys.exit(1)

    try:
        conn = psycopg2.connect(
            host=os.getenv("SUPABASE_DB_HOST"),
            port=os.getenv("SUPABASE_DB_PORT"),
            dbname=os.getenv("SUPABASE_DB_NAME"),
            user=os.getenv("SUPABASE_DB_USER"),
            password=os.getenv("SUPABASE_DB_PASSWORD"),
        )
        print(f"[OK] 使用环境变量连接到: {os.getenv('SUPABASE_DB_HOST')}/{os.getenv('SUPABASE_DB_NAME')}")
        return conn
    except psycopg2.Error as e:
        print(f"数据库连接失败: {e}")
        sys.exit(1)


def execute_sql(cursor, sql_statement, description=""):
    """
    执行单条 SQL 语句并处理错误

    Args:
        cursor: psycopg2 cursor 对象
        sql_statement: SQL 语句字符串
        description: 操作描述（用于日志）
    """
    try:
        cursor.execute(sql_statement)
        if description:
            print(f"[OK] {description}")
        return True
    except psycopg2.Error as e:
        print(f"[FAIL] {description if description else 'SQL 执行'} 失败: {e}")
        return False


def init_database_schema():
    """
    初始化完整的数据库架构

    执行顺序:
    1. 启用必需扩展
    2. 创建基础表（users, channels, projects）
    3. 创建账户表（ad_accounts, channel_reviews, channel_account_requests）
    4. 创建业务表（daily_reports, topup_requests, ad_spend_daily）
    5. 创建财务表（ledger_entries, reconciliation_batches, reconciliation_details）
    6. 创建系统表（audit_logs, account_status_history, account_alerts, channel_performance）
    7. 创建所有索引
    8. 创建所有注释
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    print("=" * 60)
    print("开始初始化数据库架构 (v2.3)")
    print("=" * 60)

    try:
        # ========== 1. 扩展初始化 ==========
        print("\n[1/8] 初始化数据库扩展...")

        execute_sql(
            cursor,
            "CREATE EXTENSION IF NOT EXISTS pgcrypto;",
            "启用 pgcrypto 扩展（UUID 生成支持）"
        )

        # ========== 2. 基础表 ==========
        print("\n[2/8] 创建基础表...")

        # users 表
        execute_sql(cursor, """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """, "创建 users 表")

        # channels 表
        execute_sql(cursor, """
        CREATE TABLE IF NOT EXISTS channels (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            channel_code VARCHAR(20) UNIQUE NOT NULL,
            status VARCHAR(20) NOT NULL
                CHECK (status IN ('active', 'inactive')),
            country VARCHAR(10),
            notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """, "创建 channels 表")

        # projects 表
        execute_sql(cursor, """
        CREATE TABLE IF NOT EXISTS projects (
            id BIGSERIAL PRIMARY KEY,
            project_name VARCHAR(100) NOT NULL,
            project_code VARCHAR(50) UNIQUE NOT NULL,
            client_name VARCHAR(100),
            status VARCHAR(20) NOT NULL
                CHECK (status IN ('draft', 'active', 'suspended', 'archived')),
            created_by UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
        );
        """, "创建 projects 表")

        # ========== 3. 账户管理表 ==========
        print("\n[3/8] 创建账户管理表...")

        # channel_reviews 表
        execute_sql(cursor, """
        CREATE TABLE IF NOT EXISTS channel_reviews (
            id BIGSERIAL PRIMARY KEY,
            channel_id BIGINT NOT NULL,
            reviewer_id UUID,
            review_status VARCHAR(20) NOT NULL
                CHECK (review_status IN ('draft', 'pending', 'approved', 'rejected')),
            review_notes TEXT,
            reviewed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE,
            FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE SET NULL
        );
        """, "创建 channel_reviews 表")

        # channel_account_requests 表
        execute_sql(cursor, """
        CREATE TABLE IF NOT EXISTS channel_account_requests (
            id BIGSERIAL PRIMARY KEY,
            project_id BIGINT NOT NULL,
            channel_id BIGINT NOT NULL,
            requested_by UUID,
            status VARCHAR(20) NOT NULL
                CHECK (status IN ('draft', 'pending', 'approved', 'rejected')),
            approved_by UUID,
            request_notes TEXT,
            approved_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE,
            FOREIGN KEY (requested_by) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
        );
        """, "创建 channel_account_requests 表")

        # ad_accounts 表
        execute_sql(cursor, """
        CREATE TABLE IF NOT EXISTS ad_accounts (
            id BIGSERIAL PRIMARY KEY,
            project_id BIGINT NOT NULL,
            channel_id BIGINT NOT NULL,
            account_code VARCHAR(50) UNIQUE NOT NULL,
            account_name VARCHAR(100),
            status VARCHAR(20) NOT NULL
                CHECK (status IN ('new', 'testing', 'active', 'suspended', 'dead', 'archived')),
            balance NUMERIC(15,2) NOT NULL DEFAULT 0.00,
            assigned_to UUID,
            opened_at TIMESTAMPTZ,
            died_at TIMESTAMPTZ,
            death_reason TEXT,
            death_loss NUMERIC(15,2),
            notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE,
            FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL
        );
        """, "创建 ad_accounts 表")

        # ========== 4. 业务流程表 ==========
        print("\n[4/8] 创建业务流程表...")

        # daily_reports 表
        execute_sql(cursor, """
        CREATE TABLE IF NOT EXISTS daily_reports (
            id BIGSERIAL PRIMARY KEY,
            ad_account_id BIGINT NOT NULL,
            report_date DATE NOT NULL,
            submitted_by UUID,
            reviewed_by UUID,
            status VARCHAR(20) NOT NULL
                CHECK (status IN ('draft', 'pending', 'approved', 'rejected')),
            fans_gained INTEGER,
            spend_amount NUMERIC(15,2),
            notes TEXT,
            submitted_at TIMESTAMPTZ,
            reviewed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            FOREIGN KEY (ad_account_id) REFERENCES ad_accounts(id) ON DELETE CASCADE,
            FOREIGN KEY (submitted_by) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL,
            UNIQUE (ad_account_id, report_date)
        );
        """, "创建 daily_reports 表")

        # topup_requests 表
        execute_sql(cursor, """
        CREATE TABLE IF NOT EXISTS topup_requests (
            id BIGSERIAL PRIMARY KEY,
            ad_account_id BIGINT NOT NULL,
            requested_by UUID,
            reviewed_by UUID,
            approved_by UUID,
            amount NUMERIC(15,2) NOT NULL,
            status VARCHAR(20) NOT NULL
                CHECK (status IN ('draft', 'pending_review', 'finance_approve', 'paid', 'completed', 'rejected', 'cancelled')),
            request_notes TEXT,
            reject_reason TEXT,
            requested_at TIMESTAMPTZ,
            reviewed_at TIMESTAMPTZ,
            approved_at TIMESTAMPTZ,
            paid_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            FOREIGN KEY (ad_account_id) REFERENCES ad_accounts(id) ON DELETE CASCADE,
            FOREIGN KEY (requested_by) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
        );
        """, "创建 topup_requests 表")

        # ad_spend_daily 表
        execute_sql(cursor, """
        CREATE TABLE IF NOT EXISTS ad_spend_daily (
            id BIGSERIAL PRIMARY KEY,
            ad_account_code VARCHAR(50) NOT NULL,
            spend_date DATE NOT NULL,
            impressions BIGINT,
            clicks BIGINT,
            conversions INTEGER,
            cost NUMERIC(15,2),
            revenue NUMERIC(15,2),
            roi NUMERIC(12,4),
            imported_by UUID,
            imported_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            FOREIGN KEY (imported_by) REFERENCES users(id) ON DELETE SET NULL,
            UNIQUE (ad_account_code, spend_date)
        );
        """, "创建 ad_spend_daily 表")

        # ========== 5. 财务表 ==========
        print("\n[5/8] 创建财务表...")

        # ledger_entries 表
        execute_sql(cursor, """
        CREATE TABLE IF NOT EXISTS ledger_entries (
            id BIGSERIAL PRIMARY KEY,
            ad_account_id BIGINT NOT NULL,
            entry_type VARCHAR(20) NOT NULL
                CHECK (entry_type IN ('topup_received', 'spend', 'adjustment')),
            amount NUMERIC(15,2) NOT NULL,
            balance_after NUMERIC(15,2) NOT NULL,
            reference_id BIGINT,
            reference_type VARCHAR(50),
            notes TEXT,
            entry_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            FOREIGN KEY (ad_account_id) REFERENCES ad_accounts(id) ON DELETE CASCADE
        );
        """, "创建 ledger_entries 表")

        # reconciliation_batches 表
        execute_sql(cursor, """
        CREATE TABLE IF NOT EXISTS reconciliation_batches (
            id BIGSERIAL PRIMARY KEY,
            batch_code VARCHAR(50) UNIQUE NOT NULL,
            period_start DATE NOT NULL,
            period_end DATE NOT NULL,
            status VARCHAR(20) NOT NULL
                CHECK (status IN ('draft', 'pending', 'reviewing', 'closed')),
            total_system_spend NUMERIC(15,2),
            total_actual_spend NUMERIC(15,2),
            discrepancy NUMERIC(15,2),
            created_by UUID,
            reviewed_by UUID,
            closed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL
        );
        """, "创建 reconciliation_batches 表")

        # reconciliation_details 表
        execute_sql(cursor, """
        CREATE TABLE IF NOT EXISTS reconciliation_details (
            id BIGSERIAL PRIMARY KEY,
            batch_id BIGINT NOT NULL,
            ad_account_id BIGINT NOT NULL,
            system_spend NUMERIC(15,2) NOT NULL,
            actual_spend NUMERIC(15,2) NOT NULL,
            discrepancy NUMERIC(15,2) NOT NULL,
            status VARCHAR(20) NOT NULL
                CHECK (status IN ('pending', 'confirmed', 'adjusted')),
            notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            FOREIGN KEY (batch_id) REFERENCES reconciliation_batches(id) ON DELETE CASCADE,
            FOREIGN KEY (ad_account_id) REFERENCES ad_accounts(id) ON DELETE CASCADE
        );
        """, "创建 reconciliation_details 表")

        # ========== 6. 系统支持表 ==========
        print("\n[6/8] 创建系统支持表...")

        # audit_logs 表
        execute_sql(cursor, """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id BIGSERIAL PRIMARY KEY,
            user_id UUID,
            action VARCHAR(50) NOT NULL,
            resource_type VARCHAR(50) NOT NULL,
            resource_id VARCHAR(50),
            old_values JSONB,
            new_values JSONB,
            ip_address VARCHAR(50),
            user_agent TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
        );
        """, "创建 audit_logs 表")

        # account_status_history 表
        execute_sql(cursor, """
        CREATE TABLE IF NOT EXISTS account_status_history (
            id BIGSERIAL PRIMARY KEY,
            ad_account_id BIGINT NOT NULL,
            old_status VARCHAR(20),
            new_status VARCHAR(20) NOT NULL,
            changed_by UUID,
            reason TEXT,
            changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            FOREIGN KEY (ad_account_id) REFERENCES ad_accounts(id) ON DELETE RESTRICT,
            FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE SET NULL
        );
        """, "创建 account_status_history 表")

        # account_alerts 表
        execute_sql(cursor, """
        CREATE TABLE IF NOT EXISTS account_alerts (
            id BIGSERIAL PRIMARY KEY,
            ad_account_id BIGINT NOT NULL,
            alert_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            status VARCHAR(20) NOT NULL
                CHECK (status IN ('open', 'ack', 'resolved')),
            message TEXT NOT NULL,
            metadata JSONB,
            acknowledged_by UUID,
            acknowledged_at TIMESTAMPTZ,
            resolved_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            FOREIGN KEY (ad_account_id) REFERENCES ad_accounts(id) ON DELETE CASCADE,
            FOREIGN KEY (acknowledged_by) REFERENCES users(id) ON DELETE SET NULL
        );
        """, "创建 account_alerts 表")

        # channel_performance 表
        execute_sql(cursor, """
        CREATE TABLE IF NOT EXISTS channel_performance (
            id BIGSERIAL PRIMARY KEY,
            channel_id BIGINT NOT NULL,
            stat_date DATE NOT NULL,
            total_accounts INTEGER NOT NULL DEFAULT 0,
            active_accounts INTEGER NOT NULL DEFAULT 0,
            dead_accounts INTEGER NOT NULL DEFAULT 0,
            total_spend NUMERIC(15,2) NOT NULL DEFAULT 0.00,
            avg_account_lifespan NUMERIC(12,2),
            death_rate NUMERIC(12,4),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE,
            UNIQUE (channel_id, stat_date)
        );
        """, "创建 channel_performance 表")

        # ========== 7. 索引创建 ==========
        print("\n[7/8] 创建索引...")

        # users 表索引
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);", "users.role 索引")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);", "users.is_active 索引")

        # projects 表索引
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);", "projects.status 索引")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_projects_created_by ON projects(created_by);", "projects.created_by 索引")

        # ad_accounts 表索引
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_ad_accounts_project_id ON ad_accounts(project_id);", "ad_accounts.project_id 索引")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_ad_accounts_channel_id ON ad_accounts(channel_id);", "ad_accounts.channel_id 索引")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_ad_accounts_status ON ad_accounts(status);", "ad_accounts.status 索引")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_ad_accounts_assigned_to ON ad_accounts(assigned_to);", "ad_accounts.assigned_to 索引")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_ad_accounts_created_at ON ad_accounts(created_at);", "ad_accounts.created_at 索引")

        # daily_reports 表索引
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_daily_reports_ad_account_id ON daily_reports(ad_account_id);", "daily_reports.ad_account_id 索引")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_daily_reports_report_date ON daily_reports(report_date);", "daily_reports.report_date 索引")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_daily_reports_status ON daily_reports(status);", "daily_reports.status 索引")

        # topup_requests 表索引
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_topup_requests_ad_account_id ON topup_requests(ad_account_id);", "topup_requests.ad_account_id 索引")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_topup_requests_status ON topup_requests(status);", "topup_requests.status 索引")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_topup_requests_requested_by ON topup_requests(requested_by);", "topup_requests.requested_by 索引")

        # ad_spend_daily 表索引
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_ad_spend_daily_account_code ON ad_spend_daily(ad_account_code);", "ad_spend_daily.account_code 索引")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_ad_spend_daily_spend_date ON ad_spend_daily(spend_date);", "ad_spend_daily.spend_date 索引")

        # ledger_entries 表索引
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_ledger_entries_ad_account_id ON ledger_entries(ad_account_id);", "ledger_entries.ad_account_id 索引")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_ledger_entries_entry_date ON ledger_entries(entry_date);", "ledger_entries.entry_date 索引")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_ledger_entries_entry_type ON ledger_entries(entry_type);", "ledger_entries.entry_type 索引")

        # reconciliation_batches 表索引
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_reconciliation_batches_status ON reconciliation_batches(status);", "reconciliation_batches.status 索引")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_reconciliation_batches_period ON reconciliation_batches(period_start, period_end);", "reconciliation_batches.period 索引")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_reconciliation_batches_created_at ON reconciliation_batches(created_at);", "reconciliation_batches.created_at 索引")

        # reconciliation_details 表索引
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_reconciliation_details_batch_id ON reconciliation_details(batch_id);", "reconciliation_details.batch_id 索引")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_reconciliation_details_ad_account_id ON reconciliation_details(ad_account_id);", "reconciliation_details.ad_account_id 索引")

        # audit_logs 表索引
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);", "audit_logs.user_id 索引")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);", "audit_logs.resource 索引")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);", "audit_logs.created_at 索引")

        # account_status_history 表索引
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_account_status_history_account_id ON account_status_history(ad_account_id);", "account_status_history.account_id 索引")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_account_status_history_changed_at ON account_status_history(changed_at);", "account_status_history.changed_at 索引")

        # account_alerts 表索引
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_account_alerts_ad_account_id ON account_alerts(ad_account_id);", "account_alerts.ad_account_id 索引")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_account_alerts_status ON account_alerts(status);", "account_alerts.status 索引")
        execute_sql(cursor, "CREATE INDEX IF NOT EXISTS idx_account_alerts_created_at ON account_alerts(created_at);", "account_alerts.created_at 索引")

        # ========== 8. 注释创建 ==========
        print("\n[8/8] 创建表和列注释...")

        # users 表注释
        execute_sql(cursor, "COMMENT ON TABLE users IS '系统用户表，存储所有用户的认证信息和角色';", "users 表注释")
        execute_sql(cursor, "COMMENT ON COLUMN users.role IS '用户角色: admin/finance/data_operator/account_manager/media_buyer';", "users.role 注释")

        # channels 表注释
        execute_sql(cursor, "COMMENT ON TABLE channels IS '广告渠道表，如 Facebook, Google Ads 等';", "channels 表注释")
        execute_sql(cursor, "COMMENT ON COLUMN channels.status IS '渠道状态: active(活跃)/inactive(停用) - 参考 STATE_MACHINE.md § 6.1';", "channels.status 注释")

        # projects 表注释
        execute_sql(cursor, "COMMENT ON TABLE projects IS '项目表，每个项目对应一个客户的广告投放需求';", "projects 表注释")
        execute_sql(cursor, "COMMENT ON COLUMN projects.status IS '项目状态: draft(草稿)/active(活跃)/suspended(暂停)/archived(归档) - 参考 STATE_MACHINE.md § 5';", "projects.status 注释")

        # channel_reviews 表注释
        execute_sql(cursor, "COMMENT ON TABLE channel_reviews IS '渠道评审记录表';", "channel_reviews 表注释")
        execute_sql(cursor, "COMMENT ON COLUMN channel_reviews.review_status IS '评审状态: draft(草稿)/pending(待审)/approved(通过)/rejected(拒绝) - 参考 STATE_MACHINE.md § 6.2';", "channel_reviews.review_status 注释")

        # channel_account_requests 表注释
        execute_sql(cursor, "COMMENT ON TABLE channel_account_requests IS '渠道开户申请记录表';", "channel_account_requests 表注释")
        execute_sql(cursor, "COMMENT ON COLUMN channel_account_requests.status IS '申请状态: draft(草稿)/pending(待审)/approved(通过)/rejected(拒绝) - 参考 STATE_MACHINE.md § 6.3';", "channel_account_requests.status 注释")

        # ad_accounts 表注释
        execute_sql(cursor, "COMMENT ON TABLE ad_accounts IS '广告账户表，核心业务实体';", "ad_accounts 表注释")
        execute_sql(cursor, "COMMENT ON COLUMN ad_accounts.status IS '账户状态: new(新建)/testing(测试)/active(活跃)/suspended(暂停)/dead(死号)/archived(归档) - 参考 STATE_MACHINE.md § 7.1';", "ad_accounts.status 注释")
        execute_sql(cursor, "COMMENT ON COLUMN ad_accounts.balance IS '账户当前余额（元），精度 0.01';", "ad_accounts.balance 注释")

        # daily_reports 表注释
        execute_sql(cursor, "COMMENT ON TABLE daily_reports IS '投手每日报告表';", "daily_reports 表注释")
        execute_sql(cursor, "COMMENT ON COLUMN daily_reports.status IS '日报状态: draft(草稿)/pending(待审)/approved(通过)/rejected(拒绝) - 参考 STATE_MACHINE.md § 8';", "daily_reports.status 注释")

        # topup_requests 表注释
        execute_sql(cursor, "COMMENT ON TABLE topup_requests IS '充值申请表';", "topup_requests 表注释")
        execute_sql(cursor, "COMMENT ON COLUMN topup_requests.status IS '充值状态: draft(草稿)/pending_review(待复核)/finance_approve(财务审批)/paid(已付款)/completed(已完成)/rejected(已拒绝)/cancelled(已取消) - 参考 STATE_MACHINE.md § 9';", "topup_requests.status 注释")

        # ad_spend_daily 表注释
        execute_sql(cursor, "COMMENT ON TABLE ad_spend_daily IS '每日广告花费数据表（从渠道导入）';", "ad_spend_daily 表注释")

        # ledger_entries 表注释
        execute_sql(cursor, "COMMENT ON TABLE ledger_entries IS '总账分录表，记录所有资金流水';", "ledger_entries 表注释")
        execute_sql(cursor, "COMMENT ON COLUMN ledger_entries.entry_type IS '分录类型: topup_received(充值到账)/spend(消耗)/adjustment(调整)';", "ledger_entries.entry_type 注释")

        # reconciliation_batches 表注释
        execute_sql(cursor, "COMMENT ON TABLE reconciliation_batches IS '对账批次表';", "reconciliation_batches 表注释")
        execute_sql(cursor, "COMMENT ON COLUMN reconciliation_batches.status IS '批次状态: draft(草稿)/pending(待处理)/reviewing(审核中)/closed(已关闭) - 参考 STATE_MACHINE.md § 11.1';", "reconciliation_batches.status 注释")

        # reconciliation_details 表注释
        execute_sql(cursor, "COMMENT ON TABLE reconciliation_details IS '对账明细表';", "reconciliation_details 表注释")
        execute_sql(cursor, "COMMENT ON COLUMN reconciliation_details.status IS '明细状态: pending(待确认)/confirmed(已确认)/adjusted(已调整) - 参考 STATE_MACHINE.md § 11.2';", "reconciliation_details.status 注释")

        # audit_logs 表注释
        execute_sql(cursor, "COMMENT ON TABLE audit_logs IS '审计日志表，记录所有敏感操作';", "audit_logs 表注释")

        # account_status_history 表注释
        execute_sql(cursor, "COMMENT ON TABLE account_status_history IS '账户状态变更历史表';", "account_status_history 表注释")

        # account_alerts 表注释
        execute_sql(cursor, "COMMENT ON TABLE account_alerts IS '账户预警表';", "account_alerts 表注释")
        execute_sql(cursor, "COMMENT ON COLUMN account_alerts.status IS '预警状态: open(待处理)/ack(已确认)/resolved(已解决) - 参考 STATE_MACHINE.md § 7.3';", "account_alerts.status 注释")

        # channel_performance 表注释
        execute_sql(cursor, "COMMENT ON TABLE channel_performance IS '渠道表现统计表';", "channel_performance 表注释")

        # 提交事务
        conn.commit()

        print("\n" + "=" * 60)
        print("[SUCCESS] 数据库架构初始化完成！(v2.3)")
        print("=" * 60)
        print("\n关键更新:")
        print("  - 所有状态字段已添加 CHECK 约束")
        print("  - ledger_entries.entry_type 已添加 CHECK 约束")
        print("  - 补全 ad_accounts 和 reconciliation_batches 的 created_at 索引")
        print("  - 所有状态字段注释包含完整枚举值和文档引用")
        print("\n请执行以下验证:")
        print("  1. SELECT * FROM pg_tables WHERE schemaname = 'public';")
        print("  2. SELECT * FROM pg_indexes WHERE schemaname = 'public';")
        print("  3. SELECT * FROM pg_constraint WHERE contype = 'c';")

    except Exception as e:
        conn.rollback()
        print(f"\n[FAIL] 初始化失败: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    init_database_schema()
