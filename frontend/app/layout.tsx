import type { Metadata } from "next"
import "./globals.css"
import "../styles/design-system.css"

export const metadata: Metadata = {
  title: "AI广告代投系统",
  description: "智能化广告投放管理平台",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className="font-sans antialiased">
        {children}
      </body>
    </html>
  )
}