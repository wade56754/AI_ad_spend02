"use client";

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Trophy, TrendingUp, TrendingDown } from 'lucide-react';

interface ProjectItem {
  id: string;
  name: string;
  roi: number;
  spend: string;
  status: 'active' | 'paused';
  trend: 'up' | 'down' | 'neutral';
}

interface ProjectTopListProps {
  title?: string;
  projects?: ProjectItem[];
  className?: string;
}

const mockProjects: ProjectItem[] = [
  {
    id: '1',
    name: '美妆品牌Q4推广',
    roi: 4.2,
    spend: '￥125,000',
    status: 'active',
    trend: 'up'
  },
  {
    id: '2',
    name: '科技产品发布',
    roi: 3.8,
    spend: '￥98,500',
    status: 'active',
    trend: 'up'
  },
  {
    id: '3',
    name: '时尚服装秋季',
    roi: 3.1,
    spend: '￥76,200',
    status: 'active',
    trend: 'down'
  },
  {
    id: '4',
    name: '食品饮料推广',
    roi: 2.9,
    spend: '￥54,800',
    status: 'paused',
    trend: 'neutral'
  },
  {
    id: '5',
    name: '家居用品营销',
    roi: 2.7,
    spend: '￥42,100',
    status: 'active',
    trend: 'up'
  }
];

export function ProjectTopList({
  title = "项目Top5",
  projects = mockProjects,
  className
}: ProjectTopListProps) {
  return (
    <Card className={`rounded-2xl shadow-sm border-slate-200/60 bg-white ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Trophy className="w-4 h-4 text-yellow-500" />
            {title}
          </CardTitle>
          <Button variant="ghost" size="sm" className="text-xs hover:bg-slate-100">
            查看全部
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {projects.map((project, index) => (
          <div
            key={project.id}
            className="flex items-center justify-between p-2.5 rounded-lg hover:bg-slate-50 transition-all duration-200 cursor-pointer group"
          >
            {/* 排名和项目信息 */}
            <div className="flex items-center gap-2.5">
              <div className={`flex items-center justify-center w-5 h-5 rounded-full text-white font-semibold text-xs
                ${index === 0 ? 'bg-yellow-500' :
                  index === 1 ? 'bg-slate-400' :
                  index === 2 ? 'bg-orange-500' :
                  'bg-slate-300'}
              `}>
                {index + 1}
              </div>
              <div className="min-w-0 flex-1">
                <h4 className="font-medium text-sm text-slate-900 truncate group-hover:text-blue-600 transition-colors">
                  {project.name}
                </h4>
                <span className="text-xs text-slate-400">{project.spend}</span>
              </div>
            </div>

            {/* ROI和趋势 */}
            <div className="text-right">
              <div className="flex items-center gap-1">
                <span className="font-semibold text-sm text-slate-900">{(Number(project.roi) || 0).toFixed(1)}</span>
                {project.trend === 'up' && (
                  <TrendingUp className="w-3 h-3 text-green-500" />
                )}
                {project.trend === 'down' && (
                  <TrendingDown className="w-3 h-3 text-red-500" />
                )}
              </div>
              <span className="text-xs text-slate-400">ROI</span>
            </div>
          </div>
        ))}

        {/* 简化的总计信息 */}
        <div className="pt-2.5 mt-1 border-t border-slate-200/60">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400">平均ROI</span>
            <span className="font-semibold text-sm text-slate-900">
              {projects.length > 0 ? (projects.reduce((sum, p) => sum + (Number(p.roi) || 0), 0) / projects.length).toFixed(2) : '0.00'}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}