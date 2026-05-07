### 기본 구조

#### XML 디자인 파일
- @main.xml : PATH / (메인 페이지)
- @header.xml : header 구조
- @login.xml : 로그인 구조
- @signup.xml : 회원가입 구조
- @board.xml : 게시글 상세 페이지 구조

#### 페이지 구조 및 플로우

##### 1. 공개 페이지 (비로그인 접근 가능)
- **메인 페이지 (/)** [SPA 방식]
  - 좌측: 게시판 목록 (클릭 시 HTMX로 중앙 영역 갱신)
  - 중앙: 초기 접속 시 공지사항 게시판 표시, 이후 선택된 게시판의 글 목록 (페이지네이션)
  - 중앙 상단: 글쓰기 버튼 (권한이 있는 경우)
  - 우측: 검색 (전체 게시판 대상, 제목/내용 옵션)
  - 헤더: 로그인/회원가입 버튼 (비로그인 시), 사용자명/로그아웃 (로그인 시)

- **로그인 페이지 (/login)**
  - 이메일, 비밀번호 입력
  - 회원가입 링크
  - 로그인 성공 시 → 메인 페이지(/) 또는 이전 페이지로 리다이렉트

- **회원가입 페이지 (/signup)**
  - 이메일, 사용자명, 비밀번호 입력
  - 실시간 중복 체크 (HTMX)
  - 회원가입 성공 시 → 자동 로그인 후 메인 페이지(/)로 이동

- **이용약관 페이지 (/terms)**
  - 서비스 이용약관 전문

- **개인정보처리방침 페이지 (/privacy)**
  - 개인정보 수집 및 처리 방침

##### 2. 게시판 관련 페이지
- **게시글 작성 페이지 (/boards/{board_slug}/posts/new)** [로그인 필요]
  - 제목 입력
  - Quill.js 리치 텍스트 에디터 (이미지 붙여넣기 지원, Base64 저장)
  - 작성 완료 시 → 작성한 게시글 상세 페이지로 이동

- **게시글 상세 페이지 (/boards/{board_slug}/posts/{post_id})**
  - 게시글 제목, 작성자, 작성일, 조회수
  - 게시글 내용 (HTML 렌더링)
  - 수정/삭제 버튼 (작성자 또는 관리자)
  - 댓글 목록 (2레벨 계층구조)
  - 댓글 작성 폼 (로그인 시)

- **게시글 수정 페이지 (/boards/{board_slug}/posts/{post_id}/edit)** [작성자/관리자]
  - 기존 내용이 로드된 Quill.js 에디터
  - 수정 완료 시 → 게시글 상세 페이지로 이동

##### 3. 관리자 페이지 [관리자 권한 필요]
- **관리자 대시보드 (/admin)**
  - 전체 통계 (게시판 수, 사용자 수, 게시글 수)
  - 게시판 관리, 사용자 관리 링크

- **게시판 관리 (/admin/boards)**
  - 게시판 목록 (생성, 수정, 삭제)
  - 읽기/쓰기 권한 설정
  - 게시판 순서 관리 (display_order)

- **새 게시판 만들기 (/boards/new)** [관리자 권한 필요]
  - 게시판 이름, 설명 입력
  - 읽기/쓰기 권한 설정
  - HTMX 기반 폼 처리

- **사용자 관리 (/admin/users)**
  - 사용자 목록
  - 관리자 권한 부여/해제

##### 4. 에러 페이지
- **403 에러 페이지 (/403)** - 권한 없음 (사용자 친화적 메시지)
- **404 에러 페이지 (/404)** - 존재하지 않는 페이지
- **500 에러 페이지 (/500)** - 서버 오류

#### 페이지 플로우 다이어그램
```
[비로그인 사용자]
메인(/) → 로그인(/login) → 메인(/)
     ↓
   회원가입(/signup) → 메인(/)
     ↓
   이용약관(/terms), 개인정보처리방침(/privacy)
     ↓
   게시글 상세(/boards/{slug}/posts/{id}) - 읽기 권한 확인

[로그인 사용자]
메인(/?board={slug}) → [게시판 선택 - HTMX로 콘텐츠 갱신]
        ↓
   글쓰기(/boards/{slug}/posts/new) → 게시글 상세(/boards/{slug}/posts/{id})
        ↓                                      ↓
   글 수정(/boards/{slug}/posts/{id}/edit) ← 
        ↓
   메인(/?board={slug})로 돌아가기

[관리자]
메인(/) → 관리자 대시보드(/admin)
              ↓                    ↓
        게시판 관리(/admin/boards)  사용자 관리(/admin/users)
              ↓
        새 게시판 만들기(/boards/new) → 게시판 관리로 리다이렉트
```

