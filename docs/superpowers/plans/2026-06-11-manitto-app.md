# 마니또 앱 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 조선일보 54기 9명을 위한 마니또(시크릿 산타) 웹앱을 Next.js + Supabase + Vercel로 구현

**Architecture:** Next.js App Router, 모든 DB 접근은 서버 사이드 API Route에서만 수행. Supabase 테이블 1개(participants)에 등록·매칭 정보를 저장하고, 9번째 등록 시 derangement 알고리즘으로 자동 매칭.

**Tech Stack:** Next.js 14 (App Router), TypeScript, Tailwind CSS, Supabase (PostgreSQL), bcryptjs, Vercel

---

## 파일 맵

| 파일 | 역할 |
|------|------|
| `app/layout.tsx` | 글로벌 레이아웃, 폰트, 배경색 |
| `app/page.tsx` | 메인 화면 (등록 인원 표시, 버튼 2개) |
| `app/join/page.tsx` | 참여하기 폼 |
| `app/check/page.tsx` | 확인하기 폼 + 결과 카드 |
| `app/api/count/route.ts` | GET: 인원 수 + 매칭 완료 여부 |
| `app/api/register/route.ts` | POST: 등록 + 9번째 시 자동 매칭 |
| `app/api/check/route.ts` | POST: 비밀번호 검증 + 마니또 반환 |
| `lib/supabase.ts` | Supabase 서버 클라이언트 |
| `lib/matching.ts` | Derangement 알고리즘 |
| `lib/hash.ts` | bcrypt 유틸 |
| `.env.example` | 환경변수 템플릿 |
| `README.md` | 설치·배포·테이블 생성 가이드 |

---

### Task 1: Next.js 프로젝트 스캐폴딩

**Files:**
- Create: `manitto-app/` (프로젝트 루트)

- [ ] **Step 1: Next.js 프로젝트 생성**

```bash
cd C:\Users\CMEDIA\claude-test
npx create-next-app@latest manitto-app --typescript --tailwind --app --no-src-dir --no-import-alias
```
프롬프트는 모두 기본값(Enter).

- [ ] **Step 2: 추가 의존성 설치**

```bash
cd manitto-app
npm install @supabase/supabase-js bcryptjs
npm install -D @types/bcryptjs
```

- [ ] **Step 3: 불필요한 보일러플레이트 제거**

`app/page.tsx` 내용을 `export default function Home() { return <main /> }` 로 비우고, `app/globals.css`에서 기본 스타일 전부 삭제 후 Tailwind directives만 남김:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 4: 커밋**

```bash
git add .
git commit -m "chore: scaffold Next.js manitto-app"
```

---

### Task 2: 환경변수 + Supabase 클라이언트

**Files:**
- Create: `manitto-app/.env.example`
- Create: `manitto-app/lib/supabase.ts`
- Modify: `manitto-app/.gitignore` (`.env.local` 포함 확인)

- [ ] **Step 1: `.env.example` 작성**

```env
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

- [ ] **Step 2: `lib/supabase.ts` 작성**

```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.SUPABASE_URL!
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!

export const supabase = createClient(supabaseUrl, supabaseServiceKey)
```

- [ ] **Step 3: `.gitignore`에 `.env.local` 포함 확인**

`create-next-app`이 자동 추가하므로 확인만.

- [ ] **Step 4: 커밋**

```bash
git add lib/supabase.ts .env.example
git commit -m "feat: add Supabase server client and env template"
```

---

### Task 3: 유틸 라이브러리 (hash + matching)

**Files:**
- Create: `manitto-app/lib/hash.ts`
- Create: `manitto-app/lib/matching.ts`

- [ ] **Step 1: `lib/hash.ts` 작성**

```typescript
import bcrypt from 'bcryptjs'

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, 10)
}

