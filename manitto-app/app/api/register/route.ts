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
