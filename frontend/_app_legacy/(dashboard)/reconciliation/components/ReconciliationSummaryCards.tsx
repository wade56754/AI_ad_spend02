'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  FileText,
  Clock,
  CheckCircle,
  AlertTriangle,
  DollarSign,
  TrendingUp,
  BarChart3,
  RefreshCw,
  Target,
  Activity,
} from 'lucide-react';
import { ReconciliationSummary, KPICardConfig } from '../types';

interface ReconciliationSummaryCardsProps {
  stats: ReconciliationSummary;
  loading?: boolean;
}

/**
 * 对账管理KPI统计卡片组件
 *
 * 显示对账相关的关键指标，包括批次数量、差异情况、处理进度等
 */
export function ReconciliationSummaryCards({ stats, loading = false }: ReconciliationSummaryCardsProps) {
  // KPI卡片配置
  const kpiConfigs: KPICardConfig[] = [
    {
      title: '总对账批次',
      value: stats.total_batches,
      subtitle: `已完成: ${stats.completed_batches}`,
      color: 'primary',
      icon: FileText,
    },
    {
      title: '待处理批次',
      value: stats.pending_batches + stats.in_progress_batches,
      subtitle: `即将开始: ${stats.upcoming_batches}`,
      color: 'warning',
      icon: Clock,
      trend: stats.pending_batches > 0 ? {
        type: 'up',
        value: Math.round(((stats.pending_batches + stats.in_progress_batches) / stats.total_batches) * 100),
        period: '占比'
      } : undefined,
    },
    {
      title: '总差异金额',
      value: `¥${Math.abs(stats.total_difference).toLocaleString()}`,
      subtitle: `平均差异率: ${Math.abs(stats.avg_difference_percentage).toFixed(2)}%`,
      color: stats.total_difference >= 0 ? 'success' : 'destructive',
      icon: DollarSign,
      trend: {
        type: stats.total_difference >= 0 ? 'up' : 'down',
        value: Math.abs(stats.total_difference) / 1000,
        period: 'K'
      },
    },
    {
      title: '差异数量',
      value: stats.total_discrepancies,
      subtitle: `待处理: ${stats.pending_discrepancies}`,
      color: stats.total_discrepancies > 0 ? 'warning' : 'success',
      icon: AlertTriangle,
      trend: stats.total_discrepancies > 0 ? {
        type: 'up',
        value: Math.round((stats.pending_discrepancies / stats.total_discrepancies) * 100),
        period: '待处理率'
      } : {
        type: 'neutral',
        value: 0,
        period: '无差异'
      },
    },
    {
      title: '自动匹配率',
      value: `${(stats.auto_match_rate * 100).toFixed(1)}%`,
      subtitle: '数据匹配效率',
      color: 'info',
      icon: Target,
      trend: {
        type: 'up',
        value: Math.round(stats.auto_match_rate * 100),
        period: '效率'
      },
    },
  ];

  // Loading状态
  if (loading) {
    return (
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {[...Array(5)].map((_, index) => (
          <Card key={index} className="bg-card border-border">
            <CardContent className="p-4">
              <div className="animate-pulse space-y-3">
                <div className="flex items-center justify-between">
                  <div className="h-4 w-16 bg-muted rounded"></div>
                  <div className="h-5 w-5 bg-muted rounded"></div>
                </div>
                <div className="h-8 w-20 bg-muted rounded"></div>
                <div className="h-3 w-24 bg-muted rounded"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
      {kpiConfigs.map((config, index) => {
        const IconComponent = config.icon;

        // 根据color类型确定样式
        const getColorClasses = (color?: KPICardConfig['color']) => {
          switch (color) {
            case 'primary':
              return {
                bg: 'bg-primary/10',
                text: 'text-primary',
                border: 'border-primary/20',
              };
            case 'success':
              return {
                bg: 'bg-green-500/10',
                text: 'text-green-600',
                border: 'border-green-500/20',
              };
            case 'warning':
              return {
                bg: 'bg-yellow-500/10',
                text: 'text-yellow-600',
                border: 'border-yellow-500/20',
              };
            case 'destructive':
              return {
                bg: 'bg-destructive/10',
                text: 'text-destructive',
                border: 'border-destructive/20',
              };
            case 'info':
              return {
                bg: 'bg-blue-500/10',
                text: 'text-blue-600',
                border: 'border-blue-500/20',
              };
            default:
              return {
                bg: 'bg-muted',
                text: 'text-muted-foreground',
                border: 'border-border',
              };
          }
        };

        const colorClasses = getColorClasses(config.color);

        return (
          <Card
            key={index}
            className={`bg-card border-border hover:shadow-md transition-shadow duration-200 ${colorClasses.border}`}
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className={`p-2 rounded-lg ${colorClasses.bg}`}>
                    <IconComponent className={`h-4 w-4 ${colorClasses.text}`} />
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-muted-foreground">
                      {config.title}
                    </h3>
                  </div>
                </div>

                {/* 趋势指示器 */}
                {config.trend && (
                  <div className="flex items-center gap-1">
                    {config.trend.type === 'up' && (
                      <TrendingUp className="h-3 w-3 text-green-600" />
                    )}
                    {config.trend.type === 'down' && (
                      <TrendingUp className="h-3 w-3 text-red-600 rotate-180" />
                    )}
                    {config.trend.type === 'neutral' && (
                      <BarChart3 className="h-3 w-3 text-muted-foreground" />
                    )}
                    <span className={`text-xs font-medium ${
                      config.trend.type === 'up' ? 'text-green-600' :
                      config.trend.type === 'down' ? 'text-red-600' :
                      'text-muted-foreground'
                    }`}>
                      {config.trend.value > 0 ? '+' : ''}{config.trend.value}
                      {config.trend.period && ` ${config.trend.period}`}
                    </span>
                  </div>
                )}
              </div>

              <div className="mb-2">
                <p className="text-2xl font-bold text-foreground">
                  {config.value}
                </p>
              </div>

              {config.subtitle && (
                <div>
                  <p className="text-xs text-muted-foreground">
                    {config.subtitle}
                  </p>
                </div>
              )}

              {/* 特殊高亮提示 */}
              {config.title === '待处理批次' && (stats.pending_batches + stats.in_progress_batches) > 3 && (
                <Badge variant="outline" className="mt-2 text-xs border-orange-500/20 text-orange-600">
                  需要处理
                </Badge>
              )}

              {config.title === '总差异金额' && Math.abs(stats.avg_difference_percentage) > 5 && (
                <Badge variant="outline" className="mt-2 text-xs border-red-500/20 text-red-600">
                  差异较大
                </Badge>
              )}

              {config.title === '差异数量' && stats.total_discrepancies > 10 && (
                <Badge variant="outline" className="mt-2 text-xs border-yellow-500/20 text-yellow-600">
                  需要关注
                </Badge>
              )}

              {config.title === '自动匹配率' && stats.auto_match_rate < 0.8 && (
                <Badge variant="outline" className="mt-2 text-xs border-orange-500/20 text-orange-600">
                  匹配率偏低
                </Badge>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

export default ReconciliationSummaryCards;