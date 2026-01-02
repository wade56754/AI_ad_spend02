'use client';

/**
 * Commission Rules Page - 提成规则管理页面
 *
 * TASK-PRJ-003: 提成配置
 */

import { useState } from 'react';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useCommissionRules } from '../hooks';
import { CommissionRulesTable } from './CommissionRulesTable';
import { CommissionRuleDialog } from './CommissionRuleDialog';
import { CommissionCalculator } from './CommissionCalculator';
import type { CommissionRule } from '../types';

export function CommissionRulesPage() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<CommissionRule | null>(null);
  const [isCalculatorOpen, setIsCalculatorOpen] = useState(false);
  const [calculatorRule, setCalculatorRule] = useState<CommissionRule | null>(null);

  const { data, isLoading, error } = useCommissionRules({ limit: 50 });

  const handleEdit = (rule: CommissionRule) => {
    setEditingRule(rule);
    setIsDialogOpen(true);
  };

  const handleCreate = () => {
    setEditingRule(null);
    setIsDialogOpen(true);
  };

  const handleCalculate = (rule: CommissionRule) => {
    setCalculatorRule(rule);
    setIsCalculatorOpen(true);
  };

  const handleDialogClose = () => {
    setIsDialogOpen(false);
    setEditingRule(null);
  };

  const handleCalculatorClose = () => {
    setIsCalculatorOpen(false);
    setCalculatorRule(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">提成规则管理</h1>
          <p className="text-muted-foreground">
            配置投手提成规则，基于确认进粉数 (conversions_final) 计算提成
          </p>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="mr-2 h-4 w-4" />
          新建规则
        </Button>
      </div>

      {/* Info Card */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">阶梯提成说明</CardTitle>
          <CardDescription>
            提成按阶梯累加计算：每个阶梯内的进粉数 x 该阶梯费率，然后累加所有阶梯金额
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">
            <p className="mb-2">
              <strong>计算公式:</strong> 总提成 = Σ(阶梯内进粉数 × 阶梯费率)
            </p>
            <p>
              <strong>示例:</strong> 规则 [1-50粉: ¥1, 51-100粉: ¥1.5, 101+粉: ¥2]，实际进粉 120 →
              提成 = 50×1 + 50×1.5 + 20×2 = ¥165
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <CommissionRulesTable
        data={data?.data.items ?? []}
        isLoading={isLoading}
        error={error}
        onEdit={handleEdit}
        onCalculate={handleCalculate}
      />

      {/* Create/Edit Dialog */}
      <CommissionRuleDialog
        open={isDialogOpen}
        onOpenChange={handleDialogClose}
        rule={editingRule}
      />

      {/* Calculator Dialog */}
      <CommissionCalculator
        open={isCalculatorOpen}
        onOpenChange={handleCalculatorClose}
        rule={calculatorRule}
      />
    </div>
  );
}
