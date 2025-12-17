/**
 * 测试数据工厂
 * 用于生成测试数据
 */

/**
 * 生成随机字符串
 */
export function randomString(length = 10): string {
  const chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
  let result = ''
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

/**
 * 生成随机邮箱
 */
export function randomEmail(): string {
  return `test_${randomString(8)}@example.com`
}

/**
 * 生成随机数字
 */
export function randomNumber(min = 0, max = 100): number {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

/**
 * 生成随机日期
 */
export function randomDate(start?: Date, end?: Date): string {
  const startDate = start || new Date(2024, 0, 1)
  const endDate = end || new Date()

  const randomTime =
    startDate.getTime() +
    Math.random() * (endDate.getTime() - startDate.getTime())

  return new Date(randomTime).toISOString().split('T')[0]
}

/**
 * 用户工厂
 */
export const userFactory = {
  build: (overrides?: Partial<UserData>) => ({
    id: randomString(16),
    username: `user_${randomString(6)}`,
    email: randomEmail(),
    role: 'media_buyer',
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  }),

  buildMany: (count: number, overrides?: Partial<UserData>) => {
    return Array.from({ length: count }, () => userFactory.build(overrides))
  },
}

/**
 * 日报工厂
 */
export const dailyReportFactory = {
  build: (overrides?: Partial<DailyReportData>) => ({
    id: randomNumber(1, 10000),
    ad_account_id: randomNumber(1, 100),
    report_date: randomDate(),
    status: 'raw_submitted',
    conversions_raw: randomNumber(10, 500),
    raw_spend: randomNumber(100, 10000).toFixed(2),
    impressions: randomNumber(1000, 100000),
    clicks: randomNumber(50, 5000),
    notes: `测试日报 ${randomString(8)}`,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  }),

  buildMany: (count: number, overrides?: Partial<DailyReportData>) => {
    return Array.from({ length: count }, () => dailyReportFactory.build(overrides))
  },
}

/**
 * 充值申请工厂 (7-state workflow per STATE_MACHINE.md v2.6 § 9)
 */
export const topupRequestFactory = {
  build: (overrides?: Partial<TopupRequestData>) => {
    const id = `topup-${randomString(16)}`;
    const tenantId = `tenant-${randomString(8)}`;
    const projectId = `proj-${randomString(8)}`;
    const now = new Date().toISOString();
    const requestedAt = new Date(Date.now() - randomNumber(1, 72) * 3600 * 1000).toISOString();

    return {
      id,
      tenant_id: tenantId,
      project_id: projectId,
      project_name: `测试项目_${randomString(4)}`,
      ad_account_id: `acc-${randomString(8)}`,
      ad_account_name: `测试账户_${randomString(4)}`,
      amount: randomNumber(100000, 10000000), // cents
      currency: 'CNY',
      status: 'draft' as TopupStatus,
      version: 1,
      requested_by: `user-${randomString(8)}`,
      requested_by_name: `测试用户_${randomString(4)}`,
      requested_at: requestedAt,
      notes: `充值申请 ${randomString(8)}`,
      created_at: requestedAt,
      updated_at: now,
      ...overrides,
    };
  },

  buildMany: (count: number, overrides?: Partial<TopupRequestData>) => {
    return Array.from({ length: count }, () => topupRequestFactory.build(overrides));
  },

  // Build with specific status
  buildWithStatus: (status: TopupStatus, overrides?: Partial<TopupRequestData>) => {
    const base = topupRequestFactory.build({ status, ...overrides });
    const now = new Date().toISOString();

    // Add timestamps based on status progression
    if (['pending_review', 'finance_approve', 'paid', 'completed', 'rejected'].includes(status)) {
      base.requested_at = new Date(Date.now() - 24 * 3600 * 1000).toISOString();
    }

    if (['finance_approve', 'paid', 'completed'].includes(status)) {
      base.data_reviewed_at = new Date(Date.now() - 12 * 3600 * 1000).toISOString();
      base.data_reviewed_by = `reviewer-${randomString(8)}`;
      base.data_reviewed_by_name = `数据运营_${randomString(4)}`;
      base.data_review_notes = '数据核实无误';
    }

    if (['paid', 'completed'].includes(status)) {
      base.finance_approved_at = new Date(Date.now() - 6 * 3600 * 1000).toISOString();
      base.finance_approved_by = `finance-${randomString(8)}`;
      base.finance_approved_by_name = `财务_${randomString(4)}`;
      base.finance_approval_notes = '审批通过';
    }

    if (status === 'paid') {
      base.paid_at = new Date(Date.now() - 2 * 3600 * 1000).toISOString();
      base.payment_reference = `PAY-${randomString(12).toUpperCase()}`;
    }

    if (status === 'completed') {
      base.paid_at = new Date(Date.now() - 4 * 3600 * 1000).toISOString();
      base.payment_reference = `PAY-${randomString(12).toUpperCase()}`;
      base.completed_at = now;
      base.ledger_entry_id = `ledger-${randomString(8)}`;
    }

    if (status === 'rejected') {
      base.rejected_at = now;
      base.rejected_by = `rejector-${randomString(8)}`;
      base.rejected_by_name = `审批人_${randomString(4)}`;
      base.rejection_reason = '资料不完整';
    }

    if (status === 'cancelled') {
      base.cancelled_at = now;
      base.cancelled_by = base.requested_by;
    }

    return base;
  },

  // Build approval log
  buildApprovalLog: (topupId: string, action: TopupAction, fromStatus: TopupStatus, toStatus: TopupStatus) => ({
    id: `log-${randomString(8)}`,
    topup_id: topupId,
    action,
    from_status: fromStatus,
    to_status: toStatus,
    operator_id: `op-${randomString(8)}`,
    operator_name: `操作人_${randomString(4)}`,
    operator_role: action.includes('data_review') ? 'data_operator' : action.includes('finance') ? 'finance' : 'admin',
    notes: `${action} 操作`,
    created_at: new Date().toISOString(),
  }),
};

/**
 * 广告账户工厂
 */
export const adAccountFactory = {
  build: (overrides?: Partial<AdAccountData>) => ({
    id: randomNumber(1, 10000),
    account_code: `ACT_${randomString(10).toUpperCase()}`,
    account_name: `测试账户_${randomString(6)}`,
    status: 'active',
    balance: randomNumber(0, 100000).toFixed(2),
    project_id: randomNumber(1, 100),
    channel_id: randomString(16),
    assigned_to: randomString(16),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  }),

  buildMany: (count: number, overrides?: Partial<AdAccountData>) => {
    return Array.from({ length: count }, () => adAccountFactory.build(overrides))
  },
}

/**
 * 项目工厂
 */
export const projectFactory = {
  build: (overrides?: Partial<ProjectData>) => ({
    id: randomNumber(1, 10000),
    project_name: `测试项目_${randomString(6)}`,
    project_code: `PRJ_${randomString(6).toUpperCase()}`,
    client_name: `客户_${randomString(6)}`,
    status: 'active',
    created_by: randomString(16),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  }),

  buildMany: (count: number, overrides?: Partial<ProjectData>) => {
    return Array.from({ length: count }, () => projectFactory.build(overrides))
  },
}

// 类型定义
export interface UserData {
  id: string
  username: string
  email: string
  role: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface DailyReportData {
  id: number
  ad_account_id: number
  report_date: string
  status: string
  conversions_raw: number
  raw_spend: string
  impressions?: number
  clicks?: number
  notes?: string
  created_at: string
  updated_at: string
}

// Topup Status type (matches STATE_MACHINE.md v2.6 § 9)
export type TopupStatus =
  | 'draft'
  | 'pending_review'
  | 'finance_approve'
  | 'paid'
  | 'completed'
  | 'rejected'
  | 'cancelled';

// Topup Action type
export type TopupAction =
  | 'create'
  | 'submit'
  | 'data_review_approve'
  | 'data_review_reject'
  | 'finance_approve'
  | 'finance_reject'
  | 'mark_paid'
  | 'complete'
  | 'cancel';

export interface TopupRequestData {
  id: string
  tenant_id: string
  project_id: string
  project_name?: string
  ad_account_id?: string
  ad_account_name?: string
  amount: number
  currency: string
  status: TopupStatus
  version: number
  requested_by: string
  requested_by_name?: string
  requested_at: string
  notes?: string
  data_reviewed_by?: string
  data_reviewed_by_name?: string
  data_reviewed_at?: string
  data_review_notes?: string
  finance_approved_by?: string
  finance_approved_by_name?: string
  finance_approved_at?: string
  finance_approval_notes?: string
  paid_at?: string
  payment_reference?: string
  completed_at?: string
  ledger_entry_id?: string
  rejected_by?: string
  rejected_by_name?: string
  rejected_at?: string
  rejection_reason?: string
  cancelled_by?: string
  cancelled_at?: string
  created_at: string
  updated_at: string
}

export interface AdAccountData {
  id: number
  account_code: string
  account_name: string
  status: string
  balance: string
  project_id: number
  channel_id: string
  assigned_to: string
  created_at: string
  updated_at: string
}

export interface ProjectData {
  id: number
  project_name: string
  project_code: string
  client_name: string
  status: string
  created_by: string
  created_at: string
  updated_at: string
}
