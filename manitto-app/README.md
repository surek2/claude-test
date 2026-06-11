# 2026년 조선일보 54기 마니또

## 1. Supabase 테이블 생성

Supabase 대시보드 → SQL Editor에서 아래 SQL 실행:

```sql
CREATE TABLE participants (
  id            SERIAL PRIMARY KEY,
  name          TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  manitto_name  TEXT DEFAULT NULL,
  matching_done BOOLEAN NOT NULL DEFAULT FALSE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

RLS는 비활성화 상태로 유지 (서버 API에서 Service Role Key로만 접근).

## 2. 환경변수 설정

`.env.example`을 복사해 `.env.local`을 만들고 값을 채웁니다:

```bash
cp .env.example .env.local
```

| 변수 | 발급 방법 |
|------|-----------|
| `SUPABASE_URL` | Supabase 대시보드 → Settings → API → Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase 대시보드 → Settings → API → service_role (secret) |

## 3. 로컬 실행

```bash
npm install
npm run dev
# http://localhost:3000
```

## 4. Vercel 배포

1. GitHub에 레포 푸시
2. [vercel.com](https://vercel.com) → New Project → 레포 선택
3. Environment Variables에 아래 두 개 등록:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
4. Deploy 클릭 → 자동 빌드·배포

## 5. 관리자 운영 가이드

등록 정보 수정/삭제는 Supabase 대시보드 → Table Editor → `participants` 테이블에서 직접 처리합니다.

| 작업 | 방법 |
|------|------|
| 오등록 삭제 | 해당 row 선택 → Delete |
| 비밀번호 초기화 | `password_hash` 컬럼에 새 bcrypt 해시 입력 ([bcrypt-generator.com](https://bcrypt-generator.com), rounds=10) |
| 매칭 초기화 (긴급) | 전체 row의 `manitto_name = NULL`, `matching_done = FALSE`로 UPDATE |

## 6. 테이블 컬럼 설명

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | SERIAL | 자동 증가 PK |
| `name` | TEXT UNIQUE NOT NULL | 참가자 실명 |
| `password_hash` | TEXT NOT NULL | bcrypt(rounds=10) 해시 |
| `manitto_name` | TEXT NULL | 배정된 마니또 이름 (매칭 전 NULL) |
| `matching_done` | BOOLEAN NOT NULL | 매칭 완료 플래그 / 중복 실행 방지 락 |
| `created_at` | TIMESTAMPTZ | 등록 시각 |
