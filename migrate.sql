-- Migration: create full database schema
-- Run with: psql earlytech < migrate.sql

BEGIN;

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Articles (scrapper columns + Rust alias columns)
CREATE TABLE IF NOT EXISTS articles (
    id TEXT PRIMARY KEY,
    source_site TEXT NOT NULL,
    title TEXT,
    description TEXT,
    full_content TEXT,
    content_hash TEXT UNIQUE,
    author_info TEXT,
    keywords TEXT,
    content_url TEXT NOT NULL,
    published_date TIMESTAMPTZ,
    item_type TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    primary_subject TEXT,
    secondary_subject TEXT,
    primary_organizations JSONB,
    secondary_organizations JSONB,
    primary_event_type TEXT,
    secondary_event_type TEXT,
    cluster_id INTEGER,
    -- Rust server alias columns
    url TEXT,
    source TEXT,
    summary TEXT,
    authors TEXT[],
    content TEXT,
    scraped_at TIMESTAMPTZ
);

-- Embeddings
CREATE TABLE IF NOT EXISTS embeddings (
    id SERIAL PRIMARY KEY,
    article_id TEXT NOT NULL UNIQUE REFERENCES articles(id) ON DELETE CASCADE,
    embedding vector(1536) NOT NULL,
    embedding_model TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cluster_id ON articles(cluster_id);

-- Users (UUID, auth-ready)
DROP TABLE IF EXISTS user_article_delivery CASCADE;
DROP TABLE IF EXISTS user_keyword_embeddings CASCADE;
DROP TABLE IF EXISTS user_keywords CASCADE;
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT 'user',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- User keywords
CREATE TABLE user_keywords (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    keyword TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, keyword)
);

-- Keyword embeddings
CREATE TABLE user_keyword_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keyword_id UUID NOT NULL UNIQUE REFERENCES user_keywords(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    keyword TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    embedding_model TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Article delivery
CREATE TABLE user_article_delivery (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    article_id TEXT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    keyword_id UUID REFERENCES user_keywords(id) ON DELETE SET NULL,
    similarity_score FLOAT NOT NULL,
    delivered_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, article_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_user_keywords ON user_keywords(user_id);
CREATE INDEX IF NOT EXISTS idx_keyword_embeddings ON user_keyword_embeddings(user_id);
CREATE INDEX IF NOT EXISTS idx_user_article_delivery ON user_article_delivery(user_id);

-- Trigger: auto-populate Rust alias columns on article insert/update
CREATE OR REPLACE FUNCTION sync_article_aliases() RETURNS TRIGGER AS $$
BEGIN
    NEW.url := COALESCE(NEW.url, NEW.content_url);
    NEW.source := COALESCE(NEW.source, NEW.source_site);
    NEW.summary := COALESCE(NEW.summary, NEW.description);
    NEW.content := COALESCE(NEW.content, NEW.full_content);
    NEW.scraped_at := COALESCE(NEW.scraped_at, NEW.created_at, CURRENT_TIMESTAMP);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_article_aliases ON articles;
CREATE TRIGGER trg_sync_article_aliases
    BEFORE INSERT OR UPDATE ON articles
    FOR EACH ROW
    EXECUTE FUNCTION sync_article_aliases();

COMMIT;
