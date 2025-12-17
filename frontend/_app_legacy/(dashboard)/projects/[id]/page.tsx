"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { PageTemplate } from "@/components/layout/page-template";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import {
  ArrowLeft,
  Edit,
  DollarSign,
  Users,
  Target,
  Calendar,
  TrendingUp,
  BarChart3,
  PieChart,
  Clock,
  CheckCircle,
  AlertTriangle,
  FileText,
  Plus,
  Settings,
  Download,
  Share,
  Activity,
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
import { ProjectForm } from "@/components/projects/project-form";
import { toast } from "sonner";
import { format, subDays } from "date-fns";

// 类型定义
interface Project {
  id: number;
  name: string;
  client_name: string;
  description: string;
  currency: string;
  budget: number;
  current_spend: number;
  status: "planning" | "active" | "paused" | "completed" | "archived";
  priority: "low" | "medium" | "high";
  start_date: string;
  end_date: string;
  progress: number;
  team_lead_id: number;
  team_lead_name: string;
  team_members: Array<{
    id: number;
    name: string;
    role: string;
    avatar?: string;
  }>;
  ad_accounts_count: number;
  last_activity: string;
  created_at: string;
  updated_at: string;
  roi: number;
  conversion_rate: number;
  tags: string[];
  objectives: string[];
  deliverables: string[];
  notes: string;
  documents: Array<{
    id: number;
    name: string;
    url: string;
    upload_time: string;
    file_size: number;
    uploaded_by: string;
  }>;
  performance_metrics: {
    total_spend: number;
    total_conversions: number;
    total_follows: number;
    avg_cpl: number;
    avg_cpa: number;
    avg_roas: number;
  };
  timeline_events: Array<{
    id: number;
    date: string;
    type: "milestone" | "update" | "issue" | "achievement";
    title: string;
    description: string;
    user: string;
  }>;
  risk_assessment: {
    risk_level: "low" | "medium" | "high";
    risk_factors: string[];
    recommendations: string[];
  };
}

