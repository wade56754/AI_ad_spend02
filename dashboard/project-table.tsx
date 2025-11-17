import type { FC } from 'react'
import { clsx } from 'clsx'
import Card from './card'

export type ProjectRow = {
  id: number
  accountId: string
  date: string
  project: string
  region: string
  spending: string
  status: string
  statusColor: 'orange' | 'blue' | 'green'
}

type ProjectTableProps = {
  data: ProjectRow[]
}

const statusColorMap: Record<ProjectRow['statusColor'], string> = {
  orange: 'bg-orange-50 text-orange-500',
  blue: 'bg-blue-50 text-blue-500',
  green: 'bg-emerald-50 text-emerald-500',
}

const ProjectTable: FC<ProjectTableProps> = ({ data }) => {
  return (
    <Card>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-medium text-gray-900">项目列表</h2>
        <select className="text-xs px-2.5 py-1 rounded-md border border-gray-200 bg-white text-gray-700">
          <option>Monthly</option>
          <option>Weekly</option>
          <option>Daily</option>
        </select>
      </div>

      <div className="overflow-hidden rounded-xl border border-gray-100">
        <table className="min-w-full border-separate border-spacing-0 text-xs">
          <thead className="bg-[#F8FAFD]">
            <tr>
              <th className="whitespace-nowrap px-4 py-3 text-left font-normal text-gray-500">序号</th>
              <th className="whitespace-nowrap px-4 py-3 text-left font-normal text-gray-500">账户 ID</th>
              <th className="whitespace-nowrap px-4 py-3 text-left font-normal text-gray-500">日期</th>
              <th className="whitespace-nowrap px-4 py-3 text-left font-normal text-gray-500">所属项目</th>
              <th className="whitespace-nowrap px-4 py-3 text-left font-normal text-gray-500">投放地区</th>
              <th className="whitespace-nowrap px-4 py-3 text-left font-normal text-gray-500">累计消耗</th>
              <th className="whitespace-nowrap px-4 py-3 text-left font-normal text-gray-500">状态</th>
              <th className="whitespace-nowrap px-4 py-3 text-right font-normal text-gray-500">操作</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, idx) => (
              <tr
                key={row.id}
                className={clsx(
                  'border-t border-gray-100',
                  idx % 2 === 1 ? 'bg-[#FBFCFE]' : 'bg-white'
                )}
              >
                <td className="px-4 py-3 text-gray-600">{row.id}</td>
                <td className="px-4 py-3 text-gray-800">{row.accountId}</td>
                <td className="px-4 py-3 text-gray-600">{row.date}</td>
                <td className="px-4 py-3 text-gray-800">{row.project}</td>
                <td className="px-4 py-3 text-gray-600">{row.region}</td>
                <td className="px-4 py-3 text-gray-800">{row.spending}</td>
                <td className="px-4 py-3">
                  <span
                    className={clsx(
                      'inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] border border-transparent',
                      statusColorMap[row.statusColor]
                    )}
                  >
                    {row.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-right text-gray-400">
                  <button className="inline-flex items-center justify-center rounded-full px-1.5 py-0.5 hover:bg-gray-100">
                    ⋮
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  )
}

export default ProjectTable
