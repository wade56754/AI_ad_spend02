'use client';

import React, { useState, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import AppLayout from '@/components/dashboard/AppLayout';
import { PageHeader } from '@/components/layout/page-header';
import AdAccountSummaryCards from './components/AdAccountSummaryCards';
import AdAccountFilters from './components/AdAccountFilters';
import AdAccountTable from './components/AdAccountTable';
import {
  AdAccount,
  AdAccountStats,
  AdAccountFilters as IAdAccountFilters,
  AccountStatus,
  Platform,
  AccountType,
  RiskLevel
} from './types';
import {
  AlertTriangle,
  Plus,
  Download,
  Eye,
  Edit,
  Trash2,
} from 'lucide-react';
import { format, subDays } from 'date-fns';

// 模拟广告账户数据
const mockAccounts: AdAccount[] = [
  {
    id: 1,
    account_name: 'Facebook Main Account',
    platform: 'facebook',
    account_id: 'act_12345678901234567',
    account_status: 'active',
    account_type: 'business',
    currency: 'USD',
    timezone: 'Asia/Shanghai',
    spending_limit: 10000,
    current_spend: 7500,
    balance: 2500,
    creation_time: '2024-01-15T10:30:00Z',
    last_active: '2025-01-15T18:45:00Z',
    assigned_user_id: 1001,
    assigned_user_name: '张经理',
    assigned_user_email: 'zhang@company.com',
    project_id: 101,
    project_name: '春季推广活动',
    client_id: 201,
    client_name: 'ABC科技公司',
    notes: '主要投放账户，表现良好',
    tags: ['主要账户', '春季'],
    created_at: '2024-01-15T10:30:00Z',
    updated_at: '2025-01-15T18:45:00Z',
    created_by: 'admin',
    performance_metrics: {
      total_spend: 45000,
      total_impressions: 1250000,
      total_clicks: 8500,
      total_conversions: 340,
      avg_cpc: 5.29,
      avg_cpm: 36.0,
      avg_ctr: 0.68,
      avg_cpl: 132.35,
      avg_roas: 3.2,
      last_7d_spend: 2100,
      last_30d_spend: 7500,
      last_7d_conversions: 65,
      last_30d_conversions: 280,
      conversion_rate: 4.0,
      cost_per_result: 132.35,
      return_on_ad_spend: 3.2,
    },
    health_status: {
      risk_level: 'low',
      issues: [],
      recommendations: ['可以考虑适当增加预算'],
      last_check: '2025-01-15T10:00:00Z',
      health_score: 95,
    },
    account_settings: {
      auto_budget_optimization: true,
      budget_alert_threshold: 80,
      performance_alert_threshold: 20,
      enable_auto_pause: false,
      daily_budget_limit: 350,
      timezone_alerts: true,
      weekend_delivery: true,
      creative_rotation_enabled: true,
      audience_expansion_enabled: false,
    },
    last_performance_check: '2025-01-15T10:00:00Z',
    auto_optimization_enabled: true,
    budget_alerts_enabled: true,
  },
  {
    id: 2,
    account_name: 'TikTok Gaming Account',
    platform: 'tiktok',
    account_id: 'tt_98765432109876543',
    account_status: 'paused',
    account_type: 'business',
    currency: 'USD',
    timezone: 'Asia/Shanghai',
    spending_limit: 5000,
    current_spend: 3200,
    balance: 1800,
    creation_time: '2024-02-20T14:15:00Z',
    last_active: '2025-01-12T12:30:00Z',
    assigned_user_id: 1002,
    assigned_user_name: '李主管',
    assigned_user_email: 'li@company.com',
    project_id: 102,
    project_name: '游戏推广项目',
    client_id: 202,
    client_name: 'XYZ游戏公司',
    notes: '暂停中，等待新素材',
    tags: ['游戏', '已暂停'],
    created_at: '2024-02-20T14:15:00Z',
    updated_at: '2025-01-12T16:20:00Z',
    created_by: 'admin',
    performance_metrics: {
      total_spend: 18000,
      total_impressions: 680000,
      total_clicks: 4200,
      total_conversions: 168,
      avg_cpc: 4.29,
      avg_cpm: 26.5,
      avg_ctr: 0.62,
      avg_cpl: 107.14,
      avg_roas: 4.1,
      last_7d_spend: 800,
      last_30d_spend: 2100,
      last_7d_conversions: 28,
      last_30d_conversions: 84,
      conversion_rate: 4.0,
      cost_per_result: 107.14,
      return_on_ad_spend: 4.1,
    },
    health_status: {
      risk_level: 'medium',
      issues: [{
        type: 'performance',
        severity: 'medium',
        description: '最近3天消耗下降明显',
        impact: '可能影响推广效果',
        recommendation: '检查广告素材表现',
        detected_at: '2025-01-13T09:00:00Z',
      }],
      recommendations: ['检查广告素材表现', '考虑调整出价策略'],
      last_check: '2025-01-15T10:00:00Z',
      health_score: 75,
    },
    account_settings: {
      auto_budget_optimization: false,
      budget_alert_threshold: 70,
      performance_alert_threshold: 25,
      enable_auto_pause: true,
      daily_budget_limit: 150,
      timezone_alerts: false,
      weekend_delivery: false,
      creative_rotation_enabled: false,
      audience_expansion_enabled: true,
    },
    last_performance_check: '2025-01-15T10:00:00Z',
    auto_optimization_enabled: false,
    budget_alerts_enabled: true,
  },
  {
    id: 3,
    account_name: 'Google Ads Performance',
    platform: 'google',
    account_id: 'ga_56789012345678901',
    account_status: 'active',
    account_type: 'business',
    currency: 'USD',
    timezone: 'Asia/Shanghai',
    spending_limit: 8000,
    current_spend: 6200,
    balance: 1800,
    creation_time: '2024-03-10T09:45:00Z',
    last_active: '2025-01-15T16:20:00Z',
    assigned_user_id: 1003,
    assigned_user_name: '王总监',
    assigned_user_email: 'wang@company.com',
    project_id: 103,
    project_name: '电商转化项目',
    client_id: 203,
    client_name: 'DEF电商公司',
    notes: '搜索广告表现稳定',
    tags: ['电商', '搜索'],
    created_at: '2024-03-10T09:45:00Z',
    updated_at: '2025-01-15T16:20:00Z',
    created_by: 'admin',
    performance_metrics: {
      total_spend: 28000,
      total_impressions: 890000,
      total_clicks: 5800,
      total_conversions: 290,
      avg_cpc: 4.83,
      avg_cpm: 31.5,
      avg_ctr: 0.65,
      avg_cpl: 96.55,
      avg_roas: 2.8,
      last_7d_spend: 1800,
      last_30d_spend: 6800,
      last_7d_conversions: 58,
      last_30d_conversions: 232,
      conversion_rate: 4.0,
      cost_per_result: 96.55,
      return_on_ad_spend: 2.8,
    },
    health_status: {
      risk_level: 'low',
      issues: [],
      recommendations: ['ROI有提升空间，可以优化关键词'],
      last_check: '2025-01-15T10:00:00Z',
      health_score: 85,
    },
    account_settings: {
      auto_budget_optimization: true,
      budget_alert_threshold: 75,
      performance_alert_threshold: 15,
      enable_auto_pause: false,
      daily_budget_limit: 280,
      timezone_alerts: true,
      weekend_delivery: true,
      creative_rotation_enabled: true,
      audience_expansion_enabled: false,
    },
    last_performance_check: '2025-01-15T10:00:00Z',
    auto_optimization_enabled: true,
    budget_alerts_enabled: true,
  },
  {
    id: 4,
    account_name: 'Instagram Fashion Account',
    platform: 'instagram',
    account_id: 'ig_34567890123456789',
    account_status: 'banned',
    account_type: 'business',
    currency: 'USD',
    timezone: 'Asia/Shanghai',
    spending_limit: 3000,
    current_spend: 1200,
    balance: 0,
    creation_time: '2024-04-05T11:20:00Z',
    last_active: '2025-01-10T09:15:00Z',
    assigned_user_id: 1004,
    assigned_user_name: '陈经理',
    assigned_user_email: 'chen@company.com',
    project_id: 104,
    project_name: '时尚品牌推广',
    client_id: 204,
    client_name: 'GHI时尚集团',
    notes: '账户被封禁，正在申诉',
    tags: ['时尚', '已封禁'],
    created_at: '2024-04-05T11:20:00Z',
    updated_at: '2025-01-14T14:30:00Z',
    created_by: 'admin',
    performance_metrics: {
      total_spend: 1200,
      total_impressions: 340000,
      total_clicks: 1800,
      total_conversions: 72,
      avg_cpc: 0.67,
      avg_cpm: 3.53,
      avg_ctr: 0.53,
      avg_cpl: 16.67,
      avg_roas: 1.8,
      last_7d_spend: 0,
      last_30d_spend: 0,
      last_7d_conversions: 0,
      last_30d_conversions: 0,
      conversion_rate: 4.0,
      cost_per_result: 16.67,
      return_on_ad_spend: 1.8,
    },
    health_status: {
      risk_level: 'critical',
      issues: [{
        type: 'policy',
        severity: 'critical',
        description: '账户违反平台政策被封禁',
        impact: '无法进行广告投放',
        recommendation: '提交申诉或创建新账户',
        detected_at: '2025-01-14T10:00:00Z',
      }],
      recommendations: ['提交申诉或创建新账户'],
      last_check: '2025-01-15T10:00:00Z',
      health_score: 0,
    },
    account_settings: {
      auto_budget_optimization: false,
      budget_alert_threshold: 60,
      performance_alert_threshold: 30,
      enable_auto_pause: true,
      daily_budget_limit: 100,
      timezone_alerts: true,
      weekend_delivery: true,
      creative_rotation_enabled: false,
      audience_expansion_enabled: false,
    },
    last_performance_check: '2025-01-15T10:00:00Z',
    auto_optimization_enabled: false,
    budget_alerts_enabled: false,
  },
  {
    id: 5,
    account_name: 'LinkedIn B2B Account',
    platform: 'linkedin',
    account_id: 'li_23456789012345678',
    account_status: 'pending',
    account_type: 'agency',
    currency: 'USD',
    timezone: 'Asia/Shanghai',
    spending_limit: 2000,
    current_spend: 0,
    balance: 2000,
    creation_time: '2024-05-12T16:30:00Z',
    last_active: '2025-01-14T13:45:00Z',
    assigned_user_id: 1005,
    assigned_user_name: '刘主管',
    assigned_user_email: 'liu@company.com',
    project_id: 105,
    project_name: 'B2B企业服务',
    client_id: 205,
    client_name: 'JKL企业服务',
    notes: '等待平台审核',
    tags: ['B2B', '企业服务'],
    created_at: '2024-05-12T16:30:00Z',
    updated_at: '2025-01-14T13:45:00Z',
    created_by: 'admin',
    performance_metrics: {
      total_spend: 0,
      total_impressions: 0,
      total_clicks: 0,
      total_conversions: 0,
      avg_cpc: 0,
      avg_cpm: 0,
      avg_ctr: 0,
      avg_cpl: 0,
      avg_roas: 0,
      last_7d_spend: 0,
      last_30d_spend: 0,
      last_7d_conversions: 0,
      last_30d_conversions: 0,
      conversion_rate: 0,
      cost_per_result: 0,
      return_on_ad_spend: 0,
    },
    health_status: {
      risk_level: 'low',
      issues: [],
      recommendations: ['等待审核通过后开始投放'],
      last_check: '2025-01-15T10:00:00Z',
      health_score: 100,
    },
    account_settings: {
      auto_budget_optimization: true,
      budget_alert_threshold: 80,
      performance_alert_threshold: 20,
      enable_auto_pause: false,
      daily_budget_limit: 80,
      timezone_alerts: true,
      weekend_delivery: false,
      creative_rotation_enabled: true,
      audience_expansion_enabled: true,
    },
    last_performance_check: '2025-01-15T10:00:00Z',
    auto_optimization_enabled: true,
    budget_alerts_enabled: true,
  },
];

/**
 * 广告账户管理主页面
 *
 * 采用限宽居中布局，包含KPI统计、筛选工具栏、数据表格
 */
export default function AdAccountsPage() {
  const [loading, setLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  // 筛选条件状态
  const [filters, setFilters] = useState<IAdAccountFilters>({
    search_term: '',
    platform: 'all',
    status: 'all',
    type: 'all',
    assigned_user_id: 'all',
    project_id: 'all',
    client_id: 'all',
    risk_level: 'all',
    balance_range: {
      min: undefined,
      max: undefined,
    },
    spend_range: {
      min: undefined,
      max: undefined,
    },
    date_range: {
      start: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
      end: format(new Date(), 'yyyy-MM-dd'),
    },
    has_issues: null,
    auto_optimization: null,
    tags: [],
    sort_by: 'updated_at',
    sort_order: 'desc',
  });

  // 计算统计数据
  const stats: AdAccountStats = useMemo(() => {
    return {
      total_accounts: mockAccounts.length,
      active_accounts: mockAccounts.filter(a => a.account_status === 'active').length,
      paused_accounts: mockAccounts.filter(a => a.account_status === 'paused').length,
      banned_accounts: mockAccounts.filter(a => a.account_status === 'banned').length,
      pending_accounts: mockAccounts.filter(a => a.account_status === 'pending').length,
      total_spending_limit: mockAccounts.reduce((sum, a) => sum + a.spending_limit, 0),
      total_current_spend: mockAccounts.reduce((sum, a) => sum + a.current_spend, 0),
      total_balance: mockAccounts.reduce((sum, a) => sum + a.balance, 0),
      average_performance_score: mockAccounts.reduce((sum, a) => sum + (a.health_status?.health_score || 0), 0) / mockAccounts.length,
      high_risk_accounts: mockAccounts.filter(a => a.health_status?.risk_level === 'high' || a.health_status?.risk_level === 'critical').length,
      accounts_needing_attention: mockAccounts.filter(a => a.health_status?.issues && a.health_status.issues.length > 0).length,
      accounts_by_platform: {
        facebook: mockAccounts.filter(a => a.platform === 'facebook').length,
        tiktok: mockAccounts.filter(a => a.platform === 'tiktok').length,
        google: mockAccounts.filter(a => a.platform === 'google').length,
        twitter: mockAccounts.filter(a => a.platform === 'twitter').length,
        instagram: mockAccounts.filter(a => a.platform === 'instagram').length,
        youtube: mockAccounts.filter(a => a.platform === 'youtube').length,
        linkedin: mockAccounts.filter(a => a.platform === 'linkedin').length,
      },
      accounts_by_status: {
        active: mockAccounts.filter(a => a.account_status === 'active').length,
        paused: mockAccounts.filter(a => a.account_status === 'paused').length,
        banned: mockAccounts.filter(a => a.account_status === 'banned').length,
        pending: mockAccounts.filter(a => a.account_status === 'pending').length,
        restricted: mockAccounts.filter(a => a.account_status === 'restricted').length,
      },
      total_conversions: mockAccounts.reduce((sum, a) => sum + (a.performance_metrics?.total_conversions || 0), 0),
      average_roas: mockAccounts.reduce((sum, a) => sum + (a.performance_metrics?.avg_roas || 0), 0) / mockAccounts.filter(a => a.performance_metrics?.avg_roas && a.performance_metrics.avg_roas > 0).length,
      last_24h_spend: mockAccounts.reduce((sum, a) => sum + (a.performance_metrics?.last_7d_spend || 0) / 7, 0), // 简化计算
      last_7d_spend: mockAccounts.reduce((sum, a) => sum + (a.performance_metrics?.last_7d_spend || 0), 0),
      last_30d_spend: mockAccounts.reduce((sum, a) => sum + (a.performance_metrics?.last_30d_spend || 0), 0),
      utilization_rate: mockAccounts.reduce((sum, a) => sum + ((a.current_spend / a.spending_limit) * 100), 0) / mockAccounts.length,
    };
  }, []);

  // 筛选数据
  const filteredData: AdAccount[] = useMemo(() => {
    return mockAccounts.filter(account => {
      // 搜索筛选
      const matchesSearch = filters.search_term === '' ||
        account.account_name.toLowerCase().includes(filters.search_term.toLowerCase()) ||
        account.account_id.toLowerCase().includes(filters.search_term.toLowerCase()) ||
        account.assigned_user_name?.toLowerCase().includes(filters.search_term.toLowerCase());

      // 状态筛选
      const matchesStatus = filters.status === 'all' || account.account_status === filters.status;

      // 平台筛选
      const matchesPlatform = filters.platform === 'all' || account.platform === filters.platform;

      // 类型筛选
      const matchesType = filters.type === 'all' || account.account_type === filters.type;

      // 风险等级筛选
      const matchesRiskLevel = filters.risk_level === 'all' ||
        (account.health_status && account.health_status.risk_level === filters.risk_level);

      // 日期范围筛选
      const startDate = filters.date_range.start ? new Date(filters.date_range.start) : null;
      const endDate = filters.date_range.end ? new Date(filters.date_range.end + 'T23:59:59') : null;
      const createdDate = new Date(account.created_at);

      const matchesDateRange = (!startDate || createdDate >= startDate) &&
        (!endDate || createdDate <= endDate);

      // 余额范围筛选
      const matchesBalanceRange = (!filters.balance_range.min || account.balance >= filters.balance_range.min) &&
        (!filters.balance_range.max || account.balance <= filters.balance_range.max);

      // 消耗范围筛选
      const matchesSpendRange = (!filters.spend_range.min || account.current_spend >= filters.spend_range.min) &&
        (!filters.spend_range.max || account.current_spend <= filters.spend_range.max);

      // 问题筛选
      const hasIssues = account.health_status && account.health_status.issues.length > 0;
      const matchesHasIssues = filters.has_issues === null ||
        (filters.has_issues && hasIssues) ||
        (!filters.has_issues && !hasIssues);

      // 自动优化筛选
      const matchesAutoOptimization = filters.auto_optimization === null ||
        (filters.auto_optimization && account.auto_optimization_enabled) ||
        (!filters.auto_optimization && !account.auto_optimization_enabled);

      // 标签筛选
      const matchesTags = filters.tags.length === 0 ||
        (account.tags && filters.tags.some(tag => account.tags?.includes(tag)));

      return matchesSearch && matchesStatus && matchesPlatform && matchesType &&
             matchesRiskLevel && matchesDateRange && matchesBalanceRange &&
             matchesSpendRange && matchesHasIssues && matchesAutoOptimization && matchesTags;
    }).sort((a, b) => {
      // 排序
      let aValue: any = a[filters.sort_by];
      let bValue: any = b[filters.sort_by];

      if (aValue instanceof Date) aValue = aValue.getTime();
      if (bValue instanceof Date) bValue = bValue.getTime();

      if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      if (filters.sort_order === 'asc') {
        return aValue > bValue ? 1 : aValue < bValue ? -1 : 0;
      } else {
        return aValue < bValue ? 1 : aValue > bValue ? -1 : 0;
      }
    });
  }, [filters]);

  // 处理筛选条件变化
  const handleFiltersChange = (newFilters: IAdAccountFilters) => {
    setFilters(newFilters);
  };

  // 重置筛选条件
  const handleReset = () => {
    setFilters({
      search_term: '',
      platform: 'all',
      status: 'all',
      type: 'all',
      assigned_user_id: 'all',
      project_id: 'all',
      client_id: 'all',
      risk_level: 'all',
      balance_range: {
        min: undefined,
        max: undefined,
      },
      spend_range: {
        min: undefined,
        max: undefined,
      },
      date_range: {
        start: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
        end: format(new Date(), 'yyyy-MM-dd'),
      },
      has_issues: null,
      auto_optimization: null,
      tags: [],
      sort_by: 'updated_at',
      sort_order: 'desc',
    });
    setSelectedIds([]);
  };

  // 导出数据
  const handleExport = () => {
    console.log('导出广告账户数据:', filteredData);
    // TODO: 实现导出功能
  };

  // 新建账户
  const handleNewAccount = () => {
    console.log('新建广告账户');
    // TODO: 实现新建功能
  };

  // 查看详情
  const handleViewDetail = (account: AdAccount) => {
    console.log('查看账户详情:', account);
    // TODO: 实现详情查看功能
  };

  // 编辑账户
  const handleEdit = (account: AdAccount) => {
    console.log('编辑账户:', account);
    // TODO: 实现编辑功能
  };

  // 状态变更
  const handleStatusChange = (id: number, status: AccountStatus) => {
    console.log('更改账户状态:', id, status);
    // TODO: 实现状态变更功能
  };

  // 删除账户
  const handleDelete = (id: number) => {
    console.log('删除账户:', id);
    // TODO: 实现删除功能
  };

  // 导出选中项
  const handleExportSelected = (selectedIds: number[]) => {
    console.log('导出选中的账户:', selectedIds);
    // TODO: 实现批量导出功能
  };

  // 检查是否有高风险账户
  const hasHighRiskAccounts = filteredData.some(a =>
    a.health_status?.risk_level === 'high' || a.health_status?.risk_level === 'critical'
  );

  return (
    <AppLayout>
      {/* 主内容区域：限宽居中 */}
      <div className="flex-1 bg-background">
        <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
          {/* 页面标题 */}
          <PageHeader
            title="广告账户管理"
            subtitle="管理和监控所有广告账户的状态、表现和健康度"
            actions={
              <div className="flex gap-2">
                <Button variant="outline" onClick={handleExport}>
                  <Download className="h-4 w-4 mr-2" />
                  导出数据
                </Button>
                <Button onClick={handleNewAccount}>
                  <Plus className="h-4 w-4 mr-2" />
                  新建账户
                </Button>
              </div>
            }
          />

          {/* 高风险账户提醒 */}
          {hasHighRiskAccounts && (
            <Alert className="border-red-200 bg-red-50">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-800">
                您有 {filteredData.filter(a =>
                  a.health_status?.risk_level === 'high' || a.health_status?.risk_level === 'critical'
                ).length} 个高风险账户，请立即处理。
              </AlertDescription>
            </Alert>
          )}

          {/* KPI 统计卡片区域 */}
          <section>
            <AdAccountSummaryCards stats={stats} loading={loading} />
          </section>

          {/* 筛选 / 工具栏区域 */}
          <section>
            <AdAccountFilters
              filters={filters}
              onFiltersChange={handleFiltersChange}
              totalCount={filteredData.length}
              onReset={handleReset}
              onExport={handleExport}
              onNewAccount={handleNewAccount}
              loading={loading}
            />
          </section>

          {/* 列表区域 */}
          <section>
            <AdAccountTable
              data={filteredData}
              loading={loading}
              onRowClick={handleViewDetail}
              onViewDetail={handleViewDetail}
              onEdit={handleEdit}
              onStatusChange={handleStatusChange}
              onDelete={handleDelete}
              onExportSelected={handleExportSelected}
              selectedIds={selectedIds}
              onSelectionChange={setSelectedIds}
            />
          </section>
        </div>
      </div>
    </AppLayout>
  );
}