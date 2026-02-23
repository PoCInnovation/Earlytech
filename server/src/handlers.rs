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
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, message) = match self {
            AppError::InternalServerError => (StatusCode::INTERNAL_SERVER_ERROR, "Internal server error"),
            AppError::UserAlreadyExists => (StatusCode::CONFLICT, "User with that email already exists"),
            AppError::InvalidCredentials => (StatusCode::UNAUTHORIZED, "Invalid email or password"),
            AppError::KeywordAlreadyExists => (StatusCode::CONFLICT, "Keyword already exists for this user"),
            AppError::InvalidKeyword => (StatusCode::BAD_REQUEST, "Keyword must not be empty"),
        };
        (status, Json(json!({"error": message}))).into_response()
    }
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
