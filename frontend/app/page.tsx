'use client';

import { useState } from 'react';
import AppLayout from '@/components/layout/AppLayout';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';
import DashboardStats from '@/components/dashboard/DashboardStats';
import ModuleGrid from '@/components/dashboard/ModuleGrid';
import RightColumn from '@/components/dashboard/RightColumn';
import { moduleData, activityData, quickActionData } from '@/data/dashboardData';

export default function HomePage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <AppLayout
      sidebar={<Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />}
      header={<Header
        onSidebarToggle={() => setSidebarOpen(!sidebarOpen)}
        title="AI广告代投系统"
        subtitle="智能化广告投放管理平台"
      />}
    >
      <div className="p-6">
        {/* 指标卡片 */}
        <DashboardStats />

        {/* 主要内容区域 */}
        <div className="flex flex-col xl:flex-row gap-6">
          {/* 左侧和中间：模块网格 */}
          <div className="flex-1 xl:mr-6">
            <ModuleGrid modules={moduleData} />
          </div>

          {/* 右侧：快速操作和活动记录 */}
          <div className="w-full xl:w-80">
            <RightColumn
              activities={activityData}
              quickActions={quickActionData}
            />
          </div>
        </div>
      </div>
    </AppLayout>
  );
}