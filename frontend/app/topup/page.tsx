'use client';

import React, { useState, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import AppLayout from '@/components/dashboard/AppLayout';
import { PageHeader } from '@/components/layout/page-header';
import RechargeSummaryCards from './components/RechargeSummaryCards';
import RechargeFilters from './components/RechargeFilters';
import RechargeTable from './components/RechargeTable';
import RechargeDetailDrawer from './components/RechargeDetailDrawer';
import {
  RechargeRecord,
  RechargeRecordDetail,
  RechargeStats,
  RechargeFilters as IRechargeFilters,
  RechargeStatus,
  Platform,
  Priority,
  PaymentMethod,
} from './types';
import {
  AlertTriangle,
  Plus,
  Download,
} from 'lucide-react';
import { format, subDays } from 'date-fns';

// 模拟数据
const mockTopupRequests: RechargeRecord[] = [
  {
    id: 1,
    request_code: 'TOP-20241113-001',
    account_name: 'Facebook Main Account',
    account_id: 'act_123456789',
    platform: 'facebook',
    amount: 10000,
    currency: 'USD',
    payment_method: 'bank_transfer',
    status: 'pending',
    requested_by: '投手-张三',
    requested_at: '2024-11-13T09:30:00Z',
    priority: 'high',
    project_name: 'Q4电商推广',
    notes: '双11期间需要增加预算',
  },
  {
    id: 2,
    request_code: 'TOP-20241113-002',
    account_name: 'Google Performance Max',
    account_id: 'ga_987654321',
    platform: 'google',
    amount: 5000,
    currency: 'USD',
    payment_method: 'alipay',
    status: 'processing',
    requested_by: '投手-李四',
    requested_at: '2024-11-13T08:15:00Z',
    approved_by: '财务-王五',
    approved_at: '2024-11-13T10:45:00Z',
    priority: 'normal',
    project_name: '品牌曝光活动',
  },
  {
    id: 3,
    request_code: 'TOP-20241112-003',
    account_name: 'TikTok Gaming Account',
    account_id: 'tt_456789123',
    platform: 'tiktok',
    amount: 8000,
    currency: 'USD',
    payment_method: 'wechat',
    status: 'completed',
    requested_by: '投手-赵六',
    requested_at: '2024-11-12T16:20:00Z',
    approved_by: '财务-孙七',
    approved_at: '2024-11-12T17:30:00Z',
    completed_at: '2024-11-12T18:45:00Z',
    payment_reference: 'TX20241112184500',
    priority: 'urgent',
    project_name: '游戏推广',
    exchange_rate: 7.25,
    actual_amount: 58000,
    fee: 50,
  },
  {
    id: 4,
    request_code: 'TOP-20241111-004',
    account_name: 'Instagram Shopping',
    account_id: 'ig_789123456',
    platform: 'facebook',
    amount: 3000,
    currency: 'USD',
    payment_method: 'credit_card',
    status: 'rejected',
    requested_by: '投手-周八',
    requested_at: '2024-11-11T14:10:00Z',
    approved_by: '财务-吴九',
    approved_at: '2024-11-11T15:30:00Z',
    rejection_reason: '本月预算已用完，请等待下月',
    priority: 'low',
    project_name: '电商推广',
  },
  {
    id: 5,
    request_code: 'TOP-20241110-005',
    account_name: 'Facebook Business Account',
    account_id: 'act_567890123',
    platform: 'facebook',
    amount: 15000,
    currency: 'USD',
    payment_method: 'bank_transfer',
    status: 'pending',
    requested_by: '投手-钱十',
    requested_at: '2024-11-10T11:20:00Z',
    priority: 'urgent',
    project_name: '黑五促销',
    notes: '黑五购物节大促活动充值',
  },
];

// 模拟详情数据
const createMockDetail = (record: RechargeRecord): RechargeRecordDetail => {
  const timeline = [
    {
      id: 1,
      recharge_id: record.id,
      action: 'created' as const,
      actor: record.requested_by,
      actor_role: '投手',
      timestamp: record.requested_at,
      notes: record.notes,
      metadata: {
        platform: record.platform,
        amount: record.amount,
      },
    },
  ];

  if (record.approved_by && record.approved_at) {
    timeline.push({
      id: 2,
      recharge_id: record.id,
      action: 'approved' as const,
      actor: record.approved_by,
      actor_role: '财务',
      timestamp: record.approved_at,
      notes: '审核通过',
    });
  }

  if (record.completed_at) {
    timeline.push({
      id: 3,
      recharge_id: record.id,
      action: 'completed' as const,
      actor: '系统',
      actor_role: 'system',
      timestamp: record.completed_at,
      notes: `充值完成，支付参考号: ${record.payment_reference || 'N/A'}`,
    });
  }

  if (record.rejection_reason) {
    timeline.push({
      id: 4,
      recharge_id: record.id,
      action: 'rejected' as const,
      actor: record.approved_by || '系统',
      actor_role: '财务',
      timestamp: record.approved_at || record.requested_at,
      notes: `驳回原因: ${record.rejection_reason}`,
    });
  }

  const paymentAccount = record.payment_method === 'bank_transfer' ? {
    id: 1,
    platform: record.platform,
    account_name: '公司对公账户',
    account_number: '6225881234567890',
    bank_name: '中国工商银行',
    currency: 'CNY' as const,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  } : undefined;

  return {
    ...record,
    timeline,
    payment_account,
    attachments: record.status === 'completed' ? [
      {
        id: 1,
        name: 'payment_receipt.pdf',
        url: '/files/payment_receipt.pdf',
        type: 'pdf' as const,
      },
    ] : [],
  };
};

/**
 * 充值管理主页面
 *
 * 采用限宽居中布局，包含KPI统计、筛选工具栏、数据表格和详情抽屉
 */
export default function TopupPage() {
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [selectedRecord, setSelectedRecord] = useState<RechargeRecordDetail | null>(null);
  const [detailDrawerOpen, setDetailDrawerOpen] = useState(false);

  // 筛选条件状态
  const [filters, setFilters] = useState<IRechargeFilters>({
    search_term: '',
    status: 'all',
    platform: 'all',
    priority: 'all',
    date_range: {
      start: format(subDays(new Date(), 7), 'yyyy-MM-dd'),
      end: format(new Date(), 'yyyy-MM-dd'),
    },
    payment_method: 'all',
  });

  // 计算统计数据
  const stats: RechargeStats = useMemo(() => {
    return {
      total_requests: mockTopupRequests.length,
      pending_requests: mockTopupRequests.filter(r => r.status === 'pending').length,
      completed_requests: mockTopupRequests.filter(r => r.status === 'completed').length,
      total_amount: mockTopupRequests.reduce((sum, r) => sum + r.amount, 0),
      pending_amount: mockTopupRequests.filter(r => r.status === 'pending').reduce((sum, r) => sum + r.amount, 0),
      monthly_amount: mockTopupRequests
        .filter(r => new Date(r.requested_at).getMonth() === new Date().getMonth())
        .reduce((sum, r) => sum + r.amount, 0),
    };
  }, []);

  // 筛选数据
  const filteredData: RechargeRecord[] = useMemo(() => {
    return mockTopupRequests.filter(request => {
      // 搜索筛选
      const matchesSearch = filters.search_term === '' ||
        request.account_name.toLowerCase().includes(filters.search_term.toLowerCase()) ||
        request.request_code.toLowerCase().includes(filters.search_term.toLowerCase()) ||
        request.requested_by.toLowerCase().includes(filters.search_term.toLowerCase());

      // 状态筛选
      const matchesStatus = filters.status === 'all' || request.status === filters.status;

      // 平台筛选
      const matchesPlatform = filters.platform === 'all' || request.platform === filters.platform;

      // 优先级筛选
      const matchesPriority = filters.priority === 'all' || request.priority === filters.priority;

      // 支付方式筛选
      const matchesPaymentMethod = filters.payment_method === 'all' || request.payment_method === filters.payment_method;

      // 日期范围筛选
      const requestDate = new Date(request.requested_at);
      const startDate = filters.date_range.start ? new Date(filters.date_range.start) : null;
      const endDate = filters.date_range.end ? new Date(filters.date_range.end + 'T23:59:59') : null;

      const matchesDateRange = (!startDate || requestDate >= startDate) &&
        (!endDate || requestDate <= endDate);

      return matchesSearch && matchesStatus && matchesPlatform && matchesPriority && matchesPaymentMethod && matchesDateRange;
    });
  }, [filters]);

  // 处理筛选条件变化
  const handleFiltersChange = (newFilters: IRechargeFilters) => {
    setFilters(newFilters);
  };

  // 重置筛选条件
  const handleReset = () => {
    setFilters({
      search_term: '',
      status: 'all',
      platform: 'all',
      priority: 'all',
      date_range: {
        start: format(subDays(new Date(), 7), 'yyyy-MM-dd'),
        end: format(new Date(), 'yyyy-MM-dd'),
      },
      payment_method: 'all',
    });
    setSelectedIds([]);
  };

  // 导出数据
  const handleExport = () => {
    console.log('导出数据:', filteredData);
    // TODO: 实现导出功能
  };

  // 新建充值申请
  const handleNewRequest = () => {
    console.log('新建充值申请');
    // TODO: 实现新建功能
  };

  // 批量审核
  const handleBatchApprove = () => {
    console.log('批量审核:', selectedIds);
    // TODO: 实现批量审核功能
  };

  // 查看详情
  const handleViewDetail = (record: RechargeRecord) => {
    setDetailLoading(true);
    // 模拟API调用
    setTimeout(() => {
      const detail = createMockDetail(record);
      setSelectedRecord(detail);
      setDetailDrawerOpen(true);
      setDetailLoading(false);
    }, 500);
  };

  // 单行点击
  const handleRowClick = (record: RechargeRecord) => {
    handleViewDetail(record);
  };

  // 审核通过
  const handleApprove = (id: number) => {
    console.log('审核通过:', id);
    // TODO: 实现审核通过功能
  };

  // 驳回申请
  const handleReject = (id: number) => {
    console.log('驳回申请:', id);
    // TODO: 实现驳回功能
  };

  // 标记异常
  const handleMarkException = (id: number) => {
    console.log('标记异常:', id);
    // TODO: 实现标记异常功能
  };

  // 检查是否有紧急申请
  const hasUrgentRequests = filteredData.some(r => r.priority === 'urgent' && r.status === 'pending');

  return (
    <AppLayout>
      {/* 主内容区域：限宽居中 */}
      <div className="flex-1 bg-background">
        <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
          {/* 页面标题 */}
          <PageHeader
            title="充值管理"
            subtitle="管理广告账户充值申请，审批流程和充值记录"
            actions={
              <div className="flex gap-2">
                <Button variant="outline" onClick={handleExport}>
                  <Download className="h-4 w-4 mr-2" />
                  导出记录
                </Button>
                <Button onClick={handleNewRequest}>
                  <Plus className="h-4 w-4 mr-2" />
                  新建充值申请
                </Button>
              </div>
            }
          />

          {/* 紧急申请提醒 */}
          {hasUrgentRequests && (
            <Alert className="border-orange-200 bg-orange-50">
              <AlertTriangle className="h-4 w-4 text-orange-600" />
              <AlertDescription className="text-orange-800">
                您有 {filteredData.filter(r => r.priority === 'urgent' && r.status === 'pending').length} 个紧急充值申请等待处理，请尽快审批。
              </AlertDescription>
            </Alert>
          )}

          {/* KPI 统计卡片区域 */}
          <section>
            <RechargeSummaryCards stats={stats} loading={loading} />
          </section>

          {/* 筛选 / 工具栏区域 */}
          <section>
            <RechargeFilters
              filters={filters}
              onFiltersChange={handleFiltersChange}
              totalCount={filteredData.length}
              onReset={handleReset}
              onExport={handleExport}
              onNewRequest={handleNewRequest}
              selectedCount={selectedIds.length}
              onBatchApprove={selectedIds.length > 0 ? handleBatchApprove : undefined}
              loading={loading}
            />
          </section>

          {/* 列表 / 详情区域 */}
          <section>
            <RechargeTable
              data={filteredData}
              loading={loading}
              onRowClick={handleRowClick}
              onApprove={handleApprove}
              onReject={handleReject}
              onViewDetail={handleViewDetail}
              selectedIds={selectedIds}
              onSelectionChange={setSelectedIds}
            />
          </section>
        </div>
      </div>

      {/* 详情抽屉 */}
      <RechargeDetailDrawer
        open={detailDrawerOpen}
        onClose={() => setDetailDrawerOpen(false)}
        record={selectedRecord}
        onApprove={handleApprove}
        onReject={handleReject}
        onMarkException={handleMarkException}
        loading={detailLoading}
      />
    </AppLayout>
  );
}