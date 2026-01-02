/**
 * Settlement Rule Dialog Component
 *
 * Create/Edit dialog for settlement rules
 * Supports tiered and markup pricing configurations
 *
 * SoT: DATA_SCHEMA.md v5.6 §3.5.7 (settlement_rules entity)
 * SoT: BR-PROJ.md v1.0 (定价规则)
 * SoT: BR-PROJ-002 - rule_type 不可修改
 */

'use client';

import { useEffect } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { Plus, Trash2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useCreateSettlementRule, useUpdateSettlementRule } from '../hooks';
import {
  type SettlementRule,
  type SettlementRuleType,
  type MarkupType,
  RULE_TYPE_CONFIG,
  MARKUP_TYPE_CONFIG,
  isTieredConfig,
  isMarkupConfig,
} from '../types';

// === Validation Schema ===

const tierSchema = z.object({
  min: z.number().min(0, '起始数量不能为负'),
  max: z.number().nullable(),
  unit_price: z.number().min(0.01, '单价必须大于 0'),
});

const formSchema = z
  .object({
    name: z.string().min(1, '规则名称不能为空').max(100, '规则名称不能超过100字符'),
    rule_type: z.enum(['tiered', 'markup']),
    effective_from: z.string().min(1, '生效开始日不能为空'),
    effective_to: z.string().optional(),
    // Tiered config
    tiers: z.array(tierSchema).optional(),
    // Markup config
    markup_type: z.enum(['percentage', 'fixed']).optional(),
    markup_value: z.number().optional(),
  })
  .refine(
    (data) => {
      if (data.rule_type === 'tiered') {
        return data.tiers && data.tiers.length > 0;
      }
      return true;
    },
    { message: '阶梯规则至少需要一个阶梯', path: ['tiers'] }
  )
  .refine(
    (data) => {
      if (data.rule_type === 'markup') {
        return data.markup_type && data.markup_value !== undefined && data.markup_value > 0;
      }
      return true;
    },
    { message: '加成规则需要设置加成类型和加成值', path: ['markup_value'] }
  );

type FormValues = z.infer<typeof formSchema>;

// === Component ===

