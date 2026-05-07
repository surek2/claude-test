# AICOM Community Service - Development Progress

## 🚀 프로젝트 완료 상태

AICOM 커뮤니티 서비스의 모든 핵심 기능이 구현되었습니다.

## 🏗️ 프로젝트 구조

### 📁 디렉토리 구조
```
/app
├── __init__.py
├── auth.py          # 모든 인증 로직 통합
├── boards.py        # 게시판 관리 API
├── posts.py         # 게시글 관리 API  
├── comments.py      # 댓글 관리 API
├── admin.py         # 관리자 기능
├── config.py        # 환경변수 설정 (Pydantic v2)
├── database.py      # Supabase 클라이언트 및 RPC
├── main.py          # FastAPI 앱 및 라우트
└── tests/
    ├── test_auth_htmx.py      # HTMX 헤더 사용 테스트
    ├── test_boards_api.py     # 게시판 API 테스트
    ├── test_posts_api.py      # 게시글 API 테스트  
    └── test_comments_api.py   # 댓글 API 테스트

/templates
├── base.html        # Tailwind CSS, HTMX, Quill.js, Pretendard 폰트
├── index.html       # 메인 페이지 (SPA 방식)
├── login.html       # 로그인 폼 (HTMX 통합)
├── signup.html      # 회원가입 폼
├── error.html       # 일반 에러 페이지
├── 403.html         # 403 권한 없음 페이지
├── 404.html         # 404 에러 페이지
├── 500.html         # 500 에러 페이지
├── terms.html       # 이용약관
├── privacy.html     # 개인정보처리방침
├── boards/
│   └── new.html     # 새 게시판 만들기 페이지
├── posts/
│   ├── create.html  # 게시글 작성 페이지
│   ├── detail.html  # 게시글 상세 페이지
│   └── edit.html    # 게시글 수정 페이지
└── admin/
    ├── dashboard.html    # 관리자 대시보드
    ├── boards.html      # 게시판 관리
    └── users.html       # 사용자 관리

/static              # 정적 파일 디렉토리
└── js/
    └── editor.js    # Quill.js 에디터 설정
```

## 🗄️ 데이터베이스 구조

### Supabase 프로젝트 (2025-07-11 재생성)
- **프로젝트 이름**: `aicom-community`
- **프로젝트 ID**: `gfrdzblvntkdrlgtwimx`
- **프로젝트 URL**: `https://gfrdzblvntkdrlgtwimx.supabase.co`
- **주의사항**: Supabase Auth의 이메일 확인 설정을 비활성화해야 함

### 테이블 구조
```sql
-- public.users 테이블
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- public.boards 테이블  
CREATE TABLE boards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    can_read VARCHAR(10) DEFAULT 'all',
    can_write VARCHAR(10) DEFAULT 'member',
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- public.posts 테이블
CREATE TABLE posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id UUID REFERENCES boards(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    is_pinned BOOLEAN DEFAULT FALSE,
    view_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    search_vector tsvector,  -- 전문 검색을 위한 ts_vector
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- public.comments 테이블
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    parent_id UUID REFERENCES comments(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_boards_is_active ON boards(is_active);
CREATE INDEX idx_posts_is_active ON posts(is_active);
CREATE INDEX idx_comments_is_active ON comments(is_active);
CREATE INDEX idx_boards_display_order ON boards(display_order);
CREATE INDEX idx_posts_search_vector ON posts USING gin(search_vector);  -- 전문 검색용 GIN 인덱스

-- 전문 검색 관련 함수 및 트리거
-- strip_html_tags: HTML 태그 제거 함수
-- update_post_search_vector: search_vector 자동 업데이트 함수
-- update_post_search_vector_trigger: title/content 변경 시 자동 실행
-- search_posts: 전체 게시판 검색 RPC 함수
-- search_board_posts: 특정 게시판 검색 RPC 함수
```

## 🔐 인증 시스템

