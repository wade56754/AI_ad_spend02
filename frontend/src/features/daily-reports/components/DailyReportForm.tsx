"use client";

import React, { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Calculator, Save, X, DollarSign, Users, Target, MapPin, Tv } from "lucide-react";
import { toast } from "sonner";
import { apiPost, apiPut, isApiError } from "@/lib/api";
import {
  DailyReportCreateInput,
  AdPlatform,
  AdRegion,
  Currency,
  PLATFORM_OPTIONS,
  REGION_OPTIONS,
  CURRENCY_OPTIONS,
} from "../types/dailyReport.types";

// 类型定义
interface DailyReportFormData {
  id?: number;
  report_date: string;
  ad_account_id: number;
  raw_spend: number;
  follows_count: number;
  result_count: number;
  region: AdRegion | '';
  platform: AdPlatform | '';
  currency: Currency;
  campaign_name: string;
  ad_group_name: string;
  ad_creative_name: string;
  impressions: number;
  clicks: number;
  notes: string;
}

interface AdAccount {
  id: number;
  name: string;
  platform: string;
  project_name?: string;
}

interface DailyReportFormProps {
  report?: Partial<DailyReportFormData> | null;
  adAccounts: AdAccount[];
  onSuccess: () => void;
  onCancel: () => void;
}

