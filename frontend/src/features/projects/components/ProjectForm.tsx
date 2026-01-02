/**
 * Project Form Component
 *
 * Create/Edit project form with validation
 *
 * SoT 对齐:
 * - DATA_SCHEMA.md v5.6 (projects entity)
 * - BR-PROJ.md v1.0 (定价规则)
 * - BR-PROJ-002: settlement_type 不可修改
 */

'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
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
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useCreateProject, useUpdateProject } from '../hooks';
import { useEffectiveSettlementRules } from '@/features/settlement-rules';
import { useCommissionRules } from '@/features/commission-rules';
import type { Project, ProjectCreateInput, SettlementType } from '../types';
import { SETTLEMENT_TYPE_CONFIG } from '../types';

const projectSchema = z
  .object({
    name: z.string().min(1, '项目名称不能为空').max(200),
    client_name: z.string().min(1, '客户名称不能为空').max(200),
    client_company: z.string().min(1, '客户公司不能为空').max(200),
    description: z.string().max(1000).optional(),
    budget: z.number().min(0, '预算不能为负').optional(),
    currency: z.string().min(1, '请选择货币'),
    start_date: z.string().optional(),
    end_date: z.string().optional(),
    // 项目负责人、目标CPL
    owner_id: z.number().optional(),
    target_cpl: z.number().min(0, '目标CPL不能为负').optional(),
    // 结算配置 (BR-PROJ.md v1.0)
    settlement_type: z.enum(['fixed', 'tiered', 'markup']),
    unit_price: z.number().min(0, '单价不能为负').optional(),
    settlement_rules_id: z.number().nullable().optional(),
    // 提成配置 (TASK-PRJ-003)
    commission_rules_id: z.number().nullable().optional(),
  })
  .refine(
    (data) => {
      // BR-PROJ-007: fixed 模式必须有 unit_price > 0
      if (data.settlement_type === 'fixed') {
        return data.unit_price !== undefined && data.unit_price > 0;
      }
      return true;
    },
    { message: '按粉计费模式必须设置单粉价格', path: ['unit_price'] }
  )
  .refine(
    (data) => {
      // tiered/markup 模式需要选择结算规则
      if (data.settlement_type === 'tiered' || data.settlement_type === 'markup') {
        return data.settlement_rules_id !== undefined && data.settlement_rules_id !== null;
      }
      return true;
    },
    { message: '请选择结算规则', path: ['settlement_rules_id'] }
  );

type ProjectFormValues = z.infer<typeof projectSchema>;

