"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import { format, subDays } from "date-fns";
import { zhCN } from "date-fns/locale";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  CalendarIcon,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  Target,
  Eye,
  BarChart3,
  PieChart as PieChartIcon,
  Download,
  RefreshCw,
} from "lucide-react";
import { toast } from "sonner";

// 类型定义
interface DashboardData {
  summary: {
    total_spend: number;
    total_impressions: number;
    total_clicks: number;
    total_conversions: number;
    total_follows: number;
    avg_cpl: number;
    avg_cpa: number;
    avg_roas: number;
    total_reports: number;
  };
  trends: {
    date: string;
    spend: number;
    impressions: number;
    clicks: number;
    conversions: number;
    follows: number;
  }[];
  top_campaigns: {
    campaign_name: string;
    spend: number;
    conversions: number;
    roas: number;
  }[];
  account_performance: {
    ad_account_name: string;
    spend: number;
    follows: number;
    roas: number;
  }[];
  status_distribution: {
    status: string;
    count: number;
    percentage: number;
  }[];
}

interface DailyReportsDashboardProps {
  dateRange?: {
    start: Date;
    end: Date;
  };
  onDateRangeChange?: (range: { start: Date; end: Date }) => void;
}

const COLORS = ["#8884d8", "#82ca9d", "#ffc658", "#ff7c7c", "#8dd1e1", "#d084d0"];

