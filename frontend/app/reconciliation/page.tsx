"use client";

import React, { useState, useEffect } from "react";
import { PageTemplate } from "@/components/layout/page-template";
import { DataTable } from "@/components/ui/data-table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Plus,
  Search,
  Filter,
  Download,
  RefreshCw,
  Eye,
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  XCircle,
  CalendarIcon,
  DollarSign,
  BarChart3,
  TrendingUp,
  TrendingDown,
  FileSpreadsheet,
  Upload,
  Settings,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { toast } from "sonner";
import { format, subDays, startOfMonth, endOfMonth } from "date-fns";
import { zhCN } from "date-fns/locale";
import { cn } from "@/lib/utils";

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
  uploaded_file?: {
    filename: string;
    size: number;
    upload_time: string;
  };
}

interface ReconciliationSummary {
  total_batches: number;
  pending_batches: number;
  completed_batches: number;
  total_difference: number;
  avg_difference_percentage: number;
  last_sync_time: string;
  upcoming_batches: number;
}

// 列定义
const columns = [
  {
    id: "batch_name",
    header: "批次名称",
    cell: (row: ReconciliationBatch) => (
      <div className="flex flex-col">
        <span className="font-medium">{row.batch_name}</span>
        <span className="text-sm text-gray-500">
          {format(new Date(row.period_start), "yyyy/MM/dd")} - {format(new Date(row.period_end), "yyyy/MM/dd")}
        </span>
      </div>
    ),
  },
  {
    id: "status",
    header: "状态",
    cell: (row: ReconciliationBatch) => {
      const statusConfig = {
        pending: { icon: Clock, color: "text-blue-600", bg: "bg-blue-100", text: "待处理" },
        in_progress: { icon: RefreshCw, color: "text-yellow-600", bg: "bg-yellow-100", text: "对账中" },
        completed: { icon: CheckCircle, color: "text-green-600", bg: "bg-green-100", text: "已完成" },
        failed: { icon: XCircle, color: "text-red-600", bg: "bg-red-100", text: "失败" },
        cancelled: { icon: XCircle, color: "text-gray-600", bg: "bg-gray-100", text: "已取消" },
      };

      const config = statusConfig[row.status];
      const Icon = config.icon;

      return (
        <div className={`flex items-center gap-1 px-2 py-1 rounded-full ${config.bg}`}>
          <Icon className={`w-3 h-3 ${config.color}`} />
          <span className={`text-xs font-medium ${config.color}`}>{config.text}</span>
        </div>
      );
    },
  },
  {
    id: "progress",
    header: "进度",
    cell: (row: ReconciliationBatch) => {
      const progress = (row.processed_accounts / row.total_accounts) * 100;

      return (
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <span>{row.processed_accounts}/{row.total_accounts}</span>
            <span>{progress.toFixed(0)}%</span>
          </div>
          <div className="w-20 bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${
                row.status === "completed" ? "bg-green-500" :
                row.status === "failed" ? "bg-red-500" :
                "bg-blue-500"
              }`}
              style={{ width: `${Math.min(progress, 100)}%` }}
            />
          </div>
        </div>
      );
    },
  },
  {
    id: "discrepancies",
    header: "差异情况",
    cell: (row: ReconciliationBatch) => (
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          {row.total_discrepancies > 0 ? (
            <AlertTriangle className="w-4 h-4 text-orange-500" />
          ) : (
            <CheckCircle className="w-4 h-4 text-green-500" />
          )}
          <span className="text-sm font-medium">
            {row.total_discrepancies} 个差异
          </span>
        </div>
        <div className="text-xs text-gray-500">
          差异率: {row.difference_percentage.toFixed(2)}%
        </div>
      </div>
    ),
  },
  {
    id: "financial_summary",
    header: "财务汇总",
    cell: (row: ReconciliationBatch) => (
      <div className="text-sm space-y-1">
        <div className="flex justify-between">
          <span className="text-gray-600">系统:</span>
          <span>¥{row.total_system_spend.toLocaleString()}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">平台:</span>
          <span>¥{row.total_platform_spend.toLocaleString()}</span>
        </div>
        <div className="flex justify-between font-medium">
          <span className="text-gray-600">差异:</span>
          <span className={row.total_difference >= 0 ? "text-green-600" : "text-red-600"}>
            ¥{Math.abs(row.total_difference).toLocaleString()}
          </span>
        </div>
      </div>
    ),
  },
  {
    id: "platform_source",
    header: "平台数据源",
    cell: (row: ReconciliationBatch) => {
      const sourceConfig = {
        manual: { text: "手动录入", color: "bg-gray-100 text-gray-700" },
        api: { text: "API获取", color: "bg-blue-100 text-blue-700" },
        file: { text: "文件上传", color: "bg-green-100 text-green-700" },
      };

      const config = sourceConfig[row.platform_spend_source];

      return (
        <div className="space-y-1">
          <Badge variant="outline" className={config.color}>
            {config.text}
          </Badge>
          {row.uploaded_file && (
            <div className="text-xs text-gray-500">
              {row.uploaded_file.filename}
            </div>
          )}
        </div>
      );
    },
  },
  {
    id: "created_info",
    header: "创建信息",
    cell: (row: ReconciliationBatch) => (
      <div className="text-sm">
        <div className="font-medium">{row.created_by}</div>
        <div className="text-gray-500">
          {format(new Date(row.created_at), "MM/dd HH:mm")}
        </div>
      </div>
    ),
  },
  {
    id: "actions",
    header: "操作",
    cell: (row: ReconciliationBatch) => (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="sm">
            <Settings className="w-4 h-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuLabel>操作</DropdownMenuLabel>
          <DropdownMenuItem>
            <Eye className="w-4 h-4 mr-2" />
            查看详情
          </DropdownMenuItem>
          {row.status === "completed" && (
            <DropdownMenuItem>
              <FileSpreadsheet className="w-4 h-4 mr-2" />
              导出报告
            </DropdownMenuItem>
          )}
          <DropdownMenuSeparator />
          {row.status === "pending" && (
            <DropdownMenuItem>
              <RefreshCw className="w-4 h-4 mr-2" />
              开始对账
            </DropdownMenuItem>
          )}
          {(row.status === "pending" || row.status === "failed") && (
            <DropdownMenuItem>
              <Upload className="w-4 h-4 mr-2" />
              上传平台账单
            </DropdownMenuItem>
          )}
          <DropdownMenuItem className="text-red-600">
            <XCircle className="w-4 h-4 mr-2" />
            删除批次
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export default function ReconciliationPage() {
  const [batches, setBatches] = useState<ReconciliationBatch[]>([]);
  const [summary, setSummary] = useState<ReconciliationSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // 新建批次表单数据
  const [newBatch, setNewBatch] = useState({
    batch_name: "",
    period_start: startOfMonth(subDays(new Date(), 1)),
    period_end: endOfMonth(subDays(new Date(), 1)),
    platform_spend_source: "manual" as "manual" | "api" | "file",
    notes: "",
  });

  // 状态选项
  const statusOptions = [
    { value: "all", label: "所有状态" },
    { value: "pending", label: "待处理" },
    { value: "in_progress", label: "对账中" },
    { value: "completed", label: "已完成" },
    { value: "failed", label: "失败" },
    { value: "cancelled", label: "已取消" },
  ];

  // 模拟数据
  const mockBatches: ReconciliationBatch[] = [
    {
      id: 1,
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
      notes: "月度例行对账，发现3个账户有小额差异",
      platform_spend_source: "api",
    },
    {
      id: 2,
      batch_name: "2024年11月对账",
      period_start: "2024-11-01T00:00:00Z",
      period_end: "2024-11-30T23:59:59Z",
      status: "completed",
      total_accounts: 23,
      processed_accounts: 23,
      total_discrepancies: 0,
      total_system_spend: 98000,
      total_platform_spend: 98000,
      total_difference: 0,
      difference_percentage: 0,
      created_by: "财务部-李四",
      created_at: "2024-12-05T10:15:00Z",
      completed_at: "2024-12-05T14:20:00Z",
      notes: "无差异，对账完成",
      platform_spend_source: "file",
      uploaded_file: {
        filename: "facebook_bill_202411.xlsx",
        size: 1024000,
        upload_time: "2024-12-05T10:30:00Z",
      },
    },
    {
      id: 3,
      batch_name: "2025年1月对账",
      period_start: "2025-01-01T00:00:00Z",
      period_end: "2025-01-31T23:59:59Z",
      status: "in_progress",
      total_accounts: 28,
      processed_accounts: 15,
      total_discrepancies: 2,
      total_system_spend: 45000,
      total_platform_spend: 0, // 还未获取平台数据
      total_difference: 45000,
      difference_percentage: 100, // 临时值
      created_by: "财务部-王五",
      created_at: "2025-02-01T09:00:00Z",
      notes: "正在处理中，已获取系统数据",
      platform_spend_source: "manual",
    },
  ];

  const mockSummary: ReconciliationSummary = {
    total_batches: 15,
    pending_batches: 1,
    completed_batches: 12,
    total_difference: -1250,
    avg_difference_percentage: -0.08,
    last_sync_time: "2025-01-12T18:30:00Z",
    upcoming_batches: 2,
  };

  // 获取对账批次列表
  const fetchBatches = async () => {
    setLoading(true);
    try {
      // 实际应该调用API
      // const response = await fetch(`/api/v1/reconciliation/batches?page=${currentPage}&size=10`);
      // const result = await response.json();

      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 800));

      setBatches(mockBatches);
      setTotalCount(mockBatches.length);
      setTotalPages(Math.ceil(mockBatches.length / 10));
    } catch (error) {
      toast.error("获取对账批次失败");
      console.error("获取对账批次错误:", error);
    } finally {
      setLoading(false);
    }
  };

  // 获取汇总数据
  const fetchSummary = async () => {
    try {
      // const response = await fetch("/api/v1/reconciliation/summary");
      // const result = await response.json();

      setSummary(mockSummary);
    } catch (error) {
      console.error("获取汇总数据错误:", error);
    }
  };

  // 创建新的对账批次
  const handleCreateBatch = async () => {
    if (!newBatch.batch_name.trim()) {
      toast.error("请输入批次名称");
      return;
    }

    try {
      const response = await fetch("/api/v1/reconciliation/batches", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...newBatch,
          period_start: format(newBatch.period_start, "yyyy-MM-dd"),
          period_end: format(newBatch.period_end, "yyyy-MM-dd"),
        }),
      });

      if (response.ok) {
        toast.success("对账批次创建成功");
        setShowCreateDialog(false);
        setNewBatch({
          batch_name: "",
          period_start: startOfMonth(subDays(new Date(), 1)),
          period_end: endOfMonth(subDays(new Date(), 1)),
          platform_spend_source: "manual",
          notes: "",
        });
        fetchBatches();
      }
    } catch (error) {
      toast.error("创建批次失败");
    }
  };

  // 开始对账
  const handleStartReconciliation = async (batchId: number) => {
    try {
      const response = await fetch(`/api/v1/reconciliation/batches/${batchId}/start`, {
        method: "POST",
      });

      if (response.ok) {
        toast.success("对账已开始");
        fetchBatches();
      }
    } catch (error) {
      toast.error("启动对账失败");
    }
  };

  // 导出报告
  const handleExportReport = async (batchId: number) => {
    try {
      const response = await fetch(`/api/v1/reconciliation/batches/${batchId}/export`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `reconciliation-report-${batchId}-${format(new Date(), "yyyyMMdd")}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        toast.success("报告导出成功");
      }
    } catch (error) {
      toast.error("导出失败");
    }
  };

  // 筛选批次
  const filteredBatches = batches.filter(batch => {
    const matchesSearch = searchTerm === "" ||
      batch.batch_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      batch.created_by.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = selectedStatus === "all" || batch.status === selectedStatus;

    return matchesSearch && matchesStatus;
  });

  useEffect(() => {
    fetchBatches();
    fetchSummary();
  }, [currentPage]);

  return (
    <PageTemplate
      title="财务对账管理"
      description="管理系统消耗记录与平台账单的差异分析和对账处理"
    >
      <div className="space-y-6">
        {/* 汇总统计卡片 */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">总对账批次</p>
                    <p className="text-2xl font-bold">{summary.total_batches}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      已完成: {summary.completed_batches}
                    </p>
                  </div>
                  <FileText className="h-8 w-8 text-muted-foreground" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">待处理批次</p>
                    <p className="text-2xl font-bold text-blue-600">{summary.pending_batches}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      即将开始: {summary.upcoming_batches}
                    </p>
                  </div>
                  <Clock className="h-8 w-8 text-blue-200" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">总差异金额</p>
                    <p className={`text-2xl font-bold ${summary.total_difference >= 0 ? "text-green-600" : "text-red-600"}`}>
                      ¥{Math.abs(summary.total_difference).toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      平均差异率: {summary.avg_difference_percentage.toFixed(2)}%
                    </p>
                  </div>
                  <BarChart3 className="h-8 w-8 text-muted-foreground" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">最后同步</p>
                    <p className="text-2xl font-bold">
                      {format(new Date(summary.last_sync_time), "MM/dd")}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {format(new Date(summary.last_sync_time), "HH:mm")}
                    </p>
                  </div>
                  <RefreshCw className="h-8 w-8 text-muted-foreground" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* 筛选和操作栏 */}
        <Card>
          <CardContent className="p-4">
            <div className="flex flex-col lg:flex-row gap-4">
              {/* 搜索框 */}
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    placeholder="搜索批次名称或创建人..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              {/* 筛选器 */}
              <div className="flex flex-wrap gap-2">
                <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {statusOptions.map(option => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* 操作按钮 */}
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => fetchBatches()}>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  刷新
                </Button>
                <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
                  <DialogTrigger asChild>
                    <Button>
                      <Plus className="w-4 h-4 mr-2" />
                      新建批次
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-md">
                    <DialogHeader>
                      <DialogTitle>创建对账批次</DialogTitle>
                      <DialogDescription>
                        创建新的财务对账批次，指定对账周期和数据源
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="batchName">批次名称</Label>
                        <Input
                          id="batchName"
                          value={newBatch.batch_name}
                          onChange={(e) => setNewBatch({ ...newBatch, batch_name: e.target.value })}
                          placeholder="例如：2024年12月对账"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label>对账开始日期</Label>
                          <Popover>
                            <PopoverTrigger asChild>
                              <Button
                                variant="outline"
                                className={cn(
                                  "w-full justify-start text-left font-normal",
                                  !newBatch.period_start && "text-muted-foreground"
                                )}
                              >
                                <CalendarIcon className="mr-2 h-4 w-4" />
                                {newBatch.period_start ? format(newBatch.period_start, "yyyy年MM月dd日") : "选择日期"}
                              </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-auto p-0">
                              <Calendar
                                mode="single"
                                selected={newBatch.period_start}
                                onSelect={(date) => date && setNewBatch({ ...newBatch, period_start: date })}
                                initialFocus
                              />
                            </PopoverContent>
                          </Popover>
                        </div>
                        <div>
                          <Label>对账结束日期</Label>
                          <Popover>
                            <PopoverTrigger asChild>
                              <Button
                                variant="outline"
                                className={cn(
                                  "w-full justify-start text-left font-normal",
                                  !newBatch.period_end && "text-muted-foreground"
                                )}
                              >
                                <CalendarIcon className="mr-2 h-4 w-4" />
                                {newBatch.period_end ? format(newBatch.period_end, "yyyy年MM月dd日") : "选择日期"}
                              </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-auto p-0">
                              <Calendar
                                mode="single"
                                selected={newBatch.period_end}
                                onSelect={(date) => date && setNewBatch({ ...newBatch, period_end: date })}
                                initialFocus
                              />
                            </PopoverContent>
                          </Popover>
                        </div>
                      </div>
                      <div>
                        <Label htmlFor="platformSource">平台数据源</Label>
                        <Select
                          value={newBatch.platform_spend_source}
                          onValueChange={(value: any) => setNewBatch({ ...newBatch, platform_spend_source: value })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="manual">手动录入</SelectItem>
                            <SelectItem value="api">API获取</SelectItem>
                            <SelectItem value="file">文件上传</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label htmlFor="notes">备注说明</Label>
                        <Input
                          id="notes"
                          value={newBatch.notes}
                          onChange={(e) => setNewBatch({ ...newBatch, notes: e.target.value })}
                          placeholder="输入批次备注（可选）"
                        />
                      </div>
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                        取消
                      </Button>
                      <Button onClick={handleCreateBatch}>
                        创建批次
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 对账批次列表 */}
        <Card>
          <CardContent className="p-0">
            <DataTable
              columns={columns}
              data={filteredBatches}
              loading={loading}
              pagination={{
                currentPage,
                totalPages,
                totalCount,
                onPageChange: setCurrentPage,
              }}
            />
          </CardContent>
        </Card>
      </div>
    </PageTemplate>
  );
}