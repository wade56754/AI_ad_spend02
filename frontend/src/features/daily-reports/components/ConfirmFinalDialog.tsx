/**
 * Confirm Final Dialog Component
 *
 * Dialog for confirming final data on daily reports
 * SoT: STATE_MACHINE.md v2.6 § 8 (final_pending → final_confirmed)
 */

'use client';

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { CheckCircle, Loader2, AlertCircle } from 'lucide-react';
import { useConfirmFinal } from '../hooks';
import { toast } from 'sonner';
import type { DailyReport, FinalConfirmInput } from '../types';
import type { Money } from '@/types/common';

// Helper to extract numeric value from string | number | Money
const getNumericSpend = (value: string | number | Money | undefined | null): number => {
  if (value === undefined || value === null) return 0;
  if (typeof value === 'string') return parseFloat(value) || 0;
  if (typeof value === 'number') return value;
  // Money object
  return value.amount;
};

interface ConfirmFinalDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  report: DailyReport;
  onSuccess?: () => void;
}

export function ConfirmFinalDialog({
  open,
  onOpenChange,
  report,
  onSuccess,
}: ConfirmFinalDialogProps) {
  // Initialize form with raw values
  const [formData, setFormData] = useState<FinalConfirmInput>({
    final_spend: 0,
    final_impressions: 0,
    final_clicks: 0,
    final_conversions: 0,
    confirmation_notes: '',
  });

  // Reset form when dialog opens with report data
  useEffect(() => {
    if (open && report) {
      setFormData({
        final_spend: getNumericSpend(report.raw_spend),
        final_impressions: report.raw_impressions,
        final_clicks: report.raw_clicks,
        final_conversions: report.raw_conversions,
        confirmation_notes: '',
      });
    }
  }, [open, report]);

  const confirmFinal = useConfirmFinal({
    onSuccess: () => {
      toast.success('终审确认成功');
      onOpenChange(false);
      onSuccess?.();
    },
    onError: (error) => {
      toast.error(error.message || '确认失败');
    },
  });

  const handleInputChange = (field: keyof FinalConfirmInput, value: string | number) => {
    setFormData((prev) => ({
      ...prev,
      [field]: typeof value === 'string' && field !== 'confirmation_notes'
        ? parseFloat(value) || 0
        : value,
    }));
  };

  const handleSubmit = () => {
    // Validate required fields
    if (formData.final_spend <= 0) {
      toast.error('消耗金额必须大于 0');
      return;
    }

    confirmFinal.mutate({
      id: report.id,
      input: formData,
    });
  };

  const handleOpenChange = (open: boolean) => {
    onOpenChange(open);
  };

  // Calculate differences
  const spendDiff = formData.final_spend - getNumericSpend(report.raw_spend);
  const impressionsDiff = formData.final_impressions - report.raw_impressions;
  const clicksDiff = formData.final_clicks - report.raw_clicks;
  const conversionsDiff = formData.final_conversions - report.raw_conversions;

  const hasChanges = spendDiff !== 0 || impressionsDiff !== 0 || clicksDiff !== 0 || conversionsDiff !== 0;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            确认终审数据
          </DialogTitle>
          <DialogDescription>
            请核实并确认最终数据。确认后数据将被锁定，无法修改。
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Report Info */}
          <div className="rounded-lg bg-gray-50 p-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">报告日期:</span>
              <span className="font-medium">{report.report_date}</span>
            </div>
          </div>

          <Separator />

          {/* Data Comparison */}
          <div className="space-y-4">
            <h4 className="text-sm font-medium">数据确认</h4>

            {/* Spend */}
            <div className="grid grid-cols-3 gap-4 items-center">
              <div>
                <Label className="text-muted-foreground text-xs">原始消耗</Label>
                <div className="font-medium">
                  ¥{(getNumericSpend(report.raw_spend) / 100).toFixed(2)}
                </div>
              </div>
              <div>
                <Label htmlFor="final_spend">最终消耗 *</Label>
                <Input
                  id="final_spend"
                  type="number"
                  step="0.01"
                  value={formData.final_spend}
                  onChange={(e) => handleInputChange('final_spend', e.target.value)}
                />
              </div>
              <div>
                {spendDiff !== 0 && (
                  <span className={`text-sm ${spendDiff > 0 ? 'text-red-500' : 'text-green-500'}`}>
                    {spendDiff > 0 ? '+' : ''}{spendDiff.toFixed(2)}
                  </span>
                )}
              </div>
            </div>

            {/* Impressions */}
            <div className="grid grid-cols-3 gap-4 items-center">
              <div>
                <Label className="text-muted-foreground text-xs">原始展示</Label>
                <div className="font-medium">{report.raw_impressions.toLocaleString()}</div>
              </div>
              <div>
                <Label htmlFor="final_impressions">最终展示 *</Label>
                <Input
                  id="final_impressions"
                  type="number"
                  value={formData.final_impressions}
                  onChange={(e) => handleInputChange('final_impressions', e.target.value)}
                />
              </div>
              <div>
                {impressionsDiff !== 0 && (
                  <span className={`text-sm ${impressionsDiff > 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {impressionsDiff > 0 ? '+' : ''}{impressionsDiff.toLocaleString()}
                  </span>
                )}
              </div>
            </div>

            {/* Clicks */}
            <div className="grid grid-cols-3 gap-4 items-center">
              <div>
                <Label className="text-muted-foreground text-xs">原始点击</Label>
                <div className="font-medium">{report.raw_clicks.toLocaleString()}</div>
              </div>
              <div>
                <Label htmlFor="final_clicks">最终点击 *</Label>
                <Input
                  id="final_clicks"
                  type="number"
                  value={formData.final_clicks}
                  onChange={(e) => handleInputChange('final_clicks', e.target.value)}
                />
              </div>
              <div>
                {clicksDiff !== 0 && (
                  <span className={`text-sm ${clicksDiff > 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {clicksDiff > 0 ? '+' : ''}{clicksDiff.toLocaleString()}
                  </span>
                )}
              </div>
            </div>

            {/* Conversions */}
            <div className="grid grid-cols-3 gap-4 items-center">
              <div>
                <Label className="text-muted-foreground text-xs">原始转化</Label>
                <div className="font-medium">{report.raw_conversions.toLocaleString()}</div>
              </div>
              <div>
                <Label htmlFor="final_conversions">最终转化 *</Label>
                <Input
                  id="final_conversions"
                  type="number"
                  value={formData.final_conversions}
                  onChange={(e) => handleInputChange('final_conversions', e.target.value)}
                />
              </div>
              <div>
                {conversionsDiff !== 0 && (
                  <span className={`text-sm ${conversionsDiff > 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {conversionsDiff > 0 ? '+' : ''}{conversionsDiff.toLocaleString()}
                  </span>
                )}
              </div>
            </div>
          </div>

          <Separator />

          {/* Change Warning */}
          {hasChanges && (
            <div className="flex items-start gap-2 rounded-lg bg-amber-50 p-3 text-sm text-amber-800">
              <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium">数据有变更</p>
                <p className="text-amber-600">
                  最终数据与原始数据存在差异，请确认是否正确。
                </p>
              </div>
            </div>
          )}

          {/* Notes */}
          <div className="space-y-2">
            <Label htmlFor="confirmation_notes">确认备注</Label>
            <Textarea
              id="confirmation_notes"
              placeholder="可选：添加确认说明..."
              value={formData.confirmation_notes || ''}
              onChange={(e) => handleInputChange('confirmation_notes', e.target.value)}
              rows={3}
              className="resize-none"
            />
          </div>
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={confirmFinal.isPending}
          >
            取消
          </Button>
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={confirmFinal.isPending}
            className="bg-green-600 hover:bg-green-700"
          >
            {confirmFinal.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                确认中...
              </>
            ) : (
              <>
                <CheckCircle className="mr-2 h-4 w-4" />
                确认终审
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default ConfirmFinalDialog;
