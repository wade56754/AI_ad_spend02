'use client';

/**
 * Commission Rule Dialog - 提成规则创建/编辑弹窗
 *
 * TASK-PRJ-003: 提成配置
 */

import { useEffect } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Plus, Trash2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCreateCommissionRule, useUpdateCommissionRule } from '../hooks';
import type { CommissionRule } from '../types';

// ========== Form Schema ==========

const tierSchema = z.object({
  min: z.coerce.number().int().min(1, '最小值必须 >= 1'),
  max: z.coerce.number().int().nullable(),
  rate: z.coerce.number().min(0.01, '费率必须 > 0'),
});

const formSchema = z.object({
  name: z.string().min(1, '规则名称不能为空').max(100, '规则名称不能超过 100 字符'),
  effective_from: z.string().min(1, '生效开始日期不能为空'),
  effective_to: z.string().nullable(),
  is_default: z.boolean(),
  tiers: z.array(tierSchema).min(1, '至少需要一个阶梯'),
});

type FormValues = z.infer<typeof formSchema>;

// ========== Props ==========

interface CommissionRuleDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  rule: CommissionRule | null;
}

// ========== Component ==========

export function CommissionRuleDialog({ open, onOpenChange, rule }: CommissionRuleDialogProps) {
  const isEditing = !!rule;

  const createMutation = useCreateCommissionRule();
  const updateMutation = useUpdateCommissionRule();

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
      effective_from: new Date().toISOString().split('T')[0],
      effective_to: null,
      is_default: false,
      tiers: [{ min: 1, max: null, rate: 1 }],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: 'tiers',
  });

  // Reset form when rule changes
  useEffect(() => {
    if (rule) {
      form.reset({
        name: rule.name,
        effective_from: rule.effective_from,
        effective_to: rule.effective_to,
        is_default: rule.is_default,
        tiers: rule.config.tiers.map((tier) => ({
          min: tier.min,
          max: tier.max,
          rate: tier.rate,
        })),
      });
    } else {
      form.reset({
        name: '',
        effective_from: new Date().toISOString().split('T')[0],
        effective_to: null,
        is_default: false,
        tiers: [{ min: 1, max: null, rate: 1 }],
      });
    }
  }, [rule, form]);

  const onSubmit = (values: FormValues) => {
    // Sort tiers by min and auto-fill max values
    const sortedTiers = [...values.tiers].sort((a, b) => a.min - b.min);
    const processedTiers = sortedTiers.map((tier, index) => ({
      min: tier.min,
      max: index < sortedTiers.length - 1 ? sortedTiers[index + 1].min - 1 : null,
      rate: tier.rate,
    }));

    const payload = {
      name: values.name,
      config: { tiers: processedTiers },
      effective_from: values.effective_from,
      effective_to: values.effective_to || null,
      is_default: values.is_default,
    };

    if (isEditing) {
      updateMutation.mutate(
        { id: rule.id, input: payload },
        {
          onSuccess: () => onOpenChange(false),
        }
      );
    } else {
      createMutation.mutate(payload, {
        onSuccess: () => onOpenChange(false),
      });
    }
  };

  const addTier = () => {
    const lastTier = fields[fields.length - 1];
    const lastMax = form.getValues(`tiers.${fields.length - 1}.max`);
    const newMin = lastMax
      ? lastMax + 1
      : lastTier
        ? form.getValues(`tiers.${fields.length - 1}.min`) + 50
        : 1;
    append({ min: newMin, max: null, rate: 1 });
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEditing ? '编辑提成规则' : '新建提成规则'}</DialogTitle>
          <DialogDescription>
            配置阶梯提成规则。提成按阶梯累加计算：每个阶梯内的进粉数 × 该阶梯费率
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Basic Info */}
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem className="sm:col-span-2">
                    <FormLabel>规则名称</FormLabel>
                    <FormControl>
                      <Input placeholder="如：标准提成规则" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="effective_from"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>生效开始日期</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="effective_to"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>生效结束日期</FormLabel>
                    <FormControl>
                      <Input
                        type="date"
                        {...field}
                        value={field.value ?? ''}
                        onChange={(e) => field.onChange(e.target.value || null)}
                      />
                    </FormControl>
                    <FormDescription>留空表示永久有效</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="is_default"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3 sm:col-span-2">
                    <div className="space-y-0.5">
                      <FormLabel>设为默认规则</FormLabel>
                      <FormDescription>默认规则将自动应用于未指定规则的项目</FormDescription>
                    </div>
                    <FormControl>
                      <Switch checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
                  </FormItem>
                )}
              />
            </div>

            {/* Tier Configuration */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center justify-between">
                  <span>阶梯配置</span>
                  <Button type="button" variant="outline" size="sm" onClick={addTier}>
                    <Plus className="mr-1 h-4 w-4" />
                    添加阶梯
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {fields.map((field, index) => (
                  <div
                    key={field.id}
                    className="grid gap-3 sm:grid-cols-[1fr_1fr_1fr_auto] items-start border rounded-lg p-3"
                  >
                    <FormField
                      control={form.control}
                      name={`tiers.${index}.min`}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-xs">最小进粉数</FormLabel>
                          <FormControl>
                            <Input type="number" min={1} {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name={`tiers.${index}.max`}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-xs">最大进粉数</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              placeholder="无上限"
                              {...field}
                              value={field.value ?? ''}
                              onChange={(e) =>
                                field.onChange(e.target.value ? Number(e.target.value) : null)
                              }
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name={`tiers.${index}.rate`}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-xs">单价 (¥/粉)</FormLabel>
                          <FormControl>
                            <Input type="number" step="0.01" min={0.01} {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <div className="pt-6">
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={() => remove(index)}
                        disabled={fields.length === 1}
                        className="text-muted-foreground hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}

                {form.formState.errors.tiers?.message && (
                  <p className="text-sm text-destructive">{form.formState.errors.tiers.message}</p>
                )}
              </CardContent>
            </Card>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                取消
              </Button>
              <Button type="submit" disabled={isPending}>
                {isPending ? '保存中...' : isEditing ? '保存修改' : '创建规则'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
