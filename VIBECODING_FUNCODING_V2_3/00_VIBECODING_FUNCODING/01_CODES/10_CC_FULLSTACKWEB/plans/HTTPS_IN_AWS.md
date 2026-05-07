# AWS에서 HTTPS 설정 가이드 (CloudFront + EC2 + Route 53)

## 📋 시작하기 전에

### 현재 상황
- EC2 인스턴스에서 Docker로 웹 애플리케이션이 포트 80으로 실행 중
- Route 53에서 도메인 구매 완료 (예: example.com)
- HTTPS로 서비스하고 싶음

### 필요한 AWS 서비스
1. **Route 53**: 도메인 관리
2. **ACM (AWS Certificate Manager)**: SSL 인증서 (무료!)
3. **CloudFront**: CDN + HTTPS 제공

## 🔐 Step 1: SSL 인증서 발급받기 (ACM)

### 1.1 ACM 콘솔 접속
1. AWS 콘솔에서 "Certificate Manager" 검색
2. **⚠️ 중요**: 리전을 **"미국 동부 (버지니아 북부)"**로 변경
   - CloudFront는 이 리전의 인증서만 사용 가능

### 1.2 인증서 요청
1. "인증서 요청" 버튼 클릭
2. "퍼블릭 인증서 요청" 선택 → "다음"
3. 도메인 이름 입력:
   ```
   example.com
   *.example.com  (서브도메인도 함께 보호)
   ```
4. 검증 방법: "DNS 검증" 선택 (권장)
5. "요청" 버튼 클릭

### 1.3 DNS 검증
1. 인증서 상세 페이지에서 "Route 53에서 레코드 생성" 버튼 클릭
2. "레코드 생성" 클릭
3. 5-10분 대기 → 상태가 "발급됨"으로 변경 확인

## 🌐 Step 2: CloudFront 배포 생성

### 2.1 CloudFront 콘솔 접속
1. AWS 콘솔에서 "CloudFront" 검색
2. "배포 생성" 버튼 클릭

### 2.2 원본 설정
1. **원본 도메인**: EC2의 퍼블릭 DNS 입력
   ```
   ec2-52-79-xxx-xxx.ap-northeast-2.compute.amazonaws.com
   ```
2. **프로토콜**: "HTTP만 해당" 선택
3. **HTTP 포트**: 80 (기본값)

### 2.3 기본 캐시 동작 설정
1. **뷰어 프로토콜 정책**: "HTTP를 HTTPS로 리디렉션" 선택
2. **허용된 HTTP 메서드**: "GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE" 선택
3. **캐시 정책**: "CachingDisabled" 선택 (동적 웹사이트이므로)

### 2.4 설정
1. **대체 도메인 이름(CNAME)**: 
   ```
   example.com
   www.example.com
   ```
2. **사용자 정의 SSL 인증서**: Step 1에서 만든 인증서 선택
3. **기본 루트 객체**: 비워두기 (EC2가 처리)

### 2.5 배포 생성
1. "배포 생성" 버튼 클릭
2. 10-20분 대기 (상태: "배포 중" → "배포됨")
3. CloudFront 도메인 이름 복사 (예: d1234567890.cloudfront.net)

## 🔗 Step 3: Route 53 설정

### 3.1 호스팅 영역 접속
1. Route 53 콘솔 → "호스팅 영역"
2. 구매한 도메인 클릭

### 3.2 A 레코드 생성 (example.com)
1. "레코드 생성" 버튼 클릭
2. 설정:
   - **레코드 이름**: 비워두기
   - **레코드 유형**: A
   - **별칭**: 켜기 ✓
   - **트래픽 라우팅 대상**: 
     - "CloudFront 배포에 대한 별칭" 선택
     - Step 2에서 만든 배포 선택
3. "레코드 생성" 클릭

### 3.3 A 레코드 생성 (www.example.com)
1. 위 과정 반복
2. **레코드 이름**: www 입력
3. 나머지는 동일

## ✅ Step 4: 확인 및 설정 조정

### 4.1 HTTPS 접속 테스트
```bash
# 10-30분 후 테스트
https://example.com
https://www.example.com
```

### 4.2 애플리케이션 설정 수정

#### .env 파일 수정
```bash
# EC2에서
cd ~/aicom
nano .env

# 수정 사항
CORS_ORIGINS=["https://example.com", "https://www.example.com"]
COOKIE_SECURE=true

# Docker 재시작
sudo docker-compose down
sudo docker-compose up -d
```

## 🔧 문제 해결

### 1. "502 Bad Gateway" 에러
- CloudFront가 EC2에 접속 못함
- 해결: EC2 보안 그룹에서 CloudFront IP 범위 허용
  ```bash
  # 보안 그룹 인바운드 규칙 추가
  유형: HTTP
  포트: 80
  소스: 0.0.0.0/0 (모든 IP)
  ```

### 2. 인증서가 보이지 않음
- ACM 인증서가 "미국 동부 (버지니아 북부)" 리전에 있는지 확인

### 3. DNS 전파 대기
- Route 53 설정 후 5-30분 대기 필요

## 🎉 완료!

이제 다음과 같이 작동합니다:
1. 사용자가 `https://example.com` 접속
2. CloudFront가 HTTPS 제공
3. CloudFront → EC2는 HTTP 통신 (내부 네트워크)
4. 빠르고 안전한 서비스 제공

### 장점
- ✅ 무료 SSL 인증서
- ✅ 자동 인증서 갱신
- ✅ 전 세계 CDN으로 빠른 속도
- ✅ DDoS 방어 기본 제공
- ✅ HTTP/2 자동 지원