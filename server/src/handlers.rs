use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde_json::json;
use argon2::{
    password_hash::{
        rand_core::OsRng,
        PasswordHash, PasswordHasher, PasswordVerifier, SaltString
    },
    Argon2
};
use jsonwebtoken::{encode, EncodingKey, Header};
use chrono::{Utc, Duration};
use uuid::Uuid;
use crate::models::*;
use crate::state::AppState;

pub enum AppError {
    InternalServerError,
    UserAlreadyExists,
    InvalidCredentials,
    KeywordAlreadyExists,
    InvalidKeyword,
    InvalidInput(String),
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, message): (StatusCode, String) = match self {
            AppError::InternalServerError => (StatusCode::INTERNAL_SERVER_ERROR, "Internal server error".to_string()),
            AppError::UserAlreadyExists => (StatusCode::CONFLICT, "User with that email already exists".to_string()),
            AppError::InvalidCredentials => (StatusCode::UNAUTHORIZED, "Invalid email or password".to_string()),
            AppError::KeywordAlreadyExists => (StatusCode::CONFLICT, "Keyword already exists for this user".to_string()),
            AppError::InvalidKeyword => (StatusCode::BAD_REQUEST, "Keyword must not be empty".to_string()),
            AppError::InvalidInput(message) => (StatusCode::BAD_REQUEST, message),
        };
        (status, Json(json!({"error": message}))).into_response()
    }
}

fn is_valid_source(source: &str) -> bool {
    matches!(source, "arxiv" | "github" | "medium" | "le_monde" | "huggingface")
}

pub async fn get_article_count(State(state): State<AppState>) -> Json<ArticleCount> {
    let count: i64 = sqlx::query_scalar("SELECT count(*) FROM articles")
        .fetch_one(&state.pool)
        .await
        .unwrap_or(0); // Safer handling

    Json(ArticleCount { count })
}

pub async fn register_user_handler(
    State(state): State<AppState>,
    Json(body): Json<CreateUserSchema>,
) -> Result<impl IntoResponse, AppError> {
    let user_exists = sqlx::query("SELECT 1 FROM users WHERE email = $1")
        .bind(&body.email.to_lowercase())
        .fetch_optional(&state.pool)
        .await
        .map_err(|_| AppError::InternalServerError)?;

    if user_exists.is_some() {
        return Err(AppError::UserAlreadyExists);
    }

    let salt = SaltString::generate(&mut OsRng);
    let argon2 = Argon2::default();
    let password_hash = argon2.hash_password(body.password.as_bytes(), &salt)
        .map_err(|_| AppError::InternalServerError)?
        .to_string();

    let user_id: uuid::Uuid = sqlx::query_scalar(
        "INSERT INTO users (name, email, password_hash) VALUES ($1, $2, $3) RETURNING id",
    )
    .bind(body.name)
    .bind(body.email.to_lowercase())
    .bind(password_hash)
    .fetch_one(&state.pool)
    .await
    .map_err(|_| AppError::InternalServerError)?;

    Ok((StatusCode::CREATED, Json(json!({"status": "success", "user": {"id": user_id}}))))
}

pub async fn login_user_handler(
    State(state): State<AppState>,
    Json(body): Json<LoginUserSchema>,
) -> Result<impl IntoResponse, AppError> {
    let user = sqlx::query_as::<_, User>("SELECT * FROM users WHERE email = $1")
        .bind(&body.email.to_lowercase())
        .fetch_optional(&state.pool)
        .await
        .map_err(|_| AppError::InternalServerError)?;

    let user = user.ok_or(AppError::InvalidCredentials)?;

    let parsed_hash = PasswordHash::new(&user.password_hash)
        .map_err(|_| AppError::InternalServerError)?;
    
    Argon2::default().verify_password(body.password.as_bytes(), &parsed_hash)
        .map_err(|_| AppError::InvalidCredentials)?;

    let secret = std::env::var("JWT_SECRET").unwrap_or_else(|_| "secret".to_string());
    
    let now = Utc::now();
    let iat = now.timestamp() as usize;
    let exp = (now + Duration::minutes(60)).timestamp() as usize;
    let claims = json!({
        "sub": user.id,
        "role": user.role,
        "exp": exp,
        "iat": iat,
    });

    let token = encode(&Header::default(), &claims, &EncodingKey::from_secret(secret.as_bytes()))
        .map_err(|_| AppError::InternalServerError)?;

    Ok(Json(TokenResponse {
        status: "success".to_string(),
        token,
    }))
}

