/**
 * Dashboard 今日待办组件
 * 
 * 功能：
 * - 清晰展示优先级、任务标题、截止时间
 * - 快捷操作按钮
 * - 进度条显示完成度
 * - 分栏展示（优先级/时间/状态）
 */

'use client';

import React from 'react';
import { Clock, CheckCircle2, AlertTriangle, ChevronRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import type { TodoTask } from '../types';

interface DashboardTodayTasksProps {
  tasks: TodoTask[];
  className?: string;
  onTaskClick?: (task: TodoTask) => void;
  onHandleTask?: (task: TodoTask) => void;
}

export function DashboardTodayTasks({
  tasks,
  className,
  onTaskClick,
  onHandleTask
}: DashboardTodayTasksProps) {
  const completedCount = tasks.filter(t => t.status === 'completed').length;
  const progressPercentage =
    tasks.length > 0 ? (completedCount / tasks.length) * 100 : 0;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-success" />;
      case 'in_progress':
        return <AlertTriangle className="w-4 h-4 text-warning" />;
      default:
        return <Clock className="w-4 h-4 text-accent" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-danger ring-danger/20';
      case 'medium':
        return 'bg-warning ring-warning/20';
      default:
        return 'bg-text-subtle ring-text-subtle/20';
    }
  };

  return (
    <Card className={cn('rounded-lg border-default bg-card-bg hover:shadow-lg transition-shadow', className)}>
      <CardHeader className="pb-4">
        <div className="flex justify-between items-center">
          <CardTitle className="text-base flex items-center gap-2 text-text-strong">
            <Clock className="w-4 h-4 text-accent" />
            今日待办
          </CardTitle>
          <div className="flex items-center gap-3">
            <div className="w-28">
              <Progress 
                value={progressPercentage} 
                className="h-1.5 bg-elevated [&>div]:bg-accent" 
              />
            </div>
            <span className="text-xs text-text-muted font-mono">
              {completedCount}/{tasks.length}
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {tasks.length === 0 ? (
          <div className="text-center py-8 text-text-muted text-sm">
            暂无待办任务
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2">
            {tasks.map((task) => (
              <div
                key={task.id}
                onClick={() => onTaskClick?.(task)}
                className={cn(
                  'flex items-center justify-between p-2.5',
                  'bg-card-bg hover:bg-elevated rounded-lg transition-all',
                  'border border-transparent hover:border-default hover:shadow-sm',
                  'group cursor-pointer'
                )}
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  {/* 优先级指示点 */}
                  <div
                    className={cn(
                      'w-2 h-2 rounded-full ring-2 ring-offset-2 ring-offset-shell shrink-0',
                      getPriorityColor(task.priority)
                    )}
                  />
                  
                  {/* 任务内容 */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {getStatusIcon(task.status)}
                      <span
                        className={cn(
                          'text-sm font-medium transition-colors truncate',
                          task.status === 'completed'
                            ? 'text-text-subtle line-through'
                            : 'text-text-body group-hover:text-accent'
                        )}
                      >
                        {task.title}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-text-subtle font-mono">{task.dueTime}</span>
                      {task.assignee && (
                        <>
                          <span className="text-border-muted">|</span>
                          <Badge
                            variant="outline"
                            className="text-[10px] px-1.5 py-0.5 font-medium bg-elevated text-text-muted border-border-muted"
                          >
                            {task.assignee}
                          </Badge>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                {/* 处理按钮 */}
                {task.status !== 'completed' && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      onHandleTask?.(task);
                    }}
                    className="opacity-60 group-hover:opacity-100 text-xs px-3 py-1.5 h-auto bg-accent/10 text-accent hover:bg-accent/20 hover:text-accent-light shrink-0"
                  >
                    处理
                    <ChevronRight className="w-3 h-3 ml-1" />
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

