'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';
import {
  FileText,
  Download,
  Calendar,
  Filter,
  RefreshCw,
  Eye,
  Plus,
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart,
  Target,
  DollarSign,
  Users,
  Activity,
  Clock,
  CheckCircle,
  AlertTriangle,
} from 'lucide-react';
import { PageHeader } from '@/components/layout/page-header';
import { MetricCard } from '@/components/ui/MetricCard';
import { cn } from '@/lib/utils';
import { format, subDays, startOfMonth, endOfMonth } from 'date-fns';

// 报表类型定义
interface Report {
  id: number;
  report_name: string;
  report_type: 'daily' | 'weekly' | 'monthly' | 'custom' | 'performance' | 'financial';
  description: string;
  status: 'generating' | 'completed' | 'failed' | 'scheduled';
  created_by: string;
  created_at: string;
  generated_at?: string;
  file_size?: number;
  download_url?: string;
  parameters: {
    date_range: string;
    projects: string[];
    platforms: string[];
    metrics: string[];
  };
  schedule?: {
    frequency: 'daily' | 'weekly' | 'monthly';
    time: string;
    recipients: string[];
  };
}

interface ReportTemplate {
  id: number;
  name: string;
  description: string;
  category: string;
  icon: React.ReactNode;
  metrics: string[];
  dimensions: string[];
  charts: string[];
  sample_image?: string;
}

// 模拟数据
const mockReports: Report[] = [
  {
    id: 1,
    report_name: '2024年11月Facebook投放报告',
    report_type: 'monthly',
    description: 'Facebook平台11月广告投放表现分析',
    status: 'completed',
    created_by: '数据部-张三',
    created_at: '2024-11-13T09:00:00Z',
    generated_at: '2024-11-13T09:30:00Z',
    file_size: 2048000,
    download_url: '/reports/facebook_nov_2024.pdf',
    parameters: {
      date_range: '2024-11-01 to 2024-11-30',
      projects: ['Q4电商推广', '品牌曝光活动'],
      platforms: ['facebook'],
      metrics: ['spend', 'impressions', 'conversions', 'roi'],
    },
  },
  {
    id: 2,
    report_name: '周度ROI分析报告',
    report_type: 'weekly',
    description: '上周各项目ROI表现对比分析',
    status: 'generating',
    created_by: '财务部-李四',
    created_at: '2024-11-13T10:15:00Z',
    parameters: {
      date_range: '2024-11-07 to 2024-11-13',
      projects: [],
      platforms: ['facebook', 'google', 'tiktok'],
      metrics: ['spend', 'revenue', 'roi', 'cpa'],
    },
  },
  {
    id: 3,
    report_name: '实时投放监控报表',
    report_type: 'daily',
    description: '今日实时投放数据监控',
    status: 'scheduled',
    created_by: '运营部-王五',
    created_at: '2024-11-13T08:00:00Z',
    generated_at: '2024-11-13T08:05:00Z',
    file_size: 512000,
    download_url: '/reports/daily_monitoring_20241113.pdf',
    parameters: {
      date_range: '2024-11-13',
      projects: [],
      platforms: ['facebook', 'google', 'tiktok'],
      metrics: ['spend', 'impressions', 'clicks', 'conversions'],
    },
    schedule: {
      frequency: 'daily',
      time: '08:00',
      recipients: ['manager@company.com', 'team@company.com'],
    },
  },
  {
    id: 4,
    report_name: 'Q4财务汇总报告',
    report_type: 'financial',
    description: 'Q4季度财务数据汇总和分析',
    status: 'failed',
    created_by: '财务部-赵六',
    created_at: '2024-11-12T16:30:00Z',
    parameters: {
      date_range: '2024-10-01 to 2024-12-31',
      projects: [],
      platforms: ['facebook', 'google', 'tiktok'],
      metrics: ['spend', 'budget', 'roi', 'profit'],
    },
  },
];

