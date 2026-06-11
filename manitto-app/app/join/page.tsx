'use client'

import { useState } from 'react'
import Link from 'next/link'

export default function JoinPage() {
  const [name, setName] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)

    const res = await fetch('/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, password, passwordConfirm }),
    })
    const data = await res.json()
    setLoading(false)

    if (!res.ok) {
      setError(data.error ?? '오류가 발생했습니다')
      return
    }
    setSuccess(true)
  }

  if (success) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center px-4 py-12">
        <div className="w-full max-w-sm rounded-card bg-ios-card shadow-card p-8 flex flex-col gap-5 items-center text-center">
          <div className="text-4xl">🎁</div>
          <h2 className="text-lg font-bold text-gray-900">등록 완료!</h2>
          <p className="text-sm text-gray-500">9명이 모이면 마니또가 공개돼요</p>
          <Link href="/" className="mt-2 text-sm text-orange-500 font-medium">← 홈으로</Link>
        </div>
      </main>
    )
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm rounded-card bg-ios-card shadow-card p-8 flex flex-col gap-5">
        <Link href="/" className="text-sm text-gray-400">← 뒤로</Link>

        <h2 className="text-lg font-bold text-gray-900">마니또 참여하기</h2>
        <p className="text-sm text-gray-500">54기 9명이 전부 등록하면 랜덤으로 마니또를 지정해줘요</p>

        {/* 말풍선 */}
        <div className="relative rounded-2xl bg-orange-50 border border-orange-100 px-4 py-3">
          <p className="text-sm text-orange-700 leading-relaxed">
            마니또를 위해 내돈 주고는 절대 안 살 것 같지만,<br />
            마니또에게 찰떡일 것 같은 <span className="font-semibold">2만원 내외</span> 아이템을 선물해 주세요 🎀
          </p>
          <div className="absolute -bottom-2.5 left-6 w-4 h-4 bg-orange-50 border-b border-r border-orange-100 rotate-45" />
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4 mt-1">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-gray-700">이름</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="실명을 입력해 주세요"
              className="rounded-xl border border-gray-200 px-4 py-3 text-sm outline-none focus:border-orange-400 focus:ring-2 focus:ring-orange-100"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-gray-700">비밀번호</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="나중에 마니또 확인 시 사용"
              className="rounded-xl border border-gray-200 px-4 py-3 text-sm outline-none focus:border-orange-400 focus:ring-2 focus:ring-orange-100"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-gray-700">비밀번호 확인</label>
            <input
              type="password"
              value={passwordConfirm}
              onChange={(e) => setPasswordConfirm(e.target.value)}
              placeholder="비밀번호를 다시 입력해 주세요"
              className="rounded-xl border border-gray-200 px-4 py-3 text-sm outline-none focus:border-orange-400 focus:ring-2 focus:ring-orange-100"
            />
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="mt-1 w-full rounded-btn bg-gradient-to-r from-brand-from to-brand-to py-3.5 text-base font-semibold text-white shadow-sm disabled:opacity-60"
          >
            {loading ? '등록 중...' : '등록하기'}
          </button>
        </form>
      </div>
    </main>
  )
}