### 구현된 기능
- **회원가입**: 이메일/비밀번호/사용자명으로 가입
- **실시간 중복 체크**: 이메일/사용자명 중복 확인 (디바운싱 500ms)
- **비밀번호 강도 표시**: 실시간 비밀번호 강도 체크
- **로그인/로그아웃**: JWT 기반 인증
- **자동 로그인**: 회원가입 후 자동 로그인
- **토큰 자동 갱신**: refresh_token으로 access_token 갱신

### 보안 설정
- **JWT**: Supabase JWT Secret으로 로컬 디코딩
- **쿠키**: HttpOnly, Secure (프로덕션), SameSite=lax
- **CSRF 보호**: Double Submit Cookie 패턴
- **비밀번호**: 최소 6자 이상 필수

### 기본 계정
- **초기 관리자**: admin@example.com / admin123
- **테스트 사용자**: testuser@example.com / test123

## ✨ 구현된 주요 기능

### 1. 메인 페이지 (/)
- **HTMX 기반 SPA**: 페이지 새로고침 없이 콘텐츠 갱신
- **게시판 목록**: 좌측 사이드바에 권한별 게시판 표시
- **초기 로드**: 공지사항 게시판 자동 선택
- **반응형 디자인**: 모바일/태블릿/데스크톱 완벽 지원

### 2. 게시판 기능
- **권한 시스템**: 읽기(all/member/admin), 쓰기(all/member/admin)
  - 모든 게시판은 비로그인 사용자도 읽기 가능 (can_read="all")
  - 쓰기 권한은 게시판별로 설정 (관리자/회원 전용)
- **한글 slug 자동 변환**: 한글 이름 → 영문 slug
- **게시판 관리**: 관리자만 생성/수정/삭제 가능
- **게시판 순서**: display_order 필드로 정렬 순서 관리
- **Soft Delete**: is_active 필드로 논리적 삭제 구현
- **기본 게시판**: 공지사항, 뉴스레터, 자유게시판

### 3. 게시글 기능
- **리치 텍스트 에디터**: Quill.js 통합
  - H3 제목, 볼드, 이탤릭
  - 글자 색상, 배경색
  - 순서 있는/없는 리스트
  - 이미지 붙여넣기 (Base64 인코딩)
- **조회수 추적**: 클릭할 때마다 증가 (세션 기반 중복 방지 제거)
- **게시글 고정**: 관리자 기능
- **CRUD**: 작성/읽기/수정/삭제

### 4. 댓글 시스템
- **2단계 계층구조**: 댓글과 대댓글
- **HTMX 실시간 업데이트**: 새로고침 없이 댓글 추가/삭제
- **연쇄 삭제**: 댓글 삭제 시 대댓글도 함께 삭제

### 5. 관리자 기능
- **대시보드**: 전체 통계 표시
- **게시판 관리**: 권한 설정, 삭제
- **사용자 관리**: 관리자 권한 부여/해제
- **접근 제어**: 일반 사용자 접근 시 403 페이지

### 6. 검색 기능
- **전체 게시판 검색**: 모든 게시판 대상
- **검색 옵션**: 전체/제목/내용
- **PostgreSQL 전문 검색**: ts_vector와 GIN 인덱스
- **ILIKE fallback**: 전문 검색 실패 시 대체

### 7. 에러 페이지
- **403 Forbidden**: 권한 없음 (로그인/비로그인 구분 메시지)
- **404 Not Found**: 페이지 없음
- **500 Server Error**: 서버 오류

### 8. 정적 페이지
- **이용약관**: 11개 조항의 상세 약관
- **개인정보처리방침**: 10개 조항의 개인정보 정책

## 🐳 Docker 구성
- **FastAPI 컨테이너**: Python 3.12, uvicorn
- **Nginx 컨테이너**: 리버스 프록시, 정적 파일 서빙
- **Rate Limiting**: Nginx 레벨에서 구현
- **Health Check**: /health 엔드포인트