export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash)
}
```

- [ ] **Step 2: `lib/matching.ts` 작성**

```typescript
export function createDerangement(names: string[]): Map<string, string> {
  const n = names.length
  if (n < 2) throw new Error('최소 2명이 필요합니다')

  for (let attempt = 0; attempt < 1000; attempt++) {
    const shuffled = [...names]
    // Fisher-Yates shuffle
    for (let i = n - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
    }
    // derangement check: no one maps to themselves
    const isDerangement = shuffled.every((name, i) => name !== names[i])
    if (isDerangement) {
      const result = new Map<string, string>()
      names.forEach((name, i) => result.set(name, shuffled[i]))
      return result
    }
  }
  throw new Error('Derangement 생성 실패 (1000회 초과)')
}
```

- [ ] **Step 3: 커밋**

```bash
git add lib/hash.ts lib/matching.ts
git commit -m "feat: add bcrypt utils and derangement algorithm"
```

---

### Task 4: API Route — GET /api/count

**Files:**
- Create: `manitto-app/app/api/count/route.ts`

- [ ] **Step 1: `app/api/count/route.ts` 작성**

```typescript
import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export async function GET() {
  const { count, error } = await supabase
    .from('participants')
    .select('*', { count: 'exact', head: true })

  if (error) {
    return NextResponse.json({ error: '서버 오류' }, { status: 500 })
  }

  const { data: matchedRow } = await supabase
    .from('participants')
    .select('matching_done')
    .eq('matching_done', true)
    .limit(1)
    .maybeSingle()

  return NextResponse.json({
    count: count ?? 0,
    matchingDone: !!matchedRow,
  })
}
```

- [ ] **Step 2: 커밋**

```bash
git add app/api/count/route.ts
git commit -m "feat: add GET /api/count route"
```

---

### Task 5: API Route — POST /api/register (등록 + 자동 매칭)

**Files:**
- Create: `manitto-app/app/api/register/route.ts`

- [ ] **Step 1: `app/api/register/route.ts` 작성**

```typescript
import { NextRequest, NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'
import { hashPassword } from '@/lib/hash'
import { createDerangement } from '@/lib/matching'

const MAX_PARTICIPANTS = 9

export async function POST(req: NextRequest) {
  const { name, password, passwordConfirm } = await req.json()

  if (!name?.trim() || !password || !passwordConfirm) {
    return NextResponse.json({ error: '모든 항목을 입력해 주세요' }, { status: 400 })
  }
  if (password !== passwordConfirm) {
    return NextResponse.json({ error: '비밀번호가 일치하지 않습니다' }, { status: 400 })
  }

  // 정원 체크
  const { count } = await supabase
    .from('participants')
    .select('*', { count: 'exact', head: true })

  if ((count ?? 0) >= MAX_PARTICIPANTS) {
    return NextResponse.json({ error: '정원 9명이 모두 등록되었습니다' }, { status: 400 })
  }

  // 중복 이름 체크
  const { data: existing } = await supabase
    .from('participants')
    .select('id')
    .eq('name', name.trim())
    .maybeSingle()

  if (existing) {
    return NextResponse.json({ error: '이미 등록된 이름입니다' }, { status: 400 })
  }

  // 등록
  const passwordHash = await hashPassword(password)
  const { error: insertError } = await supabase
    .from('participants')
    .insert({ name: name.trim(), password_hash: passwordHash })

  if (insertError) {
    if (insertError.code === '23505') {
      return NextResponse.json({ error: '이미 등록된 이름입니다' }, { status: 400 })
    }
    return NextResponse.json({ error: '등록 중 오류가 발생했습니다' }, { status: 500 })
  }

  // 등록 후 인원 재조회
  const { count: newCount } = await supabase
    .from('participants')
    .select('*', { count: 'exact', head: true })

  // 9명 완료 + 아직 매칭 안 됐으면 매칭 실행
  if ((newCount ?? 0) >= MAX_PARTICIPANTS) {
    const { data: alreadyMatched } = await supabase
      .from('participants')
      .select('id')
      .eq('matching_done', true)
      .limit(1)
      .maybeSingle()

    if (!alreadyMatched) {
      const { data: allParticipants } = await supabase
        .from('participants')
        .select('name')

      if (allParticipants && allParticipants.length === MAX_PARTICIPANTS) {
        const names = allParticipants.map((p) => p.name)
        const matchMap = createDerangement(names)

        for (const [person, manitto] of matchMap.entries()) {
          await supabase
            .from('participants')
            .update({ manitto_name: manitto, matching_done: true })
            .eq('name', person)
        }
      }
    }
  }

  return NextResponse.json({
    success: true,
    message: '등록 완료! 9명이 모이면 마니또가 공개돼요',
    count: newCount ?? 0,
  })
}
```

- [ ] **Step 2: 커밋**

```bash
git add app/api/register/route.ts
git commit -m "feat: add POST /api/register with auto-matching on 9th registration"
```

---

### Task 6: API Route — POST /api/check

**Files:**
- Create: `manitto-app/app/api/check/route.ts`

- [ ] **Step 1: `app/api/check/route.ts` 작성**

```typescript
import { NextRequest, NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'
import { verifyPassword } from '@/lib/hash'

export async function POST(req: NextRequest) {
  const { name, password } = await req.json()

  if (!name?.trim() || !password) {
    return NextResponse.json({ error: '이름과 비밀번호를 입력해 주세요' }, { status: 400 })
  }

  const { data: participant } = await supabase
    .from('participants')
    .select('password_hash, manitto_name')
    .eq('name', name.trim())
    .maybeSingle()

  // 이름 존재 여부 노출하지 않음
  if (!participant) {
    return NextResponse.json({ error: '이름 또는 비밀번호가 올바르지 않습니다' }, { status: 401 })
  }

  const isValid = await verifyPassword(password, participant.password_hash)
  if (!isValid) {
    return NextResponse.json({ error: '이름 또는 비밀번호가 올바르지 않습니다' }, { status: 401 })
  }

  if (!participant.manitto_name) {
    return NextResponse.json({ success: true, manittoName: null, message: '아직 매칭이 완료되지 않았습니다' })
  }

  return NextResponse.json({ success: true, manittoName: participant.manitto_name })
}
```

- [ ] **Step 2: 커밋**

```bash
git add app/api/check/route.ts
git commit -m "feat: add POST /api/check route"
```

---

### Task 7: 글로벌 레이아웃 + 디자인 토큰

**Files:**
- Modify: `manitto-app/app/layout.tsx`
- Modify: `manitto-app/app/globals.css`
- Modify: `manitto-app/tailwind.config.ts`

- [ ] **Step 1: `tailwind.config.ts` 커스텀 색상 추가**

```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './lib/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          from: '#FF6B6B',
          to: '#FF8E53',
        },
        ios: {
          bg: '#F2F2F7',
          card: '#FFFFFF',
        },
      },
      borderRadius: {
        card: '20px',
        btn: '14px',
      },
      boxShadow: {
        card: '0 4px 24px 0 rgba(0,0,0,0.08)',
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', "'Segoe UI'", 'sans-serif'],
      },
    },
  },
  plugins: [],
}
export default config
```

- [ ] **Step 2: `app/globals.css` 정리**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  background-color: #F2F2F7;
}
```

