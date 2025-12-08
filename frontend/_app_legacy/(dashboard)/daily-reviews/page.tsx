"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import { format } from "date-fns";
import { zhCN } from "date-fns/locale";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import {
  CalendarIcon,
  Eye,
  Check,
  X,
  Filter,
  Download,
  BarChart3,
  Clock,
  CheckCircle,
  XCircle,
} from "lucide-react";
import { DailyReportDetail } from "@/components/daily-reports/daily-report-detail";

// 类型定义
interface DailyReport {
  id: number;
  report_date: string;
  ad_account_id: number;
  ad_account_name: string;
  campaign_name: string;
  ad_group_name: string;
  ad_creative_name: string;
  impressions: number;
  clicks: number;
  spend: number;
  conversions: number;
  new_follows: number;
  cpa: number;
  cpl: number;
  roas: number;
  notes: string;
  status: "pending" | "approved" | "rejected";
  created_at: string;
  updated_at: string;
  submitter?: {
    id: number;
    nickname: string;
    email: string;
  };
  reviewer?: {
    id: number;
    nickname: string;
    role: string;
  };
  review_comment?: string;
  review_time?: string;
}

interface ReviewStats {
  total: number;
  pending: number;
  approved: number;
  rejected: number;
  total_spend: number;
  avg_cpl: number;
  avg_roas: number;
}

