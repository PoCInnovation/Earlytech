use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use uuid::Uuid;
use chrono::{DateTime, Utc};

#[derive(Serialize)]
pub struct ArticleCount {
    pub count: i64,
}

#[derive(Debug, FromRow, Serialize, Deserialize)]
pub struct User {
    pub id: Uuid,
    pub name: String,
    pub email: String,
    #[serde(skip_serializing)]
    pub password_hash: String,
    pub role: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Deserialize)]
pub struct CreateUserSchema {
    pub name: String,
    pub email: String,
    pub password: String,
}

#[derive(Debug, Deserialize)]
pub struct LoginUserSchema {
    pub email: String,
    pub password: String,
}

#[derive(Debug, Serialize)]
pub struct TokenResponse {
    pub token: String,
    pub status: String,
}

#[derive(Debug, Serialize)]
pub struct ErrorResponse {
    pub status: String,
    pub message: String,
}

#[derive(Debug, FromRow, Serialize)]
pub struct UserKeyword {
    pub id: Uuid,
    pub user_id: Uuid,
    pub keyword: String,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Deserialize)]
pub struct CreateKeywordSchema {
    pub keyword: String,
}

#[derive(Debug, FromRow, Serialize)]
pub struct Article {
    pub id: String,
    pub title: Option<String>,
    pub url: String,
    pub source: String,
    pub content: Option<String>,
    pub summary: Option<String>,
    pub authors: Option<Vec<String>>,
    pub published_date: Option<DateTime<Utc>>,
    pub scraped_at: DateTime<Utc>,
}

#[derive(Debug, FromRow, Serialize)]
pub struct ArticleWithDelivery {
    pub id: String,
    pub title: Option<String>,
    pub url: String,
    pub source: String,
    pub summary: Option<String>,
    pub published_date: Option<DateTime<Utc>>,
    pub matched_keyword: String,
    pub similarity_score: f64,
    pub delivered_at: DateTime<Utc>,
}

#[derive(Debug, Serialize)]
pub struct UserFeedResponse {
    pub user_id: Uuid,
    pub total_articles: i64,
    pub articles: Vec<ArticleWithDelivery>,
}

#[derive(Debug, Serialize)]
pub struct ArticleListResponse {
    pub total: i64,
    pub page: i32,
    pub per_page: i32,
    pub articles: Vec<Article>,
}

#[derive(Debug, FromRow, Serialize)]
pub struct DeliveryStats {
    pub total_deliveries: i64,
    pub total_users: i64,
    pub total_keywords: i64,
    pub avg_similarity: Option<f64>,
}

#[derive(Debug, FromRow, Serialize)]
pub struct UserStats {
    pub user_id: Uuid,
    pub total_articles: i64,
    pub total_keywords: i64,
    pub avg_similarity: Option<f64>,
    pub last_delivery: Option<DateTime<Utc>>,
}

#[derive(Debug, FromRow, Serialize)]
pub struct RecentDelivery {
    pub id: Uuid,
    pub user_id: Uuid,
    pub user_name: String,
    pub article_id: String,
    pub article_title: Option<String>,
    pub keyword: String,
    pub similarity_score: f64,
    pub delivered_at: DateTime<Utc>,
}
