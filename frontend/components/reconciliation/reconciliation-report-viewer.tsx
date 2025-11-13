"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import {
  Download,
  FileSpreadsheet,
  FileText,
  Share,
  Print,
  Eye,
  Calendar,
  DollarSign,
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart,
  CheckCircle,
  AlertTriangle,
  Clock,
  Users,
  Target,
} from "lucide-react";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { toast } from "sonner";
import { format, subDays } from "date-fns";

// 类型定义
interface ReconciliationReport {
  id: number;
  batch_id: number;
  batch_name: string;
  period_start: string;
  period_end: string;
  generated_at: string;
  generated_by: string;
  report_type: "summary" | "detailed" | "executive";
  status: "generating" | "completed" | "failed";
  file_url?: string;
  file_size?: number;

  // 报告数据
  executive_summary: {
    total_accounts: number;
    total_system_spend: number;
    total_platform_spend: number;
    total_difference: number;
    difference_percentage: number;
    discrepancies_count: number;
    high_risk_count: number;
    resolved_count: number;
  };

  financial_analysis: {
    platform_breakdown: Array<{
      platform: string;
      system_spend: number;
      platform_spend: number;
      difference: number;
      accounts_count: number;
    }>;
    trend_data: Array<{
      date: string;
      system_spend: number;
      platform_spend: number;
      difference: number;
    }>;
    discrepancy_distribution: Array<{
      type: string;
      count: number;
      total_amount: number;
    }>;
  };

  risk_assessment: {
    high_risk_accounts: Array<{
      account_name: string;
      platform: string;
      difference: number;
      difference_percentage: number;
      risk_factors: string[];
    }>;
    recommendations: string[];
    compliance_status: "compliant" | "attention_required" | "non_compliant";
  };

  operational_insights: {
    processing_efficiency: {
      average_processing_time: number;
      error_rate: number;
      automation_rate: number;
    };
    quality_metrics: {
      data_accuracy: number;
      completeness: number;
      timeliness: number;
    };
  };
}

interface ReconciliationReportViewerProps {
  batchId: number;
  reportType?: "summary" | "detailed" | "executive";
  onGenerateReport?: (type: string) => void;
}

const COLORS = ["#8884d8", "#82ca9d", "#ffc658", "#ff7c7c", "#8dd1e1", "#d084d0"];

