# 프로젝트: 내일 기록

## 프로젝트 요약
개인용 하루 기록 웹앱. 오늘 한 일을 기록하고 조회, 삭제할 수 있는 간단한 일기 서비스.

## 기술 스택
- Cloudflare Pages, Pages Functions
- Cloudflare D1
- HTML5, Tailwind CSS, Vanilla JavaScript

## 핵심 규칙
- 토스 스타일의 직관적이고 깔끔한 UI 유지
- 모바일 우선 반응형 디자인
- 부드러운 애니메이션과 사용자 피드백 제공
- 변수명은 명확한 영어로 (약어 금지)
- 한 함수는 한 가지 일만

## 프로젝트 구조
functions/api/records/  # Cloudflare Pages Functions (API)
index.html              # 프론트엔드 메인 페이지
app.js                  # 클라이언트 로직
wrangler.toml          # Cloudflare 설정
