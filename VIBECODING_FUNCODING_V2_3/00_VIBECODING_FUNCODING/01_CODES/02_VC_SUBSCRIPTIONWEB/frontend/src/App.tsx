import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'

// API 엔드포인트
const API_URL = import.meta.env.PROD 
  ? 'https://newsletter-backend.pages.dev' 
  : 'http://localhost:8788'

function App() {
  const [email, setEmail] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showModal, setShowModal] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      alert('올바른 이메일 주소를 입력해주세요.')
      return
    }

    setIsLoading(true)
    
    try {
      const response = await fetch(`${API_URL}/api/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      })

      const data = await response.json()

      if (response.ok) {
        setShowModal(true)
        setEmail('')
      } else {
        alert(data.error || '구독 처리 중 오류가 발생했습니다.')
      }
    } catch (error) {
      console.error('Error:', error)
      alert('네트워크 오류가 발생했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-gray-50 to-white py-24 lg:py-40">
        <div className="container mx-auto px-6 text-center">
          <div className="animate-fade-in-up">
            <h1 className="mb-6 text-5xl font-bold tracking-tight text-gray-900 lg:text-7xl">
              AI 최전선의 진짜 트렌드<br />
              <span className="text-gradient-apple">5분 핵심 요약</span>
            </h1>
            <p className="mx-auto mb-12 max-w-2xl text-xl text-gray-600 lg:text-2xl">
              글로벌 AI 커뮤니티의 최신 인사이트를<br />
              매주 요약 전달합니다
            </p>
            <form onSubmit={handleSubmit} className="mx-auto flex max-w-xl flex-col gap-4 sm:flex-row">
              <Input
                type="email"
                placeholder="이메일을 입력하세요"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="flex-1"
                required
              />
              <Button type="submit" size="lg" disabled={isLoading}>
                {isLoading ? '처리중...' : '무료 구독하기'}
              </Button>
            </form>
          </div>
        </div>
      </section>

      {/* Problem Section */}
      <section className="py-24 lg:py-32">
        <div className="container mx-auto px-6">
          <h2 className="mb-20 text-center text-4xl font-bold tracking-tight text-gray-900 lg:text-5xl">
            AI 정보, <span className="text-gray-500">이래서 놓칩니다</span>
          </h2>
          <div className="mx-auto grid max-w-6xl gap-6 md:grid-cols-2 lg:grid-cols-4">
            {[
              { icon: '⏰', title: '시간 낭비', desc: '"30분 영상,\n핵심은 2분"' },
              { icon: '🔁', title: '알고리즘 함정', desc: '"늘 비슷한\n추천 콘텐츠"' },
              { icon: '😱', title: '뒤늦은 발견', desc: '"이미 대세가\n바뀌었다고?"' },
              { icon: '🌐', title: '언어 장벽', desc: '"국외 커뮤니티는\n영어라..."' },
            ].map((item, idx) => (
              <Card key={idx} className="p-8 text-center">
                <div className="mb-5 text-6xl">{item.icon}</div>
                <h3 className="mb-3 text-2xl font-bold text-gray-900">{item.title}</h3>
                <p className="whitespace-pre-line text-lg leading-relaxed text-gray-600">{item.desc}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Solution Section */}
      <section className="bg-gray-50 py-24 lg:py-32">
        <div className="container mx-auto px-6">
          <h2 className="mb-8 text-center text-4xl font-bold tracking-tight text-gray-900 lg:text-5xl">
            매주 AI 트렌드 추적<br />
            <span className="text-gray-500">핵심 요약</span>
          </h2>
          <div className="mx-auto mt-16 grid max-w-5xl gap-8 md:grid-cols-2">
            <Card className="p-10">
              <div className="mb-6 text-5xl">🌍</div>
              <h3 className="mb-6 text-3xl font-bold tracking-tight text-gray-900">
                글로벌 모니터링
              </h3>
              <ul className="space-y-3 text-lg text-gray-700">
                <li className="flex items-start">
                  <span className="mr-2 font-bold text-gray-900">✓</span>
                  <span>국내외 유명 커뮤니티</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2 font-bold text-gray-900">✓</span>
                  <span>국내외 유명 IT 리더</span>
                </li>
              </ul>
            </Card>
            <Card className="p-10">
              <div className="mb-6 text-5xl">⚡</div>
              <h3 className="mb-6 text-3xl font-bold tracking-tight text-gray-900">
                5분 완독
              </h3>
              <ul className="space-y-3 text-lg text-gray-700">
                <li className="flex items-start">
                  <span className="mr-2 font-bold text-gray-900">✓</span>
                  <span>핵심 요약</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2 font-bold text-gray-900">✓</span>
                  <span>트렌드 의견 추가</span>
                </li>
              </ul>
            </Card>
          </div>
          <p className="mt-16 text-center text-3xl font-bold tracking-tight text-gray-900">
            "진짜 AI 최전선을 만나세요"
          </p>
        </div>
      </section>

      {/* Credibility Section */}
      <section className="py-24 lg:py-32">
        <div className="container mx-auto px-6">
          <h2 className="mb-20 text-center text-4xl font-bold tracking-tight text-gray-900 lg:text-5xl">
            매주 <span className="text-gray-500">이만큼</span> 분석합니다
          </h2>
          <div className="mx-auto grid max-w-5xl gap-6 md:grid-cols-3">
            {[
              { number: '10,000+', label: '글로벌 게시물 스캔' },
              { number: '15개', label: '해외 커뮤니티 분석' },
              { number: '100+', label: '자체 분석 정교화 기능' },
            ].map((stat, idx) => (
              <Card key={idx} className="bg-gray-50 p-10 text-center">
                <div className="mb-4 text-6xl font-black tracking-tighter text-gray-900">
                  {stat.number}
                </div>
                <p className="text-xl font-bold text-gray-700">{stat.label}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* FOMO Section */}
      <section className="bg-gray-900 py-24 text-white lg:py-32">
        <div className="container mx-auto max-w-4xl px-6 text-center">
          <h2 className="mb-12 text-4xl font-bold tracking-tight lg:text-5xl">
            <span className="text-gray-400">한정</span> 무료 공개
          </h2>
          <div className="space-y-8 text-xl leading-relaxed text-gray-300 lg:text-2xl">
            <p className="font-medium">
              광고 없이 오직 입소문으로만<br />
              이 페이지를 다시 찾기는 어렵습니다
            </p>
            <p className="font-medium">
              AI 시스템 운영 비용으로<br />
              무료 구독은 선착순 제한됩니다
            </p>
            <p className="mt-8 text-3xl font-bold text-white">
              지금이 마지막 기회일 수 있습니다
            </p>
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="bg-gray-50 py-24 lg:py-32">
        <div className="container mx-auto px-6">
          <h2 className="mb-16 text-center text-4xl font-bold tracking-tight text-gray-900 lg:text-5xl">
            즉시 받는 <span className="text-gray-500">보너스</span>
          </h2>
          <Card className="mx-auto max-w-3xl p-12">
            <div className="mb-8 text-center text-7xl">🎁</div>
            <h3 className="mb-6 text-center text-3xl font-bold tracking-tight text-gray-900 lg:text-4xl">
              "실전 AI 툴 가이드"
            </h3>
            <p className="mb-8 text-center text-xl font-medium text-gray-600 lg:text-2xl">
              AI 에이전트를 위한 가이드
            </p>
            <p className="text-center text-xl font-bold text-gray-900">
              ✉️ 가입 즉시 이메일로 전송
            </p>
          </Card>
        </div>
      </section>

      {/* Sign-up Section */}
      <section className="py-24 lg:py-32">
        <div className="container mx-auto px-6 text-center">
          <h2 className="mb-16 text-4xl font-bold tracking-tight text-gray-900 lg:text-5xl">
            <span className="text-gray-500">5초</span>면 충분합니다
          </h2>
          <form onSubmit={handleSubmit} className="mx-auto flex max-w-xl flex-col gap-4 sm:flex-row">
            <Input
              type="email"
              placeholder="이메일을 입력하세요"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="flex-1"
              required
            />
            <Button type="submit" size="lg" disabled={isLoading}>
              {isLoading ? '처리중...' : '무료 구독하기'}
            </Button>
          </form>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="bg-gray-50 py-24 lg:py-32">
        <div className="container mx-auto px-6">
          <h2 className="mb-20 text-center text-4xl font-bold tracking-tight text-gray-900 lg:text-5xl">
            자주 묻는 <span className="text-gray-500">질문</span>
          </h2>
          <div className="mx-auto max-w-4xl space-y-5">
            {[
              { q: '정말 무료인가요?', a: '네, 100% 무료입니다' },
              { q: '영상보다 효율적인가요?', a: '30분 → 3분, 10배 효율' },
              { q: '영어 몰라도 되나요?', a: '완벽한 한국어 번역 제공' },
              { q: '왜 Reddit인가요?', a: '유튜브보다 빠른 정보' },
            ].map((faq, idx) => (
              <Card key={idx} className="p-8">
                <h3 className="mb-4 text-2xl font-bold text-gray-900">Q: {faq.q}</h3>
                <p className="text-xl font-medium text-gray-700">A: {faq.a}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA Section */}
      <section className="bg-gray-900 py-24 text-white lg:py-40">
        <div className="container mx-auto px-6 text-center">
          <h2 className="mb-8 text-4xl font-bold tracking-tight lg:text-6xl">
            지금이 <span className="text-gray-400">마지막 기회</span>
          </h2>
          <p className="mb-12 text-2xl font-medium text-gray-300 lg:text-3xl">
            매주 진짜 AI 트렌드를 받아보세요
          </p>
          <div className="mx-auto mb-16 max-w-xl">
            <ul className="inline-block space-y-4 text-left text-xl font-medium lg:text-2xl">
              <li className="flex items-center">
                <span className="mr-3">✓</span> 무료 구독
              </li>
              <li className="flex items-center">
                <span className="mr-3">✓</span> 즉시 취소 가능
              </li>
              <li className="flex items-center">
                <span className="mr-3">✓</span> 30분 → 3분 요약
              </li>
            </ul>
          </div>
          <form onSubmit={handleSubmit} className="mx-auto flex max-w-xl flex-col gap-4 sm:flex-row">
            <Input
              type="email"
              placeholder="이메일을 입력하세요"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="flex-1 bg-white/10 text-white placeholder:text-gray-400 focus-visible:ring-white"
              required
            />
            <Button 
              type="submit" 
              size="lg" 
              variant="outline" 
              className="border-white text-white hover:bg-white hover:text-gray-900"
              disabled={isLoading}
            >
              {isLoading ? '처리중...' : '무료 구독하기'}
            </Button>
          </form>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-black py-16 text-gray-400">
        <div className="container mx-auto px-6 text-center">
          <div className="mb-6 flex justify-center space-x-8 text-base">
            <a href="#" className="transition hover:text-white">이용약관</a>
            <a href="#" className="transition hover:text-white">개인정보보호</a>
          </div>
          <p className="text-base font-medium">주식회사 튜링스</p>
          <p className="mt-3 text-sm">© 2025 All rights reserved.</p>
        </div>
      </footer>

      {/* Success Modal */}
      {showModal && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
          onClick={() => setShowModal(false)}
        >
          <Card 
            className="mx-4 max-w-md p-12 text-center"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-6 text-7xl">🎉</div>
            <h3 className="mb-6 text-3xl font-bold tracking-tight text-gray-900">
              구독 완료!
            </h3>
            <p className="mb-8 text-lg font-medium leading-relaxed text-gray-600">
              환영합니다!<br />
              입력하신 이메일로 첫 번째 뉴스레터와<br />
              보너스 가이드를 곧 보내드립니다.
            </p>
            <Button 
              onClick={() => setShowModal(false)}
              size="lg"
              className="w-full"
            >
              확인
            </Button>
          </Card>
        </div>
      )}
    </div>
  )
}

export default App

