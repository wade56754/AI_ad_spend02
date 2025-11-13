"use client";

import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DailyReportsDashboard } from "@/components/daily-reports/daily-reports-dashboard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { format, subDays } from "date-fns";
import {
  BarChart3,
  TrendingUp,
  Target,
  Users,
  DollarSign,
  Eye,
  Download,
  Calendar,
  Filter,
} from "lucide-react";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

// 模拟数据 - 实际应该从API获取
const performanceData = [
  { date: "2024-01-01", spend: 500, follows: 100, cpl: 5, roas: 3.2 },
  { date: "2024-01-02", spend: 750, follows: 150, cpl: 5, roas: 3.5 },
  { date: "2024-01-03", spend: 600, follows: 120, cpl: 5, roas: 3.1 },
  { date: "2024-01-04", spend: 800, follows: 160, cpl: 5, roas: 3.8 },
  { date: "2024-01-05", spend: 900, follows: 180, cpl: 5, roas: 4.0 },
  { date: "2024-01-06", spend: 700, follows: 140, cpl: 5, roas: 3.6 },
  { date: "2024-01-07", spend: 850, follows: 170, cpl: 5, roas: 3.9 },
];

const channelData = [
  { channel: "Facebook", spend: 3500, follows: 700, cpl: 5, roas: 3.7 },
  { channel: "TikTok", spend: 2800, follows: 560, cpl: 5, roas: 3.4 },
  { channel: "Google", spend: 1200, follows: 240, cpl: 5, roas: 3.2 },
  { channel: "Twitter", spend: 800, follows: 160, cpl: 5, roas: 3.1 },
];

const costEfficiencyData = [
  metric: "单粉成本",
  average: 5.0,
  target: 4.5,
  best: 3.8,
  worst: 6.2,
},
  {
    metric: "转化成本",
    average: 25.0,
    target: 22.0,
    best: 18.5,
    worst: 32.0,
  },
  {
    metric: "千次展示成本",
    average: 15.0,
    target: 12.0,
    best: 10.0,
    worst: 20.0,
  },
];