## 🧪 테스트 결과

### 완료된 테스트
- ✅ 인증 기능: 회원가입, 로그인, 중복체크, JWT
- ✅ 반응형 디자인: 375px, 768px, 1920px
- ✅ 게시판 권한: 관리자 페이지 403 에러
- ✅ 에러 페이지: 404, 403, 이용약관, 개인정보처리방침

### 최근 수정 사항 (2025-07-11)
- ✅ 게시판 읽기 권한 변경
  - 모든 게시판의 can_read를 "all"로 변경
  - 비로그인 사용자도 게시판과 게시글 열람 가능
  - 쓰기 권한은 기존 설정 유지 (관리자/회원 전용)
  - init_data.py와 boards.py의 초기 데이터 설정 업데이트

### 이전 수정 사항 (2025-07-09)
- ✅ 게시글 작성 시 JSON 응답 화면 표시 문제 해결
  - 모든 폼에 `hx-swap="none"` 추가
  - `htmx:beforeSwap` 대신 `htmx:afterRequest` 이벤트 사용
- ✅ 게시글 content가 null로 저장되는 문제 해결
  - hidden input 방식으로 변경
  - editor.js에서 폼 제출 시 hidden input에 content 설정
- ✅ HTMX 이벤트 처리 전체 개선
  - 댓글 작성 폼 처리 개선 (성공 시 페이지 새로고침)
  - 중복된 responseError 이벤트 리스너 제거
  - afterRequest에서 통합 에러 처리

### 추가 수정 사항 (2025-07-09)
- ✅ 게시판 목록 페이지 검색창 None 표시 문제 해결
  - `search_query: q or ""` 처리 추가
- ✅ 관리자 페이지 전체 username 표시 통일
  - admin/dashboard.html, admin/users.html, admin/boards.html 모두 수정
  - `{{ user.username or user.email }}` 패턴 적용
- ✅ 게시글 조회수 매번 증가하도록 변경
  - 세션 기반 중복 방지 로직 제거
  - 클릭할 때마다 조회수 증가
- ✅ 새 게시판 만들기 페이지 구현 완료
  - `/boards/new` 라우트 추가 (관리자 전용)
  - `templates/boards/new.html` 생성
  - 읽기/쓰기 권한 설정 기능 포함
  - HTMX 기반 폼 처리

### 데이터베이스 스키마 버그 수정 (2025-07-09)
- ✅ display_order 필드 누락 문제 해결
  - boards 테이블에 display_order INTEGER DEFAULT 0 추가
  - 게시판 정렬 기능 정상화
- ✅ is_active 필드 누락 문제 해결
  - boards, posts, comments 테이블에 is_active BOOLEAN DEFAULT TRUE 추가
  - Soft delete 기능 정상화
- ✅ 마이그레이션 파일 생성
  - `/migrations/add_missing_fields.sql` 생성
  - 인덱스 추가로 성능 최적화

### 해결된 이슈
- ✅ 게시판 생성 UI (/boards/new) 구현 완료
- ✅ 데이터베이스 스키마와 코드 불일치 해결

## ⚙️ 환경 설정

### 필수 환경변수 (.env)
```env
# Supabase
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Session
SESSION_SECRET=your-session-secret

# Cookie Settings
COOKIE_SECURE=False  # True for production with HTTPS
COOKIE_SAMESITE=lax
```

## 🚀 실행 방법

### 데이터베이스 마이그레이션
```bash
# Supabase SQL Editor에서 실행
# /migrations/add_missing_fields.sql 파일의 내용을 복사하여 실행
```

### Docker로 실행
```bash
# 빌드 및 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 종료
docker-compose down
```

### 로컬 개발
```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 실행
uvicorn app.main:app --reload
```

## ⚠️ 프로덕션 배포 시 주의사항

