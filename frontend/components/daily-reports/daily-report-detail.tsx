"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Calendar,
  DollarSign,
  Users,
  MousePointer,
  Eye,
  Target,
  TrendingUp,
  CheckCircle,
  XCircle,
  Clock
} from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { toast } from "sonner";

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
  reviewer?: {
    id: number;
    nickname: string;
    role: string;
  };
  review_comment?: string;
  review_time?: string;
}

interface DailyReportDetailProps {
  report: DailyReport;
  onReview?: (status: "approved" | "rejected", comment: string) => void;
  isReviewer?: boolean;
}

export function DailyReportDetail({
  report,
  onReview,
  isReviewer = false
}: DailyReportDetailProps) {
  const [reviewComment, setReviewComment] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 状态显示
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "approved":
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case "rejected":
        return <XCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Clock className="w-4 h-4 text-yellow-600" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "approved":
        return "已审核";
      case "rejected":
        return "已拒绝";
      default:
        return "待审核";
    }
  };

  // 计算CTR
  const ctr = report.impressions > 0 ? (report.clicks / report.impressions * 100) : 0;

  // 模拟最近7天的趋势数据
  const trendData = [
    { name: "7天前", spend: Math.random() * 100 + 50, conversions: Math.floor(Math.random() * 10) + 5 },
    { name: "6天前", spend: Math.random() * 100 + 50, conversions: Math.floor(Math.random() * 10) + 5 },
    { name: "5天前", spend: Math.random() * 100 + 50, conversions: Math.floor(Math.random() * 10) + 5 },
    { name: "4天前", spend: Math.random() * 100 + 50, conversions: Math.floor(Math.random() * 10) + 5 },
    { name: "3天前", spend: Math.random() * 100 + 50, conversions: Math.floor(Math.random() * 10) + 5 },
    { name: "2天前", spend: Math.random() * 100 + 50, conversions: Math.floor(Math.random() * 10) + 5 },
    { name: "昨天", spend: Math.random() * 100 + 50, conversions: Math.floor(Math.random() * 10) + 5 },
    { name: "今天", spend: report.spend, conversions: report.conversions },
  ];

  // 处理审核
  const handleReview = async (status: "approved" | "rejected") => {
    if (!reviewComment.trim() && status === "rejected") {
      toast.error("拒绝审核时必须填写审核意见");
      return;
    }

    setIsSubmitting(true);
    try {
      if (onReview) {
        await onReview(status, reviewComment);
      } else {
        // 直接调用API
        const response = await fetch(`/api/v1/daily-reports/${report.id}/review`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            status,
            comment: reviewComment,
          }),
        });

        const data = await response.json();
        if (data.success) {
          toast.success(status === "approved" ? "审核通过" : "已拒绝");
          window.location.reload();
        } else {
          toast.error(data.message || "操作失败");
        }
      }
    } catch (error) {
      console.error("审核错误:", error);
      toast.error("操作失败");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 标题和状态 */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold">{report.campaign_name}</h2>
          <p className="text-gray-600">{report.ad_group_name}</p>
          <div className="flex items-center gap-2 mt-2">
            <Badge variant="outline">{report.ad_account_name}</Badge>
            <div className="flex items-center gap-1">
              {getStatusIcon(report.status)}
              <span className="text-sm">{getStatusText(report.status)}</span>
            </div>
          </div>
        </div>
        <div className="text-right text-sm text-gray-500">
          <div className="flex items-center gap-1">
            <Calendar className="w-4 h-4" />
            {report.report_date}
          </div>
          <div>提交时间: {new Date(report.created_at).toLocaleString()}</div>
        </div>
      </div>

      {/* 核心指标卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">消耗金额</p>
                <p className="text-2xl font-bold text-red-600">
                  ¥{report.spend.toFixed(2)}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-red-200" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">新增粉丝</p>
                <p className="text-2xl font-bold text-blue-600">
                  {report.new_follows}
                </p>
              </div>
              <Users className="w-8 h-8 text-blue-200" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">转化数</p>
                <p className="text-2xl font-bold text-green-600">
                  {report.conversions}
                </p>
              </div>
              <Target className="w-8 h-8 text-green-200" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">ROI</p>
                <p className="text-2xl font-bold text-purple-600">
                  {report.roas.toFixed(2)}
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-purple-200" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 详细数据 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>投放数据</CardTitle>
            <CardDescription>详细的广告投放表现数据</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="flex justify-between">
                <span className="text-gray-600">展示次数</span>
                <span className="font-semibold">{report.impressions.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">点击次数</span>
                <span className="font-semibold">{report.clicks.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">点击率 (CTR)</span>
                <span className="font-semibold">{ctr.toFixed(2)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">单粉成本 (CPL)</span>
                <span className="font-semibold">¥{report.cpl.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">转化成本 (CPA)</span>
                <span className="font-semibold">¥{report.cpa.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">广告创意</span>
                <span className="font-semibold">{report.ad_creative_name || "-"}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>成本分析</CardTitle>
            <CardDescription>投放成本和转化分析</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm text-gray-600">粉丝获取成本占比</span>
                  <span className="text-sm">{((report.cpl * report.new_follows) / report.spend * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${Math.min((report.cpl * report.new_follows) / report.spend * 100, 100)}%` }}
                  ></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm text-gray-600">转化成本占比</span>
                  <span className="text-sm">{((report.cpa * report.conversions) / report.spend * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-600 h-2 rounded-full"
                    style={{ width: `${Math.min((report.cpa * report.conversions) / report.spend * 100, 100)}%` }}
                  ></div>
                </div>
              </div>
            </div>

            <Separator />

            <div className="space-y-2">
              <h4 className="font-semibold">效率指标</h4>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">每千次展示成本 (CPM)</span>
                <span className="text-sm font-semibold">
                  ¥{(report.impressions > 0 ? (report.spend / report.impressions * 1000) : 0).toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">每次点击成本 (CPC)</span>
                <span className="text-sm font-semibold">
                  ¥{(report.clicks > 0 ? (report.spend / report.clicks) : 0).toFixed(2)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 趋势图表 */}
      <Card>
        <CardHeader>
          <CardTitle>投放趋势</CardTitle>
          <CardDescription>最近7天的消耗和转化趋势</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="spend"
                stroke="#ef4444"
                name="消耗金额(¥)"
                strokeWidth={2}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="conversions"
                stroke="#10b981"
                name="转化数"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* 备注 */}
      <Card>
        <CardHeader>
          <CardTitle>备注说明</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-700 whitespace-pre-wrap">
            {report.notes || "暂无备注"}
          </p>
        </CardContent>
      </Card>

      {/* 审核信息 */}
      {report.status !== "pending" && report.reviewer && (
        <Card>
          <CardHeader>
            <CardTitle>审核信息</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">审核人</span>
              <span>{report.reviewer.nickname} ({report.reviewer.role})</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">审核时间</span>
              <span>{report.review_time ? new Date(report.review_time).toLocaleString() : "-"}</span>
            </div>
            {report.review_comment && (
              <div>
                <Label className="text-gray-600">审核意见</Label>
                <p className="mt-1 text-gray-700">{report.review_comment}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 审核操作 */}
      {isReviewer && report.status === "pending" && (
        <Card>
          <CardHeader>
            <CardTitle>审核操作</CardTitle>
            <CardDescription>请对这份日报进行审核</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>审核意见</Label>
              <Textarea
                value={reviewComment}
                onChange={(e) => setReviewComment(e.target.value)}
                placeholder="请填写审核意见（拒绝时必填）"
                rows={3}
              />
            </div>
            <div className="flex justify-end space-x-2">
              <Button
                variant="outline"
                onClick={() => handleReview("rejected")}
                disabled={isSubmitting}
              >
                拒绝
              </Button>
              <Button
                onClick={() => handleReview("approved")}
                disabled={isSubmitting}
                className="bg-green-600 hover:bg-green-700"
              >
                通过
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}