export default function DailyReviewsPage() {
  const [reports, setReports] = useState<DailyReport[]>([]);
  const [stats, setStats] = useState<ReviewStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState<DailyReport | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [batchReviewOpen, setBatchReviewOpen] = useState(false);
  const [selectedReports, setSelectedReports] = useState<number[]>([]);
  const [filters, setFilters] = useState({
    date_from: "",
    date_to: "",
    ad_account_id: "",
    status: "pending",
    submitter_id: "",
  });

  // 获取日报列表
  const fetchReports = async () => {
    try {
      const params = new URLSearchParams();
      if (filters.date_from) params.append("date_from", filters.date_from);
      if (filters.date_to) params.append("date_to", filters.date_to);
      if (filters.ad_account_id) params.append("ad_account_id", filters.ad_account_id);
      if (filters.status) params.append("status", filters.status);
      if (filters.submitter_id) params.append("submitter_id", filters.submitter_id);
      params.append("need_review", "true");

      const response = await fetch(`/api/v1/daily-reports?${params}`);
      const data = await response.json();

      if (data.success) {
        setReports(data.data.items || []);
        setStats(data.data.stats || null);
      } else {
        toast.error("获取日报列表失败");
      }
    } catch (error) {
      console.error("获取日报列表错误:", error);
      toast.error("获取日报列表失败");
    } finally {
      setLoading(false);
    }
  };

  // 批量审核
  const handleBatchReview = async (status: "approved" | "rejected", comment: string) => {
    if (selectedReports.length === 0) {
      toast.error("请先选择要审核的日报");
      return;
    }

    try {
      const response = await fetch("/api/v1/daily-reports/batch-review", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          report_ids: selectedReports,
          status,
          comment,
        }),
      });

      const data = await response.json();

      if (data.success) {
        toast.success(`批量${status === "approved" ? "通过" : "拒绝"}成功`);
        setSelectedReports([]);
        setBatchReviewOpen(false);
        fetchReports();
      } else {
        toast.error(data.message || "批量审核失败");
      }
    } catch (error) {
      console.error("批量审核错误:", error);
      toast.error("批量审核失败");
    }
  };

  // 导出报表
  const handleExport = async () => {
    try {
      const params = new URLSearchParams();
      if (filters.date_from) params.append("date_from", filters.date_from);
      if (filters.date_to) params.append("date_to", filters.date_to);
      if (filters.ad_account_id) params.append("ad_account_id", filters.ad_account_id);
      if (filters.status) params.append("status", filters.status);

      const response = await fetch(`/api/v1/daily-reports/export?${params}`);

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `daily-reports-${format(new Date(), "yyyyMMdd")}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        toast.success("导出成功");
      } else {
        toast.error("导出失败");
      }
    } catch (error) {
      console.error("导出错误:", error);
      toast.error("导出失败");
    }
  };

  // 选择/取消选择
  const toggleSelectReport = (reportId: number) => {
    setSelectedReports((prev) =>
      prev.includes(reportId)
        ? prev.filter((id) => id !== reportId)
        : [...prev, reportId]
    );
  };

  const toggleSelectAll = () => {
    if (selectedReports.length === reports.length) {
      setSelectedReports([]);
    } else {
      setSelectedReports(reports.map((r) => r.id));
    }
  };

  useEffect(() => {
    fetchReports();
  }, [filters]);

  // 状态徽章
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "approved":
        return <Badge className="bg-green-100 text-green-800 flex items-center gap-1"><CheckCircle className="w-3 h-3" />已审核</Badge>;
      case "rejected":
        return <Badge className="bg-red-100 text-red-800 flex items-center gap-1"><XCircle className="w-3 h-3" />已拒绝</Badge>;
      default:
        return <Badge className="bg-yellow-100 text-yellow-800 flex items-center gap-1"><Clock className="w-3 h-3" />待审核</Badge>;
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* 页面标题 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">日报审核</h1>
          <p className="text-gray-600">审核和管理投手提交的日报数据</p>
        </div>
        <div className="flex space-x-2">
          {selectedReports.length > 0 && (
            <Button
              variant="outline"
              onClick={() => setBatchReviewOpen(true)}
            >
              批量审核 ({selectedReports.length})
            </Button>
          )}
          <Button variant="outline" onClick={handleExport}>
            <Download className="w-4 h-4 mr-2" />
            导出报表
          </Button>
        </div>
      </div>

      {/* 统计卡片 */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="text-center">
                <p className="text-2xl font-bold">{stats.total}</p>
                <p className="text-sm text-gray-600">总日报数</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-yellow-600">{stats.pending}</p>
                <p className="text-sm text-gray-600">待审核</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">{stats.approved}</p>
                <p className="text-sm text-gray-600">已通过</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">{stats.rejected}</p>
                <p className="text-sm text-gray-600">已拒绝</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-center">
                <p className="text-2xl font-bold">¥{stats.total_spend.toFixed(0)}</p>
                <p className="text-sm text-gray-600">总消耗</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-center">
                <p className="text-2xl font-bold">{stats.avg_roas.toFixed(2)}</p>
                <p className="text-sm text-gray-600">平均ROI</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 筛选条件 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Filter className="w-5 h-5" />
            筛选条件
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="space-y-2">
              <Label>开始日期</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !filters.date_from && "text-muted-foreground"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {filters.date_from
                      ? format(new Date(filters.date_from), "yyyy年MM月dd日", {
                          locale: zhCN,
                        })
                      : "选择开始日期"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={filters.date_from ? new Date(filters.date_from) : undefined}
                    onSelect={(date) => {
                      if (date) {
                        setFilters({
                          ...filters,
                          date_from: format(date, "yyyy-MM-dd"),
                        });
                      }
                    }}
                    locale={zhCN}
                  />
                </PopoverContent>
              </Popover>
            </div>

            <div className="space-y-2">
              <Label>结束日期</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !filters.date_to && "text-muted-foreground"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {filters.date_to
                      ? format(new Date(filters.date_to), "yyyy年MM月dd日", {
                          locale: zhCN,
                        })
                      : "选择结束日期"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={filters.date_to ? new Date(filters.date_to) : undefined}
                    onSelect={(date) => {
                      if (date) {
                        setFilters({
                          ...filters,
                          date_to: format(date, "yyyy-MM-dd"),
                        });
                      }
                    }}
                    locale={zhCN}
                  />
                </PopoverContent>
              </Popover>
            </div>

            <div className="space-y-2">
              <Label>广告账户</Label>
              <Input
                placeholder="输入账户名称"
                value={filters.ad_account_id}
                onChange={(e) =>
                  setFilters({ ...filters, ad_account_id: e.target.value })
                }
              />
            </div>

            <div className="space-y-2">
              <Label>状态</Label>
              <Select
                value={filters.status}
                onValueChange={(value) =>
                  setFilters({ ...filters, status: value })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择状态" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">全部状态</SelectItem>
                  <SelectItem value="pending">待审核</SelectItem>
                  <SelectItem value="approved">已审核</SelectItem>
                  <SelectItem value="rejected">已拒绝</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>提交人</Label>
              <Input
                placeholder="输入提交人名称"
                value={filters.submitter_id}
                onChange={(e) =>
                  setFilters({ ...filters, submitter_id: e.target.value })
                }
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 日报列表 */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle className="text-lg">日报列表</CardTitle>
              <CardDescription>
                共 {reports.length} 条记录
                {selectedReports.length > 0 && (
                  <span className="ml-2 text-blue-600">
                    已选择 {selectedReports.length} 条
                  </span>
                )}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <input
                      type="checkbox"
                      checked={selectedReports.length === reports.length && reports.length > 0}
                      onChange={toggleSelectAll}
                      className="rounded"
                    />
                  </TableHead>
                  <TableHead>日期</TableHead>
                  <TableHead>提交人</TableHead>
                  <TableHead>广告账户</TableHead>
                  <TableHead>广告系列</TableHead>
                  <TableHead>消耗</TableHead>
                  <TableHead>新增粉丝</TableHead>
                  <TableHead>ROI</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>提交时间</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reports.map((report) => (
                  <TableRow
                    key={report.id}
                    className={report.status === "pending" ? "bg-yellow-50" : ""}
                  >
                    <TableCell>
                      <input
                        type="checkbox"
                        checked={selectedReports.includes(report.id)}
                        onChange={() => toggleSelectReport(report.id)}
                        className="rounded"
                      />
                    </TableCell>
                    <TableCell>{report.report_date}</TableCell>
                    <TableCell>
                      {report.submitter ? (
                        <div>
                          <p className="font-medium">{report.submitter.nickname}</p>
                          <p className="text-sm text-gray-500">{report.submitter.email}</p>
                        </div>
                      ) : (
                        "-"
                      )}
                    </TableCell>
                    <TableCell>{report.ad_account_name}</TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{report.campaign_name}</p>
                        <p className="text-sm text-gray-500">{report.ad_group_name}</p>
                      </div>
                    </TableCell>
                    <TableCell>¥{report.spend.toFixed(2)}</TableCell>
                    <TableCell>{report.new_follows}</TableCell>
                    <TableCell>{report.roas.toFixed(2)}</TableCell>
                    <TableCell>{getStatusBadge(report.status)}</TableCell>
                    <TableCell>
                      {new Date(report.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSelectedReport(report);
                          setIsDetailOpen(true);
                        }}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* 详情对话框 */}
      <Dialog open={isDetailOpen} onOpenChange={setIsDetailOpen}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>日报详情</DialogTitle>
          </DialogHeader>
          {selectedReport && (
            <DailyReportDetail
              report={selectedReport}
              onReview={async (status, comment) => {
                const response = await fetch(`/api/v1/daily-reports/${selectedReport.id}/review`, {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json",
                  },
                  body: JSON.stringify({
                    status,
                    comment,
                  }),
                });

                const data = await response.json();
                if (data.success) {
                  toast.success(status === "approved" ? "审核通过" : "已拒绝");
                  setIsDetailOpen(false);
                  fetchReports();
                } else {
                  toast.error(data.message || "操作失败");
                }
              }}
              isReviewer={true}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* 批量审核对话框 */}
      <Dialog open={batchReviewOpen} onOpenChange={setBatchReviewOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>批量审核日报</DialogTitle>
            <DialogDescription>
              将对选中的 {selectedReports.length} 份日报进行批量审核
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>审核意见</Label>
              <Textarea
                placeholder="请填写批量审核意见"
                rows={3}
              />
            </div>
            <div className="flex justify-end space-x-2">
              <Button
                variant="outline"
                onClick={() => setBatchReviewOpen(false)}
              >
                取消
              </Button>
              <Button
                variant="destructive"
                onClick={() => handleBatchReview("rejected", "")}
              >
                <X className="w-4 h-4 mr-2" />
                批量拒绝
              </Button>
              <Button
                className="bg-green-600 hover:bg-green-700"
                onClick={() => handleBatchReview("approved", "")}
              >
                <Check className="w-4 h-4 mr-2" />
                批量通过
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}