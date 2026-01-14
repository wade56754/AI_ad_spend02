/**
 * FundDistribution - 资金分布图
 *
 * 显示资金在各项目/渠道的分布情况
 *
 * @module features/finance/components/FundOverview
 */

'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import type { DistributionItem } from '../../types/finance.types';
import { formatCurrency } from '../../utils/financeHelpers';

interface FundDistributionProps {
  title: string;
  items: DistributionItem[];
  total: number;
}

export function FundDistribution({ title, items, total }: FundDistributionProps) {

  // 取前 5 个显示
  const topItems = items.slice(0, 5);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {topItems.length === 0 ? (
          <div className="text-center text-muted-foreground py-4">暂无数据</div>
        ) : (
          topItems.map((item) => (
            <div key={item.id} className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="truncate max-w-[120px]" title={item.name}>
                  {item.name}
                </span>
                <span className="font-medium">{formatCurrency(item.balance)}</span>
              </div>
              <Progress value={item.percentage} className="h-2" />
              <div className="text-xs text-muted-foreground text-right">
                {item.percentage.toFixed(1)}%
              </div>
            </div>
          ))
        )}

        {total > 0 && (
          <div className="pt-2 border-t">
            <div className="flex items-center justify-between text-sm font-medium">
              <span>总计</span>
              <span>{formatCurrency(total)}</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
