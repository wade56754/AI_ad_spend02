/**
 * Flag Trend Dialog Component
 *
 * Dialog for flagging trend anomalies on daily reports
 * SoT: STATE_MACHINE.md v2.6 § 8 (trend_pending → trend_flagged)
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { AlertTriangle, Loader2 } from 'lucide-react';
import { useFlagTrend } from '../hooks';
import { toast } from 'sonner';

interface FlagTrendDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  reportId: string;
  onSuccess?: () => void;
  /** Phase 2 feature flag - set to true to enable this dialog */
  enabled?: boolean;
}

/**
 * Predefined anomaly types
 */
const ANOMALY_TYPES = [
  { value: 'spend_spike', label: '消耗异常增长' },
  { value: 'spend_drop', label: '消耗异常下降' },
  { value: 'conversion_anomaly', label: '转化率异常' },
  { value: 'impression_anomaly', label: '展示量异常' },
  { value: 'data_mismatch', label: '数据不匹配' },
  { value: 'other', label: '其他异常' },
] as const;

type AnomalyType = (typeof ANOMALY_TYPES)[number]['value'];

// Zod schema for form validation
const flagTrendSchema = z.object({
  anomalyType: z.enum(
    ANOMALY_TYPES.map(t => t.value) as [AnomalyType, ...AnomalyType[]],
    { required_error: '请选择异常类型' }
  ),
  notes: z
    .string()
    .min(10, '异常说明至少需要10个字符')
    .max(500, '异常说明不能超过500个字符'),
});

type FlagTrendFormValues = z.infer<typeof flagTrendSchema>;

export function FlagTrendDialog({
  open,
  onOpenChange,
  reportId,
  onSuccess,
  enabled = false,
}: FlagTrendDialogProps) {
  // Phase 1: Dialog is disabled by default
  if (!enabled) {
    return null;
  }

  // Form setup with zod validation
  const form = useForm<FlagTrendFormValues>({
    resolver: zodResolver(flagTrendSchema),
    defaultValues: {
      anomalyType: undefined,
      notes: '',
    },
  });

  // Reset form when dialog opens/closes
  useEffect(() => {
    if (open) {
      form.reset({
        anomalyType: undefined,
        notes: '',
      });
    }
  }, [open, form]);

  const flagTrend = useFlagTrend({
    onSuccess: () => {
      toast.success('趋势异常已标记');
      form.reset();
      onOpenChange(false);
      onSuccess?.();
    },
    onError: (error) => {
      toast.error(error.message || '标记失败');
    },
  });

  const onSubmit = (values: FlagTrendFormValues) => {
    const typeLabel = ANOMALY_TYPES.find(t => t.value === values.anomalyType)?.label;
    const fullNotes = `[${typeLabel}] ${values.notes}`;
    flagTrend.mutate({ id: reportId, notes: fullNotes });
  };

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      form.reset();
    }
    onOpenChange(newOpen);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            标记趋势异常
          </DialogTitle>
          <DialogDescription>
            请选择异常类型并填写详细说明，此操作将使日报进入异常处理流程。
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 py-4">
            <FormField
              control={form.control}
              name="anomalyType"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>异常类型 *</FormLabel>
                  <Select value={field.value} onValueChange={field.onChange}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="选择异常类型" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {ANOMALY_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
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
              name="notes"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>异常说明 *</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="请详细描述异常情况，包括发现的问题和可能的原因..."
                      {...field}
                      rows={4}
                      className="resize-none"
                    />
                  </FormControl>
                  <p className="text-xs text-muted-foreground">
                    最少 10 个字符，请描述清楚异常情况以便后续处理
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
                disabled={flagTrend.isPending}
              >
                取消
              </Button>
              <Button
                type="submit"
                variant="default"
                disabled={flagTrend.isPending}
                className="bg-amber-600 hover:bg-amber-700"
              >
                {flagTrend.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    提交中...
                  </>
                ) : (
                  <>
                    <AlertTriangle className="mr-2 h-4 w-4" />
                    标记异常
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

export default FlagTrendDialog;