const mockTemplates: ReportTemplate[] = [
  {
    id: 1,
    name: '投放表现报告',
    description: '全面的广告投放效果分析，包含关键指标和趋势',
    category: '效果分析',
    icon: <TrendingUp className="h-6 w-6" />,
    metrics: ['花费', '曝光量', '点击量', '转化数', 'ROI', 'CPA'],
    dimensions: ['时间', '项目', '平台', '账户', '广告系列'],
    charts: ['趋势图', '对比图', '分布图'],
  },
  {
    id: 2,
    name: '财务分析报告',
    description: '详细的财务数据和成本分析',
    category: '财务报表',
    icon: <DollarSign className="h-6 w-6" />,
    metrics: ['总花费', '预算使用率', 'ROI', '利润率', '成本分析'],
    dimensions: ['项目', '时间', '平台', '客户'],
    charts: ['成本趋势', '预算对比', 'ROI分析'],
  },
  {
    id: 3,
    name: '项目月报',
    description: '月度项目执行情况和效果总结',
    category: '项目管理',
    icon: <FileText className="h-6 w-6" />,
    metrics: ['项目进展', '目标完成率', '花费效率', 'ROI'],
    dimensions: ['项目', '客户', '时间'],
    charts: ['进度对比', '效果趋势'],
  },
  {
    id: 4,
    name: '实时监控报表',
    description: '实时投放数据监控和异常预警',
    category: '实时监控',
    icon: <Activity className="h-6 w-6" />,
    metrics: ['实时花费', '在线转化', '异常检测'],
    dimensions: ['时间', '平台', '账户'],
    charts: ['实时曲线', '状态指示器'],
  },
  {
    id: 5,
    name: '平台对比分析',
    description: '不同平台投放效果对比分析',
    category: '效果分析',
    icon: <BarChart3 className="h-6 w-6" />,
    metrics: ['平台花费', '转化效率', 'ROI对比'],
    dimensions: ['平台', '时间', '项目类型'],
    charts: ['对比柱状图', '占比分析'],
  },
  {
    id: 6,
    name: '受众分析报告',
    description: '目标受众行为和转化分析',
    category: '受众洞察',
    icon: <Users className="h-6 w-6" />,
    metrics: ['受众规模', '转化率', '获客成本', '用户价值'],
    dimensions: ['受众群体', '人口统计', '兴趣标签'],
    charts: ['受众分布', '转化漏斗'],
  },
];

// 图表数据
const performanceData = [
  { name: '11/07', spend: 12500, conversions: 125, roi: 3.2 },
  { name: '11/08', spend: 13200, conversions: 138, roi: 3.4 },
  { name: '11/09', spend: 12800, conversions: 142, roi: 3.6 },
  { name: '11/10', spend: 14100, conversions: 155, roi: 3.5 },
  { name: '11/11', spend: 13900, conversions: 148, roi: 3.3 },
  { name: '11/12', spend: 14500, conversions: 162, roi: 3.7 },
  { name: '11/13', spend: 14200, conversions: 158, roi: 3.6 },
];

const platformDistribution = [
  { name: 'Facebook', value: 45, fill: '#1877F2' },
  { name: 'Google', value: 30, fill: '#4285F4' },
  { name: 'TikTok', value: 25, fill: '#FF0050' },
];

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