- [ ] **Step 3: `app/layout.tsx` 작성**

```typescript
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
```

- [ ] **Step 4: 커밋**

```bash
git add app/layout.tsx app/globals.css tailwind.config.ts
git commit -m "feat: add global layout and design tokens"
```

---

### Task 8: 메인 페이지 (`/`)

**Files:**
- Modify: `manitto-app/app/page.tsx`

- [ ] **Step 1: `app/page.tsx` 작성**

```typescript
import Link from 'next/link'
import { supabase } from '@/lib/supabase'

async function getCount() {
  const { count } = await supabase
    .from('participants')
    .select('*', { count: 'exact', head: true })

  const { data: matchedRow } = await supabase
    .from('participants')
    .select('matching_done')
    .eq('matching_done', true)
    .limit(1)
    .maybeSingle()

  return { count: count ?? 0, matchingDone: !!matchedRow }
}

export default async function Home() {
  const { count, matchingDone } = await getCount()

  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm rounded-card bg-ios-card shadow-card p-8 flex flex-col gap-6">
        {/* 헤더 그라데이션 */}
        <div className="h-2 w-16 rounded-full bg-gradient-to-r from-brand-from to-brand-to mx-auto" />

        <h1 className="text-center text-xl font-bold text-gray-900 leading-snug">
          2026년 조선일보 54기<br />동기모임 마니또 프로젝트
        </h1>

        {/* 인원 배지 */}
        <div className="flex justify-center">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-orange-50 px-4 py-1.5 text-sm font-medium text-orange-600">
            <span className="h-2 w-2 rounded-full bg-gradient-to-r from-brand-from to-brand-to" />
            {count}/9명 등록 완료
          </span>
        </div>

        {/* 버튼 영역 */}
        <div className="flex flex-col gap-3">
          <Link
            href="/join"
            className="block w-full rounded-btn bg-gradient-to-r from-brand-from to-brand-to py-3.5 text-center text-base font-semibold text-white shadow-sm active:opacity-90"
          >
            마니또 참여하기
          </Link>

          {matchingDone ? (
            <Link
              href="/check"
              className="block w-full rounded-btn border border-orange-300 py-3.5 text-center text-base font-semibold text-orange-500 active:opacity-80"
            >
              마니또 확인하기
            </Link>
          ) : (
            <div className="flex flex-col items-center gap-1.5">
              <button
                disabled
                className="w-full rounded-btn border border-gray-200 bg-gray-100 py-3.5 text-base font-semibold text-gray-400 cursor-not-allowed"
              >
                마니또 확인하기
              </button>
              <p className="text-xs text-gray-400">9명 등록 완료 후 열려요</p>
            </div>
          )}
        </div>
      </div>
    </main>
  )
}
```

- [ ] **Step 2: 커밋**

```bash
git add app/page.tsx
git commit -m "feat: add main page with registration count and nav buttons"
```

