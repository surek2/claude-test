'use client'

import { useState } from 'react'
import Link from 'next/link'

export default function CheckClient() {
  const [name, setName] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [manittoName, setManittoName] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)

    const res = await fetch('/api/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, password }),
    })
    const data = await res.json()
    setLoading(false)

    if (!res.ok) {
      setError(data.error ?? '오류가 발생했습니다')
      return
    }
    setManittoName(data.manittoName)
  }

  if (manittoName) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center px-4 py-12">
        <div className="w-full max-w-sm rounded-card bg-ios-card shadow-card p-8 flex flex-col gap-5 text-center">
          <div className="h-2 w-16 rounded-full bg-gradient-to-r from-brand-from to-brand-to mx-auto" />
          <div className="text-3xl">🎁</div>
          <p className="text-lg font-bold text-gray-900 leading-snug">
            <span className="text-orange-500">{name}</span>님의<br />마니또는
          </p>
          <div className="rounded-2xl bg-gradient-to-r from-brand-from to-brand-to p-0.5">
            <div className="rounded-[18px] bg-white px-6 py-4">
              <p className="text-2xl font-bold text-gray-900">{manittoName}</p>
            </div>
          </div>
          <p className="text-sm text-gray-500 leading-relaxed mt-1">
            7월 2일 동기 모임까지<br />
            내돈 주고는 절대 안 살 것 같지만,<br />
            마니또에게 찰떡일 것 같은<br />
            <span className="font-semibold text-gray-700">2만원 내외</span> 아이템을 선물해주세요 🎀
          </p>
          <Link href="/" className="text-sm text-orange-500 font-medium mt-1">← 홈으로</Link>
        </div>
      </main>
    )
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm rounded-card bg-ios-card shadow-card p-8 flex flex-col gap-5">
        <Link href="/" className="text-sm text-gray-400">← 뒤로</Link>
        <h2 className="text-lg font-bold text-gray-900">마니또 확인하기</h2>
        <p className="text-sm text-gray-500">등록 시 사용한 이름과 비밀번호를 입력해 주세요</p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-gray-700">이름</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="등록 시 사용한 이름"
              className="rounded-xl border border-gray-200 px-4 py-3 text-sm outline-none focus:border-orange-400 focus:ring-2 focus:ring-orange-100"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-gray-700">비밀번호</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="등록 시 사용한 비밀번호"
              className="rounded-xl border border-gray-200 px-4 py-3 text-sm outline-none focus:border-orange-400 focus:ring-2 focus:ring-orange-100"
            />
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="mt-1 w-full rounded-btn bg-gradient-to-r from-brand-from to-brand-to py-3.5 text-base font-semibold text-white shadow-sm disabled:opacity-60"
          >
            {loading ? '확인 중...' : '마니또 확인하기'}
          </button>
        </form>
      </div>
    </main>
  )
}
