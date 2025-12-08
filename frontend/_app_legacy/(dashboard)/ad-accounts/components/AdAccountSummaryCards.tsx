'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  CreditCard,
  Activity,
  DollarSign,
  TrendingUp,
  AlertTriangle,
  Users,
  BarChart3,
  Clock,
  CheckCircle,
  Eye,
  Shield
} from 'lucide-react';
import { AdAccountStats, KPICardConfig } from '../types';

interface AdAccountSummaryCardsProps {
  stats: AdAccountStats;
  loading?: boolean;
}

/**
 * 广告账户管理KPI统计卡片组件
 *
 * 显示广告账户相关的关键指标，包括账户数量、消耗、风险等
 */
export function AdAccountSummaryCards({ stats, loading = false }: AdAccountSummaryCardsProps) {
  // KPI卡片配置
  const kpiConfigs: KPICardConfig[] = [
    {
      title: '总账户数',
      value: stats.total_accounts,
      subtitle: '所有广告账户',
      color: 'primary',
      icon: CreditCard,
    },
    {
      title: '活跃账户',
      value: stats.active_accounts,
      subtitle: '正在投放的账户',
      color: 'success',
      icon: Activity,
      trend: stats.active_accounts > 0 ? {
        type: 'up',
        value: Math.round((stats.active_accounts / stats.total_accounts) * 100),
        period: '占比'
      } : undefined,
    },
    {
      title: '已暂停账户',
      value: stats.paused_accounts,
      subtitle: '暂时停止投放',
      color: 'warning',
      icon: Clock,
    },
    {
      title: '高风险账户',
      value: stats.high_risk_accounts,
      subtitle: '需要关注的账户',
      color: 'destructive',
      icon: AlertTriangle,
    },
    {
      title: '本月消耗',
      value: `$${stats.last_30d_spend.toLocaleString()}`,
      subtitle: '最近30天总消耗',
      color: 'info',
      icon: DollarSign,
      trend: stats.last_30d_spend > 0 ? {
        type: 'up',
        value: Math.round(stats.last_30d_spend / 1000) / 10, // Convert to K
        period: 'K'
      } : undefined,
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
                      {config.trend.value > 0 ? '+' : ''}{config.trend.value}%
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
              {config.title === '活跃账户' && stats.active_accounts === 0 && (
                <Badge variant="outline" className="mt-2 text-xs border-orange-500/20 text-orange-600">
                  无活跃账户
                </Badge>
              )}

              {config.title === '高风险账户' && stats.high_risk_accounts > 0 && (
                <Badge variant="outline" className="mt-2 text-xs border-red-500/20 text-red-600">
                  需要处理
                </Badge>
              )}

              {config.title === '已暂停账户' && stats.paused_accounts > stats.active_accounts && (
                <Badge variant="outline" className="mt-2 text-xs border-yellow-500/20 text-yellow-600">
                  暂停较多
                </Badge>
              )}

              {config.title === '本月消耗' && stats.utilization_rate > 90 && (
                <Badge variant="outline" className="mt-2 text-xs border-green-500/20 text-green-600">
                  高利用率
                </Badge>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

export default AdAccountSummaryCards;