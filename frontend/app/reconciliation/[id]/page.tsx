"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { PageTemplate } from "@/components/layout/page-template";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import {
  ArrowLeft,
  Download,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Clock,
  XCircle,
  DollarSign,
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart,
  FileText,
  Eye,
  Edit,
  Upload,
  Settings,
  FileSpreadsheet,
  Filter,
  Search,
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
import { DataTable } from "@/components/ui/data-table";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { format, subDays } from "date-fns";
import { zhCN } from "date-fns/locale";

// 类型定义
interface ReconciliationBatch {
  id: number;
  batch_name: string;
  period_start: string;
  period_end: string;
  status: "pending" | "in_progress" | "completed" | "failed" | "cancelled";
  total_accounts: number;
  processed_accounts: number;
  total_discrepancies: number;
  total_system_spend: number;
  total_platform_spend: number;
  total_difference: number;
  difference_percentage: number;
  created_by: string;
  created_at: string;
  completed_at?: string;
  notes: string;
  platform_spend_source: "manual" | "api" | "file";
}

interface AccountDiscrepancy {
  id: number;
  account_id: number;
  account_name: string;
  platform: string;
  system_spend: number;
  platform_spend: number;
  difference: number;
  difference_percentage: number;
  discrepancy_type: "overage" | "shortage" | "matched";
  severity: "low" | "medium" | "high";
  notes: string;
  resolution_status: "pending" | "investigating" | "resolved" | "ignored";
  resolved_by?: string;
  resolved_at?: string;
  resolution_notes?: string;
}

interface DiscrepancyAnalysis {
  total_discrepancies: number;
  overage_count: number;
  shortage_count: number;
  matched_count: number;
  high_severity_count: number;
  medium_severity_count: number;
  low_severity_count: number;
  platform_distribution: Array<{
    platform: string;
    count: number;
    total_difference: number;
  }>;
  trend_data: Array<{
    date: string;
    system_spend: number;
    platform_spend: number;
    difference: number;
  }>;
}

const COLORS = ["#8884d8", "#82ca9d", "#ffc658", "#ff7c7c", "#8dd1e1", "#d084d0"];

