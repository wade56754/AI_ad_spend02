'use client';

import React from 'react';
import { Badge } from '@/components/ui/badge';

export type StatusVariant = 'default' | 'success' | 'warning' | 'destructive';

interface ProjectData {
  id: number;
  accountId: string;
  date: string;
  project: string;
  region: string;
  spending: string;
  status: string;
  statusVariant: StatusVariant;
}

interface ProjectTableProps {
  data: ProjectData[];
  loading?: boolean;
  empty?: boolean;
}

/**
 * 项目列表表格组件
 *
 * 使用统一的表格样式和Badge组件
 * 遵循设计系统规范，支持loading和empty状态
 */
export function ProjectTable({ data, loading = false, empty = false }: ProjectTableProps) {
  // Loading状态
  if (loading) {
    return (
      <div className="bg-card border border-border rounded-xl shadow-sm">
        <div className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-6 bg-muted rounded w-1/4"></div>
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-12 bg-muted rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Empty状态
  if (empty || data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-xl shadow-sm">
        <div className="p-6">
          <div className="text-center py-12">
            <div className="text-muted-foreground text-sm">暂无项目数据</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-xl shadow-sm">
      {/* 表格头部 */}
      <div className="px-6 pt-6 pb-4">
        <h3 className="text-lg font-semibold text-foreground">项目列表</h3>
      </div>

      {/* 表格内容 */}
      <div className="px-6 pb-6">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground">账户ID</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground">日期</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground">项目</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground">地区</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground">花费</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground">状态</th>
              </tr>
            </thead>
            <tbody>
              {data.map((project) => (
                <tr
                  key={project.id}
                  className="border-b border-border hover:bg-muted/40 transition-colors"
                >
                  <td className="py-3 px-4 text-sm font-medium text-foreground">{project.accountId}</td>
                  <td className="py-3 px-4 text-sm text-muted-foreground">{project.date}</td>
                  <td className="py-3 px-4 text-sm text-foreground">{project.project}</td>
                  <td className="py-3 px-4 text-sm text-muted-foreground">{project.region}</td>
                  <td className="py-3 px-4 text-sm font-medium text-foreground">{project.spending}</td>
                  <td className="py-3 px-4">
                    <Badge variant={project.statusVariant}>
                      {project.status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default ProjectTable;