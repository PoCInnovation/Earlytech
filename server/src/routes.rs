use axum::{routing::{get, post, delete}, Router};
use crate::handlers::{
    add_user_keyword,
    delete_user_keyword,
    get_article,
    get_article_count,
    get_delivery_stats,
    get_recent_deliveries,
    get_user_feed,
    get_user_stats,
    list_articles,
    list_user_keywords,
    login_user_handler,
    register_user_handler,
};
use crate::state::AppState;

pub fn create_router(state: AppState) -> Router {
    Router::new()
        .route("/", get(|| async { "API Root" }))
        // Articles
        .route("/articles/count", get(get_article_count))
        .route("/articles", get(list_articles))
        .route("/articles/:id", get(get_article))
        // Auth
        .route("/auth/register", post(register_user_handler))
        .route("/auth/login", post(login_user_handler))
        // User keywords
        .route("/users/:id/keywords", get(list_user_keywords))
        .route("/users/:id/keywords", post(add_user_keyword))
        .route("/users/:user_id/keywords/:keyword_id", delete(delete_user_keyword))
        // User feed & stats
        .route("/users/:id/feed", get(get_user_feed))
        .route("/users/:id/stats", get(get_user_stats))
        // Global delivery stats
        .route("/delivery/stats", get(get_delivery_stats))
        .route("/delivery/recent", get(get_recent_deliveries))
        .with_state(state)
}
