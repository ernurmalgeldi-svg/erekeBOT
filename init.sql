-- Задача 29: Инициализация PostgreSQL при первом запуске контейнера

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS messages (
    id          SERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL,
    user_message TEXT,
    bot_response TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rate_limits (
    key         TEXT PRIMARY KEY,
    tokens      FLOAT NOT NULL DEFAULT 10,
    last_update TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
