'use client'

import { useState } from 'react'
import Sidebar from './sidebar'
import Header from './header'
import KPICard from './kpi-card'
import ChartCard from './chart-card'
import ProjectTable from './project-table'

const KPI_DATA = [
  { title: '总收入', value: '89,935', change: 10.2, changePercent: '+1.01%', trend: 'up' as const, icon: '💰' },
  { title: '总进粉', value: '23,283.5', change: 3.1, changePercent: '+0.49%', trend: 'up' as const, icon: '👥' },
  { title: '广告总消耗', value: '46,827', change: 2.56, changePercent: '-0.91%', trend: 'down' as const, icon: '📊' },
  { title: '总利润', value: '124,854', change: 7.2, changePercent: '+1.51%', trend: 'up' as const, icon: '📈' },
]

const PROJECT_DATA = [
  { id: 1, accountId: '#12594', date: 'Oct 15, 2023', project: 'Frank Murlo', region: '312 S Wilmette Ave', spending: '$847.69', status: 'New Order', statusColor: 'orange' as const },
  { id: 2, accountId: '#12595', date: 'Oct 14, 2023', project: 'Jennifer Lee', region: '405 N Michigan Ave', spending: '$1,250.00', status: 'Processing', statusColor: 'blue' as const },
  { id: 3, accountId: '#12596', date: 'Oct 13, 2023', project: 'David Chen', region: '500 W Madison St', spending: '$595.43', status: 'Completed', statusColor: 'green' as const },
]

const LEGEND_ITEMS = [
  { color: 'bg-slate-900', label: 'Offline' },
  { color: 'bg-orange-500', label: 'Online' },
  { color: 'bg-purple-400', label: 'Trade' },
]

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className={`h-1.5 w-1.5 rounded-full ${color}`} />
      <span className="text-xs text-gray-500">{label}</span>
    </div>
  )
}

export default function DashboardPage() {
  const [activeMenu, setActiveMenu] = useState('workbench')

  return (
    <div className="flex h-screen bg-[#F4F6FB]">
      <Sidebar activeMenu={activeMenu} onMenuChange={setActiveMenu} />

      <div className="flex-1 overflow-auto">
        <Header userName="Anthony" />

        <main className="mx-auto flex max-w-[1200px] flex-col gap-6 px-10 pb-10 pt-6">
          {/* KPI Cards */}
          <section className="grid grid-cols-4 gap-5">
            {KPI_DATA.map((kpi, index) => (
              <KPICard key={index} {...kpi} />
            ))}
          </section>

          {/* Charts Section */}
          <section className="grid grid-cols-3 gap-5">
            <ChartCard title="投放消耗趋势" className="col-span-2">
              <div className="mb-4 flex items-center justify-between">
                <div className="flex gap-4">
                  <div className="flex items-center gap-2">
                    <span className="h-2.5 w-2.5 rounded-full bg-slate-900" />
                    <span className="text-xs text-gray-500">总消耗</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="h-2.5 w-2.5 rounded-full bg-orange-500" />
                    <span className="text-xs text-gray-500">总充值</span>
                  </div>
                </div>
                <select className="rounded-md border border-gray-200 bg-white px-2.5 py-1 text-xs text-gray-700">
                  <option>Monthly</option>
                  <option>Weekly</option>
                  <option>Daily</option>
                </select>
              </div>

              <div className="relative mt-1 flex h-56 items-center justify-center rounded-2xl bg-[#F9FAFD] px-4 py-3">
                <div className="text-center text-xs text-gray-400">
                  <div className="mb-1">Interactive Line Chart</div>
                  <div>Jan - Jul 2023</div>
                </div>

                <svg className="pointer-events-none absolute inset-0 h-full w-full" viewBox="0 0 400 200" preserveAspectRatio="none">
                  <polyline points="0,120 50,100 100,110 150,80 200,90 250,70 300,75 350,60 400,50" fill="none" stroke="#0f172a" strokeWidth="2" opacity="0.25" />
                  <polyline points="0,140 50,130 100,135 150,110 200,115 250,95 300,100 350,85 400,75" fill="none" stroke="#f97316" strokeWidth="2" opacity="0.25" />
                </svg>
              </div>
            </ChartCard>

            <ChartCard title="项目占比">
              <div className="flex h-full flex-col">
                <div className="flex flex-1 items-center justify-center">
                  <div className="relative flex h-36 w-36 items-center justify-center">
                    <svg className="h-full w-full" viewBox="0 0 100 100">
                      <circle cx="50" cy="50" r="40" fill="none" stroke="#1e3a8a" strokeWidth="12" strokeDasharray="62.8 251.2" />
                      <circle cx="50" cy="50" r="40" fill="none" stroke="#f97316" strokeWidth="12" strokeDasharray="62.8 251.2" strokeDashoffset="-62.8" transform="rotate(-90 50 50)" />
                      <circle cx="50" cy="50" r="40" fill="none" stroke="#a78bfa" strokeWidth="12" strokeDasharray="62.8 251.2" strokeDashoffset="-125.6" />
                      <circle cx="50" cy="50" r="40" fill="none" stroke="#93c5fd" strokeWidth="12" strokeDasharray="62.8 251.2" strokeDashoffset="-188.4" />
                    </svg>
                    <div className="absolute flex flex-col items-center">
                      <span className="text-xl font-semibold text-gray-900">$452</span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap justify-center gap-3 pt-3">
                  {LEGEND_ITEMS.map((item) => (
                    <LegendDot key={item.label} color={item.color} label={item.label} />
                  ))}
                </div>
              </div>
            </ChartCard>
          </section>

          {/* Project Table */}
          <ProjectTable data={PROJECT_DATA} />
        </main>
      </div>
    </div>
  )
}
