use sqlx::postgres::PgPoolOptions;
use sqlx::{Pool, Postgres};
use std::env;

pub async fn establish_connection() -> Pool<Postgres> {
    let database_url = env::var("DATABASE_URL").expect("DATABASE_URL must be set");

    let pool = PgPoolOptions::new()
        .max_connections(5)
        .connect(&database_url)
        .await
        .expect("Failed to connect to Postgres");

    sqlx::query(
        r#"
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            digest_enabled BOOLEAN NOT NULL DEFAULT false,
            digest_frequency TEXT NOT NULL DEFAULT 'daily',
            digest_hour_utc SMALLINT NOT NULL DEFAULT 8,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (digest_frequency IN ('daily', 'weekly')),
            CHECK (digest_hour_utc BETWEEN 0 AND 23)
        )
        "#,
    )
    .execute(&pool)
    .await
    .expect("Failed to ensure user_preferences table");

    sqlx::query(
        r#"
        CREATE TABLE IF NOT EXISTS user_excluded_sources (
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            source TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, source)
        )
        "#,
    )
    .execute(&pool)
    .await
    .expect("Failed to ensure user_excluded_sources table");

    sqlx::query(
        r#"
        CREATE TABLE IF NOT EXISTS user_excluded_keywords (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            keyword TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (user_id, keyword)
        )
        "#,
    )
    .execute(&pool)
    .await
    .expect("Failed to ensure user_excluded_keywords table");

    sqlx::query(
        r#"
        CREATE TABLE IF NOT EXISTS user_article_feedback (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            article_id TEXT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
            feedback TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (user_id, article_id),
            CHECK (feedback IN ('relevant', 'not_relevant'))
        )
        "#,
    )
    .execute(&pool)
    .await
    .expect("Failed to ensure user_article_feedback table");

    pool
}