pub async fn list_user_keywords(
    Path(user_id): Path<Uuid>,
    State(state): State<AppState>,
) -> Result<Json<Vec<UserKeyword>>, AppError> {
    let keywords = sqlx::query_as::<_, UserKeyword>(
        "SELECT id, user_id, keyword, created_at FROM user_keywords WHERE user_id = $1 ORDER BY created_at DESC",
    )
    .bind(user_id)
    .fetch_all(&state.pool)
    .await
    .map_err(|_| AppError::InternalServerError)?;

    Ok(Json(keywords))
}

pub async fn add_user_keyword(
    Path(user_id): Path<Uuid>,
    State(state): State<AppState>,
    Json(body): Json<CreateKeywordSchema>,
) -> Result<impl IntoResponse, AppError> {
    let keyword = body.keyword.trim().to_lowercase();
    if keyword.is_empty() {
        return Err(AppError::InvalidKeyword);
    }

    let inserted = sqlx::query_as::<_, UserKeyword>(
        "INSERT INTO user_keywords (user_id, keyword) VALUES ($1, $2) \n         ON CONFLICT (user_id, keyword) DO NOTHING \n         RETURNING id, user_id, keyword, created_at",
    )
    .bind(user_id)
    .bind(keyword)
    .fetch_optional(&state.pool)
    .await
    .map_err(|_| AppError::InternalServerError)?;

    match inserted {
        Some(keyword) => Ok((StatusCode::CREATED, Json(keyword))),
        None => Err(AppError::KeywordAlreadyExists),
    }
}

pub async fn delete_user_keyword(
    Path((user_id, keyword_id)): Path<(Uuid, Uuid)>,
    State(state): State<AppState>,
) -> Result<impl IntoResponse, AppError> {
    let result = sqlx::query(
        "DELETE FROM user_keywords WHERE id = $1 AND user_id = $2",
    )
    .bind(keyword_id)
    .bind(user_id)
    .execute(&state.pool)
    .await
    .map_err(|_| AppError::InternalServerError)?;

    if result.rows_affected() == 0 {
        return Err(AppError::InvalidKeyword);
    }

    Ok(StatusCode::NO_CONTENT)
}

pub async fn get_user_feed(
    Path(user_id): Path<Uuid>,
    State(state): State<AppState>,
) -> Result<Json<UserFeedResponse>, AppError> {
    let articles = sqlx::query_as::<_, ArticleWithDelivery>(
        r#"
        SELECT 
            a.id, a.title, a.url, a.source, a.summary, a.published_date,
            uk.keyword as matched_keyword,
            uad.similarity_score,
            uad.delivered_at,
            uaf.feedback
        FROM user_article_delivery uad
        JOIN articles a ON uad.article_id = a.id
        JOIN user_keywords uk ON uad.keyword_id = uk.id
        LEFT JOIN user_article_feedback uaf ON uaf.user_id = uad.user_id AND uaf.article_id = uad.article_id
        WHERE uad.user_id = $1
          AND NOT EXISTS (
              SELECT 1
              FROM user_excluded_sources ues
              WHERE ues.user_id = uad.user_id AND ues.source = a.source
          )
          AND NOT EXISTS (
              SELECT 1
              FROM user_excluded_keywords uek
              WHERE uek.user_id = uad.user_id AND uek.keyword = uk.keyword
          )
        ORDER BY uad.delivered_at DESC
        LIMIT 50
        "#,
    )
    .bind(user_id)
    .fetch_all(&state.pool)
    .await
    .map_err(|_| AppError::InternalServerError)?;

    let total: i64 = sqlx::query_scalar(
        "SELECT COUNT(*) FROM user_article_delivery WHERE user_id = $1",
    )
    .bind(user_id)
    .fetch_one(&state.pool)
    .await
    .unwrap_or(0);

    Ok(Json(UserFeedResponse {
        user_id,
        total_articles: total,
        articles,
    }))
}

pub async fn list_articles(
    State(state): State<AppState>,
) -> Result<Json<ArticleListResponse>, AppError> {
    let articles = sqlx::query_as::<_, Article>(
        "SELECT id, title, url, source, content, summary, authors, published_date, scraped_at \n         FROM articles \n         ORDER BY scraped_at DESC \n         LIMIT 50",
    )
    .fetch_all(&state.pool)
    .await
    .map_err(|_| AppError::InternalServerError)?;

    let total: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM articles")
        .fetch_one(&state.pool)
        .await
        .unwrap_or(0);

    Ok(Json(ArticleListResponse {
        total,
        page: 1,
        per_page: 50,
        articles,
    }))
}

