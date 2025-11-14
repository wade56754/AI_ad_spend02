'use client';

import React, { useState } from 'react';
import AppLayout from '@/components/dashboard/AppLayout';
import { ChartCard } from '@/components/dashboard/ChartCard';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Plus, Search, Filter, Download, RefreshCw, Eye, Edit, Users, DollarSign, TrendingUp, Calendar } from 'lucide-react';

// 简化的项目数据类型
interface Project {
  id: number;
  name: string;
  client_name: string;
  status: 'planning' | 'active' | 'paused' | 'completed';
  priority: 'low' | 'medium' | 'high';
  budget: number;
  current_spend: number;
  team_lead: string;
  start_date: string;
  end_date: string;
  roi: number;
}

export default function ProjectsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [projects] = useState<Project[]>([
    {
      id: 1,
      name: '春季推广活动',
      client_name: 'ABC科技公司',
      status: 'active',
      priority: 'high',
      budget: 50000,
      current_spend: 32500,
      team_lead: '张经理',
      start_date: '2025-01-01',
      end_date: '2025-03-31',
      roi: 3.8
    },
    {
      id: 2,
      name: '品牌形象提升',
      client_name: 'XYZ时尚集团',
      status: 'active',
      priority: 'medium',
      budget: 30000,
      current_spend: 18500,
      team_lead: '李主管',
      start_date: '2025-01-01',
      end_date: '2025-06-30',
      roi: 2.1
    },
    {
      id: 3,
      name: '夏季促销活动',
      client_name: 'DEF零售连锁',
      status: 'planning',
      priority: 'high',
      budget: 80000,
      current_spend: 0,
      team_lead: '王总监',
      start_date: '2025-06-01',
      end_date: '2025-08-31',
      roi: 0
    },
  ]);

  const getStatusColor = (status: string) => {
    const colors = {
      planning: 'bg-blue-100 text-blue-800',
      active: 'bg-green-100 text-green-800',
      paused: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-purple-100 text-purple-800',
    };
    return colors[status] || colors.planning;
  };

  const getStatusText = (status: string) => {
    const texts = {
      planning: '规划中',
      active: '进行中',
      paused: '暂停',
      completed: '已完成',
    };
    return texts[status] || '未知';
  };

  const getPriorityColor = (priority: string) => {
    const colors = {
      low: 'bg-gray-100 text-gray-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-red-100 text-red-800',
    };
    return colors[priority] || colors.medium;
  };

  const getPriorityText = (priority: string) => {
    const texts = {
      low: '低',
      medium: '中',
      high: '高',
    };
    return texts[priority] || '未知';
  };

  const filteredProjects = projects.filter(project =>
    project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    project.client_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <AppLayout>
      <main className="flex flex-col gap-6">
        {/* 页面头部 */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">项目管理</h1>
            <p className="text-gray-600 mt-1">查看并管理所有投放项目</p>
          </div>
          <Button className="bg-[#1E3A8A] hover:bg-[#1E3A8A]/90">
            <Plus className="w-4 h-4 mr-2" />
            新建项目
          </Button>
        </div>

        {/* 搜索和筛选 */}
        <ChartCard title="项目筛选">
          <div className="flex flex-wrap items-center gap-4">
            <div className="relative flex-1 min-w-80">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                placeholder="搜索项目名称或客户..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>

            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="rounded-xl border border-[#ECECEC] bg-white px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
            >
              <option value="all">所有状态</option>
              <option value="planning">规划中</option>
              <option value="active">进行中</option>
              <option value="paused">暂停</option>
              <option value="completed">已完成</option>
            </select>

            <Button variant="outline" size="sm">
              <RefreshCw className="w-4 h-4 mr-2" />
              刷新
            </Button>

            <Button variant="outline" size="sm">
              <Download className="w-4 h-4 mr-2" />
              导出
            </Button>
          </div>
        </ChartCard>

        {/* 项目列表 */}
        <ChartCard title="项目列表">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">项目信息</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">状态</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">优先级</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">预算进度</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">团队</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">ROI</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">时间线</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">操作</th>
                </tr>
              </thead>
              <tbody>
                {filteredProjects.map((project) => (
                  <tr key={project.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <div>
                        <div className="font-medium text-gray-900">{project.name}</div>
                        <div className="text-sm text-gray-600">{project.client_name}</div>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(project.status)}`}>
                        {getStatusText(project.status)}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getPriorityColor(project.priority)}`}>
                        {getPriorityText(project.priority)}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span>¥{project.current_spend.toLocaleString()}</span>
                          <span className="text-gray-600">/ ¥{project.budget.toLocaleString()}</span>
                        </div>
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              (project.current_spend / project.budget) > 1 ? "bg-red-500" :
                              (project.current_spend / project.budget) > 0.8 ? "bg-yellow-500" : "bg-green-500"
                            }`}
                            style={{ width: `${Math.min((project.current_spend / project.budget) * 100, 100)}%` }}
                          />
                        </div>
                        <div className="text-xs text-gray-500">
                          {((project.current_spend / project.budget) * 100).toFixed(1)}%
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <Users className="w-4 h-4 text-gray-400" />
                        <span className="text-sm">{project.team_lead}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`font-medium ${project.roi > 0 ? 'text-green-600' : 'text-gray-600'}`}>
                        {project.roi.toFixed(2)}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="text-sm text-gray-600">
                        <div className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          <span>{new Date(project.start_date).toLocaleDateString()}</span>
                        </div>
                        <div className="text-xs">至 {new Date(project.end_date).toLocaleDateString()}</div>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <Button variant="outline" size="sm">
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button variant="outline" size="sm">
                          <Edit className="w-4 h-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </ChartCard>

        {/* 项目统计 */}
        <div className="grid grid-cols-4 gap-4">
          <ChartCard title="总项目数">
            <div className="flex items-center justify-between h-16">
              <span className="text-2xl font-bold text-gray-900">{projects.length}</span>
              <TrendingUp className="w-8 h-8 text-[#1E3A8A]" />
            </div>
          </ChartCard>

          <ChartCard title="活跃项目">
            <div className="flex items-center justify-between h-16">
              <span className="text-2xl font-bold text-gray-900">
                {projects.filter(p => p.status === 'active').length}
              </span>
              <DollarSign className="w-8 h-8 text-green-600" />
            </div>
          </ChartCard>

          <ChartCard title="总预算">
            <div className="flex items-center justify-between h-16">
              <span className="text-2xl font-bold text-gray-900">
                ¥{projects.reduce((sum, p) => sum + p.budget, 0).toLocaleString()}
              </span>
              <DollarSign className="w-8 h-8 text-[#F59E0B]" />
            </div>
          </ChartCard>

          <ChartCard title="平均ROI">
            <div className="flex items-center justify-between h-16">
              <span className="text-2xl font-bold text-gray-900">
                {(projects.reduce((sum, p) => sum + p.roi, 0) / projects.length).toFixed(2)}
              </span>
              <TrendingUp className="w-8 h-8 text-purple-600" />
            </div>
          </ChartCard>
        </div>
      </main>
    </AppLayout>
  );
}