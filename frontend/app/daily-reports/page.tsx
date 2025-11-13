"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import { format } from "date-fns";
import { zhCN } from "date-fns/locale";
import { CalendarIcon, Plus, FileText, Eye, Edit, Trash2 } from "lucide-react";
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
  DialogTrigger,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import { DailyReportForm } from "@/components/daily-reports/daily-report-form";
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
  roas: number;
  notes: string;
  status: "pending" | "approved" | "rejected";
  created_at: string;
  updated_at: string;
}

interface AdAccount {
  id: number;
  name: string;
  platform: string;
  status: string;
}

export default function DailyReportsPage() {
  const [reports, setReports] = useState<DailyReport[]>([]);
  const [adAccounts, setAdAccounts] = useState<AdAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [selectedReport, setSelectedReport] = useState<DailyReport | null>(null);
  const [editingReport, setEditingReport] = useState<DailyReport | null>(null);
  const [filters, setFilters] = useState({
    date: format(new Date(), "yyyy-MM-dd"),
    ad_account_id: "",
    status: "",
  });

  // 获取日报列表
  const fetchReports = async () => {
    try {
      const params = new URLSearchParams();
      if (filters.date) params.append("date", filters.date);
      if (filters.ad_account_id) params.append("ad_account_id", filters.ad_account_id);
      if (filters.status) params.append("status", filters.status);

      const response = await fetch(`/api/v1/daily-reports?${params}`);
      const data = await response.json();

      if (data.success) {
        setReports(data.data.items || []);
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

  // 获取广告账户列表
  const fetchAdAccounts = async () => {
    try {
      const response = await fetch("/api/v1/ad-accounts");
      const data = await response.json();

      if (data.success) {
        setAdAccounts(data.data.items || []);
      }
    } catch (error) {
      console.error("获取广告账户错误:", error);
    }
  };

  // 删除日报
  const handleDelete = async (reportId: number) => {
    if (!confirm("确定要删除这份日报吗？")) return;

    try {
      const response = await fetch(`/api/v1/daily-reports/${reportId}`, {
        method: "DELETE",
      });

      const data = await response.json();

      if (data.success) {
        toast.success("删除成功");
        fetchReports();
      } else {
        toast.error(data.message || "删除失败");
      }
    } catch (error) {
      console.error("删除日报错误:", error);
      toast.error("删除失败");
    }
  };

  // 查看详情
  const handleView = (report: DailyReport) => {
    setSelectedReport(report);
    setIsDetailOpen(true);
  };

  // 编辑
  const handleEdit = (report: DailyReport) => {
    setEditingReport(report);
    setIsFormOpen(true);
  };

  // 表单提交成功
  const handleFormSuccess = () => {
    setIsFormOpen(false);
    setEditingReport(null);
    fetchReports();
  };

  useEffect(() => {
    fetchReports();
    fetchAdAccounts();
  }, [filters]);

  // 状态徽章颜色
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "approved":
        return <Badge className="bg-green-100 text-green-800">已审核</Badge>;
      case "rejected":
        return <Badge className="bg-red-100 text-red-800">已拒绝</Badge>;
      default:
        return <Badge className="bg-yellow-100 text-yellow-800">待审核</Badge>;
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* 页面标题 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">日报管理</h1>
          <p className="text-gray-600">管理和提交广告投放日报</p>
        </div>
        <Dialog open={isFormOpen} onOpenChange={setIsFormOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => setEditingReport(null)}>
              <Plus className="w-4 h-4 mr-2" />
              新建日报
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {editingReport ? "编辑日报" : "新建日报"}
              </DialogTitle>
              <DialogDescription>
                填写广告投放日报数据
              </DialogDescription>
            </DialogHeader>
            <DailyReportForm
              report={editingReport}
              adAccounts={adAccounts}
              onSuccess={handleFormSuccess}
              onCancel={() => {
                setIsFormOpen(false);
                setEditingReport(null);
              }}
            />
          </DialogContent>
        </Dialog>
      </div>

      {/* 筛选条件 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">筛选条件</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>日期</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !filters.date && "text-muted-foreground"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {filters.date
                      ? format(new Date(filters.date), "yyyy年MM月dd日", {
                          locale: zhCN,
                        })
                      : "选择日期"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={new Date(filters.date)}
                    onSelect={(date) => {
                      if (date) {
                        setFilters({
                          ...filters,
                          date: format(date, "yyyy-MM-dd"),
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
              <Select
                value={filters.ad_account_id}
                onValueChange={(value) =>
                  setFilters({ ...filters, ad_account_id: value })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择广告账户" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">全部账户</SelectItem>
                  {adAccounts.map((account) => (
                    <SelectItem key={account.id} value={account.id.toString()}>
                      {account.name} - {account.platform}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
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
          </div>
        </CardContent>
      </Card>

      {/* 日报列表 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">日报列表</CardTitle>
          <CardDescription>
            共 {reports.length} 条记录
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            </div>
          ) : reports.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-semibold text-gray-900">
                暂无日报数据
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                点击上方"新建日报"按钮创建第一份日报
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>日期</TableHead>
                  <TableHead>广告账户</TableHead>
                  <TableHead>广告系列</TableHead>
                  <TableHead>消耗</TableHead>
                  <TableHead>转化</TableHead>
                  <TableHead>ROI</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reports.map((report) => (
                  <TableRow key={report.id}>
                    <TableCell>{report.report_date}</TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{report.ad_account_name}</p>
                        <p className="text-sm text-gray-500">{report.ad_group_name}</p>
                      </div>
                    </TableCell>
                    <TableCell>{report.campaign_name}</TableCell>
                    <TableCell>¥{report.spend.toFixed(2)}</TableCell>
                    <TableCell>{report.conversions}</TableCell>
                    <TableCell>{report.roas.toFixed(2)}</TableCell>
                    <TableCell>{getStatusBadge(report.status)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end space-x-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleView(report)}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        {report.status === "pending" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEdit(report)}
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                        )}
                        {report.status === "pending" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(report.id)}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* 详情对话框 */}
      <Dialog
        open={isDetailOpen}
        onOpenChange={setIsDetailOpen}
      >
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>日报详情</DialogTitle>
          </DialogHeader>
          {selectedReport && (
            <DailyReportDetail report={selectedReport} />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}