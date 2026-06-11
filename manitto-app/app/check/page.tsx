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
