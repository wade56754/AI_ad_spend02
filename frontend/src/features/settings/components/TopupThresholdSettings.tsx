/**
 * TopupThresholdSettings - 充值阈值配置组件
 *
 * TASK-FE-SET-003: 充值阈值配置
 *
 * SoT 引用:
 * - FRONTEND_PAGE_DESIGN_v2.1.md §4.2 (充值权限表)
 * - 默认大额阈值: ¥50,000
 *
 * 功能:
 * - 大额充值阈值配置
 * - 低余额预警阈值配置
 * - 配置变更需确认
 * - 保存成功显示 toast
 */

'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Loader2,
  Save,
  AlertTriangle,
  DollarSign,
  TrendingUp,
  Bell,
  Info,
  CheckCircle2,
} from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

// === 类型定义 ===

const thresholdSettingsSchema = z.object({
  // 大额充值阈值 (默认 50000)
  largeTopupThreshold: z
    .number()
    .min(10000, '大额充值阈值最少 10,000 元')
    .max(1000000, '大额充值阈值最多 1,000,000 元'),
  // 低余额预警阈值
  lowBalanceThreshold: z
    .number()
    .min(1000, '低余额预警阈值最少 1,000 元')
    .max(100000, '低余额预警阈值最多 100,000 元'),
  // 充值提醒提前天数
  topupReminderDays: z
    .number()
    .min(1, '最少提前 1 天提醒')
    .max(30, '最多提前 30 天提醒'),
});

type ThresholdSettingsFormValues = z.infer<typeof thresholdSettingsSchema>;

export interface TopupThresholdSettingsProps {
  /** 初始值 */
  initialValues?: Partial<ThresholdSettingsFormValues>;
  /** 变更回调 */
  onChange?: () => void;
  /** 保存回调 */
  onSave?: (values: ThresholdSettingsFormValues) => Promise<void>;
}

// === 默认值 - SoT: FRONTEND_PAGE_DESIGN_v2.1.md §4.2 ===

const DEFAULT_VALUES: ThresholdSettingsFormValues = {
  largeTopupThreshold: 50000, // 大额充值阈值默认 ¥50,000
  lowBalanceThreshold: 5000, // 低余额预警默认 ¥5,000
  topupReminderDays: 3, // 提前 3 天提醒
};

// === 格式化金额 ===

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

// === 主组件 ===

