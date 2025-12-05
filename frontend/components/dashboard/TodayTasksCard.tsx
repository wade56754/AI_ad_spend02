"use client";

import React, { useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Clock, CheckCircle, AlertTriangle } from 'lucide-react';
import type { TodoTask } from '@/modules/dashboard/types';

interface TodayTasksCardProps {
  title?: string;
  tasks?: TodoTask[];
  className?: string;
}

// Mock data removed - use external mock data from @/modules/dashboard/data/mock-data

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed': return <CheckCircle className="w-4 h-4 text-green-500" />;
    case 'in_progress': return <AlertTriangle className="w-4 h-4 text-amber-500" />;
    default: return <Clock className="w-4 h-4 text-blue-500" />;
  }
};

export function TodayTasksCard({
  title = "今日待办",
  tasks = [],
  className
}: TodayTasksCardProps) {
  const router = useRouter();
  const pendingCount = tasks.filter(t => t.status === 'pending').length;
  const inProgressCount = tasks.filter(t => t.status === 'in_progress').length;
  const completedCount = tasks.filter(t => t.status === 'completed').length;

  // 点击任务跳转到对应详情页
  const handleTaskClick = useCallback((task: TodoTask) => {
    const routeMap: Record<string, string> = {
      daily_report: '/dashboard/daily-reports',
      topup_request: '/dashboard/topup',
      reconciliation: '/dashboard/reconciliation',
    };
    const route = task.relatedEntityType ? routeMap[task.relatedEntityType] : '/dashboard';
    router.push(task.relatedEntityId ? `${route}/${task.relatedEntityId}` : route);
  }, [router]);

  return (
    <Card className={`rounded-2xl shadow-sm border-slate-200/60 bg-white ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Clock className="w-4 h-4 text-blue-500" />
            {title}
          </CardTitle>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">{pendingCount} 待处理</span>
            {inProgressCount > 0 && (
              <span className="text-xs text-slate-400">· {inProgressCount} 进行中</span>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y divide-slate-100">
          {tasks.map((task) => (
            <div
              key={task.id}
              className="group flex items-center gap-3 px-5 py-2.5 hover:bg-slate-50 transition-colors cursor-pointer"
              onClick={() => handleTaskClick(task)}
            >
              {/* 状态指示器 */}
              <div className="flex-shrink-0">
                {getStatusIcon(task.status)}
              </div>

              {/* 任务内容 */}
              <div className="flex-1 min-w-0">
                <h4 className={`text-sm leading-tight truncate group-hover:text-blue-600 transition-colors ${
                  task.status === 'completed'
                    ? 'text-slate-400 line-through'
                    : 'text-slate-900'
                }`}>
                  {task.title}
                </h4>
                <div className="flex items-center gap-3 mt-1 text-xs text-slate-400">
                  {task.assignee && (
                    <span>{task.assignee}</span>
                  )}
                  {task.assignee && task.dueTime && (
                    <span>·</span>
                  )}
                  {task.dueTime && (
                    <span>{task.dueTime}</span>
                  )}
                </div>
              </div>

              {/* 优先级指示器 */}
              <div className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                <div className={`w-1.5 h-1.5 rounded-full ${
                  task.priority === 'high' ? 'bg-red-500' :
                  task.priority === 'medium' ? 'bg-amber-500' : 'bg-slate-300'
                }`} />
              </div>
            </div>
          ))}
        </div>

        {/* 紧凑的进度条 */}
        <div className="px-4 py-3 border-t border-slate-100">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-slate-400">完成进度</span>
            <span className="text-xs font-medium text-slate-600">
              {completedCount} / {tasks.length}
            </span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-0.5">
            <div
              className="bg-blue-500 h-0.5 rounded-full transition-all duration-300"
              style={{ width: `${tasks.length > 0 ? (completedCount / tasks.length) * 100 : 0}%` }}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}