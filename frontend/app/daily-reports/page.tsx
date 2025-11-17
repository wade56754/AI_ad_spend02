'use client';

import React, { useState, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import AppLayout from '@/components/dashboard/AppLayout';
import { PageHeader } from '@/components/layout/page-header';
import DailyReportSummaryCards from './components/DailyReportSummaryCards';
import DailyReportFilters from './components/DailyReportFilters';
import DailyReportTable from './components/DailyReportTable';
import {
  DailyReport,
  DailyReportStats,
  DailyReportFilters as IDailyReportFilters,
  ReportStatus,
  DateRange
} from './types';
import {
  AlertTriangle,
  Plus,
  Download,
  Eye,
  Edit,
  Clock,
  CheckCircle,
} from 'lucide-react';
import { format, subDays, startOfDay, endOfDay } from 'date-fns';

// 模拟日报数据
const mockReports: DailyReport[] = [
  {
    id: 1,
    report_date: '2025-01-15',
    project_id: 1,
    project_name: '春季推广活动',
    account_id: 1,
    account_name: 'Facebook Main Account',
    platform: 'facebook',
    submitted_by: 1001,
    submitted_by_name: '张数据员',
    submitted_by_email: 'zhang@company.com',
    status: 'approved',
    spend_amount: 1250.50,
    currency: 'USD',
    follow_count: 85,
    conversion_count: 12,
    cpl: 14.71,
    roi: 3.2,
    notes: '今日投放效果良好，转化率有所提升',
    submitted_at: '2025-01-15T18:30:00Z',
    reviewed_by: 1002,
    reviewed_by_name: '李审核员',
    reviewed_by_email: 'li@company.com',
    reviewed_at: '2025-01-15T20:15:00Z',
    review_notes: '数据准确，审核通过',
    attachments: [
      {
        id: 1,
        name: '投放截图.png',
        url: '/screenshots/ad_screenshot.png',
        size: 1024576,
        type: 'image/png',
        uploaded_at: '2025-01-15T18:30:00Z',
        uploaded_by: 1001,
        description: '投放效果截图'
      },
    ],
    performance_metrics: {
      ctr: 0.025,
      cpm: 8.5,
      reach: 147000,
      impressions: 588000,
      frequency: 4.0,
      clicks: 14700,
      cpc: 0.085,
      conversion_rate: 0.082,
      cost_per_conversion: 104.21,
      return_on_ad_spend: 3.2,
    },
    quality_score: 92,
    is_anomaly: false,
    anomaly_reasons: [],
    tags: ['优质报告', '高ROI'],
    created_at: '2025-01-15T18:30:00Z',
    updated_at: '2025-01-15T20:15:00Z',
  },
  {
    id: 2,
    report_date: '2025-01-15',
    project_id: 2,
    project_name: '品牌形象提升',
    account_id: 2,
    account_name: 'TikTok Gaming Account',
    platform: 'tiktok',
    submitted_by: 1002,
    submitted_by_name: '王投手',
    submitted_by_email: 'wang@company.com',
    status: 'pending',
    spend_amount: 890.25,
    currency: 'USD',
    follow_count: 62,
    conversion_count: 8,
    cpl: 13.66,
    roi: 2.8,
    notes: '今日消耗略高，但整体表现稳定',
    submitted_at: '2025-01-15T19:45:00Z',
    attachments: [],
    performance_metrics: {
      ctr: 0.018,
      cpm: 6.2,
      reach: 143500,
      impressions: 458000,
      frequency: 3.2,
      clicks: 8244,
      cpc: 0.108,
      conversion_rate: 0.097,
      cost_per_conversion: 111.28,
      return_on_ad_spend: 2.8,
    },
    quality_score: 85,
    is_anomaly: false,
    anomaly_reasons: [],
    tags: ['待审核'],
    created_at: '2025-01-15T19:45:00Z',
    updated_at: '2025-01-15T19:45:00Z',
  },
  {
    id: 3,
    report_date: '2025-01-14',
    project_id: 1,
    project_name: '春季推广活动',
    account_id: 3,
    account_name: 'Google Ads Performance',
    platform: 'google',
    submitted_by: 1003,
    submitted_by_name: '李户管',
    submitted_by_email: 'li@company.com',
    status: 'needs_revision',
    spend_amount: 980.75,
    currency: 'USD',
    follow_count: 45,
    conversion_count: 6,
    cpl: 16.35,
    roi: 2.1,
    notes: '转化成本偏高，需要优化投放策略',
    submitted_at: '2025-01-14T17:20:00Z',
    reviewed_by: 1001,
    reviewed_by_name: '张审核员',
    reviewed_by_email: 'zhang@company.com',
    reviewed_at: '2025-01-14T19:30:00Z',
    review_notes: 'CPL过高，请优化素材和出价',
    attachments: [
      {
        id: 2,
        name: '数据报表.xlsx',
        url: '/reports/daily_report.xlsx',
        size: 2048576,
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        uploaded_at: '2025-01-14T17:20:00Z',
        uploaded_by: 1003,
        description: '详细数据报表'
      },
    ],
    performance_metrics: {
      ctr: 0.015,
      cpm: 7.8,
      reach: 125600,
      impressions: 628000,
      frequency: 5.0,
      clicks: 9420,
      cpc: 0.104,
      conversion_rate: 0.064,
      cost_per_conversion: 163.46,
      return_on_ad_spend: 2.1,
    },
    quality_score: 72,
    is_anomaly: true,
    anomaly_reasons: ['CPL异常偏高', '转化率低于平均水平'],
    tags: ['需修改', '异常数据'],
    created_at: '2025-01-14T17:20:00Z',
    updated_at: '2025-01-14T19:30:00Z',
  },
  {
    id: 4,
    report_date: '2025-01-14',
    project_id: 3,
    project_name: '夏季促销活动',
    account_id: 4,
    account_name: 'Instagram Fashion Account',
    platform: 'instagram',
    submitted_by: 1004,
    submitted_by_name: '陈经理',
    submitted_by_email: 'chen@company.com',
    status: 'approved',
    spend_amount: 750.00,
    currency: 'USD',
    follow_count: 120,
    conversion_count: 15,
    cpl: 12.50,
    roi: 4.5,
    notes: 'Instagram表现优异，粉丝增长稳定',
    submitted_at: '2025-01-14T16:10:00Z',
    reviewed_by: 1002,
    reviewed_by_name: '李审核员',
    reviewed_by_email: 'li@company.com',
    reviewed_at: '2025-01-14T18:25:00Z',
    review_notes: '数据优秀，继续保持',
    attachments: [
      {
        id: 3,
        name: 'Instagram分析.pdf',
        url: '/reports/instagram_analysis.pdf',
        size: 1536000,
        type: 'application/pdf',
        uploaded_at: '2025-01-14T16:10:00Z',
        uploaded_by: 1004,
        description: 'Instagram平台分析报告'
      },
    ],
    performance_metrics: {
      ctr: 0.032,
      cpm: 9.2,
      reach: 81500,
      impressions: 244500,
      frequency: 3.0,
      clicks: 7824,
      cpc: 0.096,
      conversion_rate: 0.192,
      cost_per_conversion: 50.00,
      return_on_ad_spend: 4.5,
    },
    quality_score: 95,
    is_anomaly: false,
    anomaly_reasons: [],
    tags: ['优质报告', 'Instagram'],
    created_at: '2025-01-14T16:10:00Z',
    updated_at: '2025-01-14T18:25:00Z',
  },
  {
    id: 5,
    report_date: '2025-01-13',
    project_id: 4,
    project_name: 'B2B企业服务',
    account_id: 5,
    account_name: 'LinkedIn B2B Account',
    platform: 'linkedin',
    submitted_by: 1005,
    submitted_by_name: '刘主管',
    submitted_by_email: 'liu@company.com',
    status: 'rejected',
    spend_amount: 450.30,
    currency: 'USD',
    follow_count: 25,
    conversion_count: 2,
    cpl: 18.01,
    roi: 1.2,
    notes: 'B2B业务转化周期较长，需要耐心跟进',
    submitted_at: '2025-01-13T15:30:00Z',
    reviewed_by: 1001,
    reviewed_by_name: '张审核员',
    reviewed_by_email: 'zhang@company.com',
    reviewed_at: '2025-01-13T17:45:00Z',
    review_notes: 'ROI过低，建议调整投放策略',
    attachments: [],
    performance_metrics: {
      ctr: 0.008,
      cpm: 12.5,
      reach: 36024,
      impressions: 180120,
      frequency: 5.0,
      clicks: 1441,
      cpc: 0.313,
      conversion_rate: 0.139,
      cost_per_conversion: 225.15,
      return_on_ad_spend: 1.2,
    },
    quality_score: 68,
    is_anomaly: true,
    anomaly_reasons: ['ROI过低', '点击成本偏高'],
    tags: ['已拒绝', '低ROI'],
    created_at: '2025-01-13T15:30:00Z',
    updated_at: '2025-01-13T17:45:00Z',
  },
];

/**
 * 日报管理主页面
 *
 * 采用限宽居中布局，包含KPI统计、筛选工具栏、数据表格
 */
export default function DailyReportsPage() {
  const [loading, setLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  // 筛选条件状态
  const [filters, setFilters] = useState<IDailyReportFilters>({
    search_term: '',
    status: 'all',
    project_id: 'all',
    account_id: 'all',
    submitted_by: 'all',
    reviewed_by: 'all',
    date_range: 'last_7_days',
    custom_date_range: {
      start: format(subDays(new Date(), 7), 'yyyy-MM-dd'),
      end: format(new Date(), 'yyyy-MM-dd'),
    },
    spend_range: {
      min: undefined,
      max: undefined,
    },
    roi_range: {
      min: undefined,
      max: undefined,
    },
    has_attachments: null,
    has_anomalies: null,
    quality_score_range: {
      min: undefined,
      max: undefined,
    },
    tags: [],
    sort_by: 'submitted_at',
    sort_order: 'desc',
  });

  // 计算统计数据
  const stats: DailyReportStats = useMemo(() => {
    return {
      total_reports: mockReports.length,
      pending_reports: mockReports.filter(r => r.status === 'pending').length,
      approved_reports: mockReports.filter(r => r.status === 'approved').length,
      rejected_reports: mockReports.filter(r => r.status === 'rejected').length,
      needs_revision_reports: mockReports.filter(r => r.status === 'needs_revision').length,
      total_spend: mockReports.reduce((sum, r) => sum + r.spend_amount, 0),
      total_conversions: mockReports.reduce((sum, r) => sum + r.conversion_count, 0),
      average_roi: mockReports.reduce((sum, r) => sum + r.roi, 0) / mockReports.length,
      average_cpl: mockReports.reduce((sum, r) => sum + r.cpl, 0) / mockReports.length,
      reports_today: mockReports.filter(r => {
        const reportDate = new Date(r.report_date);
        const today = new Date();
        return reportDate.toDateString() === today.toDateString();
      }).length,
      reports_this_week: mockReports.filter(r => {
        const reportDate = new Date(r.report_date);
        const weekStart = subDays(new Date(), 7);
        return reportDate >= weekStart;
      }).length,
      reports_this_month: mockReports.filter(r => {
        const reportDate = new Date(r.report_date);
        const monthStart = new Date();
        monthStart.setDate(1);
        return reportDate >= monthStart;
      }).length,
      pending_reviews_today: mockReports.filter(r => {
        return r.status === 'pending' && new Date(r.submitted_at).toDateString() === new Date().toDateString();
      }).length,
      approval_rate: mockReports.filter(r => r.status !== 'pending').length > 0
        ? mockReports.filter(r => r.status === 'approved').length / mockReports.filter(r => r.status !== 'pending').length
        : 0,
      average_quality_score: mockReports.reduce((sum, r) => sum + (r.quality_score || 0), 0) / mockReports.length,
      anomaly_reports: mockReports.filter(r => r.is_anomaly).length,
      reports_by_status: {
        pending: mockReports.filter(r => r.status === 'pending').length,
        approved: mockReports.filter(r => r.status === 'approved').length,
        rejected: mockReports.filter(r => r.status === 'rejected').length,
        needs_revision: mockReports.filter(r => r.status === 'needs_revision').length,
      },
      reports_by_platform: {
        facebook: mockReports.filter(r => r.platform === 'facebook').length,
        tiktok: mockReports.filter(r => r.platform === 'tiktok').length,
        google: mockReports.filter(r => r.platform === 'google').length,
        instagram: mockReports.filter(r => r.platform === 'instagram').length,
        linkedin: mockReports.filter(r => r.platform === 'linkedin').length,
      },
      spend_by_date: [
        { date: '2025-01-15', amount: 2140.75, conversions: 20 },
        { date: '2025-01-14', amount: 1730.75, conversions: 21 },
        { date: '2025-01-13', amount: 450.30, conversions: 2 },
      ],
      top_performers: [
        {
          account_name: 'Instagram Fashion Account',
          roi: 4.5,
          spend: 750.00,
          conversions: 15,
        },
        {
          account_name: 'Facebook Main Account',
          roi: 3.2,
          spend: 1250.50,
          conversions: 12,
        },
        {
          account_name: 'TikTok Gaming Account',
          roi: 2.8,
          spend: 890.25,
          conversions: 8,
        },
      ],
    };
  }, []);

  // 筛选数据
  const filteredData: DailyReport[] = useMemo(() => {
    return mockReports.filter(report => {
      // 搜索筛选
      const matchesSearch = filters.search_term === '' ||
        report.project_name.toLowerCase().includes(filters.search_term.toLowerCase()) ||
        report.account_name.toLowerCase().includes(filters.search_term.toLowerCase()) ||
        report.submitted_by_name.toLowerCase().includes(filters.search_term.toLowerCase());

      // 状态筛选
      const matchesStatus = filters.status === 'all' || report.status === filters.status;

      // 项目筛选
      const matchesProject = filters.project_id === 'all' || report.project_id === filters.project_id;

      // 账户筛选
      const matchesAccount = filters.account_id === 'all' || report.account_id === filters.account_id;

      // 提交人筛选
      const matchesSubmittedBy = filters.submitted_by === 'all' || report.submitted_by === filters.submitted_by;

      // 日期范围筛选
      const reportDate = new Date(report.report_date);
      const matchesDateRange = (() => {
        switch (filters.date_range) {
          case 'today':
            return reportDate.toDateString() === new Date().toDateString();
          case 'yesterday':
            const yesterday = subDays(new Date(), 1);
            return reportDate.toDateString() === yesterday.toDateString();
          case 'last_7_days':
            const weekStart = subDays(new Date(), 7);
            return reportDate >= weekStart;
          case 'last_30_days':
            const monthStart = subDays(new Date(), 30);
            return reportDate >= monthStart;
          case 'this_month':
            const thisMonthStart = new Date();
            thisMonthStart.setDate(1);
            return reportDate >= thisMonthStart;
          case 'custom':
            if (filters.custom_date_range.start && filters.custom_date_range.end) {
              const startDate = new Date(filters.custom_date_range.start);
              const endDate = new Date(filters.custom_date_range.end);
              return reportDate >= startDate && reportDate <= endDate;
            }
            return true;
          default:
            return true;
        }
      })();

      // 消耗范围筛选
      const matchesSpendRange = (!filters.spend_range.min || report.spend_amount >= filters.spend_range.min) &&
        (!filters.spend_range.max || report.spend_amount <= filters.spend_range.max);

      // ROI范围筛选
      const matchesRoiRange = (!filters.roi_range.min || report.roi >= filters.roi_range.min) &&
        (!filters.roi_range.max || report.roi <= filters.roi_range.max);

      // 附件筛选
      const matchesHasAttachments = filters.has_attachments === null ||
        (filters.has_attachments && report.attachments.length > 0) ||
        (!filters.has_attachments && report.attachments.length === 0);

      // 异常数据筛选
      const matchesHasAnomalies = filters.has_anomalies === null ||
        (filters.has_anomalies && report.is_anomaly) ||
        (!filters.has_anomalies && !report.is_anomaly);

      // 质量评分范围筛选
      const matchesQualityScoreRange = (!filters.quality_score_range.min || (report.quality_score && report.quality_score >= filters.quality_score_range.min)) &&
        (!filters.quality_score_range.max || (report.quality_score && report.quality_score <= filters.quality_score_range.max));

      // 标签筛选
      const matchesTags = filters.tags.length === 0 ||
        (report.tags && filters.tags.some(tag => report.tags?.includes(tag)));

      return matchesSearch && matchesStatus && matchesProject && matchesAccount &&
             matchesSubmittedBy && matchesDateRange && matchesSpendRange &&
             matchesRoiRange && matchesHasAttachments && matchesHasAnomalies &&
             matchesQualityScoreRange && matchesTags;
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
  const handleFiltersChange = (newFilters: IDailyReportFilters) => {
    setFilters(newFilters);
  };

  // 重置筛选条件
  const handleReset = () => {
    setFilters({
      search_term: '',
      status: 'all',
      project_id: 'all',
      account_id: 'all',
      submitted_by: 'all',
      reviewed_by: 'all',
      date_range: 'last_7_days',
      custom_date_range: {
        start: format(subDays(new Date(), 7), 'yyyy-MM-dd'),
        end: format(new Date(), 'yyyy-MM-dd'),
      },
      spend_range: {
        min: undefined,
        max: undefined,
      },
      roi_range: {
        min: undefined,
        max: undefined,
      },
      has_attachments: null,
      has_anomalies: null,
      quality_score_range: {
        min: undefined,
        max: undefined,
      },
      tags: [],
      sort_by: 'submitted_at',
      sort_order: 'desc',
    });
    setSelectedIds([]);
  };

  // 导出数据
  const handleExport = () => {
    console.log('导出日报数据:', filteredData);
    // TODO: 实现导出功能
  };

  // 提交日报
  const handleNewReport = () => {
    console.log('提交新日报');
    // TODO: 实现提交功能
  };

  // 查看详情
  const handleViewDetail = (report: DailyReport) => {
    console.log('查看日报详情:', report);
    // TODO: 实现详情查看功能
  };

  // 编辑日报
  const handleEdit = (report: DailyReport) => {
    console.log('编辑日报:', report);
    // TODO: 实现编辑功能
  };

  // 审核日报
  const handleReview = (report: DailyReport) => {
    console.log('审核日报:', report);
    // TODO: 实现审核功能
  };

  // 下载附件
  const handleDownload = (report: DailyReport) => {
    console.log('下载附件:', report);
    // TODO: 实现下载功能
  };

  // 导出选中项
  const handleExportSelected = (selectedIds: number[]) => {
    console.log('导出选中的日报:', selectedIds);
    // TODO: 实现批量导出功能
  };

  // 批量审核
  const handleBatchReview = (selectedIds: number[], status: ReportStatus, notes?: string) => {
    console.log('批量审核日报:', selectedIds, status, notes);
    // TODO: 实现批量审核功能
  };

  // 选项数据
  const projectOptions = [
    { value: '1', label: '春季推广活动' },
    { value: '2', label: '品牌形象提升' },
    { value: '3', label: '夏季促销活动' },
    { value: '4', label: 'B2B企业服务' },
  ];

  const accountOptions = [
    { value: '1', label: 'Facebook Main Account' },
    { value: '2', label: 'TikTok Gaming Account' },
    { value: '3', label: 'Google Ads Performance' },
    { value: '4', label: 'Instagram Fashion Account' },
    { value: '5', label: 'LinkedIn B2B Account' },
  ];

  const userOptions = [
    { value: '1001', label: '张数据员' },
    { value: '1002', label: '王投手' },
    { value: '1003', label: '李户管' },
    { value: '1004', label: '陈经理' },
    { value: '1005', label: '刘主管' },
  ];

  // 检查是否有待审核报告
  const hasPendingReports = filteredData.some(r => r.status === 'pending');

  return (
    <AppLayout>
      {/* 主内容区域：限宽居中 */}
      <div className="flex-1 bg-background">
        <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
          {/* 页面标题 */}
          <PageHeader
            title="日报管理"
            subtitle="查看和管理所有广告投放日报数据，跟踪投放效果和ROI表现"
            actions={
              <div className="flex gap-2">
                <Button variant="outline" onClick={handleExport}>
                  <Download className="h-4 w-4 mr-2" />
                  导出数据
                </Button>
                <Button onClick={handleNewReport}>
                  <Plus className="h-4 w-4 mr-2" />
                  提交日报
                </Button>
              </div>
            }
          />

          {/* 待审核报告提醒 */}
          {hasPendingReports && (
            <Alert className="border-orange-200 bg-orange-50">
              <Clock className="h-4 w-4 text-orange-600" />
              <AlertDescription className="text-orange-800">
                您有 {filteredData.filter(r => r.status === 'pending').length} 份报告待审核，请及时处理。
              </AlertDescription>
            </Alert>
          )}

          {/* KPI 统计卡片区域 */}
          <section>
            <DailyReportSummaryCards stats={stats} loading={loading} />
          </section>

          {/* 筛选 / 工具栏区域 */}
          <section>
            <DailyReportFilters
              filters={filters}
              onFiltersChange={handleFiltersChange}
              totalCount={filteredData.length}
              onReset={handleReset}
              onExport={handleExport}
              onNewReport={handleNewReport}
              loading={loading}
              projectOptions={projectOptions}
              accountOptions={accountOptions}
              userOptions={userOptions}
            />
          </section>

          {/* 列表区域 */}
          <section>
            <DailyReportTable
              data={filteredData}
              loading={loading}
              onRowClick={handleViewDetail}
              onViewDetail={handleViewDetail}
              onEdit={handleEdit}
              onReview={handleReview}
              onDownload={handleDownload}
              onExportSelected={handleExportSelected}
              onBatchReview={handleBatchReview}
              selectedIds={selectedIds}
              onSelectionChange={setSelectedIds}
            />
          </section>
        </div>
      </div>
    </AppLayout>
  );
}