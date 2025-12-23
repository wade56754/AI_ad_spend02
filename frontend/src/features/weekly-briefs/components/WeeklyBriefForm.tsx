/**
 * Weekly Brief Form Component
 *
 * Form for creating and editing weekly briefs
 * SoT: B3-weekly-brief.md §3.2, §7
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { format } from 'date-fns';
import {
  ArrowLeft,
  Save,
  Send,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  Target,
  Loader2,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import { LoadingState, ErrorState } from '@/components/ui/data-state';

import { WeekPicker, getWeekStart, getWeekLabel } from './WeekPicker';
import { WeeklyBriefStatusBadge } from './WeeklyBriefStatusBadge';
import {
  useWeeklyBriefDetail,
  useProjectWeeklySummary,
  useCreateWeeklyBrief,
  useUpdateWeeklyBrief,
  useSubmitWeeklyBrief,
} from '../hooks';
import { useProjects } from '@/features/projects/hooks';
import type { WeeklyBrief, WeeklySummary } from '../types';

// Form schema
const weeklyBriefFormSchema = z.object({
  project_id: z.number().min(1, '请选择项目'),
  week_start: z.string().min(1, '请选择周次'),
  achievements: z.string().optional(),
  issues: z.string().optional(),
  solutions: z.string().optional(),
  next_week_plan: z.string().optional(),
});

type WeeklyBriefFormValues = z.infer<typeof weeklyBriefFormSchema>;

// Format currency
function formatCurrency(amount: number): string {
  if (amount >= 10000) {
    return `¥${(amount / 10000).toFixed(2)}万`;
  }
  return `¥${amount.toLocaleString('zh-CN', { maximumFractionDigits: 2 })}`;
}

// Format CPL
function formatCPL(cpl: number | null | undefined): string {
  if (cpl === null || cpl === undefined || cpl === 0) return '--';
  return `¥${cpl.toFixed(2)}`;
}

// Trend indicator component
function TrendIndicator({
  value,
  invertColors = false,
}: {
  value: number | null | undefined;
  invertColors?: boolean;
}) {
  if (value === null || value === undefined) return <span className="text-muted-foreground">--</span>;

  const isPositive = value >= 0;
  // For CPL, negative is good (invertColors=true)
  const isGood = invertColors ? !isPositive : isPositive;

  return (
    <span
      className={`inline-flex items-center text-sm ${
        isGood ? 'text-green-600' : 'text-red-600'
      }`}
    >
      {isPositive ? (
        <TrendingUp className="h-4 w-4 mr-1" />
      ) : (
        <TrendingDown className="h-4 w-4 mr-1" />
      )}
      {isPositive ? '+' : ''}
      {value.toFixed(1)}% vs 上周
    </span>
  );
}

// Summary card component
function SummaryCard({
  summary,
  isLoading,
}: {
  summary?: WeeklySummary | null;
  isLoading?: boolean;
}) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">周数据汇总</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!summary) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">周数据汇总</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-4">
            选择项目和周次后自动汇总
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">周数据汇总 (自动计算)</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-6">
          {/* Weekly Spend */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-muted-foreground">
              <DollarSign className="h-4 w-4" />
              <span className="text-sm">周消耗</span>
            </div>
            <div className="text-2xl font-bold">
              {formatCurrency(summary.weekly_spend)}
            </div>
            <TrendIndicator value={summary.trends?.spend_change} />
          </div>

          {/* Weekly Conversions */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Users className="h-4 w-4" />
              <span className="text-sm">周进粉</span>
            </div>
            <div className="text-2xl font-bold">
              {summary.weekly_conversions.toLocaleString()}
            </div>
            <TrendIndicator value={summary.trends?.conversions_change} />
          </div>

          {/* Weekly CPL */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Target className="h-4 w-4" />
              <span className="text-sm">周 CPL</span>
            </div>
            <div className="text-2xl font-bold">{formatCPL(summary.weekly_cpl)}</div>
            <TrendIndicator value={summary.trends?.cpl_change} invertColors />
            {summary.target_cpl && (
              <div className="text-xs text-muted-foreground">
                目标: {formatCPL(summary.target_cpl)}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface WeeklyBriefFormProps {
  briefId?: number;
  mode?: 'create' | 'edit' | 'view';
}

export function WeeklyBriefForm({ briefId, mode = 'create' }: WeeklyBriefFormProps) {
  const router = useRouter();

  const isEditMode = mode === 'edit' && briefId;
  const isViewMode = mode === 'view';
  const isCreateMode = mode === 'create';

  // State
  const [selectedWeek, setSelectedWeek] = useState<Date>(() => getWeekStart(new Date()));
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);

  // Data hooks
  const {
    data: existingBrief,
    isLoading: isLoadingBrief,
    error: briefError,
  } = useWeeklyBriefDetail(briefId || 0, { enabled: !!briefId });

  const { data: projectsData } = useProjects({});

  const {
    data: weeklySummary,
    isLoading: isLoadingSummary,
  } = useProjectWeeklySummary(
    selectedProjectId || 0,
    format(selectedWeek, 'yyyy-MM-dd'),
    { enabled: !!selectedProjectId }
  );

  // Mutations
  const createMutation = useCreateWeeklyBrief();
  const updateMutation = useUpdateWeeklyBrief();
  const submitMutation = useSubmitWeeklyBrief();

  // Form
  const form = useForm<WeeklyBriefFormValues>({
    resolver: zodResolver(weeklyBriefFormSchema),
    defaultValues: {
      project_id: 0,
      week_start: format(selectedWeek, 'yyyy-MM-dd'),
      achievements: '',
      issues: '',
      solutions: '',
      next_week_plan: '',
    },
  });

  // Sync form with existing brief
  useEffect(() => {
    if (existingBrief) {
      form.reset({
        project_id: existingBrief.project_id,
        week_start: existingBrief.week_start,
        achievements: existingBrief.achievements || '',
        issues: existingBrief.issues || '',
        solutions: existingBrief.solutions || '',
        next_week_plan: existingBrief.next_week_plan || '',
      });
      setSelectedProjectId(existingBrief.project_id);
      setSelectedWeek(getWeekStart(new Date(existingBrief.week_start)));
    }
  }, [existingBrief, form]);

  // Handle project change
  const handleProjectChange = (projectId: string) => {
    const id = parseInt(projectId, 10);
    setSelectedProjectId(id);
    form.setValue('project_id', id);
  };

  // Handle week change
  const handleWeekChange = (date: Date) => {
    setSelectedWeek(date);
    form.setValue('week_start', format(date, 'yyyy-MM-dd'));
  };

  // Handle save (create or update)
  const handleSave = async (data: WeeklyBriefFormValues) => {
    try {
      if (isEditMode && briefId) {
        await updateMutation.mutateAsync({
          id: briefId,
          data: {
            achievements: data.achievements,
            issues: data.issues,
            solutions: data.solutions,
            next_week_plan: data.next_week_plan,
          },
        });
        toast.success('周报已更新');
      } else {
        await createMutation.mutateAsync({
          project_id: data.project_id,
          week_start: data.week_start,
          achievements: data.achievements,
          issues: data.issues,
          solutions: data.solutions,
          next_week_plan: data.next_week_plan,
        });
        toast.success('周报已保存为草稿');
        router.push('/weekly-briefs');
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '保存失败，请稍后重试');
    }
  };

  // Handle submit
  const handleSubmit = async () => {
    if (!briefId && !existingBrief?.id) {
      // Create first, then submit
      const data = form.getValues();
      try {
        const created = await createMutation.mutateAsync({
          project_id: data.project_id,
          week_start: data.week_start,
          achievements: data.achievements,
          issues: data.issues,
          solutions: data.solutions,
          next_week_plan: data.next_week_plan,
        });
        await submitMutation.mutateAsync(created.id);
        toast.success('周报已提交');
        router.push('/weekly-briefs');
      } catch (error) {
        toast.error(error instanceof Error ? error.message : '提交失败，请稍后重试');
      }
    } else {
      // Update then submit
      const id = briefId || existingBrief!.id;
      try {
        const data = form.getValues();
        await updateMutation.mutateAsync({
          id,
          data: {
            achievements: data.achievements,
            issues: data.issues,
            solutions: data.solutions,
            next_week_plan: data.next_week_plan,
          },
        });
        await submitMutation.mutateAsync(id);
        toast.success('周报已提交');
        router.push('/weekly-briefs');
      } catch (error) {
        toast.error(error instanceof Error ? error.message : '提交失败，请稍后重试');
      }
    }
  };

  // Loading state for edit mode
  if (isEditMode && isLoadingBrief) {
    return <LoadingState />;
  }

  // Error state
  if (briefError) {
    return <ErrorState error={briefError} onRetry={() => router.back()} />;
  }

  // Check if submitted (view only)
  const isSubmitted = existingBrief?.status === 'submitted';
  const isReadOnly = isViewMode || isSubmitted;

  const isSaving = createMutation.isPending || updateMutation.isPending;
  const isSubmitting = submitMutation.isPending;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="icon" onClick={() => router.back()}>
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {isCreateMode
                    ? '创建周报'
                    : existingBrief?.project_name
                    ? `${existingBrief.project_name} - ${getWeekLabel(
                        new Date(existingBrief.week_start)
                      )}周报`
                    : '编辑周报'}
                </h1>
                {existingBrief && (
                  <div className="mt-1 flex items-center gap-2">
                    <WeeklyBriefStatusBadge status={existingBrief.status} size="sm" />
                  </div>
                )}
              </div>
            </div>

            {!isReadOnly && (
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={form.handleSubmit(handleSave)}
                  disabled={isSaving || isSubmitting}
                >
                  {isSaving ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4 mr-2" />
                  )}
                  保存草稿
                </Button>
                <Button
                  onClick={handleSubmit}
                  disabled={isSaving || isSubmitting}
                >
                  {isSubmitting ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4 mr-2" />
                  )}
                  提交周报
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <main className="px-4 sm:px-6 lg:px-8 py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Project & Week Selection (only for create) */}
          {isCreateMode && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">基本信息</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">项目</label>
                    <Select
                      value={selectedProjectId ? String(selectedProjectId) : ''}
                      onValueChange={handleProjectChange}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="选择项目" />
                      </SelectTrigger>
                      <SelectContent>
                        {projectsData?.data?.map((project) => (
                          <SelectItem key={project.id} value={String(project.id)}>
                            {project.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">周次</label>
                    <WeekPicker value={selectedWeek} onChange={handleWeekChange} />
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Summary Card */}
          <SummaryCard
            summary={weeklySummary || (existingBrief ? {
              project_id: existingBrief.project_id,
              project_name: existingBrief.project_name || '',
              week_start: existingBrief.week_start,
              week_end: existingBrief.week_end,
              weekly_spend: existingBrief.weekly_spend,
              weekly_conversions: existingBrief.weekly_conversions,
              weekly_cpl: existingBrief.weekly_cpl,
              trends: existingBrief.cpl_trend ? {
                spend_change: 0,
                conversions_change: 0,
                cpl_change: existingBrief.cpl_trend,
              } : null,
            } : null)}
            isLoading={isLoadingSummary}
          />

          {/* Form */}
          <Form {...form}>
            <form className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">周报内容</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Achievements */}
                  <FormField
                    control={form.control}
                    name="achievements"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>本周成果</FormLabel>
                        <FormControl>
                          <Textarea
                            placeholder="1. 完成抖音渠道新账户测试，CPL 达标&#10;2. 优化落地页，转化率提升 5%&#10;3. ..."
                            className="min-h-[120px]"
                            disabled={isReadOnly}
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/* Issues */}
                  <FormField
                    control={form.control}
                    name="issues"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>遇到问题</FormLabel>
                        <FormControl>
                          <Textarea
                            placeholder="1. 快手渠道审核变严，过审率下降&#10;2. 周末流量波动较大&#10;3. ..."
                            className="min-h-[120px]"
                            disabled={isReadOnly}
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/* Solutions */}
                  <FormField
                    control={form.control}
                    name="solutions"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>解决方案</FormLabel>
                        <FormControl>
                          <Textarea
                            placeholder="1. 调整素材风格，预计下周过审率恢复&#10;2. 周末降低预算，避免无效消耗&#10;3. ..."
                            className="min-h-[120px]"
                            disabled={isReadOnly}
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/* Next Week Plan */}
                  <FormField
                    control={form.control}
                    name="next_week_plan"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>下周计划</FormLabel>
                        <FormControl>
                          <Textarea
                            placeholder="1. 测试视频号渠道&#10;2. 提升日均消耗到 25,000&#10;3. CPL 目标控制在 35 以内&#10;..."
                            className="min-h-[120px]"
                            disabled={isReadOnly}
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>
            </form>
          </Form>
        </div>
      </main>
    </div>
  );
}

export default WeeklyBriefForm;
