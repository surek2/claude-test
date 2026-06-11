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