1. **Supabase RLS**: Row Level Security 반드시 활성화
2. **환경변수**: 프로덕션용 시크릿 키 사용
3. **HTTPS**: COOKIE_SECURE=True 설정
4. **백업**: 정기적인 데이터베이스 백업
5. **모니터링**: 로그 및 성능 모니터링 구성
6. **Rate Limiting**: DDoS 방어를 위한 설정 강화

## 🔒 보안 강화 및 버그 수정 (2025-07-09 추가)

### 보안 취약점 수정
- ✅ **XSS 방어 강화**
  - posts.py, comments.py의 HTML sanitization 강화
  - a 태그의 target 속성 제거 (tabnabbing 방지)
  - img src는 Base64 이미지만 허용하도록 검증 추가
  - 허용 프로토콜 명시 (http, https, data)
  - BeautifulSoup으로 img 태그 추가 검증
  
- ✅ **CSRF 보호 강화**
  - HTMX 요청에도 CSRF 토큰 검증 적용
  - X-CSRF-Token 헤더, form data, JSON body에서 토큰 확인
  - 세션 만료 시 사용자 친화적 에러 메시지
  
- ✅ **보안 헤더 추가**
  - X-Content-Type-Options: nosniff
  - X-Frame-Options: DENY
  - X-XSS-Protection: 1; mode=block
  - Strict-Transport-Security (HTTPS 환경에서만)
  - Content-Security-Policy 설정
  - Referrer-Policy: strict-origin-when-cross-origin
  
- ✅ **민감한 정보 로깅 제거**
  - database.py에서 Service role key 로깅 제거

### 검색 기능 개선
- ✅ **전체 게시판 검색 구현**
  - `/api/search/posts-html` 엔드포인트 추가
  - 모든 읽기 권한이 있는 게시판 대상 검색
  - 검색 결과 전용 템플릿 `partials/search_results.html` 생성
  - 게시판명 표시되는 통합 검색 결과
  - 검색 범위를 현재 게시판에서 전체 게시판으로 변경

### 기타 수정사항
- ✅ 로그아웃 버튼 CSRF 토큰 추가 (index.html)
- ✅ 보안 미들웨어 추가로 전체적인 보안 강화

### 추가 버그 수정 (2025-07-09)
- ✅ 403 페이지 로그아웃 CSRF 토큰 누락 수정
- ✅ 403 페이지 사용자명 표시 버그 수정 (이메일 대신 username 우선 표시)
- ✅ 검색 결과 URL 인코딩 문제 수정 (특수문자 포함 검색어 처리)
- ✅ 페이지네이션 range() 오류 수정 (Jinja2 템플릿에서 page_range 사용)
- ✅ 게시판 삭제 로직 통일 (하드 삭제 → 소프트 삭제)
- ✅ 이미지 크기 제한 추가 (1MB 초과 시 에러 메시지 표시)
- ✅ 관리자 대시보드 경로 문서 수정 (/admin/ → /admin)

### 코드 개선 사항 (2025-07-09)
- ✅ TESTPLAN.md 파일 전체 업데이트
  - users_profile 테이블 참조 제거 (users 테이블만 사용)
  - 파일 업로드 관련 테스트 케이스 제거 (Base64 이미지만 지원)
  - 조회수 로직 설명 업데이트 (세션별 1회 증가)
  - 댓글 계층 제한 명확화 (2단계까지만 허용)
  - API 엔드포인트 현재 구현에 맞게 수정
- ✅ 조회수 추적 로직 수정
  - posts.py의 track_view 함수에서 세션 기반 중복 방지 로직 제거
  - PROGRESS.md 문서와 일치하도록 매번 증가하게 변경
- ✅ Docker 환경 재빌드 및 테스트
  - 모든 서비스 정상 작동 확인
  - 초기 게시판(공지사항, 뉴스레터) 자동 생성 확인
  - health 엔드포인트 및 API 정상 동작 확인
