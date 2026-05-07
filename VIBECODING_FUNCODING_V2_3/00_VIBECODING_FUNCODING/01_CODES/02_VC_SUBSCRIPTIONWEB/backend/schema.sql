-- 구독자 테이블 생성
CREATE TABLE IF NOT EXISTS subscribers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    subscribed_at DATETIME NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 이메일 인덱스 생성 (검색 성능 향상)
CREATE INDEX IF NOT EXISTS idx_email ON subscribers(email);
CREATE INDEX IF NOT EXISTS idx_status ON subscribers(status);

