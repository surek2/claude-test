# AWS EC2 배포 가이드

## 사전 준비
- EC2 인스턴스 (Ubuntu 20.04 이상)
- Docker, Docker Compose 설치됨
- 보안 그룹에서 80 포트 오픈

## 배포 단계

### 1. 프로젝트 업로드
- 폴더 생성 후, FTP 등 활용

### 2. 환경 설정
```bash
# .env 파일 수정
nano .env

# CORS 설정 변경 (필요시)
# CORS_ORIGINS=["*"] 또는 ["http://YOUR-EC2-IP"]
```

### 3. 실행
```bash
sudo docker-compose up -d
```

### 4. 확인
```bash
# 로그 확인
sudo docker-compose logs -f

# 브라우저에서 접속
http://YOUR-EC2-IP
```

## 필수 파일 목록
- `.env` - 환경 설정
- `.dockerignore` - Docker 빌드 시 제외 파일
- `docker-compose.yml` - Docker 구성
- `Dockerfile` - FastAPI 이미지
- `nginx.conf` - Nginx 설정
- `requirements.txt` - Python 패키지
- `/app` - 애플리케이션 코드
- `/templates` - HTML 템플릿
- `/static` - 정적 파일

## 트러블슈팅
- 포트 80 접속 안됨 → 보안 그룹 확인
- 502 에러 → `sudo docker-compose logs fastapi` 확인
- CORS 에러 → `.env`의 CORS_ORIGINS 수정