interface ProjectFormProps {
  project?: Project | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ProjectForm({ project, open, onOpenChange }: ProjectFormProps) {
  const isEdit = !!project;

  const createMutation = useCreateProject({
    onSuccess: () => onOpenChange(false),
  });

  const updateMutation = useUpdateProject({
    onSuccess: () => onOpenChange(false),
  });

  // 获取生效的结算规则列表
  const { data: effectiveRules = [], isLoading: rulesLoading } = useEffectiveSettlementRules();

  // 获取提成规则列表
  const { data: commissionRulesData, isLoading: commissionRulesLoading } = useCommissionRules({
    limit: 50,
  });
  const commissionRules = commissionRulesData?.data.items ?? [];

  const form = useForm<ProjectFormValues>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      name: '',
      client_name: '',
      client_company: '',
      description: '',
      budget: 0,
      currency: 'CNY',
      owner_id: undefined,
      target_cpl: undefined,
      settlement_type: 'fixed',
      unit_price: undefined,
      settlement_rules_id: null,
      commission_rules_id: null,
    },
  });

  const settlementType = form.watch('settlement_type');

  useEffect(() => {
    if (project) {
      form.reset({
        name: project.name,
        client_name: project.client_name,
        client_company: project.client_company,
        description: project.description || '',
        budget: project.budget,
        currency: project.currency,
        start_date: project.start_date || '',
        end_date: project.end_date || '',
        owner_id: project.owner_id || project.account_manager_id,
        target_cpl: project.target_cpl ?? undefined,
        settlement_type: project.settlement_type || 'fixed',
        unit_price: project.unit_price ?? undefined,
        settlement_rules_id: project.settlement_rules_id ?? null,
        commission_rules_id: project.commission_rules_id ?? null,
      });
    } else {
      form.reset({
        name: '',
        client_name: '',
        client_company: '',
        description: '',
        budget: 0,
        currency: 'CNY',
        owner_id: undefined,
        target_cpl: undefined,
        settlement_type: 'fixed',
        unit_price: undefined,
        settlement_rules_id: null,
        commission_rules_id: null,
      });
    }
  }, [project, form]);

  const onSubmit = (values: ProjectFormValues) => {
    const input: ProjectCreateInput = {
      name: values.name,
      client_name: values.client_name,
      client_company: values.client_company,
      description: values.description,
      budget: values.budget,
      currency: values.currency,
      start_date: values.start_date || undefined,
      end_date: values.end_date || undefined,
      owner_id: values.owner_id,
      target_cpl: values.target_cpl,
      settlement_type: values.settlement_type as SettlementType,
      unit_price: values.settlement_type === 'fixed' ? values.unit_price : undefined,
      settlement_rules_id: values.settlement_type !== 'fixed' ? values.settlement_rules_id : null,
      commission_rules_id: values.commission_rules_id,
    };

    if (isEdit && project) {
      // BR-PROJ-002: settlement_type 不可修改，所以不包含在更新中
      const updateInput = {
        name: values.name,
        client_name: values.client_name,
        client_company: values.client_company,
        description: values.description,
        budget: values.budget,
        start_date: values.start_date || undefined,
        end_date: values.end_date || undefined,
        owner_id: values.owner_id,
        target_cpl: values.target_cpl,
        unit_price: values.settlement_type === 'fixed' ? values.unit_price : undefined,
        settlement_rules_id: values.settlement_type !== 'fixed' ? values.settlement_rules_id : null,
        commission_rules_id: values.commission_rules_id,
      };
      updateMutation.mutate({ id: project.id, input: updateInput });
    } else {
      createMutation.mutate(input);
    }
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  // 根据当前结算类型过滤规则
  const filteredRules = effectiveRules.filter((rule) => {
    if (settlementType === 'tiered') return rule.rule_type === 'tiered';
    if (settlementType === 'markup') return rule.rule_type === 'markup';
    return false;
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEdit ? '编辑项目' : '新建项目'}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? '修改项目信息。结算类型创建后不可修改。'
              : '创建新项目，设置客户信息和结算方式。'}
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>项目名称 *</FormLabel>
                  <FormControl>
                    <Input placeholder="请输入项目名称" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="client_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>客户联系人 *</FormLabel>
                    <FormControl>
                      <Input placeholder="联系人姓名" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="client_company"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>客户公司 *</FormLabel>
                    <FormControl>
                      <Input placeholder="公司名称" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>项目描述</FormLabel>
                  <FormControl>
                    <Textarea placeholder="项目描述（可选）" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="budget"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>预算</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        step="0.01"
                        min="0"
                        {...field}
                        onChange={(e) => field.onChange(parseFloat(e.target.value) || 0)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="currency"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>货币</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="USD">USD</SelectItem>
                        <SelectItem value="CNY">CNY</SelectItem>
                        <SelectItem value="EUR">EUR</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="start_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>开始日期</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="end_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>结束日期</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* 结算配置区域 */}
            <div className="space-y-4 border-t pt-4">
              <h3 className="text-sm font-medium">结算配置</h3>

              <FormField
                control={form.control}
                name="settlement_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>结算类型 *</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value}
                      disabled={isEdit} // BR-PROJ-002
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="选择结算类型" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {Object.entries(SETTLEMENT_TYPE_CONFIG).map(([key, config]) => (
                          <SelectItem key={key} value={key}>
                            {config.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {isEdit && (
                      <FormDescription className="text-orange-600">
                        结算类型创建后不可修改
                      </FormDescription>
                    )}
                    <FormDescription>
                      {SETTLEMENT_TYPE_CONFIG[settlementType as SettlementType]?.description}
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* 按粉计费: 显示单粉价格 */}
              {settlementType === 'fixed' && (
                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="unit_price"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>单粉价格 (¥) *</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            step="0.01"
                            min="0"
                            placeholder="如: 50.00"
                            value={field.value ?? ''}
                            onChange={(e) => {
                              const val = e.target.value;
                              field.onChange(val ? parseFloat(val) : undefined);
                            }}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="target_cpl"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>目标CPL (¥)</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            step="0.01"
                            min="0"
                            placeholder="如: 35.00"
                            value={field.value ?? ''}
                            onChange={(e) => {
                              const val = e.target.value;
                              field.onChange(val ? parseFloat(val) : undefined);
                            }}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              )}

              {/* 阶梯/加成计费: 显示结算规则选择器 */}
              {(settlementType === 'tiered' || settlementType === 'markup') && (
                <FormField
                  control={form.control}
                  name="settlement_rules_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>结算规则 *</FormLabel>
                      <Select
                        onValueChange={(v) => field.onChange(v ? parseInt(v) : null)}
                        value={field.value?.toString() || ''}
                        disabled={rulesLoading}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue
                              placeholder={rulesLoading ? '加载中...' : '选择结算规则'}
                            />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {filteredRules.length === 0 ? (
                            <SelectItem value="__empty__" disabled>
                              暂无可用的{settlementType === 'tiered' ? '阶梯' : '加成'}规则
                            </SelectItem>
                          ) : (
                            filteredRules.map((rule) => (
                              <SelectItem key={rule.id} value={rule.id.toString()}>
                                {rule.name}
                              </SelectItem>
                            ))
                          )}
                        </SelectContent>
                      </Select>
                      <FormDescription>
                        请先在「定价配置」页面创建
                        {settlementType === 'tiered' ? '阶梯' : '加成'}规则
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}

              {/* 非 fixed 模式也显示目标 CPL */}
              {settlementType !== 'fixed' && (
                <FormField
                  control={form.control}
                  name="target_cpl"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>目标CPL (¥)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          step="0.01"
                          min="0"
                          placeholder="如: 35.00"
                          value={field.value ?? ''}
                          onChange={(e) => {
                            const val = e.target.value;
                            field.onChange(val ? parseFloat(val) : undefined);
                          }}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}
            </div>

            {/* 提成配置区域 (TASK-PRJ-003) */}
            <div className="space-y-4 border-t pt-4">
              <h3 className="text-sm font-medium">提成配置</h3>

              <FormField
                control={form.control}
                name="commission_rules_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>提成规则</FormLabel>
                    <Select
                      onValueChange={(v) =>
                        field.onChange(v && v !== '__none__' ? parseInt(v) : null)
                      }
                      value={field.value?.toString() || '__none__'}
                      disabled={commissionRulesLoading}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue
                            placeholder={
                              commissionRulesLoading ? '加载中...' : '选择提成规则（可选）'
                            }
                          />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="__none__">不使用提成规则</SelectItem>
                        {commissionRules.map((rule) => (
                          <SelectItem key={rule.id} value={rule.id.toString()}>
                            {rule.name}
                            {rule.is_default && ' (默认)'}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormDescription>
                      提成规则用于计算投手的提成金额，基于确认进粉数 (conversions_final)
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

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