#### 기술 스택 선택
- **리치 텍스트 에디터**: Quill.js
- **이미지 저장**: Base64 인코딩하여 content 필드에 직접 저장 (외부 URL 차단)
- **검색 기능**: PostgreSQL 전문 검색(ts_vector) 사용, 전체 게시판 대상
- **리스트 표시**: 페이지네이션 (무한 스크롤 미사용)
- **보안**: XSS 방어(bleach), CSRF 보호, 보안 헤더, Rate Limiting

#### 프로젝트 파일 구조
```
app/
├── main.py          # FastAPI 앱 초기화, 라우터 등록, 미들웨어 설정
├── auth.py          # 인증 관련 모든 기능 (라우터, 서비스, 모델, JWT 처리)
├── boards.py        # 게시판 관리 API
├── posts.py         # 게시글 관리 API
├── comments.py      # 댓글 관리 API
├── admin.py         # 관리자 기능
├── config.py        # 환경변수 및 설정 (Pydantic v2)
├── database.py      # Supabase 클라이언트 연결 및 데이터베이스 헬퍼
├── templates/       # Jinja2 HTML 템플릿
│   ├── base.html    # 기본 레이아웃 (Tailwind CSS, HTMX, Quill.js 포함)
│   ├── index.html   # 메인 페이지
│   ├── login.html   # 로그인 페이지
│   ├── signup.html  # 회원가입 페이지
│   ├── error.html   # 에러 페이지
│   ├── 403.html     # 403 권한 없음 페이지
│   ├── 404.html     # 404 에러 페이지
│   ├── 500.html     # 500 에러 페이지
│   ├── terms.html   # 이용약관 페이지
│   ├── privacy.html # 개인정보처리방침 페이지
│   ├── partials/    # HTMX 부분 템플릿
│   │   ├── board_posts.html  # 게시판 글 목록
│   │   └── search_results.html # 검색 결과
│   ├── boards/
│   │   └── new.html     # 새 게시판 만들기 페이지
│   ├── posts/
│   │   ├── create.html  # 게시글 작성 페이지
│   │   ├── detail.html  # 게시글 상세 페이지
│   │   └── edit.html    # 게시글 수정 페이지
│   └── admin/
│       ├── dashboard.html # 관리자 대시보드
│       ├── boards.html    # 게시판 관리
│       └── users.html     # 사용자 관리
├── static/          # 정적 파일
│   └── js/          # JavaScript 파일 (Quill 설정 등)
├── tests/           # 테스트 파일
│   ├── test_auth_htmx.py     # HTMX 인증 테스트
│   ├── test_boards_api.py    # 게시판 API 테스트
│   ├── test_posts_api.py     # 게시글 API 테스트
│   └── test_comments_api.py  # 댓글 API 테스트
├── Dockerfile       # FastAPI 앱 Docker 이미지
├── nginx.conf       # Nginx 설정
├── docker-compose.yml # Docker Compose 설정
├── requirements.txt   # Python 패키지 목록
└── .env              # 환경변수 파일 (Git에서 제외됨)
```

#### 주요 파일별 역할
- **main.py**: FastAPI 앱의 진입점, 전체 설정 및 라우터 통합
- **auth.py**: 인증의 모든 것 (회원가입, 로그인, JWT, 중복체크 등)
- **boards.py**: 게시판 CRUD API
- **posts.py**: 게시글 CRUD API 및 검색
- **comments.py**: 댓글/대댓글 CRUD API
- **admin.py**: 관리자 전용 기능
- **config.py**: 환경변수 로드 및 앱 설정 관리
- **database.py**: Supabase 연결 및 공통 DB 작업

#### 주요 API 엔드포인트
- **인증**: `/api/auth/*` (signup, login, logout, refresh, check-email, check-username)
- **게시판**: `/api/boards/*` (CRUD, 게시글 목록 HTML)
- **게시글**: `/api/posts/*` (CRUD)
- **댓글**: `/api/comments/*` (CRUD)
- **검색**: `/api/search/posts-html` (전체 게시판 검색)
- **관리자**: `/api/admin/*` (대시보드, 게시판/사용자 관리)

