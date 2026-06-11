import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: '2026 조선일보 54기 마니또',
  description: '조선일보 54기 동기모임 마니또 프로젝트',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-ios-bg font-sans">{children}</body>
    </html>
  )
}