export function ReconciliationReportViewer({
  batchId,
  reportType = "detailed",
  onGenerateReport,
}: ReconciliationReportViewerProps) {
  const [report, setReport] = useState<ReconciliationReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  // 模拟报告数据
  const mockReport: ReconciliationReport = {
    id: 1,
    batch_id: batchId,
    batch_name: "2024年12月对账",
    period_start: "2024-12-01T00:00:00Z",
    period_end: "2024-12-31T23:59:59Z",
    generated_at: "2025-01-05T16:30:00Z",
    generated_by: "财务系统",
    report_type: reportType,
    status: "completed",
    file_url: "/reports/reconciliation-202412.xlsx",
    file_size: 2048000,

    executive_summary: {
      total_accounts: 25,
      total_system_spend: 125000,
      total_platform_spend: 124800,
      total_difference: -200,
      difference_percentage: -0.16,
      discrepancies_count: 3,
      high_risk_count: 0,
      resolved_count: 2,
    },

    financial_analysis: {
      platform_breakdown: [
        {
          platform: "Facebook",
          system_spend: 75000,
          platform_spend: 74800,
          difference: -200,
          accounts_count: 15,
        },
        {
          platform: "TikTok",
          system_spend: 25000,
          platform_spend: 25000,
          difference: 0,
          accounts_count: 5,
        },
        {
          platform: "Google Ads",
          system_spend: 20000,
          platform_spend: 20000,
          difference: 0,
          accounts_count: 3,
        },
        {
          platform: "Twitter",
          system_spend: 5000,
          platform_spend: 5000,
          difference: 0,
          accounts_count: 2,
        },
      ],
      trend_data: [
        { date: "2024-12-01", system_spend: 4200, platform_spend: 4180, difference: -20 },
        { date: "2024-12-07", system_spend: 5100, platform_spend: 5080, difference: -20 },
        { date: "2024-12-14", system_spend: 4800, platform_spend: 4820, difference: 20 },
        { date: "2024-12-21", system_spend: 5200, platform_spend: 5180, difference: -20 },
        { date: "2024-12-28", system_spend: 5500, platform_spend: 5480, difference: -20 },
        { date: "2024-12-31", system_spend: 125000, platform_spend: 124800, difference: -200 },
      ],
      discrepancy_distribution: [
        { type: "多计", count: 0, total_amount: 0 },
        { type: "少计", count: 2, total_amount: -200 },
        { type: "匹配", count: 23, total_amount: 0 },
      ],
    },

    risk_assessment: {
      high_risk_accounts: [],
      recommendations: [
        "建议建立自动化的数据同步机制",
        "加强差异监控和预警系统",
        "完善数据质量检查流程",
      ],
      compliance_status: "compliant",
    },

    operational_insights: {
      processing_efficiency: {
        average_processing_time: 2.5, // 小时
        error_rate: 0.08, // 8%
        automation_rate: 0.85, // 85%
      },
      quality_metrics: {
        data_accuracy: 0.98, // 98%
        completeness: 0.95, // 95%
        timeliness: 0.92, // 92%
      },
    },
  };

  // 获取报告数据
  const fetchReport = async () => {
    setLoading(true);
    try {
      // const response = await fetch(`/api/v1/reconciliation/batches/${batchId}/report?type=${reportType}`);
      // const result = await response.json();

      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));

      setReport(mockReport);
    } catch (error) {
      toast.error("获取报告失败");
      console.error("获取报告错误:", error);
    } finally {
      setLoading(false);
    }
  };

  // 生成报告
  const handleGenerateReport = async (type: string) => {
    setGenerating(true);
    try {
      const response = await fetch(`/api/v1/reconciliation/batches/${batchId}/generate-report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type }),
      });

      if (response.ok) {
        toast.success("报告生成已开始，请稍候查看");
        if (onGenerateReport) {
          onGenerateReport(type);
        }
        // 定期检查报告状态
        const checkInterval = setInterval(() => {
          fetchReport();
        }, 5000);

        // 5分钟后停止检查
        setTimeout(() => {
          clearInterval(checkInterval);
        }, 300000);
      }
    } catch (error) {
      toast.error("生成报告失败");
    } finally {
      setGenerating(false);
    }
  };

  // 下载报告
  const handleDownloadReport = async () => {
    if (!report?.file_url) return;

    try {
      const response = await fetch(report.file_url);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `reconciliation-report-${format(new Date(), "yyyyMMdd")}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        toast.success("报告下载成功");
      }
    } catch (error) {
      toast.error("下载失败");
    }
  };

  // 打印报告
  const handlePrintReport = () => {
    window.print();
  };

  // 分享报告
  const handleShareReport = async () => {
    if (!report) return;

    try {
      const response = await fetch(`/api/v1/reconciliation/reports/${report.id}/share`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          recipients: [], // 可以添加收件人
          message: "请查看最新的对账报告",
        }),
      });

      if (response.ok) {
        toast.success("报告分享成功");
      }
    } catch (error) {
      toast.error("分享失败");
    }
  };

  useEffect(() => {
    fetchReport();
  }, [batchId, reportType]);

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">正在生成报告...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!report) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-64">
          <div className="text-center">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 mb-4">暂无报告数据</p>
            <Button onClick={() => handleGenerateReport(reportType)} disabled={generating}>
              {generating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  生成中...
                </>
              ) : (
                <>
                  <FileSpreadsheet className="w-4 h-4 mr-2" />
                  生成报告
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6" id="reconciliation-report">
      {/* 报告头部 */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                {report.batch_name} - 对账报告
              </CardTitle>
              <CardDescription>
                {format(new Date(report.period_start), "yyyy年MM月dd日")} - {format(new Date(report.period_end), "yyyy年MM月dd日")}
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={handleDownloadReport}>
                <Download className="w-4 h-4 mr-2" />
                下载
              </Button>
              <Button variant="outline" size="sm" onClick={handleShareReport}>
                <Share className="w-4 h-4 mr-2" />
                分享
              </Button>
              <Button variant="outline" size="sm" onClick={handlePrintReport}>
                <Print className="w-4 h-4 mr-2" />
                打印
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-600">生成时间:</span>
              <div>{format(new Date(report.generated_at), "yyyy-MM-dd HH:mm")}</div>
            </div>
            <div>
              <span className="text-gray-600">生成人:</span>
              <div>{report.generated_by}</div>
            </div>
            <div>
              <span className="text-gray-600">报告类型:</span>
              <div>
                {report.report_type === "summary" ? "汇总报告" :
                 report.report_type === "detailed" ? "详细报告" : "高管报告"}
              </div>
            </div>
            <div>
              <span className="text-gray-600">状态:</span>
              <div>
                <Badge variant={report.status === "completed" ? "default" : "secondary"}>
                  {report.status === "completed" ? "已完成" :
                   report.status === "generating" ? "生成中" : "失败"}
                </Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 报告内容 */}
      <Tabs defaultValue="summary" className="space-y-4">
        <TabsList>
          <TabsTrigger value="summary">执行摘要</TabsTrigger>
          <TabsTrigger value="financial">财务分析</TabsTrigger>
          <TabsTrigger value="risk">风险评估</TabsTrigger>
          <TabsTrigger value="operational">运营洞察</TabsTrigger>
        </TabsList>

        <TabsContent value="summary">
          <div className="space-y-6">
            {/* 关键指标 */}
            <Card>
              <CardHeader>
                <CardTitle>关键指标概览</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="text-center p-4 border rounded-lg">
                    <Users className="w-8 h-8 text-blue-500 mx-auto mb-2" />
                    <div className="text-2xl font-bold">{report.executive_summary.total_accounts}</div>
                    <div className="text-sm text-gray-600">对账账户数</div>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <DollarSign className="w-8 h-8 text-green-500 mx-auto mb-2" />
                    <div className="text-2xl font-bold">¥{report.executive_summary.total_system_spend.toLocaleString()}</div>
                    <div className="text-sm text-gray-600">系统总消耗</div>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <Target className="w-8 h-8 text-purple-500 mx-auto mb-2" />
                    <div className="text-2xl font-bold">
                      {report.executive_summary.difference_percentage.toFixed(2)}%
                    </div>
                    <div className="text-sm text-gray-600">差异率</div>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <CheckCircle className="w-8 h-8 text-green-500 mx-auto mb-2" />
                    <div className="text-2xl font-bold">{report.executive_summary.resolved_count}</div>
                    <div className="text-sm text-gray-600">已解决差异</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 执行总结 */}
            <Card>
              <CardHeader>
                <CardTitle>执行总结</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose max-w-none">
                  <h4>对账结果</h4>
                  <p>
                    本次对账共涉及 <strong>{report.executive_summary.total_accounts}</strong> 个账户，
                    系统记录总消耗 <strong>¥{report.executive_summary.total_system_spend.toLocaleString()}</strong>，
                    平台账单总消耗 <strong>¥{report.executive_summary.total_platform_spend.toLocaleString()}</strong>，
                    总差异金额 <strong>¥{Math.abs(report.executive_summary.total_difference).toLocaleString()}</strong>，
                    差异率为 <strong>{report.executive_summary.difference_percentage.toFixed(2)}%</strong>。
                  </p>

                  <h4>差异分析</h4>
                  <ul>
                    <li>发现 <strong>{report.executive_summary.discrepancies_count}</strong> 个账户存在差异</li>
                    <li>高风险差异 <strong>{report.executive_summary.high_risk_count}</strong> 个</li>
                    <li>已处理差异 <strong>{report.executive_summary.resolved_count}</strong> 个</li>
                    <li>处理完成率 <strong>{((report.executive_summary.resolved_count / Math.max(report.executive_summary.discrepancies_count, 1)) * 100).toFixed(1)}%</strong>
                  </ul>

                  <h4>合规状态</h4>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <Badge className="bg-green-100 text-green-800">
                      {report.risk_assessment.compliance_status === "compliant" ? "合规" :
                       report.risk_assessment.compliance_status === "attention_required" ? "需要关注" : "不合规"}
                    </Badge>
                    <p className="mt-2 text-sm">
                      {report.risk_assessment.compliance_status === "compliant" ?
                        "对账结果符合财务合规要求，无重大风险。" :
                        "发现部分问题需要进一步关注和处理。"}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="financial">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 平台消耗对比 */}
            <Card>
              <CardHeader>
                <CardTitle>平台消耗对比</CardTitle>
                <CardDescription>各平台的系统消耗与平台账单对比</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={report.financial_analysis.platform_breakdown}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="platform" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="system_spend" fill="#8884d8" name="系统消耗" />
                    <Bar dataKey="platform_spend" fill="#82ca9d" name="平台账单" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* 差异分布 */}
            <Card>
              <CardHeader>
                <CardTitle>差异类型分布</CardTitle>
                <CardDescription>不同类型差异的数量和金额分布</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RechartsPieChart>
                    <Pie
                      data={report.financial_analysis.discrepancy_distribution}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, count }) => `${name}: ${count}`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="count"
                    >
                      {COLORS.map((color, index) => (
                        <Cell key={`cell-${index}`} fill={color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </RechartsPieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* 趋势分析 */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>消耗趋势分析</CardTitle>
                <CardDescription>对账周期内的消耗变化趋势</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={report.financial_analysis.trend_data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip />
                    <Legend />
                    <Line
                      yAxisId="left"
                      type="monotone"
                      dataKey="system_spend"
                      stroke="#3b82f6"
                      name="系统消耗"
                      strokeWidth={2}
                    />
                    <Line
                      yAxisId="left"
                      type="monotone"
                      dataKey="platform_spend"
                      stroke="#10b981"
                      name="平台消耗"
                      strokeWidth={2}
                    />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="difference"
                      stroke="#ef4444"
                      name="差异金额"
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="risk">
          <div className="space-y-6">
            {/* 风险评估 */}
            <Card>
              <CardHeader>
                <CardTitle>风险评估</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center p-4 border rounded-lg">
                      <AlertTriangle className="w-8 h-8 text-red-500 mx-auto mb-2" />
                      <div className="text-2xl font-bold">{report.executive_summary.high_risk_count}</div>
                      <div className="text-sm text-gray-600">高风险账户</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <Clock className="w-8 h-8 text-yellow-500 mx-auto mb-2" />
                      <div className="text-2xl font-bold">
                        {report.executive_summary.discrepancies_count - report.executive_summary.resolved_count}
                      </div>
                      <div className="text-sm text-gray-600">待处理差异</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <CheckCircle className="w-8 h-8 text-green-500 mx-auto mb-2" />
                      <div className="text-2xl font-bold">{report.risk_assessment.compliance_status === "compliant" ? "100%" : "85%"}</div>
                      <div className="text-sm text-gray-600">合规率</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 高风险账户 */}
            {report.risk_assessment.high_risk_accounts.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>高风险账户</CardTitle>
                  <CardDescription>需要特别关注的账户差异</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {report.risk_assessment.high_risk_accounts.map((account, index) => (
                      <div key={index} className="border rounded-lg p-4">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <div className="font-medium">{account.account_name}</div>
                            <div className="text-sm text-gray-600">{account.platform}</div>
                          </div>
                          <div className="text-right">
                            <div className="font-bold text-red-600">¥{Math.abs(account.difference).toLocaleString()}</div>
                            <div className="text-sm text-gray-600">{account.difference_percentage.toFixed(2)}%</div>
                          </div>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {account.risk_factors.map((factor, idx) => (
                            <Badge key={idx} variant="destructive" className="text-xs">
                              {factor}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* 改进建议 */}
            <Card>
              <CardHeader>
                <CardTitle>改进建议</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {report.risk_assessment.recommendations.map((recommendation, index) => (
                    <div key={index} className="flex items-start gap-2">
                      <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                      <span>{recommendation}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="operational">
          <div className="space-y-6">
            {/* 处理效率 */}
            <Card>
              <CardHeader>
                <CardTitle>处理效率</CardTitle>
                <CardDescription>对账流程的效率指标</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600">
                      {report.operational_insights.processing_efficiency.average_processing_time}h
                    </div>
                    <div className="text-sm text-gray-600">平均处理时间</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">
                      {(report.operational_insights.processing_efficiency.automation_rate * 100).toFixed(0)}%
                    </div>
                    <div className="text-sm text-gray-600">自动化率</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-orange-600">
                      {(report.operational_insights.processing_efficiency.error_rate * 100).toFixed(1)}%
                    </div>
                    <div className="text-sm text-gray-600">错误率</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 质量指标 */}
            <Card>
              <CardHeader>
                <CardTitle>数据质量指标</CardTitle>
                <CardDescription>数据质量和完整性评估</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    {
                      label: "数据准确性",
                      value: report.operational_insights.quality_metrics.data_accuracy,
                      color: "text-green-600",
                    },
                    {
                      label: "数据完整性",
                      value: report.operational_insights.quality_metrics.completeness,
                      color: "text-blue-600",
                    },
                    {
                      label: "及时性",
                      value: report.operational_insights.quality_metrics.timeliness,
                      color: "text-purple-600",
                    },
                  ].map((metric, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">{metric.label}</span>
                        <span className={`text-sm font-bold ${metric.color}`}>
                          {(metric.value * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="h-2 rounded-full bg-blue-500"
                          style={{ width: `${metric.value * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* 运营洞察 */}
            <Card>
              <CardHeader>
                <CardTitle>运营洞察</CardTitle>
                <CardDescription>基于对账数据的运营分析和建议</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="prose max-w-none">
                  <h4>流程优化建议</h4>
                  <ul>
                    <li>当前处理效率良好，平均处理时间控制在合理范围内</li>
                    <li>自动化率达到85%，建议进一步提升至90%以上</li>
                    <li>错误率8%，需要加强数据验证和质量检查</li>
                  </ul>

                  <h4>数据质量改进</h4>
                  <ul>
                    <li>数据准确性98%，表现优秀</li>
                    <li>数据完整性95%，建议提升数据收集覆盖范围</li>
                    <li>及时性92%，可以优化数据同步频率</li>
                  </ul>

                  <h4>技术优化方向</h4>
                  <ul>
                    <li>引入AI算法进行异常检测和预测</li>
                    <li>建立实时数据监控和预警机制</li>
                    <li>优化数据同步管道，减少延迟</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}