interface CardProps {
  children: React.ReactNode
  className?: string
}

export default function Card({ children, className = '' }: CardProps) {
  return (
    <div className={`bg-white rounded-[16px] shadow-sm border border-[#EDF0F5] p-6 ${className}`}>
      {children}
    </div>
  )
}
