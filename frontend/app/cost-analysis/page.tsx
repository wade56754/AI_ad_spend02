'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
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
  DollarSign,
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart,
  Calendar,
  Filter,
  Download,
  RefreshCw,
  Eye,
  AlertTriangle,
  Users,
  Target,
  Activity,
  FileText,
} from 'lucide-react';
import { PageHeader } from '@/components/layout/page-header';
import { MetricCard } from '@/components/ui/MetricCard';
import { cn } from '@/lib/utils';
import { format, subDays, startOfMonth, endOfMonth } from 'date-fns';

// 成本分析数据类型
interface CostData {
  date: string;
  total_cost: number;
  active_accounts: number;
  avg_cost_per_account: number;
  facebook_cost: number;
  google_cost: number;
  tiktok_cost: number;
  conversions: number;
  cpa: number;
  roi: number;
}

interface ProjectCost {
  id: number;
  project_name: string;
  client_name: string;
  total_cost: number;
  budget: number;
  budget_usage: number;
  roi: number;
  conversions: number;
  cpa: number;
  status: 'active' | 'paused' | 'completed';
  start_date: string;
  end_date: string;
}

interface AccountCost {
  id: number;
  account_name: string;
  platform: string;
  project_name: string;
  total_cost: number;
  daily_avg_cost: number;
  conversions: number;
  cpa: number;
  roi: number;
  status: 'active' | 'inactive' | 'suspended';
  last_active: string;
}

// 模拟数据
const mockCostData: CostData[] = [
  {
    date: '2024-11-07',
    total_cost: 12500,
    active_accounts: 45,
    avg_cost_per_account: 278,
    facebook_cost: 5500,
    google_cost: 4200,
    tiktok_cost: 2800,
    conversions: 125,
    cpa: 100,
    roi: 3.2,
  },
  {
    date: '2024-11-08',
    total_cost: 13200,
    active_accounts: 47,
    avg_cost_per_account: 281,
    facebook_cost: 5800,
    google_cost: 4500,
    tiktok_cost: 2900,
    conversions: 138,
    cpa: 96,
    roi: 3.4,
  },
  {
    date: '2024-11-09',
    total_cost: 12800,
    active_accounts: 46,
    avg_cost_per_account: 278,
    facebook_cost: 5600,
    google_cost: 4300,
    tiktok_cost: 2900,
    conversions: 142,
    cpa: 90,
    roi: 3.6,
  },
  {
    date: '2024-11-10',
    total_cost: 14100,
    active_accounts: 48,
    avg_cost_per_account: 294,
    facebook_cost: 6200,
    google_cost: 4800,
    tiktok_cost: 3100,
    conversions: 155,
    cpa: 91,
    roi: 3.5,
  },
  {
    date: '2024-11-11',
    total_cost: 13900,
    active_accounts: 47,
    avg_cost_per_account: 296,
    facebook_cost: 6000,
    google_cost: 4700,
    tiktok_cost: 3200,
    conversions: 148,
    cpa: 94,
    roi: 3.3,
  },
  {
    date: '2024-11-12',
    total_cost: 14500,
    active_accounts: 49,
    avg_cost_per_account: 296,
    facebook_cost: 6300,
    google_cost: 5000,
    tiktok_cost: 3200,
    conversions: 162,
    cpa: 90,
    roi: 3.7,
  },
  {
    date: '2024-11-13',
    total_cost: 14200,
    active_accounts: 48,
    avg_cost_per_account: 296,
    facebook_cost: 6100,
    google_cost: 4900,
    tiktok_cost: 3200,
    conversions: 158,
    cpa: 90,
    roi: 3.6,
  },
];

const mockProjectCosts: ProjectCost[] = [
  {
    id: 1,
    project_name: 'Q4电商推广',
    client_name: 'ABC公司',
    total_cost: 45000,
    budget: 50000,
    budget_usage: 90,
    roi: 3.8,
    conversions: 450,
    cpa: 100,
    status: 'active',
    start_date: '2024-11-01',
    end_date: '2024-11-30',
  },
  {
    id: 2,
    project_name: '品牌曝光活动',
    client_name: 'XYZ科技',
    total_cost: 32000,
    budget: 40000,
    budget_usage: 80,
    roi: 2.9,
    conversions: 280,
    cpa: 114,
    status: 'active',
    start_date: '2024-11-05',
    end_date: '2024-11-25',
  },
  {
    id: 3,
    project_name: 'APP推广计划',
    client_name: 'DEF游戏',
    total_cost: 28000,
    budget: 35000,
    budget_usage: 80,
    roi: 4.2,
    conversions: 350,
    cpa: 80,
    status: 'active',
    start_date: '2024-11-10',
    end_date: '2024-12-10',
  },
];

