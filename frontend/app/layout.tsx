import type { Metadata } from "next"
import "./globals.css"
import "../styles/design-system.css"
import { Providers } from "@/components/layout/providers"
import { ErrorBoundary } from "@/components/common/ErrorBoundary"

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
    <html lang="zh-CN" suppressHydrationWarning>
      <body className="font-sans antialiased">
        <ErrorBoundary>
          <Providers>
            {children}
          </Providers>
        </ErrorBoundary>
      </body>
    </html>
  )
}