- ✅ CSP (Content Security Policy) 오류 수정
  - Tailwind CSS CDN (https://cdn.tailwindcss.com) 추가
  - Google Fonts (fonts.googleapis.com, fonts.gstatic.com) 추가
  - base.html의 Tailwind 설정 스크립트 오류 수정
- ✅ 게시글 목록 정렬 순서 수정
  - Supabase 클라이언트 직접 사용으로 변경
  - is_pinned (내림차순) → created_at (내림차순) 순서로 명확한 정렬
  - 매번 일관된 순서로 게시글 표시

### 네비게이션 간소화 (2025-07-09)
- ✅ 중복 게시판 페이지 제거 및 URL 구조 개선
  - /boards/{slug} 라우트를 /?board={slug}로 리다이렉트 처리
  - main.py의 home 라우트에 board 파라미터 추가
  - index.html의 HTMX 버튼에 hx-push-url 추가로 History API 지원
  - URL 파라미터 기반으로 초기 게시판 로드 구현
- ✅ 템플릿 링크 업데이트
  - posts/detail.html: 뒤로가기 버튼 링크 변경 (/?board={slug})
  - posts/edit.html: 뒤로가기 및 취소 버튼 링크 변경
  - posts/detail.html, posts/edit.html: 삭제/수정 후 리다이렉트 변경
- ✅ 불필요한 파일 제거
  - templates/boards/list.html 삭제 (더 이상 사용되지 않음)
- ✅ 프로젝트 구조 문서 업데이트
  - boards/list.html 파일 제거 반영

### 정렬 순서 일관성 및 버그 수정 (2025-07-09)
- ✅ 게시글 정렬 순서 일관성 문제 해결
  - Supabase 클라이언트 직접 사용으로 통일
  - 모든 게시판 쿼리에서 order("is_pinned", desc=True).order("created_at", desc=True) 사용
  - main.py 초기 게시판 로드 시에도 동일한 정렬 적용
- ✅ 새 게시판 만들기 405 오류 수정
  - templates/boards/new.html의 API 엔드포인트 수정 (/api/boards → /api/boards/create)
- ✅ ARCHITECTURE.md 업데이트
  - 페이지 플로우 다이어그램 현재 구조에 맞게 수정
  - URL 구조 변경사항 반영 (/?board={slug} 패턴)

### 페이지네이션 상태 보존 구현 (2025-07-09)
- ✅ 게시글 목록에서 페이지 정보 유지
  - 게시판 목록에서 게시글 클릭 시 현재 페이지 번호를 from_page 파라미터로 전달
  - 게시글 상세 페이지에서 목록으로 돌아갈 때 원래 페이지로 복귀
  - 게시글 삭제 후에도 원래 페이지로 돌아가도록 구현
- ✅ URL 파라미터 기반 단순한 구현
  - 브라우저 히스토리 API나 세션 스토리지 같은 복잡한 방법 대신 URL 파라미터 사용
  - 부작용(side effect) 최소화를 위한 안정적인 접근 방식

### 페이지네이션 및 검색 개선 (2025-07-10)
- ✅ 게시판 전환 시 페이지 초기화 문제 해결
  - main.py의 home 함수에 page 파라미터 추가
  - 템플릿에서 initial_page 변수 전달
  - JavaScript에서 URL의 page 파라미터 처리 개선
- ✅ HTMX URL 업데이트 개선
  - 게시판 버튼 클릭 시 hx-push-url="true" 사용
  - htmx:beforeRequest 이벤트에서 URL 수동 업데이트
  - 페이지네이션 클릭 시에도 URL 파라미터 유지
- ✅ 검색 기능 RPC 함수 제거
  - search_posts RPC 함수 의존성 제거
  - Supabase 클라이언트의 ilike 메소드 직접 사용
  - 검색 시에도 일관된 정렬 순서 유지 (is_pinned desc, created_at desc)
- ✅ 검색 쿼리 효율성 개선
  - 전체 결과를 가져온 후 카운트하는 방식에서 별도의 count 쿼리로 변경
  - 페이지네이션 적용 전에 정확한 total_count 계산

### 게시글 삭제/수정 및 content 저장 버그 수정 (2025-07-10)
- ✅ 게시글 삭제 API 경로 수정
  - posts.py의 삭제 라우트를 `/api/posts/{post_id}/delete`에서 `/api/posts/{post_id}`로 변경
  - posts/detail.html의 HTMX delete 요청과 일치하도록 수정
  - 삭제 성공 시 204 No Content 상태 코드 반환
- ✅ 게시글 content 저장 문제 해결
  - editor.js의 setupFormSubmission 함수 간소화
  - htmx:configRequest 이벤트 제거 (json-enc extension과 충돌)
  - hidden input 방식으로 통일하여 안정성 향상
- ✅ 데이터베이스 정리
  - 기존 게시글 삭제 (content가 null 또는 빈 문자열인 잘못된 데이터)
  - migrations 폴더 제거 (이미 적용된 필드들)
- ✅ 최종 테이블 구조 확인
  - posts 테이블: is_active, display_order 필드 정상 존재
  - boards 테이블: is_active, display_order 필드 정상 존재
  - comments 테이블: is_active 필드 정상 존재

### 게시글 생성/수정 500 오류 수정 (2025-07-10)
- ✅ PostCreate/PostUpdate 스키마에 is_pinned 필드 추가
  - 관리자 옵션의 상단 고정 체크박스 처리
  - PostCreate: is_pinned: Optional[bool] = False
  - PostUpdate: is_pinned: Optional[bool] = None
- ✅ 관리자 권한 검증 로직 추가
  - create_post: 관리자가 아닌 경우 is_pinned를 False로 강제
  - update_post: 관리자가 아닌 경우 is_pinned 필드 제거
- ✅ content 처리 개선
  - editor.js에 htmx:configRequest 이벤트 다시 추가 (json-enc와 호환)
  - create_post에서 board_id를 데이터베이스의 실제 ID로 변경
  - content가 None인 경우 빈 문자열로 처리
- ✅ Tailwind CSS 프로덕션 경고
  - CDN 사용은 개발 환경에서만 권장
  - 프로덕션 배포 시 PostCSS 플러그인 또는 Tailwind CLI 사용 필요

### HTMX json-enc CSRF 토큰 문제 해결 (2025-07-10)
- ✅ HTMX json-enc 사용 시 CSRF 토큰 전송 문제 해결
  - json-enc 확장 사용 시 hidden input의 CSRF 토큰이 JSON 페이로드에 포함되지 않는 문제 발견
  - htmx:configRequest 이벤트 핸들러를 추가하여 CSRF 토큰을 JSON 페이로드에 명시적으로 추가
  - 수정된 파일:
    - templates/posts/create.html
    - templates/posts/edit.html
    - templates/posts/detail.html (댓글 폼)
    - templates/boards/new.html
- ✅ 로그아웃 폼을 HTMX 방식으로 통일
  - 일부 템플릿에 남아있던 일반 form 방식의 로그아웃을 HTMX 링크로 변경
  - X-CSRF-Token 헤더를 사용하여 CSRF 보호 유지
- ✅ Puppeteer 테스트 결과
  - 게시글 작성: CSRF 토큰 문제로 인한 실패 확인
  - 게시글 수정: 폼 제출이 작동하지 않음
  - 게시판 이동 및 정렬: 정상 작동
  - 조회수 증가: 정상 작동 (매번 증가)

### 댓글 API 엔드포인트 수정 (2025-07-10)
- ✅ RESTful API 엔드포인트로 통일
  - POST /api/comments/create → POST /api/comments
  - DELETE /api/comments/{id}/delete → DELETE /api/comments/{id}
  - PATCH /api/comments/{id}/update → PATCH /api/comments/{id}
- ✅ 대댓글 폼 CSRF 토큰 처리 추가
  - 동적으로 생성되는 대댓글 폼에 htmx:configRequest 이벤트 핸들러 추가
  - data-csrf-configured 속성으로 중복 이벤트 바인딩 방지
- ✅ 댓글 생성 500 오류 수정
  - get_post_with_details 함수가 board 정보의 일부만 반환하여 check_read_permission 실패
  - board 전체 정보를 반환하도록 수정 (can_read, can_write 필드 포함)
- ✅ 댓글 작성 시 post_id 누락 오류 수정
  - HTMX json-enc 사용 시 hidden input의 post_id가 JSON 페이로드에 포함되지 않는 문제
  - htmx:configRequest 이벤트에서 post_id, parent_id도 함께 추가하도록 수정
- ✅ bleach 라이브러리 호환성 문제 해결
  - bleach 6.x에서 `styles` 파라미터가 제거됨
  - CSS 스타일 속성 제거하고 기본 HTML 태그만 허용하도록 수정
- ✅ 대댓글 API 호출 안되는 문제 수정
  - onsubmit 이벤트가 폼 제출을 방해하는 문제 해결
  - htmx:configRequest 이벤트를 DOMContentLoaded 시점에 모든 대댓글 폼에 바인딩
  - hx-on::after-request로 성공 시 처리로 변경
- ✅ 대댓글 작성 시 백엔드 응답 화면 표시 문제 수정
  - hx-swap="afterend"를 "none"으로 변경하여 JSON 응답이 DOM에 삽입되지 않도록 수정
  - 페이지 새로고침으로 댓글 목록 갱신

### bleach 라이브러리 호환성 문제 추가 수정 (2025-07-10)
- ✅ 게시글 작성/수정 시 bleach styles 파라미터 오류 수정
  - posts.py의 PostCreate, PostUpdate 스키마에서 styles 파라미터 제거
  - bleach 6.x 버전과의 호환성 문제 해결
  - 보안은 유지하면서 스타일 관련 파라미터만 제거
- ✅ BeautifulSoup4 모듈 누락 문제 해결
  - requirements.txt에 beautifulsoup4==4.12.3 추가
  - 이미지 크기 검증을 위해 필요한 모듈
- ✅ 댓글 삭제 시 화면 갱신 문제 수정
  - 댓글 삭제 버튼의 hx-swap="delete"를 제거하고 hx-on::after-request로 변경
  - 삭제 성공 시 페이지 새로고침으로 화면 갱신
- ✅ 게시글 작성 후 리다이렉션 안되는 문제 수정
  - posts.py의 create_post 엔드포인트에 status_code=201 추가
  - 프론트엔드에서 201 응답을 받아야 리다이렉션 처리됨
- ✅ 삭제된 댓글이 계속 표시되는 문제 수정
  - main.py의 게시글 상세 페이지에서 댓글 조회 시 is_active=True 필터 추가
  - boards.py와 main.py의 댓글 수 카운트에 is_active=True 필터 추가
  - 삭제된 댓글이 댓글 수에 포함되지 않도록 수정
- ✅ 댓글 삭제 시 백엔드 응답 표시 문제 수정
  - comments.py의 delete_comment 엔드포인트에 status_code=204 추가
  - 응답 본문을 None으로 변경하여 204 No Content 반환
  - 템플릿에서 hx-swap="none" 추가 및 상태 코드 체크를 204로 변경

### 전체적인 UX 개선 (2025-07-10)
- ✅ 게시판 만들기 후 리다이렉션 문제 수정
  - boards.py의 create_board 엔드포인트에 status_code=201 추가
  - 생성 성공 시 /admin/boards로 자동 리다이렉션
- ✅ 관리자 페이지 HTMX 액션 피드백 개선
  - 게시판 권한 업데이트: 저장중/저장됨 표시 추가
  - 게시판 삭제: 애니메이션 효과 및 빈 상태 메시지 추가
  - 사용자 관리자 권한 토글: HTML 응답으로 변경하여 실시간 업데이트
  - HTMX 인디케이터 스타일 추가 (base.html)
- ✅ 모든 HTMX 액션에 적절한 피드백 제공
  - 처리 중 상태 표시
  - 성공/실패 메시지 표시
  - JSON 응답이 화면에 표시되지 않도록 hx-swap="none" 추가
- ✅ 게시글 목록 정렬 일관성 문제 해결
  - posts.py의 list_posts 함수에서 Python 정렬 대신 Supabase 쿼리 정렬 사용
  - 모든 게시글 목록에서 동일한 정렬 순서 보장 (is_pinned desc, created_at desc, id desc)
  - 메모리 효율성 개선 (전체 데이터를 가져오지 않고 페이지네이션 적용)

### 한글 검색 문제 해결 (2025-07-11)
- ✅ Supabase의 `ilike` 연산자가 한글에서 제대로 작동하지 않는 문제 발견
  - PostgreSQL의 locale/collation 설정 문제로 추정
  - "공지"로 검색 시 "공지사항입니다" 게시글이 검색되지 않는 문제
- ✅ PostgreSQL 전문 검색(ts_vector) 구현으로 근본적 해결
  - `migrations/001_add_fulltext_search.sql` 마이그레이션 작성
  - search_vector 컬럼 추가 및 자동 업데이트 트리거 설정
  - 'simple' configuration 사용으로 한글 검색 지원
  - HTML 태그 제거 함수 `strip_html_tags` 구현
  - GIN 인덱스로 검색 성능 최적화
- ✅ RPC 함수 기반 검색 구현
  - `search_posts`: 전체 게시판 검색 함수
  - `search_board_posts`: 특정 게시판 검색 함수
  - boards.py와 main.py에서 RPC 함수 사용
  - ILIKE fallback으로 안정성 확보
- ✅ 검색 결과 정렬 및 랭킹
  - ts_rank 함수로 검색 관련도 계산
  - 제목(A)에 더 높은 가중치 부여
  - is_pinned → rank → created_at 순서로 정렬

## 📝 추가 개발 필요 사항

1. **파일 첨부 기능**: Supabase Storage 활용
2. **알림 기능**: 댓글 알림 등
3. **사용자 프로필**: 프로필 수정 기능
4. **검색 고도화**: 필터, 정렬 옵션 추가
5. **게시판 순서 변경 UI**: 드래그 앤 드롭으로 display_order 변경
6. **비밀번호 정책 강화**: 최소 8자, 대소문자, 숫자 포함 필수화
7. **세션 타임아웃**: 보안을 위한 세션 만료 시간 설정

## 🚨 Supabase 프로젝트 재생성 후 필수 설정 (2025-07-11)

### 현재 상태
- 새로운 Supabase 프로젝트 생성 완료 (`gfrdzblvntkdrlgtwimx`)
- 데이터베이스 스키마 모두 생성 완료
- 초기 데이터 생성 완료 (관리자 계정, 기본 게시판)
- **문제점**: Supabase Auth의 이메일 확인 설정으로 인해 로그인 불가

### 필수 설정 사항
1. **Supabase 대시보드에서 이메일 확인 비활성화**
   - Authentication → Settings → Auth providers → Email
   - "Confirm email" 옵션을 OFF로 변경
   
2. **환경변수 확인**
   - `.env` 파일의 `SUPABASE_JWT_SECRET`과 `SUPABASE_SERVICE_ROLE_KEY` 확인
   - Supabase 대시보드 → Settings → API에서 올바른 키 복사

### 테스트 결과
- ✅ Docker 환경 정상 작동
- ✅ 초기 데이터 생성 성공
- ✅ 회원가입 성공 (이메일 확인 비활성화 후)
- ✅ 자동 로그인 성공
- ⚠️ JWT Secret/Service Role Key 확인 필요 (관리자 로그인 문제)

### 해결 방법
1. Supabase 대시보드에서 이메일 확인 비활성화
2. JWT Secret과 Service Role Key 재확인
3. 필요시 새로운 테스트 사용자 생성