import { NextRequest, NextResponse } from 'next/server'
import { getSupabase } from '@/lib/supabase'
import { verifyPassword } from '@/lib/hash'

export const dynamic = 'force-dynamic'

export async function POST(req: NextRequest) {
  const { name, password } = await req.json()

  if (!name?.trim() || !password) {
    return NextResponse.json({ error: '이름과 비밀번호를 입력해 주세요' }, { status: 400 })
  }

  const supabase = getSupabase()
  const { data: participant } = await supabase
    .from('participants')
    .select('password_hash, manitto_name')
    .eq('name', name.trim())
    .maybeSingle()

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
