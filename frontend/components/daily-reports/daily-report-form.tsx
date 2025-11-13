"use client";

import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Calculator, Save, X, Plus, Minus } from "lucide-react";
import { toast } from "sonner";

// 类型定义
interface DailyReport {
  id?: number;
  report_date: string;
  ad_account_id: number;
  campaign_name: string;
  ad_group_name: string;
  ad_creative_name: string;
  impressions: number;
  clicks: number;
  spend: number;
  conversions: number;
  new_follows: number;
  cpa?: number;
  cpl?: number;
  roas?: number;
  notes: string;
}

interface AdAccount {
  id: number;
  name: string;
  platform: string;
  project_name?: string;
}

interface DailyReportFormProps {
  report?: DailyReport | null;
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
  const [formData, setFormData] = useState<DailyReport>({
    report_date: report?.report_date || new Date().toISOString().split("T")[0],
    ad_account_id: report?.ad_account_id || 0,
    campaign_name: report?.campaign_name || "",
    ad_group_name: report?.ad_group_name || "",
    ad_creative_name: report?.ad_creative_name || "",
    impressions: report?.impressions || 0,
    clicks: report?.clicks || 0,
    spend: report?.spend || 0,
    conversions: report?.conversions || 0,
    new_follows: report?.new_follows || 0,
    cpa: report?.cpa || 0,
    cpl: report?.cpl || 0,
    roas: report?.roas || 0,
    notes: report?.notes || "",
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showCalculator, setShowCalculator] = useState(false);
  const [calculatorInput, setCalculatorInput] = useState("");
  const [calculatorResult, setCalculatorResult] = useState(0);

  // 计算派生指标
  useEffect(() => {
    const cpl = formData.new_follows > 0 ? formData.spend / formData.new_follows : 0;
    const cpa = formData.conversions > 0 ? formData.spend / formData.conversions : 0;
    // 假设ROI为5（可以根据实际情况调整）
    const roas = formData.spend > 0 ? (formData.conversions * 5) / formData.spend : 0;

    setFormData((prev) => ({
      ...prev,
      cpl: parseFloat(cpl.toFixed(2)),
      cpa: parseFloat(cpa.toFixed(2)),
      roas: parseFloat(roas.toFixed(2)),
    }));
  }, [formData.spend, formData.conversions, formData.new_follows]);

  // 处理输入变化
  const handleInputChange = (
    field: keyof DailyReport,
    value: string | number
  ) => {
    setFormData((prev) => ({
      ...prev,
      [field]: field === "report_date" || field === "ad_account_id"
        ? value
        : field === "spend" || field === "cpl" || field === "cpa" || field === "roas"
        ? parseFloat(value.toString()) || 0
        : typeof value === "number"
        ? value
        : value.toString(),
    }));
  };

  // 计算器功能
  const handleCalculator = (operation: string) => {
    try {
      if (operation === "=") {
        const result = eval(calculatorInput);
        setCalculatorResult(parseFloat(result.toFixed(2)));
      } else if (operation === "C") {
        setCalculatorInput("");
        setCalculatorResult(0);
      } else {
        setCalculatorInput(calculatorInput + operation);
      }
    } catch (error) {
      toast.error("计算错误");
    }
  };

  // 应用计算结果
  const applyCalculatorResult = (field: "spend" | "cpl" | "cpa" | "roas") => {
    handleInputChange(field, calculatorResult);
    setShowCalculator(false);
    setCalculatorInput("");
    setCalculatorResult(0);
  };

  // 提交表单
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const url = report?.id
        ? `/api/v1/daily-reports/${report.id}`
        : "/api/v1/daily-reports";
      const method = report?.id ? "PUT" : "POST";

      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (data.success) {
        toast.success(report?.id ? "更新成功" : "创建成功");
        onSuccess();
      } else {
        toast.error(data.message || "操作失败");
      }
    } catch (error) {
      console.error("提交错误:", error);
      toast.error("操作失败");
    } finally {
      setIsSubmitting(false);
    }
  };

  // 批量导入数据（从剪贴板）
  const handleBatchImport = async () => {
    try {
      const text = await navigator.clipboard.readText();
      const lines = text.split("\n");

      // 假设格式：广告系列名称,广告组名称,展示次数,点击次数,消耗,转化数,新增粉丝
      if (lines.length > 0) {
        const [campaign, group, impressions, clicks, spend, conversions, follows] =
          lines[0].split(",").map(item => item.trim());

        if (campaign && group) {
          setFormData(prev => ({
            ...prev,
            campaign_name: campaign,
            ad_group_name: group,
            impressions: parseInt(impressions) || 0,
            clicks: parseInt(clicks) || 0,
            spend: parseFloat(spend) || 0,
            conversions: parseInt(conversions) || 0,
            new_follows: parseInt(follows) || 0,
          }));
          toast.success("数据导入成功");
        }
      }
    } catch (error) {
      toast.error("导入失败，请检查剪贴板格式");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* 基本信息 */}
      <Card>
        <CardHeader>
          <CardTitle>基本信息</CardTitle>
          <CardDescription>填写日报的基本信息</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
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

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="campaign_name">广告系列名称 *</Label>
              <Input
                id="campaign_name"
                value={formData.campaign_name}
                onChange={(e) => handleInputChange("campaign_name", e.target.value)}
                placeholder="输入广告系列名称"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="ad_group_name">广告组名称 *</Label>
              <Input
                id="ad_group_name"
                value={formData.ad_group_name}
                onChange={(e) => handleInputChange("ad_group_name", e.target.value)}
                placeholder="输入广告组名称"
                required
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
        </CardContent>
      </Card>

      {/* 数据指标 */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>数据指标</CardTitle>
              <CardDescription>填写广告投放的关键数据</CardDescription>
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleBatchImport}
            >
              从剪贴板导入
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label htmlFor="impressions">展示次数</Label>
              <Input
                id="impressions"
                type="number"
                value={formData.impressions}
                onChange={(e) => handleInputChange("impressions", e.target.value)}
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
                onChange={(e) => handleInputChange("clicks", e.target.value)}
                placeholder="0"
                min="0"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="spend">
                消耗金额 (¥)
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setShowCalculator(true);
                    setCalculatorInput(formData.spend.toString());
                  }}
                >
                  <Calculator className="w-3 h-3" />
                </Button>
              </Label>
              <Input
                id="spend"
                type="number"
                step="0.01"
                value={formData.spend}
                onChange={(e) => handleInputChange("spend", e.target.value)}
                placeholder="0.00"
                min="0"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="conversions">转化数</Label>
              <Input
                id="conversions"
                type="number"
                value={formData.conversions}
                onChange={(e) => handleInputChange("conversions", e.target.value)}
                placeholder="0"
                min="0"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="new_follows">新增粉丝数</Label>
              <Input
                id="new_follows"
                type="number"
                value={formData.new_follows}
                onChange={(e) => handleInputChange("new_follows", e.target.value)}
                placeholder="0"
                min="0"
              />
            </div>

            <div className="space-y-2">
              <Label>单粉成本 (¥)</Label>
              <Input
                type="number"
                step="0.01"
                value={formData.cpl}
                readOnly
                className="bg-gray-50"
              />
            </div>

            <div className="space-y-2">
              <Label>单次转化成本 (¥)</Label>
              <Input
                type="number"
                step="0.01"
                value={formData.cpa}
                readOnly
                className="bg-gray-50"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>ROI / ROAS</Label>
            <Input
              type="number"
              step="0.01"
              value={formData.roas}
              readOnly
              className="bg-gray-50"
            />
          </div>
        </CardContent>
      </Card>

      {/* 备注 */}
      <Card>
        <CardHeader>
          <CardTitle>备注说明</CardTitle>
          <CardDescription>添加额外的说明或注意事项</CardDescription>
        </CardHeader>
        <CardContent>
          <Textarea
            value={formData.notes}
            onChange={(e) => handleInputChange("notes", e.target.value)}
            placeholder="填写备注信息..."
            rows={3}
          />
        </CardContent>
      </Card>

      {/* 计算器弹窗 */}
      {showCalculator && (
        <Card className="fixed right-4 top-1/2 transform -translate-y-1/2 w-64 shadow-lg z-50">
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle className="text-sm">计算器</CardTitle>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setShowCalculator(false)}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            <Input
              value={calculatorInput}
              onChange={(e) => setCalculatorInput(e.target.value)}
              placeholder="输入计算表达式"
            />
            <div className="text-right text-lg font-semibold">
              = {calculatorResult}
            </div>
            <div className="grid grid-cols-4 gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => handleCalculator("7")}
              >
                7
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleCalculator("8")}
              >
                8
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleCalculator("9")}
              >
                9
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleCalculator("/")}
              >
                ÷
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleCalculator("4")}
              >
                4
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleCalculator("5")}
              >
                5
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleCalculator("6")}
              >
                6
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleCalculator("*")}
              >
                ×
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleCalculator("1")}
              >
                1
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleCalculator("2")}
              >
                2
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleCalculator("3")}
              >
                3
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleCalculator("-")}
              >
                -
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleCalculator("0")}
              >
                0
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleCalculator(".")}
              >
                .
              </Button>
              <Button
                type="button"
                onClick={() => handleCalculator("=")}
              >
                =
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleCalculator("+")}
              >
                +
              </Button>
            </div>
            <div className="flex space-x-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => handleCalculator("C")}
                className="flex-1"
              >
                清除
              </Button>
              <Button
                type="button"
                size="sm"
                onClick={() => applyCalculatorResult("spend")}
                className="flex-1"
              >
                应用到消耗
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

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
              {report?.id ? "更新" : "保存"}
            </>
          )}
        </Button>
      </div>
    </form>
  );
}