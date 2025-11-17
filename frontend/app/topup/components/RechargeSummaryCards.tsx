'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  FileText,
  Clock,
  CheckCircle,
  DollarSign,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Minus
} from 'lucide-react';
import { RechargeStats, KPICardConfig } from '../types';

interface RechargeSummaryCardsProps {
  stats: RechargeStats;
  loading?: boolean;
}

/**
 * 充值管理KPI统计卡片组件
 *
 * 显示充值相关的关键指标，包括申请数量、金额统计等
 */
export function RechargeSummaryCards({ stats, loading = false }: RechargeSummaryCardsProps) {
  // KPI卡片配置
  const kpiConfigs: KPICardConfig[] = [
    {
      title: '总申请数',
      value: stats.total_requests,
      subtitle: '所有充值申请',
      color: 'primary',
      icon: FileText,
    },
    {
      title: '待审核申请',
      value: stats.pending_requests,
      subtitle: '需要处理的申请',
      color: 'warning',
      icon: Clock,
    },
    {
      title: '已完成申请',
      value: stats.completed_requests,
      subtitle: '本月已完成充值',
      color: 'success',
      icon: CheckCircle,
    },
    {
      title: '累计充值金额',
      value: `$${stats.total_amount.toLocaleString()}`,
      subtitle: '所有申请金额',
      color: 'info',
      icon: DollarSign,
    },
    {
      title: '待充值金额',
      value: `$${stats.pending_amount.toLocaleString()}`,
      subtitle: '需要处理的金额',
      color: 'destructive',
      icon: AlertTriangle,
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

                {/* 趋势指示器（可选） */}
                {config.trend && (
                  <div className="flex items-center gap-1">
                    {config.trend.type === 'up' && (
                      <TrendingUp className="h-3 w-3 text-green-600" />
                    )}
                    {config.trend.type === 'down' && (
                      <TrendingDown className="h-3 w-3 text-red-600" />
                    )}
                    {config.trend.type === 'neutral' && (
                      <Minus className="h-3 w-3 text-muted-foreground" />
                    )}
                    <span className={`text-xs font-medium ${
                      config.trend.type === 'up' ? 'text-green-600' :
                      config.trend.type === 'down' ? 'text-red-600' :
                      'text-muted-foreground'
                    }`}>
                      {config.trend.value > 0 ? '+' : ''}{config.trend.value}%
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

              {/* 待审核高亮提示 */}
              {config.title === '待审核申请' && stats.pending_requests > 0 && (
                <Badge variant="outline" className="mt-2 text-xs border-yellow-500/20 text-yellow-600">
                  需要处理
                </Badge>
              )}

              {/* 待充值金额高亮提示 */}
              {config.title === '待充值金额' && stats.pending_amount > 10000 && (
                <Badge variant="outline" className="mt-2 text-xs border-red-500/20 text-red-600">
                  高额提醒
                </Badge>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

export default RechargeSummaryCards;