interface SettlementRuleDialogProps {
  rule?: SettlementRule | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SettlementRuleDialog({ rule, open, onOpenChange }: SettlementRuleDialogProps) {
  const isEdit = !!rule;

  const createMutation = useCreateSettlementRule({
    onSuccess: () => {
      toast.success('创建成功');
      onOpenChange(false);
    },
    onError: (error) => {
      toast.error(error.message || '创建失败');
    },
  });

  const updateMutation = useUpdateSettlementRule({
    onSuccess: () => {
      toast.success('更新成功');
      onOpenChange(false);
    },
    onError: (error) => {
      toast.error(error.message || '更新失败');
    },
  });

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
      rule_type: 'tiered',
      effective_from: new Date().toISOString().split('T')[0],
      effective_to: '',
      tiers: [{ min: 0, max: null, unit_price: 100 }],
      markup_type: 'percentage',
      markup_value: 10,
    },
  });

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: 'tiers',
  });

  const ruleType = form.watch('rule_type');
  const markupType = form.watch('markup_type');

  // Reset form when rule changes
  useEffect(() => {
    if (rule) {
      const baseValues = {
        name: rule.name,
        rule_type: rule.rule_type as SettlementRuleType,
        effective_from: rule.effective_from,
        effective_to: rule.effective_to || '',
      };

      if (isTieredConfig(rule.config)) {
        form.reset({
          ...baseValues,
          tiers: rule.config.tiers,
          markup_type: 'percentage',
          markup_value: 10,
        });
      } else if (isMarkupConfig(rule.config)) {
        form.reset({
          ...baseValues,
          tiers: [{ min: 0, max: null, unit_price: 100 }],
          markup_type: rule.config.markup_type as MarkupType,
          markup_value: rule.config.markup_value,
        });
      }
    } else {
      form.reset({
        name: '',
        rule_type: 'tiered',
        effective_from: new Date().toISOString().split('T')[0],
        effective_to: '',
        tiers: [{ min: 0, max: null, unit_price: 100 }],
        markup_type: 'percentage',
        markup_value: 10,
      });
    }
  }, [rule, form]);

  const onSubmit = (values: FormValues) => {
    // Build config based on rule type
    const config =
      values.rule_type === 'tiered'
        ? { tiers: values.tiers || [] }
        : {
            markup_type: values.markup_type as MarkupType,
            markup_value: values.markup_value || 0,
          };

    const input = {
      name: values.name,
      rule_type: values.rule_type as SettlementRuleType,
      config,
      effective_from: values.effective_from,
      effective_to: values.effective_to || null,
    };

    if (isEdit && rule) {
      // BR-PROJ-002: rule_type cannot be changed
      const updateInput = {
        name: values.name,
        config,
        effective_to: values.effective_to || null,
      };
      updateMutation.mutate({ id: rule.id, input: updateInput });
    } else {
      createMutation.mutate(input);
    }
  };

  const addTier = () => {
    const lastTier = fields[fields.length - 1];
    const newMin = lastTier?.max ? lastTier.max + 1 : 0;
    append({ min: newMin, max: null, unit_price: 100 });
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEdit ? '编辑定价规则' : '新建定价规则'}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? '修改规则配置和生效日期。规则类型创建后不可修改。'
              : '创建新的定价规则，选择阶梯计价或加成计价模式。'}
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>规则名称 *</FormLabel>
                    <FormControl>
                      <Input placeholder="例如：标准阶梯定价" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="rule_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>规则类型 *</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value}
                      disabled={isEdit} // BR-PROJ-002
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="选择规则类型" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {Object.entries(RULE_TYPE_CONFIG).map(([key, config]) => (
                          <SelectItem key={key} value={key}>
                            {config.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {isEdit && (
                      <FormDescription className="text-orange-600">
                        规则类型创建后不可修改
                      </FormDescription>
                    )}
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Effective Dates */}
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="effective_from"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>生效开始日 *</FormLabel>
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
                    <FormLabel>生效结束日</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormDescription>留空表示永久生效</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Tiered Config */}
            {ruleType === 'tiered' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium">阶梯配置</h3>
                  <Button type="button" variant="outline" size="sm" onClick={addTier}>
                    <Plus className="mr-1 h-4 w-4" />
                    添加阶梯
                  </Button>
                </div>

                <div className="space-y-3">
                  {fields.map((field, index) => (
                    <div
                      key={field.id}
                      className="grid grid-cols-[1fr_1fr_1fr_auto] gap-3 items-end p-3 border rounded-md bg-muted/30"
                    >
                      <FormField
                        control={form.control}
                        name={`tiers.${index}.min`}
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel className="text-xs">起始数量</FormLabel>
                            <FormControl>
                              <Input
                                type="number"
                                min="0"
                                {...field}
                                onChange={(e) => field.onChange(parseInt(e.target.value) || 0)}
                              />
                            </FormControl>
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name={`tiers.${index}.max`}
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel className="text-xs">结束数量</FormLabel>
                            <FormControl>
                              <Input
                                type="number"
                                min="0"
                                placeholder="无上限"
                                value={field.value ?? ''}
                                onChange={(e) =>
                                  field.onChange(e.target.value ? parseInt(e.target.value) : null)
                                }
                              />
                            </FormControl>
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name={`tiers.${index}.unit_price`}
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel className="text-xs">单价 (¥/粉)</FormLabel>
                            <FormControl>
                              <Input
                                type="number"
                                min="0"
                                step="0.01"
                                {...field}
                                onChange={(e) => field.onChange(parseFloat(e.target.value) || 0)}
                              />
                            </FormControl>
                          </FormItem>
                        )}
                      />

                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={() => remove(index)}
                        disabled={fields.length <= 1}
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>

                <p className="text-xs text-muted-foreground">
                  阶梯计价采用累计方式计算，例如 34 个粉 = 15 × ¥100 + 15 × ¥120 + 4 × ¥130
                </p>
              </div>
            )}

            {/* Markup Config */}
            {ruleType === 'markup' && (
              <div className="space-y-4">
                <h3 className="text-sm font-medium">加成配置</h3>

                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="markup_type"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>加成类型 *</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="选择加成类型" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {Object.entries(MARKUP_TYPE_CONFIG).map(([key, config]) => (
                              <SelectItem key={key} value={key}>
                                {config.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="markup_value"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>加成值 ({markupType === 'percentage' ? '%' : '¥'}) *</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            min="0"
                            step={markupType === 'percentage' ? '0.1' : '0.01'}
                            {...field}
                            onChange={(e) => field.onChange(parseFloat(e.target.value) || 0)}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <p className="text-xs text-muted-foreground">
                  加成计价公式: 收入 = 广告消耗 × (1 +{' '}
                  {markupType === 'percentage' ? '加成比例' : '固定金额/消耗'})
                </p>
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end gap-2 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isPending}
              >
                取消
              </Button>
              <Button type="submit" disabled={isPending}>
                {isPending ? '保存中...' : '保存'}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
