'use client';

/**
 * Project Detail Page
 * /projects/[id]
 *
 * TASK-PRJ-004: 项目仪表盘
 */

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Edit, Users, BarChart3, Settings, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useProject } from '@/features/projects/hooks';
import { ProjectDashboard } from '@/features/projects/components';
import { PROJECT_STATUS_CONFIG } from '@/features/projects/types';

// 格式化金额
function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined) return '¥0';
  return `¥${value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// 加载骨架
function PageSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10" />
          <div>
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-32 mt-2" />
          </div>
        </div>
        <Skeleton className="h-10 w-24" />
      </div>
      <Skeleton className="h-[500px] w-full" />
    </div>
  );
}

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = Number(params.id);

  const { data, isLoading, error } = useProject(projectId);
  const project = data?.data;

  if (isLoading) {
    return (
      <div className="container mx-auto py-6 px-4">
        <PageSkeleton />
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="container mx-auto py-6 px-4">
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-destructive mb-4">加载项目失败</p>
            <Button variant="outline" onClick={() => router.back()}>
              返回
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const statusConfig = PROJECT_STATUS_CONFIG[project.status] || {
    label: project.status,
    variant: 'default',
  };

  return (
    <div className="container mx-auto py-6 px-4 space-y-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">{project.name}</h1>
              <Badge
                variant={statusConfig.variant as 'default' | 'success' | 'warning' | 'destructive'}
              >
                {statusConfig.label}
              </Badge>
            </div>
            <p className="text-muted-foreground">
              {project.client_company} · {project.client_name}
            </p>
          </div>
        </div>

        <Button onClick={() => router.push(`/projects?edit=${project.id}`)}>
          <Edit className="h-4 w-4 mr-2" />
          编辑项目
        </Button>
      </div>

      {/* 项目概要信息 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">项目预算</p>
            <p className="text-xl font-bold mt-1">{formatCurrency(project.budget)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">已消耗</p>
            <p className="text-xl font-bold mt-1">{formatCurrency(project.total_spent)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">关联账户</p>
            <p className="text-xl font-bold mt-1">
              {project.active_accounts} / {project.total_accounts}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">总进粉数</p>
            <p className="text-xl font-bold mt-1">
              {(project.total_follows || 0).toLocaleString()}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 标签页 */}
      <Tabs defaultValue="dashboard" className="w-full">
        <TabsList className="grid w-full grid-cols-4 max-w-lg">
          <TabsTrigger value="dashboard" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            仪表盘
          </TabsTrigger>
          <TabsTrigger value="members" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            成员
          </TabsTrigger>
          <TabsTrigger value="reports" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            日报
          </TabsTrigger>
          <TabsTrigger value="settings" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            设置
          </TabsTrigger>
        </TabsList>

        {/* 仪表盘 Tab */}
        <TabsContent value="dashboard" className="mt-6">
          <ProjectDashboard projectId={projectId} budget={project.budget} />
        </TabsContent>

        {/* 成员 Tab */}
        <TabsContent value="members" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>项目成员</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">成员管理功能开发中...</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 日报 Tab */}
        <TabsContent value="reports" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>日报列表</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">日报列表功能开发中...</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 设置 Tab */}
        <TabsContent value="settings" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>项目设置</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <p className="text-sm font-medium">项目描述</p>
                  <p className="text-muted-foreground mt-1">{project.description || '暂无描述'}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium">开始日期</p>
                    <p className="text-muted-foreground mt-1">{project.start_date || '未设置'}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">结束日期</p>
                    <p className="text-muted-foreground mt-1">{project.end_date || '未设置'}</p>
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium">项目负责人</p>
                  <p className="text-muted-foreground mt-1">
                    {project.account_manager_name || project.created_by_name || '未分配'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