export function DailyReportsDashboard({
  dateRange = {
    start: subDays(new Date(), 7),
    end: new Date(),
  },
  onDateRangeChange,
}: DailyReportsDashboardProps) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState("7d");
  const [chartType, setChartType] = useState<"line" | "area">("line");
  const [showCalendar, setShowCalendar] = useState(false);

  // 快速时间选项
  const timeRangeOptions = [
    { value: "7d", label: "最近7天" },
    { value: "30d", label: "最近30天" },
    { value: "90d", label: "最近90天" },
    { value: "custom", label: "自定义" },
  ];

  // 获取仪表板数据
  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append("start_date", format(dateRange.start, "yyyy-MM-dd"));
      params.append("end_date", format(dateRange.end, "yyyy-MM-dd"));

      const response = await fetch(`/api/v1/daily-reports/dashboard?${params}`);
      const result = await response.json();

      if (result.success) {
        setData(result.data);
      } else {
        toast.error("获取数据失败");
      }
    } catch (error) {
      console.error("获取仪表板数据错误:", error);
      toast.error("获取数据失败");
    } finally {
      setLoading(false);
    }
  };

  // 刷新数据
  const handleRefresh = () => {
    fetchDashboardData();
  };

  // 处理时间范围变化
  const handleTimeRangeChange = (value: string) => {
    setTimeRange(value);
    if (value === "custom") {
      setShowCalendar(true);
    } else {
      const days = parseInt(value.replace("d", ""));
      const newRange = {
        start: subDays(new Date(), days),
        end: new Date(),
      };
      onDateRangeChange?.(newRange);
    }
  };

  // 导出报表
  const handleExport = async () => {
    try {
      const params = new URLSearchParams();
      params.append("start_date", format(dateRange.start, "yyyy-MM-dd"));
      params.append("end_date", format(dateRange.end, "yyyy-MM-dd"));
      params.append("type", "dashboard");

      const response = await fetch(`/api/v1/daily-reports/export?${params}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `dashboard-${format(new Date(), "yyyyMMdd")}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        toast.success("导出成功");
      }
    } catch (error) {
      toast.error("导出失败");
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [dateRange]);

  if (!data || loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 工具栏 */}
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <Select value={timeRange} onValueChange={handleTimeRangeChange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {timeRangeOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <CalendarIcon className="w-4 h-4" />
            <span>
              {format(dateRange.start, "yyyy年MM月dd日")} -{" "}
              {format(dateRange.end, "yyyy年MM月dd日")}
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Select value={chartType} onValueChange={(value: "line" | "area") => setChartType(value)}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="line">折线图</SelectItem>
              <SelectItem value="area">面积图</SelectItem>
            </SelectContent>
          </Select>

          <Button variant="outline" onClick={handleRefresh}>
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新
          </Button>

          <Button variant="outline" onClick={handleExport}>
            <Download className="w-4 h-4 mr-2" />
            导出
          </Button>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">总消耗</p>
                <p className="text-2xl font-bold">¥{data.summary.total_spend.toLocaleString()}</p>
              </div>
              <DollarSign className="h-8 w-8 text-muted-foreground" />
            </div>
            <div className="mt-2 flex items-center text-sm">
              <Badge variant="secondary" className="bg-blue-100 text-blue-800">
                日均 ¥{(data.summary.total_spend / Math.max(data.trends.length, 1)).toFixed(0)}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">新增粉丝</p>
                <p className="text-2xl font-bold">{data.summary.total_follows.toLocaleString()}</p>
              </div>
              <Users className="h-8 w-8 text-muted-foreground" />
            </div>
            <div className="mt-2 flex items-center text-sm">
              <Badge variant="secondary" className="bg-green-100 text-green-800">
                平均 CPL ¥{data.summary.avg_cpl.toFixed(2)}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">转化数</p>
                <p className="text-2xl font-bold">{data.summary.total_conversions}</p>
              </div>
              <Target className="h-8 w-8 text-muted-foreground" />
            </div>
            <div className="mt-2 flex items-center text-sm">
              <Badge variant="secondary" className="bg-purple-100 text-purple-800">
                平均 CPA ¥{data.summary.avg_cpa.toFixed(2)}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">平均 ROI</p>
                <p className="text-2xl font-bold">{data.summary.avg_roas.toFixed(2)}</p>
              </div>
              <TrendingUp className="h-8 w-8 text-muted-foreground" />
            </div>
            <div className="mt-2 flex items-center text-sm">
              <Badge
                variant="secondary"
                className={data.summary.avg_roas >= 3 ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}
              >
                {data.summary.avg_roas >= 3 ? "表现良好" : "需要优化"}
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 趋势图表 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            投放趋势
          </CardTitle>
          <CardDescription>
            消耗、转化和粉丝增长趋势
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            {chartType === "line" ? (
              <LineChart data={data.trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="spend"
                  stroke="#ef4444"
                  name="消耗金额(¥)"
                  strokeWidth={2}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="conversions"
                  stroke="#10b981"
                  name="转化数"
                  strokeWidth={2}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="follows"
                  stroke="#3b82f6"
                  name="新增粉丝"
                  strokeWidth={2}
                />
              </LineChart>
            ) : (
              <AreaChart data={data.trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="spend"
                  stackId="1"
                  stroke="#ef4444"
                  fill="#fca5a5"
                  name="消耗金额(¥)"
                />
                <Area
                  type="monotone"
                  dataKey="impressions"
                  stackId="2"
                  stroke="#8b5cf6"
                  fill="#c4b5fd"
                  name="展示次数"
                />
              </AreaChart>
            )}
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* 排行和分布 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top 广告系列 */}
        <Card>
          <CardHeader>
            <CardTitle>Top 10 广告系列</CardTitle>
            <CardDescription>按消耗金额排序</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.top_campaigns} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="campaign_name" type="category" width={100} />
                <Tooltip />
                <Bar dataKey="spend" fill="#8884d8" name="消耗金额(¥)" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* 账户表现 */}
        <Card>
          <CardHeader>
            <CardTitle>账户表现对比</CardTitle>
            <CardDescription>各账户的消耗和ROI对比</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.account_performance}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="ad_account_name" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Bar yAxisId="left" dataKey="spend" fill="#82ca9d" name="消耗(¥)" />
                <Bar yAxisId="right" dataKey="roas" fill="#ffc658" name="ROI" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* 状态分布 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <PieChartIcon className="w-5 h-5" />
            日报审核状态分布
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row items-center gap-8">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={data.status_distribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percentage }) => `${name} ${percentage}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {data.status_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>

            <div className="space-y-2">
              {data.status_distribution.map((item, index) => (
                <div key={item.status} className="flex items-center gap-2">
                  <div
                    className="w-4 h-4 rounded"
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  />
                  <span className="text-sm font-medium">{item.status}</span>
                  <span className="text-sm text-gray-600 ml-auto">
                    {item.count} 份 ({item.percentage}%)
                  </span>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 自定义日期选择器 */}
      {showCalendar && (
        <Card className="fixed right-4 top-20 w-96 shadow-lg z-50">
          <CardHeader>
            <CardTitle className="text-lg">选择日期范围</CardTitle>
          </CardHeader>
          <CardContent>
            <Calendar
              mode="range"
              defaultMonth={dateRange.start}
              selected={dateRange}
              onSelect={(range) => {
                if (range?.from && range?.to) {
                  onDateRangeChange?.(range);
                  setShowCalendar(false);
                }
              }}
              locale={zhCN}
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}