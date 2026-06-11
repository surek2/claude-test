import { NextResponse } from 'next/server'
import { getSupabase } from '@/lib/supabase'

export const dynamic = 'force-dynamic'

export async function GET() {
  const supabase = getSupabase()
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