#### 보안 구현
- **XSS 방어**: bleach 라이브러리로 HTML sanitization
- **CSRF 보호**: Double Submit Cookie 패턴
- **인증**: JWT 기반 (HttpOnly 쿠키)
- **권한 관리**: 게시판별 읽기/쓰기 권한
- **보안 헤더**: CSP, X-Frame-Options, HSTS 등
- **Rate Limiting**: Nginx 레벨에서 구현

#### 데이터베이스 스키마
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
    icon VARCHAR(50),
    can_read VARCHAR(10) DEFAULT 'all',
    can_write VARCHAR(10) DEFAULT 'member',
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- public.posts 테이블
CREATE TABLE posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id UUID REFERENCES boards(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    content TEXT,
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

-- 전문 검색 관련 함수
-- HTML 태그 제거 함수
CREATE OR REPLACE FUNCTION strip_html_tags(html_content text) 
RETURNS text AS $$
BEGIN
    RETURN regexp_replace(
        regexp_replace(
            regexp_replace(
                regexp_replace(
                    regexp_replace(html_content, E'<[^>]+>', '', 'gi'),
                    '&nbsp;', ' ', 'gi'
                ),
                '&amp;', '&', 'gi'
            ),
            '&lt;', '<', 'gi'
        ),
        '&gt;', '>', 'gi'
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- search_vector 자동 업데이트 함수
CREATE OR REPLACE FUNCTION update_post_search_vector() 
RETURNS trigger AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('simple', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('simple', COALESCE(strip_html_tags(NEW.content), '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- search_vector 자동 업데이트 트리거
CREATE TRIGGER update_post_search_vector_trigger
BEFORE INSERT OR UPDATE OF title, content ON posts
FOR EACH ROW
EXECUTE FUNCTION update_post_search_vector();

-- 전체 게시판 검색 함수
CREATE OR REPLACE FUNCTION search_posts(
    search_query text,
    search_type text DEFAULT 'all',
    board_ids uuid[] DEFAULT NULL
) RETURNS TABLE (
    id uuid,
    board_id uuid,
    user_id uuid,
    title text,
    content text,
    is_pinned boolean,
    view_count integer,
    is_active boolean,
    created_at timestamptz,
    updated_at timestamptz,
    rank real
) AS $$
DECLARE
    ts_query tsquery;
    search_pattern text;
BEGIN
    search_pattern := '%' || search_query || '%';
    ts_query := plainto_tsquery('simple', search_query);
    
    RETURN QUERY
    SELECT DISTINCT
        p.id,
        p.board_id,
        p.user_id,
        p.title::text,
        p.content::text,
        p.is_pinned,
        p.view_count,
        p.is_active,
        p.created_at,
        p.updated_at,
        CASE 
            WHEN p.search_vector @@ ts_query THEN 
                ts_rank(p.search_vector, ts_query)
            ELSE 0.0
        END as rank
    FROM posts p
    WHERE 
        p.is_active = true
        AND (board_ids IS NULL OR p.board_id = ANY(board_ids))
        AND (
            (search_type IN ('all', 'title', 'content') AND p.search_vector @@ ts_query)
            OR
            (search_type IN ('all', 'title') AND p.title ILIKE search_pattern)
            OR
            (search_type IN ('all', 'content') AND strip_html_tags(p.content) ILIKE search_pattern)
        )
    ORDER BY 
        p.is_pinned DESC,
        rank DESC,
        p.created_at DESC,
        p.id DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- 특정 게시판 검색 함수
CREATE OR REPLACE FUNCTION search_board_posts(
    board_id_param uuid,
    search_query text,
    search_type text DEFAULT 'all'
) RETURNS TABLE (
    id uuid,
    board_id uuid,
    user_id uuid,
    title text,
    content text,
    is_pinned boolean,
    view_count integer,
    is_active boolean,
    created_at timestamptz,
    updated_at timestamptz,
    rank real
) AS $$
BEGIN
    RETURN QUERY 
    SELECT * FROM search_posts(
        search_query, 
        search_type, 
        ARRAY[board_id_param]::uuid[]
    );
END;
$$ LANGUAGE plpgsql STABLE;
```