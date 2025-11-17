'use client';

import React, { useState, useEffect } from "react";
import PageLayout from "@/components/layout/page-template";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Plus, CalendarIcon } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { format, subDays, startOfMonth, endOfMonth } from "date-fns";
import { cn } from "@/lib/utils";

// 导入新开发的组件
import { ReconciliationSummaryCards } from "./components/ReconciliationSummaryCards";
import { ReconciliationFilters } from "./components/ReconciliationFilters";
import { ReconciliationTable } from "./components/ReconciliationTable";

// 导入类型定义
import {
  ReconciliationBatch,
  ReconciliationSummary,
  ReconciliationFilters as IReconciliationFilters,
  ReconciliationStatus,
  PlatformSpendSource
} from "./types";

export default function ReconciliationPage() {
  const [batches, setBatches] = useState<ReconciliationBatch[]>([]);
  const [summary, setSummary] = useState<ReconciliationSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [totalCount, setTotalCount] = useState(0);

  // 筛选器状态
  const [filters, setFilters] = useState<IReconciliationFilters>({
    search_term: '',
    status: 'all',
    platform_spend_source: 'all',
    date_range: 'last_30_days',
    custom_date_range: {
      start: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
      end: format(new Date(), 'yyyy-MM-dd')
    },
    difference_range: { min: undefined, max: undefined },
    discrepancy_range: { min: undefined, max: undefined },
    sort_by: 'created_at',
    sort_order: 'desc'
  });

  // 新建批次表单数据
  const [newBatch, setNewBatch] = useState({
    batch_name: "",
    period_start: startOfMonth(subDays(new Date(), 1)),
    period_end: endOfMonth(subDays(new Date(), 1)),
    platform_spend_source: "manual" as PlatformSpendSource,
    notes: "",
  });

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
      created_by: 1,
      created_by_name: "财务部-张三",
      created_at: "2025-01-05T09:00:00Z",
      completed_at: "2025-01-05T11:30:00Z",
      notes: "月度例行对账，发现3个账户有小额差异",
      platform_spend_source: "api",
      uploaded_file: undefined
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
      created_by: 2,
      created_by_name: "财务部-李四",
      created_at: "2024-12-05T10:15:00Z",
      completed_at: "2024-12-05T14:20:00Z",
      notes: "无差异，对账完成",
      platform_spend_source: "file",
      uploaded_file: {
        filename: "facebook_bill_202411.xlsx",
        size: 1024000,
        upload_time: "2024-12-05T10:30:00Z",
      }
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
      created_by: 3,
      created_by_name: "财务部-王五",
      created_at: "2025-02-01T09:00:00Z",
      notes: "正在处理中，已获取系统数据",
      platform_spend_source: "manual",
      uploaded_file: undefined
    },
    {
      id: 4,
      batch_name: "2025年2月对账",
      period_start: "2025-02-01T00:00:00Z",
      period_end: "2025-02-28T23:59:59Z",
      status: "pending",
      total_accounts: 30,
      processed_accounts: 0,
      total_discrepancies: 0,
      total_system_spend: 0,
      total_platform_spend: 0,
      total_difference: 0,
      difference_percentage: 0,
      created_by: 1,
      created_by_name: "财务部-张三",
      created_at: "2025-03-01T09:00:00Z",
      notes: "准备开始3月对账",
      platform_spend_source: "api",
      uploaded_file: undefined
    },
    {
      id: 5,
      batch_name: "2024年10月对账",
      period_start: "2024-10-01T00:00:00Z",
      period_end: "2024-10-31T23:59:59Z",
      status: "failed",
      total_accounts: 20,
      processed_accounts: 18,
      total_discrepancies: 8,
      total_system_spend: 87000,
      total_platform_spend: 86500,
      total_difference: -500,
      difference_percentage: -0.58,
      created_by: 2,
      created_by_name: "财务部-李四",
      created_at: "2024-11-05T10:00:00Z",
      notes: "对账过程中发现异常，需要人工处理",
      platform_spend_source: "file",
      uploaded_file: {
        filename: "facebook_bill_202410.xlsx",
        size: 980000,
        upload_time: "2024-11-05T10:15:00Z",
      }
    }
  ];

  const mockSummary: ReconciliationSummary = {
    total_batches: 15,
    pending_batches: 2,
    in_progress_batches: 1,
    completed_batches: 10,
    failed_batches: 2,
    cancelled_batches: 0,
    total_difference: -1250,
    total_system_spend: 455000,
    total_platform_spend: 453750,
    avg_difference_percentage: -0.08,
    total_discrepancies: 25,
    auto_match_rate: 89.5,
    last_sync_time: "2025-01-12T18:30:00Z"
  };

  // 获取对账批次列表
  const fetchBatches = async () => {
    setLoading(true);
    try {
      // 实际应该调用API
      await new Promise(resolve => setTimeout(resolve, 800));
      setBatches(mockBatches);
      setTotalCount(mockBatches.length);
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

  // 处理筛选器重置
  const handleFiltersReset = () => {
    setFilters({
      search_term: '',
      status: 'all',
      platform_spend_source: 'all',
      date_range: 'last_30_days',
      custom_date_range: {
        start: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
        end: format(new Date(), 'yyyy-MM-dd')
      },
      difference_range: { min: undefined, max: undefined },
      discrepancy_range: { min: undefined, max: undefined },
      sort_by: 'created_at',
      sort_order: 'desc'
    });
  };

  // 处理数据导出
  const handleExport = () => {
    toast.info("导出功能开发中...");
  };

  // 处理行点击
  const handleRowClick = (batch: ReconciliationBatch) => {
    toast.info(`查看批次详情: ${batch.batch_name}`);
  };

  // 处理查看详情
  const handleViewDetail = (batch: ReconciliationBatch) => {
    toast.info(`查看详情: ${batch.batch_name}`);
  };

  // 处理开始对账
  const handleStartReconciliation = (batch: ReconciliationBatch) => {
    toast.success(`开始对账: ${batch.batch_name}`);
  };

  // 处理暂停对账
  const handlePauseReconciliation = (batch: ReconciliationBatch) => {
    toast.info(`暂停对账: ${batch.batch_name}`);
  };

  // 处理导出报告
  const handleExportReport = (batch: ReconciliationBatch) => {
    toast.info(`导出报告: ${batch.batch_name}`);
  };

  // 处理上传平台数据
  const handleUploadPlatformData = (batch: ReconciliationBatch) => {
    toast.info(`上传平台账单: ${batch.batch_name}`);
  };

  // 处理删除批次
  const handleDelete = (batchId: number) => {
    const batch = batches.find(b => b.id === batchId);
    if (batch) {
      toast.success(`删除批次: ${batch.batch_name}`);
      fetchBatches();
    }
  };

  useEffect(() => {
    fetchBatches();
    fetchSummary();
  }, []);

  return (
    <PageLayout
      title="财务对账管理"
      description="管理系统消耗记录与平台账单的差异分析和对账处理"
    >
      {/* KPI 统计卡片 */}
      {summary && (
        <ReconciliationSummaryCards
          stats={summary}
          loading={loading}
        />
      )}

      {/* 筛选器组件 */}
      <ReconciliationFilters
        filters={filters}
        onFiltersChange={setFilters}
        totalCount={totalCount}
        onReset={handleFiltersReset}
        onExport={handleExport}
        onNewReport={() => setShowCreateDialog(true)}
        loading={loading}
      />

      {/* 数据表格组件 */}
      <ReconciliationTable
        data={batches}
        loading={loading}
        selectedIds={selectedIds}
        onSelectionChange={setSelectedIds}
        onRowClick={handleRowClick}
        onViewDetail={handleViewDetail}
        onStartReconciliation={handleStartReconciliation}
        onPauseReconciliation={handlePauseReconciliation}
        onExportReport={handleExportReport}
        onUploadPlatformData={handleUploadPlatformData}
        onDelete={handleDelete}
      />

      {/* 创建批次对话框 */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
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
                onValueChange={(value: PlatformSpendSource) => setNewBatch({ ...newBatch, platform_spend_source: value })}
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
    </PageLayout>
  );
}