'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  FolderOpen,
  PlayCircle,
  CheckCircle,
  DollarSign,
  TrendingUp,
  Users,
  AlertTriangle,
  Clock,
  Target,
  BarChart3
} from 'lucide-react';
import { ProjectStats, KPICardConfig } from '../types';

interface ProjectSummaryCardsProps {
  stats: ProjectStats;
  loading?: boolean;
}

/**
 * 项目管理KPI统计卡片组件
 *
 * 显示项目相关的关键指标，包括项目数量、预算、ROI等
 */
export function ProjectSummaryCards({ stats, loading = false }: ProjectSummaryCardsProps) {
  // KPI卡片配置
  const kpiConfigs: KPICardConfig[] = [
    {
      title: '总项目数',
      value: stats.total_projects,
      subtitle: '所有项目',
      color: 'primary',
      icon: FolderOpen,
    },
    {
      title: '活跃项目',
      value: stats.active_projects,
      subtitle: '进行中的项目',
      color: 'success',
      icon: PlayCircle,
      trend: stats.active_projects > 0 ? {
        type: 'up',
        value: Math.round((stats.active_projects / stats.total_projects) * 100),
        period: '占比'
      } : undefined,
    },
    {
      title: '已完成项目',
      value: stats.completed_projects,
      subtitle: '成功交付的项目',
      color: 'info',
      icon: CheckCircle,
      trend: stats.completed_projects > 0 ? {
        type: 'up',
        value: Math.round((stats.completed_projects / stats.total_projects) * 100),
        period: '完成率'
      } : undefined,
    },
    {
      title: '总预算',
      value: `¥${stats.total_budget.toLocaleString()}`,
      subtitle: '所有项目预算总额',
      color: 'warning',
      icon: DollarSign,
    },
    {
      title: '平均ROI',
      value: stats.average_roi.toFixed(2),
      subtitle: '投资回报率平均值',
      color: 'success',
      icon: TrendingUp,
      trend: stats.average_roi > 0 ? {
        type: 'up',
        value: Math.round(stats.average_roi * 10) / 10,
        period: '平均'
      } : {
        type: 'neutral',
        value: 0,
        period: '无收益'
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
              {config.title === '活跃项目' && stats.active_projects === 0 && (
                <Badge variant="outline" className="mt-2 text-xs border-yellow-500/20 text-yellow-600">
                  无活跃项目
                </Badge>
              )}

              {config.title === '平均ROI' && stats.average_roi < 1 && stats.average_roi > 0 && (
                <Badge variant="outline" className="mt-2 text-xs border-orange-500/20 text-orange-600">
                  ROI偏低
                </Badge>
              )}

              {config.title === '平均ROI' && stats.average_roi === 0 && (
                <Badge variant="outline" className="mt-2 text-xs border-red-500/20 text-red-600">
                  无收益
                </Badge>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

export default ProjectSummaryCards;