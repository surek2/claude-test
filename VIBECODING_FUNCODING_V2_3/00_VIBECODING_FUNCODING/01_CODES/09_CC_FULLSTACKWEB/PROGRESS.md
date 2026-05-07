# AICOM 개발 진행 상황

## 프로젝트 개요
- **프로젝트명**: AICOM (구 AIZEVA)
- **설명**: 다중 게시판 커뮤니티 서비스
- **기술 스택**: Python 3.13, FastAPI, Supabase, HTMX, Tailwind CSS
- **개발 기간**: [REMOVED]

## 완료된 주요 기능
- ✅ **인증 시스템**: JWT 쿠키 기반, CSRF 보호
- ✅ **게시판 시스템**: 다중 게시판, 권한 관리 (all/member/admin)
- ✅ **게시글 CRUD**: Quill.js 에디터, Base64 이미지 (1MB 제한)
- ✅ **댓글 시스템**: 2단계 계층 구조
- ✅ **검색 기능**: 제목/내용 검색, 페이지네이션
- ✅ **관리자 기능**: 게시판/사용자 관리
- ✅ **HTMX 통합**: SPA 경험 제공
- ✅ **반응형 디자인**: 모바일/태블릿/데스크톱 지원
- ✅ **Docker 배포**: 개발/프로덕션 환경 지원

## 보안 구현
- ✅ **XSS 방어**: bleach 라이브러리로 HTML sanitization
- ✅ **CSRF 보호**: Double Submit Cookie 패턴
- ✅ **Rate Limiting**: Nginx 레벨 구현 (30req/min)
- ✅ **보안 헤더**: CSP, X-Frame-Options 등
- ✅ **안전한 에러 로깅**: 민감정보 노출 방지

## 데이터베이스 구조
- **users**: 사용자 프로필 (auth.users 참조)
- **boards**: 게시판 정보 (UUID 기반)
- **posts**: 게시글 데이터
- **comments**: 댓글 데이터 (auth.users 직접 참조)
- **RPC 함수**: increment_view_count (조회수 원자적 증가)

## 초기 데이터
- **관리자**: [REMOVED]
- **게시판**: 공지사항(관리자 전용), 뉴스레터(관리자 전용), 자유게시판(회원 전용)

## Docker 구성 최종 단순화

### 프로덕션 환경으로 통합
- **단일 환경**: 프로덕션 환경으로만 구성
- **고정 설정**: 환경변수 제거, 모든 설정 하드코딩
- **단순 실행**: `docker compose up --build -d`만으로 실행

### Docker 구성
- **Nginx**: 80포트, 리버스 프록시, Rate limiting
- **FastAPI**: 내부 8000포트, 4 workers
- **환경변수**: .env 파일만 사용

### 삭제된 파일
- docker-compose.dev.yml
- run.sh
- .env.docker.example

### 실행 방법
```bash
# 실행
docker compose up --build -d

# 접속
http://localhost

# 중지
docker compose down
```

## 테스트 현황
- **단위 테스트**: 79개 모두 통과
- **E2E 테스트**: 5개 시나리오 완료
  - 회원가입/로그인 플로우
  - 게시글 CRUD
  - 댓글 시스템
  - 검색 기능
  - 관리자 기능
- **반응형 디자인**: 3개 뷰포트 검증 완료

## 알려진 제한사항
1. **검색 기능**: Supabase Python 클라이언트 v2.1.0의 or_() 미지원으로 제목+내용 동시 검색 제한
2. **댓글 UI**: 대댓글 시각적 구분 개선 필요 (들여쓰기)
3. **Puppeteer MCP**: 타임아웃 문제로 일부 E2E 테스트 제한

## 향후 개선 제안
1. **검색 개선**: Supabase 클라이언트 업그레이드 또는 RPC 함수 구현
2. **사용자 경험**: 이메일 알림, 프로필 페이지, 북마크 기능
3. **모니터링**: APM 도구 연동, 로그 수집 시스템
4. **보안 강화**: 비밀번호 정책, 2FA 지원

## 프로젝트 상태
- **개발 완료**: Phase 1-10 모든 기능 구현 및 테스트 완료
- **배포 준비**: Docker 환경 구성 완료, 3가지 배포 시나리오 지원
- **문서화**: 모든 주요 문서 최신화 완료
- **보안 검증**: XSS, CSRF, SQL Injection 등 주요 취약점 대응 완료

## CSRF 보호 강화

### JSON API 엔드포인트 CSRF 보호 추가
모든 state-changing JSON API 엔드포인트에 CSRF 토큰 검증 추가:

#### posts.py
- ✅ POST `/boards/{board_id}/posts` - 게시글 작성
- ✅ PUT `/posts/{post_id}` - 게시글 수정
- ✅ DELETE `/posts/{post_id}` - 게시글 삭제
- ✅ PATCH `/posts/{post_id}/pin` - 게시글 고정/해제

#### comments.py
- ✅ POST `/posts/{post_id}/comments` - 댓글 작성
- ✅ PUT `/comments/{comment_id}` - 댓글 수정
- ✅ DELETE `/comments/{comment_id}` - 댓글 삭제

#### admin.py
- ✅ POST `/admin/boards` - 게시판 생성
- ✅ PUT `/admin/boards/{board_id}` - 게시판 수정
- ✅ DELETE `/admin/boards/{board_id}` - 게시판 삭제
- ✅ PUT `/admin/users/{user_id}` - 사용자 권한 수정

### 제외된 엔드포인트
- 인증 엔드포인트 (/auth/login, /auth/signup, /auth/refresh) - 인증 과정의 일부
- 폼 엔드포인트 (/form, /delete로 끝나는 경로) - 이미 자체 CSRF 검증 구현됨
- 로그아웃 (/auth/logout) - 이미 CSRF 검증 구현됨