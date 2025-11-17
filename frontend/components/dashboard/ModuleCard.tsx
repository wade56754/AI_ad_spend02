"use client";

import React from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import {
  LayoutDashboard,
  Users,
  FileText,
  DollarSign,
  BarChart3,
  Target,
  TrendingUp,
  Settings,
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react';

export interface ModuleCardProps {
  title: string;
  description: string;
  status: 'active' | 'normal' | 'warning' | 'error';
  primaryMetric?: {
    value: string | number;
    label: string;
  };
  secondaryMetric?: {
    value: string | number;
    label: string;
  };
  ctaLabel?: string;
  onClick?: () => void;
  href?: string;
  icon: React.ComponentType<any>;
  iconColor?: string;
  className?: string;
}

const statusConfig = {
  active: {
    badgeVariant: 'default' as const,
    badgeColor: 'bg-blue-100 text-blue-800 border-blue-200',
    cardBorder: 'border-l-4 border-l-blue-500',
    icon: CheckCircle
  },
  normal: {
    badgeVariant: 'default' as const,
    badgeColor: 'bg-green-100 text-green-800 border-green-200',
    cardBorder: 'border-l-4 border-l-green-500',
    icon: CheckCircle
  },
  warning: {
    badgeVariant: 'secondary' as const,
    badgeColor: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    cardBorder: 'border-l-4 border-l-yellow-500',
    icon: AlertTriangle
  },
  error: {
    badgeVariant: 'destructive' as const,
    badgeColor: 'bg-red-100 text-red-800 border-red-200',
    cardBorder: 'border-l-4 border-l-red-500',
    icon: XCircle
  }
};

export function ModuleCard({
  title,
  description,
  status = 'normal',
  primaryMetric,
  secondaryMetric,
  ctaLabel = '进入模块',
  onClick,
  href,
  icon: Icon,
  iconColor = 'text-blue-600',
  className
}: ModuleCardProps) {
  const config = statusConfig[status];

  // 防御性检查：如果status无效，使用默认的'normal'配置
  const safeConfig = config || statusConfig.normal;
  const StatusIcon = safeConfig.icon;

  const CardWrapper = href ? 'a' : 'div';
  const cardProps = href
    ? { href, className: "block" }
    : { onClick, className: "block cursor-pointer" };

  return (
    <CardWrapper {...cardProps}>
      <Card
        className={cn(
          "group relative overflow-hidden transition-all duration-200 hover:shadow-lg hover:scale-[1.02] border bg-card",
          safeConfig.cardBorder,
          className
        )}
      >
        <CardContent className="p-6">
          {/* 顶部：图标和状态 */}
          <div className="flex items-start justify-between mb-4">
            <div className={cn(
              "flex items-center justify-center w-12 h-12 rounded-lg",
              iconColor === 'text-blue-600' && 'bg-blue-100',
              iconColor === 'text-green-600' && 'bg-green-100',
              iconColor === 'text-purple-600' && 'bg-purple-100',
              iconColor === 'text-orange-600' && 'bg-orange-100',
              iconColor === 'text-red-600' && 'bg-red-100',
              iconColor === 'text-gray-600' && 'bg-gray-100'
            )}>
              <Icon className={cn("w-6 h-6", iconColor)} />
            </div>
            <div className="flex items-center gap-2">
              <StatusIcon className={cn("w-4 h-4", status === 'active' && 'text-blue-600', status === 'normal' && 'text-green-600', status === 'warning' && 'text-yellow-600', status === 'error' && 'text-red-600')} />
              <Badge
                variant={safeConfig.badgeVariant}
                className={cn("text-xs font-medium", safeConfig.badgeColor)}
              >
                {status === 'active' ? '活跃' : status === 'normal' ? '正常' : status === 'warning' ? '警告' : '异常'}
              </Badge>
            </div>
          </div>

          {/* 中间：标题和描述 */}
          <div className="mb-4">
            <h3 className="text-base font-semibold text-card-foreground leading-tight mb-1">
              {title}
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {description}
            </p>
          </div>

          {/* 底部：指标和CTA */}
          <div className="space-y-4">
            {/* 指标数据 */}
            <div className="space-y-2">
              {primaryMetric && (
                <div className="flex items-baseline justify-between">
                  <span className="text-2xl font-bold text-card-foreground">
                    {primaryMetric.value}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {primaryMetric.label}
                  </span>
                </div>
              )}
              {secondaryMetric && (
                <div className="flex items-baseline justify-between">
                  <span className="text-lg font-semibold text-card-foreground">
                    {secondaryMetric.value}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {secondaryMetric.label}
                  </span>
                </div>
              )}
            </div>

            {/* CTA按钮 */}
            <Button
              variant="outline"
              size="sm"
              className="w-full group-hover:bg-primary group-hover:text-primary-foreground group-hover:border-primary"
            >
              {ctaLabel}
            </Button>
          </div>
        </CardContent>
      </Card>
    </CardWrapper>
  );
}

export default ModuleCard;