'use client';

/**
 * Commission Calculator - 提成计算器
 *
 * TASK-PRJ-003: 提成配置
 * 用于测试提成规则的计算结果
 */

import { useState, useEffect } from 'react';
import { Calculator } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { useCalculateCommissionMutation } from '../hooks';
import { type CommissionRule, formatTierRange, formatCommissionAmount } from '../types';

interface CommissionCalculatorProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  rule: CommissionRule | null;
}

export function CommissionCalculator({ open, onOpenChange, rule }: CommissionCalculatorProps) {
  const [conversions, setConversions] = useState<number>(100);

  const calculateMutation = useCalculateCommissionMutation();

  // Recalculate when conversions or rule changes
  useEffect(() => {
    if (rule && conversions >= 0) {
      calculateMutation.mutate({ ruleId: rule.id, conversions });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversions, rule?.id]);

  if (!rule) return null;

  const result = calculateMutation.data?.data;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Calculator className="h-5 w-5" />
            提成计算器
          </DialogTitle>
          <DialogDescription>测试规则「{rule.name}」的提成计算结果</DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Input */}
          <div className="space-y-2">
            <Label htmlFor="conversions">输入进粉数</Label>
            <Input
              id="conversions"
              type="number"
              min={0}
              value={conversions}
              onChange={(e) => setConversions(Math.max(0, parseInt(e.target.value) || 0))}
              placeholder="请输入进粉数"
            />
          </div>

          {/* Rule Tiers */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">阶梯配置</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1">
                {rule.config.tiers.map((tier, index) => (
                  <div key={index} className="flex justify-between text-sm">
                    <span className="text-muted-foreground">{formatTierRange(tier)}</span>
                    <span className="font-medium">{formatCommissionAmount(tier.rate)}/粉</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Calculation Result */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">计算结果</CardTitle>
            </CardHeader>
            <CardContent>
              {calculateMutation.isPending ? (
                <div className="space-y-2">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-8 w-1/2" />
                </div>
              ) : result ? (
                <div className="space-y-3">
                  {/* Breakdown */}
                  <div className="space-y-1">
                    {result.breakdown.map((item, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between text-sm border-b last:border-0 pb-1 last:pb-0"
                      >
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs">
                            {formatTierRange(item.tier)}
                          </Badge>
                          <span className="text-muted-foreground">
                            {item.count} 粉 × {formatCommissionAmount(item.tier.rate)}
                          </span>
                        </div>
                        <span className="font-medium">{formatCommissionAmount(item.amount)}</span>
                      </div>
                    ))}
                  </div>

                  {/* Total */}
                  <div className="pt-2 border-t flex items-center justify-between">
                    <span className="font-medium">总提成</span>
                    <span className="text-xl font-bold text-primary">
                      {formatCommissionAmount(result.total_commission, result.currency)}
                    </span>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">输入进粉数后显示计算结果</p>
              )}

              {calculateMutation.isError && (
                <p className="text-sm text-destructive">计算失败，请重试</p>
              )}
            </CardContent>
          </Card>

          {/* Formula Explanation */}
          <div className="text-xs text-muted-foreground bg-muted/50 rounded-md p-3">
            <p className="font-medium mb-1">计算公式</p>
            <p>
              总提成 = Σ(阶梯内进粉数 × 阶梯费率)
              <br />
              按阶梯累加计算，每个阶梯范围内的进粉数乘以对应费率后求和
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
