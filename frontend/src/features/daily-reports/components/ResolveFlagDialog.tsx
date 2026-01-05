/**
 * Resolve Flag Dialog Component
 *
 * Dialog for resolving trend flag anomalies on daily reports
 * SoT: STATE_MACHINE.md v2.6 § 8 (trend_flagged → trend_resolved)
 *
 * ⚠️ PHASE 2 COMPONENT
 * This component is only active when enabled=true.
 * In Phase 1, this dialog is disabled (enabled defaults to false).
 */

'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
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
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Shield, Loader2, CheckCircle, Edit, XCircle } from 'lucide-react';
import { useResolveFlag } from '../hooks';
import { toast } from 'sonner';
import type { TrendResolveInput } from '../types';

interface ResolveFlagDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  reportId: string;
  onSuccess?: () => void;
  /** Phase 2 feature flag - set to true to enable this dialog */
  enabled?: boolean;
}

/**
 * Resolution action options
 */
const RESOLUTION_ACTIONS: {
  value: TrendResolveInput['resolution_action'];
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}[] = [
  {
    value: 'accept',
    label: '确认正常',
    description: '数据已核实，异常属于正常波动',
    icon: CheckCircle,
  },
  {
    value: 'adjust',
    label: '调整数据',
    description: '数据已调整修正，可以继续流程',
    icon: Edit,
  },
  {
    value: 'reject',
    label: '拒绝日报',
    description: '数据问题严重，需要重新提交',
    icon: XCircle,
  },
];

// Zod schema for form validation
const resolveFlagSchema = z.object({
  resolution_action: z.enum(['accept', 'adjust', 'reject'], {
    required_error: '请选择处理方式',
  }),
  trend_notes: z
    .string()
    .min(10, '处理说明至少需要10个字符')
    .max(500, '处理说明不能超过500个字符'),
});

type ResolveFlagFormValues = z.infer<typeof resolveFlagSchema>;

export function ResolveFlagDialog({
  open,
  onOpenChange,
  reportId,
  onSuccess,
  enabled = false,
}: ResolveFlagDialogProps) {
  // Phase 1: Dialog is disabled by default
  if (!enabled) {
    return null;
  }

  // Form setup with zod validation
  const form = useForm<ResolveFlagFormValues>({
    resolver: zodResolver(resolveFlagSchema),
    defaultValues: {
      resolution_action: 'accept',
      trend_notes: '',
    },
  });

  // Reset form when dialog opens/closes
  useEffect(() => {
    if (open) {
      form.reset({
        resolution_action: 'accept',
        trend_notes: '',
      });
    }
  }, [open, form]);

  const resolveFlag = useResolveFlag({
    onSuccess: () => {
      toast.success('异常已处理');
      form.reset();
      onOpenChange(false);
      onSuccess?.();
    },
    onError: (error) => {
      toast.error(error.message || '处理失败');
    },
  });

  const onSubmit = (values: ResolveFlagFormValues) => {
    const input: TrendResolveInput = {
      resolution_action: values.resolution_action,
      trend_notes: values.trend_notes,
    };
    resolveFlag.mutate({ id: reportId, input });
  };

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      form.reset();
    }
    onOpenChange(newOpen);
  };

  const selectedAction = form.watch('resolution_action');

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-blue-500" />
            处理趋势异常
          </DialogTitle>
          <DialogDescription>
            请选择处理方式并填写处理说明，此操作将解决当前的异常状态。
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 py-4">
            <FormField
              control={form.control}
              name="resolution_action"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>处理方式 *</FormLabel>
                  <FormControl>
                    <RadioGroup
                      value={field.value}
                      onValueChange={field.onChange}
                      className="space-y-3"
                    >
                      {RESOLUTION_ACTIONS.map((option) => {
                        const Icon = option.icon;
                        return (
                          <div
                            key={option.value}
                            className={`flex items-start space-x-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                              selectedAction === option.value
                                ? 'border-blue-500 bg-blue-50'
                                : 'border-gray-200 hover:border-gray-300'
                            }`}
                            onClick={() => field.onChange(option.value)}
                          >
                            <RadioGroupItem value={option.value} id={option.value} className="mt-1" />
                            <div className="flex-1">
                              <Label
                                htmlFor={option.value}
                                className="flex items-center gap-2 cursor-pointer font-medium"
                              >
                                <Icon className="h-4 w-4" />
                                {option.label}
                              </Label>
                              <p className="text-sm text-muted-foreground mt-1">
                                {option.description}
                              </p>
                            </div>
                          </div>
                        );
                      })}
                    </RadioGroup>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="trend_notes"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>处理说明 *</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="请详细描述处理过程和结果..."
                      {...field}
                      rows={4}
                      className="resize-none"
                    />
                  </FormControl>
                  <p className="text-xs text-muted-foreground">
                    最少 10 个字符，请说明处理过程以供审计追溯
                  </p>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleOpenChange(false)}
                disabled={resolveFlag.isPending}
              >
                取消
              </Button>
              <Button
                type="submit"
                disabled={resolveFlag.isPending}
              >
                {resolveFlag.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    处理中...
                  </>
                ) : (
                  <>
                    <Shield className="mr-2 h-4 w-4" />
                    确认处理
                  </>
                )}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

export default ResolveFlagDialog;
