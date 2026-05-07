# AICOM 프로젝트 개발 시 주의사항 및 해결방안

## 1. HTMX 폼 제출 시 JSON 응답 표시 문제

### 문제
- 폼 제출 후 JSON 응답(`{"message":"..."}`)이 화면에 그대로 표시됨
- 특히 게시글 작성, 댓글 작성, 로그아웃 등에서 발생

### 해결방안
```html
<!-- 잘못된 방법 -->
<form action="/api/endpoint" method="post">

<!-- 올바른 방법 -->
<form hx-post="/api/endpoint" 
      hx-swap="none"
      hx-on::after-request="if(event.detail.xhr.status === 201) { window.location.reload(); }">
```

- `hx-swap="none"` 필수 추가
- 서버에서 적절한 상태 코드 반환 (201 for create, 204 for delete)
- 리다이렉트가 필요한 경우 서버에서 `HX-Redirect` 헤더 설정

## 2. 삭제된 항목이 여전히 표시되는 문제

### 문제
- 댓글 삭제 후에도 화면에 남아있음
- 댓글 개수가 잘못 표시됨

### 해결방안
- 모든 쿼리에 `is_active=True` 필터 추가
- 카운트 쿼리에도 동일하게 적용
```python
# 잘못된 방법
db.select("comments", filters={"post_id": post_id})

# 올바른 방법
db.select("comments", filters={"post_id": post_id, "is_active": True})
```

## 3. bleach 라이브러리 버전 호환성

### 문제
- bleach 6.x에서 `styles` 파라미터가 제거됨
- `TypeError: clean() got an unexpected keyword argument 'styles'`

### 해결방안
```python
# 잘못된 방법
bleach.clean(content, styles=allowed_styles)

# 올바른 방법 (bleach 6.x)
bleach.clean(content, tags=allowed_tags, attributes=allowed_attributes, strip=True)
```

## 4. 게시글 정렬 순서 불일치

### 문제
- 동일한 게시판이 다른 경로에서 다른 순서로 표시됨
- Supabase Python 클라이언트의 체인된 order() 호출 문제

### 해결방안
```python
# 문제가 있는 방법
query.order("is_pinned", desc=True).order("created_at", desc=True)

# 올바른 방법
query.order("is_pinned.desc.nullslast,created_at.desc.nullslast,id.desc.nullslast")
```

## 5. CSRF 토큰 누락

### 문제
- 일부 폼에서 CSRF 토큰이 누락되어 403 에러 발생

### 해결방안
- 모든 POST 폼에 CSRF 토큰 포함
- 특히 동적으로 생성되는 폼 주의
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token }}">
```

## 6. 사용자 정보 표시 일관성

### 문제
- 일부 페이지에서 username 대신 email이 표시됨
- user 객체에 username이 없는 경우 처리 누락

### 해결방안
```html
<!-- 항상 이 패턴 사용 -->
{{ user.username or user.email }}
```

## 7. 데이터베이스 스키마 불일치

### 문제
- 코드에서 사용하는 필드가 실제 DB에 없음
- `display_order`, `is_active` 등 필드 누락

### 해결방안
- 마이그레이션 파일 작성 및 적용
- PROGRESS.md의 스키마 정의와 실제 DB 스키마 일치 확인

## 8. 상태 코드 사용 일관성

### 문제
- API 엔드포인트의 상태 코드가 일관되지 않음
- 클라이언트에서 예측하기 어려움

### 해결방안
- 생성: 201 (Created)
- 삭제: 204 (No Content)
- 성공: 200 (OK)
- 에러: 4xx, 5xx

## 9. 페이지네이션 상태 유지

### 문제
- 게시글 상세 페이지에서 목록으로 돌아올 때 1페이지로 리셋됨

### 해결방안
- URL 파라미터로 페이지 정보 전달
- `from_page` 파라미터 활용

## 10. 이미지 크기 제한

### 문제
- Base64 인코딩된 대용량 이미지로 인한 성능 문제

### 해결방안
- 1MB 크기 제한 구현
- 초과 시 에러 메시지 표시
```python
if len(src) > max_image_size * 1.33:  # Base64는 약 33% 더 큼
    # 에러 처리
```

## 개발 시 체크리스트

1. [ ] HTMX 폼은 항상 `hx-swap` 속성 확인
2. [ ] 삭제 기능은 soft delete (`is_active=False`)
3. [ ] 모든 조회 쿼리에 `is_active=True` 필터
4. [ ] CSRF 토큰 포함 여부 확인
5. [ ] 사용자 표시는 `username or email` 패턴
6. [ ] 정렬은 명시적으로 3단계 (is_pinned, created_at, id)
7. [ ] 상태 코드 일관성 (201, 204 등)
8. [ ] 에러 처리 시 HTMX 요청 구분

## 11. Supabase 프로젝트 설정 시 주의사항

### 문제
- 새 Supabase 프로젝트 생성 후 로그인/회원가입 실패
- "Email not confirmed" 에러 발생

### 해결방안
1. **Supabase 대시보드 설정**
   - Authentication → Settings → Auth providers → Email
   - "Confirm email" 옵션을 OFF로 변경 (필수!)
   
2. **환경변수 확인**
   - Supabase Dashboard → Settings → API
   - JWT Secret 복사하여 `.env`의 `SUPABASE_JWT_SECRET` 업데이트
   - Service Role Key 복사하여 `.env`의 `SUPABASE_SERVICE_ROLE_KEY` 업데이트
   
3. **비밀번호 정책**
   - 최소 6자 이상 (Supabase 대시보드와 코드 모두 일치)
   - 특별한 문자 요구사항 없음