export default function DailyReportsAnalysisPage() {
  const [dateRange, setDateRange] = useState({
    start: subDays(new Date(), 7),
    end: new Date(),
  });

  // 关键指标卡片
  const KpiCards = () => {
    const totalSpend = performanceData.reduce((sum, item) => sum + item.spend, 0);
    const totalFollows = performanceData.reduce((sum, item) => sum + item.follows, 0);
    const avgCpl = totalSpend / totalFollows;
    const avgRoas = performanceData.reduce((sum, item) => sum + item.roas, 0) / performanceData.length;

    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">总消耗</p>
                <p className="text-2xl font-bold">¥{totalSpend.toLocaleString()}</p>
                <p className="text-xs text-gray-500 mt-1">较上周 +12.5%</p>
              </div>
              <DollarSign className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">总粉丝数</p>
                <p className="text-2xl font-bold">{totalFollows.toLocaleString()}</p>
                <p className="text-xs text-gray-500 mt-1">较上周 +8.3%</p>
              </div>
              <Users className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">平均 CPL</p>
                <p className="text-2xl font-bold">¥{avgCpl.toFixed(2)}</p>
                <p className="text-xs text-green-600 mt-1">低于目标 10%</p>
              </div>
              <Target className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">平均 ROI</p>
                <p className="text-2xl font-bold">{avgRoas.toFixed(2)}</p>
                <p className="text-xs text-green-600 mt-1">表现良好</p>
              </div>
              <TrendingUp className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  // 成本效率分析
  const CostEfficiencyAnalysis = () => (
    <Card>
      <CardHeader>
        <CardTitle>成本效率分析</CardTitle>
        <CardDescription>关键成本指标与目标对比</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {costEfficiencyData.map((item, index) => (
            <div key={index} className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="font-medium">{item.metric}</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">
                    平均: ¥{item.average}
                  </span>
                  <Badge variant={item.average <= item.target ? "default" : "destructive"}>
                    {item.average <= item.target ? "达标" : "超标"}
                  </Badge>
                </div>
              </div>
              <div className="relative h-8 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="absolute h-full bg-blue-500 rounded-full"
                  style={{
                    width: `${(item.worst / item.worst) * 100}%`,
                    left: 0,
                  }}
                />
                <div
                  className="absolute h-full bg-gray-300 rounded-full"
                  style={{
                    width: `${((item.average - item.best) / (item.worst - item.best)) * 100}%`,
                    left: `${(item.best / item.worst) * 100}%`,
                  }}
                />
                <div
                  className="absolute h-full w-1 bg-green-500 rounded-full"
                  style={{
                    left: `${(item.target / item.worst) * 100}%`,
                  }}
                />
                <div className="absolute h-full flex items-center justify-center w-full">
                  <div className="flex justify-between w-full px-4 text-xs">
                    <span className="text-white font-semibold">¥{item.best}</span>
                    <span>目标: ¥{item.target}</span>
                    <span>¥{item.worst}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );

  // 渠道对比分析
  const ChannelComparison = () => (
    <Card>
      <CardHeader>
        <CardTitle>渠道表现对比</CardTitle>
        <CardDescription>各广告渠道的消耗和效果对比</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={channelData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="channel" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Bar yAxisId="left" dataKey="spend" fill="#8884d8" name="消耗(¥)" />
            <Bar yAxisId="right" dataKey="follows" fill="#82ca9d" name="新增粉丝" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );

  // 趋势分析
  const TrendAnalysis = () => {
    // 计算移动平均
    const movingAverageData = performanceData.map((item, index) => {
      const startIndex = Math.max(0, index - 2);
      const endIndex = index + 1;
      const subset = performanceData.slice(startIndex, endIndex);
      const avgSpend = subset.reduce((sum, item) => sum + item.spend, 0) / subset.length;
      const avgFollows = subset.reduce((sum, item) => sum + item.follows, 0) / subset.length;

      return {
        ...item,
        avgSpend: parseFloat(avgSpend.toFixed(2)),
        avgFollows: parseFloat(avgFollows.toFixed(2)),
      };
    });

    return (
      <Card>
        <CardHeader>
          <CardTitle>趋势分析</CardTitle>
          <CardDescription>消耗和粉丝增长趋势及3日移动平均</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={movingAverageData}>
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
                name="每日消耗"
                strokeWidth={2}
              />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="avgSpend"
                stroke="#f97316"
                name="消耗移动平均"
                strokeDasharray="5 5"
                strokeWidth={2}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="follows"
                stroke="#3b82f6"
                name="每日新增粉丝"
                strokeWidth={2}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="avgFollows"
                stroke="#06b6d4"
                name="粉丝移动平均"
                strokeDasharray="5 5"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* 页面标题 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">日报数据分析</h1>
          <p className="text-gray-600">深入分析广告投放数据和效果</p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline">
            <Filter className="w-4 h-4 mr-2" />
            高级筛选
          </Button>
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            导出分析报告
          </Button>
        </div>
      </div>

      {/* 关键指标 */}
      <KpiCards />

      {/* 分析标签页 */}
      <Tabs defaultValue="dashboard" className="space-y-4">
        <TabsList>
          <TabsTrigger value="dashboard">综合看板</TabsTrigger>
          <TabsTrigger value="cost">成本效率</TabsTrigger>
          <TabsTrigger value="channel">渠道对比</TabsTrigger>
          <TabsTrigger value="trend">趋势分析</TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard">
          <DailyReportsDashboard
            dateRange={dateRange}
            onDateRangeChange={setDateRange}
          />
        </TabsContent>

        <TabsContent value="cost">
          <CostEfficiencyAnalysis />
        </TabsContent>

        <TabsContent value="channel">
          <ChannelComparison />
        </TabsContent>

        <TabsContent value="trend">
          <TrendAnalysis />
        </TabsContent>
      </Tabs>

      {/* AI 洞察和建议 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            AI 洞察与建议
          </CardTitle>
          <CardDescription>基于数据分析的智能建议</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <h3 className="font-semibold text-green-600">优化建议</h3>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-1">•</span>
                  <span>Facebook 渠道 ROI 较高，建议增加 20% 预算</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-1">•</span>
                  <span>当前 CPL 低于目标，可以考虑适当提高出价获取更多流量</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-1">•</span>
                  <span>周三至周五的转化效果最佳，建议在这些日期加大投放</span>
                </li>
              </ul>
            </div>

            <div className="space-y-3">
              <h3 className="font-semibold text-yellow-600">风险提醒</h3>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-yellow-500 mt-1">•</span>
                  <span>Google 渠道成本持续上升，需要优化投放策略</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-yellow-500 mt-1">•</span>
                  <span>周末的投放效果明显下降，建议减少预算</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-yellow-500 mt-1">•</span>
                  <span>某广告系列 ROI 低于 2，建议暂停或优化</span>
                </li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}