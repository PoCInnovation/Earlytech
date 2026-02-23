use axum::{routing::{get, post}, Router};
use crate::handlers::{
    add_user_keyword,
    get_article_count,
    list_user_keywords,
    login_user_handler,
    register_user_handler,
};
use crate::state::AppState;

pub fn create_router(state: AppState) -> Router {
    Router::new()
        .route("/", get(|| async { "API Root" }))
        .route("/articles/count", get(get_article_count))
        .route("/auth/register", post(register_user_handler))
        .route("/auth/login", post(login_user_handler))
        .route("/users/:id/keywords", get(list_user_keywords))
        .route("/users/:id/keywords", post(add_user_keyword))
        .with_state(state)
}
