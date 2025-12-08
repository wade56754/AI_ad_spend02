'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Progress } from '@/components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Eye,
  MoreHorizontal,
  Edit,
  Play,
  Pause,
  CheckCircle,
  Clock,
  AlertTriangle,
  Users,
  Calendar,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  BarChart3
} from 'lucide-react';
import { Project, ProjectStatus, ProjectPriority, Platform } from '../types';
import { format } from 'date-fns';

interface ProjectTableProps {
  data: Project[];
  loading?: boolean;
  onRowClick?: (project: Project) => void;
  onViewDetail?: (project: Project) => void;
  onEdit?: (project: Project) => void;
  onStatusChange?: (id: number, status: ProjectStatus) => void;
  selectedIds?: number[];
  onSelectionChange?: (selectedIds: number[]) => void;
  empty?: boolean;
}

/**
 * 项目管理列表表格组件
 *
 * 显示项目记录，支持批量选择、状态管理等功能
 */
export function ProjectTable({
  data,
  loading = false,
  onRowClick,
  onViewDetail,
  onEdit,
  onStatusChange,
  selectedIds = [],
  onSelectionChange,
  empty = false
}: ProjectTableProps) {
  const [currentSelectedIds, setCurrentSelectedIds] = useState<number[]>(selectedIds);

  // 处理单行选择
  const handleRowSelect = (id: number, checked: boolean) => {
    let newSelectedIds: number[];
    if (checked) {
      newSelectedIds = [...currentSelectedIds, id];
    } else {
      newSelectedIds = currentSelectedIds.filter(selectedId => selectedId !== id);
    }
    setCurrentSelectedIds(newSelectedIds);
    onSelectionChange?.(newSelectedIds);
  };

  // 处理全选
  const handleSelectAll = (checked: boolean) => {
    const newSelectedIds = checked ? data.map(project => project.id) : [];
    setCurrentSelectedIds(newSelectedIds);
    onSelectionChange?.(newSelectedIds);
  };

  // 检查是否全选
  const isAllSelected = data.length > 0 && currentSelectedIds.length === data.length;
  const isIndeterminate = currentSelectedIds.length > 0 && currentSelectedIds.length < data.length;

  // 获取状态配置
  const getStatusConfig = (status: ProjectStatus) => {
    const configs = {
      planning: {
        label: '规划中',
        variant: 'info' as const,
        icon: Clock,
      },
      active: {
        label: '进行中',
        variant: 'success' as const,
        icon: Play,
      },
      paused: {
        label: '暂停',
        variant: 'warning' as const,
        icon: Pause,
      },
      completed: {
        label: '已完成',
        variant: 'secondary' as const,
        icon: CheckCircle,
      },
    };
    return configs[status];
  };

  // 获取优先级配置
  const getPriorityConfig = (priority: ProjectPriority) => {
    const configs = {
      high: {
        label: '高',
        variant: 'destructive' as const,
        color: 'text-red-600',
      },
      medium: {
        label: '中',
        variant: 'warning' as const,
        color: 'text-yellow-600',
      },
      low: {
        label: '低',
        variant: 'secondary' as const,
        color: 'text-gray-600',
      },
    };
    return configs[priority];
  };

  // 获取平台标签
  const getPlatformLabel = (platform: Platform) => {
    const labels = {
      facebook: 'Facebook',
      google: 'Google',
      tiktok: 'TikTok',
      instagram: 'Instagram',
      youtube: 'YouTube',
      twitter: 'Twitter',
      linkedin: 'LinkedIn',
    };
    return labels[platform] || platform;
  };

  // 计算预算使用率的颜色
  const getBudgetProgressColor = (utilization: number) => {
    if (utilization >= 100) return 'bg-destructive';
    if (utilization >= 80) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  // 获取ROI趋势图标
  const getROITrendIcon = (roi: number) => {
    if (roi > 2) return <TrendingUp className="h-4 w-4 text-green-600" />;
    if (roi < 1) return <TrendingDown className="h-4 w-4 text-red-600" />;
    return <BarChart3 className="h-4 w-4 text-muted-foreground" />;
  };

  // Loading状态
  if (loading) {
    return (
      <Card className="bg-card border-border">
        <CardContent className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-6 bg-muted rounded w-1/4"></div>
            <div className="space-y-2">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="h-12 bg-muted rounded"></div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty状态
  if (empty || data.length === 0) {
    return (
      <Card className="bg-card border-border">
        <CardContent className="p-12">
          <div className="text-center">
            <div className="mx-auto w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
              <Target className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">
              暂无项目
            </h3>
            <p className="text-muted-foreground max-w-md mx-auto">
              当前筛选条件下没有找到项目记录，请尝试调整筛选条件或创建新项目。
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">项目列表</CardTitle>
          {currentSelectedIds.length > 0 && (
            <Badge variant="secondary" className="gap-1">
              <CheckCircle className="h-3 w-3" />
              已选 {currentSelectedIds.length} 个
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="border-b border-border">
                <TableHead className="w-12">
                  <Checkbox
                    checked={isAllSelected}
                    onCheckedChange={handleSelectAll}
                    ref={(node) => {
                      if (node) node.indeterminate = isIndeterminate;
                    }}
                    aria-label="全选"
                  />
                </TableHead>
                <TableHead className="w-48">项目信息</TableHead>
                <TableHead className="w-20 text-center">状态</TableHead>
                <TableHead className="w-20 text-center">优先级</TableHead>
                <TableHead className="w-32">预算进度</TableHead>
                <TableHead className="w-24 text-center">ROI</TableHead>
                <TableHead className="w-32">团队</TableHead>
                <TableHead className="w-28">时间线</TableHead>
                <TableHead className="w-24">平台</TableHead>
                <TableHead className="w-20 text-center">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((project) => {
                const isSelected = currentSelectedIds.includes(project.id);
                const statusConfig = getStatusConfig(project.status);
                const priorityConfig = getPriorityConfig(project.priority);
                const StatusIcon = statusConfig.icon;
                const isOverdue = new Date(project.end_date) < new Date() && project.status !== 'completed';

                return (
                  <TableRow
                    key={project.id}
                    className={`border-b border-border hover:bg-muted/40 transition-colors cursor-pointer ${
                      isSelected ? 'bg-muted/20' : ''
                    } ${isOverdue ? 'bg-red-50/30' : ''}`}
                    onClick={() => onRowClick?.(project)}
                  >
                    <TableCell>
                      <Checkbox
                        checked={isSelected}
                        onCheckedChange={(checked) => {
                          handleRowSelect(project.id, !!checked);
                        }}
                        onClick={(e) => e.stopPropagation()}
                        aria-label={`选择项目 ${project.name}`}
                      />
                    </TableCell>

                    {/* 项目信息 */}
                    <TableCell>
                      <div className="space-y-1">
                        <div className="font-medium text-sm flex items-center gap-2">
                          {project.name}
                          {isOverdue && (
                            <AlertTriangle className="h-3 w-3 text-red-500" />
                          )}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {project.client_name}
                        </div>
                        {project.tags && project.tags.length > 0 && (
                          <div className="flex gap-1 flex-wrap mt-1">
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
                        )}
                      </div>
                    </TableCell>

                    {/* 状态 */}
                    <TableCell className="text-center">
                      <Badge variant={statusConfig.variant} className="gap-1">
                        <StatusIcon className="h-3 w-3" />
                        {statusConfig.label}
                      </Badge>
                    </TableCell>

                    {/* 优先级 */}
                    <TableCell className="text-center">
                      <Badge variant={priorityConfig.variant} className="text-xs">
                        {priorityConfig.label}
                      </Badge>
                    </TableCell>

                    {/* 预算进度 */}
                    <TableCell>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>¥{project.current_spend.toLocaleString()}</span>
                          <span className="text-muted-foreground">/ ¥{project.budget.toLocaleString()}</span>
                        </div>
                        <div className="relative">
                          <Progress
                            value={Math.min(project.budget_utilization, 100)}
                            className="h-2"
                          />
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {project.budget_utilization.toFixed(1)}%
                        </div>
                      </div>
                    </TableCell>

                    {/* ROI */}
                    <TableCell className="text-center">
                      <div className="flex items-center justify-center gap-1">
                        {getROITrendIcon(project.roi)}
                        <span className={`font-medium ${
                          project.roi > 2 ? 'text-green-600' :
                          project.roi < 1 ? 'text-red-600' :
                          'text-foreground'
                        }`}>
                          {project.roi.toFixed(2)}
                        </span>
                      </div>
                    </TableCell>

                    {/* 团队 */}
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Users className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <div className="text-sm font-medium">{project.team_lead}</div>
                          {project.team_size && (
                            <div className="text-xs text-muted-foreground">
                              {project.team_size}人
                            </div>
                          )}
                        </div>
                      </div>
                    </TableCell>

                    {/* 时间线 */}
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center gap-1 text-sm">
                          <Calendar className="h-3 w-3 text-muted-foreground" />
                          <span>{format(new Date(project.start_date), 'MM/dd')}</span>
                        </div>
                        <div className="text-xs text-muted-foreground">
                          至 {format(new Date(project.end_date), 'MM/dd')}
                        </div>
                      </div>
                    </TableCell>

                    {/* 平台 */}
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {project.platforms && project.platforms.slice(0, 2).map((platform, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {getPlatformLabel(platform)}
                          </Badge>
                        ))}
                        {project.platforms && project.platforms.length > 2 && (
                          <Badge variant="outline" className="text-xs">
                            +{project.platforms.length - 2}
                          </Badge>
                        )}
                      </div>
                    </TableCell>

                    {/* 操作 */}
                    <TableCell className="text-center">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              onViewDetail?.(project);
                            }}
                            className="cursor-pointer"
                          >
                            <Eye className="h-4 w-4 mr-2" />
                            查看详情
                          </DropdownMenuItem>

                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              onEdit?.(project);
                            }}
                            className="cursor-pointer"
                          >
                            <Edit className="h-4 w-4 mr-2" />
                            编辑项目
                          </DropdownMenuItem>

                          {project.status !== 'completed' && (
                            <>
                              <DropdownMenuSeparator />
                              {project.status === 'active' && (
                                <DropdownMenuItem
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    onStatusChange?.(project.id, 'paused');
                                  }}
                                  className="cursor-pointer text-yellow-600 focus:text-yellow-700"
                                >
                                  <Pause className="h-4 w-4 mr-2" />
                                  暂停项目
                                </DropdownMenuItem>
                              )}
                              {(project.status === 'paused' || project.status === 'planning') && (
                                <DropdownMenuItem
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    onStatusChange?.(project.id, 'active');
                                  }}
                                  className="cursor-pointer text-green-600 focus:text-green-700"
                                >
                                  <Play className="h-4 w-4 mr-2" />
                                  启动项目
                                </DropdownMenuItem>
                              )}
                              {project.status !== 'completed' && (
                                <DropdownMenuItem
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    onStatusChange?.(project.id, 'completed');
                                  }}
                                  className="cursor-pointer text-blue-600 focus:text-blue-700"
                                >
                                  <CheckCircle className="h-4 w-4 mr-2" />
                                  完成项目
                                </DropdownMenuItem>
                              )}
                            </>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}

export default ProjectTable;