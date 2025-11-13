"use client";

import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Plus,
  Target,
  DollarSign,
  Users,
  Calendar,
  MoreHorizontal,
  Clock,
  CheckCircle,
  AlertTriangle,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { format } from "date-fns";

// 类型定义
interface Project {
  id: number;
  name: string;
  client_name: string;
  currency: string;
  budget: number;
  current_spend: number;
  status: "planning" | "active" | "paused" | "completed" | "archived";
  priority: "low" | "medium" | "high";
  start_date: string;
  end_date: string;
  progress: number;
  team_lead_name: string;
  team_members: number;
  ad_accounts_count: number;
  last_activity: string;
  roi: number;
  conversion_rate: number;
  tags: string[];
}

interface ProjectKanbanProps {
  projects: Project[];
  onProjectUpdate: () => void;
}

interface KanbanColumn {
  id: string;
  title: string;
  status: Project["status"];
  projects: Project[];
  color: string;
  icon: React.ReactNode;
}

export function ProjectKanban({ projects, onProjectUpdate }: ProjectKanbanProps) {
  // 按状态分组项目
  const kanbanColumns: KanbanColumn[] = [
    {
      id: "planning",
      title: "规划中",
      status: "planning",
      projects: projects.filter(p => p.status === "planning"),
      color: "border-blue-200 bg-blue-50",
      icon: <Clock className="w-5 h-5 text-blue-600" />,
    },
    {
      id: "active",
      title: "进行中",
      status: "active",
      projects: projects.filter(p => p.status === "active"),
      color: "border-green-200 bg-green-50",
      icon: <CheckCircle className="w-5 h-5 text-green-600" />,
    },
    {
      id: "paused",
      title: "暂停",
      status: "paused",
      projects: projects.filter(p => p.status === "paused"),
      color: "border-yellow-200 bg-yellow-50",
      icon: <AlertTriangle className="w-5 h-5 text-yellow-600" />,
    },
    {
      id: "completed",
      title: "已完成",
      status: "completed",
      projects: projects.filter(p => p.status === "completed"),
      color: "border-purple-200 bg-purple-50",
      icon: <CheckCircle className="w-5 h-5 text-purple-600" />,
    },
    {
      id: "archived",
      title: "已归档",
      status: "archived",
      projects: projects.filter(p => p.status === "archived"),
      color: "border-gray-200 bg-gray-50",
      icon: <Clock className="w-5 h-5 text-gray-600" />,
    },
  ];

  // 获取优先级颜色
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high": return "bg-red-100 text-red-700 border-red-300";
      case "medium": return "bg-yellow-100 text-yellow-700 border-yellow-300";
      case "low": return "bg-green-100 text-green-700 border-green-300";
      default: return "bg-gray-100 text-gray-700 border-gray-300";
    }
  };

  // 获取优先级文本
  const getPriorityText = (priority: string) => {
    switch (priority) {
      case "high": return "高";
      case "medium": return "中";
      case "low": return "低";
      default: return "无";
    }
  };

  // 项目卡片组件
  const ProjectCard = ({ project }: { project: Project }) => (
    <Card className="mb-3 cursor-pointer hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        {/* 项目头部 */}
        <div className="flex justify-between items-start mb-3">
          <div className="flex-1">
            <h3 className="font-medium text-sm mb-1 line-clamp-2">{project.name}</h3>
            <p className="text-xs text-gray-500">{project.client_name}</p>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <MoreHorizontal className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>项目操作</DropdownMenuLabel>
              <DropdownMenuItem>
                <Target className="w-4 h-4 mr-2" />
                查看详情
              </DropdownMenuItem>
              <DropdownMenuItem>
                <DollarSign className="w-4 h-4 mr-2" />
                预算管理
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Users className="w-4 h-4 mr-2" />
                团队管理
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                编辑项目
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* 标签和优先级 */}
        <div className="flex items-center gap-2 mb-3">
          <Badge className={`text-xs ${getPriorityColor(project.priority)}`}>
            {getPriorityText(project.priority)}优先级
          </Badge>
          <div className="flex gap-1">
            {project.tags.slice(0, 2).map((tag, index) => (
              <Badge key={index} variant="outline" className="text-xs">
                {tag}
              </Badge>
            ))}
            {project.tags.length > 2 && (
              <Badge variant="outline" className="text-xs">
                +{project.tags.length - 2}
              </Badge>
            )}
          </div>
        </div>

        {/* 进度条 */}
        <div className="mb-3">
          <div className="flex justify-between text-xs mb-1">
            <span>项目进度</span>
            <span>{project.progress}%</span>
          </div>
          <Progress value={project.progress} className="h-2" />
        </div>

        {/* 预算信息 */}
        <div className="mb-3">
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-600">预算使用</span>
            <span>
              ¥{project.current_spend.toLocaleString()} / ¥{project.budget.toLocaleString()}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1.5">
            <div
              className={`h-1.5 rounded-full ${
                (project.current_spend / project.budget) > 1
                  ? "bg-red-500"
                  : (project.current_spend / project.budget) > 0.8
                  ? "bg-yellow-500"
                  : "bg-green-500"
              }`}
              style={{ width: `${Math.min((project.current_spend / project.budget) * 100, 100)}%` }}
            />
          </div>
        </div>

        {/* 项目指标 */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-1">
            <Users className="w-3 h-3 text-gray-400" />
            <span>{project.team_members}人</span>
          </div>
          <div className="flex items-center gap-1">
            <Target className="w-3 h-3 text-gray-400" />
            <span>{project.ad_accounts_count}账户</span>
          </div>
          {project.roi > 0 && (
            <div className="flex items-center gap-1 text-green-600">
              <span>ROI: {project.roi.toFixed(2)}</span>
            </div>
          )}
          {project.conversion_rate > 0 && (
            <div className="flex items-center gap-1">
              <span>转化率: {(project.conversion_rate * 100).toFixed(1)}%</span>
            </div>
          )}
        </div>

        {/* 时间信息 */}
        <div className="flex items-center gap-1 text-xs text-gray-500 mt-3">
          <Calendar className="w-3 h-3" />
          <span>{format(new Date(project.start_date), "MM/dd")} - {format(new Date(project.end_date), "MM/dd")}</span>
        </div>

        {/* 负责人信息 */}
        {project.team_lead_name && (
          <div className="flex items-center gap-1 text-xs text-gray-500 mt-2">
            <Users className="w-3 h-3" />
            <span>负责人: {project.team_lead_name}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-4">
      {/* 看板头部 */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">项目看板</h2>
          <p className="text-gray-600">拖拽项目卡片来更改状态</p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          新建项目
        </Button>
      </div>

      {/* 看板列 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {kanbanColumns.map((column) => (
          <div key={column.id} className={`rounded-lg border-2 ${column.color} p-4`}>
            {/* 列标题 */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                {column.icon}
                <h3 className="font-semibold">{column.title}</h3>
              </div>
              <Badge variant="secondary">
                {column.projects.length}
              </Badge>
            </div>

            {/* 项目卡片列表 */}
            <div className="space-y-3 min-h-[200px]">
              {column.projects.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-sm">暂无项目</div>
                  <div className="text-xs mt-1">拖拽项目到此处</div>
                </div>
              ) : (
                column.projects.map((project) => (
                  <ProjectCard key={project.id} project={project} />
                ))
              )}
            </div>

            {/* 列统计信息 */}
            {column.projects.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="text-xs text-gray-600">
                  <div className="flex justify-between mb-1">
                    <span>总预算:</span>
                    <span>
                      ¥{column.projects.reduce((sum, p) => sum + p.budget, 0).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>已消耗:</span>
                    <span>
                      ¥{column.projects.reduce((sum, p) => sum + p.current_spend, 0).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>平均进度:</span>
                    <span>
                      {(
                        column.projects.reduce((sum, p) => sum + p.progress, 0) /
                        Math.max(column.projects.length, 1)
                      ).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 统计信息 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">看板统计</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {kanbanColumns.map((column) => (
              <div key={column.id} className="text-center">
                <div className="text-2xl font-bold">{column.projects.length}</div>
                <div className="text-sm text-gray-600">{column.title}</div>
                {column.projects.length > 0 && (
                  <div className="text-xs text-gray-500 mt-1">
                    ¥{column.projects.reduce((sum, p) => sum + p.current_spend, 0).toLocaleString()}
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}