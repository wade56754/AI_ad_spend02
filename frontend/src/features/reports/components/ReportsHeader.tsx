/**
 * ReportsHeader Component
 *
 * 报表中心头部 + 标签页导航 - 从 ReportsPage.tsx 提取
 */

'use client';

import React from 'react';
import { BarChart2, RefreshCw, TrendingUp, DollarSign } from 'lucide-react';
import { type ReportTab } from '../utils/reportsHelpers';

interface ReportsHeaderProps {
  activeTab: ReportTab;
  onTabChange: (tab: ReportTab) => void;
  onRefresh: () => void;
}

const tabs = [
  { id: 'dashboard' as const, label: '仪表盘', icon: BarChart2 },
  { id: 'performance' as const, label: '效果报表', icon: TrendingUp },
  { id: 'profit' as const, label: '利润报表', icon: DollarSign },
];

export function ReportsHeader({ activeTab, onTabChange, onRefresh }: ReportsHeaderProps) {
  return (
    <>
      {/* Header */}
      <div className="bg-white border-b" data-testid="reports-header">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <BarChart2 className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">报表中心</h1>
                <p className="text-sm text-gray-500">
                  查看仪表盘、效果报表、利润报表
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={onRefresh}
                className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
              >
                <RefreshCw className="h-4 w-4" />
                刷新
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-4" aria-label="Tabs">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => onTabChange(tab.id)}
                  className={`flex items-center gap-2 px-4 py-4 text-sm font-medium border-b-2 transition-colors ${
                    isActive
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>
      </div>
    </>
  );
}

export default ReportsHeader;
