/**
 * Resolve Flag Dialog Component
 *
 * Dialog for resolving trend flag anomalies on daily reports
 * SoT: STATE_MACHINE.md v2.6 § 8 (trend_flagged → trend_resolved)
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
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Shield, Loader2, CheckCircle, Edit, XCircle } from 'lucide-react';
import { useResolveFlag } from '../hooks';
import { toast } from 'sonner';
import type { TrendResolveInput } from '../types';

interface ResolveFlagDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  reportId: string;
  onSuccess?: () => void;
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

export function ResolveFlagDialog({
  open,
  onOpenChange,
  reportId,
  onSuccess,
}: ResolveFlagDialogProps) {
  const [action, setAction] = useState<TrendResolveInput['resolution_action']>('accept');
  const [notes, setNotes] = useState('');

  const resolveFlag = useResolveFlag({
    onSuccess: () => {
      toast.success('异常已处理');
      resetForm();
      onOpenChange(false);
      onSuccess?.();
    },
    onError: (error) => {
      toast.error(error.message || '处理失败');
    },
  });

  const resetForm = () => {
    setAction('accept');
    setNotes('');
  };

  const handleSubmit = () => {
    if (!notes.trim()) {
      toast.error('请填写处理说明');
      return;
    }

    const input: TrendResolveInput = {
      resolution_action: action,
      trend_notes: notes,
    };

    resolveFlag.mutate({ id: reportId, input });
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
            <Shield className="h-5 w-5 text-blue-500" />
            处理趋势异常
          </DialogTitle>
          <DialogDescription>
            请选择处理方式并填写处理说明，此操作将解决当前的异常状态。
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-3">
            <Label>处理方式 *</Label>
            <RadioGroup
              value={action}
              onValueChange={(value) => setAction(value as TrendResolveInput['resolution_action'])}
              className="space-y-3"
            >
              {RESOLUTION_ACTIONS.map((option) => {
                const Icon = option.icon;
                return (
                  <div
                    key={option.value}
                    className={`flex items-start space-x-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                      action === option.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => setAction(option.value)}
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
          </div>

          <div className="space-y-2">
            <Label htmlFor="resolve-notes">处理说明 *</Label>
            <Textarea
              id="resolve-notes"
              placeholder="请详细描述处理过程和结果..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={4}
              className="resize-none"
            />
            <p className="text-xs text-muted-foreground">
              最少 10 个字符，请说明处理过程以供审计追溯
            </p>
          </div>
        </div>

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
            type="button"
            onClick={handleSubmit}
            disabled={resolveFlag.isPending || notes.length < 10}
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
      </DialogContent>
    </Dialog>
  );
}

export default ResolveFlagDialog;
