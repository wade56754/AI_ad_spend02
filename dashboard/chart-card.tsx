// components/dashboard/chart-card.tsx
import type { FC, ReactNode } from 'react'
import Card from './card'
import clsx from 'clsx'

type ChartCardProps = {
  title: string
  className?: string
  children: ReactNode
}

export const ChartCard: FC<ChartCardProps> = ({ title, className, children }) => {
  return (
    <Card className={clsx('!p-5 flex flex-col', className)}>
      <h2 className="mb-3 text-sm font-medium text-gray-900">{title}</h2>
      {children}
    </Card>
  )
}

export default ChartCard