export function DailyReportForm({
  report,
  adAccounts,
  onSuccess,
  onCancel,
}: DailyReportFormProps) {
  const [formData, setFormData] = useState<DailyReportFormData>({
    report_date: report?.report_date || new Date().toISOString().split("T")[0],
    ad_account_id: report?.ad_account_id || 0,
    raw_spend: report?.raw_spend || 0,
    follows_count: report?.follows_count || 0,
    result_count: report?.result_count || 0,
    region: report?.region || '',
    platform: report?.platform || '',
    currency: report?.currency || 'USD',
    campaign_name: report?.campaign_name || "",
    ad_group_name: report?.ad_group_name || "",
    ad_creative_name: report?.ad_creative_name || "",
    impressions: report?.impressions || 0,
    clicks: report?.clicks || 0,
    notes: report?.notes || "",
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // 系统自动计算的指标
  const derivedMetrics = useMemo(() => {
    const costPerFollow = formData.follows_count > 0
      ? formData.raw_spend / formData.follows_count
      : 0;
    const costPerResult = formData.result_count > 0
      ? formData.raw_spend / formData.result_count
      : 0;

    return {
      cost_per_follow: parseFloat(costPerFollow.toFixed(2)),
      cost_per_result: parseFloat(costPerResult.toFixed(2)),
    };
  }, [formData.raw_spend, formData.follows_count, formData.result_count]);

  // 处理输入变化
  const handleInputChange = (
    field: keyof DailyReportFormData,
    value: string | number
  ) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  // 处理数字输入
  const handleNumberChange = (field: keyof DailyReportFormData, value: string) => {
    const numValue = field === 'raw_spend'
      ? parseFloat(value) || 0
      : parseInt(value) || 0;
    handleInputChange(field, numValue);
  };

  // 验证表单
  const validateForm = (): boolean => {
    if (!formData.ad_account_id) {
      toast.error("请选择广告账户");
      return false;
    }
    if (!formData.region) {
      toast.error("请选择投放地区");
      return false;
    }
    if (formData.raw_spend < 0) {
      toast.error("广告消耗不能为负数");
      return false;
    }
    if (formData.follows_count < 0) {
      toast.error("进粉数不能为负数");
      return false;
    }
    if (formData.result_count < 0) {
      toast.error("成效数不能为负数");
      return false;
    }
    return true;
  };

  // 提交表单
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const submitData: DailyReportCreateInput = {
        report_date: formData.report_date,
        ad_account_id: formData.ad_account_id,
        raw_spend: formData.raw_spend,
        follows_count: formData.follows_count,
        result_count: formData.result_count,
        region: formData.region as AdRegion,
        platform: formData.platform as AdPlatform || undefined,
        currency: formData.currency,
        campaign_name: formData.campaign_name || undefined,
        ad_group_name: formData.ad_group_name || undefined,
        ad_creative_name: formData.ad_creative_name || undefined,
        impressions: formData.impressions || undefined,
        clicks: formData.clicks || undefined,
        notes: formData.notes || undefined,
      };

      const endpoint = report?.id
        ? `/api/v1/daily-reports/${report.id}`
        : "/api/v1/daily-reports";

      const response = report?.id
        ? await apiPut<{ data?: unknown }>(endpoint, submitData)
        : await apiPost<{ data?: unknown }>(endpoint, submitData);

      if (response.data) {
        toast.success(report?.id ? "更新成功" : "创建成功");
        onSuccess();
      } else {
        toast.error("操作失败");
      }
    } catch (error) {
      console.error("提交错误:", error);
      if (isApiError(error)) {
        toast.error(error.message || "操作失败");
      } else {
        toast.error("操作失败");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* 基本信息 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="w-5 h-5" />
            日报提交
          </CardTitle>
          <CardDescription>投手每日提交消耗、进粉、成效数据</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 日期和账户 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="report_date">日期 *</Label>
              <Input
                id="report_date"
                type="date"
                value={formData.report_date}
                onChange={(e) => handleInputChange("report_date", e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="ad_account_id">广告账户 *</Label>
              <Select
                value={formData.ad_account_id.toString()}
                onValueChange={(value) => handleInputChange("ad_account_id", parseInt(value))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择广告账户" />
                </SelectTrigger>
                <SelectContent>
                  {adAccounts.map((account) => (
                    <SelectItem key={account.id} value={account.id.toString()}>
                      {account.name} ({account.platform})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* 地区和平台 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="region" className="flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                投放地区 *
              </Label>
              <Select
                value={formData.region}
                onValueChange={(value) => handleInputChange("region", value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择地区" />
                </SelectTrigger>
                <SelectContent>
                  {REGION_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="platform" className="flex items-center gap-1">
                <Tv className="w-4 h-4" />
                广告平台
              </Label>
              <Select
                value={formData.platform}
                onValueChange={(value) => handleInputChange("platform", value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择平台" />
                </SelectTrigger>
                <SelectContent>
                  {PLATFORM_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="currency">货币类型</Label>
              <Select
                value={formData.currency}
                onValueChange={(value) => handleInputChange("currency", value as Currency)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择货币" />
                </SelectTrigger>
                <SelectContent>
                  {CURRENCY_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 核心数据 - 投手提交 */}
      <Card>
        <CardHeader>
          <CardTitle>核心数据</CardTitle>
          <CardDescription>填写今日广告投放的核心指标</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <Label htmlFor="raw_spend" className="flex items-center gap-1">
                <DollarSign className="w-4 h-4" />
                广告消耗 ({formData.currency}) *
              </Label>
              <Input
                id="raw_spend"
                type="number"
                step="0.01"
                value={formData.raw_spend}
                onChange={(e) => handleNumberChange("raw_spend", e.target.value)}
                placeholder="0.00"
                min="0"
                className="text-lg font-semibold"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="follows_count" className="flex items-center gap-1">
                <Users className="w-4 h-4" />
                进粉数 *
              </Label>
              <Input
                id="follows_count"
                type="number"
                value={formData.follows_count}
                onChange={(e) => handleNumberChange("follows_count", e.target.value)}
                placeholder="0"
                min="0"
                className="text-lg font-semibold"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="result_count" className="flex items-center gap-1">
                <Target className="w-4 h-4" />
                成效数 *
              </Label>
              <Input
                id="result_count"
                type="number"
                value={formData.result_count}
                onChange={(e) => handleNumberChange("result_count", e.target.value)}
                placeholder="0"
                min="0"
                className="text-lg font-semibold"
              />
            </div>
          </div>

          {/* 系统计算的指标 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t">
            <div className="space-y-2">
              <Label className="text-muted-foreground flex items-center gap-1">
                <Calculator className="w-4 h-4" />
                单粉成本 (自动计算)
              </Label>
              <Input
                type="text"
                value={`${formData.currency} ${derivedMetrics.cost_per_follow.toFixed(2)}`}
                readOnly
                className="bg-muted font-semibold"
              />
              <p className="text-xs text-muted-foreground">= 广告消耗 / 进粉数</p>
            </div>

            <div className="space-y-2">
              <Label className="text-muted-foreground flex items-center gap-1">
                <Calculator className="w-4 h-4" />
                单次成效费用 (自动计算)
              </Label>
              <Input
                type="text"
                value={`${formData.currency} ${derivedMetrics.cost_per_result.toFixed(2)}`}
                readOnly
                className="bg-muted font-semibold"
              />
              <p className="text-xs text-muted-foreground">= 广告消耗 / 成效数</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 高级选项 (可折叠) */}
      <Card>
        <CardHeader className="cursor-pointer" onClick={() => setShowAdvanced(!showAdvanced)}>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-sm">高级选项</CardTitle>
              <CardDescription>广告系列、展示、点击等详细信息</CardDescription>
            </div>
            <Button type="button" variant="ghost" size="sm">
              {showAdvanced ? "收起" : "展开"}
            </Button>
          </div>
        </CardHeader>
        {showAdvanced && (
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="campaign_name">广告系列名称</Label>
                <Input
                  id="campaign_name"
                  value={formData.campaign_name}
                  onChange={(e) => handleInputChange("campaign_name", e.target.value)}
                  placeholder="输入广告系列名称"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="ad_group_name">广告组名称</Label>
                <Input
                  id="ad_group_name"
                  value={formData.ad_group_name}
                  onChange={(e) => handleInputChange("ad_group_name", e.target.value)}
                  placeholder="输入广告组名称"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="ad_creative_name">广告创意名称</Label>
                <Input
                  id="ad_creative_name"
                  value={formData.ad_creative_name}
                  onChange={(e) => handleInputChange("ad_creative_name", e.target.value)}
                  placeholder="输入广告创意名称"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="impressions">展示次数</Label>
                <Input
                  id="impressions"
                  type="number"
                  value={formData.impressions}
                  onChange={(e) => handleNumberChange("impressions", e.target.value)}
                  placeholder="0"
                  min="0"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="clicks">点击次数</Label>
                <Input
                  id="clicks"
                  type="number"
                  value={formData.clicks}
                  onChange={(e) => handleNumberChange("clicks", e.target.value)}
                  placeholder="0"
                  min="0"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="notes">备注说明</Label>
              <Textarea
                id="notes"
                value={formData.notes}
                onChange={(e) => handleInputChange("notes", e.target.value)}
                placeholder="填写备注信息..."
                rows={3}
              />
            </div>
          </CardContent>
        )}
      </Card>

      {/* 操作按钮 */}
      <div className="flex justify-end space-x-4">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          取消
        </Button>
        <Button
          type="submit"
          disabled={isSubmitting}
          className="min-w-[100px]"
        >
          {isSubmitting ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
          ) : (
            <>
              <Save className="w-4 h-4 mr-2" />
              {report?.id ? "更新" : "提交日报"}
            </>
          )}
        </Button>
      </div>
    </form>
  );
}
