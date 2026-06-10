# 2026-06-11 마니또 앱 설계 문서

## 개요

조선일보 54기 동기모임(9명)을 위한 시크릿 산타(마니또) 웹앱.  
참가자가 이름/비밀번호로 등록 → 9명 완료 시 자동 매칭 → 각자 본인의 마니또만 조회.

## 기술 스택

| 항목 | 선택 |
|------|------|
| 프레임워크 | Next.js 14 (App Router) + TypeScript |
| DB | Supabase (PostgreSQL) |
| 배포 | Vercel |
| 비밀번호 | bcrypt (서버 사이드) |
| 스타일 | Tailwind CSS |

## 프로젝트 구조

```
manitto-app/
├── app/
│   ├── page.tsx                  # 메인 화면
│   ├── join/page.tsx             # 참여하기
│   ├── check/page.tsx            # 확인하기
│   ├── api/
│   │   ├── register/route.ts     # POST: 등록 + 9번째 시 매칭 자동 실행
│   │   ├── check/route.ts        # POST: 비밀번호 검증 + 마니또 반환
│   │   └── count/route.ts        # GET: 현재 등록 인원 + 매칭 완료 여부
│   └── layout.tsx
├── lib/
│   ├── supabase.ts               # Supabase 서버 클라이언트 (Service Role Key)
│   ├── matching.ts               # Derangement 알고리즘
│   └── hash.ts                   # bcrypt 유틸
├── .env.local                    # 실제 키 (gitignore)
├── .env.example                  # 키 템플릿
└── README.md
```

## 데이터베이스 스키마

테이블 1개.

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

- `name UNIQUE` → DB 레벨 중복 등록 차단
- `manitto_name` → 매칭 전 NULL, 매칭 후 배정된 이름
- `matching_done` → 매칭 실행 락. `FALSE`인 레코드가 있을 때만 매칭 실행
- RLS 비활성화, 모든 DB 접근은 Service Role Key를 가진 서버 API로만 제한

## API Routes

### `POST /api/register`

**요청:** `{ name: string, password: string, passwordConfirm: string }`

**처리 순서:**
1. 빈값 검증
2. `password === passwordConfirm` 확인
3. 현재 participants 수 조회 → 9명이면 `"정원 9명이 모두 등록되었습니다"` 에러 반환
4. name 중복 확인 → `"이미 등록된 이름입니다"` 에러 반환
5. `bcrypt.hash(password, 10)` → INSERT
6. INSERT 후 총 인원 재조회 → 9명이면:
   - `matching_done = FALSE` 체크 (락)
   - 매칭 실행 → `manitto_name` 일괄 UPDATE → `matching_done = TRUE` UPDATE

**응답:** `{ success: boolean, message: string, count: number }`

### `POST /api/check`

**요청:** `{ name: string, password: string }`

**처리 순서:**
1. name으로 레코드 조회
2. `bcrypt.compare(password, password_hash)`
3. 일치하면 `manitto_name` 반환
4. `manitto_name`이 NULL이면 "아직 매칭 전" 메시지

**응답:** `{ success: boolean, manittoName?: string }` 또는 `{ error: string }`

**보안:** 이름 존재 여부 노출 없이 `"이름 또는 비밀번호가 올바르지 않습니다"` 단일 에러 메시지

### `GET /api/count`

**응답:** `{ count: number, matchingDone: boolean }`  
**용도:** 메인 화면 등록 인원 표시 + 확인하기 버튼 활성화

## 페이지 UI

### 메인 (`/`)
- 카드 중앙 정렬
- 제목: "2026년 조선일보 54기 동기모임 마니또 프로젝트"
- `n/9명 등록 완료` 배지 (페이지 로드 시 `/api/count` fetch)
- [마니또 참여하기] → `/join`
- [마니또 확인하기] → `matchingDone = false`이면 비활성화 + "9명 등록 완료 후 열려요" 표시

### 참여하기 (`/join`)
- 상단 안내: "54기 9명이 전부 등록하면 랜덤으로 마니또를 지정해줘요"
- 말풍선 박스: "마니또를 위해 내돈 주고는 절대 안 살 것 같지만, 마니또에게 찰떡일 것 같은 2만원 내외 아이템을 선물해 주세요"
- 입력: 이름 / 비밀번호 / 비밀번호 확인
- 에러 메시지 인라인 표시
- 성공 시: 페이지 이동 없이 "등록 완료! 9명이 모이면 마니또가 공개돼요" 메시지로 전환

### 확인하기 (`/check`)
- `matchingDone = false`이면 메인으로 리다이렉트
- 이름 + 비밀번호 입력
- 성공 시 결과 카드: `{이름}님의 마니또는 {마니또 이름}입니다`
- 안내 문구: "7월 2일 동기 모임까지 내돈 주고는 절대 안 살 것 같지만, 마니또에게 찰떡일 것 같은 2만원 내외 아이템을 선물해주세요"
- 비밀번호 불일치: "이름 또는 비밀번호가 올바르지 않습니다" 에러

### 디자인 토큰
- 배경: `#F2F2F7` (iOS 시스템 그레이)
- 카드: `white`, `border-radius: 20px`, 부드러운 그림자
- 포인트 그라데이션: `#FF6B6B → #FF8E53`
- 폰트: `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
- 버튼: 그라데이션 fill, `border-radius: 14px`
- 모바일 우선 반응형

## 매칭 알고리즘 (Derangement)

`lib/matching.ts` — Fisher-Yates 기반 반복 셔플:

```
1. 이름 배열 복사 후 Fisher-Yates 셔플
2. 자기 자신이 자기에게 배정된 위치가 있으면 재셔플
3. 최대 1000회 시도 (9명 기준 평균 1.6회 성공)
4. Map<원래이름, 배정된이름> 반환
```

- 일반 derangement (완전 순환 아님) → 더 자연스러운 랜덤성
- 매칭 실행은 단 1회 (`matching_done` 플래그로 보장)
- 매칭 완료 후 `manitto_name` UPDATE → `matching_done = TRUE` UPDATE 순서 보장

## 보안 원칙

- Supabase Service Role Key → 서버 사이드 환경변수만 사용 (`SUPABASE_SERVICE_ROLE_KEY`)
- Supabase Anon Key → 사용하지 않음 (클라이언트 노출 없음)
- API 응답에 본인 마니또만 포함, 전체 매칭 테이블 절대 노출 금지
- 등록 정보 수정/삭제 API 없음 (관리자는 Supabase 대시보드에서 직접 수정)
- bcrypt rounds: 10

## 예외 처리 목록

| 상황 | 처리 |
|------|------|
| 이름 중복 등록 | "이미 등록된 이름입니다" |
| 10번째 등록 시도 | "정원 9명이 모두 등록되었습니다" |
| 비밀번호 불일치 (입력) | "비밀번호가 일치하지 않습니다" |
| 비밀번호 불일치 (조회) | "이름 또는 비밀번호가 올바르지 않습니다" |
| 매칭 전 확인하기 접근 | 메인으로 리다이렉트 |
| 빈값 제출 | 인라인 에러 메시지 |

## 환경변수

```env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
```

## 배포

1. Vercel에 GitHub 레포 연결
2. Environment Variables에 위 2개 키 등록
3. `npm run build` 통과 확인 후 자동 배포
