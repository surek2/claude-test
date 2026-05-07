# 프로젝트: MyTODO 웹서비스

## 목적
개인용 할일 저장 및 관리 웹서비스

## 기술 스택
- 프론트엔드: HTML, CSS, JS + Tailwind CSS (정적 파일)
- 백엔드: JavaScript (Cloudflare Pages Functions 용)
- 데이터베이스: Cloudflare D1
- 배포: Cloudflare Pages + Cloudflare Pages Functions 

## 핵심 규칙
- 로그인 기능 불필요
- 토스 디자인 스타일을 따라주세요

## 구조
todo-app/
├── public/          # 정적 파일 (Cloudflare Pages)
├── functions/       # 백엔드 (Cloudflare Pages Functions)
└── designs/         # XML 디자인 파일