export default function ReconciliationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [batch, setBatch] = useState<ReconciliationBatch | null>(null);
  const [discrepancies, setDiscrepancies] = useState<AccountDiscrepancy[]>([]);
  const [analysis, setAnalysis] = useState<DiscrepancyAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedType, setSelectedType] = useState<string>("all");
  const [selectedSeverity, setSelectedSeverity] = useState<string>("all");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");

  // 模拟数据
  const mockBatch: ReconciliationBatch = {
    id: parseInt(params.id as string),
    batch_name: "2024年12月对账",
    period_start: "2024-12-01T00:00:00Z",
    period_end: "2024-12-31T23:59:59Z",
    status: "completed",
    total_accounts: 25,
    processed_accounts: 25,
    total_discrepancies: 3,
    total_system_spend: 125000,
    total_platform_spend: 124800,
    total_difference: -200,
    difference_percentage: -0.16,
    created_by: "财务部-张三",
    created_at: "2025-01-05T09:00:00Z",
    completed_at: "2025-01-05T11:30:00Z",
    notes: "月度例行对账，发现3个账户有小额差异，已处理2个",
    platform_spend_source: "api",
  };

  const mockDiscrepancies: AccountDiscrepancy[] = [
    {
      id: 1,
      account_id: 1,
      account_name: "Facebook Main Account",
      platform: "facebook",
      system_spend: 12500,
      platform_spend: 12300,
      difference: -200,
      difference_percentage: -1.6,
      discrepancy_type: "shortage",
      severity: "medium",
      notes: "平台账单比系统记录少¥200，可能是时间差或数据延迟",
      resolution_status: "investigating",
    },
    {
      id: 2,
      account_id: 2,
      account_name: "TikTok Gaming Account",
      platform: "tiktok",
      system_spend: 8900,
      platform_spend: 9100,
      difference: 200,
      difference_percentage: 2.2,
      discrepancy_type: "overage",
      severity: "low",
      notes: "小额差异，可能是汇率转换导致",
      resolution_status: "resolved",
      resolved_by: "李四",
      resolved_at: "2025-01-05T15:30:00Z",
      resolution_notes: "确认为汇率转换差异，已标记为正常",
    },
    {
      id: 3,
      account_id: 3,
      account_name: "Google Ads Performance",
      platform: "google",
      system_spend: 15600,
      platform_spend: 15400,
      difference: -200,
      difference_percentage: -1.3,
      discrepancy_type: "shortage",
      severity: "low",
      notes: "小额差异，在正常范围内",
      resolution_status: "resolved",
      resolved_by: "王五",
      resolved_at: "2025-01-05T16:45:00Z",
      resolution_notes: "确认在正常误差范围内，已批准",
    },
  ];

  const mockAnalysis: DiscrepancyAnalysis = {
    total_discrepancies: 3,
    overage_count: 1,
    shortage_count: 2,
    matched_count: 22,
    high_severity_count: 0,
    medium_severity_count: 1,
    low_severity_count: 2,
    platform_distribution: [
      { platform: "Facebook", count: 1, total_difference: -200 },
      { platform: "TikTok", count: 1, total_difference: 200 },
      { platform: "Google", count: 1, total_difference: -200 },
    ],
    trend_data: [
      { date: "2024-12-01", system_spend: 4200, platform_spend: 4180, difference: -20 },
      { date: "2024-12-07", system_spend: 5100, platform_spend: 5080, difference: -20 },
      { date: "2024-12-14", system_spend: 4800, platform_spend: 4820, difference: 20 },
      { date: "2024-12-21", system_spend: 5200, platform_spend: 5180, difference: -20 },
      { date: "2024-12-28", system_spend: 5500, platform_spend: 5480, difference: -20 },
      { date: "2024-12-31", system_spend: 125000, platform_spend: 124800, difference: -200 },
    ],
  };

  // 差异列表列定义
  const discrepancyColumns = [
    {
      id: "account_name",
      header: "账户信息",
      cell: (row: AccountDiscrepancy) => (
        <div className="flex flex-col">
          <span className="font-medium">{row.account_name}</span>
          <Badge variant="outline" className="w-fit mt-1">
            {row.platform.toUpperCase()}
          </Badge>
        </div>
      ),
    },
    {
      id: "financial_data",
      header: "财务数据",
      cell: (row: AccountDiscrepancy) => (
        <div className="text-sm space-y-1">
          <div className="flex justify-between">
            <span className="text-gray-600">系统:</span>
            <span>¥{row.system_spend.toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">平台:</span>
            <span>¥{row.platform_spend.toLocaleString()}</span>
          </div>
          <div className={`flex justify-between font-medium ${
            row.difference >= 0 ? "text-green-600" : "text-red-600"
          }`}>
            <span>差异:</span>
            <span>¥{Math.abs(row.difference).toLocaleString()}</span>
          </div>
        </div>
      ),
    },
    {
      id: "discrepancy_info",
      header: "差异分析",
      cell: (row: AccountDiscrepancy) => {
        const typeConfig = {
          overage: { text: "多计", color: "text-green-600", bg: "bg-green-100" },
          shortage: { text: "少计", color: "text-red-600", bg: "bg-red-100" },
          matched: { text: "匹配", color: "text-gray-600", bg: "bg-gray-100" },
        };

        const severityConfig = {
          high: { text: "高", color: "text-red-600", bg: "bg-red-100" },
          medium: { text: "中", color: "text-yellow-600", bg: "bg-yellow-100" },
          low: { text: "低", color: "text-green-600", bg: "bg-green-100" },
        };

        const typeConfig_data = typeConfig[row.discrepancy_type];
        const severityConfig_data = severityConfig[row.severity];

        return (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge className={typeConfig_data.bg + " " + typeConfig_data.color}>
                {typeConfig_data.text}
              </Badge>
              <Badge className={severityConfig_data.bg + " " + severityConfig_data.color}>
                {severityConfig_data.text}风险
              </Badge>
            </div>
            <div className="text-xs text-gray-600">
              {row.difference_percentage.toFixed(2)}% 差异率
            </div>
          </div>
        );
      },
    },
    {
      id: "resolution_status",
      header: "处理状态",
      cell: (row: AccountDiscrepancy) => {
        const statusConfig = {
          pending: { icon: Clock, color: "text-blue-600", bg: "bg-blue-100", text: "待处理" },
          investigating: { icon: AlertTriangle, color: "text-yellow-600", bg: "bg-yellow-100", text: "调查中" },
          resolved: { icon: CheckCircle, color: "text-green-600", bg: "bg-green-100", text: "已解决" },
          ignored: { icon: XCircle, color: "text-gray-600", bg: "bg-gray-100", text: "已忽略" },
        };

        const config = statusConfig[row.resolution_status];
        const Icon = config.icon;

        return (
          <div className="space-y-1">
            <div className={`flex items-center gap-1 px-2 py-1 rounded-full ${config.bg}`}>
              <Icon className={`w-3 h-3 ${config.color}`} />
              <span className={`text-xs font-medium ${config.color}`}>{config.text}</span>
            </div>
            {row.resolved_by && (
              <div className="text-xs text-gray-500">
                {row.resolved_by} - {format(new Date(row.resolved_at!), "MM/dd")}
              </div>
            )}
          </div>
        );
      },
    },
    {
      id: "notes",
      header: "备注说明",
      cell: (row: AccountDiscrepancy) => (
        <div className="max-w-xs">
          <div className="text-sm text-gray-700 line-clamp-2">
            {row.notes}
          </div>
          {row.resolution_notes && (
            <div className="text-xs text-green-600 mt-1">
              处理结果: {row.resolution_notes}
            </div>
          )}
        </div>
      ),
    },
  ];

  // 获取批次详情
  const fetchBatchDetail = async () => {
    setLoading(true);
    try {
      // const response = await fetch(`/api/v1/reconciliation/batches/${params.id}`);
      // const result = await response.json();

      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 800));

      setBatch(mockBatch);
      setDiscrepancies(mockDiscrepancies);
      setAnalysis(mockAnalysis);
    } catch (error) {
      toast.error("获取对账详情失败");
      console.error("获取对账详情错误:", error);
    } finally {
      setLoading(false);
    }
  };

  // 重新开始对账
  const handleRestartReconciliation = async () => {
    try {
      const response = await fetch(`/api/v1/reconciliation/batches/${batch?.id}/restart`, {
        method: "POST",
      });

      if (response.ok) {
        toast.success("对账已重新开始");
        fetchBatchDetail();
      }
    } catch (error) {
      toast.error("重新启动对账失败");
    }
  };

  // 导出详细报告
  const handleExportDetailedReport = async () => {
    try {
      const response = await fetch(`/api/v1/reconciliation/batches/${batch?.id}/export/detailed`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `reconciliation-detailed-${batch?.id}-${format(new Date(), "yyyyMMdd")}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        toast.success("详细报告导出成功");
      }
    } catch (error) {
      toast.error("导出失败");
    }
  };

  // 筛选差异
  const filteredDiscrepancies = discrepancies.filter(discrepancy => {
    const matchesSearch = searchTerm === "" ||
      discrepancy.account_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      discrepancy.platform.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesType = selectedType === "all" || discrepancy.discrepancy_type === selectedType;
    const matchesSeverity = selectedSeverity === "all" || discrepancy.severity === selectedSeverity;
    const matchesStatus = selectedStatus === "all" || discrepancy.resolution_status === selectedStatus;

    return matchesSearch && matchesType && matchesSeverity && matchesStatus;
  });

  useEffect(() => {
    if (params.id) {
      fetchBatchDetail();
    }
  }, [params.id]);

  if (loading || !batch) {
    return (
      <PageTemplate title="对账详情" description="加载中...">
        <div className="flex justify-center items-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-gray-400" />
        </div>
      </PageTemplate>
    );
  }

  const progress = (batch.processed_accounts / batch.total_accounts) * 100;

  return (
    <PageTemplate
      title={batch.batch_name}
      description={
        <div className="flex items-center gap-2">
          <Badge variant={batch.status === "completed" ? "default" : "secondary"}>
            {batch.status === "completed" ? "已完成" :
             batch.status === "in_progress" ? "进行中" :
             batch.status === "pending" ? "待处理" :
             batch.status === "failed" ? "失败" : "已取消"}
          </Badge>
          <span className="text-gray-500">|</span>
          <span className="text-sm text-gray-600">
            {format(new Date(batch.period_start), "yyyy/MM/dd")} - {format(new Date(batch.period_end), "yyyy/MM/dd")}
          </span>
        </div>
      }
      breadcrumbs={[
        { label: "财务对账管理", href: "/reconciliation" },
        { label: batch.batch_name },
      ]}
    >
      <div className="space-y-6">
        {/* 头部操作栏 */}
        <div className="flex justify-between items-center">
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.back()}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回列表
            </Button>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleExportDetailedReport}>
              <FileSpreadsheet className="w-4 h-4 mr-2" />
              导出详细报告
            </Button>
            {(batch.status === "failed" || batch.status === "cancelled") && (
              <Button variant="outline" onClick={handleRestartReconciliation}>
                <RefreshCw className="w-4 h-4 mr-2" />
                重新开始对账
              </Button>
            )}
          </div>
        </div>

        {/* 对账概览卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">对账进度</p>
                  <p className="text-2xl font-bold">{progress.toFixed(0)}%</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {batch.processed_accounts}/{batch.total_accounts} 账户
                  </p>
                </div>
                <BarChart3 className="h-8 w-8 text-muted-foreground" />
              </div>
              <Progress value={progress} className="mt-2" />
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">系统总消耗</p>
                  <p className="text-2xl font-bold text-blue-600">
                    ¥{batch.total_system_spend.toLocaleString()}
                  </p>
                </div>
                <DollarSign className="h-8 w-8 text-blue-200" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">平台总消耗</p>
                  <p className="text-2xl font-bold text-green-600">
                    ¥{batch.total_platform_spend.toLocaleString()}
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-green-200" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">总差异</p>
                  <p className={`text-2xl font-bold ${batch.total_difference >= 0 ? "text-green-600" : "text-red-600"}`}>
                    ¥{Math.abs(batch.total_difference).toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {batch.difference_percentage.toFixed(2)}% 差异率
                  </p>
                </div>
                {batch.total_difference >= 0 ? (
                  <TrendingUp className="h-8 w-8 text-green-200" />
                ) : (
                  <TrendingDown className="h-8 w-8 text-red-200" />
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 对账详情标签页 */}
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">概览分析</TabsTrigger>
            <TabsTrigger value="discrepancies">差异详情</TabsTrigger>
            <TabsTrigger value="trends">趋势分析</TabsTrigger>
            <TabsTrigger value="summary">汇总报告</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* 差异分布饼图 */}
              <Card>
                <CardHeader>
                  <CardTitle>差异类型分布</CardTitle>
                  <CardDescription>不同类型差异的数量分布</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <RechartsPieChart>
                      <Pie
                        data={[
                          { name: "多计", value: analysis?.overage_count || 0 },
                          { name: "少计", value: analysis?.shortage_count || 0 },
                          { name: "匹配", value: analysis?.matched_count || 0 },
                        ]}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
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

              {/* 严重程度分布 */}
              <Card>
                <CardHeader>
                  <CardTitle>风险等级分布</CardTitle>
                  <CardDescription>差异风险的严重程度分析</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">高风险</span>
                      <Badge variant="destructive">
                        {analysis?.high_severity_count || 0} 个
                      </Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">中风险</span>
                      <Badge variant="secondary" className="bg-yellow-100 text-yellow-700">
                        {analysis?.medium_severity_count || 0} 个
                      </Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">低风险</span>
                      <Badge variant="secondary" className="bg-green-100 text-green-700">
                        {analysis?.low_severity_count || 0} 个
                      </Badge>
                    </div>
                    <Separator />
                    <div className="pt-2">
                      <div className="flex justify-between items-center">
                        <span className="font-medium">总差异账户</span>
                        <span className="font-bold">
                          {analysis?.total_discrepancies || 0} / {batch.total_accounts}
                        </span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* 平台差异分析 */}
              <Card>
                <CardHeader>
                  <CardTitle>平台差异分析</CardTitle>
                  <CardDescription>各平台的差异金额和数量</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={analysis?.platform_distribution || []}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="platform" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="count" fill="#8884d8" name="差异数量" />
                      <Bar dataKey="total_difference" fill="#82ca9d" name="差异金额" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* 对账信息 */}
              <Card>
                <CardHeader>
                  <CardTitle>对账信息</CardTitle>
                  <CardDescription>批次的基本信息和配置</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-sm text-gray-600">批次名称</span>
                      <p className="font-medium">{batch.batch_name}</p>
                    </div>
                    <div>
                      <span className="text-sm text-gray-600">对账周期</span>
                      <p className="font-medium">
                        {format(new Date(batch.period_start), "yyyy/MM/dd")} - {format(new Date(batch.period_end), "yyyy/MM/dd")}
                      </p>
                    </div>
                    <div>
                      <span className="text-sm text-gray-600">平台数据源</span>
                      <p className="font-medium">
                        {batch.platform_spend_source === "api" ? "API获取" :
                         batch.platform_spend_source === "file" ? "文件上传" : "手动录入"}
                      </p>
                    </div>
                    <div>
                      <span className="text-sm text-gray-600">创建人</span>
                      <p className="font-medium">{batch.created_by}</p>
                    </div>
                  </div>
                  {batch.notes && (
                    <div>
                      <span className="text-sm text-gray-600">备注说明</span>
                      <p className="font-medium mt-1">{batch.notes}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="discrepancies">
            <Card>
              <CardHeader>
                <CardTitle>差异详情列表</CardTitle>
                <CardDescription>
                  所有存在差异的账户详细信息和处理状态
                </CardDescription>
                <div className="flex flex-wrap gap-4 mt-4">
                  <div className="flex-1 min-w-64">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                      <Input
                        placeholder="搜索账户名称或平台..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10"
                      />
                    </div>
                  </div>
                  <Select value={selectedType} onValueChange={setSelectedType}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">所有类型</SelectItem>
                      <SelectItem value="overage">多计</SelectItem>
                      <SelectItem value="shortage">少计</SelectItem>
                      <SelectItem value="matched">匹配</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select value={selectedSeverity} onValueChange={setSelectedSeverity}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">所有风险</SelectItem>
                      <SelectItem value="high">高风险</SelectItem>
                      <SelectItem value="medium">中风险</SelectItem>
                      <SelectItem value="low">低风险</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">所有状态</SelectItem>
                      <SelectItem value="pending">待处理</SelectItem>
                      <SelectItem value="investigating">调查中</SelectItem>
                      <SelectItem value="resolved">已解决</SelectItem>
                      <SelectItem value="ignored">已忽略</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardHeader>
              <CardContent>
                <DataTable
                  columns={discrepancyColumns}
                  data={filteredDiscrepancies}
                  loading={loading}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="trends">
            <Card>
              <CardHeader>
                <CardTitle>差异趋势分析</CardTitle>
                <CardDescription>对账周期内的消耗和差异变化趋势</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={analysis?.trend_data || []}>
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
          </TabsContent>

          <TabsContent value="summary">
            <div className="space-y-6">
              {/* 对账总结 */}
              <Card>
                <CardHeader>
                  <CardTitle>对账总结</CardTitle>
                  <CardDescription>本次对账的整体情况和建议</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="prose max-w-none">
                    <h3>对账结果概述</h3>
                    <p>
                      本次对账共涉及 {batch.total_accounts} 个账户，已完成对账 {batch.processed_accounts} 个账户。
                      系统总消耗为 ¥{batch.total_system_spend.toLocaleString()}，平台总消耗为 ¥{batch.total_platform_spend.toLocaleString()}，
                      总差异为 ¥{Math.abs(batch.total_difference).toLocaleString()}，差异率为 {batch.difference_percentage.toFixed(2)}%。
                    </p>

                    <h3>差异分析</h3>
                    <ul>
                      <li>发现 {analysis?.total_discrepancies} 个账户存在差异</li>
                      <li>其中 {analysis?.overage_count} 个账户多计，{analysis?.shortage_count} 个账户少计</li>
                      <li>高风险差异 {analysis?.high_severity_count} 个，中风险 {analysis?.medium_severity_count} 个，低风险 {analysis?.low_severity_count} 个</li>
                      <li>已处理 {discrepancies.filter(d => d.resolution_status === "resolved").length} 个差异</li>
                    </ul>

                    <h3>建议和改进措施</h3>
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <h4 className="text-blue-800">优化建议：</h4>
                      <ul className="text-blue-700">
                        <li>建议定期进行对账，至少每月一次</li>
                        <li>对于持续出现差异的账户，建议深入调查原因</li>
                        <li>考虑优化数据同步机制，减少人为误差</li>
                        <li>建立差异处理标准流程，提高处理效率</li>
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* 处理状态统计 */}
              <Card>
                <CardHeader>
                  <CardTitle>处理状态统计</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        {discrepancies.filter(d => d.resolution_status === "pending").length}
                      </div>
                      <div className="text-sm text-gray-600">待处理</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-yellow-600">
                        {discrepancies.filter(d => d.resolution_status === "investigating").length}
                      </div>
                      <div className="text-sm text-gray-600">调查中</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {discrepancies.filter(d => d.resolution_status === "resolved").length}
                      </div>
                      <div className="text-sm text-gray-600">已解决</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-gray-600">
                        {discrepancies.filter(d => d.resolution_status === "ignored").length}
                      </div>
                      <div className="text-sm text-gray-600">已忽略</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </PageTemplate>
  );
}