import type { Metadata } from 'next'
import './globals.css'
import AuthGuard from '@/components/AuthGuard'
import Header from '@/components/Header'

export const metadata: Metadata = {
  title: 'Project Transparency - %スコアリング',
  description: 'プロジェクトの透明性を可視化するスコアリングシステム',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja">
      <body className="bg-gray-50">
        <AuthGuard>
          <Header />
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
        </AuthGuard>
      </body>
    </html>
  )
}
