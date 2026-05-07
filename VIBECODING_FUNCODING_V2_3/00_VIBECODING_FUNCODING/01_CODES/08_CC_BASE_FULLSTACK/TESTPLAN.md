# AIZEVA 테스트 계획

## 테스트 전략
- 테스트 레벨별로 각각 테스트
  1. **단위 테스트**: 개별 함수 및 메서드
  2. **통합 테스트**: API 엔드포인트
  3. **E2E 테스트**: 전체 사용자 시나리오

## 테스트 환경
- **로컬**: Python pytest + Docker Compose
- **E2E**: Puppeteer MCP
- **데이터베이스**: 실제 Supabase 환경 (.env)

## 기능별 테스트 케이스