export function TopupThresholdSettings({
  initialValues,
  onChange,
  onSave,
}: TopupThresholdSettingsProps) {
  const [isSaving, setIsSaving] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [pendingValues, setPendingValues] = useState<ThresholdSettingsFormValues | null>(null);

  const form = useForm<ThresholdSettingsFormValues>({
    resolver: zodResolver(thresholdSettingsSchema),
    defaultValues: {
      ...DEFAULT_VALUES,
      ...initialValues,
    },
  });

  // 当前值
  const currentValues = form.watch();

  // 监听表单变更
  const handleFieldChange = () => {
    onChange?.();
  };

  // 提交前确认
  const handleSubmit = (values: ThresholdSettingsFormValues) => {
    setPendingValues(values);
    setShowConfirm(true);
  };

  // 确认保存
  const handleConfirmSave = async () => {
    if (!pendingValues) return;

    setIsSaving(true);
    setShowConfirm(false);

    try {
      if (onSave) {
        await onSave(pendingValues);
      } else {
        // 模拟保存
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }
      toast.success('充值阈值配置保存成功');
    } catch (error) {
      toast.error(`保存失败: ${error instanceof Error ? error.message : '未知错误'}`);
    } finally {
      setIsSaving(false);
      setPendingValues(null);
    }
  };

  // 取消保存
  const handleCancelSave = () => {
    setShowConfirm(false);
    setPendingValues(null);
  };

  // 重置为默认值
  const handleReset = () => {
    form.reset(DEFAULT_VALUES);
    handleFieldChange();
    toast.info('已重置为默认配置');
  };

  return (
    <>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
          {/* 大额充值配置 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <TrendingUp className="h-4 w-4" />
                大额充值配置
              </CardTitle>
              <CardDescription>
                超过此金额的充值申请需要 CEO 审批
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <FormField
                control={form.control}
                name="largeTopupThreshold"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>大额充值阈值</FormLabel>
                    <FormControl>
                      <div className="flex items-center gap-2">
                        <DollarSign className="h-4 w-4 text-muted-foreground" />
                        <Input
                          type="number"
                          {...field}
                          value={field.value}
                          onChange={(e) => {
                            field.onChange(Number(e.target.value));
                            handleFieldChange();
                          }}
                          className="max-w-[200px]"
                        />
                        <span className="text-sm text-muted-foreground">元</span>
                      </div>
                    </FormControl>
                    <FormDescription className="flex items-center gap-2">
                      <Info className="h-3 w-3" />
                      <span>
                        当前阈值: {formatCurrency(currentValues.largeTopupThreshold)}，
                        超过此金额需 CEO 审批
                      </span>
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* 审批规则说明 */}
              <div className="p-4 bg-muted rounded-lg">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                  <div className="text-sm space-y-2">
                    <p className="font-medium">审批规则说明</p>
                    <ul className="space-y-1 text-muted-foreground">
                      <li>
                        - 充值金额 ≤ {formatCurrency(currentValues.largeTopupThreshold)}：
                        <Badge variant="secondary" className="ml-1">财务审批</Badge>
                      </li>
                      <li>
                        - 充值金额 &gt; {formatCurrency(currentValues.largeTopupThreshold)}：
                        <Badge variant="default" className="ml-1">CEO 审批</Badge>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 余额预警配置 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Bell className="h-4 w-4" />
                余额预警配置
              </CardTitle>
              <CardDescription>
                配置账户低余额预警阈值和提醒时间
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="lowBalanceThreshold"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>低余额预警阈值</FormLabel>
                      <FormControl>
                        <div className="flex items-center gap-2">
                          <DollarSign className="h-4 w-4 text-muted-foreground" />
                          <Input
                            type="number"
                            {...field}
                            value={field.value}
                            onChange={(e) => {
                              field.onChange(Number(e.target.value));
                              handleFieldChange();
                            }}
                          />
                          <span className="text-sm text-muted-foreground">元</span>
                        </div>
                      </FormControl>
                      <FormDescription>
                        账户余额低于此值时发送预警通知
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="topupReminderDays"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>充值提醒提前天数</FormLabel>
                      <FormControl>
                        <div className="flex items-center gap-2">
                          <Input
                            type="number"
                            {...field}
                            value={field.value}
                            onChange={(e) => {
                              field.onChange(Number(e.target.value));
                              handleFieldChange();
                            }}
                          />
                          <span className="text-sm text-muted-foreground">天</span>
                        </div>
                      </FormControl>
                      <FormDescription>
                        预计余额不足时提前提醒的天数
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              {/* 预警示例 */}
              <div className="p-4 bg-amber-50 dark:bg-amber-950/20 rounded-lg border border-amber-200 dark:border-amber-800">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="h-5 w-5 text-amber-500 mt-0.5 flex-shrink-0" />
                  <div className="text-sm space-y-2">
                    <p className="font-medium text-amber-800 dark:text-amber-200">
                      预警触发条件
                    </p>
                    <ul className="space-y-1 text-amber-700 dark:text-amber-300">
                      <li>
                        - 当账户可用余额 ≤ {formatCurrency(currentValues.lowBalanceThreshold)} 时触发预警
                      </li>
                      <li>
                        - 根据消耗速度预测，提前 {currentValues.topupReminderDays} 天发送充值提醒
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 操作按钮 */}
          <div className="flex justify-between">
            <Button type="button" variant="outline" onClick={handleReset}>
              重置为默认值
            </Button>
            <Button type="submit" disabled={isSaving}>
              {isSaving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  保存中...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  保存阈值配置
                </>
              )}
            </Button>
          </div>
        </form>
      </Form>

      {/* 确认弹窗 */}
      <AlertDialog open={showConfirm} onOpenChange={setShowConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              确认修改阈值配置
            </AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="space-y-4">
                <p>您确定要修改充值阈值配置吗？此操作将影响：</p>

                {pendingValues && (
                  <div className="p-4 bg-muted rounded-lg space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">大额充值阈值:</span>
                      <span className="font-medium">
                        {formatCurrency(pendingValues.largeTopupThreshold)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">低余额预警阈值:</span>
                      <span className="font-medium">
                        {formatCurrency(pendingValues.lowBalanceThreshold)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">提前提醒天数:</span>
                      <span className="font-medium">{pendingValues.topupReminderDays} 天</span>
                    </div>
                  </div>
                )}

                <ul className="space-y-1 text-sm text-muted-foreground">
                  <li>- 新的充值申请将使用新阈值判断审批流程</li>
                  <li>- 余额预警将按新阈值触发通知</li>
                  <li>- 已提交的充值申请不受影响</li>
                </ul>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCancelSave}>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmSave}>确认修改</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

export default TopupThresholdSettings;