pub async fn get_article(
    Path(article_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<Article>, AppError> {
    let article = sqlx::query_as::<_, Article>(
        "SELECT id, title, url, source, content, summary, authors, published_date, scraped_at \n         FROM articles \n         WHERE id = $1",
    )
    .bind(&article_id)
    .fetch_optional(&state.pool)
    .await
    .map_err(|_| AppError::InternalServerError)?;

    article
        .map(Json)
        .ok_or(AppError::InternalServerError)
}

pub async fn get_user_stats(
    Path(user_id): Path<Uuid>,
    State(state): State<AppState>,
) -> Result<Json<UserStats>, AppError> {
    let stats = sqlx::query_as::<_, UserStats>(
        r#"
        SELECT 
            $1::uuid as user_id,
            COUNT(DISTINCT uad.article_id) as total_articles,
            COUNT(DISTINCT uad.keyword_id) as total_keywords,
            AVG(uad.similarity_score) as avg_similarity,
            MAX(uad.delivered_at) as last_delivery
        FROM user_article_delivery uad
        WHERE uad.user_id = $1
        "#,
    )
    .bind(user_id)
    .fetch_one(&state.pool)
    .await
    .map_err(|_| AppError::InternalServerError)?;

    Ok(Json(stats))
}

pub async fn get_delivery_stats(
    State(state): State<AppState>,
) -> Result<Json<DeliveryStats>, AppError> {
    let stats = sqlx::query_as::<_, DeliveryStats>(
        r#"
        SELECT 
            COUNT(*) as total_deliveries,
            COUNT(DISTINCT user_id) as total_users,
            COUNT(DISTINCT keyword_id) as total_keywords,
            AVG(similarity_score) as avg_similarity
        FROM user_article_delivery
        "#,
    )
    .fetch_one(&state.pool)
    .await
    .map_err(|_| AppError::InternalServerError)?;

    Ok(Json(stats))
}

pub async fn get_recent_deliveries(
    State(state): State<AppState>,
) -> Result<Json<Vec<RecentDelivery>>, AppError> {
    let deliveries = sqlx::query_as::<_, RecentDelivery>(
        r#"
        SELECT 
            uad.id,
            uad.user_id,
            u.name as user_name,
            uad.article_id,
            a.title as article_title,
            uk.keyword,
            uad.similarity_score,
            uad.delivered_at
        FROM user_article_delivery uad
        JOIN users u ON uad.user_id = u.id
        JOIN articles a ON uad.article_id = a.id
        JOIN user_keywords uk ON uad.keyword_id = uk.id
        ORDER BY uad.delivered_at DESC
        LIMIT 20
        "#,
    )
    .fetch_all(&state.pool)
    .await
    .map_err(|_| AppError::InternalServerError)?;

    Ok(Json(deliveries))
}

pub async fn get_user_preferences(
    Path(user_id): Path<Uuid>,
    State(state): State<AppState>,
) -> Result<Json<UserPreferences>, AppError> {
    sqlx::query(
        r#"
        INSERT INTO user_preferences (user_id)
        VALUES ($1)
        ON CONFLICT (user_id) DO NOTHING
        "#,
    )
    .bind(user_id)
    .execute(&state.pool)
    .await
    .map_err(|_| AppError::InternalServerError)?;

    let prefs = sqlx::query_as::<_, UserPreferences>(
        r#"
        SELECT user_id, digest_enabled, digest_frequency, digest_hour_utc, updated_at
        FROM user_preferences
        WHERE user_id = $1
        "#,
    )
    .bind(user_id)
    .fetch_one(&state.pool)
    .await
    .map_err(|_| AppError::InternalServerError)?;

    Ok(Json(prefs))
}

pub async fn update_user_preferences(
    Path(user_id): Path<Uuid>,
    State(state): State<AppState>,
    Json(body): Json<UpdateUserPreferencesSchema>,
) -> Result<Json<UserPreferences>, AppError> {
    if body.digest_hour_utc < 0 || body.digest_hour_utc > 23 {
        return Err(AppError::InvalidInput("digest_hour_utc must be between 0 and 23".to_string()));
    }
    if body.digest_frequency != "daily" && body.digest_frequency != "weekly" {
        return Err(AppError::InvalidInput("digest_frequency must be daily or weekly".to_string()));
    }

    let prefs = sqlx::query_as::<_, UserPreferences>(
        r#"
        INSERT INTO user_preferences (user_id, digest_enabled, digest_frequency, digest_hour_utc)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (user_id)
        DO UPDATE SET
            digest_enabled = EXCLUDED.digest_enabled,
            digest_frequency = EXCLUDED.digest_frequency,
            digest_hour_utc = EXCLUDED.digest_hour_utc,
            updated_at = CURRENT_TIMESTAMP
        RETURNING user_id, digest_enabled, digest_frequency, digest_hour_utc, updated_at
        "#,
    )
    .bind(user_id)
    .bind(body.digest_enabled)
    .bind(body.digest_frequency)
    .bind(body.digest_hour_utc)
    .fetch_one(&state.pool)
    .await
    .map_err(|_| AppError::InternalServerError)?;

    Ok(Json(prefs))
}

pub async fn get_user_exclusions(
    Path(user_id): Path<Uuid>,
    State(state): State<AppState>,
) -> Result<Json<UserExclusionResponse>, AppError> {
    let sources = sqlx::query_scalar::<_, String>(
        r#"
        SELECT source
        FROM user_excluded_sources
        WHERE user_id = $1
        ORDER BY source ASC
        "#,
    )
    .bind(user_id)
    .fetch_all(&state.pool)
    .await
    .map_err(|_| AppError::InternalServerError)?;

    let keywords = sqlx::query_as::<_, UserExcludedKeyword>(
        r#"
        SELECT id, user_id, keyword, created_at
        FROM user_excluded_keywords
        WHERE user_id = $1
        ORDER BY created_at DESC
        "#,
    )
    .bind(user_id)
    .fetch_all(&state.pool)
    .await
    .map_err(|_| AppError::InternalServerError)?;

    Ok(Json(UserExclusionResponse { sources, keywords }))
}

pub async fn add_excluded_source(
    Path(user_id): Path<Uuid>,
    State(state): State<AppState>,
    Json(body): Json<UpdateExcludedSourceSchema>,
) -> Result<impl IntoResponse, AppError> {
    let source = body.source.trim().to_lowercase();
    if !is_valid_source(&source) {
        return Err(AppError::InvalidInput(
            "source must be one of: arxiv, github, medium, le_monde, huggingface".to_string(),
        ));
    }

    sqlx::query(
        r#"
        INSERT INTO user_excluded_sources (user_id, source)
        VALUES ($1, $2)
        ON CONFLICT (user_id, source) DO NOTHING
        "#,
    )
    .bind(user_id)
    .bind(source)
    .execute(&state.pool)
    .await
    .map_err(|_| AppError::InternalServerError)?;

    Ok(StatusCode::CREATED)
}

pub async fn delete_excluded_source(
    Path((user_id, source)): Path<(Uuid, String)>,
    State(state): State<AppState>,
) -> Result<impl IntoResponse, AppError> {
    let normalized = source.trim().to_lowercase();
    let result = sqlx::query(
        r#"
        DELETE FROM user_excluded_sources
        WHERE user_id = $1 AND source = $2
        "#,
    )
    .bind(user_id)
    .bind(normalized)
    .execute(&state.pool)
    .await
    .map_err(|_| AppError::InternalServerError)?;

    if result.rows_affected() == 0 {
        return Err(AppError::InvalidInput("excluded source not found".to_string()));
    }

    Ok(StatusCode::NO_CONTENT)
}

pub async fn add_excluded_keyword(
    Path(user_id): Path<Uuid>,
    State(state): State<AppState>,
    Json(body): Json<UpdateExcludedKeywordSchema>,
) -> Result<impl IntoResponse, AppError> {
    let keyword = body.keyword.trim().to_lowercase();
    if keyword.is_empty() {
        return Err(AppError::InvalidInput("keyword must not be empty".to_string()));
    }

    let inserted = sqlx::query_as::<_, UserExcludedKeyword>(
        r#"
        INSERT INTO user_excluded_keywords (user_id, keyword)
        VALUES ($1, $2)
        ON CONFLICT (user_id, keyword) DO NOTHING
        RETURNING id, user_id, keyword, created_at
        "#,
    )
    .bind(user_id)
    .bind(keyword)
    .fetch_optional(&state.pool)
    .await
    .map_err(|_| AppError::InternalServerError)?;

    match inserted {
        Some(kw) => Ok((StatusCode::CREATED, Json(kw)).into_response()),
        None => Err(AppError::InvalidInput("keyword exclusion already exists".to_string())),
    }
}

pub async fn delete_excluded_keyword(
    Path((user_id, keyword_id)): Path<(Uuid, Uuid)>,
    State(state): State<AppState>,
) -> Result<impl IntoResponse, AppError> {
    let result = sqlx::query(
        r#"
        DELETE FROM user_excluded_keywords
        WHERE user_id = $1 AND id = $2
        "#,
    )
    .bind(user_id)
    .bind(keyword_id)
    .execute(&state.pool)
    .await
    .map_err(|_| AppError::InternalServerError)?;

    if result.rows_affected() == 0 {
        return Err(AppError::InvalidInput("excluded keyword not found".to_string()));
    }

    Ok(StatusCode::NO_CONTENT)
}

pub async fn upsert_user_feedback(
    Path(user_id): Path<Uuid>,
    State(state): State<AppState>,
    Json(body): Json<UserFeedbackSchema>,
) -> Result<impl IntoResponse, AppError> {
    if body.feedback != "relevant" && body.feedback != "not_relevant" {
        return Err(AppError::InvalidInput(
            "feedback must be relevant or not_relevant".to_string(),
        ));
    }

    sqlx::query(
        r#"
        INSERT INTO user_article_feedback (user_id, article_id, feedback)
        VALUES ($1, $2, $3)
        ON CONFLICT (user_id, article_id)
        DO UPDATE SET
            feedback = EXCLUDED.feedback,
            updated_at = CURRENT_TIMESTAMP
        "#,
    )
    .bind(user_id)
    .bind(body.article_id)
    .bind(body.feedback)
    .execute(&state.pool)
    .await
    .map_err(|_| AppError::InternalServerError)?;

    Ok(StatusCode::NO_CONTENT)
}

pub async fn get_user_quality_stats(
    Path(user_id): Path<Uuid>,
    State(state): State<AppState>,
) -> Result<Json<UserQualityStats>, AppError> {
    let total_delivered: i64 = sqlx::query_scalar(
        r#"
        SELECT COUNT(*)
        FROM user_article_delivery
        WHERE user_id = $1
        "#,
    )
    .bind(user_id)
    .fetch_one(&state.pool)
    .await
    .unwrap_or(0);

    let total_feedback: i64 = sqlx::query_scalar(
        r#"
        SELECT COUNT(*)
        FROM user_article_feedback
        WHERE user_id = $1
        "#,
    )
    .bind(user_id)
    .fetch_one(&state.pool)
    .await
    .unwrap_or(0);

    let relevant_count: i64 = sqlx::query_scalar(
        r#"
        SELECT COUNT(*)
        FROM user_article_feedback
        WHERE user_id = $1 AND feedback = 'relevant'
        "#,
    )
    .bind(user_id)
    .fetch_one(&state.pool)
    .await
    .unwrap_or(0);

    let not_relevant_count: i64 = sqlx::query_scalar(
        r#"
        SELECT COUNT(*)
        FROM user_article_feedback
        WHERE user_id = $1 AND feedback = 'not_relevant'
        "#,
    )
    .bind(user_id)
    .fetch_one(&state.pool)
    .await
    .unwrap_or(0);

    let avg_similarity: Option<f64> = sqlx::query_scalar(
        r#"
        SELECT AVG(similarity_score)
        FROM user_article_delivery
        WHERE user_id = $1
        "#,
    )
    .bind(user_id)
    .fetch_one(&state.pool)
    .await
    .ok();

    let relevance_rate = if total_feedback > 0 {
        (relevant_count as f64 / total_feedback as f64) * 100.0
    } else {
        0.0
    };
    let feedback_coverage_rate = if total_delivered > 0 {
        (total_feedback as f64 / total_delivered as f64) * 100.0
    } else {
        0.0
    };

    Ok(Json(UserQualityStats {
        user_id,
        total_delivered,
        total_feedback,
        relevant_count,
        not_relevant_count,
        relevance_rate,
        feedback_coverage_rate,
        avg_similarity: avg_similarity.unwrap_or(0.0),
    }))
}
