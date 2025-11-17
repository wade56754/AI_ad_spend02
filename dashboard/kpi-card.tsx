import type { FC } from 'react'
import { clsx } from 'clsx'
import Card from './card'

type KPICardProps = {
  title: string
  value: string
  change: number
  changePercent: string
  trend: 'up' | 'down'
  icon?: string
}

const KPICard: FC<KPICardProps> = ({
  title,
  value,
  change,
  changePercent,
  trend,
  icon,
}) => {
  const isUp = trend === 'up'

  return (
    <Card className="!p-4 h-28 flex flex-col">
      <div className="mb-3 flex items-start justify-between">
        <div className="text-xs text-gray-500">{title}</div>
        {icon && (
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-orange-50 text-lg">
            {icon}
          </div>
        )}
      </div>

      <div className="flex items-end justify-between">
        <div className="text-2xl font-semibold text-gray-900">{value}</div>
        <div className="flex flex-col items-end space-y-0.5">
          <div
            className={clsx(
              'flex items-center gap-1 text-xs font-medium',
              isUp ? 'text-emerald-500' : 'text-red-500'
            )}
          >
            <span>{isUp ? '↑' : '↓'}</span>
            <span>{change.toFixed(1)}</span>
            <span>{changePercent}</span>
          </div>
          <div className="text-[11px] text-gray-400">vs 上周</div>
        </div>
      </div>
    </Card>
  )
}

export default KPICard
