'use client';

import { useState } from 'react';
import AppLayout from '@/components/dashboard/AppLayout';
import { PageHeader } from '@/components/layout/page-header';
import { MetricCard } from '@/components/ui/MetricCard';
import { ChartCard } from '@/components/dashboard/ChartCard';
import { ProjectTable, StatusVariant } from '@/components/dashboard/ProjectTable';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { DollarSign, TrendingUp, Users, CreditCard } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

// TypeScript 类型定义
interface KpiData {
  title: string;
  value: string;
  change: number;
  changeType: 'up' | 'down' | 'neutral';
  icon: React.ComponentType<any>;
  description: string;
}

interface ProjectData {
  id: number;
  accountId: string;
  date: string;
  project: string;
  region: string;
  spending: string;
  status: string;
  statusVariant: StatusVariant;
}

interface ChartData {
  month: string;
  totalConsumption: number;
  totalRecharge: number;
}

// Mock 数据 - 实际使用中应该从API获取
const KPI_DATA: KpiData[] = [
  {
    title: '总收入',
    value: '89,935',
    change: 10.2,
    changeType: 'up',
    icon: DollarSign,
    description: 'vs 上周'
  },
  {
    title: '总进粉',
    value: '23,283.5',
    change: 3.1,
    changeType: 'up',
    icon: Users,
    description: 'vs 上周'
  },
  {
    title: '广告总消耗',
    value: '46,827',
    change: -2.56,
    changeType: 'down',
    icon: CreditCard,
    description: 'vs 上周'
  },
  {
    title: '总利润',
    value: '124,854',
    change: 7.2,
    changeType: 'up',
    icon: TrendingUp,
    description: 'vs 上周'
  },
];

const PROJECT_DATA: ProjectData[] = [
  {
    id: 1,
    accountId: '#12594',
    date: 'Oct 15, 2023',
    project: 'Frank Murlo',
    region: '312 S Wilmette Ave',
    spending: '$847.69',
    status: 'New Order',
    statusVariant: 'warning'
  },
  {
    id: 2,
    accountId: '#12595',
    date: 'Oct 14, 2023',
    project: 'Jennifer Lee',
    region: '405 N Michigan Ave',
    spending: '$1,250.00',
    status: 'Processing',
    statusVariant: 'default'
  },
  {
    id: 3,
    accountId: '#12596',
    date: 'Oct 13, 2023',
    project: 'David Chen',
    region: '500 W Madison St',
    spending: '$595.43',
    status: 'Completed',
    statusVariant: 'success'
  },
];

const CHART_DATA: ChartData[] = [
  { month: '1月', totalConsumption: 42000, totalRecharge: 38000 },
  { month: '2月', totalConsumption: 45000, totalRecharge: 42000 },
  { month: '3月', totalConsumption: 48000, totalRecharge: 45000 },
  { month: '4月', totalConsumption: 52000, totalRecharge: 48000 },
  { month: '5月', totalConsumption: 49000, totalRecharge: 51000 },
  { month: '6月', totalConsumption: 55000, totalRecharge: 49000 },
  { month: '7月', totalConsumption: 58000, totalRecharge: 53000 },
];

/**
 * Dashboard主页面组件
 *
 * 采用限宽居中布局，响应式设计
 * 遵循设计系统规范，支持加载状态
 */
