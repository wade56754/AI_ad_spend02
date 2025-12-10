/**
 * Flag Trend Dialog Component
 *
 * Dialog for flagging trend anomalies on daily reports
 * SoT: STATE_MACHINE.md v2.6 § 8 (trend_pending → trend_flagged)
 */

'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
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
];

export function FlagTrendDialog({
  open,
  onOpenChange,
  reportId,
  onSuccess,
}: FlagTrendDialogProps) {
  const [anomalyType, setAnomalyType] = useState<string>('');
  const [notes, setNotes] = useState('');

  const flagTrend = useFlagTrend({
    onSuccess: () => {
      toast.success('趋势异常已标记');
      resetForm();
      onOpenChange(false);
      onSuccess?.();
    },
    onError: (error) => {
      toast.error(error.message || '标记失败');
    },
  });

  const resetForm = () => {
    setAnomalyType('');
    setNotes('');
  };

  const handleSubmit = () => {
    if (!anomalyType) {
      toast.error('请选择异常类型');
      return;
    }
    if (!notes.trim()) {
      toast.error('请填写异常说明');
      return;
    }

    const fullNotes = `[${ANOMALY_TYPES.find(t => t.value === anomalyType)?.label}] ${notes}`;
    flagTrend.mutate({ id: reportId, notes: fullNotes });
  };

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      resetForm();
    }
    onOpenChange(open);
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

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="anomaly-type">异常类型 *</Label>
            <Select value={anomalyType} onValueChange={setAnomalyType}>
              <SelectTrigger id="anomaly-type">
                <SelectValue placeholder="选择异常类型" />
              </SelectTrigger>
              <SelectContent>
                {ANOMALY_TYPES.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">异常说明 *</Label>
            <Textarea
              id="notes"
              placeholder="请详细描述异常情况，包括发现的问题和可能的原因..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={4}
              className="resize-none"
            />
            <p className="text-xs text-muted-foreground">
              最少 10 个字符，请描述清楚异常情况以便后续处理
            </p>
          </div>
        </div>

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
            type="button"
            variant="default"
            onClick={handleSubmit}
            disabled={flagTrend.isPending || !anomalyType || notes.length < 10}
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
      </DialogContent>
    </Dialog>
  );
}

export default FlagTrendDialog;
