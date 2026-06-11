import Link from 'next/link'
import { getSupabase } from '@/lib/supabase'

export const dynamic = 'force-dynamic'

async function getCount() {
  const supabase = getSupabase()
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
        {/* 헤더 그라데이션 바 */}
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