const mockAccountCosts: AccountCost[] = [
  {
    id: 1,
    account_name: 'Facebook Main Account',
    platform: 'facebook',
    project_name: 'Q4电商推广',
    total_cost: 12500,
    daily_avg_cost: 417,
    conversions: 125,
    cpa: 100,
    roi: 3.5,
    status: 'active',
    last_active: '2024-11-13',
  },
  {
    id: 2,
    account_name: 'Google Performance Max',
    platform: 'google',
    project_name: '品牌曝光活动',
    total_cost: 8900,
    daily_avg_cost: 297,
    conversions: 89,
    cpa: 100,
    roi: 3.2,
    status: 'active',
    last_active: '2024-11-13',
  },
  {
    id: 3,
    account_name: 'TikTok Gaming',
    platform: 'tiktok',
    project_name: 'APP推广计划',
    total_cost: 6800,
    daily_avg_cost: 227,
    conversions: 85,
    cpa: 80,
    roi: 4.1,
    status: 'active',
    last_active: '2024-11-13',
  },
];

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

export default function CostAnalysisPage() {
  const [costData, setCostData] = useState(mockCostData);
  const [projectCosts, setProjectCosts] = useState(mockProjectCosts);
  const [accountCosts, setAccountCosts] = useState(mockAccountCosts);
  const [loading, setLoading] = useState(false);
  const [timeRange, setTimeRange] = useState('7d');
  const [selectedPlatform, setSelectedPlatform] = useState('all');

  // 计算汇总数据
  const summaryData = {
    totalCost: costData.reduce((sum, item) => sum + item.total_cost, 0),
    totalConversions: costData.reduce((sum, item) => sum + item.conversions, 0),
    avgCPA: costData.reduce((sum, item) => sum + item.cpa, 0) / costData.length,
    avgROI: costData.reduce((sum, item) => sum + item.roi, 0) / costData.length,
    activeAccounts: costData[costData.length - 1]?.active_accounts || 0,
    totalBudget: projectCosts.reduce((sum, item) => sum + item.budget, 0),
    budgetUsage: projectCosts.reduce((sum, item) => sum + item.budget_usage, 0) / projectCosts.length,
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      active: { label: '活跃', color: 'success' as const },
      paused: { label: '暂停', color: 'warning' as const },
      completed: { label: '已完成', color: 'default' as const },
      inactive: { label: '不活跃', color: 'secondary' as const },
      suspended: { label: '已停用', color: 'destructive' as const },
    };

    const config = statusConfig[status as keyof typeof statusConfig];
    return <Badge variant={config.color}>{config.label}</Badge>;
  };

  const getPlatformData = () => {
    const filteredData = selectedPlatform === 'all' ? costData : costData;

    return [
      {
        name: 'Facebook',
        value: filteredData.reduce((sum, item) => sum + item.facebook_cost, 0),
        color: '#1877F2',
      },
      {
        name: 'Google',
        value: filteredData.reduce((sum, item) => sum + item.google_cost, 0),
        color: '#4285F4',
      },
      {
        name: 'TikTok',
        value: filteredData.reduce((sum, item) => sum + item.tiktok_cost, 0),
        color: '#FF0050',
      },
    ];
  };

  const handleExportData = () => {
    // TODO: 实现数据导出功能
    console.log('导出成本分析数据');
  };

  const handleRefreshData = () => {
    setLoading(true);
    // 模拟数据刷新
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <PageHeader
        title="成本分析"
        subtitle="全面分析广告投放成本、ROI和预算使用情况，优化投放策略"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleRefreshData} disabled={loading}>
              <RefreshCw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />
              刷新数据
            </Button>
            <Button onClick={handleExportData}>
              <Download className="h-4 w-4 mr-2" />
              导出报告
            </Button>
          </div>
        }
      />

      {/* 筛选栏 */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-gray-500" />
              <span className="text-sm font-medium">时间范围:</span>
              <Select value={timeRange} onValueChange={setTimeRange}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="7d">最近7天</SelectItem>
                  <SelectItem value="30d">最近30天</SelectItem>
                  <SelectItem value="90d">最近90天</SelectItem>
                  <SelectItem value="custom">自定义</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-500" />
              <span className="text-sm font-medium">平台:</span>
              <Select value={selectedPlatform} onValueChange={setSelectedPlatform}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有平台</SelectItem>
                  <SelectItem value="facebook">Facebook</SelectItem>
                  <SelectItem value="google">Google</SelectItem>
                  <SelectItem value="tiktok">TikTok</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 核心指标卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="总成本"
          value={`￥${summaryData.totalCost.toLocaleString()}`}
          change={12.5}
          changeType="up"
          description="选定周期内总消耗"
          color="primary"
          icon={DollarSign}
          size="sm"
        />
        <MetricCard
          title="总转化"
          value={summaryData.totalConversions}
          change={8.2}
          changeType="up"
          description="选定周期内总转化数"
          color="success"
          icon={Target}
          size="sm"
        />
        <MetricCard
          title="平均CPA"
          value={`￥${summaryData.avgCPA.toFixed(2)}`}
          change={-5.3}
          changeType="down"
          description="平均获客成本"
          color="info"
          icon={TrendingDown}
          size="sm"
        />
        <MetricCard
          title="平均ROI"
          value={summaryData.avgROI.toFixed(2)}
          change={0.8}
          changeType="up"
          description="平均投资回报率"
          color="success"
          icon={TrendingUp}
          size="sm"
        />
        <MetricCard
          title="预算使用率"
          value={`${summaryData.budgetUsage.toFixed(1)}%`}
          change={2.1}
          changeType="up"
          description="项目预算平均使用率"
          color="warning"
          icon={BarChart3}
          size="sm"
        />
      </div>

      {/* 图表分析区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 成本趋势图 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              成本趋势分析
            </CardTitle>
            <CardDescription>
              每日成本变化趋势和平台分布
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={costData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tickFormatter={(date) => format(new Date(date), 'MM/dd')}
                />
                <YAxis />
                <Tooltip
                  labelFormatter={(date) => format(new Date(date), 'yyyy-MM-dd')}
                  formatter={(value) => [`￥${value}`, '']}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="facebook_cost"
                  stackId="1"
                  stroke="#1877F2"
                  fill="#1877F2"
                  name="Facebook"
                />
                <Area
                  type="monotone"
                  dataKey="google_cost"
                  stackId="1"
                  stroke="#4285F4"
                  fill="#4285F4"
                  name="Google"
                />
                <Area
                  type="monotone"
                  dataKey="tiktok_cost"
                  stackId="1"
                  stroke="#FF0050"
                  fill="#FF0050"
                  name="TikTok"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* 平台成本分布 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="h-5 w-5" />
              平台成本分布
            </CardTitle>
            <CardDescription>
              各平台成本占比分析
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <RechartsPieChart>
                <Pie
                  data={getPlatformData()}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {getPlatformData().map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [`￥${value}`, '成本']} />
              </RechartsPieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* ROI和CPA趋势 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            ROI与CPA趋势
          </CardTitle>
          <CardDescription>
            投资回报率和获客成本的变化趋势
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={costData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(date) => format(new Date(date), 'MM/dd')}
              />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip
                labelFormatter={(date) => format(new Date(date), 'yyyy-MM-dd')}
              />
              <Legend />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="roi"
                stroke="#10b981"
                strokeWidth={2}
                name="ROI"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="cpa"
                stroke="#f59e0b"
                strokeWidth={2}
                name="CPA"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* 项目成本分析 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            项目成本分析
          </CardTitle>
          <CardDescription>
            各项目的成本使用情况和ROI表现
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>项目名称</TableHead>
                  <TableHead>客户</TableHead>
                  <TableHead>总成本</TableHead>
                  <TableHead>预算使用率</TableHead>
                  <TableHead>ROI</TableHead>
                  <TableHead>CPA</TableHead>
                  <TableHead>转化数</TableHead>
                  <TableHead>状态</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {projectCosts.map((project) => (
                  <TableRow key={project.id}>
                    <TableCell className="font-medium">{project.project_name}</TableCell>
                    <TableCell>{project.client_name}</TableCell>
                    <TableCell>￥{project.total_cost.toLocaleString()}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div
                            className={cn(
                              "h-2 rounded-full",
                              project.budget_usage >= 90 ? "bg-red-500" :
                              project.budget_usage >= 75 ? "bg-yellow-500" : "bg-green-500"
                            )}
                            style={{ width: `${Math.min(project.budget_usage, 100)}%` }}
                          />
                        </div>
                        <span className="text-sm">{project.budget_usage}%</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className={cn(
                        "font-medium",
                        project.roi >= 3 ? "text-green-600" :
                        project.roi >= 2 ? "text-yellow-600" : "text-red-600"
                      )}>
                        {project.roi.toFixed(2)}
                      </span>
                    </TableCell>
                    <TableCell>￥{project.cpa}</TableCell>
                    <TableCell>{project.conversions}</TableCell>
                    <TableCell>{getStatusBadge(project.status)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* 账户成本详情 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            账户成本详情
          </CardTitle>
          <CardDescription>
            各广告账户的成本表现和关键指标
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>账户名称</TableHead>
                  <TableHead>平台</TableHead>
                  <TableHead>所属项目</TableHead>
                  <TableHead>总成本</TableHead>
                  <TableHead>日均成本</TableHead>
                  <TableHead>CPA</TableHead>
                  <TableHead>ROI</TableHead>
                  <TableHead>转化数</TableHead>
                  <TableHead>状态</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {accountCosts.map((account) => (
                  <TableRow key={account.id}>
                    <TableCell className="font-medium">{account.account_name}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="capitalize">
                        {account.platform}
                      </Badge>
                    </TableCell>
                    <TableCell>{account.project_name}</TableCell>
                    <TableCell>￥{account.total_cost.toLocaleString()}</TableCell>
                    <TableCell>￥{account.daily_avg_cost}</TableCell>
                    <TableCell>￥{account.cpa}</TableCell>
                    <TableCell>
                      <span className={cn(
                        "font-medium",
                        account.roi >= 3 ? "text-green-600" :
                        account.roi >= 2 ? "text-yellow-600" : "text-red-600"
                      )}>
                        {account.roi.toFixed(2)}
                      </span>
                    </TableCell>
                    <TableCell>{account.conversions}</TableCell>
                    <TableCell>{getStatusBadge(account.status)}</TableCell>
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