export default function DashboardPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [timeRange, setTimeRange] = useState('monthly');

  // 模拟加载状态切换（实际使用中根据数据加载状态设置）
  // const isLoading = true;

  return (
    <AppLayout>
      {/* 主内容区域：限宽居中 */}
      <div className="flex-1 bg-background">
        <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
          <PageHeader
            title="工作台概览"
            subtitle="实时监控关键指标，快速处理异常和待办任务"
          />

          {/* KPI 指标卡片区域 */}
          <section className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
            {isLoading ? (
              // Loading 状态下的骨架屏
              [...Array(4)].map((_, index) => (
                <div key={index} className="bg-card border border-border rounded-xl p-4">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Skeleton className="h-4 w-20" />
                      <Skeleton className="h-5 w-5" />
                    </div>
                    <Skeleton className="h-8 w-24" />
                    <Skeleton className="h-4 w-16" />
                  </div>
                </div>
              ))
            ) : (
              // 正常数据展示
              KPI_DATA.map((kpi, index) => (
                <MetricCard key={index} {...kpi} size="md" />
              ))
            )}
          </section>

          {/* 图表区域：投放消耗趋势 + 项目占比 */}
          <section className="grid gap-6 grid-cols-1 xl:grid-cols-[2fr,1fr]">
            {/* 投放消耗趋势图 */}
            <ChartCard
              title="投放消耗趋势"
              loading={isLoading}
              actions={
                <Select value={timeRange} onValueChange={setTimeRange}>
                  <SelectTrigger className="w-[120px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="monthly">月度</SelectItem>
                    <SelectItem value="weekly">周度</SelectItem>
                    <SelectItem value="daily">日度</SelectItem>
                  </SelectContent>
                </Select>
              }
            >
              {/* 图表控制面板 */}
              <div className="mb-6 flex items-center justify-between">
                <div className="flex gap-6">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-primary" />
                    <span className="text-sm text-muted-foreground">总消耗</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-destructive" />
                    <span className="text-sm text-muted-foreground">总充值</span>
                  </div>
                </div>
              </div>

              {/* 图表容器：增加高度提升可读性 */}
              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={CHART_DATA}
                    margin={{
                      top: 10,
                      right: 30,
                      left: 20,
                      bottom: 10,
                    }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="hsl(var(--border))"
                      className="opacity-30"
                    />
                    <XAxis
                      dataKey="month"
                      tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                      axisLine={{ stroke: 'hsl(var(--border))' }}
                    />
                    <YAxis
                      tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                      axisLine={{ stroke: 'hsl(var(--border))' }}
                      tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      formatter={(value: number) => [`¥${value.toLocaleString()}`, '']}
                      contentStyle={{
                        backgroundColor: 'hsl(var(--background))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '8px',
                        fontSize: '12px'
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="totalConsumption"
                      stroke="hsl(var(--primary))"
                      strokeWidth={3}
                      dot={{ fill: 'hsl(var(--primary))', r: 5 }}
                      activeDot={{ r: 7, stroke: 'hsl(var(--primary))', strokeWidth: 2 }}
                      name="总消耗"
                    />
                    <Line
                      type="monotone"
                      dataKey="totalRecharge"
                      stroke="hsl(var(--destructive))"
                      strokeWidth={3}
                      dot={{ fill: 'hsl(var(--destructive))', r: 5 }}
                      activeDot={{ r: 7, stroke: 'hsl(var(--destructive))', strokeWidth: 2 }}
                      name="总充值"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>

            {/* 项目占比环形图 */}
            <ChartCard title="项目占比" loading={isLoading}>
              <div className="flex h-full flex-col">
                <div className="flex flex-1 items-center justify-center">
                  <div className="relative flex h-40 w-40 items-center justify-center">
                    {/* 简化版环形图 */}
                    <svg className="h-full w-full" viewBox="0 0 100 100">
                      <circle
                        cx="50"
                        cy="50"
                        r="40"
                        fill="none"
                        stroke="hsl(var(--primary))"
                        strokeWidth="12"
                        strokeDasharray="62.8 251.2"
                      />
                      <circle
                        cx="50"
                        cy="50"
                        r="40"
                        fill="none"
                        stroke="hsl(var(--chart-2))"
                        strokeWidth="12"
                        strokeDasharray="62.8 251.2"
                        strokeDashoffset="-62.8"
                        transform="rotate(-90 50 50)"
                      />
                      <circle
                        cx="50"
                        cy="50"
                        r="40"
                        fill="none"
                        stroke="hsl(var(--chart-3))"
                        strokeWidth="12"
                        strokeDasharray="62.8 251.2"
                        strokeDashoffset="-125.6"
                        transform="rotate(-90 50 50)"
                      />
                    </svg>
                    <div className="absolute flex flex-col items-center">
                      <span className="text-xl font-semibold text-foreground">$452</span>
                      <span className="text-xs text-muted-foreground">总消耗</span>
                    </div>
                  </div>
                </div>

                {/* 图例 */}
                <div className="flex flex-wrap justify-center gap-4 pt-4">
                  {[
                    { color: 'bg-primary', label: '线下推广' },
                    { color: 'bg-chart-2', label: '线上投放' },
                    { color: 'bg-chart-3', label: '社媒营销' },
                  ].map((item) => (
                    <div key={item.label} className="flex items-center gap-2">
                      <span className={`h-2 w-2 rounded-full ${item.color}`} />
                      <span className="text-sm text-muted-foreground">{item.label}</span>
                    </div>
                  ))}
                </div>
              </div>
            </ChartCard>
          </section>

          {/* 项目列表表格 */}
          <section>
            <ProjectTable
              data={PROJECT_DATA}
              loading={isLoading}
            />
          </section>
        </div>
      </div>
    </AppLayout>
  );
}