---

### Task 9: 참여하기 페이지 (`/join`)

**Files:**
- Create: `manitto-app/app/join/page.tsx`

- [ ] **Step 1: `app/join/page.tsx` 작성**

```typescript
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
```

- [ ] **Step 2: 커밋**

```bash
git add app/join/page.tsx
git commit -m "feat: add join page with registration form"
```

---

### Task 10: 확인하기 페이지 (`/check`)

**Files:**
- Create: `manitto-app/app/check/page.tsx`

- [ ] **Step 1: `app/check/page.tsx` 작성**

```typescript
import CheckClient from './CheckClient'
import { redirect } from 'next/navigation'
import { supabase } from '@/lib/supabase'

async function getMatchingStatus(): Promise<boolean> {
  const { data } = await supabase
    .from('participants')
    .select('matching_done')
    .eq('matching_done', true)
    .limit(1)
    .maybeSingle()
  return !!data
}

export default async function CheckPage() {
  const matchingDone = await getMatchingStatus()
  if (!matchingDone) redirect('/')
  return <CheckClient />
}
```

- [ ] **Step 2: `app/check/CheckClient.tsx` 작성**

```typescript
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
```

- [ ] **Step 3: 커밋**

```bash
git add app/check/
git commit -m "feat: add check page with manitto reveal"
```

---

### Task 11: README + .env.example 완성

**Files:**
- Create: `manitto-app/README.md`

- [ ] **Step 1: `README.md` 작성**

````markdown
# 2026년 조선일보 54기 마니또

## 1. Supabase 테이블 생성

Supabase 대시보드 → SQL Editor에서 실행:

```sql
CREATE TABLE participants (
  id            SERIAL PRIMARY KEY,
  name          TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  manitto_name  TEXT DEFAULT NULL,
  matching_done BOOLEAN NOT NULL DEFAULT FALSE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

RLS는 비활성화 상태로 유지 (서버 API에서 Service Role Key로만 접근).

## 2. 환경변수 설정

`.env.example`을 복사해 `.env.local`을 만들고 값을 채웁니다:

```bash
cp .env.example .env.local
```

| 변수 | 발급 방법 |
|------|-----------|
| `SUPABASE_URL` | Supabase 대시보드 → Settings → API → Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase 대시보드 → Settings → API → service_role (secret) |

## 3. 로컬 실행

```bash
npm install
npm run dev
# http://localhost:3000
```

## 4. Vercel 배포

1. GitHub에 푸시
2. vercel.com → New Project → 레포 선택
3. Environment Variables에 `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` 등록
4. Deploy

## 5. 관리자 운영 가이드

등록 정보 수정/삭제는 Supabase 대시보드 → Table Editor → participants에서 직접 처리합니다.

- **오등록 삭제:** 해당 row 삭제
- **비밀번호 초기화:** `password_hash` 컬럼에 새 bcrypt 해시 값 직접 입력
  (bcrypt 해시 생성: https://bcrypt-generator.com, rounds=10)
- **매칭 초기화 (긴급):** 모든 row의 `manitto_name = NULL`, `matching_done = FALSE`로 UPDATE

## 6. 테이블 컬럼 설명

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | SERIAL | 자동 증가 PK |
| `name` | TEXT UNIQUE | 참가자 실명 |
| `password_hash` | TEXT | bcrypt(rounds=10) 해시 |
| `manitto_name` | TEXT NULL | 배정된 마니또 이름 (매칭 전 NULL) |
| `matching_done` | BOOLEAN | 매칭 완료 플래그 (중복 실행 방지 락) |
| `created_at` | TIMESTAMPTZ | 등록 시각 |
````

- [ ] **Step 2: 커밋**

```bash
git add README.md .env.example
git commit -m "docs: add README with setup, deploy, and admin guide"
```

---

### Task 12: 최종 빌드 검증

- [ ] **Step 1: 빌드 실행**

```bash
npm run build
```
Expected: `✓ Compiled successfully` (타입 에러, lint 에러 없음)

- [ ] **Step 3: 로컬 dev 서버 실행 후 수동 테스트**

```bash
npm run dev
```

테스트 시나리오:
1. 메인 화면 → "0/9명 등록 완료", [마니또 확인하기] 비활성화 확인
2. `/join` → 이름/비밀번호 등록 → 성공 메시지 확인
3. 같은 이름 재등록 → "이미 등록된 이름입니다" 확인
4. 비밀번호 불일치 → "비밀번호가 일치하지 않습니다" 확인

- [ ] **Step 4: 최종 커밋**

```bash
git add .
git commit -m "chore: final build verification and env setup"
```
````