export default function ReportsPage() {
  const [reports, setReports] = useState(mockReports);
  const [templates, setTemplates] = useState(mockTemplates);
  const [loading, setLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  // 统计数据
  const stats = {
    total_reports: reports.length,
    completed_reports: reports.filter(r => r.status === 'completed').length,
    generating_reports: reports.filter(r => r.status === 'generating').length,
    scheduled_reports: reports.filter(r => r.status === 'scheduled').length,
    failed_reports: reports.filter(r => r.status === 'failed').length,
    total_size: reports.reduce((sum, r) => sum + (r.file_size || 0), 0),
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      generating: { label: '生成中', color: 'info' as const, icon: RefreshCw },
      completed: { label: '已完成', color: 'success' as const, icon: CheckCircle },
      failed: { label: '失败', color: 'destructive' as const, icon: AlertTriangle },
      scheduled: { label: '已计划', color: 'warning' as const, icon: Clock },
    };

    const config = statusConfig[status as keyof typeof statusConfig];
    const Icon = config.icon;

    return (
      <Badge variant={config.color} className="flex items-center gap-1">
        <Icon className="h-3 w-3" />
        {config.label}
      </Badge>
    );
  };

  const getReportTypeLabel = (type: string) => {
    const typeLabels = {
      daily: '日报',
      weekly: '周报',
      monthly: '月报',
      custom: '自定义',
      performance: '效果报告',
      financial: '财务报告',
    };
    return typeLabels[type as keyof typeof typeLabels] || type;
  };

  const filteredTemplates = templates.filter(template => {
    const matchesCategory = selectedCategory === 'all' || template.category === selectedCategory;
    const matchesSearch = searchTerm === '' ||
      template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      template.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const filteredReports = reports.filter(report => {
    const matchesStatus = selectedStatus === 'all' || report.status === selectedStatus;
    const matchesSearch = searchTerm === '' ||
      report.report_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const handleDownloadReport = (report: Report) => {
    if (report.download_url) {
      const link = document.createElement('a');
      link.href = report.download_url;
      link.download = `${report.report_name}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const handleCreateReport = (template: ReportTemplate) => {
    // TODO: 打开报表创建对话框
    console.log('创建报表:', template.name);
    setShowCreateDialog(true);
  };

  const handleRefreshData = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <PageHeader
        title="报表中心"
        subtitle="生成和管理各类广告投放分析报表，支持自定义和定时报表"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleRefreshData} disabled={loading}>
              <RefreshCw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />
              刷新数据
            </Button>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              新建报表
            </Button>
          </div>
        }
      />

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="总报表数"
          value={stats.total_reports}
          description="已创建的报表总数"
          color="primary"
          icon={FileText}
          size="sm"
        />
        <MetricCard
          title="已完成"
          value={stats.completed_reports}
          description="可下载的报表"
          color="success"
          icon={CheckCircle}
          size="sm"
        />
        <MetricCard
          title="生成中"
          value={stats.generating_reports}
          description="正在生成的报表"
          color="info"
          icon={RefreshCw}
          size="sm"
        />
        <MetricCard
          title="已计划"
          value={stats.scheduled_reports}
          description="定时自动生成"
          color="warning"
          icon={Clock}
          size="sm"
        />
        <MetricCard
          title="存储大小"
          value={`${(stats.total_size / 1024 / 1024).toFixed(1)}MB`}
          description="报表文件总大小"
          color="default"
          icon={Download}
          size="sm"
        />
      </div>

      {/* 报表模板 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            报表模板
          </CardTitle>
          <CardDescription>
            选择预定义模板快速创建标准化报表
          </CardDescription>

          {/* 筛选栏 */}
          <div className="flex flex-wrap gap-4 mt-4">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">分类:</span>
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部分类</SelectItem>
                  <SelectItem value="效果分析">效果分析</SelectItem>
                  <SelectItem value="财务报表">财务报表</SelectItem>
                  <SelectItem value="项目管理">项目管理</SelectItem>
                  <SelectItem value="实时监控">实时监控</SelectItem>
                  <SelectItem value="受众洞察">受众洞察</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1">
              <Input
                placeholder="搜索报表模板..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="max-w-xs"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredTemplates.map((template) => (
              <Card key={template.id} className="hover:shadow-md transition-shadow cursor-pointer">
                <CardContent className="p-4">
                  <div className="space-y-3">
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
                        {template.icon}
                      </div>
                      <div className="flex-1">
                        <h3 className="font-medium">{template.name}</h3>
                        <Badge variant="outline" className="text-xs mt-1">
                          {template.category}
                        </Badge>
                      </div>
                    </div>

                    <p className="text-sm text-gray-600">{template.description}</p>

                    <div className="space-y-2">
                      <div className="text-xs text-gray-500">
                        <strong>关键指标:</strong> {template.metrics.slice(0, 3).join(', ')}
                        {template.metrics.length > 3 && '...'}
                      </div>
                      <div className="text-xs text-gray-500">
                        <strong>图表类型:</strong> {template.charts.join(', ')}
                      </div>
                    </div>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleCreateReport(template)}
                      className="w-full"
                    >
                      使用模板
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 报表概览图表 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 投放效果趋势 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              近7天投放效果趋势
            </CardTitle>
            <CardDescription>
              花费、转化和ROI的每日变化趋势
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="spend"
                  stroke="#3b82f6"
                  name="花费"
                  strokeWidth={2}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="roi"
                  stroke="#10b981"
                  name="ROI"
                  strokeWidth={2}
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="conversions"
                  stroke="#f59e0b"
                  name="转化数"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* 平台花费分布 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="h-5 w-5" />
              平台花费分布
            </CardTitle>
            <CardDescription>
              各平台花费占比分析
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <RechartsPieChart>
                <Pie
                  data={platformDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {platformDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [`${value}%`, '占比']} />
              </RechartsPieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* 报表历史 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            报表历史
          </CardTitle>
          <CardDescription>
            查看已生成的报表历史记录和下载
          </CardDescription>

          {/* 筛选栏 */}
          <div className="flex flex-wrap gap-4 mt-4">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">状态:</span>
              <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部状态</SelectItem>
                  <SelectItem value="completed">已完成</SelectItem>
                  <SelectItem value="generating">生成中</SelectItem>
                  <SelectItem value="scheduled">已计划</SelectItem>
                  <SelectItem value="failed">失败</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>报表名称</TableHead>
                  <TableHead>类型</TableHead>
                  <TableHead>描述</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>创建人</TableHead>
                  <TableHead>创建时间</TableHead>
                  <TableHead>文件大小</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredReports.map((report) => (
                  <TableRow key={report.id}>
                    <TableCell className="font-medium">{report.report_name}</TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {getReportTypeLabel(report.report_type)}
                      </Badge>
                    </TableCell>
                    <TableCell className="max-w-xs">
                      <div className="truncate" title={report.description}>
                        {report.description}
                      </div>
                    </TableCell>
                    <TableCell>{getStatusBadge(report.status)}</TableCell>
                    <TableCell className="text-sm">{report.created_by}</TableCell>
                    <TableCell className="text-sm">
                      {format(new Date(report.created_at), 'MM/dd HH:mm')}
                    </TableCell>
                    <TableCell className="text-sm">
                      {report.file_size
                        ? `${(report.file_size / 1024 / 1024).toFixed(1)}MB`
                        : '-'
                      }
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {report.status === 'completed' && report.download_url && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDownloadReport(report)}
                          >
                            <Download className="h-4 w-4 mr-1" />
                            下载
                          </Button>
                        )}
                        <Button variant="outline" size="sm">
                          <Eye className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}