/**
 * 测试数据 Mock
 *
 * 用于 Playwright 路由拦截时返回测试数据
 */

// ============================================================
// A1 驾驶舱 Mock 数据
// ============================================================

export const mockDashboardData = {
  success: {
    kpi: {
      spend: 150000,
      conversions: 1500,
      cpl: 100,
      profit: 50000,
    },
    ops_status: {
      active_projects: 10,
      abnormal_projects: 2,
      pending_topups: 5,
    },
    top_spend: [
      { id: 'proj-1', name: '项目A', spend: 50000, cpl: 100 },
      { id: 'proj-2', name: '项目B', spend: 40000, cpl: 120 },
      { id: 'proj-3', name: '项目C', spend: 30000, cpl: 90 },
    ],
    top_roas_worst: [
      { id: 'proj-4', name: '项目D', roas: 0.5 },
      { id: 'proj-5', name: '项目E', roas: 0.6 },
    ],
  },
  empty: {
    kpi: { spend: 0, conversions: 0, cpl: null, profit: 0 },
    ops_status: { active_projects: 0, abnormal_projects: 0, pending_topups: 0 },
    top_spend: [],
    top_roas_worst: [],
  },
  abnormal: {
    kpi: { spend: 100000, conversions: 50, cpl: 2000, profit: -50000 },
    ops_status: { active_projects: 10, abnormal_projects: 5, pending_topups: 10 },
    top_spend: [
      { id: 'proj-abnormal-1', name: '超标项目', spend: 100000, cpl: 2000, target_cpl: 100, is_abnormal: true },
    ],
    top_roas_worst: [],
  },
};

// ============================================================
// A2 资金总览 Mock 数据
// ============================================================

export const mockFundData = {
  success: {
    summary: {
      topup: 500000,
      spend: 350000,
      balance: 150000,
      receivable: 50000,
      occupied: 30000,
    },
    transactions: [
      { id: 'txn-1', date: '2024-12-23', type: 'topup', amount: 100000, account: '账户A' },
      { id: 'txn-2', date: '2024-12-22', type: 'spend', amount: -50000, account: '账户A' },
    ],
  },
  empty: {
    summary: { topup: 0, spend: 0, balance: 0, receivable: 0, occupied: 0 },
    transactions: [],
  },
  negative_balance: {
    summary: {
      topup: 100000,
      spend: 150000,
      balance: -50000,  // 负余额
      receivable: 0,
      occupied: 0,
    },
    transactions: [],
  },
};

// ============================================================
// B1 充值审批 Mock 数据
// ============================================================

export const mockTopupData = {
  success: {
    items: [
      { id: 'topup-1', amount: 50000, status: 'draft', project: '项目A', created_at: '2024-12-23' },
      { id: 'topup-2', amount: 100000, status: 'pending_review', project: '项目B', created_at: '2024-12-22' },
      { id: 'topup-3', amount: 80000, status: 'finance_approve', project: '项目C', created_at: '2024-12-21' },
      { id: 'topup-4', amount: 60000, status: 'completed', project: '项目D', created_at: '2024-12-20' },
    ],
    total: 4,
  },
  empty: {
    items: [],
    total: 0,
  },
};

// ============================================================
// B2 日报审核 Mock 数据
// ============================================================

export const mockDailyReportData = {
  success: {
    items: [
      {
        id: 'dr-1',
        date: '2024-12-23',
        project_name: '项目A',
        pitcher_name: '投手小王',
        conversions: 100,
        spend: 10000,
        cpl: 100,
        status: 'trend_pending',
      },
      {
        id: 'dr-2',
        date: '2024-12-22',
        project_name: '项目B',
        pitcher_name: '投手小李',
        conversions: 80,
        spend: 8000,
        cpl: 100,
        status: 'trend_ok',
      },
    ],
    total: 2,
  },
  empty: {
    items: [],
    total: 0,
  },
  abnormal_cpl: {
    items: [
      {
        id: 'dr-abnormal-1',
        date: '2024-12-23',
        project_name: '测试项目',
        pitcher_name: '测试投手',
        conversions: 10,
        spend: 10000,
        cpl: 1000,  // CPL 超标
        target_cpl: 100,
        status: 'trend_pending',
        warnings: ['CPL 超过预警值'],
      },
    ],
    total: 1,
  },
};

// ============================================================
// C1 项目管理 Mock 数据
// ============================================================

export const mockProjectData = {
  success: {
    items: [
      { id: 'proj-1', name: '项目A', status: 'active', budget: 100000, spent: 50000, owner: '负责人A' },
      { id: 'proj-2', name: '项目B', status: 'planning', budget: 80000, spent: 0, owner: '负责人B' },
      { id: 'proj-3', name: '项目C', status: 'completed', budget: 60000, spent: 60000, owner: '负责人A' },
    ],
    total: 3,
  },
  empty: {
    items: [],
    total: 0,
  },
  over_budget: {
    items: [
      { id: 'proj-over-1', name: '超支项目', status: 'active', budget: 50000, spent: 80000, owner: '负责人C' },
    ],
    total: 1,
  },
};

// ============================================================
// D1 月度结算 Mock 数据
// ============================================================

export const mockSettlementData = {
  success: {
    items: [
      {
        id: 'settle-1',
        month: '2024-12',
        project: '项目A',
        spend: 100000,
        conversions: 1000,
        revenue: 150000,
        profit: 50000,
        status: 'draft',
      },
      {
        id: 'settle-2',
        month: '2024-11',
        project: '项目B',
        spend: 80000,
        conversions: 800,
        revenue: 120000,
        profit: 40000,
        status: 'locked',
      },
    ],
    total: 2,
  },
  empty: {
    items: [],
    total: 0,
  },
  negative_profit: {
    items: [
      {
        id: 'settle-loss-1',
        month: '2024-12',
        project: '亏损项目',
        spend: 100000,
        conversions: 500,
        revenue: 50000,
        profit: -50000,  // 负毛利
        status: 'draft',
      },
    ],
    total: 1,
  },
};