const COLORS = ["#8884d8", "#82ca9d", "#ffc658", "#ff7c7c", "#8dd1e1", "#d084d0"];

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [showEditDialog, setShowEditDialog] = useState(false);

  // 模拟项目数据
  const mockProject: Project = {
    id: parseInt(params.id as string),
    name: "春季推广活动",
    client_name: "ABC科技公司",
    description: "针对新品上市的全方位推广活动，通过多渠道整合营销，提升品牌知名度和产品销量。项目涵盖社交媒体广告、搜索引擎营销、内容营销等多个方面。",
    currency: "USD",
    budget: 50000,
    current_spend: 32500,
    status: "active",
    priority: "high",
    start_date: "2025-01-01",
    end_date: "2025-03-31",
    progress: 65,
    team_lead_id: 1,
    team_lead_name: "张经理",
    team_members: [
      { id: 1, name: "张经理", role: "项目负责人", avatar: "/avatars/zhang.jpg" },
      { id: 2, name: "李投手", role: "广告投手", avatar: "/avatars/li.jpg" },
      { id: 3, name: "王数据", role: "数据分析师", avatar: "/avatars/wang.jpg" },
      { id: 4, name: "赵设计", role: "设计师", avatar: "/avatars/zhao.jpg" },
      { id: 5, name: "陈优化", role: "优化师", avatar: "/avatars/chen.jpg" },
    ],
    ad_accounts_count: 8,
    last_activity: "2025-01-12T14:30:00Z",
    created_at: "2024-12-15T09:00:00Z",
    updated_at: "2025-01-12T14:30:00Z",
    roi: 3.8,
    conversion_rate: 0.025,
    tags: ["电商", "新品推广", "Q1目标", "社交媒体"],
    objectives: [
      "提升品牌知名度30%",
      "实现新品销量5000件",
      "获取新粉丝10万人",
      "建立品牌社交媒体影响力",
    ],
    deliverables: [
      "社交媒体广告策略方案",
      "月度投放数据分析报告",
      "创意素材库（50+张）",
      "转化优化建议书",
      "项目总结报告",
    ],
    notes: "项目进展顺利，重点关注ROI提升和成本控制。建议增加视频广告内容，提高用户参与度。",
    documents: [
      {
        id: 1,
        name: "项目计划书.pdf",
        url: "/docs/project-plan.pdf",
        upload_time: "2024-12-15T09:00:00Z",
        file_size: 2048000,
        uploaded_by: "张经理",
      },
      {
        id: 2,
        name: "创意素材库.zip",
        url: "/docs/creative-assets.zip",
        upload_time: "2025-01-05T14:30:00Z",
        file_size: 5120000,
        uploaded_by: "赵设计",
      },
      {
        id: 3,
        name: "1月投放报告.xlsx",
        url: "/docs/january-report.xlsx",
        upload_time: "2025-02-01T10:15:00Z",
        file_size: 1024000,
        uploaded_by: "王数据",
      },
    ],
    performance_metrics: {
      total_spend: 32500,
      total_conversions: 812,
      total_follows: 2150,
      avg_cpl: 15.12,
      avg_cpa: 40.02,
      avg_roas: 3.8,
    },
    timeline_events: [
      {
        id: 1,
        date: "2024-12-15T09:00:00Z",
        type: "milestone",
        title: "项目启动",
        description: "项目正式启动，团队组建完成",
        user: "张经理",
      },
      {
        id: 2,
        date: "2025-01-01T00:00:00Z",
        type: "milestone",
        title: "投放开始",
        description: "正式开始广告投放",
        user: "李投手",
      },
      {
        id: 3,
        date: "2025-01-10T15:30:00Z",
        type: "achievement",
        title: "达成月度目标",
        description: "超额完成1月份销量目标",
        user: "张经理",
      },
      {
        id: 4,
        date: "2025-01-12T14:30:00Z",
        type: "update",
        title: "预算调整",
        description: "根据ROI表现调整投放策略",
        user: "陈优化",
      },
    ],
    risk_assessment: {
      risk_level: "low",
      risk_factors: [
        "市场竞争加剧",
        "素材更新频率需要提升",
      ],
      recommendations: [
        "加强竞品分析",
        "建立创意素材更新机制",
        "优化投放时间分配",
      ],
    },
  };

  // 模拟趋势数据
  const performanceTrendData = [
    { date: "2025-01-01", spend: 2800, conversions: 68, follows: 180, roi: 3.2 },
    { date: "2025-01-07", spend: 3200, conversions: 85, follows: 210, roi: 3.8 },
    { date: "2025-01-14", spend: 3100, conversions: 78, follows: 195, roi: 3.6 },
    { date: "2025-01-21", spend: 3500, conversions: 95, follows: 240, roi: 4.1 },
    { date: "2025-01-28", spend: 3300, conversions: 88, follows: 220, roi: 3.9 },
    { date: "2025-02-04", spend: 3600, subscribers: 102, follows: 265, roi: 4.2 },
    { date: "2025-02-11", spend: 3400, conversions: 92, follows: 230, roi: 4.0 },
    { date: "2025-02-18", spend: 3800, conversions: 115, follows: 290, roi: 4.5 },
    { date: "2025-02-25", spend: 3700, conversions: 108, follows: 275, roi: 4.3 },
    { date: "2025-03-04", spend: 3900, conversions: 118, follows: 305, roi: 4.6 },
    { date: "2025-03-11", spend: 4100, conversions: 125, follows: 320, roi: 4.8 },
    { date: "2025-03-18", spend: 4000, conversions: 120, follows: 310, roi: 4.7 },
  ];

  // 获取项目详情
  const fetchProjectDetail = async () => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/v1/projects/${params.id}`);
      const result = await response.json();

      if (result.success) {
        // 将API数据转换为前端需要的格式
        const projectData = {
          ...result.data,
          team_members: mockProject.team_members, // 暂时保留模拟的团队成员数据
          tags: mockProject.tags,
          objectives: mockProject.objectives,
          deliverables: mockProject.deliverables,
          notes: mockProject.notes,
          documents: mockProject.documents,
          performance_metrics: mockProject.performance_metrics,
          timeline_events: mockProject.timeline_events,
          risk_assessment: mockProject.risk_assessment,
        };
        setProject(projectData);
      } else {
        toast.error(result.message || "获取项目详情失败");
      }
    } catch (error) {
      toast.error("获取项目详情失败");
      console.error("获取项目详情错误:", error);
      // 如果API失败，回退到模拟数据
      setProject(mockProject);
    } finally {
      setLoading(false);
    }
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  useEffect(() => {
    if (params.id) {
      fetchProjectDetail();
    }
  }, [params.id]);

  if (loading || !project) {
    return (
      <PageTemplate title="项目详情" description="加载中...">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </PageTemplate>
    );
  }

  return (
    <PageTemplate
      title={project.name}
      description={
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="bg-purple-50 text-purple-700">
            {project.client_name}
          </Badge>
          <Badge variant="outline" className={
            project.priority === "high" ? "bg-red-50 text-red-700" :
            project.priority === "medium" ? "bg-yellow-50 text-yellow-700" :
            "bg-green-50 text-green-700"
          }>
            {project.priority === "high" ? "高优先级" :
             project.priority === "medium" ? "中优先级" : "低优先级"}
          </Badge>
        </div>
      }
      breadcrumbs={[
        { label: "项目管理", href: "/projects" },
        { label: project.name },
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
            <Button variant="outline" onClick={() => setShowEditDialog(true)}>
              <Edit className="w-4 h-4 mr-2" />
              编辑项目
            </Button>
            <Button variant="outline">
              <Share className="w-4 h-4 mr-2" />
              分享
            </Button>
            <Button variant="outline">
              <Download className="w-4 h-4 mr-2" />
              导出报告
            </Button>
          </div>
        </div>

        {/* 项目概览卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">项目进度</p>
                  <p className="text-2xl font-bold">{project.progress}%</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {format(new Date(project.start_date), "yyyy/MM/dd")} - {format(new Date(project.end_date), "yyyy/MM/dd")}
                  </p>
                </div>
                <Target className="h-8 w-8 text-muted-foreground" />
              </div>
              <Progress value={project.progress} className="mt-2" />
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">预算使用</p>
                  <p className="text-2xl font-bold">¥{project.current_spend.toLocaleString()}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    总预算: ¥{project.budget.toLocaleString()}
                  </p>
                </div>
                <DollarSign className="h-8 w-8 text-muted-foreground" />
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div
                  className={`h-2 rounded-full ${
                    (project.current_spend / project.budget) > 1
                      ? "bg-red-500"
                      : (project.current_spend / project.budget) > 0.8
                      ? "bg-yellow-500"
                      : "bg-green-500"
                  }`}
                  style={{ width: `${Math.min((project.current_spend / project.budget) * 100, 100)}%` }}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">投资回报率</p>
                  <p className="text-2xl font-bold text-green-600">{project.roi.toFixed(2)}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    转化率: {(project.conversion_rate * 100).toFixed(1)}%
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
                  <p className="text-sm font-medium text-gray-600">团队规模</p>
                  <p className="text-2xl font-bold">{project.team_members.length}人</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {project.ad_accounts_count}个广告账户
                  </p>
                </div>
                <Users className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 项目详情标签页 */}
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">概览</TabsTrigger>
            <TabsTrigger value="performance">表现分析</TabsTrigger>
            <TabsTrigger value="team">团队管理</TabsTrigger>
            <TabsTrigger value="timeline">时间线</TabsTrigger>
            <TabsTrigger value="documents">文档资料</TabsTrigger>
            <TabsTrigger value="risks">风险评估</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <div className="space-y-6">
              {/* 基本信息 */}
              <Card>
                <CardHeader>
                  <CardTitle>基本信息</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div>
                        <span className="text-sm text-gray-600">项目描述</span>
                        <p className="mt-1">{project.description}</p>
                      </div>
                      <div>
                        <span className="text-sm text-gray-600">项目标签</span>
                        <div className="flex flex-wrap gap-2 mt-1">
                          {project.tags.map((tag, index) => (
                            <Badge key={index} variant="outline">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <div>
                        <span className="text-sm text-gray-600">项目目标</span>
                        <ul className="mt-1 space-y-1">
                          {project.objectives.map((objective, index) => (
                            <li key={index} className="flex items-start gap-2">
                              <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                              <span className="text-sm">{objective}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <span className="text-sm text-gray-600">主要交付物</span>
                        <ul className="mt-1 space-y-1">
                          {project.deliverables.map((deliverable, index) => (
                            <li key={index} className="flex items-start gap-2">
                              <FileText className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                              <span className="text-sm">{deliverable}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* 备注信息 */}
              {project.notes && (
                <Card>
                  <CardHeader>
                    <CardTitle>备注说明</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-700">{project.notes}</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          <TabsContent value="performance">
            <div className="space-y-6">
              {/* 性能指标 */}
              <Card>
                <CardHeader>
                  <CardTitle>关键性能指标</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        ¥{project.performance_metrics.total_spend.toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-600">总消耗</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {project.performance_metrics.total_conversions}
                      </div>
                      <div className="text-sm text-gray-600">总转化</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">
                        {project.performance_metrics.total_follows.toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-600">新增粉丝</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-orange-600">
                        ¥{project.performance_metrics.avg_cpl.toFixed(2)}
                      </div>
                      <div className="text-sm text-gray-600">平均CPL</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-red-600">
                        ¥{project.performance_metrics.avg_cpa.toFixed(2)}
                      </div>
                      <div className="text-sm text-gray-600">平均CPA</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {project.performance_metrics.avg_roas.toFixed(2)}
                      </div>
                      <div className="text-sm text-gray-600">平均ROAS</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* 趋势图表 */}
              <Card>
                <CardHeader>
                  <CardTitle>表现趋势</CardTitle>
                  <CardDescription>项目期间的关键指标变化趋势</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={performanceTrendData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis yAxisId="left" />
                      <YAxis yAxisId="right" orientation="right" />
                      <Tooltip />
                      <Legend />
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
                      <Line
                        yAxisId="right"
                        type="monotone"
                        dataKey="follows"
                        stroke="#3b82f6"
                        name="新增粉丝"
                        strokeWidth={2}
                      />
                      <Line
                        yAxisId="right"
                        type="monotone"
                        dataKey="roi"
                        stroke="#8b5cf6"
                        name="ROI"
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="team">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>团队成员</span>
                  <Button size="sm">
                    <Plus className="w-4 h-4 mr-2" />
                    添加成员
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {project.team_members.map((member) => (
                    <div key={member.id} className="flex items-center gap-3 p-3 border rounded-lg">
                      <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                        {member.avatar ? (
                          <img
                            src={member.avatar}
                            alt={member.name}
                            className="w-10 h-10 rounded-full"
                          />
                        ) : (
                          <Users className="w-5 h-5 text-gray-500" />
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="font-medium">{member.name}</div>
                        <div className="text-sm text-gray-500">{member.role}</div>
                      </div>
                      <Button variant="ghost" size="sm">
                        <Settings className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="timeline">
            <Card>
              <CardHeader>
                <CardTitle>项目时间线</CardTitle>
                <CardDescription>项目的重要节点和活动记录</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {project.timeline_events.map((event, index) => (
                    <div key={event.id} className="flex gap-4">
                      <div className="flex flex-col items-center">
                        <div className={`w-3 h-3 rounded-full ${
                          event.type === "milestone" ? "bg-blue-500" :
                          event.type === "achievement" ? "bg-green-500" :
                          event.type === "issue" ? "bg-red-500" : "bg-gray-500"
                        }`} />
                        {index < project.timeline_events.length - 1 && (
                          <div className="w-0.5 h-16 bg-gray-300" />
                        )}
                      </div>
                      <div className="flex-1 pb-8">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm text-gray-500">
                            {format(new Date(event.date), "yyyy-MM-dd HH:mm")}
                          </span>
                          <Badge variant="outline" className={
                            event.type === "milestone" ? "border-blue-500 text-blue-700" :
                            event.type === "achievement" ? "border-green-500 text-green-700" :
                            event.type === "issue" ? "border-red-500 text-red-700" : "border-gray-500"
                          }>
                            {event.type === "milestone" ? "里程碑" :
                             event.type === "achievement" ? "成就" :
                             event.type === "issue" ? "问题" : "更新"}
                          </Badge>
                        </div>
                        <div className="font-medium">{event.title}</div>
                        <div className="text-sm text-gray-600 mt-1">{event.description}</div>
                        <div className="text-xs text-gray-500 mt-1">by {event.user}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="documents">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>文档资料</span>
                  <Button size="sm">
                    <Plus className="w-4 h-4 mr-2" />
                    上传文档
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {project.documents.map((doc) => (
                    <div key={doc.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <FileText className="w-8 h-8 text-blue-500" />
                        <div>
                          <div className="font-medium">{doc.name}</div>
                          <div className="text-sm text-gray-500">
                            {formatFileSize(doc.file_size)} • {format(new Date(doc.upload_time), "yyyy-MM-dd")}
                          </div>
                          <div className="text-xs text-gray-500">上传者: {doc.uploaded_by}</div>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm">
                          <Activity className="w-4 h-4 mr-2" />
                          预览
                        </Button>
                        <Button variant="outline" size="sm">
                          <Download className="w-4 h-4 mr-2" />
                          下载
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="risks">
            <div className="space-y-6">
              {/* 风险评估 */}
              <Card>
                <CardHeader>
                  <CardTitle>风险评估</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">风险等级:</span>
                      <Badge className={
                        project.risk_assessment.risk_level === "high" ? "bg-red-100 text-red-700" :
                        project.risk_assessment.risk_level === "medium" ? "bg-yellow-100 text-yellow-700" :
                        "bg-green-100 text-green-700"
                      }>
                        {project.risk_assessment.risk_level === "high" ? "高风险" :
                         project.risk_assessment.risk_level === "medium" ? "中等风险" : "低风险"}
                      </Badge>
                    </div>

                    <div>
                      <span className="text-sm font-medium">风险因素:</span>
                      <ul className="mt-2 space-y-1">
                        {project.risk_assessment.risk_factors.map((factor, index) => (
                          <li key={index} className="flex items-start gap-2">
                            <AlertTriangle className="w-4 h-4 text-orange-500 mt-0.5 flex-shrink-0" />
                            <span className="text-sm">{factor}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* 改进建议 */}
              <Card>
                <CardHeader>
                  <CardTitle>改进建议</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {project.risk_assessment.recommendations.map((recommendation, index) => (
                      <div key={index} className="flex items-start gap-2">
                        <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                        <span className="text-sm">{recommendation}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>

        {/* 编辑项目对话框 */}
        {showEditDialog && (
          <ProjectForm
            open={showEditDialog}
            onClose={() => setShowEditDialog(false)}
            onSubmit={async (data) => {
              try {
                const response = await fetch(`/api/v1/projects/${project.id}`, {
                  method: "PUT",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify(data),
                });

                if (response.ok) {
                  toast.success("项目更新成功");
                  setShowEditDialog(false);
                  fetchProjectDetail();
                }
              } catch (error) {
                toast.error("更新失败");
              }
            }}
            editData={project}
            mode="edit"
          />
        )}
      </div>
    </PageTemplate>
  );
}