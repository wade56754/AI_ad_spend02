/**
 * FinanceCharts - 财务图表组件
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
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
} from 'recharts';
import type {
  FinancialSummary,
  SpendingTrend,
  PlatformSpending,
  TeamSpending,
} from '../types';

// =============================================================================
// 支出趋势图
// =============================================================================

interface SpendingTrendChartProps {
  data: SpendingTrend[];
}

export function SpendingTrendChart({ data }: SpendingTrendChartProps) {
  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-text-strong">支出趋势分析</CardTitle>
        <CardDescription className="text-text-muted">
          最近7天的支出和充值趋势
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis dataKey="date" stroke="hsl(var(--text-muted))" />
            <YAxis stroke="hsl(var(--text-muted))" />
            <Tooltip
              formatter={(value) => `¥${Number(value).toLocaleString()}`}
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                borderColor: 'hsl(var(--border))',
                color: 'hsl(var(--text-body))',
              }}
            />
            <Legend />
            <Area
              type="monotone"
              dataKey="spending"
              stackId="1"
              stroke="hsl(var(--danger))"
              fill="hsl(var(--danger) / 0.2)"
              name="支出"
            />
            <Area
              type="monotone"
              dataKey="topups"
              stackId="2"
              stroke="hsl(var(--success))"
              fill="hsl(var(--success) / 0.2)"
              name="充值"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

// =============================================================================
// 平台支出分布图
// =============================================================================

interface PlatformPieChartProps {
  data: PlatformSpending[];
}

export function PlatformPieChart({ data }: PlatformPieChartProps) {
  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-text-strong">平台支出分布</CardTitle>
        <CardDescription className="text-text-muted">
          各平台广告支出占比
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ platform, percentage }) => `${platform} ${percentage}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="amount"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value) => `¥${Number(value).toLocaleString()}`}
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                borderColor: 'hsl(var(--border))',
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

// =============================================================================
// 平台支出柱状图
// =============================================================================

interface PlatformBarChartProps {
  data: PlatformSpending[];
}

export function PlatformBarChart({ data }: PlatformBarChartProps) {
  return (
    <Card className="bg-card border-border lg:col-span-2">
      <CardHeader>
        <CardTitle className="text-text-strong">平台支出详细分析</CardTitle>
        <CardDescription className="text-text-muted">
          各平台支出金额和趋势分析
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis dataKey="platform" stroke="hsl(var(--text-muted))" />
            <YAxis stroke="hsl(var(--text-muted))" />
            <Tooltip
              formatter={(value) => `¥${Number(value).toLocaleString()}`}
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                borderColor: 'hsl(var(--border))',
              }}
            />
            <Bar dataKey="amount" fill="hsl(var(--accent))">
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

// =============================================================================
// 月度支出对比
// =============================================================================

interface MonthlyComparisonProps {
  summary: FinancialSummary;
}

export function MonthlyComparison({ summary }: MonthlyComparisonProps) {
  const growthRate =
    ((summary.this_month_spending - summary.last_month_spending) /
      summary.last_month_spending) *
    100;

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-text-strong">月度支出对比</CardTitle>
        <CardDescription className="text-text-muted">
          本月与上月支出对比分析
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <span className="text-sm text-text-muted">本月支出</span>
            <span className="font-semibold text-text-strong">
              ¥{summary.this_month_spending.toLocaleString()}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-text-muted">上月支出</span>
            <span className="font-semibold text-text-strong">
              ¥{summary.last_month_spending.toLocaleString()}
            </span>
          </div>
          <Progress
            value={Math.min(
              (summary.this_month_spending / summary.last_month_spending) * 100,
              100
            )}
            className="h-4"
          />
          <div className="text-sm text-center text-success font-medium">
            增长 {growthRate.toFixed(1)}%
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// =============================================================================
// 预算预测
// =============================================================================

interface BudgetProjectionProps {
  summary: FinancialSummary;
}

export function BudgetProjection({ summary }: BudgetProjectionProps) {
  const progressValue =
    (summary.this_month_spending / summary.projected_spend) * 100;

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-text-strong">预算预测</CardTitle>
        <CardDescription className="text-text-muted">
          基于当前趋势的月度预算预测
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <span className="text-sm text-text-muted">当前已支出</span>
            <span className="font-semibold text-text-strong">
              ¥{summary.this_month_spending.toLocaleString()}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-text-muted">预计总支出</span>
            <span className="font-semibold text-text-strong">
              ¥{summary.projected_spend.toLocaleString()}
            </span>
          </div>
          <Progress value={progressValue} className="h-3" />
          <div className="text-sm text-center text-text-muted">
            已完成 {progressValue.toFixed(1)}%
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// =============================================================================
// 团队预算使用
// =============================================================================

interface TeamBudgetListProps {
  data: TeamSpending[];
}

export function TeamBudgetList({ data }: TeamBudgetListProps) {
  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-text-strong">团队预算使用情况</CardTitle>
        <CardDescription className="text-text-muted">
          各团队成员的预算使用效率和绩效分析
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {data.map((member) => (
            <div
              key={member.user_name}
              className="border border-border rounded-lg p-4"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <Avatar className="h-10 w-10">
                    <AvatarFallback className="bg-accent/10 text-accent">
                      {member.user_name[0]}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <div className="font-medium text-text-strong">
                      {member.user_name}
                    </div>
                    <div className="text-sm text-text-muted">{member.role}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-semibold text-text-strong">
                    ¥{member.total_spent.toLocaleString()}
                  </div>
                  <div className="text-sm text-text-muted">
                    {member.projects_count} 个项目
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-text-muted">预算利用率</span>
                    <span className="text-text-body">
                      {member.budget_utilization}%
                    </span>
                  </div>
                  <Progress value={member.budget_utilization} className="h-2" />
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-text-muted">效率评分</span>
                    <span className="text-text-body">
                      {member.efficiency_score}/100
                    </span>
                  </div>
                  <Progress value={member.efficiency_score} className="h-2" />
                </div>

                <div className="flex items-center justify-end gap-2">
                  <Badge
                    variant={
                      member.efficiency_score >= 90
                        ? 'default'
                        : member.efficiency_score >= 80
                          ? 'secondary'
                          : 'destructive'
                    }
                    className={
                      member.efficiency_score >= 90
                        ? 'bg-success/10 text-success'
                        : member.efficiency_score >= 80
                          ? 'bg-warning/10 text-warning'
                          : 'bg-danger/10 text-danger'
                    }
                  >
                    {member.efficiency_score >= 90
                      ? '优秀'
                      : member.efficiency_score >= 80
                        ? '良好'
                        : '需改进'}
                  </Badge>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
