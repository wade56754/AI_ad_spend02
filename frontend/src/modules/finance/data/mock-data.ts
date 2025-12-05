/**
 * Finance 模块 Mock 数据
 *
 * TODO: 后续接入真实 API 后删除此文件
 *
 * 对齐：FRONTEND_MODULE_SHELL_PATTERN v1.0
 */

import type {
  TopupRequest,
  FinancialSummary,
  SpendingTrend,
  PlatformSpending,
  TeamSpending,
} from '../types';

export const MOCK_TOPUP_REQUESTS: TopupRequest[] = [
  {
    id: 1,
    user_name: '张三',
    user_role: '投手',
    account_name: 'Facebook广告账户01',
    platform: 'facebook',
    amount: 50000,
    currency: 'CNY',
    reason: '新产品推广活动需要增加预算',
    status: 'pending',
    created_at: '2025-01-13T10:30:00Z',
  },
  {
    id: 2,
    user_name: '李四',
    user_role: '户管',
    account_name: 'TikTok广告账户02',
    platform: 'tiktok',
    amount: 30000,
    currency: 'CNY',
    reason: '月度常规充值',
    status: 'approved',
    created_at: '2025-01-13T09:15:00Z',
    reviewed_at: '2025-01-13T10:20:00Z',
    reviewed_by: '财务经理',
    review_comment: '预算合理，批准充值',
  },
  {
    id: 3,
    user_name: '王五',
    user_role: '投手',
    account_name: 'Google Ads账户03',
    platform: 'google',
    amount: 80000,
    currency: 'CNY',
    reason: '大促活动预算申请',
    status: 'completed',
    created_at: '2025-01-12T14:00:00Z',
    reviewed_at: '2025-01-12T16:30:00Z',
    reviewed_by: '财务总监',
    review_comment: '大促预算已批准',
    receipt_url: '/receipts/receipt_001.pdf',
    transaction_id: 'TXN20250112001',
    completed_at: '2025-01-13T09:00:00Z',
  },
  {
    id: 4,
    user_name: '赵六',
    user_role: '户管',
    account_name: 'Facebook广告账户04',
    platform: 'facebook',
    amount: 20000,
    currency: 'CNY',
    reason: '测试账户充值',
    status: 'rejected',
    created_at: '2025-01-12T11:20:00Z',
    reviewed_at: '2025-01-12T15:45:00Z',
    reviewed_by: '财务经理',
    review_comment: '测试账户无需大额充值，建议使用小额测试',
  },
];

export const MOCK_FINANCIAL_SUMMARY: FinancialSummary = {
  total_balance: 1580000,
  currency: 'CNY',
  this_month_spending: 680000,
  last_month_spending: 520000,
  pending_topups: 180000,
  approved_topups: 420000,
  average_approval_time: 2.5,
  success_rate: 92.5,
  projected_spend: 750000,
};

export const MOCK_SPENDING_TRENDS: SpendingTrend[] = [
  { date: '1月1日', spending: 15000, topups: 50000, balance: 1485000 },
  { date: '1月2日', spending: 22000, topups: 0, balance: 1463000 },
  { date: '1月3日', spending: 18000, topups: 0, balance: 1445000 },
  { date: '1月4日', spending: 25000, topups: 0, balance: 1420000 },
  { date: '1月5日', spending: 20000, topups: 80000, balance: 1480000 },
  { date: '1月6日', spending: 30000, topups: 0, balance: 1450000 },
  { date: '1月7日', spending: 28000, topups: 0, balance: 1422000 },
  { date: '1月8日', spending: 32000, topups: 100000, balance: 1490000 },
];

export const MOCK_PLATFORM_SPENDING: PlatformSpending[] = [
  { platform: 'Facebook', amount: 320000, percentage: 47.1, color: '#1877F2' },
  { platform: 'TikTok', amount: 180000, percentage: 26.5, color: '#000000' },
  { platform: 'Google', amount: 120000, percentage: 17.6, color: '#4285F4' },
  { platform: 'Twitter', amount: 60000, percentage: 8.8, color: '#1DA1F2' },
];

export const MOCK_TEAM_SPENDING: TeamSpending[] = [
  {
    user_name: '张三',
    role: '投手',
    total_spent: 180000,
    budget_utilization: 85,
    projects_count: 8,
    efficiency_score: 92,
  },
  {
    user_name: '李四',
    role: '户管',
    total_spent: 220000,
    budget_utilization: 72,
    projects_count: 12,
    efficiency_score: 88,
  },
  {
    user_name: '王五',
    role: '投手',
    total_spent: 150000,
    budget_utilization: 90,
    projects_count: 6,
    efficiency_score: 95,
  },
  {
    user_name: '赵六',
    role: '户管',
    total_spent: 130000,
    budget_utilization: 65,
    projects_count: 10,
    efficiency_score: 82,
  },
];
